import pandas as pd
import numpy as np
import time
import logging
from vnstock import stock_historical_data
# SỬA LỖI Ở DÒNG DƯỚI: Import đúng hàm get_date_range từ config mới
from config import get_date_range, MIN_PRICE, MIN_VOL_VALUE, MIN_DAYS

# Setup logging
logging.basicConfig(filename='bot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data_safe(symbol, retries=3):
    """Lấy dữ liệu với cơ chế Retry"""
    # SỬA LỖI: Gọi hàm mới trả về 2 giá trị (start, end)
    start_date, end_date = get_date_range()
    
    for attempt in range(retries):
        try:
            # Lấy dữ liệu daily
            df = stock_historical_data(symbol, start_date, end_date, "1D", "stock")
            if df is not None and not df.empty and len(df) >= MIN_DAYS:
                # Ép kiểu dữ liệu chuẩn
                df['close'] = pd.to_numeric(df['close'])
                df['volume'] = pd.to_numeric(df['volume'])
                df['high'] = pd.to_numeric(df['high'])
                df['low'] = pd.to_numeric(df['low'])
                return df
        except Exception as e:
            logging.warning(f"⚠️ {symbol}: Lỗi lần {attempt+1}/{retries} - {str(e)}")
            time.sleep(2) # Nghỉ 2s trước khi thử lại
            
    logging.error(f"❌ {symbol}: Fetch thất bại sau {retries} lần.")
    return None

def check_quality(df, symbol):
    """Lọc rác: Chỉ giữ mã thanh khoản tốt & giá trị thực"""
    last = df.iloc[-1]
    avg_vol_20 = df['volume'].rolling(window=20).mean().iloc[-1]
    avg_val_20 = avg_vol_20 * last['close'] # Giá trị giao dịch trung bình
    
    # 1. Lọc giá
    if last['close'] < MIN_PRICE:
        return False, f"Giá thấp ({last['close']})"
    
    # 2. Lọc thanh khoản
    if avg_val_20 < MIN_VOL_VALUE:
        return False, f"Thanh khoản thấp ({avg_val_20/1e6:.1f} tr)"
        
    return True, "OK"

def calculate_indicators(df):
    """Tính toán chỉ báo kỹ thuật (Vectorized)"""
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
    df['Hist'] = df['MACD'] - df['Signal']

    # Moving Averages
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()
    df['MA200'] = df['close'].rolling(window=200).mean()
    
    # Volume MA
    df['VolMA20'] = df['volume'].rolling(window=20).mean()
    
    return df

def score_stock(df):
    """Hệ thống chấm điểm (Scoring System)"""
    if df is None: return 0, {}, 0
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    breakdown = [] # Lưu lý do cộng điểm
    
    # 1. PRICE ACTION (Max 4đ)
    change_pct = (last['close'] - prev['close']) / prev['close'] * 100
    if change_pct >= 3.0:
        score += 4
        breakdown.append("🔥 Giá tăng mạnh >3%")
    elif change_pct >= 1.0:
        score += 2
        breakdown.append("✅ Giá tăng >1%")
    elif change_pct > 0:
        score += 1
        
    # 2. VOLUME BREAKOUT (Max 5đ)
    vol_ratio = last['volume'] / last['VolMA20'] if last['VolMA20'] > 0 else 0
    if vol_ratio >= 2.0:
        score += 5
        breakdown.append(f"🔥 Vol nổ x{vol_ratio:.1f}")
    elif vol_ratio >= 1.5:
        score += 3
        breakdown.append(f"⚡ Vol tăng x{vol_ratio:.1f}")
    elif vol_ratio >= 1.3:
        score += 1
        
    # 3. RSI TÍCH LŨY/ĐẢO CHIỀU (Max 3đ)
    if 30 <= last['RSI'] <= 50:
        score += 3
        breakdown.append(f"💎 RSI tích lũy ({last['RSI']:.0f})")
    elif 50 < last['RSI'] <= 65:
        score += 2
        breakdown.append("RSI xu hướng tăng")
    elif last['RSI'] > 75:
        score -= 2
        breakdown.append("⚠️ RSI Quá mua")

    # 4. MACD GOLDEN CROSS (Max 6đ)
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 6
        breakdown.append("🌟 MACD Cắt lên")
    elif last['MACD'] > last['Signal'] and last['Hist'] > prev['Hist']:
        score += 2 
        
    # 5. TREND ALIGNMENT (Max 2đ)
    if last['close'] > last['MA50'] and last['MA50'] > last['MA200']:
        score += 2
        breakdown.append("📈 Uptrend dài hạn")

    return score, breakdown, change_pct
