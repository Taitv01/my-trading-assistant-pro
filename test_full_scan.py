"""
Test Full Scan - Run full scan on a small subset of symbols
"""
from src.market_scanner import analyze_market, format_top_stocks_report

# Test with a small subset
TEST_SYMBOLS = ["HPG", "SSI", "VCB", "FPT", "MWG", "PDR", "VIX", "HCM", "VND", "TCB"]

def main():
    print("Testing Full Scan with limited symbols...")
    top_stocks, top_industries = analyze_market(symbols=TEST_SYMBOLS)
    
    print("\n" + "=" * 40)
    report = format_top_stocks_report(top_stocks)
    print(report)

if __name__ == "__main__":
    main()
