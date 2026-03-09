#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新的 data_fetcher 实现
"""
import sys
import os
import logging

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_import():
    """测试导入"""
    print("=" * 60)
    print("测试: 导入模块")
    print("=" * 60)
    
    try:
        from data_provider import DataFetcherManager, EfinanceFetcher
        print("[OK] data_provider 导入成功")
        
        if EfinanceFetcher:
            print("[OK] EfinanceFetcher 可用")
        else:
            print("[WARN] EfinanceFetcher 不可用")
            
        return True
    except Exception as e:
        print(f"[ERROR] 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fetcher_manager():
    """测试数据源管理器"""
    print("\n" + "=" * 60)
    print("测试: DataFetcherManager")
    print("=" * 60)
    
    try:
        from data_provider import DataFetcherManager
        
        manager = DataFetcherManager()
        print(f"[OK] DataFetcherManager 创建成功")
        print(f"可用数据源: {manager.available_fetchers}")
        
        return True
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_stock_data():
    """测试获取股票数据"""
    print("\n" + "=" * 60)
    print("测试: get_stock_data (600519)")
    print("=" * 60)
    
    try:
        from data_fetcher import get_stock_data
        
        result = get_stock_data('600519', days=5)
        
        print(f"成功: {result['success']}")
        print(f"代码: {result['code']}")
        print(f"名称: {result['name']}")
        print(f"数据来源: {result['data_source']}")
        print(f"数据条数: {len(result['daily_data'])}")
        
        if result['daily_data']:
            print("\n最近3日数据:")
            for d in result['daily_data'][-3:]:
                print(f"  {d['date']}: 收{d['close']:.2f} ({d['pct_chg']:+.2f}%)")
        
        return result['success']
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    results = []
    
    results.append(("导入模块", test_import()))
    results.append(("DataFetcherManager", test_fetcher_manager()))
    results.append(("获取股票数据", test_get_stock_data()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {name}")
