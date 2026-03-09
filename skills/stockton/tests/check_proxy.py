"""
Quick proxy check - Run this after applying fix to verify
"""
import os
import sys

# Must be before any imports
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

print("="*60)
print("Proxy Configuration Check")
print("="*60)

# Check environment
print(f"\nHTTP_PROXY env: '{os.environ.get('HTTP_PROXY', 'NOT_SET')}'")
print(f"HTTPS_PROXY env: '{os.environ.get('HTTPS_PROXY', 'NOT_SET')}'")

# Try to import and test akshare
try:
    import akshare as ak
    print(f"\nakshare version: {ak.__version__}")
    
    print("\nTesting akshare API...")
    print("Fetching 600519 daily data (5 days)...")
    
    df = ak.stock_zh_a_hist(symbol="600519", period="daily", 
                            start_date="20240301", end_date="20240308", adjust="qfq")
    
    if df is not None and len(df) > 0:
        print(f"[OK] SUCCESS! Got {len(df)} rows")
        print(f"\nFirst row:")
        print(df.head(1))
        print("\n" + "="*60)
        print("PROXY IS FIXED! You can now run test_network.py")
        print("="*60)
        sys.exit(0)
    else:
        print("[WARN] No data returned (might be API issue)")
        sys.exit(1)
        
except Exception as e:
    print(f"[FAIL] Error: {str(e)[:100]}")
    print("\n" + "="*60)
    print("PROXY STILL ACTIVE - Apply fix from PROXY_FIX.md")
    print("="*60)
    sys.exit(1)
