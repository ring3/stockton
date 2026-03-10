# -*- coding: utf-8 -*-
"""
===================================
大盘市场分析模块 - OpenClaw Skill
===================================

职责：
1. 获取大盘指数数据（上证、深证、创业板、科创50等）
2. 获取市场涨跌统计（上涨/下跌家数、涨停跌停数）
3. 获取板块涨跌榜（领涨/领跌板块）
4. 生成市场概览数据，支持 JSON 格式传给 LLM

数据源：通过 DataFetcherManager 获取，支持多源自动切换
- 指数行情: 主要指数实时行情
- A股实时行情: 全市场涨跌统计
- 行业板块: 板块涨跌排行
"""

import logging
import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

import pandas as pd
import numpy as np

# 导入数据源管理器
try:
    from data_provider import DataFetcherManager, DataFetchError
except ImportError:
    DataFetcherManager = None
    DataFetchError = Exception

logger = logging.getLogger(__name__)


# =============================================================================
# 数据模型 - 所有类都支持 to_dict() 方法
# =============================================================================

@dataclass
class MarketIndex:
    """大盘指数数据"""
    code: str                    # 指数代码
    name: str                    # 指数名称
    current: float = 0.0         # 当前点位
    change: float = 0.0          # 涨跌点数
    change_pct: float = 0.0      # 涨跌幅(%)
    open: float = 0.0            # 开盘点位
    high: float = 0.0            # 最高点位
    low: float = 0.0             # 最低点位
    prev_close: float = 0.0      # 昨收点位
    volume: float = 0.0          # 成交量（手）
    amount: float = 0.0          # 成交额（元）
    amplitude: float = 0.0       # 振幅(%)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class SectorInfo:
    """板块信息"""
    name: str                    # 板块名称
    change_pct: float = 0.0      # 涨跌幅(%)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MarketOverview:
    """
    市场概览数据
    
    包含完整的市场概况信息，可直接转换为 JSON 传给 LLM
    """
    date: str                           # 日期
    
    # 主要指数
    indices: List[MarketIndex] = field(default_factory=list)
    
    # 涨跌统计
    up_count: int = 0                   # 上涨家数
    down_count: int = 0                 # 下跌家数
    flat_count: int = 0                 # 平盘家数
    limit_up_count: int = 0             # 涨停家数
    limit_down_count: int = 0           # 跌停家数
    total_amount: float = 0.0           # 两市成交额（亿元）
    
    # 板块涨跌榜
    top_sectors: List[SectorInfo] = field(default_factory=list)     # 涨幅前5板块
    bottom_sectors: List[SectorInfo] = field(default_factory=list)  # 跌幅前5板块
    
    # 期货贴水数据（新增）
    futures_basis: List[Dict[str, Any]] = field(default_factory=list)  # 股指期货贴水数据
    
    # ETF IV数据（新增）
    etf_iv: Dict[str, Any] = field(default_factory=dict)  # ETF隐含波动率数据
    
    # 元数据
    data_source: str = "akshare"
    fetch_time: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'date': self.date,
            'indices': [idx.to_dict() for idx in self.indices],
            'up_count': self.up_count,
            'down_count': self.down_count,
            'flat_count': self.flat_count,
            'limit_up_count': self.limit_up_count,
            'limit_down_count': self.limit_down_count,
            'total_amount': self.total_amount,
            'top_sectors': [s.to_dict() for s in self.top_sectors],
            'bottom_sectors': [s.to_dict() for s in self.bottom_sectors],
            'futures_basis': self.futures_basis,
            'etf_iv': self.etf_iv,
            'data_source': self.data_source,
            'fetch_time': self.fetch_time,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_llm_prompt(self) -> str:
        """
        转换为适合传给 LLM 的提示词格式
        
        Returns:
            格式化的市场概览文本
        """
        lines = [
            f"# A股市场概览 - {self.date}",
            f"数据获取时间: {self.fetch_time}",
            f"数据来源: {self.data_source}",
            "",
            "## 主要指数行情",
        ]
        
        for idx in self.indices:
            direction = "↑" if idx.change_pct > 0 else "↓" if idx.change_pct < 0 else "→"
            lines.append(
                f"- **{idx.name}** ({idx.code}): {idx.current:.2f} "
                f"{direction} {idx.change:+.2f} ({idx.change_pct:+.2f}%) "
                f"| 高: {idx.high:.2f} 低: {idx.low:.2f}"
            )
        
        lines.extend([
            "",
            "## 市场涨跌统计",
            f"- 上涨家数: {self.up_count} 📈",
            f"- 下跌家数: {self.down_count} 📉",
            f"- 平盘家数: {self.flat_count} ➡️",
            f"- 涨停家数: {self.limit_up_count} 🟥",
            f"- 跌停家数: {self.limit_down_count} 🟩",
            f"- 两市成交额: {self.total_amount:.0f} 亿元",
        ])
        
        if self.top_sectors:
            lines.extend(["", "## 领涨板块 (Top 5)"])
            for i, sector in enumerate(self.top_sectors, 1):
                lines.append(f"{i}. {sector.name}: +{sector.change_pct:.2f}%")
        
        if self.bottom_sectors:
            lines.extend(["", "## 领跌板块 (Top 5)"])
            for i, sector in enumerate(self.bottom_sectors, 1):
                lines.append(f"{i}. {sector.name}: {sector.change_pct:.2f}%")
        
        # 市场情绪判断
        lines.extend(["", "## 市场情绪"])
        if self.up_count > self.down_count * 2:
            sentiment = "强势上涨 📈📈"
        elif self.up_count > self.down_count:
            sentiment = "普涨格局 📈"
        elif self.down_count > self.up_count * 2:
            sentiment = "强势下跌 📉📉"
        elif self.down_count > self.up_count:
            sentiment = "普跌格局 📉"
        else:
            sentiment = "震荡分化 ↔️"
        
        lines.append(f"- 整体氛围: {sentiment}")
        lines.append(f"- 涨跌比: {self.up_count}:{self.down_count}")
        
        # 期货贴水数据（新增）
        # 期货代码到股指名称的映射
        futures_name_map = {
            'IF': '沪深300',
            'IC': '中证500', 
            'IM': '中证1000',
            'IH': '上证50'
        }
        
        if self.futures_basis:
            lines.extend(["", "## 股指期货贴水/升水"])
            for basis in self.futures_basis:
                futures_code = basis.get('futures_code', '')
                index_name = basis.get('index_name', 'Unknown')
                # 如果index_name为空或Unknown，使用映射表
                if not index_name or index_name == 'Unknown':
                    # 从期货代码提取前缀（如 IF0 -> IF）
                    code_prefix = ''.join([c for c in futures_code if c.isalpha()])
                    index_name = futures_name_map.get(code_prefix, futures_code)
                
                basis_val = basis.get('basis', 0)
                basis_rate = basis.get('basis_rate', 0)
                annual_rate = basis.get('annualized_rate', 0)
                days = basis.get('days_to_expiry', 0)
                
                status = "升水" if basis_val > 0 else "贴水"
                lines.append(
                    f"- **{index_name}**({futures_code}): {status} {abs(basis_val):.2f}点 "
                    f"({basis_rate:+.3f}%) | 年化{annual_rate:+.2f}% | 到期{days}天"
                )
            
            # 添加贴水分析提示
            lines.extend([
                "",
                "### 贴水/升水分析提示",
                "- **深度贴水**（年化<-5%）：期货大幅低于现货，反映市场悲观情绪，可能预示短期反弹或中性对冲需求强",
                "- **轻度贴水**（年化-2%~-5%）：正常对冲成本范围，中性偏谨慎情绪",
                "- **平水附近**（年化-2%~+2%）：市场情绪均衡，无明确方向",
                "- **升水**（年化>+2%）：期货高于现货，反映乐观情绪或分红预期",
                "- **跨品种比较**：IM贴水>IC>IF时，小盘股悲观情绪更重；反之则大盘股承压"
            ])
        
        # ETF IV数据（新增）
        if self.etf_iv:
            lines.extend(["", "## 指数ETF期权隐含波动率 (IV)"])
            # etf_iv 是字典格式: {'50ETF': 15.21, '300ETF': 15.63, ...}
            for etf_name, iv_val in self.etf_iv.items():
                lines.append(f"- **{etf_name}**: IV={iv_val:.2f}%")
            
            # 添加IV分析提示
            lines.extend([
                "",
                "### 隐含波动率(IV)分析提示",
                "- **IV<15%**：低波动环境，适合卖方策略，但需警惕波动率突变风险",
                "- **IV 15%-25%**：正常波动区间，市场情绪平稳",
                "- **IV>25%**：高波动环境，恐慌情绪升温，或存在事件驱动机会",
                "- **期限结构**：近月IV>远月为Backwardation（恐慌）；近月<远月为Contango（平稳）",
                "- **Skew偏度**：虚值Put IV>虚值Call IV时，市场担忧下跌风险（保护性需求）"
            ])
        
        return "\n".join(lines)


# =============================================================================
# 大盘分析器实现
# =============================================================================

class MarketDataAnalyzer:
    """
    大盘市场数据分析器
    
    功能：
    1. 获取大盘指数实时行情
    2. 获取市场涨跌统计
    3. 获取板块涨跌榜
    4. 生成 LLM 友好的市场概览数据
    """
    
    # 主要指数代码映射
    MAIN_INDICES = {
        'sh000001': '上证指数',
        'sz399001': '深证成指',
        'sz399006': '创业板指',
        'sh000688': '科创50',
        'sh000016': '上证50',
        'sh000300': '沪深300',
        'sz399005': '中小板指',
        'sh000905': '中证500',
    }
    
    def __init__(self):
        """初始化大盘分析器"""
        if DataFetcherManager is None:
            raise ImportError("data_provider 模块不可用")
        
        self._manager = DataFetcherManager()
        logger.info("大盘市场数据分析器初始化成功")
    
    def _get_data_with_retry(self, method_name: str, display_name: str, attempts: int = 2):
        """
        带重试的数据获取
        
        Args:
            method_name: DataFetcherManager 方法名
            display_name: 功能名称（用于日志）
            attempts: 重试次数
            
        Returns:
            (DataFrame, source_name) 或 (None, None)
        """
        last_error: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                method = getattr(self._manager, method_name)
                return method()
            except Exception as e:
                last_error = e
                logger.warning(f"[大盘] {display_name} 获取失败 (attempt {attempt}/{attempts}): {e}")
                if attempt < attempts:
                    time.sleep(min(2 ** attempt, 5))
        
        logger.error(f"[大盘] {display_name} 最终失败: {last_error}")
        return None, None
    
    def get_market_overview(self) -> MarketOverview:
        """
        获取市场概览数据
        
        Returns:
            MarketOverview: 市场概览数据对象
        """
        today = datetime.now().strftime('%Y-%m-%d')
        fetch_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        overview = MarketOverview(
            date=today,
            fetch_time=fetch_time,
            data_source="akshare"
        )
        
        # 1. 获取主要指数行情
        overview.indices = self._get_main_indices()
        
        # 2. 获取涨跌统计
        self._get_market_statistics(overview)
        
        # 3. 获取板块涨跌榜
        self._get_sector_rankings(overview)
        
        # 4. 获取股指期货贴水数据（新增）
        self._get_futures_basis_data(overview)
        
        # 5. 获取ETF期权IV数据（新增）
        self._get_etf_iv_data(overview)
        
        return overview
    
    def _get_main_indices(self) -> List[MarketIndex]:
        """获取主要指数实时行情"""
        indices = []
        
        try:
            logger.info("[大盘] 获取主要指数实时行情...")
            
            # 通过 DataFetcherManager 获取指数行情
            df, source_name = self._get_data_with_retry(
                'get_market_indices',
                "指数行情",
                attempts=2
            )
            
            if df is not None and not df.empty:
                for code, name in self.MAIN_INDICES.items():
                    # 查找对应指数
                    row = df[df['code'] == code]
                    if row.empty:
                        # 尝试模糊匹配
                        row = df[df['code'].str.contains(code, na=False)]
                    
                    if not row.empty:
                        row = row.iloc[0]
                        index = MarketIndex(
                            code=code,
                            name=name,
                            current=float(row.get('price', 0) or 0),
                            change=float(row.get('change_amount', 0) or 0),
                            change_pct=float(row.get('change_pct', 0) or 0),
                            open=float(row.get('open', 0) or 0),
                            high=float(row.get('high', 0) or 0),
                            low=float(row.get('low', 0) or 0),
                            prev_close=float(row.get('prev_close', 0) or 0),
                            volume=float(row.get('volume', 0) or 0),
                            amount=float(row.get('amount', 0) or 0),
                        )
                        # 计算振幅
                        if index.prev_close > 0:
                            index.amplitude = (index.high - index.low) / index.prev_close * 100
                        indices.append(index)
                
                logger.info(f"[大盘] 从 {source_name} 获取到 {len(indices)} 个指数行情")
                
        except Exception as e:
            logger.error(f"[大盘] 获取指数行情失败: {e}")
        
        return indices
    
    def _get_market_statistics(self, overview: MarketOverview):
        """获取市场涨跌统计"""
        try:
            logger.info("[大盘] 获取市场涨跌统计...")
            
            # 通过 DataFetcherManager 获取全部A股实时行情
            df, source_name = self._get_data_with_retry(
                'get_market_overview',
                "A股实时行情",
                attempts=2
            )
            
            if df is not None and not df.empty:
                # 涨跌统计（尝试不同的列名）
                change_col = '涨跌幅' if '涨跌幅' in df.columns else 'change_pct'
                if change_col in df.columns:
                    df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
                    overview.up_count = len(df[df[change_col] > 0])
                    overview.down_count = len(df[df[change_col] < 0])
                    overview.flat_count = len(df[df[change_col] == 0])
                    
                    # 涨停跌停统计（涨跌幅 >= 9.9% 或 <= -9.9%）
                    overview.limit_up_count = len(df[df[change_col] >= 9.9])
                    overview.limit_down_count = len(df[df[change_col] <= -9.9])
                
                # 两市成交额
                amount_col = '成交额' if '成交额' in df.columns else 'amount'
                if amount_col in df.columns:
                    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
                    overview.total_amount = df[amount_col].sum() / 1e8  # 转为亿元
                
                logger.info(
                    f"[大盘] 从 {source_name} 获取: 涨:{overview.up_count} 跌:{overview.down_count} "
                    f"平:{overview.flat_count} 涨停:{overview.limit_up_count} "
                    f"跌停:{overview.limit_down_count} 成交额:{overview.total_amount:.0f}亿"
                )
                
        except Exception as e:
            logger.error(f"[大盘] 获取涨跌统计失败: {e}")
    
    def _get_sector_rankings(self, overview: MarketOverview):
        """获取板块涨跌榜"""
        try:
            logger.info("[大盘] 获取板块涨跌榜...")
            
            # 通过 DataFetcherManager 获取行业板块行情
            df, source_name = self._get_data_with_retry(
                'get_sector_rankings',
                "行业板块行情",
                attempts=2
            )
            
            if df is not None and not df.empty:
                # 尝试不同的列名
                change_col = '涨跌幅' if '涨跌幅' in df.columns else 'change_pct'
                name_col = '板块名称' if '板块名称' in df.columns else 'name'
                
                if change_col in df.columns:
                    df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
                    df = df.dropna(subset=[change_col])
                    
                    # 涨幅前5
                    top = df.nlargest(5, change_col)
                    overview.top_sectors = [
                        SectorInfo(name=row[name_col], change_pct=row[change_col])
                        for _, row in top.iterrows()
                    ]
                    
                    # 跌幅前5
                    bottom = df.nsmallest(5, change_col)
                    overview.bottom_sectors = [
                        SectorInfo(name=row[name_col], change_pct=row[change_col])
                        for _, row in bottom.iterrows()
                    ]
                    
                    logger.info(
                        f"[大盘] 从 {source_name} 获取领涨板块: {[s.name for s in overview.top_sectors]}"
                    )
                    logger.info(
                        f"[大盘] 从 {source_name} 获取领跌板块: {[s.name for s in overview.bottom_sectors]}"
                    )
                    
        except Exception as e:
            logger.error(f"[大盘] 获取板块涨跌榜失败: {e}")
    
    def _get_futures_basis_data(self, overview: MarketOverview) -> None:
        """
        获取股指期货贴水/升水数据（新增）
        
        Args:
            overview: 市场概览数据对象（会被修改）
        """
        try:
            logger.info("[大盘] 获取股指期货贴水/升水数据...")
            
            df, source_name = self._get_data_with_retry(
                'get_futures_basis',
                "期货贴水",
                attempts=2
            )
            
            if df is not None and not df.empty:
                # 转换为字典列表
                overview.futures_basis = df.to_dict('records')
                logger.info(
                    f"[大盘] 从 {source_name} 获取期货贴水: {len(overview.futures_basis)} 条"
                )
                
        except Exception as e:
            logger.warning(f"[大盘] 获取期货贴水数据失败: {e}")
            overview.futures_basis = []
    
    def _get_etf_iv_data(self, overview: MarketOverview) -> None:
        """
        获取ETF期权隐含波动率数据（新增）
        
        通过 akshare 的 option_risk_indicator_sse 一次性获取所有期权风险指标，
        然后筛选主要ETF的IV数据：
        - 50ETF (510050)
        - 300ETF (510300)
        - 500ETF (510500)
        - 创业板ETF (159915)
        
        Args:
            overview: 市场概览数据对象（会被修改）
        """
        # 主要ETF代码前缀映射
        etf_map = {
            '510050': '50ETF',
            '510300': '300ETF',
            '510500': '500ETF',
            '159915': '创业板ETF',
        }
        
        etf_iv_data = {}
        
        try:
            logger.info("[大盘] 获取ETF期权IV数据...")
            
            # 直接使用第一个可用的 fetcher 获取期权风险指标
            for fetcher in self._manager._fetchers:
                try:
                    # 只尝试 akshare，因为 efinance 不支持期权
                    if hasattr(fetcher, '_ak'):
                        import akshare as ak
                        df_risk = ak.option_risk_indicator_sse()
                        
                        if df_risk is not None and not df_risk.empty:
                            # 标准化列名
                            if 'IMPLC_VOLATLTY' in df_risk.columns:
                                df_risk = df_risk.rename(columns={'IMPLC_VOLATLTY': 'iv'})
                            if 'CONTRACT_ID' in df_risk.columns:
                                df_risk = df_risk.rename(columns={'CONTRACT_ID': 'code'})
                            
                            # 为每个ETF计算平均IV
                            for etf_code, etf_name in etf_map.items():
                                etf_options = df_risk[df_risk['code'].astype(str).str.startswith(etf_code)]
                                if not etf_options.empty and 'iv' in etf_options.columns:
                                    # 过滤有效IV值
                                    valid_iv = etf_options['iv'].dropna()
                                    if not valid_iv.empty:
                                        avg_iv = valid_iv.mean()
                                        etf_iv_data[etf_name] = round(float(avg_iv) * 100, 2)
                            
                            logger.info(f"[大盘] 从 akshare 获取ETF IV: {list(etf_iv_data.keys())}")
                            break
                            
                except Exception as e:
                    logger.debug(f"[{fetcher.name}] 获取期权IV失败: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"[大盘] 获取ETF IV数据失败: {e}")
        
        overview.etf_iv = etf_iv_data
        logger.info(f"[大盘] ETF IV 数据: {etf_iv_data}")


# =============================================================================
# OpenClaw 工具函数
# =============================================================================

def get_market_overview(format_type: str = "dict") -> Union[Dict[str, Any], str]:
    """
    获取市场概览数据（OpenClaw 工具）
    
    Args:
        format_type: 输出格式
            - "dict": Python 字典（默认）
            - "json": JSON 字符串
            - "prompt": 格式化的提示词文本
            
    Returns:
        根据 format_type 返回不同格式的市场概览数据
    """
    try:
        analyzer = MarketDataAnalyzer()
        overview = analyzer.get_market_overview()
        
        if format_type == "json":
            return overview.to_json()
        elif format_type == "prompt":
            return overview.to_llm_prompt()
        else:
            return overview.to_dict()
            
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        error_result = {
            'success': False,
            'error': str(e),
            'date': datetime.now().strftime('%Y-%m-%d'),
        }
        if format_type == "json":
            return json.dumps(error_result, ensure_ascii=False)
        elif format_type == "prompt":
            return f"获取市场概览失败: {str(e)}"
        return error_result


def get_main_indices(format_type: str = "dict") -> Union[List[Dict], str]:
    """
    获取主要指数行情（OpenClaw 工具）
    
    Args:
        format_type: 输出格式 ("dict", "json", "prompt")
        
    Returns:
        主要指数数据列表
    """
    try:
        analyzer = MarketDataAnalyzer()
        indices = analyzer._get_main_indices()
        
        indices_dict = [idx.to_dict() for idx in indices]
        
        if format_type == "json":
            return json.dumps(indices_dict, indent=2, ensure_ascii=False)
        elif format_type == "prompt":
            lines = ["# 主要指数行情\n"]
            for idx in indices:
                direction = "↑" if idx.change_pct > 0 else "↓" if idx.change_pct < 0 else "→"
                lines.append(
                    f"- **{idx.name}**: {idx.current:.2f} "
                    f"{direction} {idx.change_pct:+.2f}%"
                )
            return "\n".join(lines)
        else:
            return indices_dict
            
    except Exception as e:
        logger.error(f"获取指数行情失败: {e}")
        return [] if format_type == "dict" else "[]" if format_type == "json" else f"获取失败: {e}"


def get_sector_rankings(format_type: str = "dict") -> Union[Dict[str, List], str]:
    """
    获取板块涨跌榜（OpenClaw 工具）
    
    Args:
        format_type: 输出格式 ("dict", "json", "prompt")
        
    Returns:
        板块涨跌榜数据
    """
    try:
        analyzer = MarketDataAnalyzer()
        overview = MarketOverview(date=datetime.now().strftime('%Y-%m-%d'))
        analyzer._get_sector_rankings(overview)
        
        result = {
            'date': overview.date,
            'top_sectors': [s.to_dict() for s in overview.top_sectors],
            'bottom_sectors': [s.to_dict() for s in overview.bottom_sectors],
        }
        
        if format_type == "json":
            return json.dumps(result, indent=2, ensure_ascii=False)
        elif format_type == "prompt":
            lines = [f"# 板块涨跌榜 - {overview.date}\n"]
            
            if overview.top_sectors:
                lines.append("## 领涨板块 (Top 5)")
                for i, s in enumerate(overview.top_sectors, 1):
                    lines.append(f"{i}. {s.name}: +{s.change_pct:.2f}%")
                lines.append("")
            
            if overview.bottom_sectors:
                lines.append("## 领跌板块 (Top 5)")
                for i, s in enumerate(overview.bottom_sectors, 1):
                    lines.append(f"{i}. {s.name}: {s.change_pct:.2f}%")
            
            return "\n".join(lines)
        else:
            return result
            
    except Exception as e:
        logger.error(f"获取板块涨跌榜失败: {e}")
        error_result = {'error': str(e)}
        if format_type == "json":
            return json.dumps(error_result, ensure_ascii=False)
        elif format_type == "prompt":
            return f"获取失败: {e}"
        return error_result


def analyze_market_for_llm() -> str:
    """
    获取完整的市场分析数据，格式化为 LLM 提示词
    
    Returns:
        完整的市场分析文本，可直接作为 LLM 输入
    """
    try:
        analyzer = MarketDataAnalyzer()
        overview = analyzer.get_market_overview()
        
        prompt = overview.to_llm_prompt()
        
        # 添加分析请求
        prompt += """

---

## 请基于以上市场数据进行分析

请提供：
1. **市场总结**: 今日市场整体表现如何？（2-3句话概括）
2. **指数点评**: 主要指数走势特点分析
3. **资金动向**: 成交额和资金流向解读
4. **热点解读**: 领涨领跌板块背后的逻辑
5. **衍生品情绪**: 
   - 股指期货贴水/升水分析：基差水平反映的市场情绪（悲观/乐观/中性），对冲需求强度，跨品种比较（IF/IC/IM/IH差异）
   - ETF期权IV分析：波动率水平（高/低/正常），市场情绪（恐慌/平稳），期限结构暗示的预期
6. **后市展望**: 结合现货走势+衍生品情绪，给出明日市场预判
7. **风险提示**: 需要关注的风险点（波动率突变、贴水扩大、风格切换等）

请用专业的分析师视角给出见解，特别关注衍生品数据与现货走势的背离/印证关系。
"""
        return prompt
        
    except Exception as e:
        return f"获取市场分析数据失败: {str(e)}"


# 类型提示需要放在最后
try:
    from typing import Union
except ImportError:
    Union = None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("大盘市场数据分析器测试")
    print("=" * 60)
    
    # 测试 1: 获取市场概览（字典格式）
    print("\n1. 获取市场概览（字典格式）:")
    result = get_market_overview(format_type="dict")
    if isinstance(result, dict) and 'indices' in result:
        print(f"日期: {result['date']}")
        print(f"指数数量: {len(result['indices'])}")
        print(f"上涨: {result['up_count']} | 下跌: {result['down_count']}")
        print(f"成交额: {result['total_amount']:.0f}亿")
    else:
        print(f"结果: {result}")
    
    # 测试 2: 获取市场概览（JSON格式）
    print("\n2. 获取市场概览（JSON格式片段）:")
    json_result = get_market_overview(format_type="json")
    print(json_result[:500] + "...")
    
    # 测试 3: 获取市场概览（Prompt格式）
    print("\n3. 获取市场概览（Prompt格式）:")
    prompt = get_market_overview(format_type="prompt")
    print(prompt)
    
    # 测试 4: 完整的市场分析（LLM格式）
    print("\n" + "=" * 60)
    print("4. 完整的市场分析（LLM格式）")
    print("=" * 60)
    full_analysis = analyze_market_for_llm()
    print(full_analysis[:1000] + "...")
