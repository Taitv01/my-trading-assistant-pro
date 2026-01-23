import pandas as pd
from vnstock import *
from datetime import datetime, timedelta

def get_vietnam_time():
    return datetime.utcnow() + timedelta(hours=7)

def get_market_data(symbol, days=100):
    """Lấy dữ liệu và tính toán chỉ báo"""
    try:
        today_str = get_vietnam_time().strftime('%Y-%m-%d')
        # Lấy 100 ngày để tính MA50, Bollinger Bands chuẩn
        df = stock_historical_data(symbol, "2025-06-01", today_str, "1D", "stock")
        
        if df is None or len(df) < 60: return None

        # --- 1. TÍNH CHỈ BÁO KỸ THUẬT (Signals) ---
        
        # RSI (14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        # MACD (12, 26, 9)
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands (20, 2)
        df['SMA20'] = df['close'].rolling(window=20).mean()
        df['StdDev'] = df['close'].rolling(window=20).std()
        df['Upper'] = df['SMA20'] + (df['StdDev'] * 2)
        df['Lower'] = df['SMA20'] - (df['StdDev'] * 2)
        
        # MA50 (Xu hướng trung hạn)
        df['MA50'] = df['close'].rolling(window=50).mean()

        return df
    except Exception as e:
        print(f"Lỗi data {symbol}: {e}")
        return None

def check_conditions(df):
    """Bộ lọc rủi ro và tìm điểm mua (Filters)"""
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    signals = []
    score = 0 # Hệ thống chấm điểm (Ranking)
    
    # 1. Volume Breakout (> 1.3 TB20)
    avg_vol_20 = df.iloc[-22:-2]['volume'].mean()
    if avg_vol_20 == 0: return False, "", 0
    vol_ratio = last['volume'] / avg_vol_20
    
    # 2. Giá tăng
    change_pct = (last['close'] - prev['close']) / prev['close'] * 100
    
    # --- CÁC CHIẾN LƯỢC (STRATEGIES) ---
    
    # A. Chiến lược Dòng tiền (Cũ nhưng hiệu quả)
    if vol_ratio > 1.3 and change_pct > 0.5:
        score += 1
        signals.append(f"Tiền vào x{vol_ratio:.1f}")

    # B. Chiến lược MACD (Mới)
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 2
        signals.append("MACD cắt lên (Golden Cross)")
        
    # C. Chiến lược Bollinger Bands Squeeze (Bắt đáy/Hồi phục)
    # Giá chạm dải dưới và bật lên
    if prev['close'] < prev['Lower'] and last['close'] > last['Lower']:
        score += 1.5
        signals.append("Chạm Band dưới bật lên")

    # D. Xu hướng (MA50)
    if last['close'] > last['MA50']:
        score += 0.5 # Cộng điểm nếu đang ở trên MA50 (uptrend)
    
    # KẾT LUẬN: Chỉ báo mua khi có điểm số >= 2 (Tránh nhiễu)
    is_buy = score >= 2 and last['RSI'] < 75
    
    return is_buy, ", ".join(signals), score, change_pct
