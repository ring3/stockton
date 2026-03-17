# -*- coding: utf-8 -*-
"""
OpenClaw 模拟执行: 查看大盘
测试 akshare API 可用性
"""

import os
import sys
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 清除代理
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

# 添加路径
skill_scripts_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'stockton', 'scripts')
sys.path.insert(0, skill_scripts_path)

print('=' * 70)
print('OpenClaw 模拟执行: 查看大盘')
print('=' * 70)
print()

try:
    from market_analyzer import get_market_overview, analyze_market_for_llm
    
    print('[1/3] 获取市场概况数据...')
    market_data = get_market_overview(format_type='dict')
    
    if market_data:
        indices = market_data.get('indices', {})
        indices_count = len(indices) if isinstance(indices, (dict, list)) else 0
        has_futures = 'futures_basis' in market_data and market_data['futures_basis']
        has_etf_iv = 'etf_iv' in market_data and market_data['etf_iv']
        has_stats = 'statistics' in market_data and market_data['statistics']
        
        print(f'    主要指数数量: {indices_count}')
        print(f'    期货贴水数据: {"OK" if has_futures else "FAIL"}')
        print(f'    ETF IV数据: {"OK" if has_etf_iv else "FAIL"}')
        print(f'    市场统计: {"OK" if has_stats else "FAIL"}')
        print('    状态: 成功')
        
        # 显示期货数据
        if has_futures:
            print()
            print('    期货贴水数据:')
            futures = market_data['futures_basis']
            if isinstance(futures, dict):
                for code, data in futures.items():
                    print(f'      {code}: 年化{data.get("annualized_rate", 0):+.2f}%')
            elif isinstance(futures, list):
                for item in futures:
                    code = item.get('futures_code', 'N/A')
                    rate = item.get('annualized_rate', 0)
                    print(f'      {code}: 年化{rate:+.2f}%')
    else:
        print('    状态: 无数据返回')
    
    print()
    print('[2/3] 生成LLM格式分析...')
    llm_analysis = analyze_market_for_llm()
    
    if llm_analysis and len(llm_analysis) > 100:
        preview = llm_analysis[:300].replace('\n', ' | ')
        print(f'    分析预览: {preview}...')
        print('    状态: 成功')
    else:
        print('    状态: 分析生成失败或无数据')
    
    print()
    print('[3/3] 数据源检查...')
    from data_provider import DataFetcherManager
    manager = DataFetcherManager()
    fetchers = manager.available_fetchers
    print(f'    可用数据源: {fetchers}')
    
    print()
    print('=' * 70)
    print('执行完成')
    print('=' * 70)
    
except Exception as e:
    print(f'错误: {type(e).__name__}: {str(e)[:200]}')
    import traceback
    traceback.print_exc()
