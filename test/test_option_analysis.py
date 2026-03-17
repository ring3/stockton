# -*- coding: utf-8 -*-
"""
期权价值分析接口测试 - 获取当月和次月平值期权

注意：此脚本需要在无代理限制的网络环境中运行
"""
import os
import sys

# 尝试清除代理环境变量
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]
os.environ['NO_PROXY'] = '*'

import urllib3
urllib3.disable_warnings()

import requests
import pandas as pd
from datetime import datetime

print('=' * 80)
print('期权价值分析接口测试')
print('=' * 80)

# 请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://data.eastmoney.com/other/valueAnal.html',
}

# 接口参数
base_url = 'https://push2.eastmoney.com/api/qt/clist/get'
params = {
    'fid': 'f301',
    'po': '1',
    'pz': '100',
    'pn': '1',
    'np': '1',
    'fltt': '2',
    'invt': '2',
    'ut': 'b2884a393a59ad64002292a3e90d46a5',
    'fields': 'f1,f2,f3,f12,f13,f14,f152,f249,f298,f299,f300,f301,f330,f331,f332,f333,f334,f335,f336',
    'fs': 'm:10',  # 金融期权
}

try:
    print('正在获取数据...')
    session = requests.Session()
    session.trust_env = False
    
    all_data = []
    page = 1
    
    while True:
        params['pn'] = str(page)
        resp = session.get(base_url, params=params, headers=headers, timeout=30, proxies={})
        
        if resp.status_code != 200:
            print(f'[WARN] 请求失败，状态码: {resp.status_code}')
            break
        
        data = resp.json()
        
        if data.get('rc') != 0:
            print(f'[WARN] API返回错误: {data}')
            break
        
        total = data.get('data', {}).get('total', 0)
        diff = data.get('data', {}).get('diff', [])
        
        if not diff:
            break
        
        all_data.extend(diff)
        print(f'  第{page}页: 获取 {len(diff)} 条，累计 {len(all_data)}/{total}')
        
        if len(all_data) >= total:
            break
        
        page += 1
        if page > 10:
            break
    
    print(f'\n[OK] 共获取 {len(all_data)} 条记录')
    
    # 转换为DataFrame
    df = pd.DataFrame(all_data)
    
    # 列名映射
    column_map = {
        'f12': '期权代码',
        'f14': '期权名称', 
        'f2': '最新价',
        'f3': '涨跌幅',
        'f298': '时间价值',
        'f299': '内在价值',
        'f249': '隐含波动率',
        'f300': '理论价格',
        'f334': '标的名称',
        'f335': '标的最新价',
        'f336': '标的近一年波动率',
        'f301': '到期日',
    }
    df = df.rename(columns=column_map)
    df['到期日'] = pd.to_datetime(df['到期日'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
    
    # 分析到期日
    unique_dates = sorted(df['到期日'].unique())
    print(f'\n到期日分布: {unique_dates}')
    
    if len(unique_dates) >= 2:
        current_month = unique_dates[0]
        next_month = unique_dates[1]
        
        print(f'\n{"="*80}')
        print(f'当月到期日: {current_month}')
        print(f'次月到期日: {next_month}')
        print(f'{"="*80}')
        
        # 分析50ETF期权
        etf_options = df[df['期权名称'].str.contains('50ETF', na=False)]
        
        for label, expiry in [('当月', current_month), ('次月', next_month)]:
            options = etf_options[etf_options['到期日'] == expiry].copy()
            print(f'\n【{label}50ETF期权】数量: {len(options)}')
            
            if len(options) > 0:
                # 找出接近平值的期权（内在价值最小）
                options['内在价值绝对'] = options['内在价值'].abs()
                atm_options = options.sort_values('内在价值绝对').head(5)
                
                print(atm_options[['期权代码', '期权名称', '最新价', '时间价值', '内在价值', '隐含波动率']].to_string())
    
    # 保存数据
    df.to_csv('data/option_value_analysis.csv', index=False, encoding='utf-8-sig')
    print(f'\n[OK] 数据已保存到 data/option_value_analysis.csv')
    
except Exception as e:
    print(f'[FAIL] 获取数据失败: {e}')
    print('\n提示: 此接口可能在当前网络环境下无法访问，建议:')
    print('1. 检查是否有代理或防火墙限制')
    print('2. 尝试在其他网络环境中运行')
    print('3. 使用浏览器访问 https://data.eastmoney.com/other/valueAnal.html 查看是否正常')
