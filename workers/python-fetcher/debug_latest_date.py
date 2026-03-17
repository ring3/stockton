# -*- coding: utf-8 -*-
"""
诊断 get_latest_date 问题
不删除数据库，直接测试函数返回值
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from local_db import LocalDatabase

# 1. 直接测试 LocalDatabase.get_latest_date
print("="*60)
print("测试 LocalDatabase.get_latest_date 函数")
print("="*60)

db = LocalDatabase('./data/stock_data.db')

test_codes = ['000001', '600519', '300750', '601318', '000333']
for code in test_codes:
    result = db.get_latest_date('data_if300', code)
    print(f"  {code}: {result}")

# 2. 直接执行 SQL 对比
print("\n" + "="*60)
print("直接执行 SQL 查询")
print("="*60)

conn = sqlite3.connect('./data/stock_data.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

for code in test_codes:
    cursor.execute(
        "SELECT MAX(date) as latest_date FROM data_if300 WHERE code=?", 
        (code,)
    )
    row = cursor.fetchone()
    print(f"  {code}: {row['latest_date']}")

# 3. 检查表中实际有哪些股票
print("\n" + "="*60)
print("data_if300 表中的股票统计")
print("="*60)

cursor.execute("""
    SELECT code, COUNT(*) as cnt, MAX(date) as max_date, MIN(date) as min_date
    FROM data_if300 
    GROUP BY code 
    ORDER BY code
""")

rows = cursor.fetchall()
print(f"总共有 {len(rows)} 只股票")
print("\n前10只:")
for row in rows[:10]:
    print(f"  {row['code']}: {row['cnt']}条, 最新:{row['max_date']}, 最早:{row['min_date']}")

# 4. 检查是否有异常：code 为 NULL 或空字符串
print("\n" + "="*60)
print("检查异常数据")
print("="*60)

cursor.execute("SELECT COUNT(*) FROM data_if300 WHERE code IS NULL OR code=''")
null_count = cursor.fetchone()[0]
print(f"  code 为 NULL 或空的记录数: {null_count}")

# 5. 如果 600519 返回了错误日期，检查实际数据
cursor.execute("SELECT COUNT(*) FROM data_if300 WHERE code='600519'")
count_600519 = cursor.fetchone()[0]
print(f"\n  600519 实际记录数: {count_600519}")

if count_600519 == 0:
    print("  ⚠️ 600519 无数据，但函数可能返回了错误值！")
    
    # 检查函数的 WHERE 条件是否生效
    cursor.execute("SELECT COUNT(DISTINCT code) FROM data_if300")
    distinct_codes = cursor.fetchone()[0]
    print(f"  表中不同股票数: {distinct_codes}")
    
    # 直接测试 MAX 函数
    cursor.execute("SELECT MAX(date) FROM data_if300")
    max_date_all = cursor.fetchone()[0]
    print(f"  整张表的最大日期: {max_date_all}")

conn.close()

print("\n" + "="*60)
print("诊断完成")
print("="*60)
