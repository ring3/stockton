# -*- coding: utf-8 -*-
"""
测试 Baostock 数据源适配器
对比各数据源的数据差异
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.data_source import (
    DataSourceManager,
    AkshareTencentAdapter,
    AkshareSinaAdapter,
    BaostockAdapter
)

def test_source(adapter_class, name, code='000001'):
    """测试单个数据源"""
    print("\n" + "="*70)
    print("[测试: {}]".format(name))
    print("="*70)
    
    try:
        adapter = adapter_class()
        
        # 测试连接
        if not adapter.is_available():
            print("[FAIL] 连接测试失败")
            return None
        print("[OK] 连接测试通过")
        
        # 获取数据
        import time
        start = time.time()
        records = adapter.get_stock_history(code, '20250301', '20250315')
        elapsed = time.time() - start
        
        print("[OK] 获取 {} 条记录, 耗时 {:.2f}s".format(len(records), elapsed))
        
        if records:
            r = records[-1]
            print("\n最新记录详情:")
            print("  日期: {}".format(r['date']))
            print("  开盘: {}, 收盘: {}".format(r['open'], r['close']))
            print("  成交量: {} 股".format(r['volume']))
            print("  成交额: {}".format(r['amount'] if r['amount'] else 'N/A'))
            print("  MA5: {:.2f}, MA10: {:.2f}, MA20: {:.2f}, MA60: {:.2f}".format(
                r.get('ma5') or 0, r.get('ma10') or 0, 
                r.get('ma20') or 0, r.get('ma60') or 0))
            print("  涨跌幅: {:.2f}%".format(r.get('change_pct') or 0))
            print("  换手率: {}".format(
                '{:.2f}%'.format(r['turnover_rate']) if r['turnover_rate'] else 'N/A'))
        
        return records
        
    except Exception as e:
        print("[FAIL] 测试失败: {}".format(e))
        import traceback
        traceback.print_exc()
        return None


def compare_sources():
    """对比所有数据源"""
    print("="*70)
    print("数据源对比测试 - 股票: 000001 (平安银行)")
    print("="*70)
    
    results = {}
    
    # 测试腾讯
    results['akshare_tx'] = test_source(AkshareTencentAdapter, "腾讯 (akshare_tx)")
    
    # 测试新浪
    results['akshare_sina'] = test_source(AkshareSinaAdapter, "新浪 (akshare_sina)")
    
    # 测试 baostock
    results['baostock'] = test_source(BaostockAdapter, "Baostock")
    
    # 对比总结
    print("\n" + "="*70)
    print("[对比总结]")
    print("="*70)
    print("{:<20} {:<10} {:<10} {:<10} {:<10}".format(
        '数据源', '记录数', '成交额', '换手率', 'MA60'))
    print("-"*70)
    
    for name in ['akshare_tx', 'akshare_sina', 'baostock']:
        records = results[name]
        if records:
            r = records[-1]
            has_amount = 'Yes' if r.get('amount') else 'No'
            has_turnover = 'Yes' if r.get('turnover_rate') else 'No'
            has_ma60 = 'Yes' if r.get('ma60') else 'No'
            print("{:<20} {:<10} {:<10} {:<10} {:<10}".format(
                name, len(records), has_amount, has_turnover, has_ma60))
        else:
            print("{:<20} {:<10} {:<10} {:<10} {:<10}".format(
                name, 'FAIL', '-', '-', '-'))
    
    print("\n" + "="*70)
    print("[单位检查]")
    print("="*70)
    
    for name in ['akshare_tx', 'akshare_sina', 'baostock']:
        records = results[name]
        if records and len(records) >= 2:
            r = records[-1]
            print("\n{}:".format(name))
            print("  成交量单位检查: {} (应为股数，非手数)".format(r['volume']))
            if r.get('amount'):
                print("  成交额单位检查: {} (应为元)".format(r['amount']))
            if r.get('turnover_rate'):
                print("  换手率单位检查: {:.4f}% (应为百分比，如 0.94%)".format(r['turnover_rate']))
            if r.get('change_pct'):
                print("  涨跌幅单位检查: {:.2f}% (应为百分比)".format(r['change_pct']))
    
    print("\n" + "="*70)
    print("[数据源特点总结]")
    print("="*70)
    print("腾讯 (akshare_tx):")
    print("  + 速度最快")
    print("  + 网络连通性好")
    print("  - 无成交额(amount)字段")
    print("  - 无换手率(turnover_rate)字段")
    print("\n新浪 (akshare_sina):")
    print("  + 数据字段完整")
    print("  + 网络连通性好")
    print("  + 有换手率")
    print("  - 需要自行计算均线")
    print("\nBaostock:")
    print("  + 稳定性好")
    print("  + 数据范围大(1990年至今)")
    print("  + 字段完整")
    print("  - 日线数据有延迟(17:30入库)")
    print("  - 需要登录")
    print("  - 所有数据为字符串，需要转换")


if __name__ == '__main__':
    compare_sources()
