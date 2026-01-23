import requests
import os
from config import TELEGRAM_TOKEN, CHAT_ID

def send_text_report(exchange, grouped_data):
    """
    Gửi báo cáo gom nhóm theo ngành (Text Only)
    grouped_data: Dictionary {'Ngân hàng': [list các mã], ...}
    """
    if not TELEGRAM_TOKEN or not CHAT_ID: return

    # Tiêu đề báo cáo
    message = f"📊 **BÁO CÁO TÍN HIỆU {exchange}**\n"
    message += "------------------------------\n"
    
    # Duyệt từng ngành
    for industry, items in grouped_data.items():
        # Header Ngành (In đậm)
        message += f"🏢 **NHÓM: {industry.upper()}**\n"
        
        # Duyệt từng mã trong ngành đó
        for item in items:
            symbol = item['symbol']
            price = item['price']
            change = item['change']
            score = item['score']
            reasons = item['reasons'] # List lý do
            
            # Icon điểm số
            icon = "🔥" if score >= 9 else "✅"
            
            # Format chi tiết từng mã
            message += f"{icon} **{symbol}**: {price:,.0f} ({change:+.1f}%) | {score}đ\n"
            message += f"   • _Lý do:_ {', '.join(reasons)}\n"
            message += f"   • [Fireant](https://fireant.vn/ma-co-phieu/{symbol})\n"
        
        message += "\n" # Xuống dòng giữa các ngành cho thoáng

    message += "#BotTradingPro #PhanNganh"

    # Gửi tin nhắn (Vì tin nhắn có thể dài, Telegram giới hạn 4096 ký tự)
    # Ta sẽ cắt nhỏ nếu quá dài, nhưng với Top 10-15 mã thì thường vẫn đủ.
    try:
        if len(message) > 4000:
            # Nếu dài quá thì cắt đôi gửi 2 lần (Logic đơn giản)
            part1 = message[:4000]
            part2 = message[4000:]
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={'chat_id': CHAT_ID, 'text': part1, 'parse_mode': 'Markdown'})
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={'chat_id': CHAT_ID, 'text': part2, 'parse_mode': 'Markdown'})
        else:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'})
            
    except Exception as e:
        print(f"Lỗi gửi Telegram: {e}")
