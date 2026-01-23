import os
from datetime import datetime, timedelta

# --- CẤU HÌNH TELEGRAM ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- CẤU HÌNH DỮ LIỆU ---
def get_date_range(days=365):
    """Lấy vùng dữ liệu (Mặc định 1 năm)"""
    end = (datetime.utcnow() + timedelta(hours=7)).strftime('%Y-%m-%d')
    start = (datetime.utcnow() + timedelta(hours=7) - timedelta(days=days)).strftime('%Y-%m-%d')
    return start, end

# --- BỘ LỌC CƠ BẢN ---
MIN_PRICE = 5000               # Giá > 5.000 VND
MIN_VOL_VALUE = 2_000_000_000  # GTGD TB > 2 tỷ (Lọc kỹ hơn để tránh rác)
MIN_DAYS = 100                 # Đã niêm yết > 100 ngày

# --- CẤU HÌNH CHẤM ĐIỂM & RANKING (PHẦN BẠN ĐANG THIẾU) ---
MIN_SCORE_TO_ALERT = 7    # Điểm tối thiểu để được báo cáo (Thang 10)
TOP_RANKING = 20          # Lấy Top 20 mã ngon nhất thị trường để báo cáo
