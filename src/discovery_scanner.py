import time
import random
import pandas as pd
from .notifier import send_telegram_message  # Giả sử bạn import notifier như này

def run_discovery_scan(config):
    print("Bắt đầu Discovery Scan toàn thị trường...")
    
    # 1. Lấy danh sách mã (đã lọc sơ bộ)
    # Giả sử hàm listing_companies() lấy về DataFrame
    try:
        from vnstock import listing_companies
        df_stocks = listing_companies()
        # Lọc bỏ sàn UPCOM nếu cần, hoặc chỉ lấy mã có tên dài 3 ký tự
        symbols = df_stocks['ticker'].tolist()
        print(f"Tổng số mã cần quét: {len(symbols)}")
    except Exception as e:
        print(f"Lỗi không lấy được danh sách mã: {e}")
        return

    # 2. Vòng lặp quét an toàn
    scan_results = []
    
    for index, symbol in enumerate(symbols):
        try:
            # In log để biết đang chạy đến đâu
            if index % 10 == 0:
                print(f"Đang quét mã thứ {index}/{len(symbols)}: {symbol}...")

            # --- [QUAN TRỌNG] THÊM DELAY ---
            # Nghỉ ngẫu nhiên 2-4 giây để tránh lỗi 429 Too Many Requests
            time.sleep(random.uniform(2, 4)) 
            # -------------------------------

            # ... Gọi logic phân tích kỹ thuật của bạn ở đây ...
            # Ví dụ:
            # data = stock_historical_data(symbol, ...)
            # signal = analyze_stock(data)
            # if signal:
            #     scan_results.append(signal)

        except Exception as e:
            # Nếu lỗi 1 mã, chỉ in lỗi và bỏ qua, KHÔNG DỪNG CHƯƠNG TRÌNH
            print(f"⚠️ Lỗi quét mã {symbol}: {str(e)}")
            continue

    # 3. Gửi báo cáo sau khi quét xong
    if scan_results:
        message = f"📊 KẾT QUẢ DISCOVERY SCAN:\nTìm thấy {len(scan_results)} mã tiềm năng."
        # send_telegram_message(message)
    else:
        print("Không tìm thấy mã nào đạt tiêu chuẩn.")

    print("Hoàn thành Discovery Scan.")
