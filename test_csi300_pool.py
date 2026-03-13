# -*- coding: utf-8 -*-
"""
测试获取沪深300成分股股票池
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

skill_scripts_path = os.path.join(os.path.dirname(__file__), 'skills', 'stockton', 'scripts')
if skill_scripts_path not in sys.path:
    sys.path.insert(0, skill_scripts_path)

try:
    from stock_screener import StockScreener
    from data_provider import DataFetcherManager
    
    print("=" * 70)
    print("Test: Get CSI 300 Stock Pool")
    print("=" * 70)
    
    screener = StockScreener()
    
    # 直接获取沪深300成分股
    print("\nGetting CSI 300 components...")
    stock_pool = screener._get_stock_pool("A股", "沪深300")
    
    print("[OK] Got %d stocks from CSI 300" % len(stock_pool))
    
    if stock_pool:
        print("\nFirst 20 CSI 300 Components:")
        print("-" * 70)
        for i, code in enumerate(stock_pool[:20], 1):
            print("  %2d. %s" % (i, code))
        
        if len(stock_pool) > 20:
            print("  ... and %d more" % (len(stock_pool) - 20))
    
    # 获取实时行情验证
    print("\n" + "=" * 70)
    print("Test: Get Real-time Quote for First 5 Stocks")
    print("=" * 70)
    
    from data_provider import AkshareFetcher
    fetcher = AkshareFetcher()
    
    print("\n%-10s %-15s %-10s %-10s" % ("Code", "Name", "Price", "Change%"))
    print("-" * 50)
    
    for code in stock_pool[:5]:
        try:
            quote = fetcher._get_realtime_quote(code)
            if quote:
                print("%-10s %-15s %-10.2f %-10.2f%%" % (
                    code, 
                    quote['name'][:15], 
                    quote['price'], 
                    quote['change_pct']
                ))
            else:
                print("%-10s %-15s %-10s %-10s" % (code, "N/A", "N/A", "N/A"))
        except Exception as e:
            print("%-10s Error: %s" % (code, str(e)[:30]))
    
    print("\n" + "=" * 70)
    print("Summary:")
    print("  - CSI 300 stock pool: %d stocks" % len(stock_pool))
    print("  - Data source: Database cache / Akshare")
    print("  - Stock screener requires pre-calculated financial data in DB")
    print("  - Use '数据预加载' to prepare data before screening")
    print("=" * 70)

except Exception as e:
    logger.error("Error: %s", e)
    import traceback
    traceback.print_exc()
