"""
Health Check Script - Chạy trước khi quét chính để đảm bảo hệ thống hoạt động
"""
import sys
import os

# Thêm thư mục gốc vào path để import được src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_fetcher import fetch_data
from src.indicators import calculate_indicators, check_signals
from src.filters import is_investable


def main():
    print("=" * 50)
    print("🏥 HEALTH CHECK - Kiểm tra hệ thống")
    print("=" * 50)
    
    # ========================================
    # 1. KIỂM TRA LẤY DỮ LIỆU (SCRAPING CHECK)
    # ========================================
    print("\n1️⃣  Kiểm tra API lấy dữ liệu...")
    test_symbol = 'FPT'
    
    try:
        df = fetch_data(test_symbol, days=100)
        
        if df is None or df.empty:
            print(f"❌ FAILED: fetch_data('{test_symbol}') trả về None hoặc rỗng.")
            print("   → API vnstock có thể bị lỗi hoặc rate limit.")
            sys.exit(1)
        
        # Kiểm tra cột bắt buộc
        required_cols = ['close', 'open', 'high', 'low', 'volume', 'time']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"❌ FAILED: Thiếu cột dữ liệu: {missing_cols}")
            print(f"   → Các cột có: {list(df.columns)}")
            sys.exit(1)
            
        print(f"✅ Lấy dữ liệu thành công!")
        print(f"   • Mã: {test_symbol}")
        print(f"   • Số dòng: {len(df)}")
        print(f"   • Ngày mới nhất: {df.iloc[-1]['time']}")
        print(f"   • Giá đóng cửa: {df.iloc[-1]['close']:,.0f} VND")
        
    except Exception as e:
        print(f"❌ FAILED: Lỗi khi lấy dữ liệu - {type(e).__name__}: {e}")
        sys.exit(1)

    # ========================================
    # 2. KIỂM TRA TÍNH CHỈ BÁO (INDICATORS)
    # ========================================
    print("\n2️⃣  Kiểm tra tính toán chỉ báo kỹ thuật...")
    
    try:
        df = calculate_indicators(df)
        
        # Các chỉ báo thực tế trong indicators.py
        indicator_cols = ['RSI', 'MACD', 'Signal', 'SMA20', 'VolMA20']
        missing = [col for col in indicator_cols if col not in df.columns]
        
        if missing:
            print(f"❌ FAILED: Thiếu chỉ báo: {missing}")
            sys.exit(1)
            
        print(f"✅ Tính chỉ báo thành công!")
        last = df.iloc[-1]
        print(f"   • RSI: {last['RSI']:.1f}")
        print(f"   • MACD: {last['MACD']:.2f}")
        
    except Exception as e:
        print(f"❌ FAILED: Lỗi tính chỉ báo - {type(e).__name__}: {e}")
        sys.exit(1)

    # ========================================
    # 3. KIỂM TRA LOGIC LỌC & TÍNH ĐIỂM
    # ========================================
    print("\n3️⃣  Kiểm tra logic lọc và tính điểm...")
    
    try:
        # Test bộ lọc
        investable = is_investable(df)
        print(f"   • is_investable: {investable}")
        
        # Test tính điểm
        score, reasons = check_signals(df)
        print(f"   • Score: {score}")
        print(f"   • Reasons: {reasons if reasons else 'Không có tín hiệu'}")
        
        print("✅ Logic hoạt động bình thường!")
        
    except Exception as e:
        print(f"❌ FAILED: Lỗi logic - {type(e).__name__}: {e}")
        sys.exit(1)

    # ========================================
    # KẾT THÚC
    # ========================================
    print("\n" + "=" * 50)
    print("🎉 HEALTH CHECK PASSED!")
    print("   Hệ thống sẵn sàng để chạy quét chính.")
    print("=" * 50)
    sys.exit(0)


if __name__ == "__main__":
    main()
