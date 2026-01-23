import pandas as pd
from vnstock import Quote
from datetime import datetime, timedelta

def fetch_data(symbol, days=365):
    """Lấy dữ liệu lịch sử 1 năm qua"""
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
        print(f"Error fetching data for {symbol}: {e}")
        return None
