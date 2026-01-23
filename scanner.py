"""
Scanner Entry Point - Supports Quick Scan (VN30) and Full Scan (All Markets)
Usage:
    python scanner.py --mode quick   # Scan VN30 only
    python scanner.py --mode full    # Scan entire market (HOSE, HNX, UPCOM)
"""
import argparse
import sys
from src.config import WATCHLIST, MIN_SCORE
from src.data_fetcher import fetch_data
from src.indicators import calculate_indicators, check_signals
from src.filters import is_investable
from src.notifier import send_telegram_alert, send_summary_report
from src.market_scanner import analyze_market, format_top_stocks_report


def quick_scan():
    """Quick Scan - VN30 stocks only (Original logic)"""
    print("QUICK SCAN - Scanning VN30...")
    print(f"Watchlist: {len(WATCHLIST)} stocks")

    signal_count = 0

    for symbol in WATCHLIST:
        # 1. Fetch data
        df = fetch_data(symbol)
        if df is None:
            continue

        # 2. Calculate indicators
        df = calculate_indicators(df)

        # 3. Filter (liquidity/price)
        if not is_investable(df):
            continue

        # 4. Check signals
        score, reasons = check_signals(df)

        # 5. Alert if score meets threshold
        if score >= MIN_SCORE:
            print(f"SIGNAL: {symbol} (Score: {score})")
            send_telegram_alert(symbol, score, reasons, df.iloc[-1]['close'], df)
            signal_count += 1
        else:
            print(f"zzz {symbol}: {score} points (Ignored)")

    if signal_count == 0:
        print("No buy signals found.")
    else:
        print(f"Found {signal_count} signals.")


def full_scan():
    """Full Scan - All 3 exchanges (HOSE, HNX, UPCOM)"""
    print("FULL SCAN - Scanning entire market...")
    
    top_stocks, top_industries = analyze_market()
    
    # Format and send report
    report = format_top_stocks_report(top_stocks)
    print(report)
    
    # Send to Telegram
    send_summary_report(top_stocks, top_industries)
    
    print("Full scan complete.")


def main():
    parser = argparse.ArgumentParser(description='Stock Scanner')
    parser.add_argument(
        '--mode', 
        choices=['quick', 'full'], 
        default='quick',
        help='Scan mode: quick (VN30) or full (all markets)'
    )
    args = parser.parse_args()

    print(f"Starting scanner in {args.mode.upper()} mode...")
    
    if args.mode == 'quick':
        quick_scan()
    elif args.mode == 'full':
        full_scan()
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
