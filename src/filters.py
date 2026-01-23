from .config import MIN_VOLUME_VALUE, MIN_PRICE

def is_investable(df):
    """Kiểm tra điều kiện cơ bản (Thanh khoản & Giá)"""
    if df is None or df.empty: return False

    last = df.iloc[-1]

    # 1. Lọc giá quá thấp
    if last['close'] < MIN_PRICE:
        return False

    # 2. Lọc thanh khoản thấp
    trading_value = last['close'] * last['volume']
    if trading_value < MIN_VOLUME_VALUE:
        return False

    return True
