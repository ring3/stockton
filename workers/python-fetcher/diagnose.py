# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from local_db import LocalDatabase

db = LocalDatabase('./data/stock_data.db')

# 测试 get_latest_date 函数
print('测试 get_latest_date 函数:')
print('  000001: {}'.format(db.get_latest_date('data_if300', '000001')))
print('  600519: {}'.format(db.get_latest_date('data_if300', '600519')))
print('  300750: {}'.format(db.get_latest_date('data_if300', '300750')))

# 直接查询数据库
import sqlite3
conn = sqlite3.connect('./data/stock_data.db')
cursor = conn.cursor()

print('\n直接查询数据库:')
for code in ['000001', '600519', '300750']:
    cursor.execute("SELECT MAX(date) FROM data_if300 WHERE code=?", (code,))
    result = cursor.fetchone()
    print('  {}: {}'.format(code, result[0]))

# 检查所有股票
cursor.execute('SELECT code, COUNT(*), MAX(date) FROM data_if300 GROUP BY code')
print('\n表 data_if300 所有股票:')
for row in cursor.fetchall():
    print('  {}: {} 条, 最新: {}'.format(row[0], row[1], row[2]))

conn.close()
