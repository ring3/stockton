# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('./data/stock_data.db')
cursor = conn.cursor()

print("所有表:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for row in cursor.fetchall():
    print(f"  {row[0]}")

print("\nstock_a_data 表结构:")
cursor.execute('PRAGMA table_info(stock_a_data)')
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print("\nstock_h_data 表结构:")
cursor.execute('PRAGMA table_info(stock_h_data)')
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

print("\n数据来源分布:")
cursor.execute('''
    SELECT source_index, COUNT(*), COUNT(DISTINCT code) 
    FROM stock_a_data 
    GROUP BY source_index
''')
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}条记录, {row[2]}只股票")

conn.close()
