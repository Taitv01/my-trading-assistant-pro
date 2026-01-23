import pandas as pd
import numpy as np

def calculate_indicators(df):
    """Tính toán các chỉ báo kỹ thuật"""
    if df is None: return None

    # 1. RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))

    # 2. MACD (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # 3. Bollinger Bands (20, 2)
    df['SMA20'] = df['close'].rolling(window=20).mean()
    df['StdDev'] = df['close'].rolling(window=20).std()
    df['Upper'] = df['SMA20'] + (df['StdDev'] * 2)
    df['Lower'] = df['SMA20'] - (df['StdDev'] * 2)

    # 4. Volume MA (20)
    df['VolMA20'] = df['volume'].rolling(window=20).mean()

    return df

def check_signals(df):
    """Hệ thống chấm điểm tín hiệu"""
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []

    # Signal 1: Dòng tiền vào mạnh (Vol > 1.3 TB20)
    if last['VolMA20'] > 0:
        vol_ratio = last['volume'] / last['VolMA20']
        if vol_ratio > 1.3:
            score += 2
            reasons.append(f"Vol Spike (x{vol_ratio:.1f})")

    # Signal 2: MACD Cắt lên (Đảo chiều tăng)
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 3
        reasons.append("MACD Golden Cross")

    # Signal 3: Giá vượt MA20 (Bollinger Middle)
    if last['close'] > last['SMA20'] and prev['close'] <= prev['SMA20']:
        score += 2
        reasons.append("Price Cross MA20")

    # Signal 4: RSI vùng đẹp (Tăng từ vùng thấp)
    if 40 < last['RSI'] < 60 and last['RSI'] > prev['RSI']:
        score += 1

    return score, reasons
