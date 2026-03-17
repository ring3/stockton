# -*- coding: utf-8 -*-
"""
使用 akshare 的 option_value_analysis_em 接口获取期权数据
目标：获取当月和次月平值期权及上下两档信息

运行说明：
- 需要网络连接正常
- 建议在无代理/VPN环境中运行
"""
import os

# 清除代理环境变量
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']:
    os.environ.pop(key, None)

import akshare as ak
import pandas as pd

print('=' * 80)
print('Akshare 期权价值分析 - 当月/次月平值期权提取')
print('=' * 80)

try:
    # 获取期权价值分析数据
    print('\n[1/3] 正在获取期权价值分析数据...')
    df = ak.option_value_analysis_em()
    print(f'     ✓ 成功获取 {len(df)} 条期权数据')
    
    # 数据处理
    print('\n[2/3] 数据处理...')
    
    # 查看有哪些标的
    print(f'\n可用标的:')
    print(df['标的名称'].value_counts())
    
    # 查看到期日分布
    print(f'\n到期日分布:')
    expiry_dates = sorted(df['到期日'].unique())
    for i, date in enumerate(expiry_dates[:5], 1):
        count = len(df[df['到期日'] == date])
        print(f'  {i}. {date}: {count} 个期权')
    
    # 获取当月和次月
    if len(expiry_dates) >= 2:
        current_month = expiry_dates[0]  # 当月
        next_month = expiry_dates[1]     # 次月
        
        print(f'\n[3/3] 提取当月({current_month})和次月({next_month})平值期权...')
        
        # 选择标的（50ETF 或 300ETF）
        for underlying in ['50ETF', '300ETF']:
            underlying_options = df[df['标的名称'].str.contains(underlying, na=False)]
            
            if len(underlying_options) == 0:
                continue
                
            print(f'\n{"="*80}')
            print(f'标的: {underlying}')
            print(f'{"="*80}')
            
            for month_label, expiry in [('当月', current_month), ('次月', next_month)]:
                month_options = underlying_options[underlying_options['到期日'] == expiry].copy()
                
                if len(month_options) == 0:
                    continue
                
                # 找出平值期权（内在价值最接近0）
                month_options['内在价值绝对值'] = month_options['内在价值'].abs()
                
                # 获取平值及上下两档（共5个）
                atm_options = month_options.sort_values('内在价值绝对值').head(5)
                
                print(f'\n【{month_label} - {expiry}】')
                print('-' * 80)
                
                display_cols = ['期权代码', '期权名称', '最新价', '标的最新价', 
                               '时间价值', '内在价值', '隐含波动率', '理论价格']
                
                # 标记平值
                for idx, row in atm_options.iterrows():
                    flag = ' ← 平值' if row['内在价值绝对值'] == atm_options['内在价值绝对值'].min() else ''
                    print(f"\n期权: {row['期权名称']} ({row['期权代码']}){flag}")
                    print(f"  最新价: {row['最新价']:.4f}")
                    print(f"  标的价: {row['标的最新价']:.4f}")
                    print(f"  时间价值: {row['时间价值']:.4f}")
                    print(f"  内在价值: {row['内在价值']:.4f}")
                    print(f"  隐含波动率: {row['隐含波动率']:.2f}%")
    
    # 保存数据
    output_file = 'data/option_value_analysis.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'\n\n✓ 完整数据已保存: {output_file}')
    
except Exception as e:
    print(f'\n✗ 错误: {e}')
    print('\n可能原因:')
    print('1. 网络连接问题')
    print('2. 代理/VPN干扰（请检查系统代理设置）')
    print('3. 接口暂时不可用')
    import traceback
    traceback.print_exc()
