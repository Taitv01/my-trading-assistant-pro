import time
import random
import pandas as pd
from .config import MIN_SCORE
from .data_fetcher import fetch_data
from .indicators import calculate_indicators, check_signals
from .filters import is_investable

def run_discovery_scan():
    """Chạy quét toàn bộ thị trường"""
    print("Đang khởi tạo danh sách mã...")
    try:
        from vnstock import listing_companies
        # Lấy danh sách mã chứng khoán
        df_stocks = listing_companies()
        # Lọc các sàn chính (bỏ qua sàn lạ)
        df_stocks = df_stocks[df_stocks['exchange'].isin(['HOSE', 'HNX', 'UPCOM'])]
        symbols = df_stocks['ticker'].tolist()
        print(f"Tổng số mã cần quét: {len(symbols)}")
    except Exception as e:
        print(f"Lỗi lấy dữ liệu thị trường: {e}")
        return {}

    scanned_count = 0
    top_stocks = []
    volume_spikes = []

    # Quét từng mã
    for i, symbol in enumerate(symbols):
        # In tiến độ mỗi 10 mã
        if i % 10 == 0:
            print(f"Scanning {i}/{len(symbols)}: {symbol}...")
        
        try:
            # 1. Lấy dữ liệu
            df = fetch_data(symbol)
            if df is None or df.empty:
                time.sleep(1.0) # Vẫn nghỉ chút dù lỗi
                continue

            # 2. Lọc thanh khoản & giá (để đỡ tốn công tính toán mã rác)
            if not is_investable(df):
                time.sleep(1.0)
                continue
                
            # 3. Tính chỉ báo kỹ thuật
            df = calculate_indicators(df)
            
            # 4. Kiểm tra tín hiệu mua
            score, reasons = check_signals(df)
            scanned_count += 1
            
            # Logic lưu kết quả
            current_price = df.iloc[-1]['close']
            rsi_val = df.iloc[-1].get('rsi', 0)
            
            # Nếu điểm tốt (>=4) thì lưu lại
            if score >= 4:
                print(f"Found {symbol}: Score {score}")
                top_stocks.append({
                    'symbol': symbol,
                    'exchange': df_stocks[df_stocks['ticker'] == symbol]['exchange'].values[0],
                    'price': current_price,
                    'score': score,
                    'reasons': reasons,
                    'rsi': rsi_val
                })

            # Check volume spike (Đột biến khối lượng > 5 lần trung bình)
            avg_vol = df['volume'].mean()
            last_vol = df.iloc[-1]['volume']
            if avg_vol > 0 and (last_vol / avg_vol) > 5.0:
                 volume_spikes.append({
                    'symbol': symbol,
                    'exchange': df_stocks[df_stocks['ticker'] == symbol]['exchange'].values[0],
                    'vol_ratio': last_vol / avg_vol
                 })

            # --- QUAN TRỌNG: Sleep để tránh lỗi 429 Too Many Requests ---
            time.sleep(1.2) 

        except Exception as e:
            # print(f"Error {symbol}: {e}") # Có thể bỏ qua lỗi nhỏ
            continue

    # Sắp xếp kết quả theo điểm số giảm dần
    top_stocks.sort(key=lambda x: x['score'], reverse=True)
    
    # Trả về format đúng chuẩn cho notifier
    return {
        'total_scanned': scanned_count,
        'top_20_stocks': top_stocks[:20],
        'volume_spikes': volume_spikes,
        'top_industries': [] 
    }

def format_discovery_report(report):
    """Format kết quả quét để in ra màn hình console (Hàm bạn đang thiếu)"""
    if not report:
        return "Không có dữ liệu báo cáo."
    
    lines = [
        "\n" + "="*40,
        "   KẾT QUẢ DISCOVERY SCAN",
        "="*40,
        f"Tổng mã quét: {report.get('total_scanned', 0)}",
        f"Số mã đạt tiêu chuẩn: {len(report.get('top_20_stocks', []))}",
        "\nTOP 5 CỔ PHIẾU TIỀM NĂNG:"
    ]
    
    top_5 = report.get('top_20_stocks', [])[:5]
    if not top_5:
        lines.append(" (Không tìm thấy mã nào)")
    
    for stock in top_5:
        lines.append(f"- {stock['symbol']} ({stock['exchange']}): Score {stock['score']} | Giá: {stock['price']:,.0f}")
        
    return "\n".join(lines)
