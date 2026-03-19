# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from local_db import LocalDatabase

db = LocalDatabase('./data/stock_data.db')

# 测试 get_latest_date
print('测试 get_latest_date:')
for code in ['000001', '600519', '300750', '601318']:
    result = db.get_latest_date('data_if300', code)
    print('  {}: {}'.format(code, result))

# 直接查询
import sqlite3
conn = sqlite3.connect('./data/stock_data.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print('\n直接SQL查询:')
for code in ['000001', '600519', '300750', '601318']:
    cursor.execute("SELECT MAX(date) as latest_date FROM data_if300 WHERE code=?", (code,))
    row = cursor.fetchone()
    print('  {}: {}'.format(code, row['latest_date']))

# 检查表的所有内容
cursor.execute("SELECT code, date FROM data_if300 ORDER BY date DESC LIMIT 20")
print('\n表 data_if300 最新20条:')
for row in cursor.fetchall():
    print('  {} {}'.format(row['code'], row['date']))

conn.close()
