# -*- coding: utf-8 -*-
"""
数据源基类与管理器

设计模式：策略模式 (Strategy Pattern)
- BaseFetcher: 抽象基类，定义统一接口
- DataFetcherManager: 策略管理器，实现自动切换

防封禁策略：
1. 每个 Fetcher 内置流控逻辑
2. 失败自动切换到下一个数据源
3. 指数退避重试机制
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

import pandas as pd
import numpy as np

# 配置日志
logger = logging.getLogger(__name__)

# 标准化列名定义
STANDARD_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']

# 额外数据键名
REALTIME_QUOTE_KEY = '_realtime_quote'
CHIP_DISTRIBUTION_KEY = '_chip_distribution'


class DataFetchError(Exception):
    """数据获取异常基类"""
    pass


class RateLimitError(DataFetchError):
    """API 速率限制异常"""
    pass


class DataSourceUnavailableError(DataFetchError):
    """数据源不可用异常"""
    pass


class BaseFetcher(ABC):
    """
    数据源抽象基类

    职责：
    1. 定义统一的数据获取接口
    2. 提供数据标准化方法
    3. 实现通用的技术指标计算

    子类实现：
    - _fetch_raw_data(): 从具体数据源获取原始数据
    - _normalize_data(): 将原始数据转换为标准格式
    """

    name: str = "BaseFetcher"
    priority: int = 99  # 优先级数字越小越优先

    @abstractmethod
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从数据源获取原始数据（子类必须实现）

        Args:
            stock_code: 股票代码，如 '600519', '000001'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'

        Returns:
            原始数据 DataFrame（列名因数据源而异）
        """
        pass

    @abstractmethod
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        标准化数据列名（子类必须实现）

        将不同数据源的列名统一为：
        ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']
        """
        pass

    @abstractmethod
    def _get_realtime_quote(self, stock_code: str) -> Optional[dict]:
        """
        获取实时行情数据（子类必须实现）

        Args:
            stock_code: 股票代码

        Returns:
            实时行情字典，包含字段：
            - code, name, price, change_pct, change_amount
            - volume, amount, turnover_rate, volume_ratio, amplitude
            - high, low, open_price
            - pe_ratio, pb_ratio, total_mv, circ_mv
            获取失败返回 None
        """
        pass

    @abstractmethod
    def _get_chip_distribution(self, stock_code: str) -> Optional[dict]:
        """
        获取筹码分布数据（子类必须实现）

        Args:
            stock_code: 股票代码

        Returns:
            筹码分布字典，包含字段：
            - code, date, profit_ratio, avg_cost, concentration_90, concentration_70
            获取失败返回 None
        """
        pass

    # ========== 期权数据接口 ==========

    @abstractmethod
    def _get_option_chain(self, underlying_code: str, expiry_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取期权链数据
        
        Args:
            underlying_code: 标的代码，如 '510050' (50ETF)
            expiry_date: 到期日（可选，格式 YYYY-MM-DD），默认返回全部
        
        Returns:
            DataFrame 包含列：
            - code: 期权代码
            - name: 期权名称
            - underlying: 标的代码
            - type: 'call' 或 'put'
            - strike: 行权价
            - expiry: 到期日
            - price: 最新价
            - change_pct: 涨跌幅
            - volume: 成交量
            - open_interest: 持仓量
            - iv: 隐含波动率
            - delta, gamma, theta, vega, rho: 希腊字母
            获取失败返回空 DataFrame
        """
        pass

    @abstractmethod
    def _get_option_iv(self, underlying_code: str) -> Optional[float]:
        """
        获取期权隐含波动率（加权平均）
        
        Args:
            underlying_code: 标的代码
        
        Returns:
            加权平均 IV，获取失败返回 None
        """
        pass

    @abstractmethod
    def _get_option_cp_ratio(self, underlying_code: str) -> Optional[Dict[str, Any]]:
        """
        获取认购认沽比 (CP Ratio)
        
        Args:
            underlying_code: 标的代码
        
        Returns:
            {
                'volume_cp_ratio': float,  # 成交量 CP 比
                'oi_cp_ratio': float,      # 持仓量 CP 比
                'call_volume': int,
                'put_volume': int,
                'call_oi': int,
                'put_oi': int,
            }
            获取失败返回 None
        """
        pass

    # ========== 期货贴水数据接口 ==========

    @abstractmethod
    def _get_futures_basis(self) -> pd.DataFrame:
        """
        获取股指期货贴水/升水数据
        
        Returns:
            DataFrame 包含列：
            - index_code: 指数代码（如 '000300' 沪深300）
            - index_name: 指数名称
            - index_price: 现货指数价格
            - futures_code: 期货代码（如 'IF0'）
            - futures_name: 期货名称
            - futures_price: 期货价格
            - basis: 基差（期货 - 现货）
            - basis_rate: 贴水率/升水率（%）
            - annualized_rate: 年化贴水率（%）
            - days_to_expiry: 距离到期日天数
            获取失败返回空 DataFrame
        """
        pass

    # ========== 大盘数据接口（市场分析用）==========

    @abstractmethod
    def _get_market_indices(self) -> pd.DataFrame:
        """
        获取主要指数实时行情（大盘分析用）

        Returns:
            DataFrame 包含列：
            - code: 指数代码（如 '000001', '399001'）
            - name: 指数名称（如 '上证指数', '深证成指'）
            - price: 最新点位
            - change_pct: 涨跌幅
            - change_amount: 涨跌额
            - volume: 成交量
            - amount: 成交额
            获取失败返回空 DataFrame
        """
        pass

    @abstractmethod
    def _get_market_overview(self) -> pd.DataFrame:
        """
        获取市场概览数据（A股实时行情统计）

        Returns:
            DataFrame 包含全部A股实时行情，用于统计：
            - 上涨/下跌家数
            - 涨停/跌停家数
            列名与个股实时行情一致
        """
        pass

    @abstractmethod
    def _get_sector_rankings(self) -> pd.DataFrame:
        """
        获取行业板块涨跌排行

        Returns:
            DataFrame 包含列：
            - name: 板块名称
            - change_pct: 涨跌幅
            - leading_stocks: 领涨股（可选）
            获取失败返回空 DataFrame
        """
        pass

    # ========== 股票筛选相关接口（新增）==========

    @abstractmethod
    def _get_index_components(self, index_code: str) -> pd.DataFrame:
        """
        获取指数成分股（用于选股）

        Args:
            index_code: 指数代码，如 '000300', '000905', '000852', '000016'

        Returns:
            DataFrame 包含列：
            - stock_code: 股票代码
            - stock_name: 股票名称
            - weight: 权重（可选）
            如果不支持返回空 DataFrame，调用端需处理
        """
        pass

    @abstractmethod
    def _get_stock_pool(self, market: str = "A股") -> pd.DataFrame:
        """
        获取市场股票池（用于选股）

        Args:
            market: 市场范围（"A股", "沪市", "深市", "创业板", "科创板"）

        Returns:
            DataFrame 包含列：
            - code: 股票代码
            - name: 股票名称
            - market: 所属市场
            - industry: 所属行业（可选）
            如果不支持返回空 DataFrame，调用端需处理
        """
        pass

    @abstractmethod
    def _get_industry_stocks(self, industry_name: str) -> pd.DataFrame:
        """
        获取行业成分股（用于选股）

        Args:
            industry_name: 行业名称，如 "半导体", "白酒"

        Returns:
            DataFrame 包含列：
            - code: 股票代码
            - name: 股票名称
            如果不支持返回空 DataFrame，调用端需处理
        """
        pass

    @abstractmethod
    def _get_industry_list(self) -> pd.DataFrame:
        """
        获取行业/板块列表（用于选股）

        Returns:
            DataFrame 包含列：
            - name: 行业名称
            - code: 行业代码（可选）
            如果不支持返回空 DataFrame，调用端需处理
        """
        pass

    # ========== 财务分析相关接口（新增）==========

    @abstractmethod
    def _get_financial_report(
        self,
        stock_code: str,
        report_type: str = "利润表"
    ) -> pd.DataFrame:
        """
        获取财务报表（用于财务分析）

        Args:
            stock_code: 股票代码
            report_type: 报表类型（"利润表", "资产负债表", "现金流量表"）

        Returns:
            DataFrame 包含多期报表数据，列名取决于报表类型
            如果不支持返回空 DataFrame，调用端需处理
        """
        pass

    @abstractmethod
    def _get_financial_indicators(self, stock_code: str) -> pd.DataFrame:
        """
        获取财务分析指标（用于财务分析）

        Args:
            stock_code: 股票代码

        Returns:
            DataFrame 包含关键财务指标，如：
            - 净资产收益率(roe)
            - 毛利率(gross_margin)
            - 营收增长率(revenue_growth)
            - 资产负债率(debt_ratio)
            - 市盈率(pe_ratio)
            - 市净率(pb_ratio)
            如果不支持返回空 DataFrame，调用端需处理
        """
        pass

    @abstractmethod
    def _get_stock_basic_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息（用于显示股票名称、行业、市值等）

        Args:
            stock_code: 股票代码

        Returns:
            字典包含股票基本信息：
            - code: 股票代码
            - name: 股票名称
            - industry: 所属行业
            - list_date: 上市日期
            - total_shares: 总股本
            - float_shares: 流通股本
            - total_mv: 总市值
            - circ_mv: 流通市值
            获取失败返回空字典
        """
        pass

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> pd.DataFrame:
        """
        获取日线数据（统一入口）

        流程：
        1. 计算日期范围
        2. 调用子类获取原始数据
        3. 标准化列名
        4. 计算技术指标

        Args:
            stock_code: 股票代码
            start_date: 开始日期（可选）
            end_date: 结束日期（可选，默认今天）
            days: 获取天数（当 start_date 未指定时使用）

        Returns:
            标准化的 DataFrame，包含技术指标
        """
        # 计算日期范围
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if start_date is None:
            from datetime import timedelta
            start_dt = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=days * 2)
            start_date = start_dt.strftime('%Y-%m-%d')

        logger.info(f"[{self.name}] 获取 {stock_code} 数据: {start_date} ~ {end_date}")

        try:
            # Step 1: 获取原始数据
            raw_df = self._fetch_raw_data(stock_code, start_date, end_date)

            if raw_df is None or raw_df.empty:
                raise DataFetchError(f"[{self.name}] 未获取到 {stock_code} 的数据")

            # Step 2: 标准化列名
            df = self._normalize_data(raw_df, stock_code)

            # Step 3: 数据清洗（保留 attrs）
            df = self._clean_data(df)

            # Step 4: 计算技术指标（保留 attrs）
            df = self._calculate_indicators(df)

            # Step 5: 获取实时行情和筹码分布（存储在 attrs 中）
            try:
                realtime_quote = self._get_realtime_quote(stock_code)
                if realtime_quote:
                    df.attrs[REALTIME_QUOTE_KEY] = realtime_quote
            except Exception as e:
                logger.debug(f"[{self.name}] 获取实时行情失败: {e}")

            try:
                chip_distribution = self._get_chip_distribution(stock_code)
                if chip_distribution:
                    df.attrs[CHIP_DISTRIBUTION_KEY] = chip_distribution
            except Exception as e:
                logger.debug(f"[{self.name}] 获取筹码分布失败: {e}")

            logger.info(f"[{self.name}] {stock_code} 获取成功，共 {len(df)} 条数据")
            return df

        except Exception as e:
            logger.error(f"[{self.name}] 获取 {stock_code} 失败: {str(e)}")
            raise DataFetchError(f"[{self.name}] {stock_code}: {str(e)}") from e

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗

        处理：
        1. 确保日期列格式正确
        2. 数值类型转换
        3. 去除空值行
        4. 按日期排序
        """
        # 保存 attrs（如果有）
        attrs = df.attrs if hasattr(df, 'attrs') else {}
        df = df.copy()
        df.attrs.update(attrs)

        # 确保日期列为 datetime 类型，然后转为字符串
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            # 转换为 YYYY-MM-DD 字符串格式
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')

        # 数值列类型转换
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 去除关键列为空的行
        df = df.dropna(subset=['close', 'volume'])

        # 按日期升序排序
        df = df.sort_values('date', ascending=True).reset_index(drop=True)

        return df

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标

        计算指标：
        - MA5, MA10, MA20: 移动平均线
        - Volume_Ratio: 量比（今日成交量 / 5日平均成交量）
        """
        # 保存 attrs（如果有）
        attrs = df.attrs if hasattr(df, 'attrs') else {}
        df = df.copy()
        df.attrs.update(attrs)

        # 移动平均线
        df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()

        # 量比：当日成交量 / 5日平均成交量
        avg_volume_5 = df['volume'].rolling(window=5, min_periods=1).mean()
        df['volume_ratio'] = df['volume'] / avg_volume_5.shift(1)
        df['volume_ratio'] = df['volume_ratio'].fillna(1.0)

        # 保留2位小数
        for col in ['ma5', 'ma10', 'ma20', 'volume_ratio']:
            if col in df.columns:
                df[col] = df[col].round(2)

        return df

    @staticmethod
    def random_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """
        智能随机休眠（Jitter）

        防封禁策略：模拟人类行为的随机延迟
        在请求之间加入不规则的等待时间
        """
        sleep_time = random.uniform(min_seconds, max_seconds)
        logger.debug(f"随机休眠 {sleep_time:.2f} 秒...")
        time.sleep(sleep_time)


class DataFetcherManager:
    """
    数据源策略管理器

    职责：
    1. 管理多个数据源（按优先级排序）
    2. 自动故障切换（Failover）
    3. 提供统一的数据获取接口

    切换策略：
    - 优先使用高优先级数据源
    - 失败后自动切换到下一个
    - 记录每个数据源的失败原因
    - 所有数据源失败后抛出异常
    """

    def __init__(self, fetchers: Optional[List[BaseFetcher]] = None):
        """
        初始化管理器

        Args:
            fetchers: 数据源列表（可选，默认按优先级自动创建）
        """
        self._fetchers: List[BaseFetcher] = []

        if fetchers:
            # 按优先级排序
            self._fetchers = sorted(fetchers, key=lambda f: f.priority)
        else:
            # 默认数据源将在首次使用时延迟加载
            self._init_default_fetchers()

    def _init_default_fetchers(self) -> None:
        """
        初始化默认数据源列表

        按优先级排序：
        1. EfinanceFetcher (Priority 0) - 优先尝试
        2. AkshareFetcher (Priority 1) - 主要备选
        3. BaostockFetcher (Priority 2) - 最后备选（主要用于基本信息查询）
        
        说明：数据源都是可选的，只要有一个可用即可工作
        """
        # 优先尝试 efinance（如果安装）
        try:
            from .efinance_fetcher import EfinanceFetcher
            import efinance as _  # 验证库真的可用
            self._fetchers.append(EfinanceFetcher())
            logger.info("EfinanceFetcher 已加载（优先使用）")
        except Exception as e:
            logger.debug(f"EfinanceFetcher 不可用: {e}")

        # 备用数据源：akshare（可选）
        try:
            from .akshare_fetcher import AkshareFetcher
            self._fetchers.append(AkshareFetcher())
            logger.info("AkshareFetcher 已加载")
        except Exception as e:
            logger.warning(f"AkshareFetcher 不可用: {e}")
        
        # 第二备选：baostock（主要用于股票基本信息查询）
        try:
            from .baostock_fetcher import BaostockFetcher
            self._fetchers.append(BaostockFetcher())
            logger.info("BaostockFetcher 已加载")
        except Exception as e:
            logger.debug(f"BaostockFetcher 不可用: {e}")

        # 按优先级排序
        self._fetchers.sort(key=lambda f: f.priority)

        if self._fetchers:
            logger.info(f"已初始化 {len(self._fetchers)} 个数据源: " +
                       ", ".join([f.name for f in self._fetchers]))
        else:
            logger.error("没有可用的数据源！请安装至少一个数据源：")
            logger.error("  pip install efinance    # 推荐，更稳定")
            logger.error("  pip install akshare     # 备用")
            logger.error("  pip install baostock    # 证券宝备选")

    def add_fetcher(self, fetcher: BaseFetcher) -> None:
        """添加数据源并重新排序"""
        self._fetchers.append(fetcher)
        self._fetchers.sort(key=lambda f: f.priority)

    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> Tuple[pd.DataFrame, str]:
        """
        获取日线数据（自动切换数据源）

        故障切换策略：
        1. 从最高优先级数据源开始尝试
        2. 捕获异常后自动切换到下一个
        3. 记录每个数据源的失败原因
        4. 所有数据源失败后抛出详细异常

        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            days: 获取天数

        Returns:
            Tuple[DataFrame, str]: (数据, 成功的数据源名称)

        Raises:
            DataFetchError: 所有数据源都失败时抛出
        """
        errors = []

        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取 {stock_code}...")
                df = fetcher.get_daily_data(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    days=days
                )

                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取 {stock_code}")
                    return df, fetcher.name

            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                # 继续尝试下一个数据源
                continue

        # 所有数据源都失败
        error_summary = f"所有数据源获取 {stock_code} 失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    @property
    def available_fetchers(self) -> List[str]:
        """返回可用数据源名称列表"""
        return [f.name for f in self._fetchers]

    # ========== 大盘数据获取方法 ==========

    def get_market_indices(self) -> Tuple[pd.DataFrame, str]:
        """
        获取主要指数实时行情（自动切换数据源）
        
        Returns:
            Tuple[DataFrame, str]: (指数数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取指数行情...")
                df = fetcher._get_market_indices()
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取指数行情")
                    return df, fetcher.name
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        # 所有数据源都失败
        error_summary = "所有数据源获取指数行情失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    def get_market_overview(self) -> Tuple[pd.DataFrame, str]:
        """
        获取市场概览数据（自动切换数据源）
        
        Returns:
            Tuple[DataFrame, str]: (A股实时数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取市场概览...")
                df = fetcher._get_market_overview()
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取市场概览")
                    return df, fetcher.name
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        error_summary = "所有数据源获取市场概览失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    def get_sector_rankings(self) -> Tuple[pd.DataFrame, str]:
        """
        获取行业板块排行（自动切换数据源）
        
        Returns:
            Tuple[DataFrame, str]: (板块数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取板块排行...")
                df = fetcher._get_sector_rankings()
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取板块排行")
                    return df, fetcher.name
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        error_summary = "所有数据源获取板块排行失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    # ========== 期权数据获取方法 ==========

    def get_option_chain(self, underlying_code: str, expiry_date: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
        """
        获取期权链数据（自动切换数据源）
        
        Args:
            underlying_code: 标的代码，如 '510050'
            expiry_date: 到期日（可选）
        
        Returns:
            Tuple[DataFrame, str]: (期权链数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取期权链 {underlying_code}...")
                df = fetcher._get_option_chain(underlying_code, expiry_date)
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取期权链")
                    return df, fetcher.name
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        error_summary = f"所有数据源获取期权链 {underlying_code} 失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    def get_option_iv(self, underlying_code: str) -> Tuple[Optional[float], str]:
        """
        获取期权隐含波动率（自动切换数据源）
        
        Args:
            underlying_code: 标的代码
        
        Returns:
            Tuple[Optional[float], str]: (IV值, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取期权IV {underlying_code}...")
                iv = fetcher._get_option_iv(underlying_code)
                
                if iv is not None:
                    logger.info(f"[{fetcher.name}] 成功获取期权IV: {iv}")
                    return iv, fetcher.name
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        error_summary = f"所有数据源获取期权IV {underlying_code} 失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    def get_option_cp_ratio(self, underlying_code: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        获取认购认沽比（自动切换数据源）
        
        Args:
            underlying_code: 标的代码
        
        Returns:
            Tuple[Dict, str]: (CP Ratio数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取CP Ratio {underlying_code}...")
                cp_data = fetcher._get_option_cp_ratio(underlying_code)
                
                if cp_data is not None:
                    logger.info(f"[{fetcher.name}] 成功获取CP Ratio")
                    return cp_data, fetcher.name
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        error_summary = f"所有数据源获取CP Ratio {underlying_code} 失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    # ========== 期货贴水数据获取方法 ==========

    def get_futures_basis(self) -> Tuple[pd.DataFrame, str]:
        """
        获取股指期货贴水/升水数据（自动切换数据源）
        
        Returns:
            Tuple[DataFrame, str]: (贴水数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取期货贴水数据...")
                df = fetcher._get_futures_basis()
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取期货贴水数据")
                    return df, fetcher.name
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        error_summary = "所有数据源获取期货贴水数据失败:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)

    # ========== 股票筛选相关统一访问方法（新增）==========

    def get_index_components(self, index_code: str) -> Tuple[pd.DataFrame, str]:
        """
        获取指数成分股（自动切换数据源）
        
        Args:
            index_code: 指数代码，如 '000300', '000905'
        
        Returns:
            Tuple[DataFrame, str]: (成分股数据, 成功的数据源名称)
            DataFrame 包含列：stock_code, stock_name, weight
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取指数 {index_code} 成分股...")
                df = fetcher._get_index_components(index_code)
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取指数 {index_code} 成分股")
                    return df, fetcher.name
                else:
                    logger.debug(f"[{fetcher.name}] 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        # 所有数据源都失败，返回空 DataFrame
        logger.warning(f"所有数据源获取指数 {index_code} 成分股失败，返回空数据")
        return pd.DataFrame(), "None"

    def get_stock_pool(self, market: str = "A股") -> Tuple[pd.DataFrame, str]:
        """
        获取市场股票池（自动切换数据源）
        
        Args:
            market: 市场范围（"A股", "沪市", "深市", "创业板", "科创板"）
        
        Returns:
            Tuple[DataFrame, str]: (股票池数据, 成功的数据源名称)
            DataFrame 包含列：code, name, market, industry
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取 {market} 股票池...")
                df = fetcher._get_stock_pool(market)
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取 {market} 股票池")
                    return df, fetcher.name
                else:
                    logger.debug(f"[{fetcher.name}] 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        logger.warning(f"所有数据源获取 {market} 股票池失败，返回空数据")
        return pd.DataFrame(), "None"

    def get_industry_stocks(self, industry_name: str) -> Tuple[pd.DataFrame, str]:
        """
        获取行业成分股（自动切换数据源）
        
        Args:
            industry_name: 行业名称，如 "半导体", "白酒"
        
        Returns:
            Tuple[DataFrame, str]: (成分股数据, 成功的数据源名称)
            DataFrame 包含列：code, name
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取行业 {industry_name} 成分股...")
                df = fetcher._get_industry_stocks(industry_name)
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取行业 {industry_name} 成分股")
                    return df, fetcher.name
                else:
                    logger.debug(f"[{fetcher.name}] 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        logger.warning(f"所有数据源获取行业 {industry_name} 成分股失败，返回空数据")
        return pd.DataFrame(), "None"

    def get_industry_list(self) -> Tuple[pd.DataFrame, str]:
        """
        获取行业/板块列表（自动切换数据源）
        
        Returns:
            Tuple[DataFrame, str]: (行业列表, 成功的数据源名称)
            DataFrame 包含列：name, code（可选）
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取行业列表...")
                df = fetcher._get_industry_list()
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取行业列表")
                    return df, fetcher.name
                else:
                    logger.debug(f"[{fetcher.name}] 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        logger.warning("所有数据源获取行业列表失败，返回空数据")
        return pd.DataFrame(), "None"

    def get_stock_basic_info(self, stock_code: str) -> Tuple[Dict[str, Any], str]:
        """
        获取股票基本信息（自动切换数据源）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            Tuple[Dict, str]: (股票信息字典, 成功的数据源名称)
            字典包含：code, name, industry, list_date, total_shares等
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取 {stock_code} 基本信息...")
                info = fetcher._get_stock_basic_info(stock_code)
                
                if info and info.get('name'):
                    logger.info(f"[{fetcher.name}] 成功获取 {stock_code} 基本信息: {info.get('name')}")
                    return info, fetcher.name
                else:
                    logger.debug(f"[{fetcher.name}] 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        logger.warning(f"所有数据源获取 {stock_code} 基本信息失败，返回空数据")
        return {}, "None"

    # ========== 财务分析相关统一访问方法（新增）==========

    def get_financial_report(
        self,
        stock_code: str,
        report_type: str = "利润表"
    ) -> Tuple[pd.DataFrame, str]:
        """
        获取财务报表（自动切换数据源）
        
        Args:
            stock_code: 股票代码
            report_type: 报表类型（"利润表", "资产负债表", "现金流量表"）
        
        Returns:
            Tuple[DataFrame, str]: (报表数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取 {stock_code} {report_type}...")
                df = fetcher._get_financial_report(stock_code, report_type)
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取财务报表")
                    return df, fetcher.name
                else:
                    logger.debug(f"[{fetcher.name}] 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        logger.warning(f"所有数据源获取 {stock_code} {report_type}失败，返回空数据")
        return pd.DataFrame(), "None"

    def get_financial_indicators(self, stock_code: str) -> Tuple[pd.DataFrame, str]:
        """
        获取财务分析指标（自动切换数据源）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            Tuple[DataFrame, str]: (财务指标数据, 成功的数据源名称)
        """
        errors = []
        
        for fetcher in self._fetchers:
            try:
                logger.info(f"尝试使用 [{fetcher.name}] 获取 {stock_code} 财务指标...")
                df = fetcher._get_financial_indicators(stock_code)
                
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功获取财务指标")
                    return df, fetcher.name
                else:
                    logger.debug(f"[{fetcher.name}] 返回空数据，尝试下一个数据源")
                    
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失败: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        logger.warning(f"所有数据源获取 {stock_code} 财务指标失败，返回空数据")
        return pd.DataFrame(), "None"
