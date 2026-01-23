import os
import requests
import pandas as pd
from vnstock import *
from datetime import datetime, timedelta

# ==============================================================================
# 1. CẤU HÌNH & LẤY KHÓA BÍ MẬT (TỪ GITHUB SECRETS)
# ==============================================================================
# Lưu ý: Không điền trực tiếp Token vào đây. GitHub sẽ tự điền khi chạy.
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Danh sách cổ phiếu theo dõi
WATCHLIST = {
    "🏦 NGÂN HÀNG": ["STB", "MBB", "TCB", "ACB", "VPB", "BID", "HDB"],
    "🔨 THÉP": ["HPG", "HSG", "NKG"],
    "📈 CHỨNG KHOÁN": ["SSI", "VIX", "VND", "HCM", "FTS", "MBS"],
    "🏘 BẤT ĐỘNG SẢN": ["DIG", "PDR", "DXG", "KBC", "IDC", "CEO", "NVL"],
    "🛒 BÁN LẺ/CN": ["MWG", "FPT", "DGW", "FRT"]
}

# ==============================================================================
# 2. CÁC HÀM XỬ LÝ LOGIC
# ==============================================================================

def get_vietnam_time():
    """Lấy giờ hiện tại theo múi giờ Việt Nam (UTC+7)"""
    return datetime.utcnow() + timedelta(hours=7)

def send_telegram(message):
    """Gửi tin nhắn đến Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Lỗi: Chưa tìm thấy Token hoặc Chat ID trong Secrets.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Lỗi gửi tin: {e}")

def calculate_rsi(series, period=14):
    """Tính chỉ số RSI"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_trading_minutes():
    """Tính số phút đã giao dịch thực tế trong ngày để dự phóng Volume"""
    now = get_vietnam_time()
    
    # Các mốc giờ giao dịch (Sáng: 9h-11h30, Chiều: 13h-14h45)
    t9h00 = now.replace(hour=9, minute=0, second=0, microsecond=0)
    t11h30 = now.replace(hour=11, minute=30, second=0, microsecond=0)
    t13h00 = now.replace(hour=13, minute=0, second=0, microsecond=0)
    t14h45 = now.replace(hour=14, minute=45, second=0, microsecond=0)
    
    minutes = 0
    if now < t9h00: minutes = 0
    elif t9h00 <= now <= t11h30: minutes = (now - t9h00).seconds / 60
    elif t11h30 < now < t13h00: minutes = 150 # Full sáng
    elif t13h00 <= now <= t14h45: minutes = 150 + (now - t13h00).seconds / 60
    else: minutes = 255 # Full ngày (4 tiếng 15 phút)
    
    return max(1, int(minutes)) # Tránh chia cho 0

def analyze_stock(symbol):
    """Phân tích chuyên sâu từng mã"""
    try:
        today_str = get_vietnam_time().strftime('%Y-%m-%d')
        # Lấy dữ liệu đủ dài để tính RSI và MA20
        df = stock_historical_data(symbol, "2025-10-01", today_str, "1D", "stock")
        
        if df is None or len(df) < 30: return None

        # Tính RSI
        df['RSI'] = calculate_rsi(df['close'])
        
        now_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        current_price = now_row['close']
        current_vol = now_row['volume']
        pct_change = (current_price - prev_row['close']) / prev_row['close'] * 100
        
        # --- LOGIC DỰ PHÓNG VOLUME (REAL-TIME PROJECTION) ---
        avg_vol_20 = df.iloc[-21:-1]['volume'].mean() # TB 20 phiên trước
        minutes_done = get_trading_minutes()
        total_minutes = 255
        
        # Nếu đang trong giờ GD, dự phóng volume cuối ngày theo tốc độ hiện tại
        projected_vol = (current_vol / minutes_done) * total_minutes
        
        # Nếu đã hết giờ (sau 14h45), dùng volume thực tế
        if minutes_done >= 255:
            projected_vol = current_vol
            
        vol_ratio = projected_vol / avg_vol_20
        
        return {
            "symbol": symbol,
            "price": current_price,
            "change": pct_change,
            "vol_ratio": vol_ratio,
            "rsi": now_row['RSI']
        }
    except:
        return None

# ==============================================================================
# 3. CHƯƠNG TRÌNH CHÍNH (CHẠY 1 LẦN RỒI THOÁT)
# ==============================================================================
def main():
    vn_time = get_vietnam_time()
    time_str = vn_time.strftime('%H:%M %d/%m')
    print(f"🚀 GitHub Action bắt đầu quét lúc: {time_str}")
    
    full_report = []
    
    for industry, stocks in WATCHLIST.items():
        signals = []
        for stock in stocks:
            data = analyze_stock(stock)
            if data:
                # --- BỘ LỌC TÍN HIỆU ---
                
                # 1. TIỀN VÀO MẠNH (Mua chủ động)
                # Vol dự kiến > 1.2 lần TB20 + Giá tăng > 1%
                if data['vol_ratio'] > 1.2 and data['change'] > 1.0:
                    icon = "🔥" if data['vol_ratio'] > 2.0 else "✅"
                    rsi_warn = " (⚠️RSI Cao)" if data['rsi'] > 70 else ""
                    
                    line = (f"{icon} *{stock}*: {data['price']} ({data['change']:.1f}%) "
                            f"| Vol: x{data['vol_ratio']:.1f} | RSI: {data['rsi']:.0f}{rsi_warn}")
                    signals.append(line)
                
                # 2. CẢNH BÁO XẢ HÀNG (Phân phối - Cá mập bán)
                # Vol to (>1.5 lần) nhưng Giá giảm sâu (<-1.5%)
                elif data['vol_ratio'] > 1.5 and data['change'] < -1.5:
                    line = (f"💀 *{stock} (BÁN THÁO)*: {data['price']} ({data['change']:.1f}%) "
                            f"| Vol: x{data['vol_ratio']:.1f} | RSI: {data['rsi']:.0f}")
                    signals.append(line)

        if signals:
            full_report.append(f"**{industry}**")
            full_report.extend(signals)
            full_report.append("---")
    
    # Gửi tin nhắn nếu có tín hiệu
    if full_report:
        msg = f"🔔 **TÍN HIỆU ({time_str})**\n\n" + "\n".join(full_report)
        msg += "\n_Sent from GitHub Actions_"
        send_telegram(msg)
        print("✅ Đã phát hiện cơ hội & Gửi tin Telegram!")
    else:
        print("💤 Thị trường ảm đạm, chưa có tín hiệu đặc biệt.")

if __name__ == "__main__":
    main()
