# -*- coding: utf-8 -*-
"""
简单测试 Baostock 数据源
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

print("="*60)
print("测试 Baostock 数据源")
print("="*60)

try:
    from src.data_source import BaostockAdapter
    
    adapter = BaostockAdapter()
    print("[OK] 适配器初始化成功")
    
    # 获取数据
    print("\n获取股票数据 (000001)...")
    records = adapter.get_stock_history('000001', '20250301', '20250315')
    print("[OK] 获取到 {} 条记录".format(len(records)))
    
    if records:
        print("\n最新记录:")
        r = records[-1]
        print("  日期: {}".format(r['date']))
        print("  收盘: {}".format(r['close']))
        print("  成交量: {} 股".format(r['volume']))
        print("  成交额: {} 元".format(r['amount']))
        print("  涨跌幅: {:.2f}%".format(r.get('change_pct') or 0))
        print("  换手率: {:.2f}%".format(r.get('turnover_rate') or 0))
        print("  MA5: {:.2f}, MA10: {:.2f}, MA20: {:.2f}, MA60: {:.2f}".format(
            r.get('ma5') or 0, r.get('ma10') or 0, 
            r.get('ma20') or 0, r.get('ma60') or 0))
    
    print("\n" + "="*60)
    print("Baostock 测试通过!")
    print("="*60)
    
except Exception as e:
    print("[FAIL] 测试失败: {}".format(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
