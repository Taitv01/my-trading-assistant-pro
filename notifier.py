# notifier.py
import matplotlib.pyplot as plt
import requests
import os
import matplotlib.dates as mdates
from config import TELEGRAM_TOKEN, CHAT_ID

def create_pro_chart(symbol, df):
    """Vẽ Chart Pro: Giá/MA, Volume, MACD"""
    data = df.tail(60).copy() # Zoom vào 60 phiên gần nhất
    
    # Tạo 3 khung: Giá (to nhất), Volume, MACD
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # --- AX1: Giá, BB, MA ---
    ax1.plot(data['time'], data['close'], label='Giá', color='black', linewidth=1.5)
    ax1.plot(data['time'], data['MA20'], label='MA20', color='orange', linestyle='--')
    ax1.plot(data['time'], data['MA50'], label='MA50', color='blue', linewidth=1)
    ax1.fill_between(data['time'], data['Upper'], data['Lower'], color='gray', alpha=0.1)
    ax1.set_title(f"Phân tích kỹ thuật: {symbol}", fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # --- AX2: Volume (Dạng Bar) ---
    colors = ['green' if c >= o else 'red' for c, o in zip(data['close'], data['open'])]
    ax2.bar(data['time'], data['volume'], color=colors, alpha=0.7)
    ax2.set_ylabel("Volume")
    ax2.grid(True, alpha=0.3)

    # --- AX3: MACD ---
    ax3.plot(data['time'], data['MACD'], label='MACD', color='blue')
    ax3.plot(data['time'], data['Signal'], label='Signal', color='orange')
    ax3.bar(data['time'], data['Hist'], color=['green' if h > 0 else 'red' for h in data['Hist']], alpha=0.3)
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)

    # Format ngày tháng
    plt.tight_layout()
    filename = f"{symbol}_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_telegram_alert(symbol, price, change, score, reasons, chart_path):
    if not TELEGRAM_TOKEN or not CHAT_ID: return

    # Icon theo điểm số
    icon = "🔥" if score >= 4 else "✅"
    
    caption = (
        f"{icon} **TÍN HIỆU: {symbol}** (Điểm: {score}/5)\n"
        f"💰 Giá: {price:,.0f} ({change:+.2f}%)\n"
        f"📋 Lý do: {', '.join(reasons)}\n"
        f"📊 [Fireant](https://fireant.vn/ma-co-phieu/{symbol}) | [Vietstock](https://finance.vietstock.vn/{symbol})\n"
        f"#BotTradingPro"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as img:
        try:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': img})
        except Exception as e:
            print(f"Lỗi gửi tin: {e}")
    
    if os.path.exists(chart_path):
        os.remove(chart_path)
