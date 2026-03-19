#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QMT 数据接收服务测试脚本

使用方法：
    # 1. 先启动接收服务
    python src/qmt_pusher.py --port 8888
    
    # 2. 运行测试脚本
    python test_qmt_receiver.py
"""

import json
import time
import random
from datetime import datetime

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2


def test_health_check(base_url: str = 'http://127.0.0.1:8888'):
    """测试健康检查"""
    print("\n[测试1] 健康检查...")
    
    try:
        response = urllib2.urlopen(f"{base_url}/health", timeout=5)
        data = json.loads(response.read().decode('utf-8'))
        print(f"  响应: {data}")
        print("  [OK] 服务正常")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_push_quotes(base_url: str = 'http://127.0.0.1:8888'):
    """测试推送行情数据"""
    print("\n[测试2] 推送行情数据...")
    
    quotes = [
        {
            'code': '000001',
            'name': '平安银行',
            'price': 10.50 + random.uniform(-0.1, 0.1),
            'change_pct': random.uniform(-2, 2),
            'volume': random.randint(1000000, 5000000),
            'amount': random.uniform(10000000, 50000000),
            'timestamp': datetime.now().isoformat(),
        },
        {
            'code': '600519',
            'name': '贵州茅台',
            'price': 1400 + random.uniform(-5, 5),
            'change_pct': random.uniform(-1, 1),
            'volume': random.randint(50000, 200000),
            'amount': random.uniform(50000000, 200000000),
            'timestamp': datetime.now().isoformat(),
        },
    ]
    
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'quotes': quotes}).encode('utf-8')
    
    try:
        request = urllib2.Request(
            f"{base_url}/api/v1/prices",
            data=data,
            headers=headers
        )
        response = urllib2.urlopen(request, timeout=10)
        result = json.loads(response.read().decode('utf-8'))
        print(f"  响应: {result}")
        
        if result.get('success'):
            print(f"  [OK] 成功推送 {result.get('saved', 0)} 条数据")
            return True
        else:
            print("  [FAIL] 推送失败")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_push_options(base_url: str = 'http://127.0.0.1:8888'):
    """测试推送期权数据"""
    print("\n[测试3] 推送期权数据...")
    
    options = [
        {
            'code': '10002544',
            'underlying': '510050',
            'option_type': 'call',
            'strike': 2.5,
            'expiry_date': '2024-03',
            'price': 0.1234,
            'iv': 0.18,
            'delta': 0.52,
            'gamma': 0.05,
            'theta': -0.01,
            'vega': 0.002,
            'rho': 0.001,
            'volume': 1234,
            'open_interest': 5678,
            'timestamp': datetime.now().isoformat(),
        },
        {
            'code': '10002545',
            'underlying': '510050',
            'option_type': 'put',
            'strike': 2.5,
            'expiry_date': '2024-03',
            'price': 0.0567,
            'iv': 0.19,
            'delta': -0.48,
            'gamma': 0.04,
            'theta': -0.008,
            'vega': 0.0018,
            'rho': -0.001,
            'volume': 567,
            'open_interest': 3456,
            'timestamp': datetime.now().isoformat(),
        },
    ]
    
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'options': options}).encode('utf-8')
    
    try:
        request = urllib2.Request(
            f"{base_url}/api/v1/options",
            data=data,
            headers=headers
        )
        response = urllib2.urlopen(request, timeout=10)
        result = json.loads(response.read().decode('utf-8'))
        print(f"  响应: {result}")
        
        if result.get('success'):
            print(f"  [OK] 成功推送 {result.get('saved', 0)} 条数据")
            return True
        else:
            print("  [FAIL] 推送失败")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_push_positions(base_url: str = 'http://127.0.0.1:8888'):
    """测试推送持仓数据"""
    print("\n[测试4] 推送持仓数据...")
    
    positions = [
        {
            'account': '88888888',
            'code': '000001',
            'name': '平安银行',
            'position_type': 'stock',
            'quantity': 1000,
            'available': 1000,
            'avg_cost': 10.20,
            'market_value': 10500,
            'pnl': 500,
            'timestamp': datetime.now().isoformat(),
        },
        {
            'account': '88888888',
            'code': '10002544',
            'name': '50ETF购3月2500',
            'position_type': 'option',
            'quantity': 10,
            'available': 10,
            'avg_cost': 0.10,
            'market_value': 1234,
            'pnl': 234,
            'timestamp': datetime.now().isoformat(),
        },
    ]
    
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({'positions': positions}).encode('utf-8')
    
    try:
        request = urllib2.Request(
            f"{base_url}/api/v1/positions",
            data=data,
            headers=headers
        )
        response = urllib2.urlopen(request, timeout=10)
        result = json.loads(response.read().decode('utf-8'))
        print(f"  响应: {result}")
        
        if result.get('success'):
            print(f"  [OK] 成功推送 {result.get('saved', 0)} 条数据")
            return True
        else:
            print("  [FAIL] 推送失败")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def run_continuous_test(base_url: str = 'http://127.0.0.1:8888', duration: int = 60):
    """持续测试（模拟 QMT 推送）"""
    print(f"\n[持续测试] 模拟 QMT 推送 {duration} 秒...")
    print("按 Ctrl+C 停止")
    
    start_time = time.time()
    count = 0
    
    try:
        while time.time() - start_time < duration:
            quotes = [
                {
                    'code': '000001',
                    'name': '平安银行',
                    'price': 10.50 + random.uniform(-0.1, 0.1),
                    'change_pct': random.uniform(-2, 2),
                    'volume': random.randint(1000000, 5000000),
                    'timestamp': datetime.now().isoformat(),
                },
            ]
            
            headers = {'Content-Type': 'application/json'}
            data = json.dumps({'quotes': quotes}).encode('utf-8')
            
            try:
                request = urllib2.Request(
                    f"{base_url}/api/v1/prices",
                    data=data,
                    headers=headers
                )
                response = urllib2.urlopen(request, timeout=5)
                count += 1
                print(f"\r  已推送 {count} 次", end='', flush=True)
            except Exception as e:
                print(f"\n  推送失败: {e}")
            
            time.sleep(1)
        
        print(f"\n  [OK] 持续测试完成，共推送 {count} 次")
        
    except KeyboardInterrupt:
        print(f"\n  [STOP] 用户停止，共推送 {count} 次")


def main():
    """主函数"""
    import sys
    
    base_url = 'http://127.0.0.1:8888'
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print("=" * 60)
    print("QMT 数据接收服务测试")
    print("=" * 60)
    print(f"目标地址: {base_url}")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("健康检查", test_health_check(base_url)))
    results.append(("行情推送", test_push_quotes(base_url)))
    results.append(("期权推送", test_push_options(base_url)))
    results.append(("持仓推送", test_push_positions(base_url)))
    
    # 统计结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
    
    print("=" * 60)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 60)
    
    # 询问是否进行持续测试
    if passed == total:
        print("\n是否进行持续压力测试？(60秒)")
        try:
            input("按 Enter 开始，Ctrl+C 跳过...")
            run_continuous_test(base_url)
        except KeyboardInterrupt:
            print("\n跳过持续测试")


if __name__ == '__main__':
    main()
