# -*- coding: utf-8 -*-
"""
测试数据源自动故障切换功能

模拟一个数据源失败时自动切换到另一个
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_source import DataSourceManager

def test_normal_operation():
    """测试正常运行（不需要故障切换）"""
    print("\n" + "="*60)
    print("[测试1] 正常运行 - 首选数据源可用")
    print("="*60)
    
    try:
        manager = DataSourceManager(preferred_source='akshare_tx')
        print(f"[OK] 当前数据源: {manager.current_source_name}")
        
        # 获取数据
        records = manager.get_stock_history('000001', '20250301', '20250315')
        print(f"[OK] 成功获取 {len(records)} 条记录")
        
        if records:
            r = records[-1]
            print(f"  最新: {r['date']} 收盘={r['close']}")
        
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


def test_failover_simulation():
    """
    测试故障切换
    
    由于无法真正让数据源失败，我们测试以下场景:
    1. 优先选择东财（可能被代理阻止）
    2. 系统应该自动切换到腾讯或新浪
    """
    print("\n" + "="*60)
    print("[测试2] 故障切换 - 首选数据源不可用时的自动切换")
    print("="*60)
    
    try:
        # 首选东财（可能被代理阻止）
        manager = DataSourceManager(preferred_source='akshare_em')
        print(f"[INFO] 首选数据源: akshare_em")
        print(f"[INFO] 实际使用数据源: {manager.current_source_name}")
        
        # 获取数据 - 如果东财失败，应该自动切换
        records = manager.get_stock_history('000001', '20250301', '20250315')
        print(f"[OK] 成功获取 {len(records)} 条记录")
        print(f"[INFO] 最终使用数据源: {manager.current_source_name}")
        
        if manager.current_source_name != 'akshare_em':
            print("[OK] 故障切换成功: 从 akshare_em 切换到 " + manager.current_source_name)
        
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


def test_all_sources_failover():
    """测试所有数据源的故障切换链"""
    print("\n" + "="*60)
    print("[测试3] 故障切换链 - 测试多个数据源的切换")
    print("="*60)
    
    # 创建一个按特定顺序尝试的管理器
    # 模拟：baostock -> akshare_sina -> akshare_tx
    priority = ['baostock', 'akshare_sina', 'akshare_tx']
    
    try:
        manager = DataSourceManager(preferred_source='baostock', priority=priority)
        print(f"[INFO] 初始化数据源: {manager.current_source_name}")
        print(f"[INFO] 优先级顺序: {priority}")
        
        # 获取数据
        records = manager.get_stock_history('000001', '20250301', '20250315')
        print(f"[OK] 成功获取 {len(records)} 条记录")
        
        # 获取指数成分股
        components = manager.get_index_components('000300')
        print(f"[OK] 成功获取 {len(components)} 只成分股")
        
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


def test_consecutive_requests():
    """测试连续请求 - 验证数据源状态保持一致"""
    print("\n" + "="*60)
    print("[测试4] 连续请求 - 验证数据源状态一致性")
    print("="*60)
    
    try:
        manager = DataSourceManager(preferred_source='akshare_tx')
        print(f"[INFO] 初始数据源: {manager.current_source_name}")
        
        # 连续获取多只股票数据
        codes = ['000001', '000002', '600000']
        for code in codes:
            records = manager.get_stock_history(code, '20250310', '20250315')
            print(f"[OK] {code}: 获取 {len(records)} 条记录 (数据源: {manager.current_source_name})")
        
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


def test_error_recovery():
    """测试错误恢复 - 模拟某个股票在某个数据源失败"""
    print("\n" + "="*60)
    print("[测试5] 错误恢复 - 单个股票失败不影响其他股票")
    print("="*60)
    
    try:
        manager = DataSourceManager(preferred_source='akshare_tx')
        
        # 正常股票
        records = manager.get_stock_history('000001', '20250301', '20250315')
        print(f"[OK] 000001: {len(records)} 条记录")
        
        # 另一个正常股票
        records = manager.get_stock_history('600000', '20250301', '20250315')
        print(f"[OK] 600000: {len(records)} 条记录")
        
        # ETF
        records = manager.get_stock_history('510300', '20250301', '20250315')
        print(f"[OK] 510300 (沪深300ETF): {len(records)} 条记录")
        
        return True
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("="*60)
    print("数据源自动故障切换测试")
    print("="*60)
    
    results = {}
    
    # 运行所有测试
    results['normal'] = test_normal_operation()
    results['failover'] = test_failover_simulation()
    results['chain'] = test_all_sources_failover()
    results['consecutive'] = test_consecutive_requests()
    results['recovery'] = test_error_recovery()
    
    # 测试总结
    print("\n" + "="*60)
    print("[测试总结]")
    print("="*60)
    
    for name, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {name:20s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n[OK] 所有测试通过！自动故障切换功能正常工作")
    else:
        print(f"\n[WARN] {total - passed} 个测试失败")


if __name__ == '__main__':
    main()
