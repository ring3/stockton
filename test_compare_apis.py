# -*- coding: utf-8 -*-
"""
对比 stock_zh_a_hist 和 stock_zh_a_spot
"""
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak

print('=== 对比测试：stock_zh_a_hist vs stock_zh_a_spot ===\n')

# 1. stock_zh_a_hist (单股K线)
print('1. stock_zh_a_hist (单股历史K线)')
print('   参数: symbol=000001, period=daily')
df_hist = ak.stock_zh_a_hist(symbol='000001', period='daily', start_date='20250310', end_date='20250313', adjust='')
print(f'   返回条数: {len(df_hist)}')
print(f'   数据列: {list(df_hist.columns)}')
latest = df_hist.iloc[-1]
print(f'   最新日期: {latest["日期"]}')
print(f'   最新收盘价(实时价): {latest["收盘"]}')
print(f'   涨跌幅: {latest["涨跌幅"]}%')
print(f'   换手率: {latest["换手率"]}%')
print()

# 2. stock_zh_a_spot (新浪全量实时)
print('2. stock_zh_a_spot (新浪全量实时) - 只取平安银行对比')
df_spot = ak.stock_zh_a_spot()
row = df_spot[df_spot['代码'] == '000001'].iloc[0]
print(f'   平安银行 ({row["代码"]})')
print(f'   最新价: {row["最新价"]}')
print(f'   涨跌幅: {row["涨跌幅"]}%')
print(f'   换手率: {row["换手率"]}%')
print()

print('=== 字段对比分析 ===')
print('stock_zh_a_hist 包含的字段:')
print('  - 日期、开盘、收盘、最高、最低')
print('  - 成交量、成交额')
print('  - 振幅、涨跌幅、涨跌额、换手率')
print()
print('stock_zh_a_spot 额外有的字段:')
print('  - 量比、市盈率、市净率')
print('  - 总市值、流通市值')
print('  - 今开、昨收')
print()

# 验证收盘价是否一致
print('=== 数据一致性验证 ===')
print(f'  stock_zh_a_hist 收盘价: {latest["收盘"]}')
print(f'  stock_zh_a_spot 最新价: {row["最新价"]}')
print(f'  是否一致: {abs(float(latest["收盘"]) - float(row["最新价"])) < 0.01}')
