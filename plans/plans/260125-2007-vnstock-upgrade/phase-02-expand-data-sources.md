# Phase 2: Expand Data Sources

## Overview

| Attribute | Value |
|-----------|-------|
| Priority | P1 |
| Status | pending |
| Effort | 1h |
| Dependencies | Phase 1 |

Create modular data layer with `VnstockClient` wrapper class and `Listing` integration for dynamic symbol management.

## Context Links

- [vnstock 3.x API Research](./research/researcher-01-vnstock-api.md)
- [Phase 1 - Fix Critical](./phase-01-fix-critical-issues.md)

## Key Insights

1. **Listing class** provides `symbols_by_exchange()`, `symbols_by_group()` for dynamic symbol lists
2. **Quote class** reusable instance - pass symbol to `history()` method
3. **Source parameter** - VCI recommended for data quality, KBS as fallback
4. **Rate limit** - 20 req/min (Guest), 60 req/min (Community)

## Related Code Files

### Files to Create
- `src/data/__init__.py` - Package marker
- `src/data/listing.py` - Listing wrapper for symbol management
- `src/data/fetcher.py` - VnstockClient class (refactored)

### Files to Modify
- `src/bot.py` - Update imports to use new data layer

## Implementation Steps

### Step 2.1: Create `src/data/__init__.py`

```python
# src/data/__init__.py
from .listing import get_symbols_by_exchange, get_symbols_by_group
from .fetcher import VnstockClient

__all__ = ['VnstockClient', 'get_symbols_by_exchange', 'get_symbols_by_group']
```

### Step 2.2: Create `src/data/listing.py`

```python
"""Symbol listing utilities using vnstock 3.x Listing class"""
from vnstock import Listing
from ..config import DATA_SOURCE

def get_symbols_by_exchange(exchange: str) -> list:
    """
    Get all symbols from an exchange.

    Args:
        exchange: One of 'HOSE', 'HNX', 'UPCOM'

    Returns:
        List of symbol strings
    """
    try:
        listing = Listing(source=DATA_SOURCE)
        df = listing.symbols_by_exchange()

        if df is None or df.empty:
            return []

        # Normalize exchange column
        df.columns = df.columns.str.lower()

        # Filter by exchange
        mask = df['exchange'].str.upper() == exchange.upper()
        symbols = df.loc[mask, 'symbol'].tolist()

        return symbols
    except Exception as e:
        print(f"Error fetching {exchange} symbols: {e}")
        return []


def get_symbols_by_group(group: str) -> list:
    """
    Get symbols by predefined group (VN30, VN100, etc).

    Args:
        group: One of 'VN30', 'VN100', 'VNALL', etc.

    Returns:
        List of symbol strings
    """
    try:
        listing = Listing(source=DATA_SOURCE)
        df = listing.symbols_by_group(group=group)

        if df is None or df.empty:
            return []

        df.columns = df.columns.str.lower()
        return df['symbol'].tolist()
    except Exception as e:
        print(f"Error fetching {group} symbols: {e}")
        return []


def get_all_symbols() -> list:
    """Get all tradable symbols across exchanges."""
    try:
        listing = Listing(source=DATA_SOURCE)
        df = listing.all_symbols()

        if df is None or df.empty:
            return []

        df.columns = df.columns.str.lower()
        return df['symbol'].tolist()
    except Exception as e:
        print(f"Error fetching all symbols: {e}")
        return []
```

### Step 2.3: Create `src/data/fetcher.py`

```python
"""VnstockClient - Wrapper for vnstock 3.x API"""
import pandas as pd
from datetime import datetime, timedelta
from vnstock import Quote
from ..config import DATA_SOURCE, DATA_SOURCE_FALLBACK

class VnstockClient:
    """
    Unified client for vnstock 3.x API with fallback support.

    Usage:
        client = VnstockClient()
        df = client.get_historical_data('VCI', days=365)
    """

    def __init__(self, source: str = None):
        """
        Initialize client.

        Args:
            source: Data source ('VCI', 'TCBS', 'MSN', 'KBS').
                    Defaults to DATA_SOURCE from config.
        """
        self.source = source or DATA_SOURCE
        self.fallback_source = DATA_SOURCE_FALLBACK
        self._quote = None
        self._fallback_quote = None

    @property
    def quote(self) -> Quote:
        """Lazy-load Quote instance."""
        if self._quote is None:
            self._quote = Quote(source=self.source)
        return self._quote

    @property
    def fallback_quote(self) -> Quote:
        """Lazy-load fallback Quote instance."""
        if self._fallback_quote is None:
            self._fallback_quote = Quote(source=self.fallback_source)
        return self._fallback_quote

    def get_historical_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        Fetch OHLCV data with VCI → KBS fallback.

        Args:
            symbol: Stock ticker (e.g., 'VCI')
            days: Number of days to fetch (default 365)

        Returns:
            DataFrame or None if both sources fail
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Try primary source (VCI)
        df = self._fetch_history(self.quote, symbol, start_date, end_date)

        # Fallback to KBS if primary fails
        if df is None and self.fallback_source != self.source:
            print(f"Fallback to {self.fallback_source} for {symbol}")
            df = self._fetch_history(self.fallback_quote, symbol, start_date, end_date)

        return df

    def _fetch_history(self, quote: Quote, symbol: str, start: str, end: str):
        """Internal: fetch and normalize data from a quote source."""
        try:
            df = quote.history(symbol=symbol, start=start, end=end, interval='D')
            if df is None or df.empty or len(df) < 50:
                return None

            df.columns = df.columns.str.lower()
            for col in ['close', 'open', 'high', 'low', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            time_col = 'time' if 'time' in df.columns else 'date'
            df['time'] = pd.to_datetime(df[time_col])
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def get_intraday(self, symbol: str, page_size: int = 100) -> pd.DataFrame:
        """Fetch intraday trade data (for future use)."""
        try:
            return self.quote.intraday(symbol=symbol, page_size=page_size)
        except Exception as e:
            print(f"Error fetching intraday {symbol}: {e}")
            return None
```

### Step 2.4: Update `src/bot.py` to use new data layer

```python
"""Trading Bot - Main entry point"""
import argparse
import time
from .config import WATCHLIST, MIN_SCORE, VNSTOCK_API_KEY
from .data import VnstockClient, get_symbols_by_exchange
from .indicators import calculate_indicators, check_signals
from .filters import is_investable
from .notifier import send_telegram_alert

# Rate limit: ~0.5s delay between requests (60 req/min safe margin)
REQUEST_DELAY = 0.5

def main():
    parser = argparse.ArgumentParser(description='Trading Bot Scanner')
    parser.add_argument('--exchange', type=str, choices=['HOSE', 'HNX', 'UPCOM'],
                        help='Exchange to scan')
    parser.add_argument('--group', type=str, help='Stock group (VN30, VN100)')
    args = parser.parse_args()

    # Register API key if provided
    if VNSTOCK_API_KEY:
        try:
            from vnstock import register_user
            register_user(api_key=VNSTOCK_API_KEY)
            print("API key registered (Community tier)")
        except Exception:
            pass

    # Get symbols based on args
    if args.exchange:
        symbols = get_symbols_by_exchange(args.exchange)
        scan_name = args.exchange
    elif args.group:
        from .data import get_symbols_by_group
        symbols = get_symbols_by_group(args.group)
        scan_name = args.group
    else:
        symbols = WATCHLIST
        scan_name = "WATCHLIST"

    if not symbols:
        print(f"No symbols found for {scan_name}, falling back to WATCHLIST")
        symbols = WATCHLIST
        scan_name = "WATCHLIST"

    print(f"Bot v3.0 | Scanning: {scan_name} ({len(symbols)} symbols)")

    # Initialize client
    client = VnstockClient()
    signal_count = 0

    for i, symbol in enumerate(symbols):
        # Rate limiting
        if i > 0:
            time.sleep(REQUEST_DELAY)

        df = client.get_historical_data(symbol)
        if df is None:
            continue

        df = calculate_indicators(df)
        if not is_investable(df):
            continue

        score, reasons = check_signals(df)

        if score >= MIN_SCORE:
            print(f"[SIGNAL] {symbol} | Score: {score}")
            send_telegram_alert(symbol, score, reasons, df.iloc[-1]['close'], df)
            signal_count += 1
        else:
            print(f"... {symbol}: {score} pts")

    print(f"\nScan complete. Found {signal_count} signals.")

if __name__ == "__main__":
    main()
```

### Step 2.5: Update old `src/data_fetcher.py` (deprecation wrapper)

Keep for backward compatibility but redirect to new module:

```python
"""
DEPRECATED: Use src.data.fetcher.VnstockClient instead.
This file kept for backward compatibility.
"""
from .data import VnstockClient

_client = VnstockClient()

def fetch_data(symbol: str, days: int = 365):
    """Deprecated wrapper. Use VnstockClient.get_historical_data()"""
    return _client.get_historical_data(symbol, days)
```

## Todo List

- [ ] Create `src/data/__init__.py`
- [ ] Create `src/data/listing.py` with exchange/group functions
- [ ] Create `src/data/fetcher.py` with VnstockClient class
- [ ] Update `src/bot.py` to use new data layer
- [ ] Update old `src/data_fetcher.py` as deprecation wrapper
- [ ] Test `python -m src.bot --exchange HOSE`
- [ ] Test `python -m src.bot --group VN30`

## Success Criteria

- [ ] `get_symbols_by_exchange('HOSE')` returns ~400 symbols
- [ ] `get_symbols_by_exchange('HNX')` returns ~350 symbols
- [ ] `get_symbols_by_exchange('UPCOM')` returns ~800 symbols
- [ ] `VnstockClient.get_historical_data('VCI')` returns valid DataFrame
- [ ] Old `fetch_data()` still works (backward compat)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Empty symbol list | Bot scans nothing | Fallback to WATCHLIST |
| Rate limit hit | API block | Add REQUEST_DELAY constant |
| Source unavailable | No data | Try fallback source (VCI -> KBS) |

## Security Considerations

- No API key hardcoding
- Log symbols count, not full list (privacy)
