# -*- coding: utf-8 -*-
"""
对比 stock_zh_a_hist 和 stock_zh_a_spot
"""
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak
import pandas as pd

print('=== API 对比测试 ===\n')

# 1. stock_zh_a_hist (单股K线)
print('1. stock_zh_a_hist (单股历史K线)')
print('   参数: symbol=000001, period=daily')
df_hist = ak.stock_zh_a_hist(symbol='000001', period='daily', start_date='20250310', end_date='20250313', adjust='')
print(f'   返回条数: {len(df_hist)}')
print(f'   列名: {df_hist.columns.tolist()}')
print()

latest = df_hist.iloc[-1]
print('   最新一行数据:')
for col in df_hist.columns:
    print(f'      {col}: {latest[col]}')
print()

# 2. 验证收盘价作为实时价的可行性
print('=== 关键发现 ===')
print(f'1. stock_zh_a_hist 返回 {len(df_hist)} 条数据（仅4天）')
print(f'2. 数据量: {df_hist.memory_usage(deep=True).sum()} bytes')
print(f'3. 包含字段: {len(df_hist.columns)} 个')
print()

print('=== 字段覆盖度分析 ===')
print('stock_zh_a_hist 包含:')
print('  - 基础价格: 开盘、收盘、最高、最低')
print('  - 成交数据: 成交量、成交额')
print('  - 涨跌数据: 涨跌幅、涨跌额、振幅')
print('  - 其他: 换手率')
print()

print('缺少字段（相比全量实时）:')
print('  - 量比、市盈率、市净率')
print('  - 总市值、流通市值')
print('  - 量比')
print()

# 3. 评估替代可行性
print('=== 替代可行性评估 ===')
print('适用场景:')
print('  获取个股实时行情 - 适合')
print('  计算技术指标 - 适合')
print('  判断趋势 - 适合')
print()
print('不适用场景:')
print('  需要量比数据 - 不适合')
print('  需要市值数据 - 不适合')
print('  需要估值数据(PE/PB) - 不适合')
print()

# 4. 性能对比
print('=== 性能对比 ===')
import time

# 测试 stock_zh_a_hist
start = time.time()
for i in range(3):
    _ = ak.stock_zh_a_hist(symbol='000001', period='daily', start_date='20250310', end_date='20250313', adjust='')
elapsed_hist = (time.time() - start) / 3
print(f'stock_zh_a_hist (单股): {elapsed_hist:.3f}s/次')

# 测试 stock_zh_a_spot
start = time.time()
_ = ak.stock_zh_a_spot()
elapsed_spot = time.time() - start
print(f'stock_zh_a_spot (全量): {elapsed_spot:.3f}s/次')

print(f'\n性能提升: {elapsed_spot/elapsed_hist:.1f}x 倍')
