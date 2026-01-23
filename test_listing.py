from vnstock import Listing
import pandas as pd

def test_listing():
    print("Testing Listing...")
    
    # Try VCI all_symbols
    try:
        print("\n--- Testing VCI all_symbols ---")
        l = Listing(source='VCI')
        df = l.all_symbols()
        print(f"Total symbols found: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        if 'exchange' in df.columns:
             print("Exchange counts:")
             print(df['exchange'].value_counts())
    except Exception as e:
        print(f"VCI all_symbols failed: {e}")

    # Try MSN symbols_by_exchange
    try:
        print("\n--- Testing MSN symbols_by_exchange ---")
        l = Listing(source='MSN')
        for exchange in ['HOSE', 'HNX', 'UPCOM']:
            try:
                symbols = l.symbols_by_exchange(exchange)
                print(f"{exchange}: Found {len(symbols)} symbols")
            except Exception as e:
                print(f"{exchange}: Failed - {e}")
    except Exception as e:
        print(f"MSN Init failed: {e}")

if __name__ == "__main__":
    test_listing()
