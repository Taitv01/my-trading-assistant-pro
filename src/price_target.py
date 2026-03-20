"""
Price Target & Stop Loss Module
Tính mục tiêu giá và mức cắt lỗ cho mỗi tín hiệu
"""
import numpy as np


def calculate_support_resistance(df, window=20):
    """
    Tìm mức hỗ trợ và kháng cự gần nhất dựa trên pivot points.
    
    Args:
        df: DataFrame with OHLCV data
        window: Số phiên để tìm pivot
        
    Returns:
        dict with 'support' and 'resistance' levels
    """
    highs = df['high'].tail(window * 3).values
    lows = df['low'].tail(window * 3).values
    close = df['close'].iloc[-1]
    
    # Tìm các đỉnh (resistance) - local maxima
    resistances = []
    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            resistances.append(highs[i])
    
    # Tìm các đáy (support) - local minima
    supports = []
    for i in range(1, len(lows) - 1):
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            supports.append(lows[i])
    
    # Lấy kháng cự gần nhất (trên giá hiện tại)
    resistance = None
    valid_resistances = sorted([r for r in resistances if r > close])
    if valid_resistances:
        resistance = valid_resistances[0]  # Kháng cự gần nhất
    
    # Lấy hỗ trợ gần nhất (dưới giá hiện tại)
    support = None
    valid_supports = sorted([s for s in supports if s < close], reverse=True)
    if valid_supports:
        support = valid_supports[0]  # Hỗ trợ gần nhất
    
    return {
        'support': support,
        'resistance': resistance,
        'all_supports': sorted(valid_supports[:3]) if valid_supports else [],
        'all_resistances': sorted(valid_resistances[:3]) if valid_resistances else [],
    }


def calculate_price_targets(df, signal_type='buy'):
    """
    Tính mục tiêu giá và mức cắt lỗ.
    
    Args:
        df: DataFrame đã tính indicators (có Bollinger, SMA20, etc.)
        signal_type: 'buy' hoặc 'sell'
        
    Returns:
        dict with target_price, stop_loss, risk_reward_ratio
    """
    last = df.iloc[-1]
    close = last['close']
    
    # Lấy support/resistance
    sr = calculate_support_resistance(df)
    
    if signal_type == 'buy':
        # === MỤC TIÊU GIÁ (Target) ===
        # Ưu tiên: Kháng cự gần nhất > Bollinger Upper > +10%
        if sr['resistance'] and sr['resistance'] > close * 1.02:
            target = sr['resistance']
            target_method = "Kháng cự"
        elif 'Upper' in df.columns and last['Upper'] > close * 1.02:
            target = last['Upper']
            target_method = "Bollinger Upper"
        else:
            target = close * 1.10  # +10% default
            target_method = "+10%"
        
        # === CẮT LỖ (Stop Loss) ===
        # Ưu tiên: Hỗ trợ gần nhất > Bollinger Lower > -5%
        if sr['support'] and sr['support'] > close * 0.90:
            stop = sr['support']
            stop_method = "Hỗ trợ"
        elif 'Lower' in df.columns and last['Lower'] > close * 0.90:
            stop = last['Lower']
            stop_method = "Bollinger Lower"
        else:
            stop = close * 0.95  # -5% default
            stop_method = "-5%"
            
    else:  # sell signal
        # Ngược lại: Target xuống, Stop Loss lên
        if sr['support'] and sr['support'] < close * 0.98:
            target = sr['support']
            target_method = "Hỗ trợ"
        elif 'Lower' in df.columns and last['Lower'] < close * 0.98:
            target = last['Lower']
            target_method = "Bollinger Lower"
        else:
            target = close * 0.90  # -10% default
            target_method = "-10%"
        
        if sr['resistance'] and sr['resistance'] < close * 1.10:
            stop = sr['resistance']
            stop_method = "Kháng cự"
        elif 'Upper' in df.columns and last['Upper'] < close * 1.10:
            stop = last['Upper']
            stop_method = "Bollinger Upper"
        else:
            stop = close * 1.05  # +5% default
            stop_method = "+5%"
    
    # === RISK/REWARD RATIO ===
    if signal_type == 'buy':
        potential_gain = target - close
        potential_loss = close - stop
    else:
        potential_gain = close - target
        potential_loss = stop - close
    
    if potential_loss > 0:
        rr_ratio = potential_gain / potential_loss
    else:
        rr_ratio = 0.0
    
    return {
        'current_price': close,
        'target_price': target,
        'target_method': target_method,
        'target_pct': ((target - close) / close) * 100,
        'stop_loss': stop,
        'stop_method': stop_method,
        'stop_pct': ((stop - close) / close) * 100,
        'risk_reward': rr_ratio,
        'support': sr['support'],
        'resistance': sr['resistance'],
    }


def format_price_target(pt, signal_type='buy'):
    """
    Format price target info cho tin nhắn Telegram.
    
    Args:
        pt: dict from calculate_price_targets()
        signal_type: 'buy' or 'sell'
        
    Returns:
        Formatted string
    """
    if signal_type == 'buy':
        lines = [
            f"🎯 Target: {pt['target_price']:,.0f} ({pt['target_pct']:+.1f}%) [{pt['target_method']}]",
            f"🛑 Stop Loss: {pt['stop_loss']:,.0f} ({pt['stop_pct']:+.1f}%) [{pt['stop_method']}]",
            f"⚖️ R/R: 1:{pt['risk_reward']:.1f}",
        ]
    else:
        lines = [
            f"🎯 Target: {pt['target_price']:,.0f} ({pt['target_pct']:+.1f}%) [{pt['target_method']}]",
            f"🛑 Stop Loss: {pt['stop_loss']:,.0f} ({pt['stop_pct']:+.1f}%) [{pt['stop_method']}]",
            f"⚖️ R/R: 1:{pt['risk_reward']:.1f}",
        ]
    
    return "\n".join(lines)
