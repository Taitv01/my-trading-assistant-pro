import pandas as pd
from vnstock import Quote
from datetime import datetime, timedelta
import time

# Rate Limit Settings
MAX_RETRIES = 3
INITIAL_BACKOFF = 25  # Chờ 25 giây khi gặp rate limit (API yêu cầu 22s)

def fetch_data(symbol, days=365):
    """Lấy dữ liệu lịch sử 1 năm qua - Có retry khi gặp rate limit"""
    for attempt in range(MAX_RETRIES):
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            # Lấy dữ liệu daily using new API (default source='VCI')
            quote = Quote(symbol=symbol, source='VCI')
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
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Kiểm tra nếu là lỗi rate limit
            if 'rate limit' in error_str or 'too many requests' in error_str or '429' in error_str:
                backoff_time = INITIAL_BACKOFF * (2 ** attempt)  # Exponential backoff
                print(f"⚠️ Rate limit hit for {symbol}. Retry {attempt + 1}/{MAX_RETRIES} after {backoff_time}s...")
                time.sleep(backoff_time)
            else:
                # Lỗi khác - không retry
                print(f"Error fetching data for {symbol}: {e}")
                return None
                
    # Hết số lần retry
    print(f"❌ Failed to fetch {symbol} after {MAX_RETRIES} retries (rate limited)")
    return None
