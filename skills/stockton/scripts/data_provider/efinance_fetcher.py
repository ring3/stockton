# -*- coding: utf-8 -*-
"""
===================================
EfinanceFetcher - 优先数据源 (Priority 0)
===================================

数据来源：东方财富爬虫（通过 efinance 库）
特点：免费、无需 Token、数据全面、API 简洁
仓库：https://github.com/Micro-sheep/efinance

与 AkshareFetcher 类似，但 efinance 库：
1. API 更简洁易用
2. 支持批量获取数据
3. 更稳定的接口封装

防封禁策略：
1. 每次请求前随机休眠 1.5-3.0 秒
2. 随机轮换 User-Agent
3. 失败后重试
"""

import logging
import random
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

import pandas as pd

from .base import BaseFetcher, DataFetchError, RateLimitError, STANDARD_COLUMNS

logger = logging.getLogger(__name__)

# User-Agent 池，用于随机轮换
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# 缓存实时行情数据（避免重复请求）
_realtime_cache: Dict[str, Any] = {
    'data': None,
    'timestamp': 0,
    'ttl': 60  # 60秒缓存有效期
}


def _is_etf_code(stock_code: str) -> bool:
    """
    判断代码是否为 ETF 基金

    ETF 代码规则：
    - 上交所 ETF: 51xxxx, 52xxxx, 56xxxx, 58xxxx
    - 深交所 ETF: 15xxxx, 16xxxx, 18xxxx
    """
    etf_prefixes = ('51', '52', '56', '58', '15', '16', '18')
    return stock_code.startswith(etf_prefixes) and len(stock_code) == 6


class EfinanceFetcher(BaseFetcher):
    """
    Efinance 数据源实现

    优先级：0（最高，优先于 AkshareFetcher）
    数据来源：东方财富网（通过 efinance 库封装）
    仓库：https://github.com/Micro-sheep/efinance

    主要 API：
    - ef.stock.get_quote_history(): 获取历史 K 线数据
    - ef.stock.get_base_info(): 获取股票基本信息
    - ef.stock.get_realtime_quotes(): 获取实时行情

    关键策略：
    - 每次请求前随机休眠 1.5-3.0 秒
    - 随机 User-Agent 轮换
    - 失败后重试
    """

    name = "EfinanceFetcher"
    priority = 0  # 最高优先级

    def __init__(self, sleep_min: float = 1.5, sleep_max: float = 3.0):
        """
        初始化 EfinanceFetcher

        Args:
            sleep_min: 最小休眠时间（秒）
            sleep_max: 最大休眠时间（秒）
        """
        self.sleep_min = sleep_min
        self.sleep_max = sleep_max
        self._last_request_time: Optional[float] = None

    def _enforce_rate_limit(self) -> None:
        """
        强制执行速率限制
        """
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            min_interval = self.sleep_min
            if elapsed < min_interval:
                additional_sleep = min_interval - elapsed
                logger.debug(f"补充休眠 {additional_sleep:.2f} 秒")
                time.sleep(additional_sleep)

        # 执行随机 jitter 休眠
        self.random_sleep(self.sleep_min, self.sleep_max)
        self._last_request_time = time.time()

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        从 efinance 获取原始数据

        根据代码类型自动选择 API：
        - 普通股票：使用 ef.stock.get_quote_history()
        - ETF 基金：使用 ef.fund.get_quote_history()
        """
        import efinance as ef

        # 防封禁策略
        self._enforce_rate_limit()

        # 格式化日期（efinance 使用 YYYYMMDD 格式）
        beg_date = start_date.replace('-', '')
        end_date_fmt = end_date.replace('-', '')

        # 根据代码类型选择不同的获取方法
        if _is_etf_code(stock_code):
            return self._fetch_etf_data(ef, stock_code, beg_date, end_date_fmt)
        else:
            return self._fetch_stock_data(ef, stock_code, beg_date, end_date_fmt)

    def _fetch_stock_data(self, ef, stock_code: str, beg_date: str, end_date: str) -> pd.DataFrame:
        """
        获取普通 A 股历史数据
        """
        logger.info(f"[Efinance] 调用 ef.stock.get_quote_history({stock_code}, {beg_date}, {end_date})")

        try:
            # 调用 efinance 获取 A 股日线数据
            df = ef.stock.get_quote_history(
                stock_codes=stock_code,
                beg=beg_date,
                end=end_date,
                klt=101,  # 日线
                fqt=1     # 前复权
            )

            if df is not None and not df.empty:
                logger.info(f"[Efinance] 返回 {len(df)} 行数据")
            else:
                logger.warning(f"[Efinance] 返回空数据")

            return df

        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['banned', 'blocked', '频率', 'rate', '限制']):
                raise RateLimitError(f"efinance 可能被限流: {e}") from e
            raise DataFetchError(f"efinance 获取数据失败: {e}") from e

    def _fetch_etf_data(self, ef, stock_code: str, beg_date: str, end_date: str) -> pd.DataFrame:
        """
        获取 ETF 基金历史数据
        """
        logger.info(f"[Efinance] 调用 ef.fund.get_quote_history({stock_code}, {beg_date}, {end_date})")

        try:
            df = ef.fund.get_quote_history(
                fund_code=stock_code,
                beg=beg_date,
                end=end_date,
                klt=101,  # 日线
                fqt=1     # 前复权
            )

            if df is not None and not df.empty:
                logger.info(f"[Efinance] 返回 {len(df)} 行数据")
            else:
                logger.warning(f"[Efinance] 返回空数据")

            return df

        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ['banned', 'blocked', '频率', 'rate', '限制']):
                raise RateLimitError(f"efinance 可能被限流: {e}") from e
            raise DataFetchError(f"efinance 获取 ETF 数据失败: {e}") from e

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        标准化 efinance 数据

        efinance 返回的列名（中文）：
        股票名称, 股票代码, 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率

        需要映射到标准列名：
        date, open, high, low, close, volume, amount, pct_chg
        """
        df = df.copy()

        # 列名映射
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_chg',
            '股票代码': 'code',
            '股票名称': 'name',
            '基金代码': 'code',
            '基金名称': 'name',
        }

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 如果没有 code 列，手动添加
        if 'code' not in df.columns:
            df['code'] = stock_code

        # 只保留需要的列
        keep_cols = ['code'] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]

        return df

    def _get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情数据

        Returns:
            实时行情字典，获取失败返回 None
        """
        import efinance as ef

        try:
            # 检查缓存
            current_time = time.time()
            if (_realtime_cache['data'] is not None and
                current_time - _realtime_cache['timestamp'] < _realtime_cache['ttl']):
                df = _realtime_cache['data']
                logger.debug(f"[缓存] 使用缓存的实时行情数据")
            else:
                # 防封禁策略
                self._enforce_rate_limit()

                logger.info(f"[Efinance] 调用 ef.stock.get_realtime_quotes()")
                df = ef.stock.get_realtime_quotes()

                # 更新缓存
                _realtime_cache['data'] = df
                _realtime_cache['timestamp'] = current_time

            # 查找指定股票
            code_col = '股票代码' if '股票代码' in df.columns else 'code'
            row = df[df[code_col] == stock_code]
            if row.empty:
                logger.warning(f"[Efinance] 未找到股票 {stock_code} 的实时行情")
                return None

            row = row.iloc[0]

            # 安全获取字段值
            def safe_float(val, default=0.0):
                try:
                    if pd.isna(val):
                        return default
                    return float(val)
                except:
                    return default

            # 获取列名（处理中英文列名）
            def get_col(cn_name, en_name):
                return cn_name if cn_name in df.columns else en_name
            
            name_col = get_col('股票名称', 'name')
            price_col = get_col('最新价', 'price')
            pct_col = get_col('涨跌幅', 'pct_chg')
            chg_col = get_col('涨跌额', 'change')
            vol_col = get_col('成交量', 'volume')
            amt_col = get_col('成交额', 'amount')
            turn_col = get_col('换手率', 'turnover_rate')
            vr_col = get_col('量比', 'volume_ratio')
            amp_col = get_col('振幅', 'amplitude')
            high_col = get_col('最高', 'high')
            low_col = get_col('最低', 'low')
            open_col = get_col('开盘', 'open')
            pe_col = get_col('市盈率-动态', 'pe_ratio')
            pb_col = get_col('市净率', 'pb_ratio')
            tmv_col = get_col('总市值', 'total_mv')
            cmv_col = get_col('流通市值', 'circ_mv')

            return {
                'code': stock_code,
                'name': str(row.get(name_col, '')),
                'price': safe_float(row.get(price_col)),
                'change_pct': safe_float(row.get(pct_col)),
                'change_amount': safe_float(row.get(chg_col)),
                'volume': safe_float(row.get(vol_col)),
                'amount': safe_float(row.get(amt_col)),
                'turnover_rate': safe_float(row.get(turn_col)),
                'volume_ratio': safe_float(row.get(vr_col)),
                'amplitude': safe_float(row.get(amp_col)),
                'high': safe_float(row.get(high_col)),
                'low': safe_float(row.get(low_col)),
                'open_price': safe_float(row.get(open_col)),
                'pe_ratio': safe_float(row.get(pe_col)),
                'pb_ratio': safe_float(row.get(pb_col)),
                'total_mv': safe_float(row.get(tmv_col)),
                'circ_mv': safe_float(row.get(cmv_col)),
            }

        except Exception as e:
            logger.error(f"[Efinance] 获取 {stock_code} 实时行情失败: {e}")
            return None

    def _get_chip_distribution(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取筹码分布数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            筹码分布数据字典，获取失败返回 None
        """
        try:
            import efinance as ef
            
            self._enforce_rate_limit()
            
            logger.info(f"[Efinance] 获取 {stock_code} 筹码分布...")
            
            # efinance 通过 stock.get_quote_history 获取筹码分布
            df = ef.stock.get_quote_history(stock_code, klt=101)
            
            if df is None or df.empty:
                logger.warning(f"[Efinance] {stock_code} 返回空数据")
                return None
            
            # 取最新一天的数据
            latest = df.iloc[-1]
            
            # 安全获取字段
            def safe_float(val, default=0.0):
                try:
                    if pd.isna(val):
                        return default
                    return float(val)
                except:
                    return default
            
            return {
                'code': stock_code,
                'date': str(latest.get('日期', '')),
                'profit_ratio': safe_float(latest.get('获利比例', 0)),
                'avg_cost': safe_float(latest.get('平均成本', 0)),
                'concentration_90': safe_float(latest.get('90%集中度', 0)),
                'concentration_70': safe_float(latest.get('70%集中度', 0)),
            }
            
        except Exception as e:
            logger.error(f"[Efinance] 获取 {stock_code} 筹码分布失败: {e}")
            return None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)

    fetcher = EfinanceFetcher()

    # 测试普通股票
    print("=" * 50)
    print("测试普通股票数据获取 (efinance)")
    print("=" * 50)
    try:
        df = fetcher.get_daily_data('600519')  # 茅台
        print(f"[股票] 获取成功，共 {len(df)} 条数据")
        print(df.tail())
    except Exception as e:
        print(f"[股票] 获取失败: {e}")

    # 测试 ETF 基金
    print("\n" + "=" * 50)
    print("测试 ETF 基金数据获取 (efinance)")
    print("=" * 50)
    try:
        df = fetcher.get_daily_data('512400')  # 有色龙头ETF
        print(f"[ETF] 获取成功，共 {len(df)} 条数据")
        print(df.tail())
    except Exception as e:
        print(f"[ETF] 获取失败: {e}")
