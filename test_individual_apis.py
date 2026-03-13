# -*- coding: utf-8 -*-
"""
测试个股专用接口
"""
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak
import time

test_code = "000001"

print('=== 测试个股专用接口 ===\n')

# 1. stock_individual_spot_xq (雪球)
print('1. stock_individual_spot_xq (雪球)')
try:
    start = time.time()
    df = ak.stock_individual_spot_xq(symbol=test_code)
    elapsed = time.time() - start
    print(f'   [OK] 耗时 {elapsed:.3f}s, {len(df)} 条数据')
    print(f'   列名: {df.columns.tolist()}')
    if not df.empty:
        print(f'   示例数据: {dict(df.iloc[0])}')
except Exception as e:
    print(f'   [FAIL] {type(e).__name__}: {str(e)[:100]}')
print()

# 2. stock_individual_info_em (东方财富个股信息)
print('2. stock_individual_info_em (东方财富个股信息)')
try:
    start = time.time()
    df = ak.stock_individual_info_em(symbol=test_code)
    elapsed = time.time() - start
    print(f'   [OK] 耗时 {elapsed:.3f}s, {len(df)} 条数据')
    print(f'   列名: {df.columns.tolist()}')
    if not df.empty:
        print(f'   数据: {dict(df.iloc[0])}')
except Exception as e:
    print(f'   [FAIL] {type(e).__name__}: {str(e)[:100]}')
print()

# 3. stock_zh_a_hist (历史K线 - 我们的主要替代方案)
print('3. stock_zh_a_hist (历史K线)')
try:
    start = time.time()
    df = ak.stock_zh_a_hist(symbol=test_code, period='daily', 
                            start_date='20250310', end_date='20250313', adjust='')
    elapsed = time.time() - start
    print(f'   [OK] 耗时 {elapsed:.3f}s, {len(df)} 条数据')
    print(f'   列名: {df.columns.tolist()}')
    if not df.empty:
        latest = df.iloc[-1]
        print(f'   最新数据: 收盘={latest["收盘"]}, 涨跌幅={latest["涨跌幅"]}%')
except Exception as e:
    print(f'   [FAIL] {type(e).__name__}: {str(e)[:100]}')
print()

print('=== 结论 ===')
print('根据测试结果，选择合适的补充数据源')
