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
    parser = argparse.ArgumentParser(description='Bot Trading Pro')
    parser.add_argument('--exchange', type=str, default='HOSE', 
                        choices=['HOSE', 'HNX', 'UPCOM'], help='Chọn sàn')
    return parser.parse_args()

def get_ticker_industry_map(exchange_name):
    print(f"⏳ Đang tải danh sách ngành nghề sàn {exchange_name}...")
    try:
        df = listing_companies()
        exchange_name = exchange_name.upper()
        if 'exchange' in df.columns:
            df_filtered = df[df['exchange'] == exchange_name]
            # Lấy cột ngành (ưu tiên industry, nếu ko có lấy organ_short_name)
            ind_col = 'industry' if 'industry' in df_filtered.columns else 'organ_short_name'
            
            # Tạo map: Ticker -> Industry
            industry_map = pd.Series(df_filtered[ind_col].values, index=df_filtered['ticker']).to_dict()
            tickers = df_filtered['ticker'].tolist()
            print(f"✅ Đã tìm thấy {len(tickers)} mã.")
            return tickers, industry_map
        return [], {}
    except Exception as e:
        logging.error(f"Lỗi ngành: {e}")
        return [], {}

def main():
    args = parse_arguments()
    target = args.exchange
    
    # 1. LẤY MÃ
    watchlist, ind_map = get_ticker_industry_map(target)
    if not watchlist: return

    opportunities = []
    print(f"📋 Đang quét {len(watchlist)} mã...")
    
    # 2. QUÉT VÒNG LẶP
    for idx, symbol in enumerate(watchlist):
        if idx % 50 == 0: print(f"Scanning {idx}/{len(watchlist)}...")
        
        # A. Lấy data & Lọc
        df = fetch_data_safe(symbol)
        if df is None: continue
        
        is_good, _ = check_quality(df, symbol)
        if not is_good: continue
            
        # B. Tính điểm
        df = calculate_indicators(df)
        score, reasons, change = score_stock(df)
        
        # C. Lưu nếu đạt chuẩn
        if score >= MIN_SCORE_TO_ALERT:
            industry = ind_map.get(symbol, "Khác")
            opportunities.append({
                'symbol': symbol,
                'industry': industry,
                'score': score,
                'change': change,
                'reasons': reasons,
                'price': df.iloc[-1]['close']
            })

    # 3. GỬI BÁO CÁO
    if opportunities:
        # Sắp xếp theo điểm
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        top_picks = opportunities[:TOP_RANKING]
        
        # Gom nhóm theo ngành
        grouped = defaultdict(list)
        for item in top_picks:
            grouped[item['industry']].append(item)
            
        send_text_report(target, grouped)
    else:
        print("💤 Thị trường yên ắng.")

if __name__ == "__main__":
    main()
