# -*- coding: utf-8 -*-
"""
Akshare API Availability Test Script
=====================================

Test all APIs used in akshare_fetcher to detect which are blocked by proxy

Usage:
    python test_akshare_apis.py

Output:
    - Test result for each API (success/failure)
    - Failure reason categorization (proxy blocked / other error)
    - Summary report
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Callable

# Remove proxy to avoid interference
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AkshareAPITester:
    """Akshare API Tester"""
    
    def __init__(self):
        self.ak = None
        self.results: List[Dict] = []
        
    def init_akshare(self) -> bool:
        """Initialize akshare"""
        try:
            import akshare as ak
            self.ak = ak
            print("[OK] akshare initialized successfully")
            return True
        except ImportError:
            print("[ERROR] akshare not installed. Run: pip install akshare")
            return False
    
    def test_api(self, name: str, func: Callable, *args, **kwargs) -> Dict:
        """
        Test a single API
        
        Args:
            name: API name
            func: Function to test
            *args, **kwargs: Function arguments
            
        Returns:
            Test result dict
        """
        result = {
            'name': name,
            'status': 'pending',
            'error_type': None,
            'error_msg': None,
            'data_preview': None,
            'duration': 0
        }
        
        start_time = time.time()
        try:
            print(f"\nTesting: {name}...")
            data = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Check result
            if hasattr(data, 'empty'):
                is_valid = not data.empty
                if is_valid:
                    result['data_preview'] = f"{len(data)} rows"
            elif hasattr(data, '__len__'):
                is_valid = len(data) > 0
                result['data_preview'] = f"{len(data)} items"
            else:
                is_valid = data is not None
                result['data_preview'] = str(data)[:50] if data else None
            
            result['status'] = 'success' if is_valid else 'empty'
            result['duration'] = round(duration, 2)
            
            if is_valid:
                print(f"  [OK] Success ({result['duration']}s) - {result['data_preview']}")
            else:
                print(f"  [WARN] Empty data ({result['duration']}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            result['duration'] = round(duration, 2)
            error_msg = str(e)
            result['error_msg'] = error_msg[:200]
            
            # Categorize error type
            if 'push2.eastmoney.com' in error_msg or 'proxy' in error_msg.lower():
                result['error_type'] = 'PROXY_BLOCKED'
                result['status'] = 'blocked'
                print(f"  [BLOCKED] Proxy blocked ({result['duration']}s)")
            elif 'Connection' in error_msg or 'Timeout' in error_msg:
                result['error_type'] = 'NETWORK_ERROR'
                result['status'] = 'network_error'
                print(f"  [NET ERROR] Network error ({result['duration']}s)")
            else:
                result['error_type'] = 'OTHER_ERROR'
                result['status'] = 'error'
                print(f"  [ERROR] {error_msg[:100]} ({result['duration']}s)")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self):
        """Run all API tests"""
        if not self.init_akshare():
            return
        
        ak = self.ak
        
        print("\n" + "=" * 70)
        print("Akshare API Availability Test")
        print("=" * 70)
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Akshare Version: {ak.__version__ if hasattr(ak, '__version__') else 'unknown'}")
        print("=" * 70)
        
        # ==================== 1. Real-time Quote APIs ====================
        print("\n[1. Real-time Quote APIs]")
        
        # A-share real-time (Eastmoney) - USED IN MARKET OVERVIEW
        self.test_api(
            "stock_zh_a_spot_em (A-share real-time - Eastmoney)",
            ak.stock_zh_a_spot_em
        )
        
        # A-share real-time (Alternative - stock_zh_a_spot)
        self.test_api(
            "stock_zh_a_spot (A-share real-time - General)",
            ak.stock_zh_a_spot
        )
        
        # Market-specific A-share
        self.test_api(
            "stock_sh_a_spot_em (Shanghai A-share)",
            ak.stock_sh_a_spot_em
        )
        
        self.test_api(
            "stock_sz_a_spot_em (Shenzhen A-share)",
            ak.stock_sz_a_spot_em
        )
        
        self.test_api(
            "stock_cy_a_spot_em (ChiNext A-share)",
            ak.stock_cy_a_spot_em
        )
        
        self.test_api(
            "stock_kc_a_spot_em (STAR Market A-share)",
            ak.stock_kc_a_spot_em
        )
        
        # Index real-time
        self.test_api(
            "stock_zh_index_spot_sina (Index real-time - Sina)",
            ak.stock_zh_index_spot_sina
        )
        
        self.test_api(
            "stock_zh_index_spot_em (Index real-time - Eastmoney)",
            ak.stock_zh_index_spot_em
        )
        
        # ==================== 2. Historical Data APIs ====================
        print("\n[2. Historical Data APIs]")
        
        self.test_api(
            "stock_zh_a_hist (A-share historical K-line)",
            ak.stock_zh_a_hist,
            symbol="000001",
            period="daily",
            start_date="20250101",
            end_date="20250301",
            adjust="qfq"
        )
        
        self.test_api(
            "stock_hk_hist (HK stock historical)",
            ak.stock_hk_hist,
            symbol="00700",
            period="daily",
            start_date="20250101",
            end_date="20250301"
        )
        
        self.test_api(
            "fund_etf_hist_em (ETF historical)",
            ak.fund_etf_hist_em,
            symbol="510050",
            period="daily",
            start_date="20250101",
            end_date="20250301",
            adjust="qfq"
        )
        
        # ==================== 3. Sector/Industry APIs ====================
        print("\n[3. Sector/Industry APIs]")
        
        # Industry rankings - USED IN MARKET OVERVIEW
        self.test_api(
            "stock_board_industry_name_em (Industry list - Eastmoney)",
            ak.stock_board_industry_name_em
        )
        
        self.test_api(
            "stock_board_industry_name_ths (Industry list - THS)",
            ak.stock_board_industry_name_ths
        )
        
        self.test_api(
            "stock_board_industry_cons_em (Industry constituents)",
            ak.stock_board_industry_cons_em,
            symbol="半导体"
        )
        
        # Concept boards
        self.test_api(
            "stock_board_concept_name_em (Concept board list)",
            ak.stock_board_concept_name_em
        )
        
        # ==================== 4. Futures APIs ====================
        print("\n[4. Futures APIs]")
        
        self.test_api(
            "futures_main_sina (Futures main contract - Sina)",
            ak.futures_main_sina,
            symbol="IF0"
        )
        
        self.test_api(
            "futures_zh_spot (Futures real-time)",
            ak.futures_zh_spot,
            symbol="IF2506,IH2506,IC2506,IM2506"
        )
        
        # ==================== 5. Index Constituent APIs ====================
        print("\n[5. Index Constituent APIs]")
        
        self.test_api(
            "index_stock_cons_weight_csindex (CSI Index constituents)",
            ak.index_stock_cons_weight_csindex,
            symbol="000300"
        )
        
        # ==================== 6. Options APIs ====================
        print("\n[6. Options APIs]")
        
        self.test_api(
            "option_risk_indicator_sse (Option risk indicators)",
            ak.option_risk_indicator_sse
        )
        
        self.test_api(
            "option_current_em (Option real-time quotes)",
            ak.option_current_em
        )
        
        self.test_api(
            "option_sse_spot_price_sina (Option spot price - Sina)",
            ak.option_sse_spot_price_sina
        )
        
        # ==================== 7. Chip Distribution APIs ====================
        print("\n[7. Chip Distribution APIs]")
        
        self.test_api(
            "stock_cyq_em (Chip distribution - Eastmoney)",
            ak.stock_cyq_em,
            symbol="000001"
        )
        
        # ==================== 8. Financial Data APIs ====================
        print("\n[8. Financial Data APIs]")
        
        self.test_api(
            "stock_financial_report_sina (Financial report - Sina)",
            ak.stock_financial_report_sina,
            stock="600519",
            symbol="利润表"
        )
        
        self.test_api(
            "stock_financial_analysis_indicator (Financial indicators)",
            ak.stock_financial_analysis_indicator,
            symbol="600519"
        )
    
    def print_report(self):
        """Print test report"""
        print("\n" + "=" * 70)
        print("Test Report Summary")
        print("=" * 70)
        
        # Statistics
        total = len(self.results)
        success = sum(1 for r in self.results if r['status'] == 'success')
        empty = sum(1 for r in self.results if r['status'] == 'empty')
        blocked = sum(1 for r in self.results if r['status'] == 'blocked')
        network_error = sum(1 for r in self.results if r['status'] == 'network_error')
        other_error = sum(1 for r in self.results if r['status'] == 'error')
        
        print(f"\nTotal Tests: {total}")
        print(f"  [OK] Success: {success}")
        print(f"  [WARN] Empty: {empty}")
        print(f"  [BLOCKED] Proxy Blocked: {blocked}")
        print(f"  [NET] Network Error: {network_error}")
        print(f"  [ERR] Other Error: {other_error}")
        
        # Categorized lists
        if blocked > 0:
            print("\n[APIs BLOCKED by Proxy]")
            for r in self.results:
                if r['status'] == 'blocked':
                    print(f"  - {r['name']}")
        
        if success > 0:
            print("\n[AVAILABLE APIs]")
            for r in self.results:
                if r['status'] == 'success':
                    print(f"  + {r['name']} ({r['data_preview']})")
        
        if other_error > 0:
            print("\n[APIs with OTHER ERRORS]")
            for r in self.results:
                if r['status'] == 'error':
                    print(f"  ! {r['name']}: {r['error_msg']}")
        
        print("\n" + "=" * 70)
        
        # Save detailed report to file
        report_file = f"akshare_api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("Akshare API Test Detailed Report\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Tests: {total}\n\n")
                
                for r in self.results:
                    f.write(f"\n{'='*70}\n")
                    f.write(f"API: {r['name']}\n")
                    f.write(f"Status: {r['status']}\n")
                    f.write(f"Duration: {r['duration']}s\n")
                    if r['data_preview']:
                        f.write(f"Data: {r['data_preview']}\n")
                    if r['error_type']:
                        f.write(f"Error Type: {r['error_type']}\n")
                    if r['error_msg']:
                        f.write(f"Error Msg: {r['error_msg']}\n")
            
            print(f"\nDetailed report saved to: {report_file}")
        except Exception as e:
            print(f"\nFailed to save report: {e}")


def main():
    """Main function"""
    tester = AkshareAPITester()
    tester.run_all_tests()
    tester.print_report()


if __name__ == "__main__":
    main()
