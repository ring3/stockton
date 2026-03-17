# -*- coding: utf-8 -*-
"""
网络环境检测脚本
================

检测当前网络环境下 akshare API 的可用性
"""
import os
import sys
import time
import logging

# 清除环境
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_simple(name, func, timeout=10):
    """简单测试 API"""
    import concurrent.futures
    
    print(f"\n测试: {name}")
    start = time.time()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func)
        try:
            result = future.result(timeout=timeout)
            elapsed = time.time() - start
            if result is not None and not (hasattr(result, 'empty') and result.empty):
                print(f"  [OK] 成功，耗时 {elapsed:.1f}s，数据: {len(result)} 条")
                return True
            else:
                print(f"  [EMPTY] 返回空数据，耗时 {elapsed:.1f}s")
                return False
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - start
            print(f"  [TIMEOUT] 超时({timeout}s)，实际耗时 {elapsed:.1f}s")
            return False
        except Exception as e:
            elapsed = time.time() - start
            error_type = type(e).__name__
            if "RemoteDisconnected" in str(e) or "Connection aborted" in str(e):
                print(f"  [BLOCKED] 连接被重置/拦截，耗时 {elapsed:.1f}s")
            elif "Max retries" in str(e):
                print(f"  [TIMEOUT] 连接超时，耗时 {elapsed:.1f}s")
            else:
                print(f"  [ERROR] {error_type}，耗时 {elapsed:.1f}s")
            return False

def main():
    print("=" * 70)
    print("网络环境检测 - Akshare API 可用性测试")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n说明:")
    print("  [OK]      - API 可用")
    print("  [EMPTY]   - 返回空数据")
    print("  [TIMEOUT] - 连接超时")
    print("  [BLOCKED] - 被 WAF/防火墙拦截")
    print("  [ERROR]   - 其他错误")
    
    # 设置 User-Agent
    import urllib.request
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
    ]
    urllib.request.install_opener(opener)
    
    import akshare as ak
    
    # 测试关键 API
    results = {
        'ok': [],
        'failed': []
    }
    
    print("\n" + "=" * 70)
    print("【关键 API 测试】")
    print("=" * 70)
    
    # 1. 指数行情
    if test_api_simple("stock_zh_index_spot_sina", ak.stock_zh_index_spot_sina, 15):
        results['ok'].append('stock_zh_index_spot_sina')
    else:
        results['failed'].append('stock_zh_index_spot_sina')
    
    # 2. A股实时
    if test_api_simple("stock_zh_a_spot", ak.stock_zh_a_spot, 60):
        results['ok'].append('stock_zh_a_spot')
    else:
        results['failed'].append('stock_zh_a_spot')
    
    # 3. 期货数据
    if test_api_simple("futures_main_sina(IF0)", lambda: ak.futures_main_sina("IF0"), 10):
        results['ok'].append('futures_main_sina')
    else:
        results['failed'].append('futures_main_sina')
    
    # 4. 行业板块
    if test_api_simple("stock_board_industry_name_ths", ak.stock_board_industry_name_ths, 10):
        results['ok'].append('stock_board_industry_name_ths')
    else:
        results['failed'].append('stock_board_industry_name_ths')
    
    print("\n" + "=" * 70)
    print("【测试结果汇总】")
    print("=" * 70)
    print(f"可用 API ({len(results['ok'])}):")
    for api in results['ok']:
        print(f"  + {api}")
    print(f"\n不可用 API ({len(results['failed'])}):")
    for api in results['failed']:
        print(f"  - {api}")
    
    print("\n" + "=" * 70)
    if len(results['ok']) >= 3:
        print("结论: 网络环境良好，大部分 API 可用")
    elif len(results['ok']) >= 1:
        print("结论: 网络环境受限，部分 API 可用，依赖 fallback 机制")
    else:
        print("结论: 网络环境严格限制，API 大部分不可用")
    print("=" * 70)

if __name__ == "__main__":
    main()
