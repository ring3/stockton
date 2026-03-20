# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

# 检查两个数据库文件
db_paths = [
    Path("data/stock_data.db"),
    Path("workers/python-fetcher/data/stock_data.db"),
]

for db_path in db_paths:
    print(f"\n{'='*60}")
    print(f"Database: {db_path}")
    print(f"Exists: {db_path.exists()}")
    
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables ({len(tables)}):")
        for t in tables:
            print(f"  - {t[0]}")
        
        # 检查 stock_a_data 数据量
        if any(t[0] == 'stock_a_data' for t in tables):
            cursor.execute("SELECT COUNT(*) FROM stock_a_data")
            count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT code) FROM stock_a_data")
            stocks = cursor.fetchone()[0]
            print(f"  stock_a_data: {count} rows, {stocks} stocks")
        
        conn.close()
