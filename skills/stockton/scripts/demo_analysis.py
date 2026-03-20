# -*- coding: utf-8 -*-
"""
模拟测试：展示改造后的数据分析能力
对比本地数据库 vs 网络 fetch
"""
import sys
import time
import logging

logging.basicConfig(level=logging.WARNING)

def demo_analyzer():
    """演示股票分析器"""
    print("=" * 70)
    print("DEMO 1: 股票技术分析 (stock_analyzer)")
    print("=" * 70)
    
    from stock_analyzer import analyze_trend, analyze_for_llm
    
    test_codes = ['600519', '000001', '600036']
    
    for code in test_codes:
        print(f"\n--- 分析股票 {code} ---")
        
        # 使用本地数据库分析
        start = time.time()
        result = analyze_trend(code, days=30, format_type='dict', use_local_db=True)
        local_time = time.time() - start
        
        print(f"  数据来源: 本地数据库 (SQLite)")
        print(f"  查询时间: {local_time*1000:.1f}ms")
        print(f"  股票名称: {result.get('name') or '(未知)'}")
        print(f"  趋势状态: {result.get('trend_status')}")
        print(f"  买入信号: {result.get('buy_signal')}")
        print(f"  信号评分: {result.get('signal_score')}/100")
        
        indicators = result.get('indicators', {})
        print(f"  技术指标:")
        print(f"    - 当前价: {indicators.get('current_price', 'N/A')}")
        print(f"    - MA5: {indicators.get('ma5', 'N/A')}")
        print(f"    - MA10: {indicators.get('ma10', 'N/A')}")
        print(f"    - MA20: {indicators.get('ma20', 'N/A')}")
        print(f"    - 量比: {indicators.get('volume_ratio_5d', 'N/A')}")
        print(f"    - 乖离率(MA5): {indicators.get('bias_ma5', 'N/A'):.2f}%")


def demo_screener():
    """演示股票筛选器"""
    print("\n" + "=" * 70)
    print("DEMO 2: 股票筛选 (stock_screener)")
    print("=" * 70)
    
    from stock_screener import StockScreener, ScreenFactor
    
    screener = StockScreener(use_local_db=True)
    
    # 获取沪深300成分股
    print("\n--- 沪深300成分股 ---")
    start = time.time()
    codes = screener._get_index_components('沪深300')
    elapsed = time.time() - start
    print(f"  成分股数量: {len(codes)} 只")
    print(f"  查询时间: {elapsed*1000:.1f}ms")
    print(f"  前10只: {', '.join(codes[:10])}")
    
    # 获取技术指标
    print("\n--- 技术指标示例 (600519) ---")
    tech_data = screener._dal.get_latest_tech_data('600519')
    if tech_data:
        print(f"  收盘价: {tech_data.get('close')}")
        print(f"  涨跌幅: {tech_data.get('pct_chg')}%")
        print(f"  MA5: {tech_data.get('ma5')}")
        print(f"  MA10: {tech_data.get('ma10')}")
        print(f"  MA20: {tech_data.get('ma20')}")
        print(f"  量比: {tech_data.get('volume_ratio')}")
        print(f"  多头排列: {tech_data.get('bullish_arrangement')}")
    
    # 获取动量数据
    print("\n--- 动量数据示例 (600519) ---")
    momentum = screener._dal.get_momentum_data('600519')
    if momentum:
        print(f"  20日动量: {momentum.get('momentum_20d')}%")
        print(f"  60日动量: {momentum.get('momentum_60d')}%")
        print(f"  120日动量: {momentum.get('momentum_120d')}%")
        print(f"  趋势一致性: {momentum.get('trend_consistency')}")


def demo_data_access():
    """演示数据访问层"""
    print("\n" + "=" * 70)
    print("DEMO 3: 数据访问层 (data_access)")
    print("=" * 70)
    
    from data_access import StocktonDataAccess
    
    dal = StocktonDataAccess()
    
    print(f"\n数据库路径: {dal.db_path}")
    
    # 日线数据
    print("\n--- 日线数据示例 (000001 平安银行) ---")
    df = dal.get_daily_data('000001', days=5)
    if df is not None and not df.empty:
        print(df[['date', 'close', 'ma5', 'volume_ratio']].to_string(index=False))
    
    # 股票池统计
    print("\n--- 股票池统计 ---")
    for market in ['A股', '沪市', '深市', '创业板']:
        codes = dal.get_stock_pool(market)
        print(f"  {market}: {len(codes)} 只")


if __name__ == "__main__":
    try:
        demo_data_access()
        demo_analyzer()
        demo_screener()
        
        print("\n" + "=" * 70)
        print("模拟测试完成!")
        print("=" * 70)
        print("\n关键改进:")
        print("1. 优先从本地 SQLite 读取数据，速度更快")
        print("2. 支持自动故障切换，本地失败时回退到网络 fetch")
        print("3. 技术指标(MA、量比、乖离率)在查询时自动计算")
        print("4. 动量数据(20/60/120日)从本地历史数据计算")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
