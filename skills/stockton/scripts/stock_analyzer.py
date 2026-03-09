# -*- coding: utf-8 -*-
"""
===================================
A股趋势交易分析器 - OpenClaw Skill (Akshare版本)
===================================

职责：
1. 基于趋势交易理念进行技术分析
2. 计算技术指标（MA、乖离率、量比等）
3. 生成买入/卖出信号
4. 所有结果均可转换为 JSON 格式，便于传给 LLM 分析

交易理念核心原则：
1. 严进策略 - 不追高，追求每笔交易成功率
2. 趋势交易 - MA5>MA10>MA20 多头排列，顺势而为
3. 效率优先 - 关注筹码结构好的股票
4. 买点偏好 - 在 MA5/MA10 附近回踩买入

技术标准：
- 多头排列：MA5 > MA10 > MA20
- 乖离率：(Close - MA5) / MA5 < 5%（不追高）
- 量能形态：缩量回调优先
"""

import logging
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Union
from enum import Enum

import pandas as pd
import numpy as np

from data_fetcher import (
    AkshareDataSource, StockDailyData, RealtimeQuote, ChipDistribution,
    get_stock_data
)

logger = logging.getLogger(__name__)


# =============================================================================
# 枚举类型
# =============================================================================

class TrendStatus(Enum):
    """趋势状态枚举"""
    STRONG_BULL = "强势多头"
    BULL = "多头排列"
    WEAK_BULL = "弱势多头"
    CONSOLIDATION = "盘整"
    WEAK_BEAR = "弱势空头"
    BEAR = "空头排列"
    STRONG_BEAR = "强势空头"


class VolumeStatus(Enum):
    """量能状态枚举"""
    HEAVY_VOLUME_UP = "放量上涨"
    HEAVY_VOLUME_DOWN = "放量下跌"
    SHRINK_VOLUME_UP = "缩量上涨"
    SHRINK_VOLUME_DOWN = "缩量回调"
    NORMAL = "量能正常"


class BuySignal(Enum):
    """买入信号枚举"""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    WAIT = "观望"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"


# =============================================================================
# 数据模型 - 所有类都支持 to_dict() 和 to_json() 方法
# =============================================================================

@dataclass
class TechnicalIndicators:
    """技术指标数据"""
    # 价格
    current_price: float = 0.0
    
    # 移动平均线
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0
    
    # 乖离率
    bias_ma5: float = 0.0
    bias_ma10: float = 0.0
    bias_ma20: float = 0.0
    
    # 量能
    volume_ratio_5d: float = 0.0
    volume_status: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class SupportResistance:
    """支撑压力位"""
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    ma5_support: bool = False
    ma10_support: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendAnalysisResult:
    """
    趋势分析结果
    
    包含完整的技术分析数据，可直接转换为 JSON 传给 LLM
    """
    code: str
    name: str = ""
    
    # 趋势判断
    trend_status: str = ""
    ma_alignment: str = ""
    trend_strength: float = 0.0  # 0-100
    
    # 技术指标
    indicators: TechnicalIndicators = None
    
    # 支撑压力
    support_resistance: SupportResistance = None
    
    # 买入信号
    buy_signal: str = ""
    signal_score: int = 0  # 0-100
    signal_reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    # 分析时间
    analysis_time: str = ""
    
    def __post_init__(self):
        if self.indicators is None:
            self.indicators = TechnicalIndicators()
        if self.support_resistance is None:
            self.support_resistance = SupportResistance()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'trend_status': self.trend_status,
            'ma_alignment': self.ma_alignment,
            'trend_strength': self.trend_strength,
            'indicators': self.indicators.to_dict() if self.indicators else None,
            'support_resistance': self.support_resistance.to_dict() if self.support_resistance else None,
            'buy_signal': self.buy_signal,
            'signal_score': self.signal_score,
            'signal_reasons': self.signal_reasons,
            'risk_factors': self.risk_factors,
            'analysis_time': self.analysis_time,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_llm_prompt(self) -> str:
        """
        转换为适合传给 LLM 的提示词格式
        
        Returns:
            格式化的分析文本
        """
        lines = [
            f"# 技术分析报告: {self.code} {self.name}",
            f"分析时间: {self.analysis_time}",
            "",
            "## 趋势判断",
            f"- 趋势状态: {self.trend_status}",
            f"- 均线排列: {self.ma_alignment}",
            f"- 趋势强度: {self.trend_strength}/100",
            "",
            "## 技术指标",
        ]
        
        if self.indicators:
            ind = self.indicators
            lines.extend([
                f"- 当前价格: {ind.current_price:.2f}",
                f"- MA5: {ind.ma5:.2f} (乖离 {ind.bias_ma5:+.2f}%)",
                f"- MA10: {ind.ma10:.2f} (乖离 {ind.bias_ma10:+.2f}%)",
                f"- MA20: {ind.ma20:.2f} (乖离 {ind.bias_ma20:+.2f}%)",
                f"- 量比: {ind.volume_ratio_5d:.2f}",
                f"- 量能状态: {ind.volume_status}",
            ])
        
        if self.support_resistance:
            sr = self.support_resistance
            lines.extend([
                "",
                "## 支撑与压力",
                f"- 支撑位: {[f'{s:.2f}' for s in sr.support_levels]}",
                f"- 压力位: {[f'{r:.2f}' for r in sr.resistance_levels]}",
                f"- MA5支撑: {'有效' if sr.ma5_support else '无效'}",
                f"- MA10支撑: {'有效' if sr.ma10_support else '无效'}",
            ])
        
        lines.extend([
            "",
            "## 买入信号",
            f"- 信号: {self.buy_signal}",
            f"- 综合评分: {self.signal_score}/100",
        ])
        
        if self.signal_reasons:
            lines.extend(["", "### 买入理由"])
            for reason in self.signal_reasons:
                lines.append(f"- {reason}")
        
        if self.risk_factors:
            lines.extend(["", "### 风险因素"])
            for risk in self.risk_factors:
                lines.append(f"- {risk}")
        
        # 操作建议
        lines.extend(["", "## 操作建议"])
        if self.signal_score >= 80:
            lines.append("✅ 强烈买入 - 多条件满足，可以积极做多")
        elif self.signal_score >= 65:
            lines.append("✅ 买入 - 基本条件满足，可适当建仓")
        elif self.signal_score >= 50:
            lines.append("⚠️ 持有 - 趋势尚可，继续观察")
        elif self.signal_score >= 35:
            lines.append("⏸️ 观望 - 等待更好时机")
        else:
            lines.append("❌ 卖出/空仓 - 趋势不利，建议离场")
        
        return "\n".join(lines)


# =============================================================================
# 分析器实现
# =============================================================================

class StockTrendAnalyzer:
    """
    股票趋势分析器
    
    基于趋势交易理念实现：
    1. 趋势判断 - MA5>MA10>MA20 多头排列
    2. 乖离率检测 - 不追高，偏离 MA5 超过 5% 不买
    3. 量能分析 - 偏好缩量回调
    4. 买点识别 - 回踩 MA5/MA10 支撑
    """
    
    # 交易参数配置
    BIAS_THRESHOLD = 5.0        # 乖离率阈值（%）
    VOLUME_SHRINK_RATIO = 0.7   # 缩量判断阈值
    VOLUME_HEAVY_RATIO = 1.5    # 放量判断阈值
    MA_SUPPORT_TOLERANCE = 0.02  # MA 支撑判断容忍度（2%）
    
    def analyze(self, daily_data: List[StockDailyData], code: str, name: str = "") -> TrendAnalysisResult:
        """
        分析股票趋势
        
        Args:
            daily_data: 日线数据列表
            code: 股票代码
            name: 股票名称
            
        Returns:
            TrendAnalysisResult 分析结果
        """
        result = TrendAnalysisResult(
            code=code,
            name=name,
            analysis_time=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        if not daily_data or len(daily_data) < 20:
            logger.warning(f"{code} 数据不足，无法进行趋势分析")
            result.risk_factors.append("数据不足，无法完成分析")
            return result
        
        # 转换为 DataFrame 便于计算
        df = pd.DataFrame([d.to_dict() for d in daily_data])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 获取最新数据
        latest = df.iloc[-1]
        
        # 安全转换为 float（处理 None 值）
        def safe_float(val, default=0.0):
            try:
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    return default
                return float(val)
            except (ValueError, TypeError):
                return default
        
        result.indicators.current_price = safe_float(latest['close'])
        result.indicators.ma5 = safe_float(latest['ma5'])
        result.indicators.ma10 = safe_float(latest['ma10'])
        result.indicators.ma20 = safe_float(latest['ma20'])
        result.indicators.ma60 = safe_float(latest.get('ma60'), 0)
        result.indicators.volume_ratio_5d = safe_float(latest.get('volume_ratio'), 1.0)
        
        # 1. 趋势判断
        self._analyze_trend(df, result)
        
        # 2. 乖离率计算
        self._calculate_bias(result)
        
        # 3. 量能分析
        self._analyze_volume(df, result)
        
        # 4. 支撑压力分析
        self._analyze_support_resistance(df, result)
        
        # 5. 生成买入信号
        self._generate_signal(result)
        
        return result
    
    def _analyze_trend(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """分析趋势状态"""
        ind = result.indicators
        ma5, ma10, ma20 = ind.ma5, ind.ma10, ind.ma20
        
        if ma5 > ma10 > ma20:
            # 检查间距是否在扩大
            if len(df) >= 5:
                prev = df.iloc[-5]
                prev_spread = (prev['ma5'] - prev['ma20']) / prev['ma20'] * 100 if prev['ma20'] > 0 else 0
                curr_spread = (ma5 - ma20) / ma20 * 100 if ma20 > 0 else 0
                
                if curr_spread > prev_spread and curr_spread > 5:
                    result.trend_status = TrendStatus.STRONG_BULL.value
                    result.ma_alignment = "强势多头排列，均线发散上行"
                    result.trend_strength = 90
                else:
                    result.trend_status = TrendStatus.BULL.value
                    result.ma_alignment = "多头排列 MA5>MA10>MA20"
                    result.trend_strength = 75
            else:
                result.trend_status = TrendStatus.BULL.value
                result.ma_alignment = "多头排列 MA5>MA10>MA20"
                result.trend_strength = 75
                
        elif ma5 > ma10 and ma10 <= ma20:
            result.trend_status = TrendStatus.WEAK_BULL.value
            result.ma_alignment = "弱势多头，MA5>MA10 但 MA10≤MA20"
            result.trend_strength = 55
            
        elif ma5 < ma10 < ma20:
            result.trend_status = TrendStatus.BEAR.value
            result.ma_alignment = "空头排列 MA5<MA10<MA20"
            result.trend_strength = 25
            
        elif ma5 < ma10 and ma10 >= ma20:
            result.trend_status = TrendStatus.WEAK_BEAR.value
            result.ma_alignment = "弱势空头，MA5<MA10 但 MA10≥MA20"
            result.trend_strength = 40
            
        else:
            result.trend_status = TrendStatus.CONSOLIDATION.value
            result.ma_alignment = "均线缠绕，趋势不明"
            result.trend_strength = 50
    
    def _calculate_bias(self, result: TrendAnalysisResult) -> None:
        """计算乖离率"""
        ind = result.indicators
        price = ind.current_price
        
        if ind.ma5 > 0:
            ind.bias_ma5 = (price - ind.ma5) / ind.ma5 * 100
        if ind.ma10 > 0:
            ind.bias_ma10 = (price - ind.ma10) / ind.ma10 * 100
        if ind.ma20 > 0:
            ind.bias_ma20 = (price - ind.ma20) / ind.ma20 * 100
    
    def _analyze_volume(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """分析量能"""
        ind = result.indicators
        
        if len(df) < 2:
            return
        
        latest = df.iloc[-1]
        prev_close = df.iloc[-2]['close']
        price_change = (latest['close'] - prev_close) / prev_close * 100
        
        # 量能状态判断
        if ind.volume_ratio_5d >= self.VOLUME_HEAVY_RATIO:
            if price_change > 0:
                ind.volume_status = VolumeStatus.HEAVY_VOLUME_UP.value
            else:
                ind.volume_status = VolumeStatus.HEAVY_VOLUME_DOWN.value
        elif ind.volume_ratio_5d <= self.VOLUME_SHRINK_RATIO:
            if price_change > 0:
                ind.volume_status = VolumeStatus.SHRINK_VOLUME_UP.value
            else:
                ind.volume_status = VolumeStatus.SHRINK_VOLUME_DOWN.value
        else:
            ind.volume_status = VolumeStatus.NORMAL.value
    
    def _analyze_support_resistance(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
        """分析支撑压力位"""
        ind = result.indicators
        sr = result.support_resistance
        price = ind.current_price
        
        # 检查 MA5 支撑
        if ind.ma5 > 0:
            ma5_distance = abs(price - ind.ma5) / ind.ma5
            if ma5_distance <= self.MA_SUPPORT_TOLERANCE and price >= ind.ma5:
                sr.ma5_support = True
                sr.support_levels.append(ind.ma5)
        
        # 检查 MA10 支撑
        if ind.ma10 > 0:
            ma10_distance = abs(price - ind.ma10) / ind.ma10
            if ma10_distance <= self.MA_SUPPORT_TOLERANCE and price >= ind.ma10:
                sr.ma10_support = True
                sr.support_levels.append(ind.ma10)
        
        # MA20 作为重要支撑
        if ind.ma20 > 0 and price >= ind.ma20:
            sr.support_levels.append(ind.ma20)
        
        # 近期高点作为压力
        if len(df) >= 20:
            recent_high = df['high'].iloc[-20:].max()
            if recent_high > price:
                sr.resistance_levels.append(recent_high)
    
    def _generate_signal(self, result: TrendAnalysisResult) -> None:
        """生成买入信号"""
        ind = result.indicators
        score = 0
        reasons = []
        risks = []
        
        # === 趋势评分（40分）===
        trend_scores = {
            TrendStatus.STRONG_BULL.value: 40,
            TrendStatus.BULL.value: 35,
            TrendStatus.WEAK_BULL.value: 25,
            TrendStatus.CONSOLIDATION.value: 15,
            TrendStatus.WEAK_BEAR.value: 10,
            TrendStatus.BEAR.value: 5,
            TrendStatus.STRONG_BEAR.value: 0,
        }
        trend_score = trend_scores.get(result.trend_status, 15)
        score += trend_score
        
        if result.trend_status in [TrendStatus.STRONG_BULL.value, TrendStatus.BULL.value]:
            reasons.append(f"✅ {result.trend_status}，顺势做多")
        elif result.trend_status in [TrendStatus.BEAR.value, TrendStatus.STRONG_BEAR.value]:
            risks.append(f"⚠️ {result.trend_status}，不宜做多")
        
        # === 乖离率评分（30分）===
        bias = ind.bias_ma5
        if bias < 0:
            if bias > -3:
                score += 30
                reasons.append(f"✅ 价格略低于MA5({bias:.1f}%)，回踩买点")
            elif bias > -5:
                score += 25
                reasons.append(f"✅ 价格回踩MA5({bias:.1f}%)，观察支撑")
            else:
                score += 10
                risks.append(f"⚠️ 乖离率过大({bias:.1f}%)，可能破位")
        elif bias < 2:
            score += 28
            reasons.append(f"✅ 价格贴近MA5({bias:.1f}%)，介入好时机")
        elif bias < self.BIAS_THRESHOLD:
            score += 20
            reasons.append(f"⚡ 价格略高于MA5({bias:.1f}%)，可小仓介入")
        else:
            score += 5
            risks.append(f"❌ 乖离率过高({bias:.1f}% > 5%)，严禁追高！")
        
        # === 量能评分（20分）===
        volume_scores = {
            VolumeStatus.SHRINK_VOLUME_DOWN.value: 20,
            VolumeStatus.HEAVY_VOLUME_UP.value: 15,
            VolumeStatus.NORMAL.value: 12,
            VolumeStatus.SHRINK_VOLUME_UP.value: 8,
            VolumeStatus.HEAVY_VOLUME_DOWN.value: 0,
        }
        vol_score = volume_scores.get(ind.volume_status, 10)
        score += vol_score
        
        if ind.volume_status == VolumeStatus.SHRINK_VOLUME_DOWN.value:
            reasons.append("✅ 缩量回调，主力洗盘")
        elif ind.volume_status == VolumeStatus.HEAVY_VOLUME_DOWN.value:
            risks.append("⚠️ 放量下跌，注意风险")
        
        # === 支撑评分（10分）===
        sr = result.support_resistance
        if sr.ma5_support:
            score += 5
            reasons.append("✅ MA5支撑有效")
        if sr.ma10_support:
            score += 5
            reasons.append("✅ MA10支撑有效")
        
        # === 综合判断 ===
        result.signal_score = score
        result.signal_reasons = reasons
        result.risk_factors = risks
        
        # 生成买入信号
        if score >= 80 and result.trend_status in [TrendStatus.STRONG_BULL.value, TrendStatus.BULL.value]:
            result.buy_signal = BuySignal.STRONG_BUY.value
        elif score >= 65 and result.trend_status in [TrendStatus.STRONG_BULL.value, TrendStatus.BULL.value, TrendStatus.WEAK_BULL.value]:
            result.buy_signal = BuySignal.BUY.value
        elif score >= 50:
            result.buy_signal = BuySignal.HOLD.value
        elif score >= 35:
            result.buy_signal = BuySignal.WAIT.value
        elif result.trend_status in [TrendStatus.BEAR.value, TrendStatus.STRONG_BEAR.value]:
            result.buy_signal = BuySignal.STRONG_SELL.value
        else:
            result.buy_signal = BuySignal.SELL.value


# =============================================================================
# OpenClaw 工具函数
# =============================================================================

def analyze_trend(
    stock_code: str,
    days: int = 60,
    format_type: str = "dict"  # "dict", "json", "prompt"
) -> Union[Dict[str, Any], str]:
    """
    执行趋势分析（OpenClaw 工具）
    
    Args:
        stock_code: 股票代码
        days: 分析用的历史数据天数
        format_type: 输出格式
            - "dict": Python 字典（默认）
            - "json": JSON 字符串
            - "prompt": 格式化的提示词文本
            
    Returns:
        根据 format_type 返回不同格式的分析结果
    """
    try:
        # 获取数据
        data = get_stock_data(stock_code, days=days)
        
        if not data['success']:
            error_result = {
                'success': False,
                'code': stock_code,
                'error': data.get('error_message', '获取数据失败'),
            }
            if format_type == 'json':
                return json.dumps(error_result, ensure_ascii=False)
            elif format_type == 'prompt':
                return f"分析失败: {error_result['error']}"
            return error_result
        
        # 转换为 StockDailyData 对象
        daily_data = [StockDailyData(**d) for d in data['daily_data']]
        
        # 分析
        analyzer = StockTrendAnalyzer()
        name = data.get('name', '')
        result = analyzer.analyze(daily_data, stock_code, name)
        
        if format_type == 'json':
            return result.to_json()
        elif format_type == 'prompt':
            return result.to_llm_prompt()
        else:
            return result.to_dict()
            
    except Exception as e:
        logger.error(f"分析 {stock_code} 失败: {e}")
        error_result = {
            'success': False,
            'code': stock_code,
            'error': str(e),
        }
        if format_type == 'json':
            return json.dumps(error_result, ensure_ascii=False)
        elif format_type == 'prompt':
            return f"分析失败: {str(e)}"
        return error_result


def batch_analyze(
    stock_codes: List[str],
    days: int = 60,
    max_workers: int = 3
) -> List[Dict[str, Any]]:
    """
    批量分析多只股票（OpenClaw 工具）
    
    Args:
        stock_codes: 股票代码列表
        days: 分析用的历史数据天数
        max_workers: 并发数（建议保持低并发防封禁）
        
    Returns:
        每只股票的分析结果字典列表
    """
    from concurrent.futures import ThreadPoolExecutor
    
    results = []
    
    def analyze_one(code):
        return analyze_trend(code, days=days, format_type='dict')
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(analyze_one, stock_codes))
    
    # 按评分排序
    def get_score(r):
        if isinstance(r, dict) and 'signal_score' in r:
            return r['signal_score']
        return 0
    
    results.sort(key=get_score, reverse=True)
    
    return results


def analyze_for_llm(stock_code: str, days: int = 60) -> str:
    """
    获取完整的股票分析结果（数据 + 技术分析），格式化为 LLM 提示词
    
    Args:
        stock_code: 股票代码
        days: 历史数据天数
        
    Returns:
        完整的分析文本，可直接作为 LLM 的输入
    """
    from data_fetcher import get_stock_data_for_llm
    
    # 获取原始数据
    data_prompt = get_stock_data_for_llm(stock_code, days=days, format_type='prompt')
    
    # 获取技术分析
    analysis_prompt = analyze_trend(stock_code, days=days, format_type='prompt')
    
    # 合并
    full_prompt = f"""{data_prompt}

---

{analysis_prompt}

---

## 请基于以上数据给出投资建议

请分析：
1. 当前趋势状态如何？是否适合买入？
2. 如果适合买入，理想的买入价位是多少？
3. 主要风险点有哪些？
4. 建议的仓位和止损位？
"""
    
    return full_prompt


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("趋势分析器测试")
    print("=" * 60)
    
    # 测试单只股票分析
    print("\n1. 获取字典格式结果:")
    result = analyze_trend('600519', days=30, format_type='dict')
    if result.get('success') != False:
        print(f"股票: {result['code']} {result['name']}")
        print(f"趋势: {result['trend_status']}")
        print(f"买入信号: {result['buy_signal']}")
        print(f"综合评分: {result['signal_score']}/100")
    else:
        print(f"失败: {result.get('error')}")
    
    # 测试 JSON 格式
    print("\n2. 获取 JSON 格式结果（片段）:")
    json_result = analyze_trend('600519', days=30, format_type='json')
    print(json_result[:500] + "...")
    
    # 测试 Prompt 格式
    print("\n3. 获取 Prompt 格式结果:")
    prompt = analyze_trend('600519', days=30, format_type='prompt')
    print(prompt)
    
    # 测试完整分析（数据 + 技术分析）
    print("\n" + "=" * 60)
    print("完整分析（数据 + 技术分析）")
    print("=" * 60)
    full = analyze_for_llm('600519', days=30)
    print(full[:1000] + "...")
