# Phase 4: Production Ready

## Overview

| Attribute | Value |
|-----------|-------|
| Priority | P2 |
| Status | pending |
| Effort | 1h |
| Dependencies | Phase 3 |

Add rate limiting, error handling, retry logic, and update requirements.txt.

## Context Links

- [vnstock 3.x API Research](./research/researcher-01-vnstock-api.md) - Rate limit info
- [Brainstorm Report](../reports/brainstorm-260125-2007-vnstock-integration-upgrade.md)

## Key Insights

1. **Rate Limits**: Guest 20/min, Community 60/min, Sponsor 180+/min
2. **Retry Strategy**: Exponential backoff on transient failures
3. **UPCOM Challenge**: 800+ symbols requires ~15 min at safe rate
4. **Pin Versions**: Prevent breaking changes from dependency updates

## Related Code Files

### Files to Create
- `src/utils/__init__.py` - Package marker
- `src/utils/rate_limiter.py` - Rate limiting helper

### Files to Modify
- `src/data/fetcher.py` - Add retry logic
- `requirements.txt` - Pin versions
- `README.md` - Add API key guide

## Implementation Steps

### Step 4.1: Create `src/utils/__init__.py`

```python
# src/utils/__init__.py
from .rate_limiter import RateLimiter

__all__ = ['RateLimiter']
```

### Step 4.2: Create `src/utils/rate_limiter.py`

```python
"""Rate limiting utility for API requests"""
import time
from collections import deque
from datetime import datetime

class RateLimiter:
    """
    Token bucket rate limiter.

    Usage:
        limiter = RateLimiter(requests_per_minute=60)
        limiter.wait()  # Blocks if rate limit would be exceeded
        # make request
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests allowed per minute
        """
        self.rpm = requests_per_minute
        self.window = 60.0  # seconds
        self.timestamps = deque()

    def wait(self):
        """
        Wait if necessary to respect rate limit.
        Call before each API request.
        """
        now = time.time()

        # Remove timestamps older than window
        while self.timestamps and self.timestamps[0] < now - self.window:
            self.timestamps.popleft()

        # If at limit, wait until oldest timestamp expires
        if len(self.timestamps) >= self.rpm:
            sleep_time = self.timestamps[0] - (now - self.window) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.timestamps.append(time.time())

    @property
    def current_rate(self) -> int:
        """Current requests in window"""
        now = time.time()
        while self.timestamps and self.timestamps[0] < now - self.window:
            self.timestamps.popleft()
        return len(self.timestamps)


def create_limiter(tier: str = 'guest') -> RateLimiter:
    """
    Factory to create rate limiter based on tier.

    Args:
        tier: 'guest' (20/min), 'community' (60/min), 'sponsor' (180/min)
    """
    rates = {
        'guest': 20,
        'community': 60,
        'sponsor': 180
    }
    return RateLimiter(requests_per_minute=rates.get(tier, 20))
```

### Step 4.3: Update `src/data/fetcher.py` with retry logic

```python
"""VnstockClient - Wrapper for vnstock 3.x API with retry logic"""
import pandas as pd
import time
from datetime import datetime, timedelta
from vnstock import Quote
from ..config import DATA_SOURCE
from ..utils import RateLimiter

# Default retry settings
MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds
BACKOFF_MAX = 10  # seconds

class VnstockClient:
    """
    Unified client for vnstock 3.x API with rate limiting and retry.
    """

    def __init__(self, source: str = None, rate_limit: int = 55):
        """
        Initialize client.

        Args:
            source: Data source ('VCI', 'TCBS', 'MSN', 'KBS')
            rate_limit: Requests per minute (default 55, safe for Community)
        """
        self.source = source or DATA_SOURCE
        self._quote = None
        self.limiter = RateLimiter(requests_per_minute=rate_limit)

    @property
    def quote(self) -> Quote:
        """Lazy-load Quote instance."""
        if self._quote is None:
            self._quote = Quote(source=self.source)
        return self._quote

    def _retry_request(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass

        Returns:
            Function result or None on failure
        """
        for attempt in range(MAX_RETRIES):
            try:
                self.limiter.wait()  # Respect rate limit
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    backoff = min(BACKOFF_BASE * (2 ** attempt), BACKOFF_MAX)
                    print(f"Retry {attempt + 1}/{MAX_RETRIES} in {backoff}s: {e}")
                    time.sleep(backoff)
                else:
                    print(f"Failed after {MAX_RETRIES} attempts: {e}")
                    return None
        return None

    def get_historical_data(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """
        Fetch OHLCV data with retry logic.

        Args:
            symbol: Stock ticker (e.g., 'VCI')
            days: Number of days to fetch

        Returns:
            DataFrame or None on failure
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        def fetch():
            return self.quote.history(
                symbol=symbol,
                start=start_date,
                end=end_date,
                interval='D'
            )

        df = self._retry_request(fetch)

        if df is None or df.empty or len(df) < 50:
            return None

        # Normalize
        df.columns = df.columns.str.lower()
        numeric_cols = ['close', 'open', 'high', 'low', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        time_col = 'time' if 'time' in df.columns else 'date'
        df['time'] = pd.to_datetime(df[time_col])

        return df

    def get_intraday(self, symbol: str, page_size: int = 100) -> pd.DataFrame:
        """Fetch intraday data with retry."""
        def fetch():
            return self.quote.intraday(symbol=symbol, page_size=page_size)
        return self._retry_request(fetch)
```

### Step 4.4: Update `requirements.txt` with pinned versions

```txt
# Core
pandas>=2.0.0,<3.0.0
numpy>=1.24.0,<2.0.0

# Data
vnstock>=3.4.0,<4.0.0

# Visualization
matplotlib>=3.7.0,<4.0.0

# HTTP
requests>=2.28.0,<3.0.0

# Optional: Telegram bot (if using python-telegram-bot)
# python-telegram-bot>=20.0,<21.0
```

### Step 4.5: Update `README.md` with API key guide

Add section after existing content:

```markdown
## API Key Configuration

### vnstock API Key (Optional but Recommended)

Without API key: 20 requests/minute (Guest tier)
With API key: 60 requests/minute (Community tier)

**Setup:**

1. Go to https://vnstocks.com and login with Google
2. Copy your API key from dashboard
3. Add to GitHub Secrets:
   - Go to repository Settings > Secrets > Actions
   - Click "New repository secret"
   - Name: `VNSTOCK_API_KEY`
   - Value: `vnstock_YOUR_KEY_HERE`

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Yes | Your Telegram chat ID |
| `VNSTOCK_API_KEY` | No | vnstock Community API key |
| `VNSTOCK_DATA_SOURCE` | No | Data source: VCI, TCBS, MSN, KBS (default: VCI) |

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run with WATCHLIST (default)
python -m src.bot

# Run for specific exchange
python -m src.bot --exchange HOSE
python -m src.bot --exchange HNX
python -m src.bot --exchange UPCOM

# Run for stock group
python -m src.bot --group VN30
```

### Rate Limits

| Tier | Requests/min | Symbols/scan | Est. Time |
|------|-------------|--------------|-----------|
| Guest | 20 | 400 (HOSE) | ~20 min |
| Community | 60 | 400 (HOSE) | ~7 min |
| Community | 60 | 800 (UPCOM) | ~15 min |
```

### Step 4.6: Update `src/bot.py` to detect API key tier

```python
# Add after API key registration in main():

# Detect tier for rate limiting
tier = 'community' if VNSTOCK_API_KEY else 'guest'
rate_limit = 55 if tier == 'community' else 18  # Safe margin

client = VnstockClient(rate_limit=rate_limit)
print(f"Rate limit: {rate_limit} req/min ({tier} tier)")
```

## Todo List

- [ ] Create `src/utils/__init__.py`
- [ ] Create `src/utils/rate_limiter.py` with RateLimiter class
- [ ] Update `src/data/fetcher.py` with retry logic
- [ ] Update `requirements.txt` with pinned versions
- [ ] Add API key guide to README.md
- [ ] Update bot.py to detect tier and set rate limit
- [ ] Test with Guest tier (no API key)
- [ ] Test with Community tier (with API key)

## Success Criteria

- [ ] Rate limiter prevents exceeding 60 req/min
- [ ] Retry logic handles transient failures
- [ ] UPCOM scan (800 symbols) completes without timeout
- [ ] README has clear setup instructions
- [ ] `pip install -r requirements.txt` works on fresh environment

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rate limit hit anyway | Temporary block | Add 10% safety margin to rate |
| GitHub Actions timeout | Incomplete scan | Split large exchanges into batches |
| vnstock major version | Breaking changes | Pin to `>=3.4.0,<4.0.0` |

## Security Considerations

- API key stored in GitHub Secrets only
- Never log API key value
- Rate limiter prevents abuse
- No credential in requirements.txt or code

## Next Steps After Phase 4

1. Monitor GitHub Actions runs for 1 week
2. Tune MIN_SCORE threshold based on signal quality
3. Consider adding more exchanges or stock groups
4. Add error notification to Telegram on bot failures
