import matplotlib.pyplot as plt
import requests
import os
from .config import TELEGRAM_TOKEN, CHAT_ID

def generate_chart(symbol, df):
    """Vẽ biểu đồ mini nhanh"""
    data = df.tail(60) # 60 phiên gần nhất

    plt.figure(figsize=(10, 6))

    # Vẽ Giá và Bollinger Bands
    plt.plot(data['time'], data['close'], label='Giá', color='black')
    plt.plot(data['time'], data['Upper'], color='green', linestyle='--', alpha=0.5)
    plt.plot(data['time'], data['Lower'], color='red', linestyle='--', alpha=0.5)
    plt.fill_between(data['time'], data['Upper'], data['Lower'], color='gray', alpha=0.1)

    plt.title(f"Biểu đồ {symbol} (2 tháng)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    filename = f"{symbol}_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename

def send_telegram_alert(symbol, score, reasons, price, df):
    if not TELEGRAM_TOKEN or not CHAT_ID: return

    # Tạo nội dung tin nhắn
    fireant_link = f"https://fireant.vn/ma-co-phieu/{symbol}"
    msg = (
        f"🚀 **TÍN HIỆU MUA: {symbol}**\n"
        f"⭐ Điểm số: {score}/10\n"
        f"💰 Giá: {price:,.0f}\n"
        f"💡 Lý do: {', '.join(reasons)}\n"
        f"🔗 [Xem trên Fireant]({fireant_link})"
    )

    # Vẽ chart
    chart_path = generate_chart(symbol, df)

    # Gửi ảnh kèm text
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_path, 'rb') as img:
        payload = {
            'chat_id': CHAT_ID, 
            'caption': msg, 
            'parse_mode': 'Markdown'
        }
        files = {'photo': img}
        try:
            requests.post(url, data=payload, files=files)
        except Exception as e:
            print(f"Lỗi gửi tin Telegram: {e}")

    # Dọn dẹp ảnh
    if os.path.exists(chart_path):
        os.remove(chart_path)
