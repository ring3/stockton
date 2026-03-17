# -*- coding: utf-8 -*-
"""
简化的动量策略测试 - 验证选股器基本功能
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

skill_scripts_path = os.path.join(os.path.dirname(__file__), '..', 'skills', 'stockton', 'scripts')
if skill_scripts_path not in sys.path:
    sys.path.insert(0, skill_scripts_path)

try:
    from stock_screener import StockScreener, ScreenCriteria
    
    print("=" * 70)
    print("Test: Basic Stock Screening from CSI 300")
    print("=" * 70)
    
    screener = StockScreener()
    
    # 最简单的条件 - 只指定指数，不设置动量条件
    criteria = ScreenCriteria(
        index_components="沪深300",
        # 不设置动量条件，只测试基本选股功能
    )
    
    print("\nCriteria: CSI 300 only (no momentum filters)")
    print("Running screening...\n")
    
    results = screener.screen_by_criteria(criteria, top_n=10)
    
    print("[OK] Found %d stocks" % len(results))
    
    if results:
        print("\nTop 10 Stocks from CSI 300:")
        print("-" * 100)
        print("%-10s %-15s %-8s %-10s %-10s %-12s %-15s" % (
            "Code", "Name", "Score", "Price", "Change", "Market Cap", "Industry"
        ))
        print("-" * 100)
        
        for stock in results[:10]:
            code = stock.stock_code
            name = stock.stock_name[:15]
            score = stock.total_score
            price = stock.current_price
            change = stock.change_pct
            market_cap = stock.market_cap
            industry = stock.industry[:15] if stock.industry else "N/A"
            print("%-10s %-15s %-8s %-10s %-10s %-12s %-15s" % (
                code, name, score, "%.2f" % price, "%.2f%%" % change, 
                "%.0f亿" % market_cap if market_cap else "N/A", industry
            ))
        
        # 显示技术评分详情
        print("\n" + "-" * 100)
        print("Technical Score Details (first 5 stocks):")
        print("-" * 100)
        for stock in results[:5]:
            print("%s: Technical Score=%s, Above MA20=%s, Volume Ratio=%s" % (
                stock.stock_code,
                stock.technical_score,
                "Yes" if stock.current_price > stock.ma20 else "No",
                "%.2f" % stock.volume_ratio if stock.volume_ratio else "N/A"
            ))
    else:
        print("No stocks found")
    
    print("\n" + "=" * 70)
    print("Note: Momentum screening requires pre-calculated momentum data")
    print("in the database. Without momentum data, only basic technical")
    print("and financial scoring is applied.")
    print("=" * 70)

except Exception as e:
    logger.error("Error: %s", e)
    import traceback
    traceback.print_exc()
