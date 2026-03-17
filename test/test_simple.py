# -*- coding: utf-8 -*-
"""
简单测试 - 只测试期货贴水
"""
import os
import sys
import time
import logging

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

skill_scripts_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'stockton', 'scripts')
sys.path.insert(0, skill_scripts_path)

from data_provider import AkshareFetcher

print('=' * 70)
print('测试期货贴水数据')
print('=' * 70)

fetcher = AkshareFetcher()

# 只测试期货贴水
print('\n[_get_futures_basis] 获取股指期货贴水...')
print('  优化点: 指数数据只获取一次，带10秒超时和fallback')
start = time.time()
df = fetcher._get_futures_basis()
elapsed = time.time() - start

if not df.empty:
    print(f'  [OK] 成功获取 {len(df)} 个期货数据，耗时 {elapsed:.2f}s')
    for i, row in df.iterrows():
        print(f'    {row["futures_code"]}: 年化{row["annualized_rate"]:+.2f}%')
else:
    print(f'  [WARN] 获取失败或为空，耗时 {elapsed:.2f}s')

print('\n' + '=' * 70)
