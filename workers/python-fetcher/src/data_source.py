# -*- coding: utf-8 -*-
"""
数据源适配器 - 支持多数据源自动故障切换

================================================================================
数据源详细对比与自动故障切换策略
================================================================================

【故障切换策略】
1. 初始化时：按优先级测试各数据源可用性，选择第一个可用的
2. 请求失败时：自动切换到下一个可用数据源重试
3. 指数成分股：优先使用当前数据源，失败时回退到 akshare_em
4. 所有数据源都失败时才抛出异常

【故障切换优先级】
默认顺序：akshare_tx → akshare_sina → baostock → akshare_em

================================================================================
数据源详细对比
================================================================================

【1. 网络连通性】
- akshare_tx (腾讯): ✅ 可用，无代理问题
- akshare_sina (新浪): ✅ 可用，无代理问题  
- akshare_em (东财): ❌ 可能被代理阻止
- baostock: ✅ 可用，但需登录，API稳定性较好

【2. 数据延迟】
- akshare_tx/sina/em: 实时数据，当日收盘后即可获取
- baostock: 
  * 日线数据：交易日 17:30 完成入库
  * 分钟线数据：交易日 20:30 完成入库
  * 财务数据：第二自然日 1:30 完成入库
  * 结论：日线数据有 ~17:30 的延迟

【3. 数据字段对比】与数据库表结构对比 (data_if300 等表)

数据库表字段:
  code, date, open, high, low, close, volume, amount, 
  ma5, ma10, ma20, ma60, change_pct, turnover_rate

┌─────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ 字段            │ akshare_tx   │ akshare_sina │ baostock     │ akshare_em   │
├─────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ code            │ ✅           │ ✅           │ ✅           │ ✅           │
│ date            │ ✅           │ ✅           │ ✅           │ ✅           │
│ open            │ ✅           │ ✅           │ ✅           │ ✅           │
│ high            │ ✅           │ ✅           │ ✅           │ ✅           │
│ low             │ ✅           │ ✅           │ ✅           │ ✅           │
│ close           │ ✅           │ ✅           │ ✅           │ ✅           │
│ volume          │ ✅ 股数      │ ✅ 股数      │ ✅ 股数      │ ✅ 股数      │
│ amount          │ ❌ 无        │ ✅ 元        │ ✅ 元        │ ✅ 元        │
│ ma5/10/20/60    │ ✅ 计算      │ ✅ 计算      │ ✅ 计算      │ ✅ 原始      │
│ change_pct      │ ✅ 计算      │ ✅ 原始      │ ✅ 原始      │ ✅ 原始      │
│ turnover_rate   │ ❌ 无        │ ✅           │ ✅           │ ✅           │
└─────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

【4. 单位一致性】
- volume (成交量):
  * akshare_tx: 原始数据为"手"，已转换为"股" (×100)
  * akshare_sina: "股"
  * akshare_em: "股"
  * baostock: "股"
  * ✅ 统一为"股"

- amount (成交额):
  * akshare_tx: ❌ 无此字段
  * akshare_sina: "元"
  * akshare_em: "元"
  * baostock: "元"
  * ✅ 除腾讯外统一为"元"

- change_pct (涨跌幅):
  * akshare_tx: 计算值，单位%
  * akshare_sina: 原始值，单位%
  * akshare_em: 原始值，单位%
  * baostock: 原始值，单位%
  * ✅ 统一为%

- turnover_rate (换手率):
  * akshare_tx: ❌ 无此字段
  * akshare_sina: 原始值 (小数，如0.01表示1%)
  * akshare_em: 原始值，单位%
  * baostock: 原始值 (小数，如0.01表示1%)
  * ⚠️ 新浪和baostock需要×100转换为%

【5. 指数成分股支持】
- akshare_tx: ❌ 不支持
- akshare_sina: ❌ 不支持
- akshare_em: ✅ 支持
- baostock: ⚠️ 有限支持

【6. 代码格式】
- akshare_tx/sina: sz000001/sh600000 (带市场前缀)
- akshare_em: 000001 (纯数字)
- baostock: sh.600000/sz.000001 (带点号前缀)

【7. 使用建议】
- 首选: akshare_tx (速度最快，无代理问题)
- 备选1: akshare_sina (数据完整，有换手率)
- 备选2: baostock (稳定性好，支持指数成分股，但有日线延迟)
- 备选3: akshare_em (数据最全，但可能被代理阻止)

================================================================================
"""
import logging
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
from datetime import datetime
import os
import time
import traceback
import socket
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

# 请求超时时间（秒）
REQUEST_TIMEOUT = 30

def run_with_socket_timeout(func, timeout=5, *args, **kwargs):
    """
    使用 socket 层超时控制执行函数
    这可以中断 C 扩展中的网络阻塞调用
    """
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        return func(*args, **kwargs)
    finally:
        socket.setdefaulttimeout(old_timeout)

logger = logging.getLogger(__name__)

# Monkey-patch requests 禁用代理
import requests
_original_get = requests.get

def _get_no_proxy(url, **kwargs):
    """禁用代理的 GET 请求"""
    kwargs['proxies'] = {'http': None, 'https': None}
    return _original_get(url, **kwargs)

requests.get = _get_no_proxy


def run_with_timeout(func, timeout=REQUEST_TIMEOUT, *args, **kwargs):
    """
    在单独的线程中执行函数，带超时控制
    
    Args:
        func: 要执行的函数
        timeout: 超时时间（秒）
        *args, **kwargs: 函数参数
        
    Returns:
        函数返回值
        
    Raises:
        TimeoutError: 函数执行超时
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except FutureTimeoutError:
            raise TimeoutError(f"请求超时（{timeout}秒）")


def is_hk_stock_code(code: str) -> bool:
    """
    判断是否为港股代码
    
    港股代码规则：
    - 1-5位数字代码，如 '00700' (腾讯控股), '1810' (小米集团)
    - 部分港股代码可能带有前缀，如 'hk00700', 'hk1810'
    
    Args:
        code: 股票代码
        
    Returns:
        True 如果是港股代码，False 否则
        
    Examples:
        >>> is_hk_stock_code('00700')
        True
        >>> is_hk_stock_code('hk00700')
        True
        >>> is_hk_stock_code('1810')
        True
        >>> is_hk_stock_code('hk1810')
        True
        >>> is_hk_stock_code('000001')
        False
        >>> is_hk_stock_code('600519')
        False
    """
    code = str(code).strip().lower()
    
    # 去除 hk 前缀
    if code.startswith('hk'):
        code = code[2:]
    
    # 检查是否为1-5位数字（港股代码范围00001-09999）
    if 1 <= len(code) <= 5 and code.isdigit():
        return True
    
    return False


def normalize_stock_code(code: str) -> str:
    """将股票代码转换为带市场前缀的格式 (sz000001/sh600000)"""
    code = str(code).strip()
    
    if code.startswith(('sh', 'sz', 'bj')) and '.' not in code:
        return code
    
    if code.startswith(('sh.', 'sz.', 'bj.')):
        return code.replace('.', '')
    
    if code.startswith('6'):
        return f'sh{code}'
    elif code.startswith('0') or code.startswith('3'):
        return f'sz{code}'
    elif code.startswith('68'):
        return f'sh{code}'
    elif code.startswith('8') or code.startswith('4'):
        return f'bj{code}'
    else:
        return f'sz{code}'


def to_baostock_code(code: str) -> str:
    """转换为 baostock 格式代码 (sh.600000/sz.000001)"""
    code = str(code).strip()
    
    if code.startswith(('sh.', 'sz.', 'bj.')):
        return code
    
    if code.startswith(('sh', 'sz', 'bj')):
        market = code[:2]
        num = code[2:]
        return f'{market}.{num}'
    
    if code.startswith('6'):
        return f'sh.{code}'
    elif code.startswith('0') or code.startswith('3'):
        return f'sz.{code}'
    elif code.startswith('68'):
        return f'sh.{code}'
    elif code.startswith('8') or code.startswith('4'):
        return f'bj.{code}'
    else:
        return f'sz.{code}'


class DataSourceAdapter(ABC):
    """数据源适配器基类"""
    
    name = "base"
    
    @abstractmethod
    def get_stock_history(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """获取股票历史数据"""
        pass
    
    @abstractmethod
    def get_index_components(self, index_code: str) -> List[Dict]:
        """获取指数成分股"""
        pass
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        try:
            # 使用超时控制测试连接（防止某些数据源卡住）
            run_with_timeout(self._test_connection, timeout=10)
            return True
        except TimeoutError:
            logger.warning(f"{self.name} 可用性测试超时")
            return False
        except Exception as e:
            logger.warning(f"{self.name} 不可用: {e}")
            return False
    
    def _test_connection(self):
        """测试连接（子类可覆盖）"""
        pass
    
    def _calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算均线，保留3位小数
        
        数据不足时用当天收盘价代替（前N天无法计算MA N时用close填充）
        """
        df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean().round(3)
        df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean().round(3)
        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean().round(3)
        df['ma60'] = df['close'].rolling(window=60, min_periods=1).mean().round(3)
        return df


class AkshareEastmoneyAdapter(DataSourceAdapter):
    """Akshare 东方财富数据源适配器"""
    
    name = "akshare_em"
    
    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
        except ImportError:
            raise ImportError("akshare not installed")
    
    def _test_connection(self):
        """测试连接，使用短超时避免卡住"""
        try:
            df = run_with_timeout(
                self._test_connection_impl,
                timeout=5
            )
        except TimeoutError:
            raise ConnectionError("东财连接测试超时")
    
    def _test_connection_impl(self):
        """实际测试连接逻辑"""
        df = self.ak.stock_zh_a_hist(symbol='000001', period='daily', 
                                     start_date='20230101', end_date='20230105')
        if df is None or df.empty:
            raise ConnectionError("akshare test failed")
    
    def get_stock_history(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """获取股票历史数据"""
        df = self.ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        
        if df is None or df.empty:
            return []
        
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'change_pct',
            '换手率': 'turnover_rate',
        })
        
        df = self._calculate_ma(df)
        
        records = []
        for _, row in df.iterrows():
            records.append({
                'code': code,
                'date': row['date'],
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                'amount': float(row['amount']) if pd.notna(row['amount']) else None,
                'ma5': float(row['ma5']) if pd.notna(row['ma5']) else None,
                'ma10': float(row['ma10']) if pd.notna(row['ma10']) else None,
                'ma20': float(row['ma20']) if pd.notna(row['ma20']) else None,
                'ma60': float(row['ma60']) if pd.notna(row['ma60']) else None,
                'change_pct': float(row['change_pct']) if pd.notna(row['change_pct']) else None,
                'turnover_rate': float(row['turnover_rate']) if pd.notna(row['turnover_rate']) else None,
            })
        
        return records
    
    def get_index_components(self, index_code: str) -> List[Dict]:
        """获取指数成分股"""
        df = self.ak.index_stock_cons_weight_csindex(symbol=index_code)
        
        if df is None or df.empty:
            return []
        
        components = []
        for _, row in df.iterrows():
            components.append({
                'stock_code': str(row['成分券代码']),
                'stock_name': str(row.get('成分券名称', '')),
                'weight': float(row.get('权重', 0)) if pd.notna(row.get('权重')) else None
            })
        
        return components


class AkshareSinaAdapter(DataSourceAdapter):
    """Akshare 新浪财经数据源适配器"""
    
    name = "akshare_sina"
    
    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
        except ImportError:
            raise ImportError("akshare not installed")
    
    def _test_connection(self):
        """测试连接，使用短超时避免卡住"""
        try:
            df = run_with_timeout(
                self._test_connection_impl,
                timeout=5  # 5秒超时
            )
        except TimeoutError:
            raise ConnectionError("新浪连接测试超时")
    
    def _test_connection_impl(self):
        """实际测试连接逻辑"""
        df = self.ak.stock_zh_a_daily(symbol='sz000001', start_date='20230101', end_date='20230105')
        if df is None or df.empty:
            raise ConnectionError("sina test failed")
    
    def get_stock_history(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """获取股票历史数据"""
        symbol = normalize_stock_code(code)
        
        try:
            df = self.ak.stock_zh_a_daily(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        except Exception as e:
            raise RuntimeError(f"akshare请求失败: {e}")
        
        if df is None or df.empty:
            return []
        
        try:
            df = df.rename(columns={
                'date': 'date',
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'volume': 'volume',
                'amount': 'amount',
                'turnover': 'turnover_rate',
            })
            
            try:
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            except Exception as e:
                raise RuntimeError(f"日期解析失败: {e}, 原始数据: {df['date'].tolist()[:3] if 'date' in df.columns else '无date列'}...")
            
            df = self._calculate_ma(df)
            df['change_pct'] = df['close'].pct_change() * 100
        except Exception as e:
            raise RuntimeError(f"数据处理失败: {e}")
        
        records = []
        for _, row in df.iterrows():
            records.append({
                'code': code,
                'date': row['date'],
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                'amount': float(row['amount']) if pd.notna(row['amount']) else None,
                'ma5': float(row['ma5']) if pd.notna(row['ma5']) else None,
                'ma10': float(row['ma10']) if pd.notna(row['ma10']) else None,
                'ma20': float(row['ma20']) if pd.notna(row['ma20']) else None,
                'ma60': float(row['ma60']) if pd.notna(row['ma60']) else None,
                'change_pct': float(row['change_pct']) if pd.notna(row['change_pct']) else None,
                'turnover_rate': float(row['turnover_rate']) * 100 if pd.notna(row['turnover_rate']) else None,
            })
        
        return records
    
    def get_index_components(self, index_code: str) -> List[Dict]:
        """新浪不支持获取指数成分股"""
        logger.warning(f"新浪接口不支持获取指数成分股: {index_code}")
        return []


class AkshareTencentAdapter(DataSourceAdapter):
    """Akshare 腾讯数据源适配器"""
    
    name = "akshare_tx"
    
    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
        except ImportError:
            raise ImportError("akshare not installed")
    
    def _test_connection(self):
        """测试连接，使用短超时避免卡住"""
        try:
            df = run_with_timeout(
                self._test_connection_impl,
                timeout=5
            )
        except TimeoutError:
            raise ConnectionError("腾讯连接测试超时")
    
    def _test_connection_impl(self):
        """实际测试连接逻辑"""
        df = self.ak.stock_zh_a_hist_tx(symbol='sz000001', start_date='20230101', end_date='20230105')
        if df is None or df.empty:
            raise ConnectionError("tencent test failed")
    
    def get_stock_history(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """获取股票历史数据"""
        symbol = normalize_stock_code(code)
        
        try:
            df = self.ak.stock_zh_a_hist_tx(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        except Exception as e:
            raise RuntimeError(f"akshare请求失败: {e}")
        
        if df is None or df.empty:
            return []
        
        try:
            df = df.rename(columns={
                'date': 'date',
                'open': 'open',
                'close': 'close',
                'high': 'high',
                'low': 'low',
                'amount': 'volume',
            })
            
            # 日期解析错误处理
            try:
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
            except Exception as e:
                raise RuntimeError(f"日期解析失败: {e}, 原始数据: {df['date'].tolist()[:3]}...")
            
            df['volume'] = df['volume'] * 100  # 手转股
            df = self._calculate_ma(df)
            df['change_pct'] = df['close'].pct_change() * 100
        except Exception as e:
            raise RuntimeError(f"数据处理失败: {e}")
        
        records = []
        for _, row in df.iterrows():
            records.append({
                'code': code,
                'date': row['date'],
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                'amount': None,
                'ma5': float(row['ma5']) if pd.notna(row['ma5']) else None,
                'ma10': float(row['ma10']) if pd.notna(row['ma10']) else None,
                'ma20': float(row['ma20']) if pd.notna(row['ma20']) else None,
                'ma60': float(row['ma60']) if pd.notna(row['ma60']) else None,
                'change_pct': float(row['change_pct']) if pd.notna(row['change_pct']) else None,
                'turnover_rate': None,
            })
        
        return records
    
    def get_index_components(self, index_code: str) -> List[Dict]:
        """腾讯不支持获取指数成分股"""
        logger.warning(f"腾讯接口不支持获取指数成分股: {index_code}")
        return []


class BaostockAdapter(DataSourceAdapter):
    """Baostock 数据源适配器"""
    
    name = "baostock"
    
    def __init__(self):
        self._bs = None
        self._logged_in = False
    
    @property
    def bs(self):
        """延迟导入 baostock"""
        if self._bs is None:
            try:
                import baostock as bs
                self._bs = bs
            except ImportError:
                raise ImportError("baostock not installed")
        return self._bs
    
    def _login(self):
        """登录 baostock，带超时控制"""
        if not self._logged_in:
            try:
                result = run_with_timeout(self.bs.login, timeout=10)
                if result.error_code != '0':
                    raise ConnectionError(f"Baostock login failed: {result.error_msg}")
                self._logged_in = True
                logger.info("Baostock 登录成功")
            except TimeoutError:
                raise ConnectionError("Baostock 登录超时")
    
    def _logout(self):
        """登出 baostock"""
        if self._logged_in:
            try:
                run_with_timeout(self.bs.logout, timeout=5)
            except:
                pass
            self._logged_in = False
            logger.info("Baostock 登出")
    
    def _test_connection(self):
        """测试连接，带超时控制"""
        try:
            run_with_timeout(self._test_connection_impl, timeout=15)
        except TimeoutError:
            raise ConnectionError("Baostock 连接测试超时")
    
    def _test_connection_impl(self):
        """实际测试连接逻辑"""
        self._login()
        rs = self.bs.query_history_k_data_plus(
            "sh.600000",
            "date",
            start_date='2023-01-01',
            end_date='2023-01-05',
            frequency='d',
            adjustflag='2'
        )
        if rs.error_code != '0':
            raise ConnectionError(f"Baostock test failed: {rs.error_msg}")
    
    def get_stock_history(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """获取股票历史数据，带超时控制"""
        try:
            return run_with_timeout(
                self._get_stock_history_impl,
                timeout=30,  # 30秒超时
                code=code,
                start_date=start_date,
                end_date=end_date
            )
        except TimeoutError:
            raise RuntimeError(f"baostock获取{code}超时")
    
    def _get_stock_history_impl(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """实际获取股票历史数据逻辑"""
        self._login()
        
        bs_code = to_baostock_code(code)
        start_fmt = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        end_fmt = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        
        fields = "date,code,open,high,low,close,volume,amount,turn,pctChg"
        
        rs = self.bs.query_history_k_data_plus(
            bs_code,
            fields,
            start_date=start_fmt,
            end_date=end_fmt,
            frequency='d',
            adjustflag='2'
        )
        
        if rs.error_code != '0':
            raise RuntimeError(f"Baostock query failed: {rs.error_msg}")
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            return []
        
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'turn', 'pctChg']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.rename(columns={
            'date': 'date',
            'turn': 'turnover_rate',
            'pctChg': 'change_pct',
        })
        
        df = self._calculate_ma(df)
        
        records = []
        for _, row in df.iterrows():
            records.append({
                'code': code,
                'date': row['date'],
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                'amount': float(row['amount']) if pd.notna(row['amount']) else None,
                'ma5': float(row['ma5']) if pd.notna(row['ma5']) else None,
                'ma10': float(row['ma10']) if pd.notna(row['ma10']) else None,
                'ma20': float(row['ma20']) if pd.notna(row['ma20']) else None,
                'ma60': float(row['ma60']) if pd.notna(row['ma60']) else None,
                'change_pct': float(row['change_pct']) if pd.notna(row['change_pct']) else None,
                'turnover_rate': float(row['turnover_rate']) * 100 if pd.notna(row['turnover_rate']) else None,
            })
        
        return records
    
    def get_index_components(self, index_code: str) -> List[Dict]:
        """获取指数成分股（有限支持），带超时控制"""
        try:
            return run_with_timeout(
                self._get_index_components_impl,
                timeout=20,
                index_code=index_code
            )
        except TimeoutError:
            logger.warning("baostock获取指数成分股超时")
            return []
    
    def _get_index_components_impl(self, index_code: str) -> List[Dict]:
        """实际获取指数成分股逻辑"""
        self._login()
        
        today = datetime.now().strftime('%Y-%m-%d')
        rs = self.bs.query_all_stock(day=today.replace('-', ''))
        
        if rs.error_code != '0':
            logger.error(f"Baostock query_all_stock failed: {rs.error_msg}")
            return []
        
        stock_list = []
        while (rs.error_code == '0') & rs.next():
            stock_list.append(rs.get_row_data())
        
        logger.warning("baostock 没有直接的指数成分股接口，建议配合 akshare_em 使用")
        
        components = []
        for row in stock_list[:300]:
            code = row[0]
            code_clean = code.replace('sh.', '').replace('sz.', '')
            components.append({
                'stock_code': code_clean,
                'stock_name': '',
                'weight': None
            })
        
        return components


class DataSourceManager:
    """
    数据源管理器 - 支持请求级自动故障切换
    
    故障切换策略:
    1. 初始化时按优先级选择第一个可用的数据源
    2. 请求失败时自动切换到下一个可用数据源重试
    3. 记录失败的适配器，避免在同一请求中重复尝试
    4. 所有数据源都失败时才抛出异常
    
    默认优先级: akshare_sina → akshare_em → akshare_tx → baostock
    """
    
    DEFAULT_PRIORITY = ['akshare_sina', 'akshare_em', 'akshare_tx', 'baostock']
    
    def __init__(self, preferred_source: str = 'akshare_sina', 
                 priority: List[str] = None):
        """
        初始化数据源管理器
        
        Args:
            preferred_source: 首选数据源
            priority: 自定义优先级列表
        """
        self.adapters = {}
        self.current_adapter = None
        self.priority = priority or self.DEFAULT_PRIORITY.copy()
        
        # 将首选数据源移到最前面
        if preferred_source in self.priority:
            self.priority.remove(preferred_source)
            self.priority.insert(0, preferred_source)
        
        # 注册适配器
        self._register_adapters()
        
        # 选择初始数据源
        self._select_adapter()
    
    def _register_adapters(self):
        """注册所有适配器"""
        adapters_map = {
            'akshare_em': AkshareEastmoneyAdapter,
            'akshare_sina': AkshareSinaAdapter,
            'akshare_tx': AkshareTencentAdapter,
            'baostock': BaostockAdapter,
        }
        
        for name, adapter_class in adapters_map.items():
            try:
                self.adapters[name] = adapter_class()
                logger.info(f"注册适配器: {name}")
            except Exception as e:
                logger.warning(f"无法注册 {name} 适配器: {e}")
    
    def _select_adapter(self):
        """选择数据源（初始化时），直接使用第一个适配器"""
        for name in self.priority:
            if name in self.adapters:
                adapter = self.adapters[name]
                self.current_adapter = adapter
                logger.info(f"选择数据源: {name}")
                return
        
        raise RuntimeError("没有可用的数据源")
    
    def _get_fallback_adapters(self, exclude_names: Set[str]) -> List[tuple]:
        """获取备选适配器列表（排除已失败的）"""
        fallback = []
        for name in self.priority:
            if name not in exclude_names and name in self.adapters:
                fallback.append((name, self.adapters[name]))
        return fallback
    
    def get_stock_history(self, code: str, start_date: str, end_date: str) -> List[Dict]:
        """
        获取股票历史数据，支持自动故障切换和超时控制
        
        如果当前数据源失败或超时，会自动尝试其他数据源，直到成功或所有都失败
        """
        failed_adapters = set()
        last_error = None
        
        # 首先尝试当前适配器
        if self.current_adapter:
            try:
                logger.debug(f"使用 {self.current_adapter.name} 获取 {code} 数据")
                # 使用超时控制执行请求
                return run_with_timeout(
                    self.current_adapter.get_stock_history,
                    REQUEST_TIMEOUT,
                    code, start_date, end_date
                )
            except TimeoutError as e:
                failed_adapters.add(self.current_adapter.name)
                last_error = e
                logger.warning(f"{self.current_adapter.name} 获取 {code} 超时: {e}")
            except Exception as e:
                failed_adapters.add(self.current_adapter.name)
                last_error = e
                logger.warning(f"{self.current_adapter.name} 获取 {code} 失败: {e}")
        
        # 当前适配器失败，尝试其他适配器
        for name, adapter in self._get_fallback_adapters(failed_adapters):
            try:
                logger.info(f"切换到 {name} 重试获取 {code}")
                # 使用超时控制执行请求
                result = run_with_timeout(
                    adapter.get_stock_history,
                    REQUEST_TIMEOUT,
                    code, start_date, end_date
                )
                # 成功后更新当前适配器
                self.current_adapter = adapter
                logger.info(f"故障切换成功: 切换到 {name}")
                return result
            except TimeoutError as e:
                failed_adapters.add(name)
                last_error = e
                logger.warning(f"{name} 获取 {code} 超时: {e}")
            except Exception as e:
                failed_adapters.add(name)
                last_error = e
                logger.warning(f"{name} 获取 {code} 失败: {e}")
        
        # 所有适配器都失败
        error_msg = f"所有数据源都无法获取 {code} 数据。已尝试: {', '.join(failed_adapters)}"
        logger.error(error_msg)
        if last_error:
            raise RuntimeError(f"{error_msg}. 最后一个错误: {last_error}")
        else:
            raise RuntimeError(error_msg)
    
    def get_index_components(self, index_code: str) -> List[Dict]:
        """
        获取指数成分股，支持自动故障切换和超时控制
        
        策略：
        1. 优先使用 akshare_em（支持最好）
        2. 如果失败，尝试当前适配器
        3. 最后尝试其他适配器
        """
        failed_adapters = set()
        last_error = None
        
        # 策略1: 优先使用 akshare_em（如果可用且不是当前适配器）
        if self.current_adapter and self.current_adapter.name != 'akshare_em':
            if 'akshare_em' in self.adapters:
                try:
                    logger.debug(f"使用 akshare_em 获取指数 {index_code} 成分股")
                    return run_with_timeout(
                        self.adapters['akshare_em'].get_index_components,
                        REQUEST_TIMEOUT,
                        index_code
                    )
                except TimeoutError as e:
                    failed_adapters.add('akshare_em')
                    last_error = e
                    logger.warning(f"akshare_em 获取指数成分股超时: {e}")
                except Exception as e:
                    failed_adapters.add('akshare_em')
                    last_error = e
                    logger.warning(f"akshare_em 获取指数成分股失败: {e}")
        
        # 策略2: 尝试当前适配器（如果 akshare_em 失败或不可用）
        if self.current_adapter and self.current_adapter.name not in failed_adapters:
            try:
                logger.debug(f"使用 {self.current_adapter.name} 获取指数 {index_code} 成分股")
                return run_with_timeout(
                    self.current_adapter.get_index_components,
                    REQUEST_TIMEOUT,
                    index_code
                )
            except TimeoutError as e:
                failed_adapters.add(self.current_adapter.name)
                last_error = e
                logger.warning(f"{self.current_adapter.name} 获取指数成分股超时: {e}")
            except Exception as e:
                failed_adapters.add(self.current_adapter.name)
                last_error = e
                logger.warning(f"{self.current_adapter.name} 获取指数成分股失败: {e}")
        
        # 策略3: 尝试其他适配器
        for name, adapter in self._get_fallback_adapters(failed_adapters):
            try:
                logger.info(f"切换到 {name} 重试获取指数 {index_code} 成分股")
                result = run_with_timeout(
                    adapter.get_index_components,
                    REQUEST_TIMEOUT,
                    index_code
                )
                logger.info(f"使用 {name} 成功获取指数成分股")
                return result
            except TimeoutError as e:
                failed_adapters.add(name)
                last_error = e
                logger.warning(f"{name} 获取指数成分股超时: {e}")
            except Exception as e:
                failed_adapters.add(name)
                last_error = e
                logger.warning(f"{name} 获取指数成分股失败: {e}")
        
        # 所有适配器都失败，返回空列表（非致命错误）
        logger.error(f"所有数据源都无法获取指数 {index_code} 成分股")
        return []
    
    @property
    def current_source_name(self) -> str:
        """当前数据源名称"""
        return self.current_adapter.name if self.current_adapter else "none"
