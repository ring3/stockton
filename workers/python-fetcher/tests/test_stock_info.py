#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票基本信息功能测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from local_db import LocalDatabase
from fetcher import StockDataFetcher


def test_stock_info():
    """测试股票基本信息功能"""
    print("=" * 60)
    print("股票基本信息功能测试")
    print("=" * 60)
    
    # 初始化数据库和获取器
    db = LocalDatabase('./data/test_stock_info.db')
    fetcher = StockDataFetcher(local_db=db)
    
    # 测试代码列表
    test_codes = ['000001', '600519', '000333']
    
    print(f"\n1. 测试获取股票基本信息（{len(test_codes)} 只）")
    print("-" * 60)
    
    for code in test_codes:
        print(f"\n获取 {code} 基本信息...")
        info = fetcher.data_source.get_stock_basic_info(code)
        
        if info and info.get('name'):
            print(f"  代码: {info['code']}")
            print(f"  名称: {info['name']}")
            print(f"  行业: {info.get('industry', 'N/A')}")
            print(f"  上市日期: {info.get('list_date', 'N/A')}")
            
            # 格式化市值显示
            total_mv = info.get('total_mv', 0)
            if total_mv >= 1e8:
                print(f"  总市值: {total_mv/1e8:.2f} 亿")
            else:
                print(f"  总市值: {total_mv}")
            
            # 保存到数据库
            db.save_stock_basic_info(info, fetcher.data_source.current_source_name)
            print(f"  [OK] 已保存到数据库")
        else:
            print(f"  [FAIL] 获取失败")
    
    print(f"\n2. 测试从数据库读取股票信息")
    print("-" * 60)
    
    for code in test_codes:
        info = db.get_stock_basic_info(code)
        if info:
            print(f"{code}: {info.get('name')} ({info.get('industry')})")
        else:
            print(f"{code}: 未找到")
    
    print(f"\n3. 测试股票信息统计")
    print("-" * 60)
    
    stats = db.get_stock_info_stats()
    print(f"总数: {stats['total_count']}")
    print(f"有名称: {stats['with_name']}")
    print(f"有行业: {stats['with_industry']}")
    print(f"最后更新: {stats['latest_update']}")
    
    print(f"\n4. 测试批量更新功能")
    print("-" * 60)
    
    stats = fetcher.fetch_and_save_stock_basic_info(test_codes)
    print(f"总计: {stats['total']}")
    print(f"保存: {stats['saved']}")
    print(f"跳过: {stats['skipped']}")
    print(f"失败: {stats['failed']}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    test_stock_info()
