"""
Scanner Entry Point - Supports Quick, Full, Discovery, and Bot modes
Usage:
    python scanner.py --mode quick      # Scan VN30 only (~2 min)
    python scanner.py --mode full       # Scan top 132 liquid stocks (~6 min)
    python scanner.py --mode discovery  # Scan entire market (~70 min, once daily)
    python scanner.py --mode bot        # Start Telegram command bot (interactive)
"""
import argparse
import sys
import time
from src.config import WATCHLIST, MIN_SCORE, VNSTOCK_API_KEY
from src.data_fetcher import fetch_data
from src.indicators import calculate_indicators, check_signals, check_sell_signals
from src.filters import is_investable
from src.notifier import send_telegram_message, send_sell_alert, send_summary_report, send_discovery_report
from src.market_scanner import analyze_market, format_top_stocks_report
from src.discovery_scanner import run_discovery_scan, format_discovery_report
from src.price_target import calculate_price_targets, format_price_target
from src.tracker import record_signal

# Sell signal threshold
MIN_SELL_SCORE = 7

# Default Rate limiting (Guest)
API_DELAY_SECONDS = 3.0

# Register API Key if available to increase limit
if VNSTOCK_API_KEY:
    try:
        from vnstock import register_user
        register_user(api_key=VNSTOCK_API_KEY)
        # Community Tier: 60 req/min => 1s delay (safe margin 1.2s)
        API_DELAY_SECONDS = 1.2 
        print(f"[OK] VNSTOCK API Key registered. Rate limit updated (Delay: {API_DELAY_SECONDS}s)")
    except Exception as e:
        print(f"[WARN] Warning: Could not register API key: {e}")


def quick_scan():
    """Quick Scan - VN30 stocks only (with Buy + Sell signals)"""
    print("QUICK SCAN - Scanning VN30...")
    print(f"Watchlist: {len(WATCHLIST)} stocks")
    print(f"Rate limit: {API_DELAY_SECONDS}s delay per request")
    estimated_time = len(WATCHLIST) * API_DELAY_SECONDS / 60
    print(f"Estimated time: {estimated_time:.1f} minutes")

    buy_count = 0
    sell_count = 0

    for i, symbol in enumerate(WATCHLIST):
        # In tiến độ
        if (i + 1) % 5 == 0:
            print(f"Progress: {i + 1}/{len(WATCHLIST)}...")
        
        try:
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

            # 4. Check BUY signals
            buy_score, buy_reasons = check_signals(df)

            # 5. Check SELL signals
            sell_score, sell_reasons = check_sell_signals(df)

            # 6. Alert if buy score meets threshold
            if buy_score >= MIN_SCORE:
                print(f"🔥 BUY SIGNAL: {symbol} (Score: {buy_score})")
                
                # Calculate price targets
                pt = calculate_price_targets(df, 'buy')
                
                # Send alert
                send_telegram_message(symbol, buy_score, buy_reasons, df.iloc[-1]['close'], df)
                
                # Record signal for tracking
                record_signal(
                    symbol=symbol,
                    signal_type='buy',
                    score=buy_score,
                    reasons=buy_reasons,
                    price=df.iloc[-1]['close'],
                    target_price=pt['target_price'],
                    stop_loss=pt['stop_loss']
                )
                buy_count += 1
            
            # 7. Alert if sell score meets threshold
            elif sell_score >= MIN_SELL_SCORE:
                print(f"📉 SELL SIGNAL: {symbol} (Score: {sell_score})")
                
                # Calculate price targets
                pt = calculate_price_targets(df, 'sell')
                
                # Send sell alert
                send_sell_alert(symbol, sell_score, sell_reasons, df.iloc[-1]['close'], df)
                
                # Record signal for tracking
                record_signal(
                    symbol=symbol,
                    signal_type='sell',
                    score=sell_score,
                    reasons=sell_reasons,
                    price=df.iloc[-1]['close'],
                    target_price=pt['target_price'],
                    stop_loss=pt['stop_loss']
                )
                sell_count += 1
            else:
                print(f"   {symbol}: Buy={buy_score} Sell={sell_score} (Ignored)")
        
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
        
        # Rate limiting
        time.sleep(API_DELAY_SECONDS)

    print(f"\n{'='*30}")
    print(f"📊 Results: {buy_count} buy signals, {sell_count} sell signals")
    if buy_count == 0 and sell_count == 0:
        print("No signals found.")


def full_scan():
    """Full Scan - Top liquid stocks"""
    print("FULL SCAN - Scanning top liquid stocks...")
    
    # Hàm này gọi logic bên market_scanner.py (đã xử lý delay bên đó)
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
    
    # Hàm này gọi logic bên discovery_scanner.py (đã xử lý delay bên đó)
    report = run_discovery_scan()
    
    # Format and print
    formatted = format_discovery_report(report)
    print(formatted)
    
    # Send to Telegram
    send_discovery_report(report)
    
    print("Discovery scan complete.")


def bot_mode():
    """Start interactive Telegram Command Bot"""
    print("BOT MODE - Starting Telegram Command Bot...")
    from src.telegram_bot import run_bot
    run_bot()


def main():
    parser = argparse.ArgumentParser(description='Stock Scanner')
    parser.add_argument(
        '--mode', 
        choices=['quick', 'full', 'discovery', 'bot'], 
        default='quick',
        help='Scan mode: quick (VN30), full (top liquidity), discovery (all market), bot (interactive)'
    )
    args = parser.parse_args()

    print(f"Starting scanner in {args.mode.upper()} mode...")
    
    if args.mode == 'quick':
        quick_scan()
    elif args.mode == 'full':
        full_scan()
    elif args.mode == 'discovery':
        discovery_scan()
    elif args.mode == 'bot':
        bot_mode()
    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
