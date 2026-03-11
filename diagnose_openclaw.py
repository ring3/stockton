# -*- coding: utf-8 -*-
"""诊断 OpenClaw 执行问题"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills', 'stockton', 'scripts'))
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

print("=" * 60)
print("诊断: OpenClaw 工具函数执行")
print("=" * 60)

# 测试1: 直接调用 get_market_overview
print("\n[测试1] 直接调用 get_market_overview('prompt')...")
try:
    from market_analyzer import get_market_overview
    result = get_market_overview('prompt')
    print(f"结果长度: {len(result)} chars")
    print(f"包含'股指期货': {'股指期货' in result}")
    print(f"包含'ETF期权': {'ETF期权' in result}")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 逐步检查每个步骤
print("\n[测试2] 逐步执行 MarketDataAnalyzer...")
try:
    from market_analyzer import MarketDataAnalyzer
    analyzer = MarketDataAnalyzer()
    
    print("  - 获取主要指数...")
    indices = analyzer._get_main_indices()
    print(f"    获取到 {len(indices)} 个指数")
    
    print("  - 获取市场概览...")
    overview = analyzer.get_market_overview()
    print(f"    futures_basis: {len(overview.futures_basis)} 条")
    print(f"    etf_iv: {overview.etf_iv}")
    
    print("  - 生成提示词...")
    prompt = overview.to_llm_prompt()
    print(f"    提示词长度: {len(prompt)} chars")
    print(f"    包含'股指期货': {'股指期货' in prompt}")
    print(f"    包含'ETF期权': {'ETF期权' in prompt}")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
