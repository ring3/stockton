# -*- coding: utf-8 -*-
"""
测试 Timeout 和 Fallback 机制
"""
import os
import sys
import time
import logging

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, 'skills/stockton/scripts')

from data_provider import AkshareFetcher

print('=' * 70)
print('测试 Timeout 和 Fallback 机制')
print('=' * 70)

fetcher = AkshareFetcher()

# 测试 1: _get_market_indices
print('\n[测试1] _get_market_indices (指数行情)')
print('  预期: 15秒超时，Sina失败则fallback到EM')
start = time.time()
df = fetcher._get_market_indices()
elapsed = time.time() - start

if not df.empty:
    print(f'  [OK] 成功获取 {len(df)} 个指数，耗时 {elapsed:.2f}s')
    print(f'  前3个指数:')
    for i, row in df.head(3).iterrows():
        print(f'    {row["code"]} {row["name"]}: {row["price"]}')
else:
    print(f'  [WARN] 获取失败或为空，耗时 {elapsed:.2f}s')

# 测试 2: _get_sector_rankings
print('\n[测试2] _get_sector_rankings (行业板块)')
print('  预期: EM失败则fallback到THS')
start = time.time()
df = fetcher._get_sector_rankings()
elapsed = time.time() - start

if not df.empty:
    print(f'  [OK] 成功获取 {len(df)} 个行业，耗时 {elapsed:.2f}s')
else:
    print(f'  [WARN] 获取失败或为空，耗时 {elapsed:.2f}s')

# 测试 3: _get_market_overview
print('\n[测试3] _get_market_overview (市场概览)')
print('  预期: EM失败则fallback到Sina')
start = time.time()
df = fetcher._get_market_overview()
elapsed = time.time() - start

if not df.empty:
    print(f'  [OK] 成功获取 {len(df)} 只股票，耗时 {elapsed:.2f}s')
else:
    print(f'  [WARN] 获取失败或为空，耗时 {elapsed:.2f}s')

# 测试 4: _get_futures_basis
print('\n[测试4] _get_futures_basis (期货贴水)')
print('  预期: 指数数据只获取一次，带10秒超时')
start = time.time()
df = fetcher._get_futures_basis()
elapsed = time.time() - start

if not df.empty:
    print(f'  [OK] 成功获取 {len(df)} 个期货数据，耗时 {elapsed:.2f}s')
    for i, row in df.iterrows():
        print(f'    {row["futures_code"]}: 现货{row["index_price"]} 期货{row["futures_price"]} 年化{row["annualized_rate"]:.2f}%')
else:
    print(f'  [WARN] 获取失败或为空，耗时 {elapsed:.2f}s')

print('\n' + '=' * 70)
print('测试完成')
print('=' * 70)
