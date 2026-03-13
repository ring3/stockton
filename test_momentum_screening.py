# -*- coding: utf-8 -*-
"""
测试动量策略选股 - 从沪深300中筛选动量股
"""
import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加 skill 路径到 sys.path
skill_scripts_path = os.path.join(os.path.dirname(__file__), 'skills', 'stockton', 'scripts')
if skill_scripts_path not in sys.path:
    sys.path.insert(0, skill_scripts_path)

try:
    logger.info("Importing modules...")
    from stock_screener import StockScreener, ScreenCriteria
    logger.info("[OK] Modules imported")
    
    # 初始化选股器
    screener = StockScreener()
    
    print("\n" + "=" * 70)
    print("Test 1: Relaxed Momentum Strategy from CSI 300")
    print("=" * 70)
    
    # 降低阈值测试 - 20日涨幅>0%且60日涨幅>0%（找正动量股票）
    criteria = ScreenCriteria(
        index_components="沪深300",
        momentum_20d_min=0.0,        # 20日涨幅>0%
        momentum_60d_min=0.0,        # 60日涨幅>0%
    )
    
    print("Criteria:")
    print("  - Stock pool: CSI 300")
    print("  - 20-day momentum: >0%")
    print("  - 60-day momentum: >0%")
    print()
    
    results = screener.screen_by_criteria(criteria, top_n=20)
    
    print("\n[OK] Found %d stocks matching criteria" % len(results))
    
    if results:
        print("\nTop 10 Momentum Stocks:")
        print("-" * 90)
        print("%-10s %-15s %-8s %-12s %-12s %-10s" % (
            "Code", "Name", "Score", "Price", "Change", "Industry"
        ))
        print("-" * 90)
        
        for stock in results[:10]:
            code = stock.stock_code
            name = stock.stock_name[:15]
            score = stock.total_score
            price = stock.current_price
            change = stock.change_pct
            industry = stock.industry[:10] if stock.industry else "N/A"
            print("%-10s %-15s %-8s %-12s %-12s %-10s" % (
                code, name, score, "%.2f" % price, "%.2f%%" % change, industry
            ))
    else:
        print("No stocks found")
    
    print("\n" + "=" * 70)
    print("Test 2: Very Relaxed Criteria (Any positive 20-day momentum)")
    print("=" * 70)
    
    # 更宽松的条件 - 只要有正动量即可
    criteria2 = ScreenCriteria(
        index_components="沪深300",
        momentum_20d_min=-5.0,        # 允许一定程度的下跌
    )
    
    print("Criteria:")
    print("  - Stock pool: CSI 300")
    print("  - 20-day momentum: >-5%")
    print()
    
    results2 = screener.screen_by_criteria(criteria2, top_n=20)
    
    print("\n[OK] Found %d stocks" % len(results2))
    
    if results2:
        print("\nTop 10 Stocks:")
        print("-" * 90)
        print("%-10s %-15s %-8s %-12s %-12s %-10s" % (
            "Code", "Name", "Score", "Price", "Change", "Industry"
        ))
        print("-" * 90)
        
        for stock in results2[:10]:
            code = stock.stock_code
            name = stock.stock_name[:15]
            score = stock.total_score
            price = stock.current_price
            change = stock.change_pct
            industry = stock.industry[:10] if stock.industry else "N/A"
            print("%-10s %-15s %-8s %-12s %-12s %-10s" % (
                code, name, score, "%.2f" % price, "%.2f%%" % change, industry
            ))
    
    print("\n" + "=" * 70)
    print("Momentum screening test completed!")
    print("=" * 70)
    print("\nNote: The momentum data is calculated from historical K-line data.")
    print("If no stocks match, it may indicate the current market is in a downturn.")

except Exception as e:
    logger.error("Error: %s", e)
    import traceback
    traceback.print_exc()
