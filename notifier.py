import requests
from config import TELEGRAM_TOKEN, CHAT_ID

def send_text_report(exchange, grouped_data):
    if not TELEGRAM_TOKEN or not CHAT_ID: return

    # Header
    msg = f"📊 **BÁO CÁO TÍN HIỆU {exchange}**\n"
    msg += "------------------------------\n"
    
    # Body
    for industry, items in grouped_data.items():
        msg += f"🏢 **{industry.upper()}**\n"
        for item in items:
            icon = "🔥" if item['score'] >= 9 else "✅"
            msg += f"{icon} **{item['symbol']}**: {item['price']:,.0f} ({item['change']:+.1f}%) | {item['score']}đ\n"
            msg += f"   • {', '.join(item['reasons'])}\n"
        msg += "\n"
        
    msg += "#BotTradingPro"

    # Gửi tin (Chia nhỏ nếu quá dài)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    if len(msg) > 4000:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': msg[:4000], 'parse_mode': 'Markdown'})
        requests.post(url, json={'chat_id': CHAT_ID, 'text': msg[4000:], 'parse_mode': 'Markdown'})
    else:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
