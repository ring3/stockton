# -*- coding: utf-8 -*-
"""
股票筛选器（选股功能）

提供多因子选股模型：
1. 价值选股：低PE、低PB、高股息
2. 成长选股：高营收增长、高利润增长
3. 质量选股：高ROE、低负债、稳定现金流
4. 技术选股：多头排列、突破形态
5. 自定义条件筛选
"""

import logging
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# 导入数据库管理器（支持相对导入和绝对导入）
_HAS_DB = False
DatabaseManager = None

try:
    # 尝试相对导入（在包内使用时）
    from .storage import DatabaseManager
    _HAS_DB = True
except ImportError:
    try:
        # 尝试绝对导入（独立脚本使用时）
        from storage import DatabaseManager
        _HAS_DB = True
    except ImportError:
        try:
            # 尝试从 skills.stockton.scripts 导入
            from skills.stockton.scripts.storage import DatabaseManager
            _HAS_DB = True
        except ImportError:
            _HAS_DB = False
            DatabaseManager = None


class ScreenFactor(Enum):
    """筛选因子类型"""
    # 估值因子
    PE_LOW = "pe_low"  # 低市盈率
    PB_LOW = "pb_low"  # 低市净率
    HIGH_DIVIDEND = "high_dividend"  # 高股息率
    
    # 成长因子
    HIGH_GROWTH = "high_growth"  # 高成长
    HIGH_REVENUE_GROWTH = "high_revenue_growth"  # 高营收增长
    HIGH_PROFIT_GROWTH = "high_profit_growth"  # 高利润增长
    
    # 质量因子
    HIGH_ROE = "high_roe"  # 高ROE
    LOW_DEBT = "low_debt"  # 低负债率
    POSITIVE_CASHFLOW = "positive_cashflow"  # 正现金流
    
    # 技术因子
    BULLISH_MA = "bullish_ma"  # 多头排列
    BREAKOUT = "breakout"  # 突破形态
    HIGH_VOLUME = "high_volume"  # 放量
    
    # 动量因子
    MOMENTUM = "momentum"  # 价格动量（纯动量策略）
    DUAL_MOMENTUM = "dual_momentum"  # 双动量策略（绝对+相对动量）
    
    # 综合因子
    VALUE = "value"  # 价值投资
    GROWTH = "growth"  # 成长投资
    QUALITY = "quality"  # 质量投资
    BLUE_CHIP = "blue_chip"  # 蓝筹股
    SMALL_CAP_GROWTH = "small_cap_growth"  # 小盘成长


@dataclass
class ScreenCriteria:
    """筛选条件"""
    # 估值条件
    pe_max: Optional[float] = None  # 最大PE
    pb_max: Optional[float] = None  # 最大PB
    ps_max: Optional[float] = None  # 最大PS
    dividend_yield_min: Optional[float] = None  # 最小股息率
    
    # 成长条件
    revenue_growth_min: Optional[float] = None  # 最小营收增长率
    profit_growth_min: Optional[float] = None  # 最小净利润增长率
    roe_min: Optional[float] = None  # 最小ROE
    
    # 财务安全
    debt_ratio_max: Optional[float] = None  # 最大资产负债率
    current_ratio_min: Optional[float] = None  # 最小流动比率
    gross_margin_min: Optional[float] = None  # 最小毛利率
    
    # 市值条件
    market_cap_min: Optional[float] = None  # 最小市值（亿元）
    market_cap_max: Optional[float] = None  # 最大市值（亿元）
    
    # 技术条件
    above_ma20: bool = False  # 股价高于MA20
    volume_ratio_min: Optional[float] = None  # 最小量比
    
    # 动量条件（价格动量）
    momentum_20d_min: Optional[float] = None  # 最小20日涨跌幅(%)
    momentum_60d_min: Optional[float] = None  # 最小60日涨跌幅(%)
    momentum_120d_min: Optional[float] = None  # 最小120日涨跌幅(%)
    require_positive_momentum: bool = False  # 要求绝对动量为正（双动量）
    
    # 行业/板块筛选
    industries: List[str] = field(default_factory=list)  # 指定行业/板块
    exclude_industries: List[str] = field(default_factory=list)  # 排除行业/板块
    
    # 指数成分股筛选（新增）
    index_components: Optional[str] = None  # 指定指数：'沪深300', '中证500', '中证1000', '上证50'
    
    # 评分条件
    min_total_score: Optional[int] = None  # 最小综合评分


@dataclass
class ScreenResult:
    """选股结果"""
    stock_code: str
    stock_name: str
    industry: str = ""
    
    # 估值数据
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    ps_ratio: float = 0.0
    dividend_yield: float = 0.0
    market_cap: float = 0.0  # 市值（亿元）
    
    # 成长数据
    revenue_growth: float = 0.0
    profit_growth: float = 0.0
    roe: float = 0.0
    
    # 财务数据
    debt_ratio: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    
    # 技术数据
    current_price: float = 0.0
    change_pct: float = 0.0
    ma20: float = 0.0
    volume_ratio: float = 0.0
    
    # 综合评分
    financial_score: int = 0
    technical_score: int = 0
    total_score: int = 0
    
    # 匹配因子
    matched_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'industry': self.industry,
            '估值': {
                'PE': round(self.pe_ratio, 2),
                'PB': round(self.pb_ratio, 2),
                '市值': f"{self.market_cap:.0f}亿",
                '股息率': f"{self.dividend_yield:.2f}%",
            },
            '成长': {
                'ROE': f"{self.roe:.2f}%",
                '营收增长': f"{self.revenue_growth:.2f}%",
                '利润增长': f"{self.profit_growth:.2f}%",
            },
            '财务': {
                '毛利率': f"{self.gross_margin:.2f}%",
                '净利率': f"{self.net_margin:.2f}%",
                '资产负债率': f"{self.debt_ratio:.2f}%",
            },
            '技术': {
                '现价': self.current_price,
                '涨跌幅': f"{self.change_pct:.2f}%",
                '量比': round(self.volume_ratio, 2),
            },
            '评分': {
                '财务评分': self.financial_score,
                '技术评分': self.technical_score,
                '综合评分': self.total_score,
            },
            '匹配因子': self.matched_factors,
        }


class StockScreener:
    """股票筛选器"""
    
    # 预设策略参数
    PRESET_STRATEGIES = {
        ScreenFactor.VALUE: {
            'name': '价值投资',
            'description': '低估值、高股息',
            'criteria': ScreenCriteria(
                pe_max=20,
                pb_max=2,
                dividend_yield_min=2,
                roe_min=10,
                debt_ratio_max=60,
            )
        },
        ScreenFactor.GROWTH: {
            'name': '成长投资',
            'description': '高成长、高ROE',
            'criteria': ScreenCriteria(
                revenue_growth_min=20,
                profit_growth_min=20,
                roe_min=15,
                debt_ratio_max=50,
            )
        },
        ScreenFactor.QUALITY: {
            'name': '质量投资',
            'description': '高质量、稳定盈利',
            'criteria': ScreenCriteria(
                roe_min=15,
                debt_ratio_max=40,
                gross_margin_min=30,
                current_ratio_min=1.5,
            )
        },
        ScreenFactor.BLUE_CHIP: {
            'name': '蓝筹股',
            'description': '大盘蓝筹、稳健分红',
            'criteria': ScreenCriteria(
                market_cap_min=500,
                pe_max=25,
                pb_max=3,
                roe_min=12,
                dividend_yield_min=2,
            )
        },
        ScreenFactor.SMALL_CAP_GROWTH: {
            'name': '小盘成长',
            'description': '小市值、高成长',
            'criteria': ScreenCriteria(
                market_cap_max=200,
                revenue_growth_min=30,
                profit_growth_min=30,
                roe_min=10,
            )
        },
        
        # 动量策略
        ScreenFactor.MOMENTUM: {
            'name': '价格动量',
            'description': '强势上涨、趋势延续',
            'criteria': ScreenCriteria(
                momentum_20d_min=10,  # 20日涨跌幅>10%
                momentum_60d_min=15,  # 60日涨跌幅>15%
                above_ma20=True,      # 价格在MA20之上
                volume_ratio_min=1.0, # 有成交量配合
            )
        },
        ScreenFactor.DUAL_MOMENTUM: {
            'name': '双动量策略',
            'description': '绝对动量+相对动量，选最强的股票',
            'criteria': ScreenCriteria(
                momentum_20d_min=5,    # 绝对动量：20日涨跌幅>5%
                momentum_60d_min=10,   # 绝对动量：60日涨跌幅>10%
                require_positive_momentum=True,  # 要求动量为正
                roe_min=8,             # 基本面过滤：ROE>8%
                debt_ratio_max=60,     # 基本面过滤：负债率<60%
            )
        },
    }
    
    def __init__(self):
        self._financial_cache = {}  # 财务数据缓存
        
        # 初始化数据源管理器（优先使用，替代直接akshare调用）
        self._data_manager = None
        try:
            # 尝试相对导入（包内使用）
            try:
                from .data_provider import DataFetcherManager
            except ImportError:
                # 尝试绝对导入（独立脚本使用）
                from data_provider import DataFetcherManager
            self._data_manager = DataFetcherManager()
            logger.debug("选股器已初始化数据源管理器")
        except Exception as e:
            logger.warning(f"选股器数据源管理器初始化失败: {e}")
        
        # 保留akshare作为备选（兼容旧代码）
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
                logger.debug("选股器已连接数据库")
            except Exception as e:
                logger.warning(f"选股器数据库连接失败: {e}")
    
    def screen_by_preset(
        self, 
        strategy: ScreenFactor, 
        top_n: int = 20,
        market: str = "A股"
    ) -> List[ScreenResult]:
        """
        使用预设策略筛选股票
        
        Args:
            strategy: 预设策略类型
            top_n: 返回前N个结果
            market: 市场范围（"A股", "沪市", "深市", "创业板", "科创板"）
            
        Returns:
            选股结果列表
        """
        if strategy not in self.PRESET_STRATEGIES:
            raise ValueError(f"未知策略: {strategy}")
        
        preset = self.PRESET_STRATEGIES[strategy]
        logger.info(f"[选股] 使用预设策略: {preset['name']} - {preset['description']}")
        
        return self.screen_by_criteria(preset['criteria'], top_n, market)
    
    def screen_by_criteria(
        self, 
        criteria: ScreenCriteria,
        top_n: int = 20,
        market: str = "A股"
    ) -> List[ScreenResult]:
        """
        根据自定义条件筛选股票
        
        Args:
            criteria: 筛选条件
            top_n: 返回前N个结果
            market: 市场范围（当criteria.industries或criteria.index_components指定时，market参数被覆盖）
            
        Returns:
            选股结果列表
        """
        if self._ak is None:
            logger.error("akshare未安装")
            return []
        
        try:
            # 确定股票池来源
            if criteria.index_components:
                logger.info(f"[选股] 开始筛选，指数: {criteria.index_components}...")
                stock_pool = self._get_stock_pool(market, criteria.index_components)
            elif criteria.industries:
                # 如果指定了行业/板块，获取这些行业的股票
                industry_name = criteria.industries[0]  # 暂时只支持单个行业
                logger.info(f"[选股] 开始筛选，板块: {industry_name}...")
                stock_pool = self.get_industry_stocks(industry_name)
            else:
                logger.info(f"[选股] 开始筛选，市场: {market}...")
                stock_pool = self._get_stock_pool(market)
            
            logger.info(f"[选股] 股票池数量: {len(stock_pool)}")
            
            # 筛选符合条件的股票（基本面 + 技术面）
            results = []
            for stock_code in stock_pool[:200]:  # 限制处理数量，避免太慢
                try:
                    result = self._evaluate_stock(stock_code, criteria)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"评估 {stock_code} 失败: {e}")
                    continue
            
            # 按综合评分排序
            results.sort(key=lambda x: x.total_score, reverse=True)
            
            logger.info(f"[选股] 筛选完成，符合条件的股票: {len(results)}，返回前{top_n}")
            return results[:top_n]
            
        except Exception as e:
            logger.error(f"[选股] 筛选失败: {e}")
            return []
    
    def _get_stock_pool(self, market: str, index_name: Optional[str] = None) -> List[str]:
        """
        获取股票池（使用统一数据源接口）
        
        Args:
            market: 市场范围（"A股", "沪市", "深市", "创业板", "科创板"）
            index_name: 指数名称（"沪深300", "中证500", "中证1000", "上证50"），优先于market参数
        """
        try:
            # 如果指定了指数，从指数成分股中获取
            if index_name:
                return self._get_index_components(index_name)
            
            # 优先使用数据源管理器（统一接口）
            if self._data_manager:
                df, source = self._data_manager.get_stock_pool(market)
                if df is not None and not df.empty:
                    logger.info(f"[选股] 从 {source} 获取 {market} 股票池: {len(df)} 只")
                    return df['code'].tolist()
                else:
                    logger.warning(f"[选股] 数据源管理器返回空数据，尝试备选方案")
            
            # 备选：直接使用akshare
            if self._ak:
                if market == "沪市":
                    df = self._ak.stock_sh_a_spot_em()
                elif market == "深市":
                    df = self._ak.stock_sz_a_spot_em()
                elif market == "创业板":
                    df = self._ak.stock_cy_a_spot_em()
                elif market == "科创板":
                    df = self._ak.stock_kc_a_spot_em()
                else:  # A股全部
                    df = self._ak.stock_zh_a_spot_em()
                
                if df is not None and not df.empty:
                    return df['代码'].tolist()
        except Exception as e:
            logger.error(f"获取股票池失败: {e}")
        
        return []
    
    def _get_index_components(self, index_name: str) -> List[str]:
        """
        获取指数成分股（带数据库缓存，使用统一数据源接口）
        
        Args:
            index_name: 指数名称（"沪深300", "中证500", "中证1000", "上证50"）
            
        Returns:
            成分股代码列表
        """
        try:
            logger.info(f"[选股] 获取 {index_name} 成分股...")
            
            # 指数代码映射
            index_code_map = {
                '沪深300': '000300',
                '中证500': '000905',
                '中证1000': '000852',
                '上证50': '000016',
            }
            
            if index_name not in index_code_map:
                logger.warning(f"未知指数: {index_name}")
                return []
            
            index_code = index_code_map[index_name]
            
            # 方法1：从数据库缓存获取（优先）
            if self._db:
                try:
                    cached = self._db.get_index_components(index_code, max_age_days=1)
                    if cached:
                        logger.info(f"[选股] 从数据库缓存获取 {index_name} 成分股: {len(cached)} 只")
                        return [item['stock_code'] for item in cached]
                except Exception as e:
                    logger.debug(f"从数据库获取指数成分股失败: {e}")
            
            # 方法2：使用数据源管理器（统一接口）
            if self._data_manager:
                df, source = self._data_manager.get_index_components(index_code)
                if df is not None and not df.empty:
                    components = df['stock_code'].tolist()
                    logger.info(f"[选股] 从 {source} 获取 {index_name} 成分股: {len(components)} 只")
                    
                    # 保存到数据库缓存
                    if self._db:
                        try:
                            cache_data = []
                            for _, row in df.iterrows():
                                cache_data.append({
                                    'stock_code': row.get('stock_code', ''),
                                    'stock_name': row.get('stock_name', ''),
                                    'weight': row.get('weight', 0)
                                })
                            self._db.save_index_components(index_code, index_name, cache_data)
                        except Exception as e:
                            logger.debug(f"保存指数成分股缓存失败: {e}")
                    
                    return components
                else:
                    logger.warning(f"[选股] 数据源管理器返回空数据，尝试备选方案")
            
            # 方法3：直接使用akshare（备选）
            if self._ak:
                try:
                    df = self._ak.index_stock_cons_weight_csindex(symbol=index_code)
                    if df is not None and not df.empty:
                        components = df['成分券代码'].tolist()
                        logger.info(f"[选股] 从akshare获取 {index_name} 成分股: {len(components)} 只")
                        return components
                except Exception as e:
                    logger.debug(f"从akshare获取成分股失败: {e}")
            
            logger.error(f"无法获取 {index_name} 成分股")
            return []
            
        except Exception as e:
            logger.error(f"获取指数成分股失败: {e}")
            return []
    
    def get_industry_stocks(self, industry_name: str) -> List[str]:
        """
        获取板块/行业成分股（使用统一数据源接口）
        
        Args:
            industry_name: 行业/板块名称，如 "半导体", "白酒", "银行"
            
        Returns:
            股票代码列表
        """
        try:
            logger.info(f"[选股] 获取 {industry_name} 板块股票...")
            
            # 优先使用数据源管理器（统一接口）
            if self._data_manager:
                df, source = self._data_manager.get_industry_stocks(industry_name)
                if df is not None and not df.empty:
                    logger.info(f"[选股] 从 {source} 获取行业 {industry_name} 成分股: {len(df)} 只")
                    return df['code'].tolist()
                else:
                    logger.warning(f"[选股] 数据源管理器返回空数据，尝试备选方案")
            
            # 备选：直接使用akshare
            if self._ak:
                try:
                    df = self._ak.stock_board_industry_cons_em(symbol=industry_name)
                    if df is not None and not df.empty:
                        return df['代码'].tolist()
                except Exception as e1:
                    logger.debug(f"方法1获取行业成分股失败: {e1}")
                
                # 备选2：从全市场筛选所属行业
                try:
                    df = self._ak.stock_zh_a_spot_em()
                    if df is not None and not df.empty:
                        industry_stocks = df[df['所属行业'] == industry_name]
                        if not industry_stocks.empty:
                            return industry_stocks['代码'].tolist()
                except Exception as e2:
                    logger.debug(f"方法2获取行业成分股失败: {e2}")
            
            logger.warning(f"未找到 {industry_name} 板块的股票")
            return []
            
        except Exception as e:
            logger.error(f"获取行业成分股失败: {e}")
            return []
    
    def get_available_industries(self) -> List[str]:
        """获取可用的行业/板块列表（使用统一数据源接口）"""
        try:
            # 优先使用数据源管理器
            if self._data_manager:
                df, source = self._data_manager.get_industry_list()
                if df is not None and not df.empty:
                    logger.info(f"[选股] 从 {source} 获取行业列表: {len(df)} 个")
                    return df['name'].tolist()
            
            # 备选：直接使用akshare
            if self._ak:
                df = self._ak.stock_board_industry_name_em()
                if df is not None and not df.empty:
                    return df['板块名称'].tolist()
        except Exception as e:
            logger.error(f"获取行业列表失败: {e}")
        
        return []
    
    def _get_stock_name(self, stock_code: str) -> str:
        """
        获取股票名称
        
        优先从数据库获取，数据库没有则尝试从akshare获取
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票名称，找不到返回空字符串
        """
        # 方法1：从数据库获取（最快）
        if self._db:
            try:
                name = self._db.get_stock_name(stock_code)
                if name:
                    return name
            except Exception as e:
                logger.debug(f"从数据库获取股票名称失败: {e}")
        
        # 方法2：尝试从指数成分股缓存获取
        # 这个方法保留作为备选，但现在已经不太需要了
        
        return ""
    
    def _evaluate_stock(
        self, 
        stock_code: str, 
        criteria: ScreenCriteria
    ) -> Optional[ScreenResult]:
        """
        评估股票（基本面 + 技术面）
        
        基于数据库中的历史K线数据进行技术面分析，避免使用实时接口
        """
        result = ScreenResult(stock_code=stock_code, stock_name="")
        matched_factors = []
        
        # 从数据库获取股票名称
        result.stock_name = self._get_stock_name(stock_code)
        
        # 获取财务数据（主要筛选依据）
        fin_data = self._get_financial_data_cached(stock_code)
        if not fin_data:
            return None
        
        result.roe = fin_data.get('roe', 0)
        result.revenue_growth = fin_data.get('revenue_growth', 0)
        result.profit_growth = fin_data.get('profit_growth', 0)
        result.debt_ratio = fin_data.get('debt_ratio', 0)
        result.gross_margin = fin_data.get('gross_margin', 0)
        result.net_margin = fin_data.get('net_margin', 0)
        result.financial_score = fin_data.get('total_score', 0)
        
        # 从财务数据获取估值指标
        result.pe_ratio = fin_data.get('pe_ratio', 0)
        result.pb_ratio = fin_data.get('pb_ratio', 0)
        result.market_cap = fin_data.get('total_mv', 0)  # 亿元
        
        # 检查市值条件
        if criteria.market_cap_min is not None and result.market_cap < criteria.market_cap_min:
            return None
        if criteria.market_cap_max is not None and result.market_cap > criteria.market_cap_max:
            return None
        
        # 检查估值条件
        if criteria.pe_max is not None and (result.pe_ratio <= 0 or result.pe_ratio > criteria.pe_max):
            return None
        if criteria.pb_max is not None and (result.pb_ratio <= 0 or result.pb_ratio > criteria.pb_max):
            return None
        
        # 检查财务条件
        if criteria.roe_min is not None and result.roe < criteria.roe_min:
            return None
        if criteria.revenue_growth_min is not None and result.revenue_growth < criteria.revenue_growth_min:
            return None
        if criteria.profit_growth_min is not None and result.profit_growth < criteria.profit_growth_min:
            return None
        if criteria.debt_ratio_max is not None and result.debt_ratio > criteria.debt_ratio_max:
            return None
        
        # 记录匹配因子
        if criteria.pe_max is not None and 0 < result.pe_ratio <= criteria.pe_max:
            matched_factors.append(f"低PE({result.pe_ratio:.1f})")
        if criteria.pb_max is not None and 0 < result.pb_ratio <= criteria.pb_max:
            matched_factors.append(f"低PB({result.pb_ratio:.1f})")
        if criteria.roe_min is not None and result.roe >= criteria.roe_min:
            matched_factors.append(f"高ROE({result.roe:.1f}%)")
        if criteria.revenue_growth_min is not None and result.revenue_growth >= criteria.revenue_growth_min:
            matched_factors.append(f"高增长({result.revenue_growth:.1f}%)")
        
        # === 技术面分析（基于数据库中的历史数据）===
        tech_data = None
        if self._db:
            try:
                tech_data = self._db.get_latest_tech_data(stock_code)
            except Exception as e:
                logger.debug(f"获取技术指标失败: {e}")
        
        if tech_data:
            result.current_price = tech_data.get('close', 0)
            result.change_pct = tech_data.get('pct_chg', 0)
            result.ma20 = tech_data.get('ma20', 0)
            result.volume_ratio = tech_data.get('volume_ratio', 0)
            
            # 技术评分（基于动量和技术形态）
            technical_score = 0
            
            # 1. 动量评分（涨跌幅）
            if result.change_pct > 5:
                technical_score += 15
                matched_factors.append(f"强势上涨({result.change_pct:.1f}%)")
            elif result.change_pct > 2:
                technical_score += 10
                matched_factors.append(f"温和上涨({result.change_pct:.1f}%)")
            elif result.change_pct > 0:
                technical_score += 5
            
            # 2. 多头排列评分
            if tech_data.get('bullish_arrangement'):
                technical_score += 15
                matched_factors.append("多头排列")
            
            # 3. 突破形态（价格相对MA20的位置）
            price_vs_ma20 = tech_data.get('price_vs_ma20', 0)
            if price_vs_ma20 > 5:
                technical_score += 10
                matched_factors.append("突破MA20")
            elif price_vs_ma20 > 0:
                technical_score += 5
            
            # 4. 放量评分
            if criteria.volume_ratio_min is not None:
                if result.volume_ratio >= criteria.volume_ratio_min:
                    technical_score += 10
                    matched_factors.append(f"放量({result.volume_ratio:.1f})")
            elif result.volume_ratio > 2:
                technical_score += 10
                matched_factors.append(f"放量({result.volume_ratio:.1f})")
            elif result.volume_ratio > 1.5:
                technical_score += 5
            
            result.technical_score = min(50, technical_score)  # 技术面最高50分
        else:
            # 无技术数据，技术评分为0
            result.technical_score = 0
        
        # === 动量分析（多周期价格动量）===
        momentum_data = None
        if self._db:
            try:
                momentum_data = self._db.get_momentum_data(stock_code)
            except Exception as e:
                logger.debug(f"获取动量数据失败: {e}")
        
        momentum_score = 0  # 动量得分（额外加分项）
        
        if momentum_data:
            m20 = momentum_data.get('momentum_20d', 0)
            m60 = momentum_data.get('momentum_60d', 0)
            m120 = momentum_data.get('momentum_120d', 0)
            consistency = momentum_data.get('trend_consistency', 0)
            
            # 检查动量条件
            if criteria.momentum_20d_min is not None and m20 < criteria.momentum_20d_min:
                return None  # 不满足20日动量要求，过滤掉
            if criteria.momentum_60d_min is not None and m60 < criteria.momentum_60d_min:
                return None  # 不满足60日动量要求，过滤掉
            if criteria.momentum_120d_min is not None and m120 < criteria.momentum_120d_min:
                return None  # 不满足120日动量要求，过滤掉
            
            # 双动量策略：要求绝对动量为正
            if criteria.require_positive_momentum:
                if m20 <= 0 or m60 <= 0:
                    return None  # 绝对动量不满足，过滤掉
            
            # 动量评分（额外加分，最高30分）
            # 1. 20日动量评分
            if m20 > 20:
                momentum_score += 10
                matched_factors.append(f"强势20日动量({m20:.1f}%)")
            elif m20 > 10:
                momentum_score += 7
                matched_factors.append(f"良好20日动量({m20:.1f}%)")
            elif m20 > 5:
                momentum_score += 5
            
            # 2. 60日动量评分
            if m60 > 30:
                momentum_score += 10
                matched_factors.append(f"强势60日动量({m60:.1f}%)")
            elif m60 > 15:
                momentum_score += 7
                matched_factors.append(f"良好60日动量({m60:.1f}%)")
            elif m60 > 5:
                momentum_score += 5
            
            # 3. 长期动量评分（120日）
            if m120 > 50:
                momentum_score += 5
                matched_factors.append(f"超强长期动量({m120:.1f}%)")
            elif m120 > 20:
                momentum_score += 3
            
            # 4. 趋势一致性奖励
            if consistency >= 1.0:
                momentum_score += 5
                matched_factors.append("趋势一致向上")
            elif consistency >= 0.67:
                momentum_score += 3
            
            momentum_score = min(30, momentum_score)  # 动量最高30分
        
        # 综合评分 = 财务评分 + 技术评分 + 动量得分
        result.total_score = result.financial_score + result.technical_score + momentum_score
        
        # 检查综合评分条件
        if criteria.min_total_score is not None and result.total_score < criteria.min_total_score:
            return None
        
        result.matched_factors = matched_factors
        
        return result
    
    def _get_financial_data_cached(self, stock_code: str) -> Optional[Dict]:
        """获取缓存的财务数据"""
        if stock_code in self._financial_cache:
            return self._financial_cache[stock_code]
        
        try:
            # 导入财务分析器
            from .financial_analyzer import FinancialAnalyzer
            analyzer = FinancialAnalyzer()
            fin_indicators = analyzer.get_financial_data(stock_code)
            
            if fin_indicators:
                data = {
                    'roe': fin_indicators.roe,
                    'revenue_growth': fin_indicators.revenue_growth,
                    'profit_growth': fin_indicators.profit_growth,
                    'debt_ratio': fin_indicators.debt_ratio,
                    'gross_margin': fin_indicators.gross_margin,
                    'net_margin': fin_indicators.net_margin,
                    'total_score': fin_indicators.total_score,
                }
                self._financial_cache[stock_code] = data
                return data
        except Exception as e:
            logger.debug(f"获取 {stock_code} 财务数据失败: {e}")
        
        return None
    
    def get_preset_strategies(self) -> Dict[str, Any]:
        """获取所有预设策略"""
        return {
            key.value: {
                'name': value['name'],
                'description': value['description'],
            }
            for key, value in self.PRESET_STRATEGIES.items()
        }


# 便捷函数
def screen_stocks(
    strategy: str = "value",
    top_n: int = 20,
    market: str = "A股",
    format_type: str = "dict"
) -> Any:
    """
    选股功能（OpenClaw工具函数）
    
    Args:
        strategy: 策略名称 ("value", "growth", "quality", "blue_chip", "small_cap_growth")
        top_n: 返回股票数量
        market: 市场范围 ("A股", "沪市", "深市", "创业板", "科创板")
        format_type: 输出格式 ("dict", "json", "prompt")
        
    Returns:
        选股结果
    """
    try:
        factor = ScreenFactor(strategy)
    except ValueError:
        error_msg = f"未知策略: {strategy}，可用策略: value, growth, quality, blue_chip, small_cap_growth"
        if format_type == "json":
            import json
            return json.dumps({'success': False, 'error': error_msg}, ensure_ascii=False)
        elif format_type == "prompt":
            return error_msg
        else:
            return {'success': False, 'error': error_msg}
    
    screener = StockScreener()
    results = screener.screen_by_preset(factor, top_n, market)
    
    if not results:
        error_msg = "选股失败或未找到符合条件的股票"
        if format_type == "json":
            import json
            return json.dumps({'success': False, 'error': error_msg}, ensure_ascii=False)
        elif format_type == "prompt":
            return error_msg
        else:
            return {'success': False, 'error': error_msg}
    
    # 转换为指定格式
    results_dict = [r.to_dict() for r in results]
    
    if format_type == "json":
        import json
        return json.dumps({
            'success': True,
            'strategy': strategy,
            'market': market,
            'count': len(results),
            'stocks': results_dict
        }, ensure_ascii=False, indent=2)
    
    elif format_type == "prompt":
        lines = [
            f"# 选股结果 - {strategy}",
            f"市场范围: {market}",
            f"筛选数量: {len(results)}",
            "",
            "| 排名 | 代码 | 名称 | 行业 | PE | PB | ROE | 评分 | 匹配因子 |",
            "|------|------|------|------|-----|-----|------|------|----------|",
        ]
        for i, r in enumerate(results, 1):
            factors = ", ".join(r.matched_factors[:3])
            lines.append(
                f"| {i} | {r.stock_code} | {r.stock_name} | {r.industry} | "
                f"{r.pe_ratio:.1f} | {r.pb_ratio:.1f} | {r.roe:.1f}% | "
                f"{r.total_score} | {factors} |"
            )
        return "\n".join(lines)
    
    else:
        return {
            'success': True,
            'strategy': strategy,
            'market': market,
            'count': len(results),
            'stocks': results_dict
        }


def screen_stocks_advanced(
    strategy: str = "value",
    top_n: int = 20,
    market: str = "A股",
    index_name: Optional[str] = None,
    industry: Optional[str] = None,
    format_type: str = "dict"
) -> Any:
    """
    高级选股功能（支持板块和指数）
    
    Args:
        strategy: 策略名称 ("value", "growth", "quality", "blue_chip", "small_cap_growth")
        top_n: 返回股票数量
        market: 市场范围 ("A股", "沪市", "深市", "创业板", "科创板")
        index_name: 指数名称 ("沪深300", "中证500", "中证1000", "上证50")，优先于market
        industry: 行业/板块名称 (如 "半导体", "白酒", "银行")，优先于index_name
        format_type: 输出格式 ("dict", "json", "prompt")
        
    Returns:
        选股结果
    """
    try:
        factor = ScreenFactor(strategy)
    except ValueError:
        error_msg = f"未知策略: {strategy}，可用策略: value, growth, quality, blue_chip, small_cap_growth"
        if format_type == "json":
            import json
            return json.dumps({'success': False, 'error': error_msg}, ensure_ascii=False)
        elif format_type == "prompt":
            return error_msg
        else:
            return {'success': False, 'error': error_msg}
    
    screener = StockScreener()
    preset = screener.PRESET_STRATEGIES[factor]
    criteria = preset['criteria']
    
    # 设置板块或指数筛选
    if industry:
        criteria.industries = [industry]
        scope = f"板块:{industry}"
    elif index_name:
        criteria.index_components = index_name
        scope = f"指数:{index_name}"
    else:
        scope = f"市场:{market}"
    
    results = screener.screen_by_criteria(criteria, top_n, market)
    
    if not results:
        error_msg = f"在{scope}中未找到符合条件的股票"
        if format_type == "json":
            import json
            return json.dumps({'success': False, 'error': error_msg}, ensure_ascii=False)
        elif format_type == "prompt":
            return error_msg
        else:
            return {'success': False, 'error': error_msg}
    
    # 转换为指定格式
    results_dict = [r.to_dict() for r in results]
    
    if format_type == "json":
        import json
        return json.dumps({
            'success': True,
            'strategy': strategy,
            'scope': scope,
            'count': len(results),
            'stocks': results_dict
        }, ensure_ascii=False, indent=2)
    
    elif format_type == "prompt":
        lines = [
            f"# 选股结果 - {preset['name']}",
            f"筛选范围: {scope}",
            f"策略说明: {preset['description']}",
            f"筛选数量: {len(results)}",
            "",
            "| 排名 | 代码 | 名称 | 行业 | PE | PB | ROE | 评分 | 匹配因子 |",
            "|------|------|------|------|-----|-----|------|------|----------|",
        ]
        for i, r in enumerate(results, 1):
            factors = ", ".join(r.matched_factors[:3])
            lines.append(
                f"| {i} | {r.stock_code} | {r.stock_name} | {r.industry} | "
                f"{r.pe_ratio:.1f} | {r.pb_ratio:.1f} | {r.roe:.1f}% | "
                f"{r.total_score} | {factors} |"
            )
        return "\n".join(lines)
    
    else:
        return {
            'success': True,
            'strategy': strategy,
            'scope': scope,
            'count': len(results),
            'stocks': results_dict
        }


def list_screen_strategies() -> List[Dict[str, str]]:
    """列出所有可用的选股策略"""
    screener = StockScreener()
    strategies = screener.get_preset_strategies()
    return [
        {
            'id': key,
            'name': value['name'],
            'description': value['description']
        }
        for key, value in strategies.items()
    ]


def list_available_indices() -> List[str]:
    """列出可用的指数"""
    return ["沪深300", "中证500", "中证1000", "上证50"]


def list_available_industries() -> List[str]:
    """列出可用的行业/板块"""
    screener = StockScreener()
    return screener.get_available_industries()
