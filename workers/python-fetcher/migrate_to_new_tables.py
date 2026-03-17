# -*- coding: utf-8 -*-
"""
迁移脚本：将 data_if300 和 data_ic500 数据合并到 stock_a_data 表
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_data(db_path='./data/stock_data.db'):
    """
    迁移数据：
    1. 创建新表（如果不存在）
    2. 将 data_if300 数据导入 stock_a_data，标记 source_index='IF300'
    3. 将 data_ic500 数据导入 stock_a_data，标记 source_index='IC500'
    
    注意：从项目根目录运行，db_path 是相对根目录的路径
    """
    """
    迁移数据：
    1. 创建新表（如果不存在）
    2. 将 data_if300 数据导入 stock_a_data，标记 source_index='IF300'
    3. 将 data_ic500 数据导入 stock_a_data，标记 source_index='IC500'
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查源表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('data_if300', 'data_ic500')")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"发现源表: {existing_tables}")
        
        if not existing_tables:
            logger.warning("没有找到 data_if300 或 data_ic500 表")
            return
        
        # 检查并创建目标表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_a_data'")
        if not cursor.fetchone():
            logger.info("stock_a_data 表不存在，创建新表...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_a_data (
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
                    source_index TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(code, date)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_a_code_date ON stock_a_data(code, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_a_date ON stock_a_data(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_a_code ON stock_a_data(code)')
            conn.commit()
            logger.info("stock_a_data 表创建完成")
        
        # 检查并创建 stock_h_data 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_h_data'")
        if not cursor.fetchone():
            logger.info("stock_h_data 表不存在，创建新表...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_h_data (
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_h_code_date ON stock_h_data(code, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_h_date ON stock_h_data(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_stock_h_code ON stock_h_data(code)')
            conn.commit()
            logger.info("stock_h_data 表创建完成")
        
        # 统计迁移前数据量
        cursor.execute("SELECT COUNT(*) FROM stock_a_data")
        before_count = cursor.fetchone()[0]
        logger.info(f"迁移前 stock_a_data 表记录数: {before_count}")
        
        # 迁移 data_if300 数据
        if 'data_if300' in existing_tables:
            logger.info("开始迁移 data_if300 数据...")
            cursor.execute('''
                INSERT OR REPLACE INTO stock_a_data 
                (code, date, open, high, low, close, volume, amount, 
                 ma5, ma10, ma20, ma60, change_pct, turnover_rate, source_index)
                SELECT 
                    code, date, open, high, low, close, volume, amount,
                    ma5, ma10, ma20, ma60, change_pct, turnover_rate,
                    'IF300' as source_index
                FROM data_if300
            ''')
            if300_count = cursor.rowcount
            logger.info(f"已迁移 data_if300: {if300_count} 条记录")
        
        # 迁移 data_ic500 数据
        if 'data_ic500' in existing_tables:
            logger.info("开始迁移 data_ic500 数据...")
            cursor.execute('''
                INSERT OR REPLACE INTO stock_a_data 
                (code, date, open, high, low, close, volume, amount, 
                 ma5, ma10, ma20, ma60, change_pct, turnover_rate, source_index)
                SELECT 
                    code, date, open, high, low, close, volume, amount,
                    ma5, ma10, ma20, ma60, change_pct, turnover_rate,
                    'IC500' as source_index
                FROM data_ic500
            ''')
            ic500_count = cursor.rowcount
            logger.info(f"已迁移 data_ic500: {ic500_count} 条记录")
        
        conn.commit()
        
        # 统计迁移后数据量
        cursor.execute("SELECT COUNT(*) FROM stock_a_data")
        after_count = cursor.fetchone()[0]
        logger.info(f"迁移后 stock_a_data 表记录数: {after_count}")
        
        # 统计各来源的数据量
        cursor.execute('''
            SELECT source_index, COUNT(*) as cnt 
            FROM stock_a_data 
            WHERE source_index IS NOT NULL
            GROUP BY source_index
        ''')
        logger.info("各来源数据统计:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]} 条")
        
        # 统计股票数量
        cursor.execute("SELECT COUNT(DISTINCT code) FROM stock_a_data")
        stock_count = cursor.fetchone()[0]
        logger.info(f"股票总数: {stock_count} 只")
        
        logger.info("数据迁移完成！")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_migration(db_path='./data/stock_data.db'):
    """验证迁移结果"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    logger.info("\n" + "="*60)
    logger.info("验证迁移结果")
    logger.info("="*60)
    
    # 检查各表记录数
    tables = ['data_if300', 'data_ic500', 'stock_a_data', 'stock_h_data']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        logger.info(f"{table}: {count} 条记录")
    
    # 检查 stock_a_data 中的股票
    cursor.execute('''
        SELECT code, COUNT(*) as cnt, MIN(date), MAX(date)
        FROM stock_a_data
        GROUP BY code
        ORDER BY cnt DESC
        LIMIT 10
    ''')
    logger.info("\nstock_a_data 前10只股票:")
    for row in cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]}条, {row[2]} ~ {row[3]}")
    
    conn.close()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_migration()
    else:
        migrate_data()
        verify_migration()
