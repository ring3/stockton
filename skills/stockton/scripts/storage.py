# -*- coding: utf-8 -*-
"""
===================================
Stockton Skill - 数据存储层
===================================

职责：
1. 管理 SQLite 数据库连接（单例模式）
2. 缓存已拉取过的行情数据，减少重复调用
3. 实现智能更新逻辑（断点续传）
4. 提供数据查询接口

使用示例：
    from scripts.storage import get_db
    
    db = get_db()
    
    # 检查今日数据是否已存在
    if db.has_today_data('600519'):
        print("今日数据已存在，跳过网络请求")
    else:
        # 从网络获取并保存
        df = fetcher.get_daily_data('600519')
        db.save_daily_data(df, '600519', 'AkshareFetcher')
"""

import json
import logging
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

import pandas as pd

# 尝试导入 sqlite3（Python 内置）
try:
    import sqlite3
    _HAS_SQLITE = True
except ImportError:
    _HAS_SQLITE = False

logger = logging.getLogger(__name__)

# 数据库文件路径
DB_DIR = Path(__file__).parent.parent / "data"
DB_FILE = DB_DIR / "stock_data.db"


class DatabaseManager:
    """
    数据库管理器 - 单例模式
    
    使用 SQLite 轻量级存储，无需额外安装
    """
    
    _instance: Optional['DatabaseManager'] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径（可选，默认使用项目目录下的 data/stock_data.db）
        """
        if self._initialized:
            return
        
        if not _HAS_SQLITE:
            raise ImportError("SQLite3 不可用，请检查 Python 安装")
        
        # 设置数据库路径
        if db_path is None:
            DB_DIR.mkdir(parents=True, exist_ok=True)
            self._db_path = str(DB_FILE)
        else:
            self._db_path = db_path
        
        # 初始化数据库
        self._init_db()
        
        self._initialized = True
        logger.info(f"数据库初始化完成: {self._db_path}")
    
    def _init_db(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            # 创建日线数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    pct_chg REAL,
                    ma5 REAL,
                    ma10 REAL,
                    ma20 REAL,
                    ma60 REAL,
                    volume_ratio REAL,
                    data_source TEXT,
                    realtime_quote TEXT,
                    chip_distribution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code, date)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_code_date 
                ON stock_daily(code, date)
            """)
            
            # 创建指数成分股缓存表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS index_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_code TEXT NOT NULL,
                    index_name TEXT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    weight REAL,
                    update_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(index_code, stock_code)
                )
            """)
            
            # 创建指数成分股索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_index_stock 
                ON index_components(index_code, stock_code)
            """)
            
            conn.commit()
            conn.close()
            logger.debug("数据库表结构初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self._db_path)
    
    @classmethod
    def get_instance(cls) -> 'DatabaseManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def has_today_data(self, code: str, target_date: Optional[date] = None) -> bool:
        """
        检查是否已有指定日期的数据
        
        用于断点续传逻辑：如果已有数据则跳过网络请求
        
        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）
            
        Returns:
            是否存在数据
        """
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.strftime('%Y-%m-%d')
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT 1 FROM stock_daily WHERE code = ? AND date = ? LIMIT 1",
                (code, date_str)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"检查今日数据失败: {e}")
            return False
    
    def get_latest_data(self, code: str, days: int = 2) -> List[Dict[str, Any]]:
        """
        获取最近 N 天的数据
        
        Args:
            code: 股票代码
            days: 获取天数
            
        Returns:
            数据字典列表（按日期降序）
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM stock_daily 
                WHERE code = ? 
                ORDER BY date DESC 
                LIMIT ?
                """,
                (code, days)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取最新数据失败: {e}")
            return []
    
    def get_data_range(
        self, 
        code: str, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取指定日期范围的数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            数据字典列表
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM stock_daily 
                WHERE code = ? AND date >= ? AND date <= ?
                ORDER BY date ASC
                """,
                (code, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取数据范围失败: {e}")
            return []
    
    def save_daily_data(
        self, 
        df: pd.DataFrame, 
        code: str, 
        data_source: str = "Unknown",
        name: str = "",
        realtime_quote: Optional[Dict[str, Any]] = None,
        chip_distribution: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        保存日线数据到数据库
        
        策略：
        - 使用 INSERT OR REPLACE（存在则更新，不存在则插入）
        - 跳过无效数据
        
        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            data_source: 数据来源名称
            name: 股票名称
            realtime_quote: 实时行情数据字典（可选）
            chip_distribution: 筹码分布数据字典（可选）
            
        Returns:
            新增/更新的记录数
        """
        if df is None or df.empty:
            logger.warning(f"保存数据为空，跳过 {code}")
            return 0
        
        saved_count = 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                # 解析日期
                row_date = row.get('date')
                if isinstance(row_date, str):
                    date_str = row_date
                elif isinstance(row_date, datetime):
                    date_str = row_date.strftime('%Y-%m-%d')
                elif isinstance(row_date, pd.Timestamp):
                    date_str = row_date.strftime('%Y-%m-%d')
                else:
                    continue  # 跳过无效日期
                
                # 安全获取数值
                def safe_val(col, default=None):
                    try:
                        val = row.get(col, default)
                        if pd.isna(val):
                            return default
                        return float(val)
                    except:
                        return default
                
                # 准备实时行情JSON（仅最新日期）
                rt_json = None
                if realtime_quote and date_str == df['date'].max():
                    rt_json = json.dumps(realtime_quote, ensure_ascii=False, default=str)
                
                # 准备筹码分布JSON（仅最新日期）
                chip_json = None
                if chip_distribution and date_str == df['date'].max():
                    chip_json = json.dumps(chip_distribution, ensure_ascii=False, default=str)
                
                # 使用 INSERT OR REPLACE
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO stock_daily 
                    (code, name, date, open, high, low, close, volume, amount, 
                     pct_chg, ma5, ma10, ma20, ma60, volume_ratio, data_source, realtime_quote, chip_distribution, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        code,
                        name,
                        date_str,
                        safe_val('open'),
                        safe_val('high'),
                        safe_val('low'),
                        safe_val('close'),
                        safe_val('volume'),
                        safe_val('amount'),
                        safe_val('pct_chg'),
                        safe_val('ma5'),
                        safe_val('ma10'),
                        safe_val('ma20'),
                        safe_val('ma60'),
                        safe_val('volume_ratio'),
                        data_source,
                        rt_json,
                        chip_json
                    )
                )
                saved_count += 1
            
            conn.commit()
            conn.close()
            
            if saved_count > 0:
                logger.info(f"保存 {code} 数据成功，{saved_count} 条")
            
        except Exception as e:
            logger.error(f"保存 {code} 数据失败: {e}")
            raise
        
        return saved_count
    
    def get_analysis_context(self, code: str) -> Optional[pd.DataFrame]:
        """
        获取分析所需的数据
        
        Args:
            code: 股票代码
            
        Returns:
            DataFrame 或 None
        """
        try:
            data = self.get_latest_data(code, days=60)
            if not data:
                return None
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            return df.sort_values('date')
            
        except Exception as e:
            logger.error(f"获取分析上下文失败: {e}")
            return None
    
    def delete_old_data(self, days: int = 90):
        """
        清理过期数据
        
        Args:
            days: 保留最近 N 天的数据
        """
        try:
            cutoff_date = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM stock_daily WHERE date < ?",
                (cutoff_date,)
            )
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"清理过期数据完成，删除 {deleted} 条记录")
            
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    def clear_data(self, code: Optional[str] = None) -> bool:
        """
        清除缓存数据
        
        Args:
            code: 股票代码，为 None 时清除所有数据
            
        Returns:
            是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if code:
                cursor.execute("DELETE FROM stock_daily WHERE code = ?", (code,))
                logger.info(f"清除 {code} 的缓存数据")
            else:
                cursor.execute("DELETE FROM stock_daily")
                logger.info("清除所有缓存数据")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"清除数据失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 总记录数
            cursor.execute("SELECT COUNT(*) FROM stock_daily")
            total_records = cursor.fetchone()[0]
            
            # 股票数量
            cursor.execute("SELECT COUNT(DISTINCT code) FROM stock_daily")
            stock_count = cursor.fetchone()[0]
            
            # 日期范围
            cursor.execute("SELECT MIN(date), MAX(date) FROM stock_daily")
            min_date, max_date = cursor.fetchone()
            
            # 各股票记录数
            cursor.execute("""
                SELECT code, COUNT(*) as count 
                FROM stock_daily 
                GROUP BY code 
                ORDER BY count DESC
            """)
            stock_stats = [{"code": row[0], "records": row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_records': total_records,
                'stock_count': stock_count,
                'date_range': {'min': min_date, 'max': max_date},
                'stock_stats': stock_stats[:10],  # 只返回前10
                'db_path': self._db_path,
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'error': str(e)}


    def get_stock_name(self, code: str) -> str:
        """
        从数据库获取股票名称
        
        优先从最新日期的记录中获取名称
        
        Args:
            code: 股票代码
            
        Returns:
            股票名称，找不到返回空字符串
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT name FROM stock_daily WHERE code = ? AND name IS NOT NULL ORDER BY date DESC LIMIT 1",
                (code,)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return result[0]
            return ""
            
        except Exception as e:
            logger.debug(f"获取股票名称失败: {e}")
            return ""
    
    def save_index_components(
        self, 
        index_code: str, 
        index_name: str, 
        components: List[Dict[str, Any]]
    ) -> int:
        """
        保存指数成分股到缓存
        
        Args:
            index_code: 指数代码，如 '000300', '000905'
            index_name: 指数名称，如 '沪深300', '中证500'
            components: 成分股列表，每项包含 stock_code, stock_name, weight
            
        Returns:
            保存的记录数
        """
        if not components:
            return 0
        
        today_str = date.today().strftime('%Y-%m-%d')
        saved_count = 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for comp in components:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO index_components 
                    (index_code, index_name, stock_code, stock_name, weight, update_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        index_code,
                        index_name,
                        comp.get('stock_code', ''),
                        comp.get('stock_name', ''),
                        comp.get('weight', 0),
                        today_str
                    )
                )
                saved_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"保存 {index_name} 成分股成功，{saved_count} 条")
            return saved_count
            
        except Exception as e:
            logger.error(f"保存指数成分股失败: {e}")
            return 0
    
    def get_index_components(
        self, 
        index_code: str,
        max_age_days: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取指数成分股（带缓存）
        
        Args:
            index_code: 指数代码，如 '000300'
            max_age_days: 缓存最大天数，超过则认为过期
            
        Returns:
            成分股列表，每项包含 stock_code, stock_name, weight
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 检查缓存是否过期
            cutoff_date = (date.today() - timedelta(days=max_age_days)).strftime('%Y-%m-%d')
            
            cursor.execute(
                """
                SELECT stock_code, stock_name, weight, update_date
                FROM index_components
                WHERE index_code = ? AND update_date >= ?
                ORDER BY weight DESC
                """,
                (index_code, cutoff_date)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                return [dict(row) for row in rows]
            return []
            
        except Exception as e:
            logger.error(f"获取指数成分股失败: {e}")
            return []
    
    def is_index_cache_valid(self, index_code: str, max_age_days: int = 1) -> bool:
        """
        检查指数成分股缓存是否有效
        
        Args:
            index_code: 指数代码
            max_age_days: 最大缓存天数
            
        Returns:
            缓存是否有效
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cutoff_date = (date.today() - timedelta(days=max_age_days)).strftime('%Y-%m-%d')
            
            cursor.execute(
                "SELECT COUNT(*) FROM index_components WHERE index_code = ? AND update_date >= ?",
                (index_code, cutoff_date)
            )
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.debug(f"检查缓存有效性失败: {e}")
            return False
    
    def get_latest_tech_data(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取最新技术指标数据（用于技术面选股）
        
        从数据库获取最新的K线数据，包含技术指标：
        - ma5, ma10, ma20: 移动平均线
        - volume_ratio: 量比
        - pct_chg: 涨跌幅
        - close: 最新价
        - volume: 成交量
        
        Args:
            code: 股票代码
            
        Returns:
            技术指标字典，找不到返回 None
        """
        try:
            data = self.get_latest_data(code, days=1)
            if not data:
                return None
            
            latest = data[0]
            
            # 计算技术信号
            ma5 = latest.get('ma5', 0)
            ma10 = latest.get('ma10', 0)
            ma20 = latest.get('ma20', 0)
            close = latest.get('close', 0)
            
            # 多头排列：MA5 > MA10 > MA20
            bullish_arrangement = (ma5 > ma10 > ma20) if (ma5 and ma10 and ma20) else False
            
            # 价格位置：(close - ma20) / ma20
            price_vs_ma20 = ((close - ma20) / ma20 * 100) if ma20 else 0
            
            return {
                'code': code,
                'name': latest.get('name', ''),
                'date': latest.get('date', ''),
                'close': close,
                'open': latest.get('open', 0),
                'high': latest.get('high', 0),
                'low': latest.get('low', 0),
                'volume': latest.get('volume', 0),
                'amount': latest.get('amount', 0),
                'pct_chg': latest.get('pct_chg', 0),
                'ma5': ma5,
                'ma10': ma10,
                'ma20': ma20,
                'ma60': latest.get('ma60', 0),
                'volume_ratio': latest.get('volume_ratio', 0),
                'bullish_arrangement': bullish_arrangement,  # 多头排列
                'price_vs_ma20': price_vs_ma20,  # 相对于MA20的位置(%)
            }
            
        except Exception as e:
            logger.debug(f"获取技术指标失败: {e}")
            return None
    
    def get_momentum_data(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取动量数据（用于动量策略选股）
        
        计算多时间周期的价格动量：
        - momentum_20d: 20日涨跌幅（近1个月趋势）
        - momentum_60d: 60日涨跌幅（近3个月趋势）
        - momentum_120d: 120日涨跌幅（近半年趋势）
        - momentum_annual: 年化动量（250日）
        
        Args:
            code: 股票代码
            
        Returns:
            动量数据字典，包含：
            {
                'code': '600519',
                'momentum_20d': 15.5,      # 20日涨跌幅(%)
                'momentum_60d': 28.3,      # 60日涨跌幅(%)
                'momentum_120d': 45.2,     # 120日涨跌幅(%)
                'momentum_annual': 62.1,   # 250日涨跌幅(%)
                'trend_consistency': 0.85, # 趋势一致性（0-1，越高越好）
                'latest_price': 1400.0,    # 最新价格
            }
            数据不足返回 None
        """
        try:
            # 获取最近250天数据（用于计算各种周期动量）
            data = self.get_latest_data(code, days=250)
            if not data or len(data) < 20:
                return None
            
            # 按日期升序排列（旧的在前）
            df_data = sorted(data, key=lambda x: x.get('date', ''), reverse=False)
            
            latest = df_data[-1]
            latest_price = latest.get('close', 0)
            
            # 计算不同周期的动量
            def calc_momentum(days_ago: int) -> float:
                """计算N日前的涨跌幅"""
                if len(df_data) < days_ago + 1:
                    return 0
                past_price = df_data[-(days_ago + 1)].get('close', 0)
                if past_price and past_price > 0:
                    return (latest_price - past_price) / past_price * 100
                return 0
            
            momentum_20d = calc_momentum(20)
            momentum_60d = calc_momentum(60)
            momentum_120d = calc_momentum(120) if len(df_data) >= 121 else 0
            momentum_annual = calc_momentum(250) if len(df_data) >= 251 else 0
            
            # 计算趋势一致性（各周期动量方向一致的比例）
            # 正值越多，一致性越高
            momentums = [momentum_20d, momentum_60d]
            if momentum_120d != 0:
                momentums.append(momentum_120d)
            
            positive_count = sum(1 for m in momentums if m > 0)
            trend_consistency = positive_count / len(momentums) if momentums else 0
            
            return {
                'code': code,
                'name': latest.get('name', ''),
                'date': latest.get('date', ''),
                'latest_price': latest_price,
                'momentum_20d': round(momentum_20d, 2),
                'momentum_60d': round(momentum_60d, 2),
                'momentum_120d': round(momentum_120d, 2),
                'momentum_annual': round(momentum_annual, 2),
                'trend_consistency': round(trend_consistency, 2),
            }
            
        except Exception as e:
            logger.debug(f"获取动量数据失败: {e}")
            return None


# 便捷函数
def get_db() -> DatabaseManager:
    """获取数据库管理器实例的快捷方式"""
    return DatabaseManager.get_instance()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    db = get_db()
    print("=== 数据库测试 ===")
    
    # 测试检查今日数据
    has_data = db.has_today_data('600519')
    print(f"茅台今日是否有数据: {has_data}")
    
    # 测试保存数据
    test_df = pd.DataFrame({
        'date': [date.today().strftime('%Y-%m-%d')],
        'open': [1800.0],
        'high': [1850.0],
        'low': [1780.0],
        'close': [1820.0],
        'volume': [10000000],
        'amount': [18200000000],
        'pct_chg': [1.5],
        'ma5': [1810.0],
        'ma10': [1800.0],
        'ma20': [1790.0],
    })
    
    saved = db.save_daily_data(test_df, '600519', 'TestSource')
    print(f"保存测试数据: {saved} 条")
    
    # 测试获取数据
    data = db.get_latest_data('600519', days=1)
    print(f"获取数据: {len(data)} 条")
