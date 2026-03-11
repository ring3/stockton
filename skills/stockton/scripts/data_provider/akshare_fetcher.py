# -*- coding: utf-8 -*-
"""
===================================
AkshareFetcher - 备用数据源 (Priority 1)
===================================

数据来源：akshare 库（东方财富爬虫）
特点：免费、无需 Token、数据全面
定位：当 efinance 失败时的备用数据源

支持的代码类型：
- A股：6位数字代码
- ETF：51xxxx, 15xxxx 等
- 港股：5位数字或 hk 前缀

防封禁策略：
1. 每次请求前随机休眠 2-5 秒
2. 禁用代理环境变量
3. 失败后切换到新浪/腾讯/网易数据源
"""

import logging
import os
import random
import time
from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS

logger = logging.getLogger(__name__)


def _is_etf_code(stock_code: str) -> bool:
    """判断是否为 ETF 代码"""
    etf_prefixes = ('51', '52', '56', '58', '15', '16', '18')
    return stock_code.startswith(etf_prefixes) and len(stock_code) == 6


def _is_hk_code(stock_code: str) -> bool:
    """判断是否为港股代码"""
    code = stock_code.lower()
    if code.startswith('hk'):
        numeric_part = code[2:]
        return numeric_part.isdigit() and 1 <= len(numeric_part) <= 5
    return code.isdigit() and len(code) == 5


class AkshareFetcher(BaseFetcher):
    """
    Akshare 数据源实现

    优先级：1（主要数据源）
    数据来源：东方财富网（通过 akshare 库）
    
    A股支持多源自动切换：
    - 东方财富 (stock_zh_a_hist) - 主接口
    - 新浪财经 (stock_zh_a_daily) - 备用1
    - 腾讯财经 (stock_zh_a_hist_tx) - 备用2
    - 网易财经 (stock_zh_a_hist_163) - 备用3

    支持的 API：
    - A股：ak.stock_zh_a_hist()
    - ETF：ak.fund_etf_hist_em()
    - 港股：ak.stock_hk_hist()

    特殊策略：
    - A股支持多数据源自动切换（东方财富→新浪→腾讯→网易）
    """

    name = "AkshareFetcher"
    priority = 1

    # A股多数据源配置（当东方财富失败时自动切换）
    A_SHARE_SOURCES = [
        {
            "name": "eastmoney",
            "api": "stock_zh_a_hist",
            "symbol_format": lambda x: x,  # 无前缀
            "date_format": lambda x: x.replace("-", ""),  # YYYYMMDD
        },
        {
            "name": "sina",
            "api": "stock_zh_a_daily",
            "symbol_format": lambda x: f"sh{x}" if x.startswith("6") else f"sz{x}",
            "date_format": lambda x: x,  # YYYY-MM-DD
        },
        {
            "name": "tencent",
            "api": "stock_zh_a_hist_tx",
            "symbol_format": lambda x: f"sh{x}" if x.startswith("6") else f"sz{x}",
            "date_format": lambda x: x.replace("-", ""),  # YYYYMMDD
        },
        {
            "name": "netease",
            "api": "stock_zh_a_hist_163",
            "symbol_format": lambda x: f"0{x}" if x.startswith("6") else f"1{x}",
            "date_format": lambda x: x.replace("-", ""),  # YYYYMMDD
        },
    ]

    def __init__(self, sleep_min: float = 2.0, sleep_max: float = 5.0):
        """
        初始化 AkshareFetcher

        Args:
            sleep_min: 最小休眠时间（秒）
            sleep_max: 最大休眠时间（秒）
        """
        self.sleep_min = sleep_min
        self.sleep_max = sleep_max
        self._last_request_time: Optional[float] = None

        # 禁用代理，避免连接问题
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''

        # 延迟导入 akshare
        try:
            import akshare as ak
            self._ak = ak
            logger.info("[AkshareFetcher] akshare 初始化成功")
        except ImportError:
            raise ImportError("请安装 akshare: pip install akshare")

    def _random_sleep(self) -> None:
        """随机休眠"""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.sleep_min:
                time.sleep(self.sleep_min - elapsed)

        sleep_time = random.uniform(self.sleep_min, self.sleep_max)
        time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _is_connection_error(self, error: Exception) -> bool:
        """判断是否为连接类错误"""
        error_msg = str(error).lower()
        connection_errors = [
            'proxyerror', 'max retries exceeded', 'connection',
            'timeout', 'remote end closed', 'unable to connect', 'ssl', '443',
        ]
        return any(err in error_msg for err in connection_errors)

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从 akshare 获取原始数据
        """
        # 港股
        if _is_hk_code(stock_code):
            return self._fetch_hk_data(stock_code, start_date, end_date)

        # ETF
        if _is_etf_code(stock_code):
            return self._fetch_etf_data(stock_code, start_date, end_date)

        # A股（支持多数据源切换）
        return self._fetch_a_stock_data(stock_code, start_date, end_date)

    def _fetch_hk_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取港股数据"""
        code = stock_code.lower().replace('hk', '').zfill(5)

        self._random_sleep()
        logger.info(f"[Akshare] 调用 stock_hk_hist({code})")

        df = self._ak.stock_hk_hist(
            symbol=code,
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust="qfq"
        )

        if df is None or df.empty:
            raise DataFetchError(f"港股 {stock_code} 返回空数据")

        return df

    def _fetch_etf_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取 ETF 数据"""
        self._random_sleep()
        logger.info(f"[Akshare] 调用 fund_etf_hist_em({stock_code})")

        df = self._ak.fund_etf_hist_em(
            symbol=stock_code,
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust="qfq"
        )

        if df is None or df.empty:
            raise DataFetchError(f"ETF {stock_code} 返回空数据")

        return df

    def _fetch_a_stock_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取 A 股数据（支持多数据源自动切换）
        """
        errors = []

        for source_config in self.A_SHARE_SOURCES:
            source_name = source_config["name"]
            api_name = source_config["api"]

            try:
                self._random_sleep()

                # 获取API函数
                api_func = getattr(self._ak, api_name, None)
                if api_func is None:
                    errors.append(f"{source_name}: API不存在")
                    continue

                # 格式化股票代码
                symbol = source_config["symbol_format"](stock_code)

                # 格式化日期
                start_fmt = source_config["date_format"](start_date)
                end_fmt = source_config["date_format"](end_date)

                logger.info(f"[Akshare] 尝试从 {source_name} 获取 {stock_code}...")

                # 调用API
                if source_name == "eastmoney":
                    df = api_func(
                        symbol=symbol, period="daily",
                        start_date=start_fmt, end_date=end_fmt, adjust="qfq"
                    )
                else:
                    df = api_func(symbol=symbol, start_date=start_fmt, end_date=end_fmt)

                if df is not None and not df.empty:
                    logger.info(f"[Akshare] {source_name} 成功返回 {len(df)} 条数据")
                    # 标记数据来源
                    df['_data_source'] = source_name
                    return df
                else:
                    errors.append(f"{source_name}: 返回空数据")

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"[Akshare] {source_name} 失败: {error_msg[:80]}")

                if self._is_connection_error(e):
                    errors.append(f"{source_name}: 连接错误")
                    continue
                else:
                    errors.append(f"{source_name}: {error_msg[:100]}")

        # 所有数据源都失败
        error_str = "; ".join(errors)
        raise DataFetchError(f"所有数据源都失败: {error_str}")

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        标准化 akshare 数据

        处理不同数据源的列名差异
        """
        df = df.copy()

        # 列名映射（处理不同数据源的列名差异）
        column_mapping = {
            # 东方财富
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_chg',
            # 新浪/腾讯等英文列名
            'date': 'date',
            'open': 'open',
            'close': 'close',
            'high': 'high',
            'low': 'low',
            'volume': 'volume',
        }

        # 重命名列
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})

        # 添加股票代码列
        df['code'] = stock_code

        # 只保留需要的列
        keep_cols = ['code'] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]

        return df

    def _get_chip_distribution(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取筹码分布数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            筹码分布数据字典，获取失败返回 None
        """
        try:
            self._random_sleep()
            
            logger.info(f"[Akshare] 获取 {stock_code} 筹码分布...")
            
            # 使用 akshare 的筹码分布接口
            df = self._ak.stock_cyq_em(symbol=stock_code)
            
            if df is None or df.empty:
                logger.warning(f"[Akshare] {stock_code} 返回空数据")
                return None
            
            # 取最新一天的数据
            latest = df.iloc[-1]
            
            # 处理获利比例（可能是百分比字符串）
            profit_ratio = latest.get('获利比例', 0)
            if isinstance(profit_ratio, str) and '%' in profit_ratio:
                profit_ratio = float(profit_ratio.replace('%', '')) / 100
            
            return {
                'code': stock_code,
                'date': str(latest.get('日期', '')),
                'profit_ratio': float(profit_ratio) if profit_ratio else 0.0,
                'avg_cost': float(latest.get('平均成本', 0)) if pd.notna(latest.get('平均成本')) else 0.0,
                'concentration_90': float(latest.get('90%集中度', 0)) if pd.notna(latest.get('90%集中度')) else 0.0,
                'concentration_70': float(latest.get('70%集中度', 0)) if pd.notna(latest.get('70%集中度')) else 0.0,
            }
            
        except Exception as e:
            logger.error(f"[Akshare] 获取 {stock_code} 筹码分布失败: {e}")
            return None

    def _get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            实时行情字典，获取失败返回 None
        """
        try:
            self._random_sleep()
            
            logger.info(f"[Akshare] 获取 {stock_code} 实时行情...")
            
            # 使用 akshare 获取实时行情（东方财富）
            df = self._ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                logger.warning(f"[Akshare] 实时行情返回空数据")
                return None
            
            # 查找指定股票
            row = df[df['代码'] == stock_code]
            if row.empty:
                logger.warning(f"[Akshare] 未找到股票 {stock_code}")
                return None
            
            row = row.iloc[0]
            
            # 安全获取数值
            def safe_float(val, default=0.0):
                try:
                    if pd.isna(val):
                        return default
                    return float(val)
                except:
                    return default
            
            return {
                'code': stock_code,
                'name': str(row.get('名称', '')),
                'price': safe_float(row.get('最新价')),
                'change_pct': safe_float(row.get('涨跌幅')),
                'change_amount': safe_float(row.get('涨跌额')),
                'volume': safe_float(row.get('成交量')),
                'amount': safe_float(row.get('成交额')),
                'turnover_rate': safe_float(row.get('换手率')),
                'volume_ratio': safe_float(row.get('量比')),
                'amplitude': safe_float(row.get('振幅')),
                'high': safe_float(row.get('最高')),
                'low': safe_float(row.get('最低')),
                'open_price': safe_float(row.get('今开')),
                'pe_ratio': safe_float(row.get('市盈率-动态')),
                'pb_ratio': safe_float(row.get('市净率')),
                'total_mv': safe_float(row.get('总市值')),
                'circ_mv': safe_float(row.get('流通市值')),
            }
            
        except Exception as e:
            logger.error(f"[Akshare] 获取 {stock_code} 实时行情失败: {e}")
            return None

    def _get_market_indices(self) -> pd.DataFrame:
        """
        获取主要指数实时行情
        
        Returns:
            DataFrame 包含主要指数数据
        """
        try:
            self._random_sleep()
            logger.info("[Akshare] 获取主要指数行情...")
            
            df = self._ak.stock_zh_index_spot_sina()
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 标准化列名
            column_mapping = {
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌额': 'change_amount',
                '涨跌幅': 'change_pct',
                '成交量': 'volume',
                '成交额': 'amount',
            }
            
            for old, new in column_mapping.items():
                if old in df.columns:
                    df = df.rename(columns={old: new})
            
            # 只保留需要的列
            keep_cols = ['code', 'name', 'price', 'change_pct', 'change_amount', 'volume', 'amount']
            df = df[[col for col in keep_cols if col in df.columns]]
            
            return df
            
        except Exception as e:
            logger.error(f"[Akshare] 获取指数行情失败: {e}")
            return pd.DataFrame()

    def _get_market_overview(self) -> pd.DataFrame:
        """
        获取市场概览（全部A股实时行情）
        
        Returns:
            DataFrame 包含全部A股实时数据
        """
        try:
            self._random_sleep()
            logger.info("[Akshare] 获取市场概览...")
            
            df = self._ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"[Akshare] 获取市场概览失败: {e}")
            return pd.DataFrame()

    def _get_sector_rankings(self) -> pd.DataFrame:
        """
        获取行业板块涨跌排行
        
        Returns:
            DataFrame 包含板块数据
        """
        try:
            self._random_sleep()
            logger.info("[Akshare] 获取行业板块排行...")
            
            df = self._ak.stock_board_industry_name_em()
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            return df
            
        except Exception as e:
            logger.error(f"[Akshare] 获取板块排行失败: {e}")
            return pd.DataFrame()

    # ========== 期权数据接口实现 ==========

    def _get_option_chain(self, underlying_code: str, expiry_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取期权链数据
        
        使用 akshare 接口获取期权风险指标和行情
        """
        try:
            self._random_sleep()
            logger.info(f"[Akshare] 获取 {underlying_code} 期权链...")
            
            # 获取期权风险指标（含 IV 和 Greek）
            df_risk = self._ak.option_risk_indicator_sse()
            
            if df_risk is None or df_risk.empty:
                logger.warning(f"[Akshare] {underlying_code} 期权风险指标为空，尝试使用爬虫...")
                return self._get_option_chain_fallback(underlying_code, expiry_date)
            
            # 标准化列名
            column_mapping = {
                'CONTRACT_ID': 'code',
                'CONTRACT_SYMBOL': 'name',
                'IMPLC_VOLATLTY': 'iv',
                'DELTA_VALUE': 'delta',
                'GAMMA_VALUE': 'gamma',
                'THETA_VALUE': 'theta',
                'VEGA_VALUE': 'vega',
                'RHO_VALUE': 'rho',
            }
            
            for old, new in column_mapping.items():
                if old in df_risk.columns:
                    df_risk = df_risk.rename(columns={old: new})
            
            # 筛选指定标的的期权
            if 'code' in df_risk.columns:
                df_risk = df_risk[df_risk['code'].astype(str).str.startswith(underlying_code)]
            
            # 添加 underlying 列
            df_risk['underlying'] = underlying_code
            
            # 从期权名称解析类型（认购/认沽）
            def parse_option_type(name):
                if pd.isna(name):
                    return 'unknown'
                name = str(name)
                if '购' in name:
                    return 'call'
                elif '沽' in name:
                    return 'put'
                return 'unknown'
            
            df_risk['type'] = df_risk['name'].apply(parse_option_type)
            
            # 从 code 解析行权价（如 510050C2503A02100 -> 2.100）
            def parse_strike(code):
                if pd.isna(code):
                    return None
                code = str(code)
                # 尝试提取行权价部分
                try:
                    # 格式: 510050C2503A02100 -> 2.100
                    if len(code) >= 15:
                        strike_str = code[12:17]  # 取 02100 部分
                        return float(strike_str) / 10000
                except:
                    pass
                return None
            
            df_risk['strike'] = df_risk['code'].apply(parse_strike)
            
            # 获取期权行情数据（补充成交量、持仓量）
            try:
                df_quote = self._ak.option_current_em()
                if df_quote is not None and not df_quote.empty:
                    # 合并数据
                    if '代码' in df_quote.columns and 'code' in df_risk.columns:
                        df_quote = df_quote.rename(columns={'代码': 'code'})
                        df_risk = df_risk.merge(
                            df_quote[['code', '成交量', '持仓量']], 
                            on='code', 
                            how='left'
                        )
                        df_risk = df_risk.rename(columns={'成交量': 'volume', '持仓量': 'open_interest'})
            except Exception as e:
                logger.debug(f"[Akshare] 获取期权行情失败: {e}")
            
            logger.info(f"[Akshare] 成功获取 {len(df_risk)} 条期权数据")
            return df_risk
            
        except Exception as e:
            logger.error(f"[Akshare] 获取期权链失败: {e}，尝试使用爬虫...")
            return self._get_option_chain_fallback(underlying_code, expiry_date)

    def _get_option_chain_fallback(self, underlying_code: str, expiry_date: Optional[str] = None) -> pd.DataFrame:
        """
        使用爬虫获取期权链（当 akshare 失败时）
        """
        try:
            logger.info(f"[Akshare] 使用爬虫获取 {underlying_code} 期权链...")
            
            # 动态导入爬虫模块
            import sys
            from pathlib import Path
            scripts_path = Path(__file__).parent.parent
            if str(scripts_path) not in sys.path:
                sys.path.insert(0, str(scripts_path))
            
            from option_crawler import EastMoneyOptionCrawler
            crawler = EastMoneyOptionCrawler()
            
            return crawler.get_option_chain(underlying_code)
            
        except Exception as e:
            logger.error(f"[Akshare] 爬虫获取期权链也失败: {e}")
            return pd.DataFrame()

    def _get_option_iv(self, underlying_code: str) -> Optional[float]:
        """
        获取期权隐含波动率（加权平均）
        """
        try:
            df = self._get_option_chain(underlying_code)
            if df is None or df.empty:
                return None
            
            # 筛选有 IV 和成交量的数据
            df = df.dropna(subset=['iv', 'volume'])
            if df.empty:
                return None
            
            # 按成交量加权计算平均 IV
            weighted_iv = (df['iv'] * df['volume']).sum() / df['volume'].sum()
            return float(weighted_iv)
            
        except Exception as e:
            logger.error(f"[Akshare] 计算期权IV失败: {e}")
            return None

    def _get_option_cp_ratio(self, underlying_code: str) -> Optional[Dict[str, Any]]:
        """
        获取认购认沽比
        """
        try:
            df = self._get_option_chain(underlying_code)
            if df is None or df.empty:
                return None
            
            # 分离认购和认沽
            calls = df[df['type'] == 'call']
            puts = df[df['type'] == 'put']
            
            call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
            put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0
            call_oi = calls['open_interest'].sum() if 'open_interest' in calls.columns else 0
            put_oi = puts['open_interest'].sum() if 'open_interest' in puts.columns else 0
            
            return {
                'underlying': underlying_code,
                'volume_cp_ratio': call_volume / put_volume if put_volume > 0 else 0,
                'oi_cp_ratio': call_oi / put_oi if put_oi > 0 else 0,
                'call_volume': int(call_volume),
                'put_volume': int(put_volume),
                'call_oi': int(call_oi),
                'put_oi': int(put_oi),
                'timestamp': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"[Akshare] 计算CP Ratio失败: {e}")
            return None

    def _get_futures_basis(self) -> pd.DataFrame:
        """
        获取股指期货贴水/升水数据
        
        支持的股指期货：
        - IF: 沪深300期货 -> 对应指数 000300
        - IC: 中证500期货 -> 对应指数 000905  
        - IM: 中证1000期货 -> 对应指数 000852
        - IH: 上证50期货 -> 对应指数 000016
        """
        try:
            self._random_sleep()
            logger.info("[Akshare] 获取股指期货贴水数据...")
            
            # 股指期货配置
            futures_config = [
                {'futures_code': 'IF0', 'index_code': '000300', 'name': '沪深300'},
                {'futures_code': 'IC0', 'index_code': '000905', 'name': '中证500'},
                {'futures_code': 'IM0', 'index_code': '000852', 'name': '中证1000'},
                {'futures_code': 'IH0', 'index_code': '000016', 'name': '上证50'},
            ]
            
            results = []
            
            for config in futures_config:
                try:
                    # 获取期货主力合约最新价格
                    df_futures = self._ak.futures_main_sina(symbol=config['futures_code'])
                    if df_futures is None or df_futures.empty:
                        continue
                    
                    futures_price = df_futures['收盘价'].iloc[-1]
                    
                    # 获取对应现货指数最新价格
                    # 使用 akshare 的指数行情接口
                    if config['index_code'].startswith('000'):
                        # 上海指数
                        df_index = self._ak.stock_zh_index_spot_sina()
                        index_row = df_index[df_index['代码'] == f"sh{config['index_code']}"]
                        if index_row.empty:
                            index_row = df_index[df_index['代码'] == config['index_code']]
                    else:
                        df_index = self._ak.stock_zh_index_spot_sina()
                        index_row = df_index[df_index['代码'] == config['index_code']]
                    
                    if index_row.empty:
                        continue
                    
                    index_price = float(index_row['最新价'].iloc[0])
                    
                    # 计算贴水/升水
                    basis = futures_price - index_price
                    basis_rate = (basis / index_price) * 100 if index_price > 0 else 0
                    
                    # 估算距离到期日天数（股指期货通常是每月第三个周五到期）
                    from datetime import datetime, timedelta
                    today = datetime.now()
                    # 简单估算：假设距离下月到期日约30天
                    days_to_expiry = 30 - today.day
                    if days_to_expiry < 0:
                        days_to_expiry = 30
                    
                    # 计算年化贴水率
                    annualized_rate = basis_rate * (365 / days_to_expiry) if days_to_expiry > 0 else 0
                    
                    results.append({
                        'index_code': config['index_code'],
                        'index_name': config['name'],
                        'index_price': round(index_price, 2),
                        'futures_code': config['futures_code'],
                        'futures_name': f"{config['name']}期货",
                        'futures_price': round(futures_price, 2),
                        'basis': round(basis, 2),
                        'basis_rate': round(basis_rate, 4),
                        'annualized_rate': round(annualized_rate, 4),
                        'days_to_expiry': days_to_expiry,
                        'timestamp': datetime.now().isoformat(),
                    })
                    
                except Exception as e:
                    logger.debug(f"[Akshare] 获取 {config['name']} 贴水数据失败: {e}")
                    continue
            
            if results:
                df = pd.DataFrame(results)
                logger.info(f"[Akshare] 成功获取 {len(df)} 条期货贴水数据")
                return df
            else:
                return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"[Akshare] 获取期货贴水数据失败: {e}")
            return pd.DataFrame()

    # ========== 股票筛选相关接口实现（新增）==========

    def _get_index_components(self, index_code: str) -> pd.DataFrame:
        """
        获取指数成分股

        Args:
            index_code: 指数代码，如 '000300', '000905', '000852', '000016'

        Returns:
            DataFrame 包含列：stock_code, stock_name, weight
        """
        try:
            self._random_sleep()
            logger.info(f"[Akshare] 获取指数 {index_code} 成分股...")

            df = self._ak.index_stock_cons_weight_csindex(symbol=index_code)

            if df is not None and not df.empty:
                # 标准化列名
                column_mapping = {
                    '成分券代码': 'stock_code',
                    '成分券名称': 'stock_name',
                    '权重': 'weight',
                }
                for old, new in column_mapping.items():
                    if old in df.columns:
                        df = df.rename(columns={old: new})

                # 确保必要列存在
                if 'stock_code' in df.columns and 'stock_name' in df.columns:
                    return df[['stock_code', 'stock_name', 'weight']]

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"[Akshare] 获取指数 {index_code} 成分股失败: {e}")
            return pd.DataFrame()

    def _get_stock_pool(self, market: str = "A股") -> pd.DataFrame:
        """
        获取市场股票池

        Args:
            market: 市场范围（"A股", "沪市", "深市", "创业板", "科创板"）

        Returns:
            DataFrame 包含列：code, name, market, industry
        """
        try:
            self._random_sleep()
            logger.info(f"[Akshare] 获取 {market} 股票池...")

            # 根据市场选择对应接口
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
                # 标准化列名
                column_mapping = {
                    '代码': 'code',
                    '名称': 'name',
                    '所属行业': 'industry',
                }
                for old, new in column_mapping.items():
                    if old in df.columns:
                        df = df.rename(columns={old: new})

                # 添加市场标识
                df['market'] = market

                # 选择必要列
                cols = ['code', 'name']
                if 'industry' in df.columns:
                    cols.append('industry')
                df = df[cols]

                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"[Akshare] 获取 {market} 股票池失败: {e}")
            return pd.DataFrame()

    def _get_industry_stocks(self, industry_name: str) -> pd.DataFrame:
        """
        获取行业成分股

        Args:
            industry_name: 行业名称，如 "半导体", "白酒"

        Returns:
            DataFrame 包含列：code, name
        """
        try:
            self._random_sleep()
            logger.info(f"[Akshare] 获取行业 {industry_name} 成分股...")

            # 尝试使用板块数据接口
            try:
                df = self._ak.stock_board_industry_cons_em(symbol=industry_name)
                if df is not None and not df.empty:
                    # 标准化列名
                    if '代码' in df.columns:
                        df = df.rename(columns={'代码': 'code'})
                    if '名称' in df.columns:
                        df = df.rename(columns={'名称': 'name'})

                    if 'code' in df.columns and 'name' in df.columns:
                        return df[['code', 'name']]
            except Exception as e1:
                logger.debug(f"[Akshare] 方法1获取行业成分股失败: {e1}")

            # 备选：从全市场筛选所属行业
            try:
                df = self._ak.stock_zh_a_spot_em()
                if df is not None and not df.empty:
                    industry_stocks = df[df['所属行业'] == industry_name]
                    if not industry_stocks.empty:
                        result = industry_stocks[['代码', '名称']].copy()
                        result = result.rename(columns={'代码': 'code', '名称': 'name'})
                        return result
            except Exception as e2:
                logger.debug(f"[Akshare] 方法2获取行业成分股失败: {e2}")

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"[Akshare] 获取行业 {industry_name} 成分股失败: {e}")
            return pd.DataFrame()

    def _get_industry_list(self) -> pd.DataFrame:
        """
        获取行业/板块列表

        Returns:
            DataFrame 包含列：name, code（可选）
        """
        try:
            self._random_sleep()
            logger.info(f"[Akshare] 获取行业列表...")

            df = self._ak.stock_board_industry_name_em()

            if df is not None and not df.empty:
                # 标准化列名
                if '板块名称' in df.columns:
                    df = df.rename(columns={'板块名称': 'name'})

                if 'name' in df.columns:
                    return df[['name']]

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"[Akshare] 获取行业列表失败: {e}")
            return pd.DataFrame()

    # ========== 财务分析相关接口实现（新增）==========

    def _get_financial_report(
        self,
        stock_code: str,
        report_type: str = "利润表"
    ) -> pd.DataFrame:
        """
        获取财务报表

        Args:
            stock_code: 股票代码
            report_type: 报表类型（"利润表", "资产负债表", "现金流量表"）

        Returns:
            DataFrame 包含多期报表数据
        """
        try:
            self._random_sleep()
            logger.info(f"[Akshare] 获取 {stock_code} {report_type}...")

            # 判断市场
            if stock_code.startswith('6'):
                stock_code_full = f"{stock_code}.SH"
            else:
                stock_code_full = f"{stock_code}.SZ"

            df = self._ak.stock_financial_report_sina(
                stock=stock_code_full,
                symbol=report_type
            )

            if df is not None and not df.empty:
                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"[Akshare] 获取 {stock_code} {report_type}失败: {e}")
            return pd.DataFrame()

    def _get_financial_indicators(self, stock_code: str) -> pd.DataFrame:
        """
        获取财务分析指标

        Args:
            stock_code: 股票代码

        Returns:
            DataFrame 包含关键财务指标
        """
        try:
            self._random_sleep()
            logger.info(f"[Akshare] 获取 {stock_code} 财务指标...")

            df = self._ak.stock_financial_analysis_indicator(symbol=stock_code)

            if df is not None and not df.empty:
                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"[Akshare] 获取 {stock_code} 财务指标失败: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)

    fetcher = AkshareFetcher()

    # 测试普通股票
    print("=" * 50)
    print("测试普通股票数据获取 (akshare)")
    print("=" * 50)
    try:
        df = fetcher.get_daily_data('600519')  # 茅台
        print(f"[股票] 获取成功，共 {len(df)} 条数据")
        print(df.tail())
    except Exception as e:
        print(f"[股票] 获取失败: {e}")
