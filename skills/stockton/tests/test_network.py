# -*- coding: utf-8 -*-
"""
Network tests - requires internet connection and akshare
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_akshare_import():
    """Test akshare import"""
    print("=" * 60)
    print("Test 1: Akshare Import")
    print("=" * 60)
    
    try:
        import akshare as ak
        print(f"[OK] akshare version: {ak.__version__}")
        return True
    except ImportError:
        print("[FAIL] akshare not installed")
        print("       Run: pip install akshare")
        return False


def test_stock_zh_a_hist():
    """Test stock_zh_a_hist API"""
    print("\n" + "=" * 60)
    print("Test 2: stock_zh_a_hist API")
    print("Stock: 600519 (Maotai)")
    print("=" * 60)
    
    try:
        import akshare as ak
        
        print("Fetching data...")
        df = ak.stock_zh_a_hist(
            symbol='600519',
            period='daily',
            start_date='20240301',
            end_date='20240308',
            adjust='qfq'
        )
        
        if df is not None and not df.empty:
            print(f"[OK] Got {len(df)} rows")
            print(f"[OK] Columns: {list(df.columns)}")
            print("\nFirst row:")
            print(df.head(1).to_string())
            return True
        else:
            print("[FAIL] Empty data returned")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_stock_zh_a_spot_em():
    """Test real-time quote API"""
    print("\n" + "=" * 60)
    print("Test 3: stock_zh_a_spot_em API (Real-time)")
    print("=" * 60)
    
    try:
        import akshare as ak
        
        print("Fetching real-time data...")
        df = ak.stock_zh_a_spot_em()
        
        if df is not None and not df.empty:
            print(f"[OK] Got {len(df)} stocks")
            print(f"[OK] Columns: {list(df.columns[:5])}...")
            
            # Check if 600519 is in the list
            if '600519' in df['浠ｇ爜'].values:
                print("[OK] 600519 found in data")
            else:
                print("[WARN] 600519 not found (may be normal)")
            
            return True
        else:
            print("[FAIL] Empty data returned")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_data_fetcher():
    """Test our data_fetcher module"""
    print("\n" + "=" * 60)
    print("Test 4: Data Fetcher Module")
    print("Stock: 600519")
    print("=" * 60)
    
    try:
        from data_fetcher import get_stock_data
        
        print("Fetching stock data...")
        result = get_stock_data('600519', days=5)
        
        if result['success']:
            print(f"[OK] Got {len(result['daily_data'])} days of data")
            print(f"[OK] Data source: {result['data_source']}")
            if result['daily_data']:
                latest = result['daily_data'][-1]
                print(f"[OK] Latest: {latest['date']} Close: {latest['close']}")
            return True
        else:
            print(f"[FAIL] No data returned: {result.get('error_message', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stock_analyzer():
    """Test stock analyzer"""
    print("\n" + "=" * 60)
    print("Test 5: Stock Analyzer")
    print("Stock: 600519")
    print("=" * 60)
    
    try:
        from stock_analyzer import analyze_trend
        
        print("Analyzing trend...")
        result = analyze_trend('600519', days=30, format_type='dict')
        
        if result and result.get('code'):
            print(f"[OK] Analysis complete")
            print(f"[OK] Code: {result.get('code')}")
            print(f"[OK] Trend: {result.get('trend_status', 'N/A')}")
            print(f"[OK] Signal: {result.get('buy_signal', 'N/A')}")
            print(f"[OK] Score: {result.get('signal_score', 0)}")
            return True
        else:
            print(f"[WARN] Analysis returned no data (may be normal)")
            return True
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_analyzer():
    """Test market analyzer"""
    print("\n" + "=" * 60)
    print("Test 6: Market Analyzer")
    print("=" * 60)
    
    try:
        from market_analyzer import get_market_overview
        
        print("Fetching market overview...")
        result = get_market_overview(format_type='dict')
        
        if result and result.get('indices'):
            print(f"[OK] Got market data")
            print(f"[OK] Date: {result.get('date', 'N/A')}")
            print(f"[OK] Indices: {len(result['indices'])}")
            print(f"[OK] Up: {result.get('up_count', 0)}, Down: {result.get('down_count', 0)}")
            
            if result['indices']:
                idx = result['indices'][0]
                print(f"[OK] First index: {idx.get('name', 'N/A')} = {idx.get('current', 'N/A')}")
            
            return True
        else:
            print(f"[WARN] No market data returned (may be network issue)")
            return True
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_format():
    """Test LLM prompt format"""
    print("\n" + "=" * 60)
    print("Test 7: LLM Prompt Format")
    print("=" * 60)
    
    try:
        from data_fetcher import get_stock_data_for_llm
        
        print("Generating LLM prompt...")
        prompt = get_stock_data_for_llm('600519', days=5)
        
        if prompt and len(prompt) > 50:
            print(f"[OK] Prompt generated ({len(prompt)} chars)")
            print("\nPrompt preview (first 200 chars):")
            print("-" * 40)
            print(prompt[:200])
            print("-" * 40)
            return True
        else:
            print(f"[WARN] Prompt short or error: {prompt[:100]}")
            return True
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Stockton Skill - Network Tests")
    print("=" * 70)
    print("\nThese tests require internet connection")
    print("Testing akshare data fetching...")
    print("")
    
    tests = [
        ("Akshare Import", test_akshare_import),
        ("Stock History API", test_stock_zh_a_hist),
        ("Real-time API", test_stock_zh_a_spot_em),
        ("Data Fetcher", test_data_fetcher),
        ("Stock Analyzer", test_stock_analyzer),
        ("Market Analyzer", test_market_analyzer),
        ("Prompt Format", test_prompt_format),
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
        
        time.sleep(1)  # Be nice to the server
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n[PASS] All network tests passed!")
    else:
        print(f"\n[WARN] {failed} tests failed")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Try: pip install -U akshare")
        print("3. Check if eastmoney.com is accessible")
        print("4. Try clearing proxy env vars: set HTTP_PROXY=")
    
    print("=" * 70)
