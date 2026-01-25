# Technical Indicators Research: Stochastic, ADX, OBV, MFI

**Date:** 2025-01-25
**Status:** Research Complete

## 1. Stochastic Oscillator (%K, %D)

### Formula
```
%K = (Close - Low_N) / (High_N - Low_N) * 100
%D = SMA(%K, 3)  [3-period moving average]
```
Default: 14 periods for lookback, 3 periods smoothing

### Signal Interpretation
- Overbought: > 80 (potential sell)
- Oversold: < 20 (potential buy)
- Bullish crossover: %K crosses above %D below 50 = buy signal

### Pandas Implementation
```python
def calc_stochastic(df, period=14, smooth_k=3, smooth_d=3):
    df['L_N'] = df['Low'].rolling(window=period).min()
    df['H_N'] = df['High'].rolling(window=period).max()
    df['%K'] = 100 * (df['Close'] - df['L_N']) / (df['H_N'] - df['L_N'])
    df['%K_smooth'] = df['%K'].rolling(window=smooth_k).mean()
    df['%D'] = df['%K_smooth'].rolling(window=smooth_d).mean()
    df.drop(['L_N', 'H_N'], axis=1, inplace=True)
    return df
```

## 2. ADX (Average Directional Index)

### Components
**True Range (TR):**
```
TR = max(High - Low, |High - Close_prev|, |Low - Close_prev|)
```

**Directional Movement:**
```
+DM = High - High_prev (if > Low_prev - Low, else 0)
-DM = Low_prev - Low (if > High - High_prev, else 0)

+DI = (+DM_smooth / TR_smooth) * 100
-DI = (-DM_smooth / TR_smooth) * 100
```

**ADX:**
```
DX = |+DI - -DI| / (+DI + -DI) * 100
ADX = Smoothed DX (14-period)
```

### Signal Interpretation
- ADX > 25: Strong trend (momentum exists)
- ADX < 20: Weak/no trend
- +DI > -DI: Uptrend
- -DI > +DI: Downtrend

### Pandas Implementation
```python
def calc_adx(df, period=14):
    df['TR'] = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - df['Close'].shift()).abs(),
        (df['Low'] - df['Close'].shift()).abs()
    ], axis=1).max(axis=1)

    df['+DM'] = np.where(df['High'].diff() > df['Low'].diff() * (-1),
                         df['High'].diff().clip(lower=0), 0)
    df['-DM'] = np.where(df['Low'].diff() * (-1) > df['High'].diff(),
                         df['Low'].diff() * (-1).clip(lower=0), 0)

    df['TR_smooth'] = df['TR'].rolling(period).sum()
    df['+DM_smooth'] = df['+DM'].rolling(period).sum()
    df['-DM_smooth'] = df['-DM'].rolling(period).sum()

    df['+DI'] = 100 * (df['+DM_smooth'] / df['TR_smooth'])
    df['-DI'] = 100 * (df['-DM_smooth'] / df['TR_smooth'])

    df['DX'] = 100 * (df['+DI'] - df['-DI']).abs() / (df['+DI'] + df['-DI'])
    df['ADX'] = df['DX'].rolling(period).mean()

    return df[['ADX', '+DI', '-DI']]
```

## 3. OBV (On-Balance Volume)

### Formula
```
OBV = Cumulative(Volume if Close > Close_prev else -Volume)
Signal: Interpret OBV trend, not absolute value
```

### Signal Interpretation
- OBV rising: Accumulation (bullish)
- OBV falling: Distribution (bearish)
- OBV divergence: Price up/OBV down = potential reversal

### Pandas Implementation
```python
def calc_obv(df):
    df['OBV'] = (df['Volume'] * np.sign(df['Close'].diff())).fillna(0).cumsum()
    return df[['OBV']]
```

## 4. MFI (Money Flow Index)

### Formula
```
TP = (High + Low + Close) / 3
MF = TP * Volume

Positive MF: if TP > TP_prev
Negative MF: if TP < TP_prev

MFI = 100 * (PMF_sum / (PMF_sum + NMF_sum))
[PMF/NMF summed over N periods]
```
Default: 14 periods

### Signal Interpretation
- MFI > 80: Overbought (potential sell)
- MFI < 20: Oversold (potential buy)
- MFI divergence: Price trend vs MFI trend = reversal signal

### Pandas Implementation
```python
def calc_mfi(df, period=14):
    df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['MF'] = df['TP'] * df['Volume']

    df['MF_sign'] = np.where(df['TP'].diff() > 0, df['MF'],
                             np.where(df['TP'].diff() < 0, -df['MF'], 0))

    df['PMF'] = df['MF'].where(df['TP'].diff() > 0, 0).rolling(period).sum()
    df['NMF'] = -df['MF'].where(df['TP'].diff() < 0, 0).rolling(period).sum()

    df['MFI'] = 100 * df['PMF'] / (df['PMF'] + df['NMF'])

    return df[['MFI']]
```

## Implementation Recommendations

### Integration Pattern
```python
# Single function to add all indicators
def add_technical_indicators(df):
    df = calc_stochastic(df, 14, 3, 3)
    df = calc_adx(df, 14)
    df[['OBV']] = calc_obv(df)
    df[['MFI']] = calc_mfi(df, 14)
    return df
```

### Buy Signal Logic
```python
# Multi-indicator confirmation
buy_signal = (
    (df['%D'] < 20) &                    # Stochastic oversold
    (df['ADX'] > 20) &                   # Trend exists
    (df['MFI'] < 30) &                   # Volume weakness confirmed
    (df['OBV'].diff() > 0)               # Volume accumulation starting
)
```

### Library Alternative
Use `pandas_ta` for production:
```python
import pandas_ta as ta
df.ta.stoch(length=14, k_smoothing=3, d_smoothing=3, append=True)
df.ta.adx(length=14, append=True)
df.ta.obv(append=True)
df.ta.mfi(length=14, append=True)
```

## Performance Notes
- **Stochastic:** Fast, no lag, works well on 4H+ timeframes
- **ADX:** Best for trend confirmation, avoid rangebound markets
- **OBV:** Cumulative, sensitive to volume spikes, use with trend
- **MFI:** Combines price + volume, best 14-period on daily+

## Unresolved Questions
- None - all formulas and implementation patterns documented

---
**Sources:**
- [Stochastic Oscillator in Python](https://www.alpharithms.com/stochastic-oscillator-in-python-483214/)
- [ADX Calculation Guide](https://blog.quantinsti.com/adx-indicator-python/)
- [Money Flow Index](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/money-flow-index-mfi)
- [Technical Analysis Libraries](https://github.com/bukosabino/ta)
- [Pandas TA Documentation](https://pypi.org/project/pandas-ta/)
