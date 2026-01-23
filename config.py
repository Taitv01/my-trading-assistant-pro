import os
from datetime import datetime, timedelta

# --- SYSTEM ---
LOG_FILE = "bot.log"
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- DATA ---
def get_date_range(days=365):
    end = (datetime.utcnow() + timedelta(hours=7)).strftime('%Y-%m-%d')
    start = (datetime.utcnow() + timedelta(hours=7) - timedelta(days=days)).strftime('%Y-%m-%d')
    return start, end

# --- FILTERS (QUAN TRỌNG KHI QUÉT FULL MARKET) ---
MIN_PRICE = 5000               # Bỏ qua cổ phiếu trà đá < 5k
MIN_VOL_VALUE = 3_000_000_000  # GTGD TB > 3 Tỷ/phiên (Nâng cao lên để lọc nhiễu UPCOM)
MIN_DAYS = 120                 # Niêm yết > 6 tháng

# --- SCORING ---
MIN_SCORE_TO_ALERT = 7.0
TOP_RANKING = 10               # Tăng lên Top 10 vì quét nhiều mã hơn
