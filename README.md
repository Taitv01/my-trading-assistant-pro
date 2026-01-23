# My Trading Assistant Pro

Bot tự động quét tín hiệu kỹ thuật và dòng tiền cho thị trường chứng khoán Việt Nam (HOSE, HNX, UPCOM).

## Tính năng chính
- Quét danh sách cổ phiếu (VN30 hoặc watchlist tùy chỉnh).
- Phân tích RSI (14), MACD, volume breakout.
- Phát hiện tín hiệu mua tiềm năng.
- Vẽ biểu đồ giá + RSI.
- Gửi thông báo + ảnh qua Telegram.
- Chạy tự động qua GitHub Actions (lịch trình hàng ngày).

## Yêu cầu
- Python 3.8+
- Thư viện: vnstock, pandas, matplotlib, requests

## Cài đặt & Cấu hình
1. Fork/Clonet repo.
2. Tạo bot Telegram qua @BotFather → lấy `TELEGRAM_BOT_TOKEN`.
3. Lấy `TELEGRAM_CHAT_ID` của channel/group.
4. Trong GitHub repo → Settings → Secrets and variables → Actions → Thêm 2 secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

## Cách chạy local
```bash
pip install vnstock pandas matplotlib requests
python bot.py
