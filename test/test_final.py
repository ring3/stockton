# -*- coding: utf-8 -*-
"""
测试最终优化效果
"""
import os
import sys
import time

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

skill_scripts_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'stockton', 'scripts')
sys.path.insert(0, skill_scripts_path)

from data_provider import AkshareFetcher

print('=' * 70)
print('测试优化后的 _get_market_overview')
print('=' * 70)

fetcher = AkshareFetcher()

print('\n[测试1] _get_market_overview (使用 stock_market_activity_legu)')
print('   预期: 0.5s 左右')
start = time.time()
df = fetcher._get_market_overview()
elapsed = time.time() - start

if not df.empty:
    print(f'   [OK] 耗时 {elapsed:.3f}s')
    print(f'   数据:')
    if '上涨家数' in df.columns:
        # 新格式
        row = df.iloc[0]
        print(f'     上涨: {int(row["上涨家数"])}')
        print(f'     下跌: {int(row["下跌家数"])}')
        print(f'     涨停: {int(row["涨停家数"])}')
        print(f'     跌停: {int(row["跌停家数"])}')
    else:
        # 旧格式
        print(f'     数据条数: {len(df)}')
else:
    print(f'   [FAIL] 耗时 {elapsed:.3f}s')

print('\n[测试2] 缓存命中')
start = time.time()
df = fetcher._get_market_overview()
elapsed = time.time() - start
print(f'   耗时: {elapsed:.3f}s (应为 0.000s)')

print('\n' + '=' * 70)
