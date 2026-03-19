# -*- coding: utf-8 -*-
"""
测试 Akshare 的三个历史数据接口
比较参数、返回值和网络连通性
"""
import sys
import os
import time

# 禁用系统代理环境变量
print("[INFO] 禁用系统代理环境变量...")
proxy_backup = {}
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if key in os.environ:
        proxy_backup[key] = os.environ[key]
        del os.environ[key]
        print(f"  已删除: {key}")

import pandas as pd

# 设置 requests 默认不使用代理
import requests
session = requests.Session()
session.trust_env = False  # 不信任环境变量中的代理

#  monkey-patch akshare 的 requests
def get_session_no_proxy():
    s = requests.Session()
    s.trust_env = False
    return s

# 替换 akshare 内部使用的 session
import akshare as ak
if hasattr(ak, 'stock_zh_a_hist'):
    # 通过修改 akshare 内部的 requests 调用来禁用代理
    original_get = requests.get
    def get_no_proxy(url, **kwargs):
        kwargs['proxies'] = {'http': None, 'https': None}
        return original_get(url, **kwargs)
    requests.get = get_no_proxy

def test_eastmoney():
    """测试东方财富接口 (stock_zh_a_hist)"""
    print("\n" + "="*60)
    print("[1] 测试东方财富接口 (stock_zh_a_hist)")
    print("  目标: push2his.eastmoney.com")
    print("="*60)
    
    try:
        import akshare as ak
        
        start = time.time()
        df = ak.stock_zh_a_hist(
            symbol='000001',
            period='daily',
            start_date='20250101',
            end_date='20250301',
            adjust='qfq'
        )
        elapsed = time.time() - start
        
        print("[OK] 成功! 耗时: {:.2f}s".format(elapsed))
        print("  数据条数: {}".format(len(df)))
        print("  列名: {}".format(list(df.columns)))
        if len(df) > 0:
            print("  第一条:")
            print(df.head(1).to_string())
        return True, df
        
    except Exception as e:
        print("[FAIL] 失败: {}: {}".format(type(e).__name__, str(e)[:150]))
        return False, None


def test_sina():
    """测试新浪财经接口 (stock_zh_a_daily)"""
    print("\n" + "="*60)
    print("[2] 测试新浪财经接口 (stock_zh_a_daily)")
    print("  目标: finance.sina.com.cn")
    print("="*60)
    
    try:
        import akshare as ak
        
        start = time.time()
        df = ak.stock_zh_a_daily(
            symbol='sz000001',  # 注意：新浪需要带市场前缀
            start_date='20250101',
            end_date='20250301',
            adjust='qfq'
        )
        elapsed = time.time() - start
        
        print("[OK] 成功! 耗时: {:.2f}s".format(elapsed))
        print("  数据条数: {}".format(len(df)))
        print("  列名: {}".format(list(df.columns)))
        if len(df) > 0:
            print("  第一条:")
            print(df.head(1).to_string())
        return True, df
        
    except Exception as e:
        print("[FAIL] 失败: {}: {}".format(type(e).__name__, str(e)[:150]))
        return False, None


def test_tencent():
    """测试腾讯接口 (stock_zh_a_hist_tx)"""
    print("\n" + "="*60)
    print("[3] 测试腾讯接口 (stock_zh_a_hist_tx)")
    print("  目标: web.ifzq.gtimg.cn")
    print("="*60)
    
    try:
        import akshare as ak
        
        start = time.time()
        df = ak.stock_zh_a_hist_tx(
            symbol='sz000001',  # 注意：腾讯需要带市场前缀
            start_date='20250101',
            end_date='20250301',
            adjust='qfq'
        )
        elapsed = time.time() - start
        
        print("[OK] 成功! 耗时: {:.2f}s".format(elapsed))
        print("  数据条数: {}".format(len(df)))
        print("  列名: {}".format(list(df.columns)))
        if len(df) > 0:
            print("  第一条:")
            print(df.head(1).to_string())
        return True, df
        
    except Exception as e:
        print("[FAIL] 失败: {}: {}".format(type(e).__name__, str(e)[:150]))
        return False, None


def compare_interfaces():
    """比较三个接口"""
    results = {}
    
    # 测试东财
    success, df = test_eastmoney()
    results['eastmoney'] = {
        'success': success,
        'source': '东方财富',
        'api': 'stock_zh_a_hist',
        'code_format': '000001 (无前缀)',
        'has_ma': True if success and any(col in df.columns for col in ['MA5', 'ma5']) else False,
        'has_turnover': True if success and '换手率' in df.columns else False,
        'url': 'push2his.eastmoney.com'
    }
    
    time.sleep(1)
    
    # 测试新浪
    success, df = test_sina()
    results['sina'] = {
        'success': success,
        'source': '新浪财经',
        'api': 'stock_zh_a_daily',
        'code_format': 'sz000001 (带市场前缀)',
        'has_ma': False,
        'has_turnover': True if success and 'turnover' in df.columns else False,
        'url': 'finance.sina.com.cn'
    }
    
    time.sleep(1)
    
    # 测试腾讯
    success, df = test_tencent()
    results['tencent'] = {
        'success': success,
        'source': '腾讯证券',
        'api': 'stock_zh_a_hist_tx',
        'code_format': 'sz000001 (带市场前缀)',
        'has_ma': False,
        'has_turnover': False,
        'url': 'web.ifzq.gtimg.cn'
    }
    
    # 打印对比表
    print("\n" + "="*60)
    print("[对比总结]")
    print("="*60)
    print("{:<12} {:<10} {:<20} {:<10} {:<10}".format('数据源', '可用', 'API', '均线', '换手率'))
    print("-"*62)
    for key in ['eastmoney', 'sina', 'tencent']:
        r = results[key]
        print("{:<12} {:<10} {:<20} {:<10} {:<10}".format(
            r['source'],
            'OK' if r['success'] else 'FAIL',
            r['api'],
            'Yes' if r['has_ma'] else 'No',
            'Yes' if r['has_turnover'] else 'No'
        ))
    
    # 打印网络连通性分析
    print("\n" + "="*60)
    print("[网络连通性分析]")
    print("="*60)
    for key in ['eastmoney', 'sina', 'tencent']:
        r = results[key]
        status = "可连通" if r['success'] else "被阻止"
        print("  {} ({}): {}".format(r['source'], r['url'], status))
    
    # 推荐
    print("\n" + "="*60)
    print("[推荐方案]")
    print("="*60)
    
    available = [k for k, v in results.items() if v['success']]
    if available:
        print("可用接口: {}".format(', '.join([results[k]['source'] for k in available])))
        if 'eastmoney' in available:
            print("- 首选: 东财 (数据最完整，有均线和换手率)")
        if 'sina' in available:
            print("- 备选: 新浪 (需自己计算均线，带市场前缀)")
        if 'tencent' in available:
            print("- 备选: 腾讯 (数据最简单，带市场前缀)")
    else:
        print("警告: 所有接口都不可用")
        print("可能的解决方案:")
        print("  1. 检查系统防火墙设置")
        print("  2. 尝试切换网络环境")
        print("  3. 使用本地预下载数据文件")
    
    return results


if __name__ == '__main__':
    results = compare_interfaces()
    
    # 如果有可用接口，显示代码转换
    if any(r['success'] for r in results.values()):
        print("\n" + "="*60)
        print("[股票代码格式转换]")
        print("="*60)
        print("东财格式: 000001 (通用)")
        print("新浪/腾讯格式: sz000001 (深市), sh600000 (沪市)")
        print("\n转换规则:")
        print("  6开头 -> sh (沪市主板)")
        print("  3开头 -> sz (深市创业板)")
        print("  0开头 -> sz (深市主板)")
        print("  68开头 -> sh (科创板)")
        print("  8/4开头 -> bj (北交所)")
