# -*- coding: utf-8 -*-
"""
测试数据源适配器
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.data_source import DataSourceManager

def test_datasource():
    print("=" * 60)
    print("测试数据源适配器")
    print("=" * 60)
    
    # 尝试初始化数据源管理器（首选 akshare）
    try:
        print("\n[1] 尝试初始化首选 akshare...")
        manager = DataSourceManager(preferred_source='akshare', disable_proxy_on_error=True)
        print("[OK] 当前数据源: {}".format(manager.current_source_name))
    except Exception as e:
        print("[FAIL] 初始化失败: {}".format(e))
        return False
    
    # 测试获取单只股票数据
    try:
        print("\n[2] 测试获取股票数据 (000001)...")
        records = manager.get_stock_history('000001', '20250101', '20250301')
        print("[OK] 获取到 {} 条记录".format(len(records)))
        if records:
            print("  最新记录: {} 收盘价: {}".format(records[-1]['date'], records[-1]['close']))
    except Exception as e:
        print("[FAIL] 获取股票数据失败: {}".format(e))
        return False
    
    # 测试获取指数成分股
    try:
        print("\n[3] 测试获取指数成分股 (000300 沪深300)...")
        components = manager.get_index_components('000300')
        print("[OK] 获取到 {} 只成分股".format(len(components)))
        if components:
            print("  前5只: {}".format([c['stock_code'] for c in components[:5]]))
    except Exception as e:
        print("[FAIL] 获取成分股失败: {}".format(e))
        # 注意：efinance 可能不支持获取指数成分股
        if manager.current_source_name == 'efinance':
            print("  (efinance 不支持获取指数成分股，这是正常的)")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_datasource()
    sys.exit(0 if success else 1)
