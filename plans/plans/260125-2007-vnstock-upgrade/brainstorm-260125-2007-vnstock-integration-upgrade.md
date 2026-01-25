# Brainstorm Report: vnstock Integration Upgrade

**Date:** 2026-01-25
**Project:** my-trading-assistant-pro
**Status:** Analysis Complete

---

## 1. Problem Statement

Project hiện tại sử dụng vnstock API cũ (v1.x/v2.x) đã deprecated. Cần upgrade lên vnstock 3.x API mới để:
- Đảm bảo bot chạy ổn định không bị lỗi
- Mở rộng khả năng scrape dữ liệu
- Quét toàn bộ sàn HOSE/HNX/UPCOM thay vì watchlist cố định

---

## 2. Current State Analysis

### 2.1 Code Issues Found

| File | Issue | Severity |
|------|-------|----------|
| `data_fetcher.py:2` | `from vnstock import stock_historical_data` - Hàm đã deprecated | **CRITICAL** |
| `data_fetcher.py:12` | `stock_historical_data(symbol, start_date, end_date, "1D", "stock")` - API cũ | **CRITICAL** |
| `config.py` | Hardcoded WATCHLIST 37 mã | Medium |
| `bot.py` | Không parse `--exchange` argument | Medium |
| `hnx_scan.yml` | Thiếu setup steps, syntax error | High |
| `upcom_scan.yml` | Thiếu setup steps, syntax error | High |
| `main.yml:32` | Indentation error tại `env:` | High |

### 2.2 vnstock API Changes (v1/v2 → v3.x)

**Old API (deprecated):**
```python
from vnstock import stock_historical_data
df = stock_historical_data("VCI", "2024-01-01", "2024-12-31", "1D", "stock")
```

**New API (vnstock 3.x):**
```python
from vnstock import Quote
quote = Quote(symbol='VCI', source='KBS')
df = quote.history(start='2024-01-01', end='2024-12-31', interval='D')
```

### 2.3 vnstock 3.x Features Available

| Feature | Class | Methods |
|---------|-------|---------|
| Giá lịch sử | `Quote` | `history()`, `intraday()`, `price_depth()` |
| Listing symbols | `Listing` | `all_symbols()`, `symbols_by_exchange()`, `symbols_by_group()` |
| Thông tin công ty | `Company` | `overview()`, `profile()`, `shareholders()` |
| Báo cáo tài chính | `Finance` | `balance_sheet()`, `income_statement()`, `cash_flow()`, `ratio()` |
| Bảng giá | `Trading` | `price_board()` |

### 2.4 Rate Limits (vnstock 3.4.0+)

| Tier | Requests/min | Financial Periods | Cost |
|------|-------------|-------------------|------|
| Guest | 20 | 4 kỳ | Free |
| Community | 60 | 8 kỳ | Free (cần API key) |
| Sponsor | 180+ | Unlimited | Paid |

---

## 3. Proposed Solution

### 3.1 Architecture Overview

```
my-trading-assistant-pro/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main entry, argument parsing
│   ├── config.py           # Settings, env vars, API key placeholder
│   ├── data/
│   │   ├── __init__.py
│   │   ├── fetcher.py      # NEW: vnstock 3.x wrapper
│   │   ├── listing.py      # NEW: Get symbols by exchange
│   │   └── financial.py    # NEW: Financial data fetcher
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── indicators.py   # Technical indicators (enhanced)
│   │   ├── signals.py      # Signal detection logic
│   │   └── filters.py      # Stock filtering rules
│   ├── notification/
│   │   ├── __init__.py
│   │   ├── telegram.py     # Telegram alerts
│   │   └── templates.py    # Message templates
│   └── utils/
│       ├── __init__.py
│       └── rate_limiter.py # NEW: Rate limiting helper
├── .github/workflows/
│   ├── hose_scan.yml       # HOSE scanning job
│   ├── hnx_scan.yml        # HNX scanning job
│   └── upcom_scan.yml      # UPCOM scanning job
├── requirements.txt
└── README.md
```

### 3.2 Key Changes

#### Phase 1: Fix Critical Issues (Sửa lỗi cấp bách)
1. Update `data_fetcher.py` → Use vnstock 3.x `Quote` class
2. Fix YAML syntax errors in workflow files
3. Add argument parsing for `--exchange`

#### Phase 2: Expand Data Sources (Mở rộng dữ liệu)
1. Add `Listing` integration để lấy danh sách symbols động
2. Add `Finance` integration cho báo cáo tài chính
3. Add intraday/price_board data fetching

#### Phase 3: Enhance Analysis (Cải tiến phân tích)
1. Thêm chỉ báo mới: Stochastic, ADX, OBV, MFI
2. Improve scoring system với weighted factors
3. Add summary report aggregation

#### Phase 4: Production Ready (Hoàn thiện)
1. Add rate limiting với delay between requests
2. Add error handling và retry logic
3. Add API key configuration guide

### 3.3 New Data Fetcher Design

```python
# src/data/fetcher.py
from vnstock import Quote, Listing, Finance
from datetime import datetime, timedelta

class VnstockClient:
    """Wrapper for vnstock 3.x API"""

    def __init__(self, source='KBS'):
        self.source = source

    def get_symbols_by_exchange(self, exchange: str) -> list:
        """Get all symbols from HOSE/HNX/UPCOM"""
        listing = Listing(source=self.source)
        df = listing.symbols_by_exchange()
        return df[df['exchange'] == exchange]['symbol'].tolist()

    def get_historical_data(self, symbol: str, days: int = 365):
        """Get OHLCV data using new API"""
        quote = Quote(symbol=symbol, source=self.source)
        end = datetime.now().strftime('%Y-%m-%d')
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return quote.history(start=start, end=end, interval='D')

    def get_financial_ratios(self, symbol: str):
        """Get financial ratios for fundamental analysis"""
        finance = Finance(symbol=symbol, source=self.source)
        return finance.ratio(period='quarter')
```

### 3.4 GitHub Actions Strategy

**Chia thành 3 workflows riêng biệt:**

| Workflow | Schedule (UTC) | Schedule (VN) | Symbols |
|----------|---------------|---------------|---------|
| hose_scan | `15 2 * * 1-5` | 9:15 AM | ~400 mã |
| hnx_scan | `30 2 * * 1-5` | 9:30 AM | ~350 mã |
| upcom_scan | `45 2 * * 1-5` | 9:45 AM | ~800 mã |

**Rate limit handling:**
- 60 requests/min với Community API key
- UPCOM (~800 mã) cần ~15 phút nếu không có delay
- Recommend: Thêm 0.5s delay giữa mỗi request

### 3.5 New Technical Indicators

| Indicator | Formula | Signal Weight |
|-----------|---------|---------------|
| RSI (14) | Existing | +1 nếu 40 < RSI < 60 |
| MACD | Existing | +3 nếu Golden Cross |
| Bollinger | Existing | +2 nếu vượt MA20 |
| Volume | Existing | +2 nếu Vol > 1.3x MA20 |
| **Stochastic (14,3)** | NEW | +2 nếu %K cross %D từ oversold |
| **ADX (14)** | NEW | +1 nếu ADX > 25 (strong trend) |
| **OBV** | NEW | +1 nếu OBV divergence positive |
| **MFI (14)** | NEW | +1 nếu MFI từ oversold + tăng |

---

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limit exceeded | Bot bị block tạm thời | Implement delay + retry logic |
| vnstock API changes | Code break | Pin version trong requirements.txt |
| GitHub Actions timeout | Workflow fail | Chia nhỏ thành multiple jobs |
| Data quality issues | Sai signal | Validate data trước khi analyze |
| API key leak | Security risk | Dùng GitHub Secrets, không hardcode |

---

## 5. Implementation Estimate

| Phase | Complexity | Files Changed |
|-------|------------|---------------|
| Phase 1: Fix Critical | Medium | 4 files |
| Phase 2: Expand Data | Medium | 3 new files |
| Phase 3: Enhance Analysis | Medium | 2 files |
| Phase 4: Production | Low | 2 files |

---

## 6. Success Criteria

- [ ] Bot chạy không lỗi với vnstock 3.x
- [ ] Quét được toàn bộ HOSE/HNX/UPCOM symbols
- [ ] Lấy được dữ liệu tài chính cơ bản
- [ ] GitHub Actions chạy đúng schedule
- [ ] Telegram notification hoạt động
- [ ] Summary report cuối phiên

---

## 7. API Key Configuration Guide (Draft)

```markdown
## Hướng dẫn cấu hình API Key vnstock

1. Truy cập https://vnstocks.com/login
2. Đăng nhập bằng Google
3. Copy API key được cấp
4. Thêm vào GitHub Secrets:
   - Settings → Secrets → Actions → New secret
   - Name: `VNSTOCK_API_KEY`
   - Value: `vnstock_XXXXXX`
5. Trong code sử dụng:
   ```python
   from vnstock import register_user
   import os
   register_user(api_key=os.environ.get('VNSTOCK_API_KEY'))
   ```
```

---

## 8. Final Recommendation

**Approach:** Incremental upgrade - sửa lỗi critical trước, sau đó mở rộng dần.

**Priority:**
1. 🔴 **CRITICAL**: Fix `data_fetcher.py` để bot chạy được
2. 🟠 **HIGH**: Fix GitHub Actions YAML syntax
3. 🟡 **MEDIUM**: Add dynamic symbol listing
4. 🟢 **LOW**: Add new indicators, summary report

---

## 9. Unresolved Questions

1. **vnstock source preference**: KBS vs VCI - cần test độ ổn định và tốc độ
2. **UPCOM handling**: 800+ mã có thể exceed rate limit - cần strategy cụ thể hơn
3. **Financial data frequency**: Lấy quarterly hay yearly ratio?
4. **Error notification**: Có cần gửi Telegram khi bot gặp lỗi không?

---

## Next Steps

Nếu đồng ý với approach này, tôi sẽ tạo implementation plan chi tiết với từng phase và task cụ thể.
