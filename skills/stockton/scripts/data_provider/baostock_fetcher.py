# -*- coding: utf-8 -*-
"""
===================================
BaostockFetcher - 证券宝数据源 (Priority 2)
===================================

数据来源：baostock 库（证券宝）
特点：免费、数据权威、需登录
定位：作为 akshare 和 efinance 的备选数据源

主要用于：
- 股票基本信息查询（上市日期、行业等）
- 证券基本资料
- 历史数据备选

注意：
- 需要调用 login() 登录
- 股票代码格式：sh.600000, sz.000001
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS

logger = logging.getLogger(__name__)


class BaostockFetcher(BaseFetcher):
    """
    Baostock 数据源实现
    
    优先级：2（备选数据源）
    数据来源：证券宝（baostock）
    
    特点：
    - 需要登录（login/logout）
    - 股票代码格式：sh.600000, sz.000001
    - 数据权威可靠
    """
    
    name = "BaostockFetcher"
    priority = 2
    
    def __init__(self):
        """初始化 BaostockFetcher"""
        self._bs = None
        self._logged_in = False
        self._init_baostock()
    
    def _init_baostock(self):
        """初始化 baostock 库"""
        try:
            import baostock as bs
            self._bs = bs
            logger.info("[BaostockFetcher] baostock 库加载成功")
        except ImportError:
            logger.warning("[BaostockFetcher] baostock 未安装，请执行: pip install baostock")
            self._bs = None
    
    def _login(self) -> bool:
        """
        登录 baostock
        
        Returns:
            是否登录成功
        """
        if self._bs is None:
            return False
        
        if self._logged_in:
            return True
        
        try:
            result = self._bs.login()
            if result.error_code == '0':
                self._logged_in = True
                logger.info("[Baostock] 登录成功")
                return True
            else:
                logger.error(f"[Baostock] 登录失败: {result.error_msg}")
                return False
        except Exception as e:
            logger.error(f"[Baostock] 登录异常: {e}")
            return False
    
    def _logout(self):
        """登出 baostock"""
        if self._bs and self._logged_in:
            try:
                self._bs.logout()
                self._logged_in = False
                logger.info("[Baostock] 已登出")
            except Exception as e:
                logger.debug(f"[Baostock] 登出异常: {e}")
    
    def _to_bs_code(self, stock_code: str) -> str:
        """
        转换为 baostock 代码格式
        
        Args:
            stock_code: 原始代码，如 '600000', '000001'
            
        Returns:
            baostock 格式代码，如 'sh.600000', 'sz.000001'
        """
        code = str(stock_code).lower().strip()
        
        # 如果已经是 baostock 格式，直接返回
        if code.startswith('sh.') or code.startswith('sz.') or code.startswith('bj.'):
            return code
        
        # 判断市场
        if code.startswith('6'):
            return f"sh.{code}"
        elif code.startswith(('0', '3')):
            return f"sz.{code}"
        elif code.startswith('8') or code.startswith('4'):
            # 北交所/新三板
            return f"bj.{code}"
        else:
            # 默认按上海处理
            return f"sh.{code}"
    
    def _get_stock_basic_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息（Baostock 实现）
        
        使用 query_stock_basic 接口
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票基本信息字典
        """
        if not self._login():
            return {}
        
        result = {
            'code': stock_code,
            'name': '',
            'industry': '',
            'list_date': '',
            'total_shares': 0.0,
            'float_shares': 0.0,
            'total_mv': 0.0,
            'circ_mv': 0.0,
            'out_date': '',  # 退市日期
            'status': '',    # 上市状态
        }
        
        try:
            bs_code = self._to_bs_code(stock_code)
            logger.info(f"[Baostock] 查询 {stock_code} ({bs_code}) 基本信息...")
            
            # 查询证券基本资料
            rs = self._bs.query_stock_basic(code=bs_code)
            
            if rs.error_code != '0':
                logger.error(f"[Baostock] 查询失败: {rs.error_msg}")
                return {}
            
            # 获取数据
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                logger.warning(f"[Baostock] {stock_code} 返回空数据")
                return {}
            
            # 解析数据
            # 返回字段：code, code_name, ipoDate, outDate, type, status
            data = data_list[0]
            fields = rs.fields
            
            # 构建字典
            row_dict = dict(zip(fields, data))
            
            result['name'] = row_dict.get('code_name', '')
            result['list_date'] = row_dict.get('ipoDate', '').replace('-', '')
            result['out_date'] = row_dict.get('outDate', '')
            
            # 证券类型：1=股票，2=指数，3=其他，4=可转债，5=ETF
            sec_type = row_dict.get('type', '')
            # 上市状态：1=上市，0=退市
            status = row_dict.get('status', '')
            result['status'] = '上市' if status == '1' else '退市' if status == '0' else status
            
            logger.info(f"[Baostock] 成功获取 {stock_code} 基本信息: {result['name']}")
            return result
            
        except Exception as e:
            logger.error(f"[Baostock] 获取 {stock_code} 基本信息失败: {e}")
            return {}
    
    def query_by_name(self, name: str) -> pd.DataFrame:
        """
        通过名称模糊查询股票
        
        Args:
            name: 股票名称（支持模糊查询）
            
        Returns:
            DataFrame 包含匹配的股票列表
        """
        if not self._login():
            return pd.DataFrame()
        
        try:
            logger.info(f"[Baostock] 模糊查询名称: {name}")
            
            rs = self._bs.query_stock_basic(code_name=name)
            
            if rs.error_code != '0':
                logger.error(f"[Baostock] 查询失败: {rs.error_msg}")
                return pd.DataFrame()
            
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return pd.DataFrame()
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 转换代码格式：sh.600000 -> 600000
            df['code_pure'] = df['code'].str.replace(r'^(sh|sz|bj)\.', '', regex=True)
            
            logger.info(f"[Baostock] 找到 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"[Baostock] 模糊查询失败: {e}")
            return pd.DataFrame()
    
    def get_all_stocks(self) -> pd.DataFrame:
        """
        获取所有股票列表
        
        Returns:
            DataFrame 包含所有上市股票
        """
        if not self._login():
            return pd.DataFrame()
        
        try:
            logger.info("[Baostock] 获取所有股票列表...")
            
            # 使用 query_all_stock 获取当前日期的所有股票
            today = datetime.now().strftime('%Y-%m-%d')
            rs = self._bs.query_all_stock(day=today)
            
            if rs.error_code != '0':
                logger.error(f"[Baostock] 获取失败: {rs.error_msg}")
                return pd.DataFrame()
            
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 转换代码格式
            df['code_pure'] = df['code'].str.replace(r'^(sh|sz|bj)\.', '', regex=True)
            
            logger.info(f"[Baostock] 获取到 {len(df)} 只股票")
            return df
            
        except Exception as e:
            logger.error(f"[Baostock] 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_industry_info(self, stock_code: str) -> Dict[str, str]:
        """
        获取股票行业分类信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            包含行业信息的字典
        """
        if not self._login():
            return {}
        
        try:
            bs_code = self._to_bs_code(stock_code)
            
            logger.info(f"[Baostock] 查询 {stock_code} 行业信息...")
            
            # 查询行业分类
            rs = self._bs.query_stock_industry(code=bs_code)
            
            if rs.error_code != '0':
                logger.error(f"[Baostock] 查询失败: {rs.error_msg}")
                return {}
            
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                return {}
            
            fields = rs.fields
            data = data_list[0]
            row_dict = dict(zip(fields, data))
            
            return {
                'code': stock_code,
                'name': row_dict.get('code_name', ''),
                'industry': row_dict.get('industry', ''),
                'industry_classification': row_dict.get('industryClassification', ''),
                'update_date': row_dict.get('updateDate', ''),
            }
            
        except Exception as e:
            logger.error(f"[Baostock] 获取行业信息失败: {e}")
            return {}
    
    # ========== 必须实现的抽象方法 ==========
    
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取原始日线数据（Baostock 实现）"""
        if not self._login():
            raise DataFetchError("Baostock 未登录")
        
        try:
            bs_code = self._to_bs_code(stock_code)
            
            logger.info(f"[Baostock] 获取 {stock_code} 历史数据: {start_date} ~ {end_date}")
            
            # 查询历史K线数据
            rs = self._bs.query_history_k_data_plus(
                code=bs_code,
                fields="date,open,high,low,close,volume,amount,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"  # 复权类型：3=后复权，2=前复权，1=不复权
            )
            
            if rs.error_code != '0':
                raise DataFetchError(f"查询失败: {rs.error_msg}")
            
            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                raise DataFetchError("返回空数据")
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 添加股票代码列
            df['code'] = stock_code
            
            logger.info(f"[Baostock] 获取到 {len(df)} 条数据")
            return df
            
        except Exception as e:
            raise DataFetchError(f"获取数据失败: {e}")
    
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化数据"""
        df = df.copy()
        
        # 列名映射
        column_mapping = {
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
            'pctChg': 'pct_chg',
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # 确保 code 列存在
        df['code'] = stock_code
        
        # 选择需要的列
        keep_cols = ['code'] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]
        
        return df
    
    def _get_realtime_quote(self, stock_code: str) -> Optional[dict]:
        """
        Baostock 不支持实时行情，返回 None
        """
        logger.debug("[Baostock] 不支持实时行情查询")
        return None
    
    def _get_chip_distribution(self, stock_code: str) -> Optional[dict]:
        """
        Baostock 不支持筹码分布，返回 None
        """
        logger.debug("[Baostock] 不支持筹码分布查询")
        return None
    
    # ========== 其他抽象方法（返回空值或默认值）==========
    
    def _get_option_chain(self, underlying_code: str, expiry_date: Optional[str] = None) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持期权数据")
        return pd.DataFrame()
    
    def _get_option_iv(self, underlying_code: str) -> Optional[float]:
        logger.debug("[Baostock] 不支持期权IV")
        return None
    
    def _get_option_cp_ratio(self, underlying_code: str) -> Optional[Dict[str, Any]]:
        logger.debug("[Baostock] 不支持期权CP Ratio")
        return None
    
    def _get_futures_basis(self) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持期货贴水数据")
        return pd.DataFrame()
    
    def _get_market_indices(self) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持指数行情")
        return pd.DataFrame()
    
    def _get_market_overview(self) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持市场概览")
        return pd.DataFrame()
    
    def _get_sector_rankings(self) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持板块排行")
        return pd.DataFrame()
    
    def _get_index_components(self, index_code: str) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持指数成分股")
        return pd.DataFrame()
    
    def _get_stock_pool(self, market: str = "A股") -> pd.DataFrame:
        """获取股票池"""
        return self.get_all_stocks()
    
    def _get_industry_stocks(self, industry_name: str) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持行业成分股")
        return pd.DataFrame()
    
    def _get_industry_list(self) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持行业列表")
        return pd.DataFrame()
    
    def _get_financial_report(self, stock_code: str, report_type: str = "利润表") -> pd.DataFrame:
        logger.debug("[Baostock] 不支持财务报表")
        return pd.DataFrame()
    
    def _get_financial_indicators(self, stock_code: str) -> pd.DataFrame:
        logger.debug("[Baostock] 不支持财务指标")
        return pd.DataFrame()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    fetcher = BaostockFetcher()
    
    # 测试股票基本信息
    print("=" * 50)
    print("测试股票基本信息查询")
    print("=" * 50)
    
    test_codes = ['000001', '600519', '000333']
    
    for code in test_codes:
        print(f"\n查询 {code}:")
        info = fetcher._get_stock_basic_info(code)
        if info:
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("  查询失败")
    
    # 测试模糊查询
    print("\n" + "=" * 50)
    print("测试模糊查询（'银行'）")
    print("=" * 50)
    
    df = fetcher.query_by_name("银行")
    if not df.empty:
        print(df.head(10))
    
    # 登出
    fetcher._logout()
