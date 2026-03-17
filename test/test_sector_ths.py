# -*- coding: utf-8 -*-
"""
测试 THS 行业板块 API
"""
import os
import time
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak

print('=== 测试 THS 行业板块 API ===\n')

# 1. stock_board_industry_name_ths
print('1. stock_board_industry_name_ths')
start = time.time()
try:
    df = ak.stock_board_industry_name_ths()
    elapsed = time.time() - start
    print(f'   [OK] 耗时 {elapsed:.3f}s, {len(df)} 条数据')
    print(f'   列名: {df.columns.tolist()}')
    print(f'   前3行:')
    print(df.head(3).to_string())
except Exception as e:
    print(f'   [FAIL] {e}')

print()

# 2. stock_board_industry_summary_ths
print('2. stock_board_industry_summary_ths')
start = time.time()
try:
    df = ak.stock_board_industry_summary_ths()
    elapsed = time.time() - start
    print(f'   [OK] 耗时 {elapsed:.3f}s, {len(df)} 条数据')
    print(f'   列名: {df.columns.tolist()}')
    print(f'   前3行:')
    print(df.head(3).to_string())
except Exception as e:
    print(f'   [FAIL] {e}')
