# My Trading Assistant Pro 📈

> Automated stock scanner for Vietnam market (HOSE, HNX, UPCOM) with Telegram alerts.

## Features

| Mode | Description | Schedule |
|------|-------------|----------|
| **Quick Scan** | VN30 stocks only | Every 30 minutes (9AM-3PM) |
| **Full Scan** | All 3 exchanges (~1,700 stocks) | 10:00, 13:00, 15:00 |

### Technical Indicators
- RSI (14) - Relative Strength Index
- MACD (12, 26, 9) - Moving Average Convergence Divergence
- Bollinger Bands (20, 2)
- Volume Breakout Detection

### Signal Scoring System
| Signal | Points |
|--------|--------|
| Volume Spike (>1.3x MA20) | +2 |
| MACD Golden Cross | +3 |
| Price Cross MA20 | +2 |
| RSI in optimal zone (40-60) | +1 |

Minimum score for alert: **4 points**

## Quick Start

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/my-trading-assistant-pro.git
cd my-trading-assistant-pro
```

### 2. Configure Telegram Bot
1. Create bot via [@BotFather](https://t.me/BotFather) → Get `TELEGRAM_BOT_TOKEN`
2. Get your `TELEGRAM_CHAT_ID` from [@userinfobot](https://t.me/userinfobot)

### 3. Add GitHub Secrets
Go to: **Settings** → **Secrets and variables** → **Actions**

| Secret | Value |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token |
| `TELEGRAM_CHAT_ID` | Your chat/group ID |

### 4. Enable GitHub Actions
The bot will run automatically on schedule!

## Local Development

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run Quick Scan
python scanner.py --mode quick

# Run Full Scan
python scanner.py --mode full
```

## Project Structure

```
my-trading-assistant-pro/
├── scanner.py              # Main entry point
├── src/
│   ├── config.py           # Configuration (watchlist, thresholds)
│   ├── data_fetcher.py     # Price data from vnstock
│   ├── indicators.py       # Technical indicators calculation
│   ├── filters.py          # Liquidity/price filters
│   ├── market_scanner.py   # Full market scan logic
│   └── notifier.py         # Telegram notifications
├── .github/workflows/
│   ├── quick_scan.yml      # VN30 every 30 min
│   └── full_scan.yml       # All markets 3x/day
└── requirements.txt
```

## Requirements
- Python 3.9+
- Dependencies: vnstock, pandas, matplotlib, python-telegram-bot

## License
MIT

---
Made with ❤️ for Vietnam stock traders
