# -*- coding: utf-8 -*-
"""
测试 Akshare Fetcher Fallback 功能
"""
import os
import sys
import logging

# 清除代理
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, 'skills/stockton/scripts')

from data_provider import AkshareFetcher

def test_api(name, func, *args, **kwargs):
    """测试单个 API"""
    try:
        print(f"\n测试: {name}...")
        result = func(*args, **kwargs)
        if hasattr(result, 'empty'):
            if not result.empty:
                print(f"  [OK] 成功，获取 {len(result)} 条数据")
                return True
            else:
                print(f"  [WARN] 返回空数据")
                return False
        elif result is not None:
            print(f"  [OK] 成功，结果: {result}")
            return True
        else:
            print(f"  [WARN] 返回 None")
            return False
    except Exception as e:
        print(f"  [FAIL] 失败: {str(e)[:100]}")
        return False

def main():
    print("=" * 70)
    print("Akshare Fetcher Fallback 测试")
    print("=" * 70)
    
    fetcher = AkshareFetcher()
    ak = fetcher._ak
    
    # 测试 1: 市场概览 (带 fallback)
    print("\n【测试1】市场概览 _get_market_overview")
    print("  预期行为: 先尝试 stock_zh_a_spot_em，失败后使用 stock_zh_a_spot")
    df = fetcher._get_market_overview()
    if not df.empty:
        print(f"  [OK] 成功获取 {len(df)} 条数据")
    else:
        print(f"  [FAIL] 获取失败")
    
    # 测试 2: 行业板块排行 (带 fallback)
    print("\n【测试2】行业板块排行 _get_sector_rankings")
    print("  预期行为: 先尝试 stock_board_industry_name_em，失败后使用 stock_board_industry_name_ths")
    df = fetcher._get_sector_rankings()
    if not df.empty:
        print(f"  [OK] 成功获取 {len(df)} 条数据")
    else:
        print(f"  [FAIL] 获取失败")
    
    # 测试 3: 实时行情 (带 fallback)
    print("\n【测试3】实时行情 _get_realtime_quote")
    print("  预期行为: 先尝试 stock_zh_a_spot_em，失败后使用 stock_zh_a_spot")
    quote = fetcher._get_realtime_quote("000001")
    if quote:
        print(f"  [OK] 成功获取 {quote.get('name')} 数据")
    else:
        print(f"  [FAIL] 获取失败")
    
    # 测试 4: 股票池 (带 fallback)
    print("\n【测试4】股票池 _get_stock_pool")
    print("  预期行为: 先尝试 Eastmoney 源，失败后使用 Sina 源")
    df = fetcher._get_stock_pool("A股")
    if not df.empty:
        print(f"  [OK] 成功获取 {len(df)} 条数据")
    else:
        print(f"  [FAIL] 获取失败")
    
    # 测试 5: 行业列表 (带 fallback)
    print("\n【测试5】行业列表 _get_industry_list")
    print("  预期行为: 先尝试 stock_board_industry_name_em，失败后使用 stock_board_industry_name_ths")
    df = fetcher._get_industry_list()
    if not df.empty:
        print(f"  [OK] 成功获取 {len(df)} 条数据，前5个: {df['name'].head().tolist()}")
    else:
        print(f"  [FAIL] 获取失败")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
