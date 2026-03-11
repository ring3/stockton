# -*- coding: utf-8 -*-
"""
数据源接口定义

定义所有数据源需要实现的统一接口，以及返回数据结构的标准格式。
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import pandas as pd


# =============================================================================
# 统一返回数据结构定义
# =============================================================================

@dataclass
class IndexComponent:
    """指数成分股数据"""
    stock_code: str          # 股票代码
    stock_name: str          # 股票名称
    weight: float = 0.0      # 权重（可选）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'weight': self.weight,
        }


@dataclass
class StockBasicInfo:
    """股票基本信息（用于股票池）"""
    code: str                # 股票代码
    name: str                # 股票名称
    market: str = ""         # 所属市场（沪市/深市/创业板/科创板）
    industry: str = ""       # 所属行业
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'market': self.market,
            'industry': self.industry,
        }


@dataclass
class FinancialReport:
    """财务报表数据（单期）"""
    report_date: str         # 报告期（YYYY-MM-DD）
    report_type: str         # 报表类型（利润表/资产负债表/现金流量表）
    
    # 利润表关键字段
    revenue: Optional[float] = None              # 营业收入
    operating_profit: Optional[float] = None     # 营业利润
    net_profit: Optional[float] = None           # 净利润
    
    # 资产负债表关键字段
    total_assets: Optional[float] = None         # 总资产
    total_liabilities: Optional[float] = None    # 总负债
    shareholders_equity: Optional[float] = None  # 股东权益
    
    # 现金流量表关键字段
    operating_cash_flow: Optional[float] = None  # 经营活动现金流
    investing_cash_flow: Optional[float] = None  # 投资活动现金流
    financing_cash_flow: Optional[float] = None  # 筹资活动现金流
    
    # 原始数据（其他字段）
    raw_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'report_date': self.report_date,
            'report_type': self.report_type,
        }
        if self.revenue is not None:
            result['revenue'] = self.revenue
        if self.operating_profit is not None:
            result['operating_profit'] = self.operating_profit
        if self.net_profit is not None:
            result['net_profit'] = self.net_profit
        if self.total_assets is not None:
            result['total_assets'] = self.total_assets
        if self.total_liabilities is not None:
            result['total_liabilities'] = self.total_liabilities
        if self.shareholders_equity is not None:
            result['shareholders_equity'] = self.shareholders_equity
        if self.operating_cash_flow is not None:
            result['operating_cash_flow'] = self.operating_cash_flow
        return result


@dataclass
class FinancialIndicators:
    """财务分析指标"""
    stock_code: str
    stock_name: str = ""
    report_date: str = ""
    
    # 盈利能力
    roe: float = 0.0                 # 净资产收益率(%)
    roa: float = 0.0                 # 总资产收益率(%)
    gross_margin: float = 0.0        # 毛利率(%)
    net_margin: float = 0.0          # 净利率(%)
    
    # 成长能力
    revenue_growth: float = 0.0      # 营收增长率(%)
    profit_growth: float = 0.0       # 净利润增长率(%)
    
    # 偿债能力
    debt_ratio: float = 0.0          # 资产负债率(%)
    current_ratio: float = 0.0       # 流动比率
    
    # 估值指标
    pe_ratio: float = 0.0            # 市盈率
    pb_ratio: float = 0.0            # 市净率
    
    # 原始数据
    raw_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'report_date': self.report_date,
            'roe': self.roe,
            'roa': self.roa,
            'gross_margin': self.gross_margin,
            'net_margin': self.net_margin,
            'revenue_growth': self.revenue_growth,
            'profit_growth': self.profit_growth,
            'debt_ratio': self.debt_ratio,
            'current_ratio': self.current_ratio,
            'pe_ratio': self.pe_ratio,
            'pb_ratio': self.pb_ratio,
        }


@dataclass
class IndustryInfo:
    """行业/板块信息"""
    name: str                # 行业名称
    code: Optional[str] = None  # 行业代码（可选）
    change_pct: float = 0.0  # 涨跌幅（可选）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'code': self.code,
            'change_pct': self.change_pct,
        }


# =============================================================================
# 数据源接口抽象基类（扩展版）
# =============================================================================

class DataSourceInterface(ABC):
    """
    完整的数据源接口定义
    
    所有数据源（Efinance、Akshare、Baostock等）都需要实现这些接口。
    如果某个数据源不支持某个接口，返回空列表/字典/DataFrame，并在返回结果中
    包含 'unsupported' 标记，以便调用端处理。
    """
    
    name: str = "BaseInterface"
    
    # -------------------------------------------------------------------------
    # 基础数据接口（必须实现）
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def get_daily_data(self, stock_code: str, days: int = 60) -> pd.DataFrame:
        """获取日线数据（含技术指标）"""
        pass
    
    @abstractmethod
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取实时行情"""
        pass
    
    # -------------------------------------------------------------------------
    # 股票筛选相关接口
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def get_index_components(self, index_code: str) -> List[IndexComponent]:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码，如 '000300', '000905'
            
        Returns:
            IndexComponent 列表，如果不支持返回空列表
        """
        pass
    
    @abstractmethod
    def get_stock_pool(self, market: str = "A股") -> List[StockBasicInfo]:
        """
        获取市场股票池
        
        Args:
            market: 市场范围（"A股", "沪市", "深市", "创业板", "科创板"）
            
        Returns:
            StockBasicInfo 列表，如果不支持返回空列表
        """
        pass
    
    @abstractmethod
    def get_industry_stocks(self, industry_name: str) -> List[StockBasicInfo]:
        """
        获取行业成分股
        
        Args:
            industry_name: 行业名称，如 "半导体", "白酒"
            
        Returns:
            StockBasicInfo 列表，如果不支持返回空列表
        """
        pass
    
    @abstractmethod
    def get_industry_list(self) -> List[IndustryInfo]:
        """
        获取行业/板块列表
        
        Returns:
            IndustryInfo 列表，如果不支持返回空列表
        """
        pass
    
    # -------------------------------------------------------------------------
    # 财务分析相关接口
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def get_financial_report(
        self, 
        stock_code: str, 
        report_type: str = "利润表"
    ) -> List[FinancialReport]:
        """
        获取财务报表
        
        Args:
            stock_code: 股票代码
            report_type: 报表类型（"利润表", "资产负债表", "现金流量表"）
            
        Returns:
            FinancialReport 列表（多期数据），如果不支持返回空列表
        """
        pass
    
    @abstractmethod
    def get_financial_indicators(self, stock_code: str) -> Optional[FinancialIndicators]:
        """
        获取财务分析指标
        
        Args:
            stock_code: 股票代码
            
        Returns:
            FinancialIndicators 对象，如果不支持返回 None
        """
        pass
    
    # -------------------------------------------------------------------------
    # 市场数据接口
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def get_market_indices(self) -> pd.DataFrame:
        """获取主要指数行情"""
        pass
    
    @abstractmethod
    def get_market_overview(self) -> pd.DataFrame:
        """获取市场概览（全市场股票实时数据）"""
        pass
    
    @abstractmethod
    def get_sector_rankings(self) -> pd.DataFrame:
        """获取板块排行"""
        pass
    
    # -------------------------------------------------------------------------
    # 特色数据接口（可选实现）
    # -------------------------------------------------------------------------
    
    @abstractmethod
    def get_chip_distribution(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取筹码分布（A股特有）"""
        pass
    
    @abstractmethod
    def get_futures_basis(self) -> pd.DataFrame:
        """获取股指期货贴水数据"""
        pass
    
    @abstractmethod
    def get_option_chain(self, underlying_code: str) -> pd.DataFrame:
        """获取期权链数据"""
        pass
