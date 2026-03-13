# -*- coding: utf-8 -*-
"""
独立测试 StockScreener（不依赖 OpenClaw）

运行方式:
    cd d:\coding\projects\stockton
    python test_screener_standalone.py
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

logger.info("Add path: %s", skill_scripts_path)

try:
    # 测试导入 stock_screener
    logger.info("Import stock_screener...")
    from stock_screener import StockScreener, ScreenCriteria, ScreenFactor
    logger.info("[OK] stock_screener imported")
    
    print("\n" + "=" * 70)
    print("Init StockScreener...")
    print("=" * 70)
    
    # 初始化 StockScreener（无参数，内部自动初始化）
    screener = StockScreener()
    
    print("[OK] StockScreener initialized")
    
    # 检查内部组件
    print("  - Data manager: %s" % ('OK' if screener._data_manager else 'FAIL'))
    print("  - akshare: %s" % ('OK' if screener._ak else 'FAIL'))
    print("  - Database: %s" % ('OK' if screener._db else 'FAIL'))
    
    # 测试简单的选股
    print("\n" + "=" * 70)
    print("Test stock screening")
    print("=" * 70)
    
    # 获取股票池
    stock_pool = screener._get_stock_pool("A股", "沪深300")
    
    print("[OK] Got %d CSI 300 stocks" % len(stock_pool))
    
    if stock_pool:
        print("\nTop 10 components:")
        for code in stock_pool[:10]:
            print("  - %s" % code)

except Exception as e:
    logger.error("Error: %s", e)
    import traceback
    traceback.print_exc()
