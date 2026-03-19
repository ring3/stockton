# -*- coding: utf-8 -*-
"""
本地 SQLite 数据库管理
用于临时存储从 akshare 获取的数据
"""
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalDatabase:
    """本地 SQLite 数据库"""
    
    # A股统一数据表（所有A股股票、指数成分股、ETF都存到这里）
    STOCK_A_TABLE = 'stock_a_data'
    # 港股统一数据表
    STOCK_H_TABLE = 'stock_h_data'
    # 自选股列表表
    WATCHLIST_TABLE = 'watchlist'
    
    # ETF代码映射（用于元数据）
    ETF_CODES = {
        '510050': '上证50ETF',
        '510300': '沪深300ETF',
        '588000': '科创50ETF',
        '159915': '创业板ETF',
        '510500': '中证500ETF',
    }
    
    # 股票基本信息表
    STOCK_INFO_TABLE = 'stock_basic_info'
    
    def __init__(self, db_path: str = './data/stock_data.db'):
        """
        初始化本地数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_directory()
        self._init_tables()
    
    def _ensure_directory(self):
        """确保数据库目录存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """初始化所有表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 创建指数成分股表
        self._create_index_components_table(cursor)
        logger.info(f"初始化指数成分股表: data_index_components")
        
        # 创建A股统一数据表（所有A股股票、指数成分股、ETF都存到这里）
        self._create_stock_a_table(cursor)
        logger.info(f"初始化A股数据表: {self.STOCK_A_TABLE}")
        
        # 创建港股统一数据表
        self._create_stock_h_table(cursor)
        logger.info(f"初始化港股数据表: {self.STOCK_H_TABLE}")
        
        # 创建自选股列表表
        self._create_watchlist_table(cursor)
        logger.info(f"初始化自选股表: {self.WATCHLIST_TABLE}")
        
        # 创建元数据表，记录最后同步时间
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_metadata (
                code TEXT PRIMARY KEY,
                code_type TEXT,  -- 'index' 或 'etf'
                last_sync_date TEXT,
                record_count INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建股票基本信息表
        self._create_stock_info_table(cursor)
        logger.info(f"初始化股票信息表: {self.STOCK_INFO_TABLE}")
        
        conn.commit()
        conn.close()
        logger.info(f"本地数据库初始化完成: {self.db_path}")
    
    def _create_stock_a_table(self, cursor: sqlite3.Cursor):
        """创建A股统一数据表（合并沪深300、中证500等A股数据）"""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.STOCK_A_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                amount REAL,
                ma5 REAL,
                ma10 REAL,
                ma20 REAL,
                ma60 REAL,
                change_pct REAL,
                turnover_rate REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, date)
            )
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_a_code_date 
            ON {self.STOCK_A_TABLE}(code, date)
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_a_date 
            ON {self.STOCK_A_TABLE}(date)
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_a_code 
            ON {self.STOCK_A_TABLE}(code)
        ''')
    
    def _create_stock_h_table(self, cursor: sqlite3.Cursor):
        """创建港股统一数据表"""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.STOCK_H_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                amount REAL,
                ma5 REAL,
                ma10 REAL,
                ma20 REAL,
                ma60 REAL,
                change_pct REAL,
                turnover_rate REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(code, date)
            )
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_h_code_date 
            ON {self.STOCK_H_TABLE}(code, date)
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_h_date 
            ON {self.STOCK_H_TABLE}(date)
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_h_code 
            ON {self.STOCK_H_TABLE}(code)
        ''')
    
    def _create_watchlist_table(self, cursor: sqlite3.Cursor):
        """创建自选股列表表"""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.WATCHLIST_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,      -- 股票代码
                name TEXT,                       -- 股票名称
                market_type TEXT NOT NULL,       -- 'A' 或 'H'
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_sync_date TEXT,             -- 最后同步日期
                is_active INTEGER DEFAULT 1      -- 是否活跃（1=是，0=否）
            )
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_watchlist_code 
            ON {self.WATCHLIST_TABLE}(code)
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_watchlist_market 
            ON {self.WATCHLIST_TABLE}(market_type)
        ''')
    
    def _create_index_components_table(self, cursor: sqlite3.Cursor):
        """创建指数成分股表"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_index_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_code TEXT NOT NULL,        -- 指数代码 (如 '000300')
                index_name TEXT,                 -- 指数名称
                stock_code TEXT NOT NULL,        -- 成分股代码
                stock_name TEXT,                 -- 成分股名称
                weight REAL,                     -- 权重
                update_date TEXT,                -- 更新日期
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(index_code, stock_code)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_components_index_code 
            ON data_index_components(index_code)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_components_stock_code 
            ON data_index_components(stock_code)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_components_update_date 
            ON data_index_components(update_date)
        ''')
    
    def _create_stock_info_table(self, cursor: sqlite3.Cursor):
        """创建股票基本信息表"""
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.STOCK_INFO_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,       -- 股票代码
                name TEXT,                       -- 股票名称
                industry TEXT,                   -- 所属行业
                list_date TEXT,                  -- 上市日期 (YYYYMMDD)
                total_shares REAL,               -- 总股本
                float_shares REAL,               -- 流通股本
                total_mv REAL,                   -- 总市值
                circ_mv REAL,                    -- 流通市值
                data_source TEXT,                -- 数据来源
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_info_code 
            ON {self.STOCK_INFO_TABLE}(code)
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_info_industry 
            ON {self.STOCK_INFO_TABLE}(industry)
        ''')
        cursor.execute(f'''
            CREATE INDEX IF NOT EXISTS idx_stock_info_updated 
            ON {self.STOCK_INFO_TABLE}(updated_at)
        ''')
    
    def save_prices(self, table_name: str, prices: List[Dict]) -> int:
        """
        保存价格数据到指定表
        
        Args:
            table_name: 表名
            prices: 价格数据列表
            
        Returns:
            插入的记录数
        """
        if not prices:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        try:
            for price in prices:
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {table_name} 
                    (code, date, open, high, low, close, volume, amount,
                     ma5, ma10, ma20, ma60, change_pct, turnover_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    price.get('code'),
                    price.get('date'),
                    price.get('open'),
                    price.get('high'),
                    price.get('low'),
                    price.get('close'),
                    price.get('volume'),
                    price.get('amount'),
                    price.get('ma5'),
                    price.get('ma10'),
                    price.get('ma20'),
                    price.get('ma60'),
                    price.get('change_pct'),
                    price.get('turnover_rate'),
                ))
                inserted += 1
            
            conn.commit()
            logger.info(f"表 {table_name}: 保存 {inserted} 条记录")
            
        except Exception as e:
            logger.error(f"保存到表 {table_name} 失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
        
        return inserted
    
    def get_prices(self, table_name: str, code: str = None, 
                   start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        查询价格数据
        
        Args:
            table_name: 表名
            code: 股票代码（可选，为None则查询所有）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            价格数据列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        params = []
        
        if code:
            query += " AND code = ?"
            params.append(code)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_prices_for_sync(self, table_name: str) -> List[Dict]:
        """
        获取表中所有价格数据（用于同步到Workers）
        
        Args:
            table_name: 表名
            
        Returns:
            所有价格数据
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT code, date, open, high, low, close, volume, amount,
                   ma5, ma10, ma20, ma60, change_pct, turnover_rate
            FROM {table_name}
            ORDER BY code, date
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    

    
    def update_sync_metadata(self, code: str, code_type: str, 
                            last_date: str, count: int):
        """更新同步元数据"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sync_metadata 
            (code, code_type, last_sync_date, record_count, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (code, code_type, last_date, count, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_sync_metadata(self, code: str) -> Optional[Dict]:
        """获取同步元数据"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sync_metadata WHERE code = ?
        ''', (code,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_latest_date(self, table_name: str, code: str) -> Optional[str]:
        """
        获取某股票在表中的最新日期
        
        Args:
            table_name: 表名
            code: 股票代码
            
        Returns:
            最新日期 (YYYY-MM-DD)，无数据则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                SELECT MAX(date) as latest_date 
                FROM {table_name} 
                WHERE code = ?
            ''', (code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row['latest_date']:
                return row['latest_date']
            return None
            
        except Exception as e:
            logger.error(f"获取最新日期失败 {table_name}/{code}: {e}")
            conn.close()
            return None
    
    def get_stocks_in_table(self, table_name: str) -> List[str]:
        """
        获取表中所有已存在的股票代码
        
        Args:
            table_name: 表名
            
        Returns:
            股票代码列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                SELECT DISTINCT code 
                FROM {table_name}
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [row['code'] for row in rows]
            
        except Exception as e:
            logger.error(f"获取股票列表失败 {table_name}: {e}")
            conn.close()
            return []
    
    def get_table_stats(self) -> Dict[str, int]:
        """获取stock_a_data表统计信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # stock_a_data 表统计（按代码分组）
        try:
            cursor.execute(f'''
                SELECT code, COUNT(*) FROM {self.STOCK_A_TABLE} 
                GROUP BY code
            ''')
            for row in cursor.fetchall():
                stats[row[0]] = row[1]
            
            # 总计
            cursor.execute(f'SELECT COUNT(*) FROM {self.STOCK_A_TABLE}')
            stats['TOTAL'] = cursor.fetchone()[0]
        except Exception as e:
            logger.warning(f"获取stock_a_data表统计失败: {e}")
            stats['TOTAL'] = 0
        
        conn.close()
        return stats

    # ============================================================
    # 指数成分股相关方法
    # ============================================================
    
    def save_index_components(self, index_code: str, index_name: str, 
                              components: List[Dict]) -> int:
        """
        保存指数成分股数据
        
        Args:
            index_code: 指数代码
            index_name: 指数名称
            components: 成分股数据列表，每项包含 stock_code, stock_name, weight
            
        Returns:
            插入/更新的记录数
        """
        if not components:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        inserted = 0
        
        try:
            # 先清空该指数的旧数据
            cursor.execute('''
                DELETE FROM data_index_components WHERE index_code = ?
            ''', (index_code,))
            
            # 插入新数据
            for comp in components:
                cursor.execute('''
                    INSERT INTO data_index_components 
                    (index_code, index_name, stock_code, stock_name, weight, update_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    index_code,
                    index_name,
                    comp.get('stock_code'),
                    comp.get('stock_name'),
                    comp.get('weight'),
                    today
                ))
                inserted += 1
            
            conn.commit()
            logger.info(f"指数 {index_code}: 保存 {inserted} 只成分股")
            
        except Exception as e:
            logger.error(f"保存指数 {index_code} 成分股失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
        
        return inserted
    
    def get_index_components(self, index_code: str) -> List[Dict]:
        """
        从本地数据库获取指数成分股
        
        Args:
            index_code: 指数代码
            
        Returns:
            成分股数据列表，每项包含 stock_code, stock_name, weight
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT stock_code, stock_name, weight, update_date
                FROM data_index_components
                WHERE index_code = ?
                ORDER BY weight DESC
            ''', (index_code,))
            
            rows = cursor.fetchall()
            conn.close()
            
            components = []
            for row in rows:
                components.append({
                    'stock_code': row['stock_code'],
                    'stock_name': row['stock_name'],
                    'weight': row['weight'],
                    'update_date': row['update_date']
                })
            
            return components
            
        except Exception as e:
            logger.error(f"获取指数 {index_code} 成分股失败: {e}")
            conn.close()
            return []
    
    def get_index_components_update_date(self, index_code: str) -> Optional[str]:
        """
        获取指数成分股的最后更新日期
        
        Args:
            index_code: 指数代码
            
        Returns:
            最后更新日期 (YYYY-MM-DD)，无数据则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT MAX(update_date) as latest_date
                FROM data_index_components
                WHERE index_code = ?
            ''', (index_code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row and row['latest_date']:
                return row['latest_date']
            return None
            
        except Exception as e:
            logger.error(f"获取指数 {index_code} 更新日期失败: {e}")
            conn.close()
            return None
    
    def needs_components_update(self, index_code: str, force: bool = False) -> bool:
        """
        检查指数成分股是否需要更新（每月更新一次）
        
        Args:
            index_code: 指数代码
            force: 是否强制更新
            
        Returns:
            是否需要更新
        """
        if force:
            return True
        
        latest_date = self.get_index_components_update_date(index_code)
        
        if latest_date is None:
            logger.info(f"指数 {index_code}: 本地无成分股数据，需要获取")
            return True
        
        # 检查是否超过30天
        latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
        days_diff = (datetime.now() - latest_dt).days
        
        if days_diff >= 30:
            logger.info(f"指数 {index_code}: 成分股数据已 {days_diff} 天未更新，需要更新")
            return True
        else:
            logger.info(f"指数 {index_code}: 成分股数据 {days_diff} 天前更新，无需更新")
            return False
    
    def get_all_index_components_stats(self) -> Dict[str, Dict]:
        """
        获取所有指数成分股的统计信息
        
        Returns:
            统计信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # 查询表中所有存在的指数代码
            cursor.execute('''
                SELECT DISTINCT index_code FROM data_index_components
            ''')
            index_codes = [row[0] for row in cursor.fetchall()]
            
            for index_code in index_codes:
                cursor.execute('''
                    SELECT COUNT(*) as count, MAX(update_date) as latest_date
                    FROM data_index_components
                    WHERE index_code = ?
                ''', (index_code,))
                
                row = cursor.fetchone()
                stats[index_code] = {
                    'count': row['count'] if row else 0,
                    'latest_date': row['latest_date'] if row else None
                }
            
            conn.close()
            
        except Exception as e:
            logger.error(f"获取成分股统计失败: {e}")
            conn.close()
        
        return stats
    
    # ============================================================
    # 自选股列表相关方法
    # ============================================================
    
    def add_to_watchlist(self, code: str, name: str = None, market_type: str = 'A') -> bool:
        """
        添加股票到自选股列表
        
        Args:
            code: 股票代码
            name: 股票名称（可选）
            market_type: 'A' 或 'H'
            
        Returns:
            是否成功添加
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                INSERT OR REPLACE INTO {self.WATCHLIST_TABLE} 
                (code, name, market_type, is_active)
                VALUES (?, ?, ?, 1)
            ''', (code, name, market_type))
            
            conn.commit()
            conn.close()
            logger.info(f"添加到自选股: {code} ({name}) [{market_type}股]")
            return True
            
        except Exception as e:
            logger.error(f"添加自选股失败 {code}: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def remove_from_watchlist(self, code: str) -> bool:
        """
        从自选股列表移除股票
        
        Args:
            code: 股票代码
            
        Returns:
            是否成功移除
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                DELETE FROM {self.WATCHLIST_TABLE} WHERE code = ?
            ''', (code,))
            
            conn.commit()
            conn.close()
            logger.info(f"从自选股移除: {code}")
            return True
            
        except Exception as e:
            logger.error(f"移除自选股失败 {code}: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def is_in_watchlist(self, code: str) -> bool:
        """
        检查股票是否在自选股列表中
        
        Args:
            code: 股票代码
            
        Returns:
            是否在列表中
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                SELECT COUNT(*) FROM {self.WATCHLIST_TABLE} WHERE code = ?
            ''', (code,))
            
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
            
        except Exception as e:
            logger.error(f"检查自选股失败 {code}: {e}")
            conn.close()
            return False
    
    def get_watchlist(self, market_type: str = None) -> List[Dict]:
        """
        获取自选股列表
        
        Args:
            market_type: 'A' 或 'H'，None则获取全部
            
        Returns:
            自选股列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if market_type:
                cursor.execute(f'''
                    SELECT code, name, market_type, added_at, last_sync_date
                    FROM {self.WATCHLIST_TABLE}
                    WHERE market_type = ? AND is_active = 1
                    ORDER BY added_at
                ''', (market_type,))
            else:
                cursor.execute(f'''
                    SELECT code, name, market_type, added_at, last_sync_date
                    FROM {self.WATCHLIST_TABLE}
                    WHERE is_active = 1
                    ORDER BY added_at
                ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'code': row['code'],
                'name': row['name'],
                'market_type': row['market_type'],
                'added_at': row['added_at'],
                'last_sync_date': row['last_sync_date']
            } for row in rows]
            
        except Exception as e:
            logger.error(f"获取自选股列表失败: {e}")
            conn.close()
            return []
    
    def update_watchlist_sync_date(self, code: str, sync_date: str):
        """
        更新自选股的最后同步日期
        
        Args:
            code: 股票代码
            sync_date: 同步日期 (YYYY-MM-DD)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                UPDATE {self.WATCHLIST_TABLE}
                SET last_sync_date = ?
                WHERE code = ?
            ''', (sync_date, code))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新自选股同步日期失败 {code}: {e}")
            conn.rollback()
            conn.close()
    
    def get_watchlist_stock_info(self, code: str) -> Optional[Dict]:
        """
        获取自选股的详细信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票信息字典，不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                SELECT code, name, market_type, added_at, last_sync_date
                FROM {self.WATCHLIST_TABLE}
                WHERE code = ?
            ''', (code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'code': row['code'],
                    'name': row['name'],
                    'market_type': row['market_type'],
                    'added_at': row['added_at'],
                    'last_sync_date': row['last_sync_date']
                }
            return None
            
        except Exception as e:
            logger.error(f"获取自选股信息失败 {code}: {e}")
            conn.close()
            return None
    
    # ============================================================
    # 股票基本信息相关方法
    # ============================================================
    
    def save_stock_basic_info(self, info: Dict, data_source: str = '') -> bool:
        """
        保存股票基本信息
        
        Args:
            info: 股票信息字典，必须包含 'code' 和 'name' 字段
            data_source: 数据来源标识
            
        Returns:
            是否保存成功
        """
        if not info or not info.get('code'):
            logger.warning("保存股票信息失败: 数据为空或没有code")
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                INSERT OR REPLACE INTO {self.STOCK_INFO_TABLE} 
                (code, name, industry, list_date, total_shares, float_shares,
                 total_mv, circ_mv, data_source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                info.get('code'),
                info.get('name'),
                info.get('industry'),
                info.get('list_date'),
                info.get('total_shares'),
                info.get('float_shares'),
                info.get('total_mv'),
                info.get('circ_mv'),
                data_source,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            logger.debug(f"保存股票信息成功: {info.get('code')} - {info.get('name')}")
            return True
            
        except Exception as e:
            logger.error(f"保存股票信息失败 {info.get('code')}: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def get_stock_basic_info(self, code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            股票信息字典，不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                SELECT code, name, industry, list_date, total_shares, float_shares,
                       total_mv, circ_mv, data_source, updated_at
                FROM {self.STOCK_INFO_TABLE}
                WHERE code = ?
            ''', (code,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'code': row['code'],
                    'name': row['name'],
                    'industry': row['industry'],
                    'list_date': row['list_date'],
                    'total_shares': row['total_shares'],
                    'float_shares': row['float_shares'],
                    'total_mv': row['total_mv'],
                    'circ_mv': row['circ_mv'],
                    'data_source': row['data_source'],
                    'updated_at': row['updated_at']
                }
            return None
            
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            conn.close()
            return None
    
    def batch_save_stock_basic_info(self, info_list: List[Dict], data_source: str = '') -> int:
        """
        批量保存股票基本信息
        
        Args:
            info_list: 股票信息字典列表
            data_source: 数据来源标识
            
        Returns:
            成功保存的数量
        """
        if not info_list:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        saved = 0
        try:
            for info in info_list:
                if not info or not info.get('code'):
                    continue
                    
                cursor.execute(f'''
                    INSERT OR REPLACE INTO {self.STOCK_INFO_TABLE} 
                    (code, name, industry, list_date, total_shares, float_shares,
                     total_mv, circ_mv, data_source, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    info.get('code'),
                    info.get('name'),
                    info.get('industry'),
                    info.get('list_date'),
                    info.get('total_shares'),
                    info.get('float_shares'),
                    info.get('total_mv'),
                    info.get('circ_mv'),
                    data_source,
                    datetime.now().isoformat()
                ))
                saved += 1
            
            conn.commit()
            logger.info(f"批量保存股票信息成功: {saved} 只")
            
        except Exception as e:
            logger.error(f"批量保存股票信息失败: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return saved
    
    def get_all_stock_basic_info(self) -> List[Dict]:
        """
        获取所有股票基本信息
        
        Returns:
            股票信息列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                SELECT code, name, industry, list_date, total_shares, float_shares,
                       total_mv, circ_mv, data_source, updated_at
                FROM {self.STOCK_INFO_TABLE}
                ORDER BY code
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'code': row['code'],
                'name': row['name'],
                'industry': row['industry'],
                'list_date': row['list_date'],
                'total_shares': row['total_shares'],
                'float_shares': row['float_shares'],
                'total_mv': row['total_mv'],
                'circ_mv': row['circ_mv'],
                'data_source': row['data_source'],
                'updated_at': row['updated_at']
            } for row in rows]
            
        except Exception as e:
            logger.error(f"获取所有股票信息失败: {e}")
            conn.close()
            return []
    
    def search_stock_by_name(self, name_keyword: str) -> List[Dict]:
        """
        根据名称关键字搜索股票
        
        Args:
            name_keyword: 名称关键字
            
        Returns:
            匹配的股票列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f'''
                SELECT code, name, industry, list_date, total_shares, float_shares,
                       total_mv, circ_mv, data_source, updated_at
                FROM {self.STOCK_INFO_TABLE}
                WHERE name LIKE ?
                ORDER BY code
            ''', (f'%{name_keyword}%',))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{
                'code': row['code'],
                'name': row['name'],
                'industry': row['industry'],
                'list_date': row['list_date'],
                'total_shares': row['total_shares'],
                'float_shares': row['float_shares'],
                'total_mv': row['total_mv'],
                'circ_mv': row['circ_mv'],
                'data_source': row['data_source'],
                'updated_at': row['updated_at']
            } for row in rows]
            
        except Exception as e:
            logger.error(f"搜索股票失败 {name_keyword}: {e}")
            conn.close()
            return []
    
    def get_stock_info_stats(self) -> Dict:
        """
        获取股票信息统计
        
        Returns:
            统计信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {
            'total_count': 0,
            'with_name': 0,
            'with_industry': 0,
            'latest_update': None
        }
        
        try:
            # 总数
            cursor.execute(f'SELECT COUNT(*) FROM {self.STOCK_INFO_TABLE}')
            stats['total_count'] = cursor.fetchone()[0]
            
            # 有名称的数量
            cursor.execute(f"SELECT COUNT(*) FROM {self.STOCK_INFO_TABLE} WHERE name IS NOT NULL AND name != ''")
            stats['with_name'] = cursor.fetchone()[0]
            
            # 有行业的数量
            cursor.execute(f"SELECT COUNT(*) FROM {self.STOCK_INFO_TABLE} WHERE industry IS NOT NULL AND industry != ''")
            stats['with_industry'] = cursor.fetchone()[0]
            
            # 最后更新时间
            cursor.execute(f'SELECT MAX(updated_at) FROM {self.STOCK_INFO_TABLE}')
            result = cursor.fetchone()
            stats['latest_update'] = result[0] if result else None
            
            conn.close()
            
        except Exception as e:
            logger.error(f"获取股票信息统计失败: {e}")
            conn.close()
        
        return stats
