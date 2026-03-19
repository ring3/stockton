# -*- coding: utf-8 -*-
"""
数据完整性检查 - 验证各数据源的字段和单位一致性
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.data_source import (
    AkshareTencentAdapter, 
    AkshareSinaAdapter, 
    BaostockAdapter
)

def check_adapter(adapter_class, name):
    sep = "="*60
    print(sep)
    print(f'[检查] {name}')
    print(sep)
    
    try:
        adapter = adapter_class()
        if not adapter.is_available():
            print(f'[SKIP] {name} 不可用')
            return
            
        records = adapter.get_stock_history('000001', '20250310', '20250315')
        if not records:
            print(f'[FAIL] 未获取到数据')
            return
            
        r = records[-1]
        
        # 检查字段
        required_fields = ['code', 'date', 'open', 'high', 'low', 'close', 
                          'volume', 'amount', 'ma5', 'ma10', 'ma20', 'ma60', 
                          'change_pct', 'turnover_rate']
        
        print(f'记录数: {len(records)}')
        print('\n字段检查:')
        for field in required_fields:
            value = r.get(field)
            if value is None:
                print(f'  {field}: None (缺失)')
            else:
                print(f'  {field}: {value}')
        
        # 单位检查
        print('\n单位检查:')
        vol = r.get('volume')
        print(f'  volume: {vol} (类型: {type(vol).__name__})')
        if vol and vol > 1000000:
            print(f'    -> 疑似"股"单位 (数值 {vol} 较大)')
        elif vol and vol < 100000:
            print(f'    -> 疑似"手"单位 (数值 {vol} 较小)')
        
        amt = r.get('amount')
        print(f'  amount: {amt}')
        
        turnover = r.get('turnover_rate')
        print(f'  turnover_rate: {turnover}')
        if turnover:
            if turnover > 1:
                print(f'    -> 百分比单位 (如 0.88%)')
            else:
                print(f'    -> 小数单位 (如 0.0088)')
                
        # 检查连续几天的volume差异
        if len(records) >= 2:
            print('\n连续性检查:')
            for i in range(min(3, len(records))):
                rec = records[i]
                print(f'  {rec["date"]}: vol={rec["volume"]}, close={rec["close"]}')
                
    except Exception as e:
        print(f'[ERROR] {e}')
        import traceback
        traceback.print_exc()


def main():
    sep = "="*60
    print(sep)
    print('数据完整性检查 - 单位统一性验证')
    print(sep)
    print('\n数据库表字段要求:')
    print('  code, date, open, high, low, close, volume, amount,')
    print('  ma5, ma10, ma20, ma60, change_pct, turnover_rate')
    print('\n单位要求:')
    print('  volume: 股 (不是手)')
    print('  amount: 元')
    print('  turnover_rate: % (不是小数)')
    print('  change_pct: %')
    
    # 检查腾讯
    check_adapter(AkshareTencentAdapter, '腾讯 (akshare_tx)')
    
    # 检查新浪
    check_adapter(AkshareSinaAdapter, '新浪 (akshare_sina)')
    
    # 检查baostock
    check_adapter(BaostockAdapter, 'Baostock')
    
    print('\n' + sep)
    print('检查完成')
    print(sep)


if __name__ == '__main__':
    main()
