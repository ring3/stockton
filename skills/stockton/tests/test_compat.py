#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试兼容层导入
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

print("=" * 60)
print("测试兼容层导入")
print("=" * 60)

try:
    from data_fetcher import (
        AkshareDataSource, 
        RealtimeQuote, 
        ChipDistribution,
        StockDailyData,
        get_stock_data
    )
    print("[OK] 兼容层类导入成功")
    
    # 测试实例化
    source = AkshareDataSource()
    print("[OK] AkshareDataSource 实例化成功")
    
    # 测试获取数据
    print("\n测试获取 600519 数据...")
    data = source.get_daily_data('600519', days=5)
    print(f"[OK] 获取到 {len(data)} 条数据")
    
    if data:
        latest = data[-1]
        print(f"[OK] 最新数据: {latest.date} 收盘: {latest.close}")
    
    print("\n[PASS] 所有兼容层测试通过！")
    
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
