# Phase 3: Enhance Analysis

## Overview

| Attribute | Value |
|-----------|-------|
| Priority | P2 |
| Status | pending |
| Effort | 1h |
| Dependencies | Phase 2 |

Add new technical indicators (Stochastic, ADX, OBV, MFI) and enhance scoring system.

## Context Links

- [Technical Indicators Research](./research/researcher-02-technical-indicators.md)
- [Current indicators.py](../src/indicators.py)

## Key Insights

1. **Stochastic (14,3,3)**: Momentum oscillator, oversold < 20, overbought > 80
2. **ADX (14)**: Trend strength, > 25 = strong trend
3. **OBV**: Volume trend, rising = accumulation
4. **MFI (14)**: Money flow, combines price + volume

## Related Code Files

### Files to Modify
- `src/indicators.py` - Add new indicator functions
- `src/notifier.py` - Add summary report function

## Implementation Steps

### Step 3.1: Add new indicators to `src/indicators.py`

```python
import pandas as pd
import numpy as np

# ============================================================
# EXISTING INDICATORS (keep as-is)
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

# ============================================================
# NEW INDICATORS
# ============================================================

def calculate_stochastic(df: pd.DataFrame, period: int = 14,
                         smooth_k: int = 3, smooth_d: int = 3) -> pd.DataFrame:
    """
    Stochastic Oscillator (%K, %D)

    Formula:
        %K = (Close - Low_N) / (High_N - Low_N) * 100
        %D = SMA(%K, smooth_d)
    """
    low_n = df['low'].rolling(window=period).min()
    high_n = df['high'].rolling(window=period).max()

    df['%K_raw'] = 100 * (df['close'] - low_n) / (high_n - low_n)
    df['%K'] = df['%K_raw'].rolling(window=smooth_k).mean()
    df['%D'] = df['%K'].rolling(window=smooth_d).mean()

    # Cleanup temp columns
    df.drop(columns=['%K_raw'], inplace=True, errors='ignore')
    return df

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    ADX (Average Directional Index)

    Components: TR, +DI, -DI, DX, ADX
    ADX > 25 = strong trend
    """
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
    """
    OBV (On-Balance Volume)

    Cumulative volume based on price direction.
    Rising OBV = accumulation (bullish)
    """
    df['OBV'] = (df['volume'] * np.sign(df['close'].diff())).fillna(0).cumsum()
    return df

def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    MFI (Money Flow Index)

    Volume-weighted RSI. Combines price and volume.
    MFI > 80 = overbought, MFI < 20 = oversold
    """
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
    """Calculate all technical indicators"""
    if df is None or df.empty:
        return None

    # Existing indicators
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger(df)
    df = calculate_volume_ma(df)

    # New indicators
    df = calculate_stochastic(df)
    df = calculate_adx(df)
    df = calculate_obv(df)
    df = calculate_mfi(df)

    return df

def check_signals(df: pd.DataFrame) -> tuple:
    """
    Enhanced scoring system with new indicators.

    Returns:
        (score, reasons) tuple
    """
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []

    # ---- EXISTING SIGNALS ----

    # Signal 1: Volume spike (Vol > 1.3x MA20)
    if last['VolMA20'] > 0:
        vol_ratio = last['volume'] / last['VolMA20']
        if vol_ratio > 1.3:
            score += 2
            reasons.append(f"Vol spike (x{vol_ratio:.1f})")

    # Signal 2: MACD Golden Cross
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        score += 3
        reasons.append("MACD Golden Cross")

    # Signal 3: Price breaks above MA20
    if last['close'] > last['SMA20'] and prev['close'] <= prev['SMA20']:
        score += 2
        reasons.append("Break MA20")

    # Signal 4: RSI in good zone (40-60, rising)
    if 40 < last['RSI'] < 60 and last['RSI'] > prev['RSI']:
        score += 1
        reasons.append("RSI rising")

    # ---- NEW SIGNALS ----

    # Signal 5: Stochastic bullish crossover from oversold
    if last['%K'] > last['%D'] and prev['%K'] <= prev['%D'] and last['%D'] < 50:
        score += 2
        reasons.append("Stoch bullish cross")

    # Signal 6: ADX strong trend
    if last['ADX'] > 25:
        score += 1
        reasons.append(f"ADX {last['ADX']:.0f} (strong)")

    # Signal 7: OBV accumulation (rising OBV)
    obv_change = last['OBV'] - df['OBV'].iloc[-5]  # 5-day OBV change
    if obv_change > 0 and last['close'] >= prev['close']:
        score += 1
        reasons.append("OBV accumulation")

    # Signal 8: MFI from oversold
    if prev['MFI'] < 30 and last['MFI'] > prev['MFI']:
        score += 1
        reasons.append("MFI recovering")

    return score, reasons
```

### Step 3.2: Add summary report to `src/notifier.py`

Add function to send end-of-scan summary:

```python
import matplotlib.pyplot as plt
import requests
import os
from .config import TELEGRAM_TOKEN, CHAT_ID

def generate_chart(symbol, df):
    """Generate mini chart for signal"""
    data = df.tail(60)

    plt.figure(figsize=(10, 6))
    plt.plot(data['time'], data['close'], label='Price', color='black')
    plt.plot(data['time'], data['Upper'], color='green', linestyle='--', alpha=0.5)
    plt.plot(data['time'], data['Lower'], color='red', linestyle='--', alpha=0.5)
    plt.fill_between(data['time'], data['Upper'], data['Lower'], color='gray', alpha=0.1)

    plt.title(f"{symbol} - 60 Sessions")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    filename = f"{symbol}_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_telegram_alert(symbol, score, reasons, price, df):
    """Send individual stock alert"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return

    fireant_link = f"https://fireant.vn/ma-co-phieu/{symbol}"
    msg = (
        f"**BUY SIGNAL: {symbol}**\n"
        f"Score: {score}/10\n"
        f"Price: {price:,.0f}\n"
        f"Reasons: {', '.join(reasons)}\n"
        f"[View on Fireant]({fireant_link})"
    )

    chart_path = generate_chart(symbol, df)

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as img:
        payload = {'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'}
        files = {'photo': img}
        try:
            requests.post(url, data=payload, files=files)
        except Exception as e:
            print(f"Telegram error: {e}")

    if os.path.exists(chart_path):
        os.remove(chart_path)


def send_summary_report(exchange: str, total: int, signals: list):
    """
    Send end-of-scan summary report.

    Args:
        exchange: Exchange name or 'WATCHLIST'
        total: Total symbols scanned
        signals: List of (symbol, score, reasons) tuples
    """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return

    signal_count = len(signals)

    # Build message
    header = f"**SCAN COMPLETE: {exchange}**\n"
    stats = f"Scanned: {total} | Signals: {signal_count}\n"

    if signal_count > 0:
        signal_list = "\n".join([
            f"- {sym}: {score} pts"
            for sym, score, _ in sorted(signals, key=lambda x: -x[1])[:10]
        ])
        body = f"\n**Top Signals:**\n{signal_list}"
    else:
        body = "\nNo buy signals found."

    msg = header + stats + body

    # Send text message (no photo)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'}

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Summary send error: {e}")
```

### Step 3.3: Update `src/bot.py` to use summary report

Add summary at end of scan:

```python
# In main() function, after the for loop:

from .notifier import send_summary_report

# Collect signals during scan
signals_found = []  # List of (symbol, score, reasons)

for i, symbol in enumerate(symbols):
    # ... existing code ...

    if score >= MIN_SCORE:
        signals_found.append((symbol, score, reasons))
        # ... existing alert code ...

# After loop ends:
print(f"\nScan complete. Found {len(signals_found)} signals.")
send_summary_report(scan_name, len(symbols), signals_found)
```

## Todo List

- [ ] Add `calculate_stochastic()` to indicators.py
- [ ] Add `calculate_adx()` to indicators.py
- [ ] Add `calculate_obv()` to indicators.py
- [ ] Add `calculate_mfi()` to indicators.py
- [ ] Update `calculate_indicators()` to call new functions
- [ ] Update `check_signals()` with new scoring rules
- [ ] Add `send_summary_report()` to notifier.py
- [ ] Update bot.py to collect and send summary
- [ ] Test all indicators with sample data

## Success Criteria

- [ ] All new indicators calculate without errors
- [ ] New signals contribute to score correctly
- [ ] Summary report sent at end of scan
- [ ] No NaN values causing crashes

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Division by zero | Indicator crash | Use .replace(0, np.nan) |
| Missing columns | KeyError | Check column exists before access |
| Too many signals | Alert spam | Keep MIN_SCORE threshold |

## Security Considerations

- No sensitive data in summary report
- Symbol names only, no financial advice
