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


def send_summary_report(top_stocks, top_industries):
    """Send Full Scan summary report to Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram not configured, skipping notification.")
        return
    
    if not top_stocks:
        msg = "FULL SCAN REPORT\n\nKhong tim thay tin hieu mua nao trong phien."
    else:
        lines = ["FULL SCAN REPORT - TOP 10 CO PHIEU"]
        lines.append("=" * 35)
        
        for i, stock in enumerate(top_stocks[:10], 1):
            reasons_str = ", ".join(stock['reasons']) if stock['reasons'] else "-"
            lines.append(
                f"{i}. {stock['symbol']} | Score: {stock['score']} | "
                f"Gia: {stock['price']:,.0f}"
            )
            lines.append(f"   RSI: {stock['rsi']:.1f} | {reasons_str}")
        
        if top_industries:
            lines.append("\nTOP 3 NGANH DAN SONG:")
            for i, ind in enumerate(top_industries[:3], 1):
                lines.append(f"{i}. {ind['name']} ({ind['count']} tin hieu)")
        
        msg = "\n".join(lines)
    
    # Send text message
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': msg,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Summary report sent to Telegram.")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


def send_discovery_report(report):
    """Send Discovery Scan report to Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram not configured, skipping notification.")
        return
    
    lines = [
        "DISCOVERY SCAN REPORT",
        f"Scanned: {report['total_scanned']} stocks",
        "=" * 35,
        "",
        "TOP 10 STOCKS BY SIGNAL:",
    ]
    
    for i, stock in enumerate(report['top_20_stocks'][:10], 1):
        lines.append(f"{i}. {stock['symbol']} | Score:{stock['score']} | RSI:{stock['rsi']:.0f}")
    
    lines.append("")
    lines.append("VOLUME SPIKE ALERTS:")
    
    for i, stock in enumerate(report['volume_spikes'][:5], 1):
        lines.append(f"{i}. {stock['symbol']} Vol x{stock['vol_ratio']:.1f}")
    
    lines.append("")
    lines.append("TOP INDUSTRIES BY VALUE:")
    
    for i, ind in enumerate(report['top_industries'][:5], 1):
        lines.append(f"{i}. Group {ind['industry']}: {ind['stock_count']} stocks")
    
    msg = "\n".join(lines)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': msg,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Discovery report sent to Telegram.")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
