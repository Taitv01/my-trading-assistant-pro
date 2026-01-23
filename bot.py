import logging
import argparse
from datetime import datetime, timedelta
from config import MIN_SCORE_TO_ALERT, TOP_RANKING, LOG_FILE
from analysis import fetch_data_safe, check_quality, calculate_indicators, score_stock
from notifier import send_alert_pro
from vnstock import listing_companies

# Cấu hình Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def parse_args():
    """Nhận tham số từ dòng lệnh để chọn sàn"""
    parser = argparse.ArgumentParser(description="Bot Trading Pro")
    parser.add_argument("--exchange", type=str, default="HOSE", 
                        choices=["HOSE", "HNX", "UPCOM", "ALL"],
                        help="Chọn sàn giao dịch: HOSE, HNX, UPCOM hoặc ALL")
    return parser.parse_args()

def get_market_tickers(exchange="HOSE"):
    """Lấy danh sách mã chứng khoán theo sàn"""
    logging.info(f"⏳ Đang tải danh sách mã sàn {exchange}...")
    try:
        df = listing_companies()
        
        # Chuyển đổi tên sàn về chữ in hoa để so sánh
        exchange = exchange.upper()
        
        if exchange != "ALL":
            # Lọc theo sàn
            df = df[df['exchange'] == exchange]
        
        # Chỉ lấy mã cổ phiếu (độ dài < 4 ký tự để loại bỏ Chứng quyền/Phái sinh)
        # Vì chứng quyền thường dài (VD: CHPG2301), cổ phiếu thường chỉ 3 chữ (HPG)
        tickers = [t for t in df['ticker'].tolist() if len(t) == 3]
        
        logging.info(f"✅ Đã tìm thấy {len(tickers)} mã cổ phiếu trên {exchange}.")
        return tickers
    except Exception as e:
        logging.error(f"❌ Lỗi lấy danh sách ticker: {str(e)}")
        return []

def main():
    args = parse_args()
    TARGET_EXCHANGE = args.exchange

    start_time = datetime.utcnow() + timedelta(hours=7)
    logging.info(f"🚀 BOT START ({TARGET_EXCHANGE}): {start_time.strftime('%H:%M %d/%m')}")
    
    # 1. LẤY DANH SÁCH MÃ ĐỘNG (FULL MARKET)
    watchlist = get_market_tickers(TARGET_EXCHANGE)
    
    if not watchlist:
        logging.error("Không có mã nào để quét. Kết thúc.")
        return

    opportunities = []
    
    # 2. QUÉT & PHÂN TÍCH
    logging.info(f"📋 Bắt đầu quét {len(watchlist)} mã...")
    
    for idx, symbol in enumerate(watchlist):
        # Log tiến độ để biết bot còn sống (Mỗi 50 mã in 1 lần)
        if idx % 50 == 0: 
            logging.info(f"Scanning {idx}/{len(watchlist)}...")
        
        # A. Fetch Data (Retry 3 lần)
        df = fetch_data_safe(symbol)
        if df is None: continue
        
        # B. Quality Check (CỰC KỲ QUAN TRỌNG VỚI UPCOM/HNX)
        # Sàn UPCOM rất nhiều mã rác thanh khoản = 0, bước này giúp Bot chạy nhanh hơn
        # bằng cách bỏ qua ngay lập tức các mã rác mà không cần tính chỉ báo.
        is_good, msg = check_quality(df, symbol)
        if not is_good:
            # logging.debug(f"Skip {symbol}: {msg}") # Bỏ comment nếu muốn xem log chi tiết
            continue
            
        # C. Calculate & Score
        df = calculate_indicators(df)
        score, reasons, change = score_stock(df)
        
        # D. Lưu lại nếu điểm cao
        if score >= MIN_SCORE_TO_ALERT:
            logging.info(f"⭐ Detect {symbol}: {score}đ")
            opportunities.append({
                'symbol': symbol,
                'score': score,
                'change': change,
                'reasons': reasons,
                'price': df.iloc[-1]['close'],
                'df': df
            })

    # 3. RANKING & ALERT
    if not opportunities:
        logging.info(f"💤 Sàn {TARGET_EXCHANGE} hôm nay yên ắng.")
    else:
        # Sắp xếp giảm dần theo điểm
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        top_picks = opportunities[:TOP_RANKING]
        
        logging.info(f"📡 Tìm thấy {len(opportunities)} cơ hội. Gửi Top {len(top_picks)}...")
        
        for item in top_picks:
            send_alert_pro(item)
            logging.info(f"✅ Sent alert for {item['symbol']}")

    logging.info("🏁 BOT FINISHED.")

if __name__ == "__main__":
    main()
