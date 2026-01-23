# config.py
import os
from datetime import datetime, timedelta

# --- CẤU HÌNH TELEGRAM ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- CẤU HÌNH DỮ LIỆU ---
def get_start_date(days_back=365):
    """Tự động lấy ngày bắt đầu (Dynamic, không hardcode)"""
    return (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

def get_today_date():
    return (datetime.now() + timedelta(hours=7)).strftime('%Y-%m-%d') # Giờ VN

# --- CẤU HÌNH CHIẾN LƯỢC ---
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MIN_SCORE = 3  # Chỉ báo tín hiệu khi đạt ít nhất 3 điểm (Giảm nhiễu)

# --- DANH SÁCH THEO DÕI (Hardcode tạm thời, có thể nâng cấp lấy API sau) ---
DEFAULT_WATCHLIST = [
    "HPG", "SSI", "STB", "VND", "DGW", "MWG", "FPT", "DIG", "PDR", "NVL",
    "VPB", "TCB", "MBB", "ACB", "VHM", "VIC", "VRE", "GAS", "VNM", "MSN"
]
