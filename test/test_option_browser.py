# -*- coding: utf-8 -*-
"""
直接请求期权价值分析数据 - 模拟浏览器行为
"""
import os
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import urllib3
urllib3.disable_warnings()

import requests
import pandas as pd
import json

# 先访问主页面获取 cookie
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
})

print('Step 1: 访问主页面...')
main_url = 'https://data.eastmoney.com/other/valueAnal.html'
try:
    r = session.get(main_url, timeout=10)
    print(f'  状态: {r.status_code}')
    print(f'  Cookies: {dict(session.cookies)}')
except Exception as e:
    print(f'  错误: {e}')

print('\nStep 2: 请求数据...')
data_url = 'https://push2.eastmoney.com/api/qt/clist/get'
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
    'fs': 'm:10',
}

try:
    r = session.get(data_url, params=params, timeout=30)
    print(f'  状态: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        total = data.get('data', {}).get('total', 0)
        diff = data.get('data', {}).get('diff', [])
        print(f'  总记录数: {total}')
        print(f'  本页记录数: {len(diff)}')
        
        if diff:
            # 转换为 DataFrame
            df = pd.DataFrame(diff)
            
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
            
            print(f'\n数据预览:')
            print(df[['期权代码', '期权名称', '最新价', '时间价值', '内在价值', '到期日']].head())
            
            # 分析当月和次月平值期权
            unique_dates = sorted(df['到期日'].unique())
            if len(unique_dates) >= 1:
                print(f'\n{"="*80}')
                print(f'到期日: {unique_dates[0]}')
                print(f'{"="*80}')
                
                for underlying in ['50ETF', '300ETF']:
                    options = df[df['标的名称'].str.contains(underlying, na=False)]
                    if len(options) > 0:
                        options['内在价值绝对值'] = options['内在价值'].abs()
                        atm = options.sort_values('内在价值绝对值').head(3)
                        
                        print(f'\n【{underlying} 平值期权】')
                        print(atm[['期权名称', '最新价', '内在价值', '时间价值', '隐含波动率']].to_string(index=False))
            
            # 保存
            df.to_csv('data/option_analysis.csv', index=False, encoding='utf-8-sig')
            print(f'\n数据已保存到 data/option_analysis.csv')
            
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
