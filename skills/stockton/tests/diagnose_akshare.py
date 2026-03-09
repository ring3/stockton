#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Akshare 连接诊断工具

用于诊断本地 akshare 连接失败的原因
"""
import os
import sys
import socket
import urllib.request
import ssl

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

def check_proxy_settings():
    """检查代理设置"""
    print("=" * 60)
    print("1. 检查代理设置")
    print("=" * 60)
    
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
    
    has_proxy = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"  {var} = {value}")
            has_proxy = True
    
    if not has_proxy:
        print("  未发现代理环境变量")
    else:
        print("\n  [警告] 检测到代理设置，这可能导致连接问题！")
        print("  建议: 在导入 akshare 前执行:")
        print("    import os")
        print("    os.environ['HTTP_PROXY'] = ''")
        print("    os.environ['HTTPS_PROXY'] = ''")


def check_connectivity():
    """检查网络连通性"""
    print("\n" + "=" * 60)
    print("2. 检查网络连通性")
    print("=" * 60)
    
    hosts = [
        ("push2his.eastmoney.com", 443, "东方财富历史数据"),
        ("82.push2.eastmoney.com", 443, "东方财富实时数据"),
        ("www.baidu.com", 443, "百度（网络测试）"),
    ]
    
    for host, port, desc in hosts:
        try:
            sock = socket.create_connection((host, port), timeout=5)
            sock.close()
            print(f"  [OK] {desc} ({host}:{port}) - 可连接")
        except Exception as e:
            print(f"  [FAIL] {desc} ({host}:{port}) - {str(e)[:50]}")


def check_akshare_version():
    """检查 akshare 版本"""
    print("\n" + "=" * 60)
    print("3. 检查 akshare 版本")
    print("=" * 60)
    
    try:
        import akshare as ak
        print(f"  akshare 版本: {ak.__version__}")
        print(f"  akshare 路径: {ak.__file__}")
        
        # 检查关键 API 是否存在
        apis = ['stock_zh_a_hist', 'stock_zh_a_spot_em', 'stock_cyq_em']
        for api in apis:
            if hasattr(ak, api):
                print(f"  [OK] API {api} 存在")
            else:
                print(f"  [FAIL] API {api} 不存在")
    except Exception as e:
        print(f"  [ERROR] 导入 akshare 失败: {e}")


def test_direct_request():
    """测试直接 HTTP 请求"""
    print("\n" + "=" * 60)
    print("4. 测试直接 HTTP 请求")
    print("=" * 60)
    
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600519&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=0&end=20260308&lmt=5"
    
    try:
        # 禁用代理
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
        
        # 创建不验证 SSL 的上下文（仅用于测试）
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            data = response.read()
            print(f"  [OK] 请求成功")
            print(f"  状态码: {response.status}")
            print(f"  返回数据大小: {len(data)} bytes")
            print(f"  数据预览: {data[:200]}...")
    except Exception as e:
        print(f"  [FAIL] 请求失败: {e}")


def test_akshare_api():
    """测试 akshare API"""
    print("\n" + "=" * 60)
    print("5. 测试 akshare API")
    print("=" * 60)
    
    # 先清除代理
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    
    try:
        import akshare as ak
        import pandas as pd
        
        print("  测试 stock_zh_a_hist (东方财富)...")
        df = ak.stock_zh_a_hist(
            symbol="600519",
            period="daily",
            start_date="20240301",
            end_date="20240308",
            adjust="qfq"
        )
        
        if df is not None and not df.empty:
            print(f"  [OK] 成功获取数据，{len(df)} 行")
            print(f"  列名: {list(df.columns)}")
            print(f"  前3行:\n{df.head(3)}")
        else:
            print("  [FAIL] 返回空数据")
            
    except Exception as e:
        print(f"  [FAIL] API 调用失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def test_sina_backup():
    """测试新浪备用接口"""
    print("\n" + "=" * 60)
    print("6. 测试新浪备用接口")
    print("=" * 60)
    
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    os.environ['http_proxy'] = ''
    os.environ['https_proxy'] = ''
    
    try:
        import akshare as ak
        
        print("  测试 stock_zh_a_daily (新浪财经)...")
        df = ak.stock_zh_a_daily(symbol="sh600519", start_date="2024-03-01", end_date="2024-03-08")
        
        if df is not None and not df.empty:
            print(f"  [OK] 新浪接口成功，{len(df)} 行")
            print(f"  列名: {list(df.columns)}")
        else:
            print("  [FAIL] 返回空数据")
            
    except Exception as e:
        print(f"  [FAIL] 新浪接口失败: {e}")


def compare_with_github():
    """与 GitHub Actions 环境对比"""
    print("\n" + "=" * 60)
    print("7. 与 GitHub Actions 环境对比")
    print("=" * 60)
    
    print("  GitHub Actions 成功而本地失败的可能原因:")
    print("  1. 网络环境不同（GitHub 在国外，无国内防火墙限制）")
    print("  2. 本地有代理设置干扰")
    print("  3. 本地 IP 被东方财富封禁")
    print("  4. akshare 版本差异")
    print("  5. Python 环境差异（certifi/ssl 证书）")
    
    print("\n  检查是否在 GitHub Actions 中:")
    is_github = os.environ.get('GITHUB_ACTIONS') == 'true'
    print(f"    GITHUB_ACTIONS = {os.environ.get('GITHUB_ACTIONS', '未设置')}")
    print(f"    结果: {'在 GitHub Actions 中' if is_github else '在本地环境'}")


def main():
    """主函数"""
    print("Akshare 连接诊断工具")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"平台: {sys.platform}")
    print("=" * 60)
    
    check_proxy_settings()
    check_connectivity()
    check_akshare_version()
    test_direct_request()
    test_akshare_api()
    test_sina_backup()
    compare_with_github()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
