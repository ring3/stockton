# -*- coding: utf-8 -*-
"""
===================================
A股数据源获取模块 - OpenClaw Skill
===================================

职责：
1. 使用多数据源获取股票数据（efinance优先，akshare备用）
2. 支持自动故障切换
3. 所有结果均可转换为 JSON 格式，便于传给 LLM 分析

数据源优先级：
1. efinance (Priority 0) - 首选，API稳定
2. akshare (Priority 1) - 备用，支持多源切换

使用方法：
    from data_fetcher import get_stock_data, get_stock_data_for_llm
    
    # 获取股票数据
    result = get_stock_data('600519', days=60)
    
    # 获取 LLM 格式数据
    prompt = get_stock_data_for_llm('600519', days=60)
"""

import logging
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

# 配置日志
logger = logging.getLogger(__name__)

# 导入数据源管理器
try:
    from data_provider import DataFetcherManager, EfinanceFetcher
    _HAS_DATA_PROVIDER = True
except ImportError:
    _HAS_DATA_PROVIDER = False
    EfinanceFetcher = None  # 确保变量存在，避免后面引用报错
    logger.warning("data_provider 模块不可用")


# =============================================================================
# 数据模型
# =============================================================================

@dataclass
class StockDailyData:
    """股票日线数据"""
    date: str
    code: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    pct_chg: float
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    volume_ratio: Optional[float] = None
    data_source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StockDataResult:
    """股票数据获取结果"""
    success: bool
    code: str
    name: str = ""
    daily_data: List[StockDailyData] = field(default_factory=list)
    data_source: str = ""
    error_message: str = ""
    fetch_time: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'code': self.code,
            'name': self.name,
            'daily_data': [d.to_dict() for d in self.daily_data],
            'data_source': self.data_source,
            'error_message': self.error_message,
            'fetch_time': self.fetch_time,
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)
    
    def to_llm_prompt(self) -> str:
        """转换为 LLM 提示词格式"""
        lines = [
            f"# 股票数据: {self.code} {self.name}",
            f"数据获取时间: {self.fetch_time}",
            f"数据来源: {self.data_source}",
            "",
            "## 历史数据（最近10日）",
        ]
        
        if self.daily_data:
            for i, d in enumerate(reversed(self.daily_data[-10:]), 1):
                lines.append(
                    f"{i}. {d.date}: 开{d.open:.2f} 高{d.high:.2f} "
                    f"低{d.low:.2f} 收{d.close:.2f} "
                    f"({d.pct_chg:+.2f}%) "
                    f"MA5:{d.ma5:.2f} MA10:{d.ma10:.2f}"
                )
        else:
            lines.append("- 未获取到历史数据")
        
        return "\n".join(lines)


# =============================================================================
# 数据转换函数
# =============================================================================

def _df_to_daily_data_list(df, stock_code: str, data_source: str) -> List[StockDailyData]:
    """将 DataFrame 转换为 StockDailyData 列表"""
    result = []
    
    for _, row in df.iterrows():
        try:
            # 处理日期格式
            date_val = row.get('date', '')
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)[:10]
            
            data = StockDailyData(
                date=date_str,
                code=stock_code,
                open=float(row.get('open', 0)) if pd.notna(row.get('open')) else 0,
                high=float(row.get('high', 0)) if pd.notna(row.get('high')) else 0,
                low=float(row.get('low', 0)) if pd.notna(row.get('low')) else 0,
                close=float(row.get('close', 0)) if pd.notna(row.get('close')) else 0,
                volume=float(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                amount=float(row.get('amount', 0)) if pd.notna(row.get('amount')) else 0,
                pct_chg=float(row.get('pct_chg', 0)) if pd.notna(row.get('pct_chg')) else 0,
                ma5=float(row.get('ma5')) if pd.notna(row.get('ma5')) else None,
                ma10=float(row.get('ma10')) if pd.notna(row.get('ma10')) else None,
                ma20=float(row.get('ma20')) if pd.notna(row.get('ma20')) else None,
                ma60=float(row.get('ma60')) if pd.notna(row.get('ma60')) else None,
                volume_ratio=float(row.get('volume_ratio')) if pd.notna(row.get('volume_ratio')) else None,
                data_source=data_source,
            )
            result.append(data)
        except Exception as e:
            logger.warning(f"解析行数据失败: {e}")
            continue
    
    return result


# =============================================================================
# 主函数
# =============================================================================

def get_stock_data(
    stock_code: str,
    days: int = 60,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取股票完整数据（多源自动切换）
    
    Args:
        stock_code: 股票代码，如 "600519"
        days: 历史数据天数（当 start_date 未指定时使用）
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        StockDataResult 的字典形式
    """
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        if not _HAS_DATA_PROVIDER:
            return StockDataResult(
                success=False,
                code=stock_code,
                error_message="data_provider 模块不可用",
                fetch_time=start_time,
            ).to_dict()
        
        # 创建数据源管理器
        manager = DataFetcherManager()
        
        # 获取数据（自动切换数据源）
        df, source_name = manager.get_daily_data(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            days=days
        )
        
        if df is None or df.empty:
            return StockDataResult(
                success=False,
                code=stock_code,
                error_message="未获取到数据",
                fetch_time=start_time,
            ).to_dict()
        
        # 转换为 StockDailyData 列表
        daily_data = _df_to_daily_data_list(df, stock_code, source_name)
        
        # 获取股票名称（从 efinance 实时行情）
        name = f"股票{stock_code}"
        try:
            if EfinanceFetcher:
                ef_fetcher = EfinanceFetcher()
                rt = ef_fetcher.get_realtime_quote(stock_code)
                if rt and rt.get('name'):
                    name = rt['name']
        except Exception:
            pass
        
        result = StockDataResult(
            success=True,
            code=stock_code,
            name=name,
            daily_data=daily_data,
            data_source=source_name,
            fetch_time=start_time,
        )
        
        return result.to_dict()
        
    except Exception as e:
        logger.error(f"获取 {stock_code} 数据失败: {e}")
        return StockDataResult(
            success=False,
            code=stock_code,
            error_message=str(e),
            fetch_time=start_time,
        ).to_dict()


def get_stock_data_for_llm(
    stock_code: str,
    days: int = 60,
    format_type: str = "prompt"
) -> str:
    """
    获取股票数据并格式化为 LLM 可用的格式
    
    Args:
        stock_code: 股票代码
        days: 历史数据天数
        format_type: 输出格式 ("prompt", "json")
        
    Returns:
        格式化后的数据字符串
    """
    data = get_stock_data(stock_code, days=days)
    
    if not data['success']:
        return f"获取 {stock_code} 数据失败: {data.get('error_message', '未知错误')}"
    
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    # 构建 LLM 提示词格式
    lines = [
        f"# 股票数据: {data['code']} {data['name']}",
        f"数据获取时间: {data['fetch_time']}",
        f"数据来源: {data['data_source']}",
        "",
        "## 历史数据（最近10日）",
    ]
    
    daily_data = data.get('daily_data', [])
    if daily_data:
        for i, d in enumerate(reversed(daily_data[-10:]), 1):
            lines.append(
                f"{i}. {d['date']}: 开{d['open']:.2f} 高{d['high']:.2f} "
                f"低{d['low']:.2f} 收{d['close']:.2f} "
                f"({d['pct_chg']:+.2f}%) "
                f"MA5:{d.get('ma5', 0):.2f} MA10:{d.get('ma10', 0):.2f}"
            )
    else:
        lines.append("- 未获取到历史数据")
    
    return "\n".join(lines)


# =============================================================================
# 兼容层 - 为旧代码提供向后兼容
# =============================================================================

class RealtimeQuote:
    """
    实时行情数据类 (兼容旧接口)
    
    注意: 此类仅用于兼容，实际功能请使用 akshare 直接获取
    """
    def __init__(self, **kwargs):
        self.code = kwargs.get('code', '')
        self.name = kwargs.get('name', '')
        self.price = kwargs.get('price', 0.0)
        self.change_pct = kwargs.get('change_pct', 0.0)
        self.change_amount = kwargs.get('change_amount', 0.0)
        self.volume = kwargs.get('volume', 0.0)
        self.amount = kwargs.get('amount', 0.0)
        self.turnover_rate = kwargs.get('turnover_rate', 0.0)
        self.volume_ratio = kwargs.get('volume_ratio', 0.0)
        self.amplitude = kwargs.get('amplitude', 0.0)
        self.high = kwargs.get('high', 0.0)
        self.low = kwargs.get('low', 0.0)
        self.open_price = kwargs.get('open_price', 0.0)
        self.pe_ratio = kwargs.get('pe_ratio', 0.0)
        self.pb_ratio = kwargs.get('pb_ratio', 0.0)
        self.total_mv = kwargs.get('total_mv', 0.0)
        self.circ_mv = kwargs.get('circ_mv', 0.0)


class ChipDistribution:
    """
    筹码分布数据类 (兼容旧接口)
    
    注意: 此类仅用于兼容，实际功能请使用 akshare 直接获取
    """
    def __init__(self, **kwargs):
        self.code = kwargs.get('code', '')
        self.date = kwargs.get('date', '')
        self.profit_ratio = kwargs.get('profit_ratio', 0.0)
        self.avg_cost = kwargs.get('avg_cost', 0.0)
        self.concentration_90 = kwargs.get('concentration_90', 0.0)
        self.concentration_70 = kwargs.get('concentration_70', 0.0)


class AkshareDataSource:
    """
    Akshare 数据源兼容类
    
    此类为旧代码提供向后兼容，内部使用新的 DataFetcherManager
    """
    
    def __init__(self, sleep_min: float = 2.0, sleep_max: float = 5.0):
        """
        初始化数据源
        
        Args:
            sleep_min: 最小休眠时间（秒）- 已废弃，仅保留兼容性
            sleep_max: 最大休眠时间（秒）- 已废弃，仅保留兼容性
        """
        self._manager = None
        self._sleep_min = sleep_min
        self._sleep_max = sleep_max
        
        # 尝试初始化管理器
        try:
            from data_provider import DataFetcherManager
            self._manager = DataFetcherManager()
        except Exception as e:
            logger.warning(f"DataFetcherManager 初始化失败: {e}")
    
    def get_daily_data(self, stock_code: str, days: int = 60) -> List[StockDailyData]:
        """
        获取历史日线数据（兼容旧接口）
        
        Args:
            stock_code: 股票代码
            days: 获取天数
            
        Returns:
            StockDailyData 列表
        """
        if self._manager is None:
            logger.error("DataFetcherManager 未初始化")
            return []
        
        try:
            df, source_name = self._manager.get_daily_data(stock_code, days=days)
            
            if df is None or df.empty:
                return []
            
            # 转换为 StockDailyData 列表
            result = []
            for _, row in df.iterrows():
                try:
                    data = StockDailyData(
                        date=str(row.get('date', '')),
                        code=stock_code,
                        open=float(row.get('open', 0)) if pd.notna(row.get('open')) else 0,
                        high=float(row.get('high', 0)) if pd.notna(row.get('high')) else 0,
                        low=float(row.get('low', 0)) if pd.notna(row.get('low')) else 0,
                        close=float(row.get('close', 0)) if pd.notna(row.get('close')) else 0,
                        volume=float(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0,
                        amount=float(row.get('amount', 0)) if pd.notna(row.get('amount')) else 0,
                        pct_chg=float(row.get('pct_chg', 0)) if pd.notna(row.get('pct_chg')) else 0,
                        ma5=float(row.get('ma5')) if pd.notna(row.get('ma5')) else None,
                        ma10=float(row.get('ma10')) if pd.notna(row.get('ma10')) else None,
                        ma20=float(row.get('ma20')) if pd.notna(row.get('ma20')) else None,
                        ma60=float(row.get('ma60')) if pd.notna(row.get('ma60')) else None,
                        volume_ratio=float(row.get('volume_ratio')) if pd.notna(row.get('volume_ratio')) else None,
                        data_source=source_name,
                    )
                    result.append(data)
                except Exception as e:
                    logger.warning(f"解析行数据失败: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"获取 {stock_code} 数据失败: {e}")
            return []
    
    def get_realtime_quote(self, stock_code: str) -> Optional[RealtimeQuote]:
        """
        获取实时行情（兼容旧接口）
        
        注意: 此方法直接调用 akshare，不经过 DataFetcherManager
        """
        try:
            import akshare as ak
            import time
            time.sleep(0.5)  # 简单防封禁
            
            # 获取全部 A 股实时行情
            df = ak.stock_zh_a_spot_em()
            
            # 查找指定股票
            row = df[df['代码'] == stock_code]
            if row.empty:
                return None
            
            row = row.iloc[0]
            
            def safe_float(val, default=0.0):
                try:
                    if pd.isna(val):
                        return default
                    return float(val)
                except:
                    return default
            
            return RealtimeQuote(
                code=stock_code,
                name=str(row.get('名称', '')),
                price=safe_float(row.get('最新价')),
                change_pct=safe_float(row.get('涨跌幅')),
                change_amount=safe_float(row.get('涨跌额')),
                volume=safe_float(row.get('成交量')),
                amount=safe_float(row.get('成交额')),
                turnover_rate=safe_float(row.get('换手率')),
                volume_ratio=safe_float(row.get('量比')),
                amplitude=safe_float(row.get('振幅')),
                high=safe_float(row.get('最高')),
                low=safe_float(row.get('最低')),
                open_price=safe_float(row.get('今开')),
                pe_ratio=safe_float(row.get('市盈率-动态')),
                pb_ratio=safe_float(row.get('市净率')),
                total_mv=safe_float(row.get('总市值')),
                circ_mv=safe_float(row.get('流通市值')),
            )
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return None
    
    def get_chip_distribution(self, stock_code: str) -> Optional[ChipDistribution]:
        """
        获取筹码分布（兼容旧接口）
        
        注意: 此方法直接调用 akshare，不经过 DataFetcherManager
        """
        try:
            import akshare as ak
            import time
            time.sleep(0.5)  # 简单防封禁
            
            df = ak.stock_cyq_em(symbol=stock_code)
            
            if df is None or df.empty:
                return None
            
            # 取最新一天的数据
            latest = df.iloc[-1]
            
            # 处理获利比例
            profit_ratio = latest.get('获利比例', 0)
            if isinstance(profit_ratio, str) and '%' in profit_ratio:
                profit_ratio = float(profit_ratio.replace('%', '')) / 100
            
            return ChipDistribution(
                code=stock_code,
                date=str(latest.get('日期', '')),
                profit_ratio=float(profit_ratio) if profit_ratio else 0.0,
                avg_cost=float(latest.get('平均成本', 0)) if pd.notna(latest.get('平均成本')) else 0.0,
                concentration_90=float(latest.get('90集中度', 0)) if pd.notna(latest.get('90集中度')) else 0.0,
                concentration_70=float(latest.get('70集中度', 0)) if pd.notna(latest.get('70集中度')) else 0.0,
            )
            
        except Exception as e:
            logger.error(f"获取筹码分布失败: {e}")
            return None


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("测试: 多数据源获取 - 股票 600519")
    print("=" * 70)
    
    result = get_stock_data('600519', days=10)
    print(f"\n成功: {result['success']}")
    print(f"代码: {result['code']}")
    print(f"名称: {result['name']}")
    print(f"数据来源: {result['data_source']}")
    print(f"历史数据条数: {len(result['daily_data'])}")
    
    if result['daily_data']:
        print("\n最近5日数据:")
        for d in result['daily_data'][-5:]:
            print(f"  {d['date']}: 收{d['close']:.2f} ({d['pct_chg']:+.2f}%)")
    
    print("\n" + "=" * 70)
    print("测试: LLM Prompt 格式")
    print("=" * 70)
    
    prompt = get_stock_data_for_llm('600519', days=5, format_type='prompt')
    print(prompt)
