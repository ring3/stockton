# -*- coding: utf-8 -*-
"""
财务分析模块

提供个股财务数据分析功能：
1. 财务报表数据获取（利润表、资产负债表、现金流量表）
2. 关键财务指标计算（ROE、毛利率、净利率、资产负债率等）
3. 财务健康度评分
4. 成长性和估值分析
"""

import logging
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# 导入数据库管理器
try:
    from .storage import DatabaseManager
    _HAS_DB = True
except ImportError:
    _HAS_DB = False
    DatabaseManager = None


@dataclass
class FinancialIndicators:
    """财务指标数据类"""
    # 股票基本信息
    stock_code: str
    stock_name: str = ""
    report_date: str = ""  # 报告期
    
    # 盈利能力指标
    roe: float = 0.0  # 净资产收益率 (%)
    roa: float = 0.0  # 总资产收益率 (%)
    gross_margin: float = 0.0  # 毛利率 (%)
    net_margin: float = 0.0  # 净利率 (%)
    operating_margin: float = 0.0  # 营业利润率 (%)
    
    # 成长能力指标
    revenue_growth: float = 0.0  # 营业收入同比增长率 (%)
    profit_growth: float = 0.0  # 净利润同比增长率 (%)
    net_asset_growth: float = 0.0  # 净资产增长率 (%)
    
    # 偿债能力指标
    debt_ratio: float = 0.0  # 资产负债率 (%)
    current_ratio: float = 0.0  # 流动比率
    quick_ratio: float = 0.0  # 速动比率
    
    # 运营效率指标
    asset_turnover: float = 0.0  # 总资产周转率 (次)
    inventory_turnover: float = 0.0  # 存货周转率 (次)
    receivables_turnover: float = 0.0  # 应收账款周转率 (次)
    
    # 现金流指标
    operating_cash_flow: float = 0.0  # 经营活动现金流 (亿元)
    free_cash_flow: float = 0.0  # 自由现金流 (亿元)
    cash_conversion_cycle: float = 0.0  # 现金转换周期 (天)
    
    # 估值指标
    pe_ratio: float = 0.0  # 市盈率
    pb_ratio: float = 0.0  # 市净率
    ps_ratio: float = 0.0  # 市销率
    dividend_yield: float = 0.0  # 股息率 (%)
    
    # 综合评分
    profitability_score: int = 0  # 盈利能力评分 (0-100)
    growth_score: int = 0  # 成长能力评分 (0-100)
    safety_score: int = 0  # 财务安全评分 (0-100)
    valuation_score: int = 0  # 估值吸引力评分 (0-100)
    total_score: int = 0  # 综合评分 (0-100)
    
    # 原始数据
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'report_date': self.report_date,
            '盈利能力': {
                'ROE': round(self.roe, 2),
                'ROA': round(self.roa, 2),
                '毛利率': round(self.gross_margin, 2),
                '净利率': round(self.net_margin, 2),
                '营业利润率': round(self.operating_margin, 2),
            },
            '成长能力': {
                '营收增长率': round(self.revenue_growth, 2),
                '净利润增长率': round(self.profit_growth, 2),
                '净资产增长率': round(self.net_asset_growth, 2),
            },
            '偿债能力': {
                '资产负债率': round(self.debt_ratio, 2),
                '流动比率': round(self.current_ratio, 2),
                '速动比率': round(self.quick_ratio, 2),
            },
            '运营效率': {
                '总资产周转率': round(self.asset_turnover, 2),
                '存货周转率': round(self.inventory_turnover, 2),
                '应收账款周转率': round(self.receivables_turnover, 2),
            },
            '现金流': {
                '经营现金流': round(self.operating_cash_flow, 2),
                '自由现金流': round(self.free_cash_flow, 2),
            },
            '估值指标': {
                'PE': round(self.pe_ratio, 2),
                'PB': round(self.pb_ratio, 2),
                'PS': round(self.ps_ratio, 2),
                '股息率': round(self.dividend_yield, 2),
            },
            '综合评分': {
                '盈利能力': self.profitability_score,
                '成长能力': self.growth_score,
                '财务安全': self.safety_score,
                '估值吸引力': self.valuation_score,
                '总评分': self.total_score,
            },
            'data_source': 'akshare',
        }
    
    def to_llm_prompt(self) -> str:
        """转换为LLM提示词格式"""
        lines = [
            f"## 财务分析报告 - {self.stock_name}({self.stock_code})",
            f"报告期: {self.report_date}",
            "",
            "### 盈利能力",
            f"- ROE(净资产收益率): {self.roe:.2f}% {'优秀' if self.roe > 15 else '良好' if self.roe > 10 else '一般'}",
            f"- ROA(总资产收益率): {self.roa:.2f}%",
            f"- 毛利率: {self.gross_margin:.2f}%",
            f"- 净利率: {self.net_margin:.2f}%",
            "",
            "### 成长能力",
            f"- 营收增长率: {self.revenue_growth:.2f}% {'高成长' if self.revenue_growth > 20 else '稳健' if self.revenue_growth > 10 else '缓慢'}",
            f"- 净利润增长率: {self.profit_growth:.2f}%",
            "",
            "### 偿债能力",
            f"- 资产负债率: {self.debt_ratio:.2f}% {'安全' if self.debt_ratio < 50 else '适中' if self.debt_ratio < 70 else '偏高'}",
            f"- 流动比率: {self.current_ratio:.2f}",
            "",
            "### 估值水平",
            f"- PE(市盈率): {self.pe_ratio:.2f} {'低估' if self.pe_ratio < 20 else '合理' if self.pe_ratio < 40 else '高估'}",
            f"- PB(市净率): {self.pb_ratio:.2f}",
            f"- 股息率: {self.dividend_yield:.2f}%",
            "",
            "### 综合评分",
            f"- 总评分: {self.total_score}/100 {'买入' if self.total_score >= 80 else '关注' if self.total_score >= 60 else '观望'}",
            f"- 盈利能力: {self.profitability_score}/100",
            f"- 成长能力: {self.growth_score}/100",
            f"- 财务安全: {self.safety_score}/100",
            f"- 估值吸引力: {self.valuation_score}/100",
        ]
        return "\n".join(lines)


class FinancialAnalyzer:
    """财务分析器"""
    
    def __init__(self):
        # 初始化数据源管理器（优先使用，替代直接akshare调用）
        self._data_manager = None
        try:
            from .data_provider import DataFetcherManager
            self._data_manager = DataFetcherManager()
            logger.debug("财务分析器已初始化数据源管理器")
        except Exception as e:
            logger.warning(f"财务分析器数据源管理器初始化失败: {e}")
        
        # 保留akshare作为备选
        try:
            import akshare as ak
            self._ak = ak
        except ImportError:
            logger.warning("akshare未安装")
            self._ak = None
        
        # 初始化数据库连接
        self._db = None
        if _HAS_DB:
            try:
                self._db = DatabaseManager.get_instance()
                logger.debug("财务分析器已连接数据库")
            except Exception as e:
                logger.debug(f"财务分析器数据库连接失败: {e}")
    
    def _safe_float(self, value, default=0.0) -> float:
        """安全转换为float"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_financial_data(self, stock_code: str) -> Optional[FinancialIndicators]:
        """
        获取个股完整财务数据（使用统一数据源接口）
        
        Args:
            stock_code: 股票代码，如 '600519'
            
        Returns:
            FinancialIndicators对象，失败返回None
        """
        if self._data_manager is None and self._ak is None:
            logger.error("无可用数据源")
            return None
        
        try:
            logger.info(f"[财务分析] 获取 {stock_code} 财务数据...")
            
            # 获取关键指标（先获取以从中提取股票名称）
            indicators_df = self._get_key_indicators(stock_code)
            
            # 获取股票名称（从财务指标表）
            stock_name = self._get_stock_name(stock_code, indicators_df)
            
            # 获取三大报表
            profit_df = self._get_profit_statement(stock_code)
            balance_df = self._get_balance_sheet(stock_code)
            cashflow_df = self._get_cash_flow(stock_code)
            
            # 计算财务指标
            fin_indicators = self._calculate_indicators(
                stock_code, stock_name, profit_df, balance_df, cashflow_df, indicators_df
            )
            
            logger.info(f"[财务分析] {stock_code} 财务数据获取完成，评分: {fin_indicators.total_score}")
            return fin_indicators
            
        except Exception as e:
            logger.error(f"[财务分析] 获取 {stock_code} 财务数据失败: {e}")
            return None
    
    def _get_stock_name(self, stock_code: str, indicators_df: Optional[pd.DataFrame] = None) -> str:
        """
        获取股票名称
        
        由于网络限制，不再使用 stock_individual_info_em 实时接口。
        优先从数据库获取，其次从财务指标表获取。
        """
        # 方法1：从数据库获取（最快）
        if self._db:
            try:
                name = self._db.get_stock_name(stock_code)
                if name:
                    return name
            except Exception as e:
                logger.debug(f"从数据库获取股票名称失败: {e}")
        
        # 方法2：从财务指标表中获取
        if indicators_df is not None and not indicators_df.empty:
            try:
                name = indicators_df.iloc[0].get('股票简称', '')
                if name:
                    return str(name)
            except Exception:
                pass
        
        return ""  # 无法获取时返回空字符串
    
    def _get_profit_statement(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取利润表（使用统一数据源接口）"""
        # 优先使用数据源管理器
        if self._data_manager:
            try:
                df, source = self._data_manager.get_financial_report(stock_code, "利润表")
                if df is not None and not df.empty:
                    logger.debug(f"[财务分析] 从 {source} 获取利润表成功")
                    return df
            except Exception as e:
                logger.debug(f"数据源管理器获取利润表失败: {e}")
        
        # 备选：直接使用akshare
        if self._ak:
            try:
                # 判断市场
                if stock_code.startswith('6'):
                    stock_code_full = f"{stock_code}.SH"
                else:
                    stock_code_full = f"{stock_code}.SZ"
                
                df = self._ak.stock_financial_report_sina(stock=stock_code_full, symbol="利润表")
                return df
            except Exception as e:
                logger.debug(f"akshare获取利润表失败: {e}")
        
        return None
    
    def _get_balance_sheet(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取资产负债表（使用统一数据源接口）"""
        # 优先使用数据源管理器
        if self._data_manager:
            try:
                df, source = self._data_manager.get_financial_report(stock_code, "资产负债表")
                if df is not None and not df.empty:
                    logger.debug(f"[财务分析] 从 {source} 获取资产负债表成功")
                    return df
            except Exception as e:
                logger.debug(f"数据源管理器获取资产负债表失败: {e}")
        
        # 备选：直接使用akshare
        if self._ak:
            try:
                if stock_code.startswith('6'):
                    stock_code_full = f"{stock_code}.SH"
                else:
                    stock_code_full = f"{stock_code}.SZ"
                
                df = self._ak.stock_financial_report_sina(stock=stock_code_full, symbol="资产负债表")
                return df
            except Exception as e:
                logger.debug(f"akshare获取资产负债表失败: {e}")
        
        return None
    
    def _get_cash_flow(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取现金流量表（使用统一数据源接口）"""
        # 优先使用数据源管理器
        if self._data_manager:
            try:
                df, source = self._data_manager.get_financial_report(stock_code, "现金流量表")
                if df is not None and not df.empty:
                    logger.debug(f"[财务分析] 从 {source} 获取现金流量表成功")
                    return df
            except Exception as e:
                logger.debug(f"数据源管理器获取现金流量表失败: {e}")
        
        # 备选：直接使用akshare
        if self._ak:
            try:
                if stock_code.startswith('6'):
                    stock_code_full = f"{stock_code}.SH"
                else:
                    stock_code_full = f"{stock_code}.SZ"
                
                df = self._ak.stock_financial_report_sina(stock=stock_code_full, symbol="现金流量表")
                return df
            except Exception as e:
                logger.debug(f"akshare获取现金流量表失败: {e}")
        
        return None
    
    def _get_key_indicators(self, stock_code: str) -> Optional[pd.DataFrame]:
        """获取关键财务指标（使用统一数据源接口）"""
        # 优先使用数据源管理器
        if self._data_manager:
            try:
                df, source = self._data_manager.get_financial_indicators(stock_code)
                if df is not None and not df.empty:
                    logger.debug(f"[财务分析] 从 {source} 获取财务指标成功")
                    return df
            except Exception as e:
                logger.debug(f"数据源管理器获取财务指标失败: {e}")
        
        # 备选：直接使用akshare
        if self._ak:
            try:
                df = self._ak.stock_financial_analysis_indicator(symbol=stock_code)
                return df
            except Exception as e:
                logger.debug(f"akshare获取关键指标失败: {e}")
        
        return None
    
    def _calculate_indicators(
        self, 
        stock_code: str, 
        stock_name: str,
        profit_df: Optional[pd.DataFrame],
        balance_df: Optional[pd.DataFrame],
        cashflow_df: Optional[pd.DataFrame],
        indicators_df: Optional[pd.DataFrame]
    ) -> FinancialIndicators:
        """计算财务指标"""
        
        fin = FinancialIndicators(stock_code=stock_code, stock_name=stock_name)
        
        # 从关键指标表提取数据
        if indicators_df is not None and not indicators_df.empty:
            latest = indicators_df.iloc[0]
            fin.report_date = str(latest.get('报告期', ''))
            
            # 盈利能力
            fin.roe = self._safe_float(latest.get('净资产收益率(%)'), 0)
            fin.roa = self._safe_float(latest.get('总资产报酬率(%)'), 0)
            fin.gross_margin = self._safe_float(latest.get('销售毛利率(%)'), 0)
            fin.net_margin = self._safe_float(latest.get('销售净利率(%)'), 0)
            
            # 成长能力
            fin.revenue_growth = self._safe_float(latest.get('营业收入增长率(%)'), 0)
            fin.profit_growth = self._safe_float(latest.get('净利润增长率(%)'), 0)
            fin.net_asset_growth = self._safe_float(latest.get('净资产增长率(%)'), 0)
            
            # 偿债能力
            fin.debt_ratio = self._safe_float(latest.get('资产负债率(%)'), 0)
            fin.current_ratio = self._safe_float(latest.get('流动比率'), 0)
            fin.quick_ratio = self._safe_float(latest.get('速动比率'), 0)
            
            # 运营效率
            fin.asset_turnover = self._safe_float(latest.get('总资产周转率(次)'), 0)
            fin.inventory_turnover = self._safe_float(latest.get('存货周转率(次)'), 0)
            fin.receivables_turnover = self._safe_float(latest.get('应收账款周转率(次)'), 0)
        
        # 从利润表和资产负债表计算更多指标
        if profit_df is not None and not profit_df.empty and balance_df is not None and not balance_df.empty:
            try:
                # 获取最新一期数据
                profit_latest = profit_df.iloc[0]
                balance_latest = balance_df.iloc[0]
                
                # 营业利润率
                operating_profit = self._safe_float(profit_latest.get('营业利润'), 0)
                revenue = self._safe_float(profit_latest.get('营业收入'), 0)
                if revenue > 0:
                    fin.operating_margin = (operating_profit / revenue) * 100
                
            except Exception as e:
                logger.debug(f"计算额外指标失败: {e}")
        
        # 从现金流量表获取现金流数据
        if cashflow_df is not None and not cashflow_df.empty:
            try:
                cash_latest = cashflow_df.iloc[0]
                fin.operating_cash_flow = self._safe_float(cash_latest.get('经营活动产生的现金流量净额'), 0) / 1e8  # 转为亿元
            except Exception as e:
                logger.debug(f"获取现金流数据失败: {e}")
        
        # 获取估值指标（从财务分析表）
        # [注意] 由于网络限制，不再使用 stock_individual_info_em 实时接口
        # PE/PB/股息率从财务分析指标表中获取（可能不是最新实时值）
        if indicators_df is not None and not indicators_df.empty:
            try:
                latest = indicators_df.iloc[0]
                # 尝试从财务表中获取估值指标
                fin.pe_ratio = self._safe_float(latest.get('市盈率'), 0)
                fin.pb_ratio = self._safe_float(latest.get('市净率'), 0)
                # 股息率通常不在财务分析表中，保持默认值0
                fin.dividend_yield = 0
            except Exception as e:
                logger.debug(f"从财务表获取估值指标失败: {e}")
        
        # 计算综合评分
        fin = self._calculate_score(fin)
        
        return fin
    
    def _calculate_score(self, fin: FinancialIndicators) -> FinancialIndicators:
        """计算综合评分"""
        
        # 盈利能力评分 (0-25分)
        if fin.roe >= 20:
            fin.profitability_score += 10
        elif fin.roe >= 15:
            fin.profitability_score += 8
        elif fin.roe >= 10:
            fin.profitability_score += 6
        elif fin.roe >= 5:
            fin.profitability_score += 3
        
        if fin.gross_margin >= 40:
            fin.profitability_score += 8
        elif fin.gross_margin >= 30:
            fin.profitability_score += 6
        elif fin.gross_margin >= 20:
            fin.profitability_score += 4
        elif fin.gross_margin >= 10:
            fin.profitability_score += 2
        
        if fin.net_margin >= 20:
            fin.profitability_score += 7
        elif fin.net_margin >= 15:
            fin.profitability_score += 5
        elif fin.net_margin >= 10:
            fin.profitability_score += 3
        elif fin.net_margin >= 5:
            fin.profitability_score += 1
        
        fin.profitability_score = min(25, fin.profitability_score)
        
        # 成长能力评分 (0-25分)
        if fin.revenue_growth >= 30:
            fin.growth_score += 10
        elif fin.revenue_growth >= 20:
            fin.growth_score += 8
        elif fin.revenue_growth >= 10:
            fin.growth_score += 5
        elif fin.revenue_growth >= 0:
            fin.growth_score += 2
        
        if fin.profit_growth >= 30:
            fin.growth_score += 10
        elif fin.profit_growth >= 20:
            fin.growth_score += 8
        elif fin.profit_growth >= 10:
            fin.growth_score += 5
        elif fin.profit_growth >= 0:
            fin.growth_score += 2
        
        if fin.net_asset_growth >= 15:
            fin.growth_score += 5
        elif fin.net_asset_growth >= 10:
            fin.growth_score += 3
        elif fin.net_asset_growth >= 5:
            fin.growth_score += 1
        
        fin.growth_score = min(25, fin.growth_score)
        
        # 财务安全评分 (0-25分)
        if fin.debt_ratio <= 40:
            fin.safety_score += 10
        elif fin.debt_ratio <= 50:
            fin.safety_score += 8
        elif fin.debt_ratio <= 60:
            fin.safety_score += 6
        elif fin.debt_ratio <= 70:
            fin.safety_score += 3
        
        if fin.current_ratio >= 2:
            fin.safety_score += 8
        elif fin.current_ratio >= 1.5:
            fin.safety_score += 6
        elif fin.current_ratio >= 1:
            fin.safety_score += 3
        
        if fin.operating_cash_flow > 0:
            fin.safety_score += 7
        
        fin.safety_score = min(25, fin.safety_score)
        
        # 估值吸引力评分 (0-25分)
        if 0 < fin.pe_ratio <= 15:
            fin.valuation_score += 15
        elif 0 < fin.pe_ratio <= 25:
            fin.valuation_score += 10
        elif 0 < fin.pe_ratio <= 40:
            fin.valuation_score += 5
        
        if 0 < fin.pb_ratio <= 1.5:
            fin.valuation_score += 7
        elif 0 < fin.pb_ratio <= 3:
            fin.valuation_score += 4
        
        if fin.dividend_yield >= 3:
            fin.valuation_score += 3
        elif fin.dividend_yield >= 1:
            fin.valuation_score += 1
        
        fin.valuation_score = min(25, fin.valuation_score)
        
        # 总评分
        fin.total_score = fin.profitability_score + fin.growth_score + fin.safety_score + fin.valuation_score
        
        return fin


# 便捷函数
def analyze_financial(stock_code: str, format_type: str = "dict") -> Optional[Union[Dict, str]]:
    """
    分析个股财务状况（OpenClaw工具函数）
    
    Args:
        stock_code: 股票代码
        format_type: 输出格式 ("dict", "json", "prompt")
        
    Returns:
        财务分析结果
    """
    analyzer = FinancialAnalyzer()
    result = analyzer.get_financial_data(stock_code)
    
    if result is None:
        error_msg = f"获取 {stock_code} 财务数据失败"
        if format_type == "json":
            import json
            return json.dumps({'success': False, 'error': error_msg}, ensure_ascii=False)
        elif format_type == "prompt":
            return error_msg
        else:
            return {'success': False, 'error': error_msg}
    
    if format_type == "json":
        import json
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    elif format_type == "prompt":
        return result.to_llm_prompt()
    else:
        return result.to_dict()
