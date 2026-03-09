#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化测试 - 直接使用 akshare
"""
import sys
import os

# 清除代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

print("=" * 60)
print("测试 1: 直接使用 akshare")
print("=" * 60)
try:
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol="600519", period="daily", 
                            start_date="20240301", end_date="20240308", adjust="qfq")
    print(f"[OK] 直接调用成功，{len(df)} 行")
    print(df[['日期', '收盘', '涨跌幅']].head())
except Exception as e:
    print(f"[FAIL] {e}")

print("\n" + "=" * 60)
print("测试 2: 通过 AkshareFetcher")
print("=" * 60)
try:
    from data_provider.akshare_fetcher import AkshareFetcher
    fetcher = AkshareFetcher()
    df = fetcher.get_daily_data('600519', days=10)
    print(f"[OK] AkshareFetcher 成功，{len(df)} 行")
    print(df[['date', 'close', 'pct_chg']].head())
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试 3: 通过 DataFetcherManager")
print("=" * 60)
try:
    from data_provider import DataFetcherManager
    manager = DataFetcherManager()
    df, source = manager.get_daily_data('600519', days=10)
    print(f"[OK] DataFetcherManager 成功，来源: {source}，{len(df)} 行")
    print(df[['date', 'close', 'pct_chg']].head())
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试 4: 通过 data_fetcher.get_stock_data")
print("=" * 60)
try:
    from data_fetcher import get_stock_data
    result = get_stock_data('600519', days=10)
    print(f"[OK] get_stock_data 成功: {result['success']}")
    print(f"数据来源: {result['data_source']}")
    print(f"数据条数: {len(result['daily_data'])}")
    if result['daily_data']:
        for d in result['daily_data'][-3:]:
            print(f"  {d['date']}: {d['close']} ({d['pct_chg']}%)")
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
