# -*- coding: utf-8 -*-
"""
===================================
Stockton Skill 统一数据访问层
===================================

职责：
1. 封装对 python-fetcher SQLite 数据库的访问
2. 提供与现有接口兼容的数据查询方法
3. 替代直接网络 fetch，改为本地数据库查询

数据库位置：
- 默认读取 workers/python-fetcher/data/stock_data.db
- 可通过环境变量 PYTHON_FETCHER_DB_PATH 自定义
"""

import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# 默认数据库路径（相对于项目根目录）
# 使用根目录下的主数据库（data/stock_data.db），包含完整数据
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "stock_data.db"

# 环境变量可覆盖默认路径
ENV_DB_PATH = os.environ.get("PYTHON_FETCHER_DB_PATH")


def _get_db_path() -> str:
    """获取数据库路径"""
    if ENV_DB_PATH:
        return ENV_DB_PATH
    return str(DEFAULT_DB_PATH)


class StocktonDataAccess:
    """
    Stockton Skill 统一数据访问层
    
    提供从 python-fetcher SQLite 数据库读取数据的方法
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据访问层
        
        Args:
            db_path: 数据库路径，None则使用默认路径
        """
        self.db_path = db_path or _get_db_path()
        self._connection: Optional[sqlite3.Connection] = None
        
        # 验证数据库可访问
        if not Path(self.db_path).exists():
            logger.warning(f"数据库文件不存在: {self.db_path}")
        else:
            logger.debug(f"数据访问层初始化完成: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（带行工厂）"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    # =========================================================================
    # 股票数据查询
    # =========================================================================
    
    def get_daily_data(self, code: str, days: int = 60) -> Optional[pd.DataFrame]:
        """
        获取股票日线数据
        
        Args:
            code: 股票代码，如 '600519'
            days: 获取最近N天的数据
            
        Returns:
            DataFrame 包含列: date, open, high, low, close, volume, amount, 
                             ma5, ma10, ma20, ma60, change_pct, turnover_rate
            无数据返回 None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 计算日期范围
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_dt = datetime.now() - timedelta(days=days * 2)  # 多取一些确保有足够交易日
            start_date = start_dt.strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT code, date, open, high, low, close, volume, amount,
                       ma5, ma10, ma20, ma60, change_pct, turnover_rate
                FROM stock_a_data
                WHERE code = ? AND date >= ? AND date <= ?
                ORDER BY date
            ''', (code, start_date, end_date))
            
            rows = cursor.fetchall()
            
            if not rows:
                logger.debug(f"未找到 {code} 的日线数据")
                return None
            
            # 转换为 DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # 计算 volume_ratio（量比 = 今日成交量 / 5日平均成交量）
            df['volume_ratio'] = self._calculate_volume_ratio(df['volume'])
            
            # 只保留最近 N 天
            if len(df) > days:
                df = df.tail(days).reset_index(drop=True)
            
            logger.debug(f"获取 {code} 日线数据: {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取 {code} 日线数据失败: {e}")
            return None
    
    def _calculate_volume_ratio(self, volume_series: pd.Series) -> pd.Series:
        """计算量比（今日成交量 / 5日平均成交量）"""
        avg_volume_5 = volume_series.rolling(window=5, min_periods=1).mean()
        volume_ratio = volume_series / avg_volume_5.shift(1)
        volume_ratio = volume_ratio.fillna(1.0)
        return volume_ratio.round(2)
    
    def get_stock_info(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息
        
        注意：当前数据库可能没有 stock_basic_info 表，
        此方法会尝试获取，失败时返回仅包含 code 的基础信息
        
        Args:
            code: 股票代码
            
        Returns:
            {
                'code': 代码,
                'name': 名称（可能为空）,
                'industry': 行业（可能为空）,
                # 以下字段暂时为空，待数据库扩展
                'pe_ratio': None,
                'pb_ratio': None,
                'roe': None,
            }
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 尝试从 stock_basic_info 表获取
            try:
                cursor.execute('''
                    SELECT code, name, industry, list_date, total_shares, 
                           float_shares, total_mv, circ_mv
                    FROM stock_basic_info
                    WHERE code = ?
                ''', (code,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    result['pe_ratio'] = None
                    result['pb_ratio'] = None
                    result['roe'] = None
                    return result
            except sqlite3.OperationalError:
                # stock_basic_info 表不存在
                logger.debug(f"stock_basic_info 表不存在，返回基础信息")
        except Exception as e:
            logger.debug(f"获取 {code} 基本信息失败: {e}")
        
        # 返回基础信息（只有 code）
        return {
            'code': code,
            'name': '',
            'industry': '',
            'pe_ratio': None,
            'pb_ratio': None,
            'roe': None,
        }
    
    def get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        info = self.get_stock_info(code)
        return info.get('name', '') if info else ''
    
    # =========================================================================
    # 股票池查询
    # =========================================================================
    
    def get_stock_pool(self, market: str = "A股") -> List[str]:
        """
        获取股票池代码列表
        
        Args:
            market: 市场范围 ("A股", "沪市", "深市", "创业板", "科创板", "北交所")
            
        Returns:
            股票代码列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 根据市场筛选
            if market == "沪市":
                # 沪市主板以 60 开头，科创板以 688 开头
                cursor.execute('''
                    SELECT DISTINCT code FROM stock_a_data
                    WHERE code LIKE '60%' OR code LIKE '688%' OR code LIKE '689%'
                ''')
            elif market == "深市":
                # 深市主板以 00 开头，创业板以 30 开头
                cursor.execute('''
                    SELECT DISTINCT code FROM stock_a_data
                    WHERE code LIKE '00%' OR code LIKE '30%'
                ''')
            elif market == "创业板":
                cursor.execute('''
                    SELECT DISTINCT code FROM stock_a_data
                    WHERE code LIKE '30%'
                ''')
            elif market == "科创板":
                cursor.execute('''
                    SELECT DISTINCT code FROM stock_a_data
                    WHERE code LIKE '688%' OR code LIKE '689%'
                ''')
            elif market == "北交所":
                cursor.execute('''
                    SELECT DISTINCT code FROM stock_a_data
                    WHERE code LIKE '8%' OR code LIKE '4%'
                ''')
            else:  # A股全部
                cursor.execute('SELECT DISTINCT code FROM stock_a_data')
            
            rows = cursor.fetchall()
            codes = [row[0] for row in rows]
            
            logger.debug(f"获取 {market} 股票池: {len(codes)} 只")
            return codes
            
        except Exception as e:
            logger.error(f"获取股票池失败: {e}")
            return []
    
    def get_index_components(self, index_name: str) -> List[str]:
        """
        获取指数成分股代码列表
        
        Args:
            index_name: 指数名称 ("沪深300", "中证500", "中证1000", "上证50")
                       或指数代码 ("000300", "000905", "000852", "000016")
            
        Returns:
            成分股代码列表
        """
        # 指数名称到代码的映射
        index_code_map = {
            '沪深300': '000300',
            '中证500': '000905',
            '中证1000': '000852',
            '上证50': '000016',
            # 也支持直接传入代码
            '000300': '000300',
            '000905': '000905',
            '000852': '000852',
            '000016': '000016',
        }
        
        index_code = index_code_map.get(index_name)
        if not index_code:
            logger.warning(f"未知指数: {index_name}")
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT stock_code FROM data_index_components
                WHERE index_code = ?
                ORDER BY weight DESC
            ''', (index_code,))
            
            rows = cursor.fetchall()
            codes = [row[0] for row in rows]
            
            logger.debug(f"获取 {index_name} 成分股: {len(codes)} 只")
            return codes
            
        except Exception as e:
            logger.error(f"获取指数成分股失败: {e}")
            return []
    
    def get_industry_list(self) -> List[str]:
        """
        获取行业/板块列表
        
        Returns:
            行业名称列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT industry FROM stock_basic_info
                WHERE industry IS NOT NULL AND industry != ''
                ORDER BY industry
            ''')
            
            rows = cursor.fetchall()
            industries = [row[0] for row in rows if row[0]]
            
            logger.debug(f"获取行业列表: {len(industries)} 个")
            return industries
            
        except Exception as e:
            logger.error(f"获取行业列表失败: {e}")
            return []
    
    def get_industry_stocks(self, industry: str) -> List[str]:
        """
        获取某行业的股票代码列表
        
        Args:
            industry: 行业名称
            
        Returns:
            股票代码列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT code FROM stock_basic_info
                WHERE industry = ?
            ''', (industry,))
            
            rows = cursor.fetchall()
            codes = [row[0] for row in rows]
            
            logger.debug(f"获取行业 {industry} 股票: {len(codes)} 只")
            return codes
            
        except Exception as e:
            logger.error(f"获取行业股票失败: {e}")
            return []
    
    # =========================================================================
    # 技术面数据
    # =========================================================================
    
    def get_latest_tech_data(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取最新技术指标数据
        
        Args:
            code: 股票代码
            
        Returns:
            {
                'close': 最新收盘价,
                'pct_chg': 涨跌幅,
                'ma5': MA5,
                'ma10': MA10,
                'ma20': MA20,
                'ma60': MA60,
                'volume_ratio': 量比,
                'bullish_arrangement': 是否多头排列,
                'price_vs_ma20': 价格相对MA20的偏离度,
            }
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT close, change_pct as pct_chg, ma5, ma10, ma20, ma60, volume
                FROM stock_a_data
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 1
            ''', (code,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            result = dict(row)
            
            # 计算量比（需要历史数据）
            cursor.execute('''
                SELECT volume FROM stock_a_data
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 6
            ''', (code,))
            
            volume_rows = cursor.fetchall()
            if len(volume_rows) >= 2:
                today_volume = volume_rows[0][0]
                avg_5d = sum([r[0] for r in volume_rows[1:6]]) / 5 if len(volume_rows) >= 6 else volume_rows[1][0]
                result['volume_ratio'] = round(today_volume / avg_5d, 2) if avg_5d > 0 else 1.0
            else:
                result['volume_ratio'] = 1.0
            
            # 判断是否多头排列
            ma5 = result.get('ma5', 0) or 0
            ma10 = result.get('ma10', 0) or 0
            ma20 = result.get('ma20', 0) or 0
            result['bullish_arrangement'] = ma5 > ma10 > ma20
            
            # 计算价格相对MA20的偏离度
            close = result.get('close', 0) or 0
            ma20 = result.get('ma20', 0) or 0
            if ma20 > 0:
                result['price_vs_ma20'] = round((close - ma20) / ma20 * 100, 2)
            else:
                result['price_vs_ma20'] = 0
            
            return result
            
        except Exception as e:
            logger.error(f"获取 {code} 技术指标失败: {e}")
            return None
    
    def get_momentum_data(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取动量数据（多周期涨跌幅）
        
        Args:
            code: 股票代码
            
        Returns:
            {
                'momentum_20d': 20日涨跌幅(%),
                'momentum_60d': 60日涨跌幅(%),
                'momentum_120d': 120日涨跌幅(%),
                'trend_consistency': 趋势一致性(0-1),
            }
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 获取最近120+天的数据
            cursor.execute('''
                SELECT date, close FROM stock_a_data
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 130
            ''', (code,))
            
            rows = cursor.fetchall()
            
            if len(rows) < 20:
                logger.debug(f"{code} 数据不足，无法计算动量")
                return None
            
            closes = [row[1] for row in rows]
            current = closes[0]
            
            result = {}
            
            # 计算各周期涨跌幅
            if len(rows) >= 20 and closes[19] > 0:
                result['momentum_20d'] = round((current - closes[19]) / closes[19] * 100, 2)
            else:
                result['momentum_20d'] = 0
            
            if len(rows) >= 60 and closes[59] > 0:
                result['momentum_60d'] = round((current - closes[59]) / closes[59] * 100, 2)
            else:
                result['momentum_60d'] = 0
            
            if len(rows) >= 120 and closes[119] > 0:
                result['momentum_120d'] = round((current - closes[119]) / closes[119] * 100, 2)
            else:
                result['momentum_120d'] = 0
            
            # 趋势一致性：各周期动量都为正的比例
            positive_count = sum([
                result['momentum_20d'] > 0,
                result['momentum_60d'] > 0,
                result['momentum_120d'] > 0 if result['momentum_120d'] != 0 else False
            ])
            valid_periods = 3 if result['momentum_120d'] != 0 else 2
            result['trend_consistency'] = round(positive_count / valid_periods, 2)
            
            return result
            
        except Exception as e:
            logger.error(f"获取 {code} 动量数据失败: {e}")
            return None
    
    # =========================================================================
    # 实时行情 & 筹码分布（空接口，待后续实现）
    # =========================================================================
    
    def get_realtime_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情（从最新日线数据获取）
        
        Args:
            code: 股票代码
            
        Returns:
            实时行情数据字典，或 None
            注意：此方法返回的是数据库中最新的日线数据，非实时推送
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT code, close as price, change_pct, volume, amount, 
                       turnover_rate, high, low, open as open_price
                FROM stock_a_data
                WHERE code = ?
                ORDER BY date DESC
                LIMIT 1
            ''', (code,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            result = dict(row)
            result['name'] = self.get_stock_name(code)
            
            # 计算涨跌额
            prev_close = result['price'] / (1 + result.get('change_pct', 0) / 100) if result.get('change_pct') else result['price']
            result['change_amount'] = round(result['price'] - prev_close, 2)
            
            # 以下字段暂时为空
            result['volume_ratio'] = None
            result['amplitude'] = None
            result['pe_ratio'] = None
            result['pb_ratio'] = None
            result['total_mv'] = None
            result['circ_mv'] = None
            
            return result
            
        except Exception as e:
            logger.error(f"获取 {code} 实时行情失败: {e}")
            return None
    
    def get_chip_distribution(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取筹码分布数据（空接口，待数据库扩展）
        
        Args:
            code: 股票代码
            
        Returns:
            None（暂不支持）
        """
        logger.debug(f"筹码分布数据暂不支持: {code}")
        return None
    
    # =========================================================================
    # 财务数据（空接口，待数据库扩展）
    # =========================================================================
    
    def get_financial_data(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取财务数据（空接口，待数据库扩展）
        
        当前仅返回基本信息中的字段，估值数据(PE/PB/ROE)暂时为空
        
        Args:
            code: 股票代码
            
        Returns:
            {
                'code': 代码,
                'name': 名称,
                'industry': 行业,
                'total_mv': 总市值,
                # 以下字段暂时为空
                'pe_ratio': None,
                'pb_ratio': None,
                'roe': None,
                'revenue_growth': None,
                'profit_growth': None,
                'debt_ratio': None,
                'gross_margin': None,
                'net_margin': None,
                'total_score': 0,
            }
        """
        info = self.get_stock_info(code)
        
        if not info:
            return None
        
        # 构建财务数据结构（大量字段为空，待数据库扩展）
        result = {
            'code': info.get('code', code),
            'name': info.get('name', ''),
            'industry': info.get('industry', ''),
            'total_mv': info.get('total_mv', 0),
            # 估值数据（待扩展）
            'pe_ratio': None,
            'pb_ratio': None,
            'roe': None,
            # 成长数据（待扩展）
            'revenue_growth': None,
            'profit_growth': None,
            # 财务指标（待扩展）
            'debt_ratio': None,
            'gross_margin': None,
            'net_margin': None,
            # 综合评分
            'total_score': 0,
        }
        
        return result


# =============================================================================
# 便捷函数（模块级别）
# =============================================================================

_data_access: Optional[StocktonDataAccess] = None


def get_data_access() -> StocktonDataAccess:
    """获取数据访问层实例（单例模式）"""
    global _data_access
    if _data_access is None:
        _data_access = StocktonDataAccess()
    return _data_access


def get_daily_data(code: str, days: int = 60) -> Optional[pd.DataFrame]:
    """便捷函数：获取日线数据"""
    return get_data_access().get_daily_data(code, days)


def get_stock_info(code: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取股票基本信息"""
    return get_data_access().get_stock_info(code)


def get_stock_name(code: str) -> str:
    """便捷函数：获取股票名称"""
    return get_data_access().get_stock_name(code)


def get_stock_pool(market: str = "A股") -> List[str]:
    """便捷函数：获取股票池"""
    return get_data_access().get_stock_pool(market)


def get_index_components(index_name: str) -> List[str]:
    """便捷函数：获取指数成分股"""
    return get_data_access().get_index_components(index_name)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    dal = StocktonDataAccess()
    
    # 测试获取日线数据
    print("=" * 60)
    print("测试: 获取日线数据")
    print("=" * 60)
    df = dal.get_daily_data('600519', days=10)
    if df is not None:
        print(f"获取到 {len(df)} 条数据")
        print(df.tail())
    else:
        print("无数据")
    
    # 测试获取股票信息
    print("\n" + "=" * 60)
    print("测试: 获取股票信息")
    print("=" * 60)
    info = dal.get_stock_info('600519')
    print(info)
    
    # 测试获取股票池
    print("\n" + "=" * 60)
    print("测试: 获取股票池")
    print("=" * 60)
    pool = dal.get_stock_pool("沪市")
    print(f"沪市股票数量: {len(pool)}")
    if pool:
        print(f"前5只: {pool[:5]}")
