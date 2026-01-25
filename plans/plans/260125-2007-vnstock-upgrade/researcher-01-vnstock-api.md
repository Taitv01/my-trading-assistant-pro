# vnstock 3.x OOP API - Migration Research Report

**Date:** 2025-01-25 | **Focus:** API Classes & Methods Migration Path

---

## Executive Summary

vnstock 3.x uses unified OOP adapter pattern with **Quote**, **Listing**, **Company**, **Finance** classes replacing legacy functional APIs. Core migration: `stock_historical_data()` → `Quote.history()`.

---

## 1. Core API Classes

### Quote Class
**Location:** `vnstock/api/quote.py` | **Module name:** "quote"

Primary for historical & intraday data:

```python
from vnstock import Quote

# Initialize with symbol
q = Quote(source="vci", symbol="VCI", random_agent=False, show_log=True)

# Historical OHLC data
df = q.history(start="2024-01-01", end="2024-04-18", interval="D")  # Daily

# Alternative: pass symbol to method
df = q.history(symbol="FPT", start="2024-01-01", end="2024-04-18", interval="1W")  # Weekly

# Intraday trades
df = q.intraday(page_size=100, page=1)

# Order book depth
df = q.price_depth()
```

**Key Methods:**
- `history(symbol, start, end, interval)` → pandas DataFrame with OHLC
- `intraday(symbol, page_size, page)` → intraday trade data
- `price_depth(symbol)` → order book data

**Parameters:**
- `source`: "vci", "tcbs", "msn" (default: "kbs")
- `interval`: "1m", "5m", "15m", "30m", "1H", "D", "1W", "1M" (default: "D")
- Backward compat: `resolution` alias for `interval`

### Listing Class
**Location:** `vnstock/api/listing.py`

Get symbols by exchange/industry:

```python
from vnstock import Listing

lst = Listing(source="vci", random_agent=False, show_log=True)

# All symbols
df = lst.all_symbols(to_df=True)

# By exchange (HOSE, HNX, UPCOM)
df = lst.symbols_by_exchange(lang="en")

# By ICB industry
df = lst.symbols_by_industries()

# By predefined groups
df = lst.symbols_by_group(group="VN30")

# Futures & bonds
fu = lst.all_future_indices()
bonds = lst.all_bonds()
```

**Source-independent methods (no source required):**
- `all_indices()` → all standardized market indices
- `indices_by_group(group)` → indices in group

---

## 2. Design Pattern: BaseAdapter + Dynamic Method Delegation

```python
# Architecture:
Quote/Listing → BaseAdapter → Provider (explorer.<source>.quote/listing)
                 ↓
         @dynamic_method decorator detects provider capability
         @retry decorator with exponential backoff
```

**Mechanism:**
1. `Quote(source="vci")` initializes adapter
2. BaseAdapter discovers `vnstock.explorer.vci.quote` module
3. `@dynamic_method` routes calls to provider's matching method
4. `@retry` with `Config.RETRIES=3`, backoff 2-10s on failure

---

## 3. API Key & Authentication

**Location:** `vnstock/core/utils/auth.py` | Exported in `__init__.py`

```python
from vnstock import register_user, change_api_key, check_status

# Register with email & API key
register_user(email="user@example.com", api_key="your-api-key")

# Update API key
change_api_key(api_key="new-api-key")

# Verify status
status = check_status()
```

**Notes:**
- API keys are managed per vnstock session
- Some providers (VCI, KBS) may require registration for higher limits
- Rate limits handled via backoff strategy in Config

---

## 4. Rate Limit & Retry Handling

```python
# config.py settings (tunable):
REQUEST_TIMEOUT = 30           # seconds
RETRIES = 3                     # attempts
BACKOFF_MULTIPLIER = 1.0       # tenacity strategy
BACKOFF_MIN = 2                # seconds
BACKOFF_MAX = 10               # seconds
```

**Retry Mechanism:** Exponential backoff (2s → 4s → 10s) on transient failures.

---

## 5. Exported Classes & Constants

```python
from vnstock import (
    Quote, Listing, Company, Finance, Trading, Screener, Fund,
    INDICES_INFO, INDICES_MAP, SECTOR_IDS, EXCHANGES,
    register_user, change_api_key, check_status
)
```

---

## 6. Migration Steps (High-Level)

| Old (v1/v2) | New (v3) | Status |
|---|---|---|
| `stock_historical_data("VCI", "2024-01-01", "2024-12-31")` | `Quote(symbol="VCI").history(start="2024-01-01", end="2024-12-31")` | Direct |
| `get_quote_intraday("VCI")` | `Quote(symbol="VCI").intraday()` | Direct |
| `get_all_listed_symbols()` | `Listing(source="vci").all_symbols()` | Via source |
| `get_symbols_by_exchange()` | `Listing(source="vci").symbols_by_exchange()` | Via source |

---

## 7. Key Insights

1. **Source Required for Symbols:** `Listing` & provider methods need `source` parameter (vci/tcbs/msn/kbs)
2. **Quote Source Default:** Quote defaults to "kbs", but "vci" recommended for data quality
3. **Lazy Loading:** Explorer modules loaded on first use to avoid circular imports
4. **Backward Compat:** `resolution` alias still works in `history()`
5. **pandas DataFrame:** All methods return pandas DataFrames by default

---

## 8. Code Examples for Migration

### Migration Example 1: Historical Data
```python
# OLD
df = stock_historical_data("VCI", "2024-01-01", "2024-12-31")

# NEW
q = Quote(symbol="VCI", source="vci")
df = q.history(start="2024-01-01", end="2024-12-31")
```

### Migration Example 2: Multiple Symbols (Loop)
```python
# OLD
for symbol in ["VCI", "FPT", "TCB"]:
    df = stock_historical_data(symbol, "2024-01-01", "2024-12-31")

# NEW
for symbol in ["VCI", "FPT", "TCB"]:
    q = Quote(source="vci")  # Reuse instance
    df = q.history(symbol=symbol, start="2024-01-01", end="2024-12-31")
```

---

## Unresolved Questions

None. API structure fully understood.
