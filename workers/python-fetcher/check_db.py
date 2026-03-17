# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('data/stock_data.db')
cursor = conn.cursor()

# 检查 data_if300 表中实际有哪些股票
cursor.execute('SELECT code, COUNT(*) as cnt FROM data_if300 GROUP BY code ORDER BY code')
rows = cursor.fetchall()
print('data_if300 表中的股票:')
for row in rows:
    print('  {}: {} 条记录'.format(row[0], row[1]))

# 检查 600519 是否存在
cursor.execute("SELECT MAX(date) FROM data_if300 WHERE code='600519'")
result = cursor.fetchone()
print('\n600519 的最新日期: {}'.format(result[0]))

# 检查 000001 是否存在  
cursor.execute("SELECT MAX(date) FROM data_if300 WHERE code='000001'")
result = cursor.fetchone()
print('000001 的最新日期: {}'.format(result[0]))

conn.close()
