# -*- coding: utf-8 -*-
"""
测试股票数据API可用性
对比 akshare 和 efinance
"""
import os
import sys

# 清除代理
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

print("=" * 70)
print("股票数据API可用性测试")
print("=" * 70)

# 测试1: akshare stock_zh_a_hist
print("\n[1] Testing akshare.stock_zh_a_hist...")
try:
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol='000001', period='daily', 
                            start_date='20230301', end_date='20230310', 
                            adjust='qfq')
    print(f"  ✓ OK: Got {len(df)} rows")
    print(f"  Columns: {list(df.columns)}")
except Exception as e:
    print(f"  ✗ Failed: {type(e).__name__}")

# 测试2: akshare 备用接口 - stock_zh_a_spot_em
print("\n[2] Testing akshare.stock_zh_a_spot_em (实时行情)...")
try:
    import akshare as ak
    df = ak.stock_zh_a_spot_em()
    print(f"  ✓ OK: Got {len(df)} rows")
    print(f"  Columns: {list(df.columns)[:5]}...")
except Exception as e:
    print(f"  ✗ Failed: {type(e).__name__}")

# 测试3: akshare 备用接口 - stock_zh_a_daily
print("\n[3] Testing akshare.stock_zh_a_daily...")
try:
    import akshare as ak
    df = ak.stock_zh_a_daily(symbol='000001', start_date='20230301', 
                             end_date='20230310', adjust='qfq')
    print(f"  ✓ OK: Got {len(df)} rows")
except Exception as e:
    print(f"  ✗ Failed: {type(e).__name__}")

# 测试4: efinance
print("\n[4] Testing efinance...")
try:
    import efinance as ef
    df = ef.stock.get_daily_bars('000001')
    print(f"  ✓ OK: Got {len(df)} rows")
    print(f"  Columns: {list(df.columns)}")
except Exception as e:
    print(f"  ✗ Failed: {type(e).__name__}: {str(e)[:100]}")

# 测试5: yfinance
print("\n[5] Testing yfinance (000001.SZ)...")
try:
    import yfinance as yf
    ticker = yf.Ticker("000001.SZ")
    df = ticker.history(start='2023-03-01', end='2023-03-10')
    print(f"  ✓ OK: Got {len(df)} rows")
except Exception as e:
    print(f"  ✗ Failed: {type(e).__name__}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
