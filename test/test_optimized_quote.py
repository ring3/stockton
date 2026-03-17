# -*- coding: utf-8 -*-
"""
测试优化后的 _get_realtime_quote
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
print('测试优化后的 _get_realtime_quote')
print('=' * 70)

fetcher = AkshareFetcher()

# 测试多只股票
test_codes = ['000001', '600519', '300750']

for code in test_codes:
    print(f'\n测试股票: {code}')
    start = time.time()
    quote = fetcher._get_realtime_quote(code)
    elapsed = time.time() - start
    
    if quote:
        print(f'  [OK] 耗时 {elapsed:.3f}s')
        print(f'  名称: {quote["name"]}')
        print(f'  价格: {quote["price"]}')
        print(f'  涨跌幅: {quote["change_pct"]:.2f}%')
        print(f'  换手率: {quote["turnover_rate"]:.2f}%')
        print(f'  总市值: {quote["total_mv"]/1e8:.2f}亿')
        print(f'  量比: {quote["volume_ratio"]}')
    else:
        print(f'  [FAIL] 耗时 {elapsed:.3f}s')

print('\n' + '=' * 70)
print('测试完成')
print('=' * 70)
