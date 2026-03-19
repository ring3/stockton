# -*- coding: utf-8 -*-
"""
简单测试 - 只测试股票数据获取
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.data_source import DataSourceManager

print("="*60)
print("测试腾讯数据源 (akshare_tx)")
print("="*60)

try:
    manager = DataSourceManager(preferred_source='akshare_tx')
    print("[OK] 初始化成功，当前数据源: {}".format(manager.current_source_name))
    
    # 测试获取股票数据
    print("\n获取股票数据 (000001)...")
    records = manager.get_stock_history('000001', '20250301', '20250315')
    print("[OK] 获取到 {} 条记录".format(len(records)))
    
    if records:
        print("\n最新3条记录:")
        for r in records[-3:]:
            print("  {}: 开盘={}, 收盘={}, MA5={:.2f}, 换手={:.2f}%".format(
                r['date'], r['open'], r['close'], 
                r.get('ma5') or 0, r.get('turnover_rate') or 0
            ))
    
    print("\n" + "="*60)
    print("测试通过！可以使用腾讯数据源")
    print("="*60)
    
except Exception as e:
    print("[FAIL] 测试失败: {}".format(e))
    import traceback
    traceback.print_exc()
