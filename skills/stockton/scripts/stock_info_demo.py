#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票基本信息查询示例

演示如何使用新添加的股票信息查询功能
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from data_provider.base import DataFetcherManager


def main():
    print("=" * 60)
    print("股票基本信息查询演示")
    print("=" * 60)
    
    # 初始化数据管理器
    manager = DataFetcherManager()
    print(f"\n可用数据源: {manager.available_fetchers}")
    
    # 测试股票代码
    test_codes = ['000001', '600519', '000333', '000858', '002415']
    
    print("\n" + "-" * 60)
    print("查询股票基本信息")
    print("-" * 60)
    
    for code in test_codes:
        print(f"\n查询股票: {code}")
        info, source = manager.get_stock_basic_info(code)
        
        if info and info.get('name'):
            print(f"  数据源: {source}")
            print(f"  代码: {info['code']}")
            print(f"  名称: {info['name']}")
            print(f"  行业: {info.get('industry', 'N/A')}")
            print(f"  上市日期: {info.get('list_date', 'N/A')}")
            
            # 格式化市值显示
            total_mv = info.get('total_mv', 0)
            circ_mv = info.get('circ_mv', 0)
            
            if total_mv > 0:
                if total_mv >= 1e12:
                    print(f"  总市值: {total_mv/1e12:.2f} 万亿")
                elif total_mv >= 1e8:
                    print(f"  总市值: {total_mv/1e8:.2f} 亿")
                else:
                    print(f"  总市值: {total_mv:.2f}")
            
            if circ_mv > 0:
                if circ_mv >= 1e12:
                    print(f"  流通市值: {circ_mv/1e12:.2f} 万亿")
                elif circ_mv >= 1e8:
                    print(f"  流通市值: {circ_mv/1e8:.2f} 亿")
        else:
            print(f"  查询失败")
    
    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
