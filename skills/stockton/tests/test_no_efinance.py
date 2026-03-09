#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试：确保未安装 efinance 时也能正常工作
"""
import sys
import os

# 确保代理被清除
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

print("=" * 60)
print("测试：无 efinance 环境")
print("=" * 60)

# 测试 1: 从 data_provider 导入
print("\n1. 测试从 data_provider 导入...")
try:
    from data_provider import DataFetcherManager, EfinanceFetcher, AkshareFetcher
    print(f"   [OK] EfinanceFetcher = {EfinanceFetcher}")
    print(f"   [OK] AkshareFetcher = {AkshareFetcher}")
    if EfinanceFetcher is None:
        print("   [OK] EfinanceFetcher 为 None（预期行为）")
except Exception as e:
    print(f"   [FAIL] {e}")
    sys.exit(1)

# 测试 2: 从 data_fetcher 导入
print("\n2. 测试从 data_fetcher 导入...")
try:
    from data_fetcher import (
        get_stock_data, 
        AkshareDataSource,
        EfinanceFetcher  # 这个应该是从 data_provider 导入的 None
    )
    print(f"   [OK] get_stock_data 导入成功")
    print(f"   [OK] AkshareDataSource 导入成功")
    print(f"   [OK] EfinanceFetcher = {EfinanceFetcher}")
except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 3: 使用 DataFetcherManager
print("\n3. 测试 DataFetcherManager...")
try:
    manager = DataFetcherManager()
    print(f"   [OK] DataFetcherManager 创建成功")
    print(f"   可用数据源: {manager.available_fetchers}")
    
    # 获取数据
    df, source = manager.get_daily_data('600519', days=5)
    print(f"   [OK] 获取数据成功: {len(df)} 行，来源: {source}")
except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 4: 使用 get_stock_data（内部会尝试 EfinanceFetcher）
print("\n4. 测试 get_stock_data（含 EfinanceFetcher 引用）...")
try:
    result = get_stock_data('600519', days=5)
    if result['success']:
        print(f"   [OK] get_stock_data 成功")
        print(f"   数据来源: {result['data_source']}")
        print(f"   数据条数: {len(result['daily_data'])}")
    else:
        print(f"   [FAIL] {result.get('error_message')}")
        sys.exit(1)
except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试 5: 使用 AkshareDataSource（兼容层）
print("\n5. 测试 AkshareDataSource 兼容层...")
try:
    source = AkshareDataSource()
    data = source.get_daily_data('600519', days=5)
    print(f"   [OK] AkshareDataSource 成功: {len(data)} 行")
except Exception as e:
    print(f"   [FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("[PASS] 所有测试通过！")
print("=" * 60)
print("结论：未安装 efinance 时系统正常工作，无错误显示")
