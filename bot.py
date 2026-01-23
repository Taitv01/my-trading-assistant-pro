import logging
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from config import MIN_SCORE_TO_ALERT, TOP_RANKING
from analysis import fetch_data_safe, check_quality, calculate_indicators, score_stock
from notifier import send_text_report
from vnstock import listing_companies

# Setup Logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Bot Trading Pro Scan')
    parser.add_argument('--exchange', type=str, default='HOSE', 
                        choices=['HOSE', 'HNX', 'UPCOM'],
                        help='Chọn sàn giao dịch')
    return parser.parse_args()

def get_ticker_industry_map(exchange_name):
    """
    Lấy danh sách mã và map ngành nghề
    Output: (['HPG', 'NKG'], {'HPG': 'Tài nguyên', 'NKG': 'Tài nguyên'})
    """
    print(f"⏳ Đang tải dữ liệu ngành nghề sàn {exchange_name}...")
    try:
        df = listing_companies()
        exchange_name = exchange_name.upper()
        
        # Lọc theo sàn
        if 'exchange' in df.columns:
            df_filtered = df[df['exchange'] == exchange_name]
            
            # Tạo dictionary: Key=Ticker, Value=Industry
            # Cột ngành thường tên là 'industry' hoặc 'organ_sector' tùy version vnstock
            # Ta ưu tiên lấy ngành cấp 2 (chi tiết hơn)
            if 'industry' in df_filtered.columns:
                ind_col = 'industry' 
            else:
                ind_col = 'organ_short_name' # Fallback
            
            # Map ticker -> industry
            # Ví dụ: {'VCB': 'Ngân hàng', 'HPG': 'Thép'}
            industry_map = pd.Series(df_filtered[ind_col].values, index=df_filtered['ticker']).to_dict()
            tickers = df_filtered['ticker'].tolist()
            
            print(f"✅ Đã map ngành cho {len(tickers)} mã sàn {exchange_name}.")
            return tickers, industry_map
        else:
            return [], {}
    except Exception as e:
        logging.error(f"Lỗi lấy ngành: {e}")
        return [], {}

def main():
    args = parse_arguments()
    target_exchange = args.exchange
    start_time = datetime.utcnow() + timedelta(hours=7)
    
    print(f"🚀 Bot Pro (Text Only) khởi động lúc {start_time.strftime('%H:%M %d/%m')}")
    
    # 1. LẤY MÃ & NGÀNH
    watchlist, industry_map = get_ticker_industry_map(target_exchange)
    
    if not watchlist:
        print("❌ Không lấy được danh sách mã.")
        return

    opportunities = [] 
    
    print(f"📋 Bắt đầu phân tích {len(watchlist)} mã...")
    
    for idx, symbol in enumerate(watchlist):
        if idx % 50 == 0: print(f"Scanning {idx}/{len(watchlist)}...")

        # A. Lấy dữ liệu & Lọc
        df = fetch_data_safe(symbol)
        if df is None: continue
        
        is_good, msg = check_quality(df, symbol)
        if not is_good: continue 
            
        # B. Tính toán
        df = calculate_indicators(df)
        score, reasons, change = score_stock(df)
        
        # C. Lưu nếu đạt điểm
        if score >= MIN_SCORE_TO_ALERT:
            # Lấy ngành của mã này (Nếu không có thì để 'Khác')
            industry = industry_map.get(symbol, "Khác")
            
            opportunities.append({
                'symbol': symbol,
                'industry': industry, # Quan trọng: Lưu ngành vào đây
                'score': score,
                'change': change,
                'reasons': reasons,
                'price': df.iloc[-1]['close'],
                'vol': df.iloc[-1]['volume']
            })
            logging.info(f"⭐ {symbol}: {score}đ")

    # 2. GOM NHÓM THEO NGÀNH (GROUPING)
    if not opportunities:
        print(f"💤 Sàn {target_exchange} yên ắng.")
    else:
        # Sắp xếp theo điểm số cao nhất trước
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Chỉ lấy Top N mã tốt nhất toàn thị trường (để tránh spam)
        top_picks = opportunities[:TOP_RANKING + 5] # Lấy dư ra chút
        
        # Gom nhóm: Dictionary { 'Ngân hàng': [Mã A, Mã B], 'Thép': [Mã C] }
        grouped_results = defaultdict(list)
        for item in top_picks:
            grouped_results[item['industry']].append(item)
            
        print(f"📡 Đang gửi báo cáo phân ngành...")
        
        # Gửi report text
        send_text_report(target_exchange, grouped_results)

    print("✅ Hoàn thành.")

if __name__ == "__main__":
    main()
