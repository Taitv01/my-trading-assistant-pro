"""
Scanner Entry Point - Supports Quick, Full, and Discovery Scan modes
Usage:
    python scanner.py --mode quick      # Scan VN30 only (~2 min)
    python scanner.py --mode full       # Scan top 132 liquid stocks (~6 min)
    python scanner.py --mode discovery  # Scan entire market (~70 min, once daily)
"""
import argparse
import sys
import time
from src.config import WATCHLIST, MIN_SCORE
from src.data_fetcher import fetch_data
from src.indicators import calculate_indicators, check_signals
from src.filters import is_investable
from src.notifier import send_telegram_alert, send_summary_report, send_discovery_report
from src.market_scanner import analyze_market, format_top_stocks_report
from src.discovery_scanner import run_discovery_scan, format_discovery_report

# Rate limiting: vnstock Guest limit is 20 requests/minute
# 4 second delay = 15 requests/min (safe margin, leaves buffer for retries)
API_DELAY_SECONDS = 4.0


def quick_scan():
    """Quick Scan - VN30 stocks only (Original logic)"""
    print("QUICK SCAN - Scanning VN30...")
    print(f"Watchlist: {len(WATCHLIST)} stocks")
    print(f"Rate limit: {API_DELAY_SECONDS}s delay per request")
    estimated_time = len(WATCHLIST) * API_DELAY_SECONDS / 60
    print(f"Estimated time: {estimated_time:.1f} minutes")

    signal_count = 0

    for i, symbol in enumerate(WATCHLIST):
        if (i + 1) % 10 == 0:
            print(f"Progress: {i + 1}/{len(WATCHLIST)}")
        
        # 1. Fetch data
        df = fetch_data(symbol)
        if df is None:
            time.sleep(API_DELAY_SECONDS)
            continue

        # 2. Calculate indicators
        df = calculate_indicators(df)

        # 3. Filter (liquidity/price)
        if not is_investable(df):
            time.sleep(API_DELAY_SECONDS)
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
        
        # Rate limiting delay
        time.sleep(API_DELAY_SECONDS)

    if signal_count == 0:
        print("No buy signals found.")
    else:
        print(f"Found {signal_count} signals.")


def full_scan():
    """Full Scan - Top liquid stocks"""
    print("FULL SCAN - Scanning top liquid stocks...")
    
    top_stocks, top_industries = analyze_market()
    
    # Format and send report
    report = format_top_stocks_report(top_stocks)
    print(report)
    
    # Send to Telegram
    send_summary_report(top_stocks, top_industries)
    
    print("Full scan complete.")


def discovery_scan():
    """Discovery Scan - Full market analysis for new opportunities"""
    print("DISCOVERY SCAN - Analyzing entire market...")
    
    report = run_discovery_scan()
    
    # Format and print
    formatted = format_discovery_report(report)
    print(formatted)
    
    # Send to Telegram
    send_discovery_report(report)
    
    print("Discovery scan complete.")


def main():
    parser = argparse.ArgumentParser(description='Stock Scanner')
    parser.add_argument(
        '--mode', 
        choices=['quick', 'full', 'discovery'], 
        default='quick',
        help='Scan mode: quick (VN30), full (top liquidity), discovery (all market)'
    )
    args = parser.parse_args()

    print(f"Starting scanner in {args.mode.upper()} mode...")
    
    if args.mode == 'quick':
        quick_scan()
    elif args.mode == 'full':
        full_scan()
    elif args.mode == 'discovery':
        discovery_scan()
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
