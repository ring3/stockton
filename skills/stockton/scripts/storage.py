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
