import pandas as pd
import numpy as np

# ============================================================
# CÁC HÀM TÍNH TOÁN CHỈ BÁO
# ============================================================

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI (Relative Strength Index)"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss))
    return df

def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """MACD (12, 26, 9)"""
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def calculate_bollinger(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Bollinger Bands (20, 2)"""
    df['SMA20'] = df['close'].rolling(window=period).mean()
    df['StdDev'] = df['close'].rolling(window=period).std()
    df['Upper'] = df['SMA20'] + (df['StdDev'] * 2)
    df['Lower'] = df['SMA20'] - (df['StdDev'] * 2)
    return df

def calculate_volume_ma(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Volume Moving Average"""
    df['VolMA20'] = df['volume'].rolling(window=period).mean()
    return df

def calculate_stochastic(df: pd.DataFrame, period: int = 14, 
                         smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator (%K, %D)"""
    low_n = df['low'].rolling(window=period).min()
    high_n = df['high'].rolling(window=period).max()
    
    df['%K_raw'] = 100 * (df['close'] - low_n) / (high_n - low_n)
    df['%K'] = df['%K_raw'].rolling(window=smooth_k).mean()
    df['%D'] = df['%K'].rolling(window=smooth_d).mean()
    
    # Cleanup temp columns
    df.drop(columns=['%K_raw'], inplace=True, errors='ignore')
    return df

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """ADX (Average Directional Index)"""
    # True Range
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift()).abs()
    tr3 = (df['low'] - df['close'].shift()).abs()
    df['TR'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Directional Movement
    up_move = df['high'].diff()
    down_move = -df['low'].diff()
    
    df['+DM'] = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    df['-DM'] = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smoothed values
    df['TR_smooth'] = df['TR'].rolling(window=period).sum()
    df['+DM_smooth'] = df['+DM'].rolling(window=period).sum()
    df['-DM_smooth'] = df['-DM'].rolling(window=period).sum()
    
    # DI values
    df['+DI'] = 100 * (df['+DM_smooth'] / df['TR_smooth'])
    df['-DI'] = 100 * (df['-DM_smooth'] / df['TR_smooth'])
    
    # DX and ADX
    di_sum = df['+DI'] + df['-DI']
    di_diff = (df['+DI'] - df['-DI']).abs()
    df['DX'] = 100 * (di_diff / di_sum.replace(0, np.nan))
    df['ADX'] = df['DX'].rolling(window=period).mean()
    
    # Cleanup temp columns
    temp_cols = ['TR', '+DM', '-DM', 'TR_smooth', '+DM_smooth', '-DM_smooth', 'DX']
    df.drop(columns=temp_cols, inplace=True, errors='ignore')
    return df

def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
    """OBV (On-Balance Volume)"""
    df['OBV'] = (df['volume'] * np.sign(df['close'].diff())).fillna(0).cumsum()
    return df

def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """MFI (Money Flow Index)"""
    # Typical Price
    df['TP'] = (df['high'] + df['low'] + df['close']) / 3
    df['MF'] = df['TP'] * df['volume']
    
    # Positive and Negative Money Flow
    tp_diff = df['TP'].diff()
    df['PMF'] = df['MF'].where(tp_diff > 0, 0).rolling(window=period).sum()
    df['NMF'] = df['MF'].where(tp_diff < 0, 0).abs().rolling(window=period).sum()
    
    # MFI calculation
    mf_ratio = df['PMF'] / df['NMF'].replace(0, np.nan)
    df['MFI'] = 100 - (100 / (1 + mf_ratio))
    
    # Cleanup temp columns
    df.drop(columns=['TP', 'MF', 'PMF', 'NMF'], inplace=True, errors='ignore')
    return df

# ============================================================
# MAIN FUNCTIONS
# ============================================================

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Tính toán tất cả các chỉ báo kỹ thuật"""
    if df is None or df.empty:
        return None

    # Các chỉ báo cơ bản v1.0
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger(df)
    df = calculate_volume_ma(df)

    # Các chỉ báo nâng cao v1.1 (Phase 3)
    df = calculate_stochastic(df)
    df = calculate_adx(df)
    df = calculate_obv(df)
    df = calculate_mfi(df)

    return df

def check_signals(df: pd.DataFrame) -> tuple:
    """
    Hệ thống chấm điểm tín hiệu nâng cao
    Returns: (score, reasons)
    """
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []

    # ---- NHÓM 1: PRICE & VOLUME (Cơ bản) ----
    
    # Signal 1: Volume spike (Vol > 1.3x MA20)
    if last['VolMA20'] > 0:
        vol_ratio = last['volume'] / last['VolMA20']
        if vol_ratio > 1.3:
            score += 2
            reasons.append(f"Vol đột biến (x{vol_ratio:.1f})")

    # Signal 2: Giá vượt MA20 (Bollinger Middle)
    if last['close'] > last['SMA20'] and prev['close'] <= prev['SMA20']:
        score += 2
        reasons.append("Giá cắt lên MA20")

    # ---- NHÓM 2: TREND & MOMENTUM (Cơ bản) ----

    # Signal 3: MACD Golden Cross
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 3
        reasons.append("MACD Golden Cross")

    # Signal 4: RSI vùng đẹp (40-60 & đang tăng)
    if 40 < last['RSI'] < 60 and last['RSI'] > prev['RSI']:
        score += 1
        reasons.append("RSI xu hướng tăng")

    # ---- NHÓM 3: NÂNG CAO (Mới - Phase 3) ----

    # Signal 5: Stochastic Bullish Cross (từ vùng quá bán < 20 lên)
    # Lỏng tay hơn chút: %K cắt %D và %D < 50
    if last['%K'] > last['%D'] and prev['%K'] <= prev['%D'] and last['%D'] < 50:
        score += 2
        reasons.append("Stoch cắt lên (%D<50)")

    # Signal 6: ADX mạnh (> 25) xác nhận xu hướng
    if last['ADX'] > 25:
        score += 1
        reasons.append(f"ADX mạnh ({last['ADX']:.0f})")

    # Signal 7: OBV Tích lũy (OBV tăng trong 5 phiên trong khi giá đi ngang/tăng)
    # Đơn giản hóa: OBV hiện tại > OBV 5 phiên trước
    if len(df) > 5:
        obv_change = last['OBV'] - df['OBV'].iloc[-5]
        if obv_change > 0 and last['close'] >= df['close'].iloc[-5]:
            score += 1
            reasons.append("OBV tích lũy")

    # Signal 8: MFI phục hồi từ vùng quá bán (< 30)
    if prev['MFI'] < 30 and last['MFI'] > prev['MFI']:
        score += 1
        reasons.append("MFI thoát đáy")

    return score, reasons
