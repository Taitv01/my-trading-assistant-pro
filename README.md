# My Trading Assistant Pro 📈

> Hệ thống quét cổ phiếu tự động cho thị trường Việt Nam (HOSE, HNX, UPCOM) với cảnh báo Telegram.

[![Quick Scan](https://github.com/Taitv01/my-trading-assistant-pro/actions/workflows/quick_scan.yml/badge.svg)](https://github.com/Taitv01/my-trading-assistant-pro/actions/workflows/quick_scan.yml)
[![Full Scan](https://github.com/Taitv01/my-trading-assistant-pro/actions/workflows/full_scan.yml/badge.svg)](https://github.com/Taitv01/my-trading-assistant-pro/actions/workflows/full_scan.yml)

## ✨ Tính năng

### Chế độ quét

| Mode               | Mô tả                              | Lịch chạy             | Thời gian |
| ------------------ | ---------------------------------- | --------------------- | --------- |
| **Quick Scan**     | Top 30 cổ phiếu thanh khoản (VN30) | Mỗi 30 phút (9AM-3PM) | ~2 phút   |
| **Full Scan**      | Top 132 cổ phiếu thanh khoản cao   | 10:00, 13:00, 15:00   | ~6 phút   |
| **Discovery Scan** | Toàn thị trường (~1,700 mã)        | 13:30 hàng ngày       | ~85 phút  |

### Chỉ báo kỹ thuật

- **RSI (14)** - Relative Strength Index
- **MACD (12, 26, 9)** - Moving Average Convergence Divergence
- **Bollinger Bands (20, 2)** - Dải băng Bollinger
- **Volume Breakout** - Phát hiện đột biến khối lượng

### Hệ thống tính điểm

| Tín hiệu                      | Điểm |
| ----------------------------- | ---- |
| Volume đột biến (>1.3x MA20)  | +2   |
| MACD Golden Cross             | +3   |
| Giá vượt MA20                 | +2   |
| RSI trong vùng tối ưu (40-60) | +1   |

> **Ngưỡng cảnh báo:** Tối thiểu **4 điểm**

### Tính năng nâng cao

- ✅ **Smart Filter** - Loc Top 132 mã thanh khoản cao từ cả 3 sàn
- ✅ **UPCOM Filter** - Chỉ chọn UPCOM có khối lượng giao dịch >5 tỷ/phiên
- ✅ **Checkpoint System** - Lưu tiến độ, tự động resume nếu bị cancel
- ✅ **Rate Limit Handling** - Xử lý thông minh giới hạn API

---

## 🚀 Bắt đầu nhanh

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/my-trading-assistant-pro.git
cd my-trading-assistant-pro
```

### 2. Cấu hình Telegram Bot

1. Tạo bot qua [@BotFather](https://t.me/BotFather) → Lấy `TELEGRAM_BOT_TOKEN`
2. Lấy `TELEGRAM_CHAT_ID` từ [@userinfobot](https://t.me/userinfobot)

### 3. Thêm GitHub Secrets

Vào: **Settings** → **Secrets and variables** → **Actions**

| Secret               | Giá trị       |
| -------------------- | ------------- |
| `TELEGRAM_BOT_TOKEN` | Token của bot |
| `TELEGRAM_CHAT_ID`   | ID chat/group |

### 4. Kích hoạt GitHub Actions

Bot sẽ tự động chạy theo lịch!

---

## 💻 Phát triển local

```bash
# Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy các chế độ quét
python scanner.py --mode quick      # VN30 (~2 phút)
python scanner.py --mode full       # Top thanh khoản (~6 phút)
python scanner.py --mode discovery  # Toàn thị trường (~85 phút)
```

---

## 📁 Cấu trúc dự án

```
my-trading-assistant-pro/
├── scanner.py                  # Entry point chính
├── src/
│   ├── config.py               # Cấu hình (watchlist, ngưỡng)
│   ├── data_fetcher.py         # Lấy dữ liệu giá từ vnstock
│   ├── indicators.py           # Tính toán chỉ báo kỹ thuật
│   ├── filters.py              # Bộ lọc thanh khoản/giá
│   ├── smart_filter.py         # Smart watchlist logic
│   ├── market_scanner.py       # Logic quét Full Scan
│   ├── discovery_scanner.py    # Logic quét Discovery Scan
│   └── notifier.py             # Gửi thông báo Telegram
├── .github/workflows/
│   ├── quick_scan.yml          # VN30 mỗi 30 phút
│   └── full_scan.yml           # Top thanh khoản 3x/ngày
└── requirements.txt
```

---

## ⚙️ Yêu cầu hệ thống

- Python 3.9+
- Dependencies: `vnstock`, `pandas`, `matplotlib`, `python-telegram-bot`

## 📝 Changelog

### v1.1.0 (2026-01-25)

- ✨ Thêm **Discovery Scan** - quét toàn thị trường
- ✨ Thêm **Checkpoint System** - tự động lưu và resume tiến độ
- ✨ Thêm **Smart Filter** - chọn top mã thanh khoản thông minh
- 🐛 Cải thiện xử lý lỗi API (ValueError, RetryError)
- ⚡ Tăng độ ổn định với API delay 3s

### v1.0.0

- 🎉 Phiên bản đầu tiên
- Quick Scan (VN30)
- Full Scan (All Markets)
- Telegram notifications

## 📄 License

MIT

---

Made with ❤️ for Vietnam stock traders
