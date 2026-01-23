from .config import WATCHLIST, MIN_SCORE
from .data_fetcher import fetch_data
from .indicators import calculate_indicators, check_signals
from .filters import is_investable
from .notifier import send_telegram_alert
import sys

def main():
    print("🚀 Bot Version 2.0 đang khởi động...")
    print(f"📋 Danh sách theo dõi: {len(WATCHLIST)} mã")

    signal_count = 0

    for symbol in WATCHLIST:
        # 1. Lấy dữ liệu
        df = fetch_data(symbol)
        if df is None: continue

        # 2. Tính chỉ báo
        df = calculate_indicators(df)

        # 3. Lọc rác (Thanh khoản/Giá)
        if not is_investable(df):
            continue

        # 4. Kiểm tra tín hiệu
        score, reasons = check_signals(df)

        # 5. Thông báo nếu đủ điểm
        if score >= MIN_SCORE:
            print(f"✅ PHÁT HIỆN: {symbol} (Score: {score})")
            send_telegram_alert(symbol, score, reasons, df.iloc[-1]['close'], df)
            signal_count += 1
        else:
            print(f"zzz {symbol}: {score} điểm (Bỏ qua)")

    if signal_count == 0:
        print("💤 Thị trường ảm đạm, không có tín hiệu mua.")

if __name__ == "__main__":
    main()
