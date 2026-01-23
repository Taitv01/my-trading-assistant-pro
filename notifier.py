import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import requests
import os
import pandas as pd
from config import TELEGRAM_TOKEN, CHAT_ID

def create_pro_chart(symbol, df, score):
    """Vẽ Chart Pro 3 tầng (Price, RSI, MACD)"""
    # Lấy 60 phiên gần nhất để vẽ cho rõ
    data = df.tail(60).copy()
    data['time'] = pd.to_datetime(data['time'])
    
    # Thiết lập layout: 3 hàng (Tỷ lệ cao 3:1:1)
    fig = plt.figure(figsize=(10, 12))
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])
    
    # --- 1. Main Chart (Price + MA + Vol) ---
    ax1 = plt.subplot(gs[0])
    ax1.plot(data['time'], data['close'], label='Giá', color='black', linewidth=1.5)
    ax1.plot(data['time'], data['MA20'], label='MA20', color='orange', linestyle='--')
    ax1.plot(data['time'], data['MA50'], label='MA50', color='blue', alpha=0.6)
    
    # Volume (Vẽ trục phụ bên phải nhưng đẩy xuống dưới)
    ax1_vol = ax1.twinx()
    colors = ['green' if c >= o else 'red' for c, o in zip(data['close'], data['open'])]
    ax1_vol.bar(data['time'], data['volume'], color=colors, alpha=0.2)
    ax1_vol.set_ylim(0, data['volume'].max() * 4) # Đẩy volume xuống đáy chart
    ax1_vol.axis('off')
    
    ax1.set_title(f"PHÂN TÍCH KỸ THUẬT: {symbol} (Score: {score})", fontsize=14, fontweight='bold', color='#004d00')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')

    # --- 2. RSI Chart ---
    ax2 = plt.subplot(gs[1], sharex=ax1)
    ax2.plot(data['time'], data['RSI'], color='purple')
    ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
    ax2.axhline(30, color='green', linestyle='--', alpha=0.5)
    ax2.fill_between(data['time'], data['RSI'], 70, where=(data['RSI']>=70), color='red', alpha=0.1)
    ax2.set_ylabel('RSI')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)

    # --- 3. MACD Chart ---
    ax3 = plt.subplot(gs[2], sharex=ax1)
    ax3.plot(data['time'], data['MACD'], label='MACD', color='blue')
    ax3.plot(data['time'], data['Signal'], label='Signal', color='orange')
    ax3.bar(data['time'], data['Hist'], color=['green' if h > 0 else 'red' for h in data['Hist']], alpha=0.5)
    ax3.set_ylabel('MACD')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    filename = f"{symbol}_pro_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_alert_pro(item):
    """Hàm gửi ảnh Chart kèm Caption chi tiết (Được gọi từ bot.py)"""
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    
    symbol = item['symbol']
    # Gọi hàm vẽ chart
    chart_path = create_pro_chart(symbol, item['df'], item['score'])
    
    caption = (
        f"🔥 **TOP SIGNAL: {symbol}** (Điểm: {item['score']})\n"
        f"💰 Giá: {item['price']:,.0f} ({item['change']:+.2f}%)\n"
        f"📊 Lý do khuyến nghị:\n"
        f"- {f'{chr(10)}- '.join(item['reasons'])}\n"
        f"🔗 [Fireant](https://fireant.vn/ma-co-phieu/{symbol}) | [Vietstock](https://finance.vietstock.vn/{symbol})\n"
        f"#BotFullMarket"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as img:
        try:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': img})
        except Exception as e:
            print(f"Lỗi gửi Telegram: {e}")
            
    # Xóa ảnh sau khi gửi để dọn dẹp bộ nhớ
    if os.path.exists(chart_path):
        os.remove(chart_path)
