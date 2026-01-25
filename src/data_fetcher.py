import pandas as pd
from vnstock import Quote
from datetime import datetime, timedelta
import time
from .config import DATA_SOURCE, VNSTOCK_API_KEY
from .utils import RateLimiter

# Rate Limit Settings
MAX_RETRIES = 3
INITIAL_BACKOFF = 10 

# Initialize Rate Limiter
# Guest: 20 req/min | Community: 60 req/min
_rpm = 55 if VNSTOCK_API_KEY else 18  # Safe margin
_limiter = RateLimiter(requests_per_minute=_rpm)

def fetch_data(symbol, days=365):
    """Lấy dữ liệu lịch sử - Có rate limit & retry"""
    for attempt in range(MAX_RETRIES):
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            # Wrapper for Rate Limiter
            _limiter.wait()

            # Lấy dữ liệu daily using new API
            quote = Quote(symbol=symbol, source=DATA_SOURCE)
            df = quote.history(start=start_date, end=end_date, interval='1D')

            if df is None or df.empty or len(df) < 50:
                return None

            # Chuẩn hóa dữ liệu sang số
            cols = ['close', 'open', 'high', 'low', 'volume']
            for col in cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            # Fix: vnstock returns price in kVND (e.g. 26.75), convert to VND
            price_cols = ['close', 'open', 'high', 'low']
            for col in price_cols:
                df[col] = df[col] * 1000

            df['time'] = pd.to_datetime(df['time'])

            return df
            
        except ValueError as e:
            # ValueError: Invalid data from API - skip immediately, no retry
            # This happens when vnstock returns malformed data
            return None
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for RetryError with ValueError inside - skip immediately
            if 'retryerror' in error_str and 'valueerror' in error_str:
                # RetryError wrapping ValueError - skip, no retry
                return None
            
            # Check for other non-recoverable errors - skip immediately
            if 'valueerror' in error_str or 'keyerror' in error_str or 'typeerror' in error_str:
                return None
            
            # Kiểm tra nếu là lỗi rate limit - có thể retry
            if 'rate limit' in error_str or 'too many requests' in error_str or '429' in error_str:
                backoff_time = INITIAL_BACKOFF * (2 ** attempt)  # Exponential backoff
                print(f"⚠️ Rate limit hit for {symbol}. Retry {attempt + 1}/{MAX_RETRIES} after {backoff_time}s...")
                time.sleep(backoff_time)
            else:
                # Lỗi khác không xác định - skip
                print(f"Error fetching data for {symbol}: {type(e).__name__}")
                return None
                
    # Hết số lần retry
    print(f"❌ Failed to fetch {symbol} after {MAX_RETRIES} retries (rate limited)")
    return None
