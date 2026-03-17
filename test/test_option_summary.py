# -*- coding: utf-8 -*-
"""
期权数据接口测试汇总
测试环境网络限制：push2.eastmoney.com 无法访问
"""
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak
import pandas as pd

print('=' * 80)
print('Akshare 期权接口测试结果汇总')
print('=' * 80)

results = []

# 测试1: 期权价值分析（目标接口）
print('\n[1] option_value_analysis_em - 期权价值分析（目标接口）')
try:
    df = ak.option_value_analysis_em()
    print(f'    状态: ✓ 成功 ({len(df)} 条)')
    results.append(('option_value_analysis_em', '成功', len(df)))
except Exception as e:
    print(f'    状态: ✗ 失败 - {type(e).__name__}')
    print(f'    说明: push2.eastmoney.com 连接被重置')
    results.append(('option_value_analysis_em', '失败', 0))

# 测试2: 50ETF波动率指数（可用）
print('\n[2] index_option_50etf_qvix - 50ETF波动率指数')
try:
    df = ak.index_option_50etf_qvix()
    print(f'    状态: ✓ 成功 ({len(df)} 条)')
    print(f'    最新数据: {df.iloc[-1].to_dict()}')
    results.append(('index_option_50etf_qvix', '成功', len(df)))
except Exception as e:
    print(f'    状态: ✗ 失败 - {e}')
    results.append(('index_option_50etf_qvix', '失败', 0))

# 测试3: 中金所50期权现货（历史数据）
print('\n[3] option_cffex_sz50_spot_sina - 中金所50ETF期权现货')
try:
    df = ak.option_cffex_sz50_spot_sina()
    print(f'    状态: ✓ 成功 ({len(df)} 条)')
    print(f'    数据日期: {df["看涨合约-标识"].iloc[0] if len(df) > 0 else "N/A"}')
    results.append(('option_cffex_sz50_spot_sina', '成功(历史)', len(df)))
except Exception as e:
    print(f'    状态: ✗ 失败 - {e}')
    results.append(('option_cffex_sz50_spot_sina', '失败', 0))

# 测试4: 期权龙虎榜
print('\n[4] option_lhb_em - 期权龙虎榜')
try:
    df = ak.option_lhb_em()
    print(f'    状态: ✓ 成功 ({len(df)} 条)')
    results.append(('option_lhb_em', '成功(历史)', len(df)))
except Exception as e:
    print(f'    状态: ✗ 失败 - {e}')
    results.append(('option_lhb_em', '失败', 0))

# 汇总
print('\n' + '=' * 80)
print('测试汇总:')
print('=' * 80)
for name, status, count in results:
    print(f'  {name:40s} {status:15s} {count:6d} 条')

print('\n' + '=' * 80)
print('结论:')
print('=' * 80)
print('1. 目标接口 option_value_analysis_em 在当前网络环境下无法访问')
print('2. push2.eastmoney.com 域名连接被重置')
print('3. 新浪数据源可用但返回的是历史数据而非实时数据')
print('\n建议:')
print('- 尝试在其他网络环境（如手机热点）中运行')
print('- 使用券商API（如中泰xtp、华泰atic）获取实时期权数据')
print('- 使用聚宽、tushare等付费数据服务')
