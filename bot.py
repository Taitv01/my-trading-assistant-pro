import os
from analysis import get_market_data, check_conditions, get_vietnam_time
from notifier import create_chart, send_alert
from vnstock import listing_companies

# ==============================================================================
# MAIN CONTROLLER
# ==============================================================================

def get_watch_list():
    """Lấy danh sách VN30 hoặc danh sách theo dõi"""
    print("⏳ Đang tải danh sách mã...")
    default_list = ["HPG", "SSI", "STB", "VND", "DGW", "MWG", "FPT", "DIG", "PDR", "NVL", "VPB", "TCB", "MBB"]
    try:
        # Bạn có thể mở rộng lấy list VN30 ở đây
        return default_list 
    except:
        return default_list

def main():
    time_now = get_vietnam_time().strftime('%H:%M %d/%m')
    print(f"🛡️ Bot Pro khởi động lúc: {time_now}")
    
    watchlist = get_watch_list()
    print(f"📋 Đang quét {len(watchlist)} mã...")
    
    signal_found = False
    
    for stock in watchlist:
        # 1. Lấy dữ liệu & Tính chỉ báo (Gọi module analysis)
        df = get_market_data(stock)
        
        if df is not None:
            # 2. Kiểm tra điều kiện mua (Gọi module analysis)
            is_buy, reasons, score, change = check_conditions(df)
            
            if is_buy:
                signal_found = True
                print(f"✅ Phát hiện {stock} - Score: {score}")
                
                # 3. Vẽ biểu đồ & Gửi tin (Gọi module notifier)
                chart_path = create_chart(stock, df)
                send_alert(stock, df.iloc[-1]['close'], change, reasons, score, chart_path)
    
    if not signal_found:
        print("💤 Chưa thấy cơ hội ngon ăn (Score < 2).")

if __name__ == "__main__":
    main()
