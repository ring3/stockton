# -*- coding: utf-8 -*-
"""
使用 akshare 的 option_value_analysis_em 接口测试
通过monkey patch修改akshare的请求行为
"""
import os
import sys
import random
import time

# 必须在导入任何其他库之前清除代理
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 禁用urllib3警告
import urllib3
urllib3.disable_warnings()

import requests
from requests.adapters import HTTPAdapter

# 保存原始函数
_original_request_with_retry = None

def patched_request_with_retry(url, params=None, timeout=15, max_retries=3, 
                               base_delay=1.0, random_delay_range=(0.5, 1.5)):
    """修改版的request_with_retry，禁用代理并添加headers"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            with requests.Session() as session:
                # 禁用环境变量代理
                session.trust_env = False
                
                # 添加必要的headers
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Referer': 'https://data.eastmoney.com/other/valueAnal.html',
                })
                
                # 配置adapter
                adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1)
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                
                response = session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                return response
                
        except (requests.RequestException, ValueError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt) + random.uniform(*random_delay_range[0], *random_delay_range[1])
                time.sleep(delay)
    
    raise last_exception

# 导入akshare并替换函数
import akshare.utils.request as ak_request
_original_request_with_retry = ak_request.request_with_retry
ak_request.request_with_retry = patched_request_with_retry

# 同时替换func模块中的函数（因为option_value_analysis_em从那里导入）
import akshare.utils.func as ak_func
ak_func.request_with_retry = patched_request_with_retry

import akshare as ak
import pandas as pd
from datetime import datetime

print('=' * 80)
print('Akshare 期权价值分析接口测试')
print('=' * 80)

try:
    print('\n正在调用 ak.option_value_analysis_em()...')
    print('（首次调用可能需要一些时间）\n')
    
    # 调用akshare接口
    df = ak.option_value_analysis_em()
    
    print(f'[OK] 成功获取数据！共 {len(df)} 条记录\n')
    
    # 显示数据基本信息
    print('数据列名:')
    print(df.columns.tolist())
    print()
    
    # 数据预览
    print('数据预览（前5行）:')
    print(df.head())
    print()
    
    # 分析到期日
    print('到期日分布:')
    expiry_counts = df['到期日'].value_counts().sort_index()
    print(expiry_counts)
    print()
    
    # 获取当月和次月
    unique_dates = sorted(df['到期日'].unique())
    if len(unique_dates) >= 2:
        current_month = unique_dates[0]
        next_month = unique_dates[1]
        
        print('=' * 80)
        print(f'当月到期日: {current_month}')
        print(f'次月到期日: {next_month}')
        print('=' * 80)
        print()
        
        # 筛选50ETF期权进行分析
        etf50_options = df[df['期权名称'].str.contains('50ETF', na=False)]
        
        print(f'50ETF 期权总数: {len(etf50_options)}')
        print()
        
        for label, expiry_date in [('当月', current_month), ('次月', next_month)]:
            options = etf50_options[etf50_options['到期日'] == expiry_date].copy()
            
            print(f'\n【{label}50ETF期权】到期日: {expiry_date}, 数量: {len(options)}')
            print('-' * 80)
            
            if len(options) > 0:
                # 计算与标的现价的接近程度（找平值期权）
                options['内在价值绝对值'] = options['内在价值'].abs()
                
                # 按内在价值排序，取最接近平值的5个
                atm_options = options.sort_values('内在价值绝对值').head(5)
                
                display_cols = ['期权代码', '期权名称', '最新价', '标的最新价', 
                               '时间价值', '内在价值', '隐含波动率']
                print(atm_options[display_cols].to_string(index=False))
            else:
                print('  无数据')
    
    # 保存完整数据
    output_file = 'data/option_value_analysis_akshare.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'\n\n[OK] 完整数据已保存到: {output_file}')
    
except Exception as e:
    print(f'\n[FAIL] 获取数据失败: {e}')
    import traceback
    traceback.print_exc()
finally:
    # 恢复原始函数
    if _original_request_with_retry:
        ak_request.request_with_retry = _original_request_with_retry
        ak_func.request_with_retry = _original_request_with_retry
