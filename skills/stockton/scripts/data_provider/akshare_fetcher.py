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
