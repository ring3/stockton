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

数据源：akshare
- 指数行情: ak.stock_zh_index_spot_sina()
- A股实时行情: ak.stock_zh_a_spot_em()
- 行业板块: ak.stock_board_industry_name_em()
"""

import logging
import time
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

import pandas as pd
import numpy as np

# 先禁用代理，避免连接问题
import os
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# 尝试导入 akshare
try:
    import akshare as ak
except ImportError:
    ak = None

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
        if ak is None:
            raise ImportError("请安装 akshare: pip install akshare")
        
        logger.info("大盘市场数据分析器初始化成功")
    
    def _call_akshare_with_retry(self, fn, name: str, attempts: int = 2):
        """
        带重试的 akshare 调用
        
        Args:
            fn: 要执行的函数
            name: 功能名称（用于日志）
            attempts: 重试次数
            
        Returns:
            函数执行结果，失败返回 None
        """
        last_error: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                logger.warning(f"[大盘] {name} 获取失败 (attempt {attempt}/{attempts}): {e}")
                if attempt < attempts:
                    time.sleep(min(2 ** attempt, 5))
        
        logger.error(f"[大盘] {name} 最终失败: {last_error}")
        return None
    
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
        
        return overview
    
    def _get_main_indices(self) -> List[MarketIndex]:
        """获取主要指数实时行情"""
        indices = []
        
        try:
            logger.info("[大盘] 获取主要指数实时行情...")
            
            # 使用 akshare 获取指数行情
            df = self._call_akshare_with_retry(
                ak.stock_zh_index_spot_sina, 
                "指数行情", 
                attempts=2
            )
            
            if df is not None and not df.empty:
                for code, name in self.MAIN_INDICES.items():
                    # 查找对应指数
                    row = df[df['代码'] == code]
                    if row.empty:
                        # 尝试带前缀查找
                        row = df[df['代码'].str.contains(code)]
                    
                    if not row.empty:
                        row = row.iloc[0]
                        index = MarketIndex(
                            code=code,
                            name=name,
                            current=float(row.get('最新价', 0) or 0),
                            change=float(row.get('涨跌额', 0) or 0),
                            change_pct=float(row.get('涨跌幅', 0) or 0),
                            open=float(row.get('今开', 0) or 0),
                            high=float(row.get('最高', 0) or 0),
                            low=float(row.get('最低', 0) or 0),
                            prev_close=float(row.get('昨收', 0) or 0),
                            volume=float(row.get('成交量', 0) or 0),
                            amount=float(row.get('成交额', 0) or 0),
                        )
                        # 计算振幅
                        if index.prev_close > 0:
                            index.amplitude = (index.high - index.low) / index.prev_close * 100
                        indices.append(index)
                
                logger.info(f"[大盘] 获取到 {len(indices)} 个指数行情")
                
        except Exception as e:
            logger.error(f"[大盘] 获取指数行情失败: {e}")
        
        return indices
    
    def _get_market_statistics(self, overview: MarketOverview):
        """获取市场涨跌统计"""
        try:
            logger.info("[大盘] 获取市场涨跌统计...")
            
            # 获取全部A股实时行情
            df = self._call_akshare_with_retry(
                ak.stock_zh_a_spot_em, 
                "A股实时行情", 
                attempts=2
            )
            
            if df is not None and not df.empty:
                # 涨跌统计
                change_col = '涨跌幅'
                if change_col in df.columns:
                    df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
                    overview.up_count = len(df[df[change_col] > 0])
                    overview.down_count = len(df[df[change_col] < 0])
                    overview.flat_count = len(df[df[change_col] == 0])
                    
                    # 涨停跌停统计（涨跌幅 >= 9.9% 或 <= -9.9%）
                    overview.limit_up_count = len(df[df[change_col] >= 9.9])
                    overview.limit_down_count = len(df[df[change_col] <= -9.9])
                
                # 两市成交额
                amount_col = '成交额'
                if amount_col in df.columns:
                    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
                    overview.total_amount = df[amount_col].sum() / 1e8  # 转为亿元
                
                logger.info(
                    f"[大盘] 涨:{overview.up_count} 跌:{overview.down_count} "
                    f"平:{overview.flat_count} 涨停:{overview.limit_up_count} "
                    f"跌停:{overview.limit_down_count} 成交额:{overview.total_amount:.0f}亿"
                )
                
        except Exception as e:
            logger.error(f"[大盘] 获取涨跌统计失败: {e}")
    
    def _get_sector_rankings(self, overview: MarketOverview):
        """获取板块涨跌榜"""
        try:
            logger.info("[大盘] 获取板块涨跌榜...")
            
            # 获取行业板块行情
            df = self._call_akshare_with_retry(
                ak.stock_board_industry_name_em, 
                "行业板块行情", 
                attempts=2
            )
            
            if df is not None and not df.empty:
                change_col = '涨跌幅'
                if change_col in df.columns:
                    df[change_col] = pd.to_numeric(df[change_col], errors='coerce')
                    df = df.dropna(subset=[change_col])
                    
                    # 涨幅前5
                    top = df.nlargest(5, change_col)
                    overview.top_sectors = [
                        SectorInfo(name=row['板块名称'], change_pct=row[change_col])
                        for _, row in top.iterrows()
                    ]
                    
                    # 跌幅前5
                    bottom = df.nsmallest(5, change_col)
                    overview.bottom_sectors = [
                        SectorInfo(name=row['板块名称'], change_pct=row[change_col])
                        for _, row in bottom.iterrows()
                    ]
                    
                    logger.info(
                        f"[大盘] 领涨板块: {[s.name for s in overview.top_sectors]}"
                    )
                    logger.info(
                        f"[大盘] 领跌板块: {[s.name for s in overview.bottom_sectors]}"
                    )
                    
        except Exception as e:
            logger.error(f"[大盘] 获取板块涨跌榜失败: {e}")


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
5. **后市展望**: 结合当前走势，给出明日市场预判
6. **风险提示**: 需要关注的风险点

请用专业的分析师视角给出见解。
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
