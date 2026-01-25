# Phase 1: Fix Critical Issues

## Overview

| Attribute | Value |
|-----------|-------|
| Priority | P1 - CRITICAL |
| Status | pending |
| Effort | 1h |
| Dependencies | None |

Fix deprecated vnstock API, broken YAML workflows, and missing module structure.

## Context Links

- [vnstock 3.x API Research](./research/researcher-01-vnstock-api.md)
- [Current data_fetcher.py](../src/data_fetcher.py)
- [Current main.yml](../.github/workflows/main.yml)

## Key Insights

1. **API Migration**: `stock_historical_data()` -> `Quote(symbol).history()`
2. **YAML Error**: `main.yml:32` has wrong indentation on `env:` block
3. **Missing Module**: `src/__init__.py` required for `-m src.bot` to work
4. **argparse**: bot.py needs `--exchange` argument for dynamic symbol lists

## Related Code Files

### Files to Modify
- `src/data_fetcher.py` - Migrate to vnstock 3.x Quote class
- `src/config.py` - Add DATA_SOURCE, VNSTOCK_API_KEY env vars
- `src/bot.py` - Add argparse for --exchange argument
- `.github/workflows/main.yml` - Fix indentation at line 32
- `.github/workflows/hnx_scan.yml` - Add missing setup steps
- `.github/workflows/upcom_scan.yml` - Add missing setup steps

### Files to Create
- `src/__init__.py` - Empty file for Python module

## Implementation Steps

### Step 1.1: Create `src/__init__.py`

Create empty file to make `src` a proper Python package.

```python
# src/__init__.py
# Package marker
```

### Step 1.2: Update `src/config.py`

Add new environment variables for vnstock 3.x:

```python
import os

# --- TELEGRAM CONFIG ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- VNSTOCK CONFIG (NEW) ---
DATA_SOURCE = os.environ.get('VNSTOCK_DATA_SOURCE', 'VCI')  # Primary: VCI
DATA_SOURCE_FALLBACK = 'KBS'  # Fallback when VCI fails
VNSTOCK_API_KEY = os.environ.get('VNSTOCK_API_KEY', '')  # Optional for Community tier

# --- WATCHLIST (Fallback when no --exchange) ---
WATCHLIST = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
    "DGW", "DXG", "DIG", "PDR", "VIX", "HCM", "VND"
]

# --- FILTERS ---
MIN_VOLUME_VALUE = 1_000_000_000  # 1 Ty VND/session
MIN_PRICE = 10000                 # Price > 10k

# --- SIGNAL THRESHOLDS ---
MIN_SCORE = 4  # Minimum score to alert
```

### Step 1.3: Update `src/data_fetcher.py`

Replace deprecated API with vnstock 3.x Quote class:

```python
import pandas as pd
from datetime import datetime, timedelta
from vnstock import Quote
from .config import DATA_SOURCE

def fetch_data(symbol: str, days: int = 365):
    """Fetch historical data using vnstock 3.x API"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # vnstock 3.x: Use Quote class
        quote = Quote(symbol=symbol, source=DATA_SOURCE)
        df = quote.history(start=start_date, end=end_date, interval='D')

        if df is None or df.empty or len(df) < 50:
            return None

        # Normalize column names (vnstock 3.x uses lowercase)
        df.columns = df.columns.str.lower()

        # Ensure numeric types
        cols = ['close', 'open', 'high', 'low', 'volume']
        for col in cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Handle time/date column
        time_col = 'time' if 'time' in df.columns else 'date'
        df['time'] = pd.to_datetime(df[time_col])

        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None
```

### Step 1.4: Update `src/bot.py` with argparse

Add `--exchange` argument and dynamic symbol fetching:

```python
import argparse
from .config import WATCHLIST, MIN_SCORE, DATA_SOURCE, VNSTOCK_API_KEY
from .data_fetcher import fetch_data
from .indicators import calculate_indicators, check_signals
from .filters import is_investable
from .notifier import send_telegram_alert

def get_symbols(exchange: str = None) -> list:
    """Get symbols from exchange or fallback to WATCHLIST"""
    if not exchange:
        return WATCHLIST

    try:
        from vnstock import Listing
        listing = Listing(source=DATA_SOURCE)
        df = listing.symbols_by_exchange()
        # Filter by exchange column
        symbols = df[df['exchange'].str.upper() == exchange.upper()]['symbol'].tolist()
        return symbols if symbols else WATCHLIST
    except Exception as e:
        print(f"Error fetching {exchange} symbols: {e}")
        return WATCHLIST

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Trading Bot Scanner')
    parser.add_argument('--exchange', type=str, choices=['HOSE', 'HNX', 'UPCOM'],
                        help='Exchange to scan (HOSE/HNX/UPCOM)')
    args = parser.parse_args()

    # Register API key if provided
    if VNSTOCK_API_KEY:
        try:
            from vnstock import register_user
            register_user(api_key=VNSTOCK_API_KEY)
        except Exception:
            pass

    # Get symbols
    symbols = get_symbols(args.exchange)
    exchange_name = args.exchange or "WATCHLIST"

    print(f"Bot Version 3.0 starting...")
    print(f"Scanning: {exchange_name} ({len(symbols)} symbols)")

    signal_count = 0

    for symbol in symbols:
        df = fetch_data(symbol)
        if df is None: continue

        df = calculate_indicators(df)

        if not is_investable(df):
            continue

        score, reasons = check_signals(df)

        if score >= MIN_SCORE:
            print(f"FOUND: {symbol} (Score: {score})")
            send_telegram_alert(symbol, score, reasons, df.iloc[-1]['close'], df)
            signal_count += 1
        else:
            print(f"... {symbol}: {score} pts (skip)")

    if signal_count == 0:
        print("No buy signals found.")

if __name__ == "__main__":
    main()
```

### Step 1.5: Fix `main.yml` (line 32 indentation)

The `env:` block must be indented under `- name:`, not at same level:

```yaml
name: Bot Chung Khoan Auto

on:
  schedule:
    - cron: '*/15 2-8 * * 1-5'
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Run Trading Bot
      env:
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        VNSTOCK_API_KEY: ${{ secrets.VNSTOCK_API_KEY }}
        VNSTOCK_DATA_SOURCE: VCI
      run: python -m src.bot
```

### Step 1.6: Fix `hnx_scan.yml` (missing setup steps)

```yaml
name: Scan HNX
on:
  schedule:
    - cron: '30 2 * * 1-5'
  workflow_dispatch:

jobs:
  run-hnx:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - name: Scan HNX
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          VNSTOCK_API_KEY: ${{ secrets.VNSTOCK_API_KEY }}
          VNSTOCK_DATA_SOURCE: VCI
        run: python -m src.bot --exchange HNX
```

### Step 1.7: Delete `upcom_scan.yml`

Per validation decision: Skip UPCOM (800+ symbols, low liquidity). Delete file:
```bash
rm .github/workflows/upcom_scan.yml
```

## Todo List

- [ ] Create `src/__init__.py`
- [ ] Update `src/config.py` with DATA_SOURCE, VNSTOCK_API_KEY
- [ ] Migrate `src/data_fetcher.py` to vnstock 3.x Quote class
- [ ] Add argparse to `src/bot.py`
- [ ] Fix `main.yml` indentation at line 32
- [ ] Fix `hnx_scan.yml` missing setup steps
- [ ] Delete `upcom_scan.yml` (skip UPCOM per validation)
- [ ] Test bot with `python -m src.bot`
- [ ] Test bot with `python -m src.bot --exchange HOSE`

## Success Criteria

- [ ] `python -m src.bot` runs without import errors
- [ ] `python -m src.bot --exchange HOSE` fetches HOSE symbols
- [ ] No vnstock deprecation warnings in output
- [ ] All YAML files pass syntax validation

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| vnstock 3.x column names differ | Data processing fails | Normalize column names to lowercase |
| Listing API returns empty | No symbols to scan | Fallback to WATCHLIST |
| API key missing | Lower rate limit | Graceful degradation, warn user |

## Security Considerations

- API key stored in GitHub Secrets, never hardcoded
- No credentials in code or logs
- Environment variables for all sensitive config
