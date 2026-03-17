# -*- coding: utf-8 -*-
"""
测试新的多数据源适配器
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_source import DataSourceManager

def test_adapter(source_name):
    """测试指定数据源"""
    print("\n" + "="*60)
    print("[测试数据源: {}]".format(source_name))
    print("="*60)
    
    try:
        manager = DataSourceManager(preferred_source=source_name)
        print("[OK] 初始化成功，当前数据源: {}".format(manager.current_source_name))
        
        # 测试获取股票数据
        print("\n测试获取股票数据 (000001)...")
        records = manager.get_stock_history('000001', '20250301', '20250315')
        print("[OK] 获取到 {} 条记录".format(len(records)))
        
        if records:
            print("  最新记录:")
            r = records[-1]
            print("    日期: {}, 收盘: {}, MA5: {}, 换手率: {}".format(
                r['date'], r['close'], r.get('ma5'), r.get('turnover_rate')
            ))
        
        # 测试获取指数成分股（只有东财支持）
        print("\n测试获取指数成分股 (000300)...")
        components = manager.get_index_components('000300')
        print("[OK] 获取到 {} 只成分股".format(len(components)))
        if components:
            print("  前3只: {}".format([c['stock_code'] for c in components[:3]]))
        
        return True
        
    except Exception as e:
        print("[FAIL] 测试失败: {}".format(e))
        return False


def main():
    print("="*60)
    print("多数据源适配器测试")
    print("="*60)
    
    # 测试腾讯（首选）
    results = {}
    results['akshare_tx'] = test_adapter('akshare_tx')
    
    # 测试新浪
    results['akshare_sina'] = test_adapter('akshare_sina')
    
    # 总结
    print("\n" + "="*60)
    print("[测试结果总结]")
    print("="*60)
    for name, success in results.items():
        status = "OK" if success else "FAIL"
        print("  {}: {}".format(name, status))
    
    # 推荐
    print("\n[推荐配置]")
    if results.get('akshare_tx'):
        print("  首选: akshare_tx (腾讯)")
        print("  命令: python cron.py --fetch-only --data-source akshare_tx")
    elif results.get('akshare_sina'):
        print("  首选: akshare_sina (新浪)")
        print("  命令: python cron.py --fetch-only --data-source akshare_sina")
    else:
        print("  警告: 所有数据源都不可用")


if __name__ == '__main__':
    main()
