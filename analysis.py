# analysis.py
import pandas as pd
import logging
from vnstock import stock_historical_data
from config import get_start_date, get_today_date

# Cấu hình logging để biết lỗi ở đâu
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_market_data(symbol):
    """Lấy dữ liệu an toàn với Error Handling"""
    start_date = get_start_date(days_back=200) # Lấy 200 nến để tính MA50/200 chuẩn
    today = get_today_date()
    
    try:
        df = stock_historical_data(symbol, start_date, today, "1D", "stock")
        if df is None or df.empty or len(df) < 50:
            logger.warning(f"⚠️ {symbol}: Dữ liệu không đủ hoặc lỗi API.")
            return None
        return df
    except Exception as e:
        logger.error(f"❌ Lỗi lấy data {symbol}: {str(e)}")
        return None

def calculate_indicators(df):
    """Tính toán chỉ báo kỹ thuật"""
    try:
        # 1. RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))

        # 2. MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Hist'] = df['MACD'] - df['Signal']

        # 3. Moving Average & Bollinger Bands
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA50'] = df['close'].rolling(window=50).mean()
        std_dev = df['close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (std_dev * 2)
        df['Lower'] = df['MA20'] - (std_dev * 2)

        return df
    except Exception as e:
        logger.error(f"Lỗi tính chỉ báo: {e}")
        return df

def score_stock(df):
    """Hệ thống chấm điểm (Scoring System) để lọc nhiễu"""
    if df is None: return 0, [], 0
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    reasons = []

    # 1. Volume Breakout (Quan trọng nhất) - 2 Điểm
    # Vol phiên nay > 1.3 lần TB 20 phiên
    avg_vol_20 = df.iloc[-22:-2]['volume'].mean()
    if avg_vol_20 > 0:
        vol_ratio = last['volume'] / avg_vol_20
        if vol_ratio >= 1.3:
            score += 2.0
            reasons.append(f"Vol nổ x{vol_ratio:.1f}")
    
    # 2. Xu hướng giá (Price Action) - 1 Điểm
    # Giá cắt lên MA20 hoặc giá nằm trên MA50
    if last['close'] > last['MA20'] and prev['close'] <= prev['MA20']:
        score += 1.0
        reasons.append("Cắt lên MA20")
    elif last['close'] > last['MA50']:
        score += 0.5 # Điểm cộng xu hướng dài hạn

    # 3. MACD (Đảo chiều) - 1.5 Điểm
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 1.5
        reasons.append("MACD Golden Cross")
    elif last['MACD'] > last['Signal'] and last['Hist'] > prev['Hist']:
         score += 0.5 # MACD đang mạnh lên

    # 4. RSI (Lọc quá mua) - Trừ điểm nếu rủi ro
    if last['RSI'] > 70:
        score -= 2.0 # Quá mua -> Trừ điểm nặng để tránh đu đỉnh
        reasons.append("RSI Quá mua (Cẩn thận)")
    elif 40 < last['RSI'] < 60:
        score += 0.5 # Vùng RSI an toàn để tăng

    change_pct = (last['close'] - prev['close']) / prev['close'] * 100
    
    return score, reasons, change_pct
