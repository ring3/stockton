# -*- coding: utf-8 -*-
"""
测试优化后的行业板块接口
"""
import os
import sys
import time

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

sys.path.insert(0, 'skills/stockton/scripts')

from data_provider import AkshareFetcher

print('=' * 70)
print('测试优化后的行业板块接口')
print('=' * 70)

fetcher = AkshareFetcher()

# 1. 测试 _get_sector_rankings
print('\n[1] _get_sector_rankings (行业涨跌幅排行)')
print('   优化: 使用 stock_board_industry_summary_ths + 缓存')

print('   首次请求:')
start = time.time()
df = fetcher._get_sector_rankings()
elapsed = time.time() - start
if not df.empty:
    print(f'   [OK] 耗时 {elapsed:.3f}s, {len(df)} 个板块')
    if 'change_pct' in df.columns:
        top3 = df.nlargest(3, 'change_pct')
        print('   涨幅前3:')
        for _, row in top3.iterrows():
            print(f'     {row["name"]}: {row["change_pct"]}%')
else:
    print(f'   [FAIL] 耗时 {elapsed:.3f}s')

print('   缓存命中:')
start = time.time()
df = fetcher._get_sector_rankings()
elapsed = time.time() - start
print(f'   耗时 {elapsed:.3f}s')

# 2. 测试 _get_industry_list
print('\n[2] _get_industry_list (行业列表)')
print('   优化: THS源优先 + 1小时缓存')

print('   首次请求:')
start = time.time()
df = fetcher._get_industry_list()
elapsed = time.time() - start
if not df.empty:
    print(f'   [OK] 耗时 {elapsed:.3f}s, {len(df)} 个行业')
else:
    print(f'   [FAIL] 耗时 {elapsed:.3f}s')

print('   缓存命中:')
start = time.time()
df = fetcher._get_industry_list()
elapsed = time.time() - start
print(f'   耗时 {elapsed:.3f}s')

print('\n' + '=' * 70)
