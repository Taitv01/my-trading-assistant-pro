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


def get_exchange_badge(exchange: str) -> str:
    """Return emoji badge for exchange"""
    badges = {
        'HOSE': '🔴',
        'HNX': '🟢',
        'UPCOM': '🟡'
    }
    return badges.get(exchange.upper() if exchange else '', '⚪')


def get_rsi_status(rsi: float) -> str:
    """Return RSI status description"""
    if rsi >= 70:
        return "⚠️ Quá mua"
    elif rsi <= 30:
        return "🔥 Quá bán"
    elif rsi <= 50:
        return "✅ An toàn"
    else:
        return "📊 Trung tính"


def send_discovery_report(report):
    """Send professional Discovery Scan report to Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram not configured, skipping notification.")
        return
    
    from datetime import datetime
    scan_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Build professional message
    lines = [
        "👋 **Chào nhà đầu tư!**",
        f"📊 **BẢN TIN THỊ TRƯỜNG - {scan_time}**",
        f"_Quét {report['total_scanned']:,} mã - Antigravity Bot_",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🚀 **CƠ HỘI TIỀM NĂNG (Top 10)**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    
    # Group by exchange for better overview
    top_stocks = report['top_20_stocks'][:10]
    
    if not top_stocks:
        lines.append("_Không có tín hiệu mua mạnh trong phiên._")
    else:
        for i, stock in enumerate(top_stocks, 1):
            exchange = stock.get('exchange', 'UNKNOWN')
            badge = get_exchange_badge(exchange)
            rsi = stock.get('rsi', 0)
            rsi_status = get_rsi_status(rsi)
            
            lines.append(
                f"{i}. {badge} **{stock['symbol']}** ({exchange})"
            )
            lines.append(
                f"   ⭐ Score: {stock['score']}/10 | RSI: {rsi:.0f} {rsi_status}"
            )
            lines.append(
                f"   💰 Giá: {stock['price']:,.0f} VNĐ"
            )
    
    # Volume spike alerts
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🚨 **CẢNH BÁO DÒNG TIỀN ĐỘT BIẾN**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ])
    
    volume_spikes = report.get('volume_spikes', [])[:5]
    if not volume_spikes:
        lines.append("_Không có biến động khối lượng bất thường._")
    else:
        for stock in volume_spikes:
            exchange = stock.get('exchange', 'UNKNOWN')
            badge = get_exchange_badge(exchange)
            vol_ratio = stock.get('vol_ratio', 0)
            
            # Risk level based on volume spike
            if vol_ratio >= 15:
                risk = "🔴 RỦI RO CAO"
            elif vol_ratio >= 8:
                risk = "🟠 RỦI RO TB"
            else:
                risk = "🟡 THEO DÕI"
            
            lines.append(
                f"• {badge} **{stock['symbol']}** Vol x{vol_ratio:.1f} - {risk}"
            )
        
        lines.append("")
        lines.append("_⚠️ Khối lượng đột biến = Cơ hội lẫn rủi ro. Quản trị vốn chặt!_")
    
    # Industry analysis
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📈 **XU HƯỚNG DÒNG TIỀN NGÀNH**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ])
    
    top_industries = report.get('top_industries', [])[:5]
    medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    
    for i, ind in enumerate(top_industries):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        lines.append(
            f"{medal} Nhóm **{ind['industry']}**: {ind['stock_count']} mã | {ind['signal_count']} tín hiệu"
        )
    
    # Recommendation footer
    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 **KHUYẾN NGHỊ**",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ])
    
    # Dynamic recommendation based on signals
    signal_count = len([s for s in top_stocks if s.get('score', 0) >= 6])
    if signal_count >= 5:
        lines.append("✅ Thị trường có nhiều tín hiệu tốt. Có thể **giải ngân 30%** vào các mã Top 5.")
    elif signal_count >= 2:
        lines.append("⚖️ Thị trường ổn định. Nên **thăm dò 15-20%** vào các mã có RSI an toàn.")
    else:
        lines.append("⏸️ Tín hiệu còn yếu. Nên **quan sát** và chờ xác nhận xu hướng.")
    
    lines.extend([
        "",
        "_📌 Đây là phân tích kỹ thuật, không phải khuyến nghị đầu tư._",
        "_🔗 Powered by Antigravity Trading Bot_"
    ])
    
    msg = "\n".join(lines)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': msg,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Discovery report sent to Telegram.")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
