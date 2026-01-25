import os

# --- CẤU HÌNH TELEGRAM ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# --- VNSTOCK CONFIG ---
VNSTOCK_API_KEY = os.environ.get('VNSTOCK_API_KEY', 'vnstock_403a1c3ae1fcce8c5d68dd50aabd5c39')
DATA_SOURCE = 'VCI'  # Nguồn dữ liệu ưu tiên

# --- DANH MỤC THEO DÕI (VN30 + Mã Hot) ---
WATCHLIST = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
    "DGW", "DXG", "DIG", "PDR", "VIX", "HCM", "VND"
]

# --- BỘ LỌC ---
MIN_VOLUME_VALUE = 1_000_000_000  # 1 Tỷ VNĐ/phiên
MIN_PRICE = 10000                 # Giá > 10k

# --- NGƯỠNG TÍN HIỆU ---
MIN_SCORE = 4  # Điểm tối thiểu để báo tin

# --- LỌC THANH KHOẢN UPCOM ---
# Chỉ cảnh báo mã UPCOM có giao dịch >= 5 tỷ VNĐ/phiên
UPCOM_HIGH_LIQUIDITY_THRESHOLD = 5_000_000_000
