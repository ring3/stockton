# -*- coding: utf-8 -*-
"""
测试所有优化后的方法
"""
import os
import sys
import time

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

sys.path.insert(0, 'skills/stockton/scripts')

from data_provider import AkshareFetcher

print('=' * 70)
print('测试所有优化后的方法')
print('=' * 70)

fetcher = AkshareFetcher()

# 1. 测试 _get_realtime_quote (已优化)
print('\n[1] _get_realtime_quote (个股实时行情)')
print('   优化: 使用 stock_zh_a_hist + stock_individual_info_em')
start = time.time()
quote = fetcher._get_realtime_quote('000001')
elapsed = time.time() - start
if quote:
    print(f'   [OK] {elapsed:.2f}s - {quote["name"]}: {quote["price"]}元')
else:
    print(f'   [FAIL] {elapsed:.2f}s')

# 2. 测试 _get_stock_pool (已优化)
print('\n[2] _get_stock_pool (股票池) - 首次请求')
print('   优化: 使用指数成分股 + 缓存')
start = time.time()
df = fetcher._get_stock_pool("A股")
elapsed = time.time() - start
if not df.empty:
    print(f'   [OK] {elapsed:.2f}s - 获取 {len(df)} 只股票')
else:
    print(f'   [FAIL] {elapsed:.2f}s')

print('\n[2b] _get_stock_pool (股票池) - 缓存命中')
start = time.time()
df = fetcher._get_stock_pool("A股")
elapsed = time.time() - start
if not df.empty:
    print(f'   [OK] {elapsed:.3f}s - 缓存命中，{len(df)} 只股票')

# 3. 测试 _get_industry_stocks (已优化)
print('\n[3] _get_industry_stocks (行业成分股)')
print('   优化: 使用专门接口 + 缓存')
start = time.time()
df = fetcher._get_industry_stocks("半导体")
elapsed = time.time() - start
if not df.empty:
    print(f'   [OK] {elapsed:.2f}s - 获取 {len(df)} 只股票')
else:
    print(f'   [WARN] {elapsed:.2f}s - 可能该行业暂无数据')

# 4. 测试 _get_market_overview (已优化)
print('\n[4] _get_market_overview (市场概览) - 首次请求')
print('   优化: 添加缓存')
start = time.time()
df = fetcher._get_market_overview()
elapsed = time.time() - start
if not df.empty:
    print(f'   [OK] {elapsed:.2f}s - 获取 {len(df)} 只股票')
else:
    print(f'   [FAIL] {elapsed:.2f}s')

print('\n[4b] _get_market_overview (市场概览) - 缓存命中')
start = time.time()
df = fetcher._get_market_overview()
elapsed = time.time() - start
if not df.empty:
    print(f'   [OK] {elapsed:.3f}s - 缓存命中')

print('\n' + '=' * 70)
print('所有测试完成')
print('=' * 70)
