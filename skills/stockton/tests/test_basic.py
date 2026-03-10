# -*- coding: utf-8 -*-
"""Basic functionality tests (no network required)"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_import():
    """Test module imports"""
    print("=" * 60)
    print("Test 1: Module Imports")
    print("=" * 60)
    
    try:
        from data_fetcher import (
            StockDailyData, RealtimeQuote, ChipDistribution,
            StockDataResult,
            get_stock_data, get_stock_data_for_llm
        )
        print("[OK] data_fetcher imported")
        
        from stock_analyzer import (
            TrendStatus, VolumeStatus, BuySignal,
            TechnicalIndicators, SupportResistance, TrendAnalysisResult,
            StockTrendAnalyzer, analyze_trend
        )
        print("[OK] stock_analyzer imported")
        
        from market_analyzer import (
            MarketIndex, SectorInfo, MarketOverview,
            MarketDataAnalyzer, get_market_overview
        )
        print("[OK] market_analyzer imported")
        
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False


def test_data_models():
    """Test data models"""
    print("\n" + "=" * 60)
    print("Test 2: Data Models")
    print("=" * 60)
    
    from data_fetcher import StockDailyData, RealtimeQuote, StockDataResult
    
    daily = StockDailyData(
        date='2024-01-15', code='600519',
        open=1680.0, high=1700.0, low=1670.0, close=1690.0,
        volume=50000.0, amount=85000000.0, pct_chg=1.2,
        ma5=1685.0, ma10=1675.0,
    )
    print("[OK] StockDailyData created")
    
    d = daily.to_dict()
    assert d['code'] == '600519'
    print("[OK] to_dict() works")
    
    quote = RealtimeQuote(
        code='600519', name='璐靛窞鑼呭彴',
        price=1695.0, change_pct=0.3, volume_ratio=1.1,
    )
    print("[OK] RealtimeQuote created")
    
    result = StockDataResult(
        success=True, code='600519', name='璐靛窞鑼呭彴',
        daily_data=[daily], realtime_quote=quote,
    )
    print("[OK] StockDataResult created")
    
    r = result.to_dict()
    assert r['success'] == True
    print("[OK] StockDataResult.to_dict() works")
    
    json_str = result.to_json()
    assert '600519' in json_str
    print("[OK] to_json() works")
    
    return True


def test_analyzer_models():
    """Test analyzer models"""
    print("\n" + "=" * 60)
    print("Test 3: Analyzer Models")
    print("=" * 60)
    
    from stock_analyzer import (
        TrendAnalysisResult, TechnicalIndicators, SupportResistance,
        TrendStatus, BuySignal
    )
    
    result = TrendAnalysisResult(
        code='600519', name='璐靛窞鑼呭彴',
        trend_status=TrendStatus.BULL.value,
        buy_signal=BuySignal.BUY.value,
        signal_score=75,
    )
    print("[OK] TrendAnalysisResult created")
    
    d = result.to_dict()
    assert d['signal_score'] == 75
    print("[OK] to_dict() works")
    
    prompt = result.to_llm_prompt()
    assert '璐靛窞鑼呭彴' in prompt
    print("[OK] to_llm_prompt() works")
    
    return True


def test_market_models():
    """Test market analyzer models"""
    print("\n" + "=" * 60)
    print("Test 4: Market Models")
    print("=" * 60)
    
    from market_analyzer import MarketIndex, MarketOverview, SectorInfo
    
    index = MarketIndex(
        code='sh000001', name='涓婅瘉鎸囨暟',
        current=2850.50, change_pct=0.54,
    )
    print("[OK] MarketIndex created")
    
    overview = MarketOverview(
        date='2024-01-15', indices=[index],
        up_count=3200, down_count=1500, total_amount=8500.5,
    )
    print("[OK] MarketOverview created")
    
    d = overview.to_dict()
    assert d['up_count'] == 3200
    print("[OK] to_dict() works")
    
    prompt = overview.to_llm_prompt()
    assert '涓婅瘉鎸囨暟' in prompt
    print("[OK] to_llm_prompt() works")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Stockton Skill - Basic Tests")
    print("=" * 70)
    print("\nNo network required")
    print("")
    
    tests = [
        ("Import", test_import),
        ("Data Models", test_data_models),
        ("Analyzer", test_analyzer_models),
        ("Market", test_market_models),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"\n[ERROR] {name}: {e}")
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n[PASS] All tests passed!")
    
    print("=" * 70)
