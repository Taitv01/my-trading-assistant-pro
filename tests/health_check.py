import sys
import os
import pandas as pd

# Thêm thư mục gốc vào path để import được src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_fetcher import fetch_data
from src.market_scanner import analyze_market

def main():
    print("🏥 STARTING HEALTH CHECK...")
    
    # 1. KIỂM TRA LẤY DỮ LIỆU (SCRAPING CHECK)
    print("\n1️⃣  Testing Data Fetching (FPT)...")
    try:
        df = fetch_data('FPT', days=100)
        if df is None or df.empty:
            print("❌ CRITICAL: Scraping failed. fetch_data('FPT') returned None or empty.")
            sys.exit(1)
        
        required_cols = ['close', 'open', 'high', 'low', 'volume', 'time']
        if not all(col in df.columns for col in required_cols):
            print(f"❌ CRITICAL: Data missing columns. Found: {df.columns}")
            sys.exit(1)
            
        print(f"✅ Data scraping successful! Rows: {len(df)}")
        print(f"   Latest date: {df.iloc[-1]['time']}")
        
    except Exception as e:
        print(f"❌ Exception during scraping check: {e}")
        sys.exit(1)

    # 2. KIỂM TRA LOGIC/RULES (RULES CHECK)
    print("\n2️⃣  Testing Analysis Logic (Rules Check)...")
    try:
        # Chạy thử analyze_market với 2 mã mẫu
        test_symbols = ['FPT', 'VCB']
        print(f"   Running dry-run analysis on: {test_symbols}")
        
        # Hàm này gọi cả calculate_indicators, check_signals
        top_stocks, _ = analyze_market(symbols=test_symbols)
        
        print("✅ Analysis logic ran without crashing.")
        # Lưu ý: top_stocks có thể rỗng nếu không có tín hiệu mua, điều này là bình thường.
        # Quan trọng là code không bị crash.
        
    except Exception as e:
        print(f"❌ Exception during logic check: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n🎉 HEALTH CHECK PASSED! System is ready for main scan.")
    sys.exit(0)

if __name__ == "__main__":
    main()
