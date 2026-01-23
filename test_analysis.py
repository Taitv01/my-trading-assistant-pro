from src.data_fetcher import fetch_data
from src.indicators import calculate_indicators, check_signals
from src.filters import is_investable
from src.config import MIN_SCORE
import pandas as pd

# Test watchlist - adjust as needed
TEST_WATCHLIST = ["HPG", "SSI", "VCB", "FPT", "MWG"]

def test_analysis():
    print(f"Testing analysis logic on {len(TEST_WATCHLIST)} symbols...")

    signal_count = 0
    results = []

    for symbol in TEST_WATCHLIST:
        print(f"\n--- Analyzing {symbol} ---")
        
        # 1. Fetch data
        try:
            df = fetch_data(symbol)
            if df is None:
                print(f"FAILED {symbol}: Failed to fetch data")
                continue
            print(f"data fetched: {len(df)} rows")
        except Exception as e:
            print(f"FAILED {symbol}: Error fetching data: {e}")
            continue

        # 2. Calculate indicators
        try:
            df = calculate_indicators(df)
            last_row = df.iloc[-1]
            print(f"Indicators calculated. Last RSI: {last_row['RSI']:.2f}, MACD: {last_row['MACD']:.2f}")
        except Exception as e:
             print(f"FAILED {symbol}: Error calculating indicators: {e}")
             continue

        # 3. Filter check
        investable = is_investable(df)
        if not investable:
            last = df.iloc[-1]
            trading_val = last['close'] * last['volume']
            print(f"WARN {symbol}: Not investable. Close: {last['close']}, Volume: {last['volume']}, Value: {trading_val:,.0f} (Min: {1_000_000_000:,.0f})")
            # Continuing anyway for test purposes to see scores, or maybe strict like bot?
            # Let's be strict like bot but print why
            continue
        
        # 4. Check signals
        score, reasons = check_signals(df)
        print(f"Score: {score}. Reasons: {reasons}")

        if score >= MIN_SCORE:
            print(f"SIGNAL FOUND: {symbol} (Score: {score})")
            signal_count += 1
            results.append({
                "symbol": symbol,
                "score": score,
                "reasons": reasons,
                "price": df.iloc[-1]['close']
            })
        else:
            print(f"zzz {symbol}: {score} points (Ignored)")

    print("\n" + "="*30)
    print(f"Analysis Complete. Found {signal_count} signals.")
    for res in results:
        print(f"MATCH {res['symbol']} - Score: {res['score']} - {res['reasons']} - Price: {res['price']}")

if __name__ == "__main__":
    test_analysis()
