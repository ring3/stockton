#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 data_fetcher 导入
"""
import sys
import os

# 添加 scripts 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from data_fetcher import (
        AkshareDataSource, 
        get_stock_data,
        get_stock_data_for_llm,
        StockDailyData,
        StockDataResult,
        RealtimeQuote,
        ChipDistribution
    )
    print('[OK] Import successful')
    print(f'[OK] Available classes: AkshareDataSource, StockDailyData, StockDataResult')
    print('[OK] Available functions: get_stock_data, get_stock_data_for_llm')
    print('[OK] All checks passed')
except Exception as e:
    print(f'[ERROR] {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
