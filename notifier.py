import os
import requests
import matplotlib.pyplot as plt
import pandas as pd

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def create_chart(symbol, df):
    """Vẽ biểu đồ nâng cao: Giá + BB + MA + RSI"""
    data = df.tail(50).copy() # Vẽ 50 nến gần nhất
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    # --- Chart 1: Giá + Bollinger Bands + MA ---
    ax1.plot(data['time'], data['close'], label='Giá', color='black', linewidth=1.5)
    ax1.plot(data['time'], data['Upper'], color='green', linestyle='--', alpha=0.3, label='Bollinger Upper')
    ax1.plot(data['time'], data['Lower'], color='red', linestyle='--', alpha=0.3, label='Bollinger Lower')
    ax1.fill_between(data['time'], data['Upper'], data['Lower'], color='gray', alpha=0.1)
    ax1.plot(data['time'], data['MA50'], color='orange', label='MA50', linewidth=1)
    
    ax1.set_title(f"Phân tích kỹ thuật {symbol}", fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # --- Chart 2: RSI ---
    ax2.plot(data['time'], data['RSI'], label='RSI', color='purple')
    ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
    ax2.axhline(30, color='green', linestyle='--', alpha=0.5)
    ax2.fill_between(data['time'], data['RSI'], 70, where=(data['RSI']>=70), color='red', alpha=0.3)
    ax2.fill_between(data['time'], data['RSI'], 30, where=(data['RSI']<=30), color='green', alpha=0.3)
    ax2.set_title("RSI (Sức mạnh giá)")
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    
    # Lưu ảnh
    filename = f"{symbol}_pro_chart.png"
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename

def send_alert(symbol, price, change, reasons, score, image_path):
    """Gửi tin nhắn Telegram kèm Link Fireant"""
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    
    # Tạo link Fireant nhanh
    fireant_link = f"https://fireant.vn/ma-co-phieu/{symbol}"
    
    caption = (
        f"🚀 **TÍN HIỆU PRO: {symbol}** (Score: {score})\n"
        f"💰 Giá: {price} ({change:.1f}%)\n"
        f"🛠 Tín hiệu: {reasons}\n"
        f"🔗 [Xem trên Fireant]({fireant_link})\n"
        f"------------------\n"
        f"#BotNangCap"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(image_path, 'rb') as img:
        payload = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
        files = {'photo': img}
        try:
            requests.post(url, data=payload, files=files)
        except Exception as e:
            print(f"Lỗi gửi tin: {e}")
            
    # Xóa ảnh sau khi gửi
    if os.path.exists(image_path):
        os.remove(image_path)
