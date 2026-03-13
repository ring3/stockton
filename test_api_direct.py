# -*- coding: utf-8 -*-
"""
直接测试 akshare API 响应时间
"""
import os
import time
import concurrent.futures

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak

def test_with_timeout(name, func, timeout_sec, *args, **kwargs):
    """测试带超时的 API"""
    print(f"\n测试: {name} (超时 {timeout_sec}s)")
    start = time.time()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            result = future.result(timeout=timeout_sec)
            elapsed = time.time() - start
            if result is not None and not (hasattr(result, 'empty') and result.empty):
                print(f"  [OK] 成功，耗时 {elapsed:.2f}s")
                return True
            else:
                print(f"  [WARN] 返回空数据，耗时 {elapsed:.2f}s")
                return False
        except concurrent.futures.TimeoutError:
            elapsed = time.time() - start
            print(f"  [TIMEOUT] 超时，耗时 {elapsed:.2f}s")
            return False
        except Exception as e:
            elapsed = time.time() - start
            print(f"  [ERROR] 错误: {str(e)[:80]}，耗时 {elapsed:.2f}s")
            return False

print('=' * 70)
print('Akshare API 直接测试（带超时）')
print('=' * 70)

# 测试指数行情
print('\n【指数行情】')
test_with_timeout("stock_zh_index_spot_sina", ak.stock_zh_index_spot_sina, 15)
test_with_timeout("stock_zh_index_spot_em", ak.stock_zh_index_spot_em, 15)

# 测试期货
print('\n【期货数据】')
test_with_timeout("futures_main_sina(IF0)", ak.futures_main_sina, 5, "IF0")

# 测试 A 股实时
print('\n【A股实时】')
test_with_timeout("stock_zh_a_spot_em", ak.stock_zh_a_spot_em, 15)
test_with_timeout("stock_zh_a_spot", ak.stock_zh_a_spot, 60)  # 这个需要较长时间

print('\n' + '=' * 70)
print('测试完成')
print('=' * 70)
