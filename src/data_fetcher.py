import pandas as pd
from vnstock import stock_historical_data
from datetime import datetime, timedelta

def fetch_data(symbol, days=365):
    """Lấy dữ liệu lịch sử 1 năm qua"""
    try:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Lấy dữ liệu daily
        df = stock_historical_data(symbol, start_date, end_date, "1D", "stock")

        if df is None or df.empty or len(df) < 50:
            return None

        # Chuẩn hóa dữ liệu sang số
        cols = ['close', 'open', 'high', 'low', 'volume']
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df['time'] = pd.to_datetime(df['time'])

        return df
    except Exception as e:
        print(f"⚠️ Lỗi data {symbol}: {e}")
        return None
