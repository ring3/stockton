# -*- coding: utf-8 -*-
"""
使用进程池测试超时
"""
import os
import multiprocessing

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

def test_index():
    import akshare as ak
    try:
        df = ak.stock_zh_index_spot_sina()
        return ('success', len(df))
    except Exception as e:
        return ('error', str(e)[:50])

if __name__ == '__main__':
    print('测试 stock_zh_index_spot_sina (进程级 10s 超时)...')
    
    ctx = multiprocessing.get_context('spawn')
    with ctx.Pool(processes=1) as pool:
        result = pool.apply_async(test_index)
        try:
            status, data = result.get(timeout=10)
            print(f'Result: {status}, {data}')
        except multiprocessing.TimeoutError:
            print('Timeout after 10s')
            pool.terminate()
            pool.join()
