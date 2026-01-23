# bot.py
from config import DEFAULT_WATCHLIST, MIN_SCORE
from analysis import get_market_data, calculate_indicators, score_stock
from notifier import create_pro_chart, send_telegram_alert
from datetime import datetime, timedelta

def main():
    # In giờ chạy để debug
    print(f"🚀 Bot bắt đầu quét lúc {(datetime.utcnow() + timedelta(hours=7)).strftime('%H:%M')}...")
    
    # Có thể nâng cấp logic lấy watchlist từ API ở đây
    watchlist = DEFAULT_WATCHLIST
    
    for symbol in watchlist:
        # 1. Lấy dữ liệu
        df = get_market_data(symbol)
        if df is None: continue

        # 2. Tính chỉ báo
        df = calculate_indicators(df)

        # 3. Chấm điểm (Ranking)
        score, reasons, change = score_stock(df)

        # 4. Lọc tín hiệu (Chỉ báo nếu điểm cao >= MIN_SCORE)
        if score >= MIN_SCORE:
            print(f"⭐ Phát hiện {symbol}: {score} điểm -> Gửi báo cáo.")
            chart_file = create_pro_chart(symbol, df)
            send_telegram_alert(symbol, df.iloc[-1]['close'], change, score, reasons, chart_file)
        else:
            print(f"💤 {symbol}: {score} điểm (Bỏ qua)")

if __name__ == "__main__":
    main()
