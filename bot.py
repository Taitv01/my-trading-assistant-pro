import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from vnstock import *
from datetime import datetime, timedelta

# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG
# ==============================================================================
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_vietnam_time():
    """Lấy giờ Việt Nam (UTC+7)"""
    return datetime.utcnow() + timedelta(hours=7)

def get_watch_list():
    """Tự động lấy danh sách VN30"""
    print("⏳ Đang tải danh sách VN30...")
    default_list = ["HPG", "SSI", "STB", "VND", "DGW", "MWG", "FPT", "DIG", "PDR", "NVL"]
    try:
        # Lấy danh sách sàn HOSE
        df = listing_companies()
        # Lọc VN30 (Nếu API chưa cập nhật group VN30, ta lấy tạm Top vốn hóa hoặc list mặc định)
        # Ở đây mình dùng list mặc định kết hợp 1 vài mã hot để đảm bảo luôn chạy được
        return default_list 
    except:
        return default_list

# ==============================================================================
# 2. XỬ LÝ KỸ THUẬT & VẼ BIỂU ĐỒ
# ==============================================================================

def calculate_indicators(df):
    """Tính RSI và MACD"""
    # RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    
    # MACD (12, 26, 9)
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def create_chart(symbol, df):
    """Vẽ biểu đồ và lưu thành file ảnh"""
    # Lấy 40 phiên gần nhất
    data = df.tail(40).copy()
    
    # Tạo khung vẽ: Trên là Giá, Dưới là RSI
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
    
    # Chart 1: Giá
    ax1.plot(data['time'], data['close'], label='Giá', color='#1f77b4', linewidth=2)
    ax1.set_title(f"Biểu đồ {symbol} (40 phiên)", fontsize=14, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend()
    
    # Chart 2: RSI
    ax2.plot(data['time'], data['RSI'], label='RSI', color='#9467bd', linewidth=2)
    ax2.axhline(70, color='red', linestyle='--', alpha=0.5, label='Quá mua (70)')
    ax2.axhline(30, color='green', linestyle='--', alpha=0.5, label='Quá bán (30)')
    ax2.set_title("Chỉ báo RSI")
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.set_ylim(0, 100)
    
    # Lưu ảnh
    filename = f"{symbol}_analysis.png"
    plt.tight_layout()
    plt.savefig(filename)
    plt.close() # Đóng hình để giải phóng bộ nhớ
    return filename

def send_telegram_photo(caption, image_path):
    """Gửi ảnh sang Telegram"""
    if not TELEGRAM_TOKEN or not CHAT_ID: return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(image_path, 'rb') as img:
        payload = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}
        files = {'photo': img}
        try:
            requests.post(url, data=payload, files=files)
        except Exception as e:
            print(f"Lỗi gửi ảnh: {e}")

# ==============================================================================
# 3. LOGIC PHÂN TÍCH (CORE)
# ==============================================================================
def analyze_stock(symbol):
    try:
        today_str = get_vietnam_time().strftime('%Y-%m-%d')
        # Lấy 60 phiên để tính toán chỉ báo
        df = stock_historical_data(symbol, "2025-08-01", today_str, "1D", "stock")
        
        if df is None or len(df) < 50: return None

        df = calculate_indicators(df)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- TIÊU CHÍ LỌC ---
        is_signal = False
        reasons = []
        
        # 1. Logic Dòng tiền (Vol > 1.3 TB20)
        avg_vol_20 = df.iloc[-22:-2]['volume'].mean()
        vol_ratio = last['volume'] / avg_vol_20
        
        # 2. Logic Giá (Tăng > 0.5%)
        change_pct = (last['close'] - prev['close']) / prev['close'] * 100
        
        # ĐIỀU KIỆN MUA MẠNH: (Tiền vào + Giá tăng + RSI chưa quá nóng)
        if vol_ratio > 1.3 and change_pct > 0.5 and last['RSI'] < 75:
            is_signal = True
            reasons.append(f"Vol đột biến x{vol_ratio:.1f}")
            
        # ĐIỀU KIỆN ĐẢO CHIỀU: (MACD cắt lên)
        if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
            is_signal = True
            reasons.append("MACD cắt lên (Đảo chiều)")
            
        return {
            "symbol": symbol,
            "price": last['close'],
            "change": change_pct,
            "reasons": ", ".join(reasons),
            "is_signal": is_signal,
            "df": df
        }
    except:
        return None

# ==============================================================================
# 4. CHẠY CHƯƠNG TRÌNH
# ==============================================================================
def main():
    time_now = get_vietnam_time().strftime('%H:%M %d/%m')
    print(f"🚀 Bot V2.0 bắt đầu quét lúc: {time_now}")
    
    watchlist = get_watch_list()
    print(f"📋 Danh sách quét: {len(watchlist)} mã")
    
    signal_count = 0
    
    for stock in watchlist:
        res = analyze_stock(stock)
        
        if res and res['is_signal']:
            signal_count += 1
            # Vẽ biểu đồ
            chart_file = create_chart(stock, res['df'])
            
            # Soạn nội dung
            msg = (
                f"🔥 **TÍN HIỆU: {stock}**\n"
                f"⏰ {time_now}\n"
                f"💰 Giá: {res['price']} ({res['change']:.1f}%)\n"
                f"💡 Lý do: {res['reasons']}\n"
                f"------------------\n"
                f"#BotChungKhoan"
            )
            
            # Gửi ảnh
            send_telegram_photo(msg, chart_file)
            print(f"✅ Đã gửi tín hiệu mã {stock}")
            
            # Dọn dẹp file ảnh
            if os.path.exists(chart_file):
                os.remove(chart_file)
                
    if signal_count == 0:
        print("💤 Không tìm thấy tín hiệu nào đủ mạnh.")

if __name__ == "__main__":
    main()
