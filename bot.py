name: Bot Chung Khoan Auto 30p

on:
  schedule:
    # -----------------------------------------------------------
    # GIẢI THÍCH LỊCH CHẠY (CRON SCHEDULE)
    # Giờ Việt Nam (VN) = Giờ UTC + 7
    # Cấu trúc: 'phút giờ ngày tháng thứ'
    # -----------------------------------------------------------
    # Chạy vào phút 15 và 45, từ 2h đến 7h UTC (Tức 9h đến 14h VN)
    # Các mốc giờ VN sẽ chạy:
    # 09:15, 09:45
    # 10:15, 10:45
    # ...
    # 14:15, 14:45 (Kết thúc phiên)
    # -----------------------------------------------------------
    - cron: '15,45 2-7 * * 1-5'

  # Cho phép bấm nút chạy thủ công để test bất cứ lúc nào
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest

    steps:
    - name: Tải code về máy ảo
      uses: actions/checkout@v3

    - name: Cài đặt Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Cài thư viện cần thiết
      run: |
        pip install pandas requests vnstock

    - name: Chạy Bot
      env: 
        # Lấy "Chìa khóa" từ mục Settings > Secrets của GitHub
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
      run: python bot.py
