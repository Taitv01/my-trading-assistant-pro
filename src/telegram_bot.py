"""
Telegram Command Bot Module
Cho phép điều khiển bot qua các lệnh Telegram
Commands: /scan, /top10, /status, /performance, /help
"""
import os
import sys
import asyncio

# Thêm path để import được src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import TELEGRAM_TOKEN, CHAT_ID, VNSTOCK_API_KEY
from .data_fetcher import fetch_data
from .indicators import calculate_indicators, check_signals, check_sell_signals
from .filters import is_investable
from .price_target import calculate_price_targets, format_price_target
from .tracker import get_performance_stats, format_performance_report
from .notifier import get_rsi_status


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /scan <MÃ> - Quét nhanh 1 mã cổ phiếu
    Ví dụ: /scan FPT
    """
    if not context.args:
        await update.message.reply_text("⚠️ Cú pháp: /scan <MÃ>\nVí dụ: /scan FPT")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"🔍 Đang quét {symbol}...")

    try:
        # Fetch & analyze
        df = fetch_data(symbol)
        if df is None:
            await update.message.reply_text(f"❌ Không lấy được dữ liệu cho {symbol}")
            return

        df = calculate_indicators(df)
        last = df.iloc[-1]

        # Buy signals
        buy_score, buy_reasons = check_signals(df)
        # Sell signals
        sell_score, sell_reasons = check_sell_signals(df)
        # Price targets
        pt = calculate_price_targets(df, 'buy' if buy_score > sell_score else 'sell')

        # Investable check
        investable = is_investable(df)
        rsi_status = get_rsi_status(last['RSI'])

        # Format message
        fireant_link = f"https://fireant.vn/ma-co-phieu/{symbol}"
        
        lines = [
            f"📊 **PHÂN TÍCH: {symbol}**",
            "",
            f"💰 Giá: {last['close']:,.0f} VNĐ",
            f"📈 RSI: {last['RSI']:.0f} {rsi_status}",
            f"📉 MACD: {last['MACD']:.2f}",
            f"📊 ADX: {last['ADX']:.0f}",
            "",
            f"🟢 Điểm MUA: {buy_score}/14",
        ]

        if buy_reasons:
            lines.append(f"   💡 {', '.join(buy_reasons)}")

        lines.append(f"🔴 Điểm BÁN: {sell_score}/13")
        if sell_reasons:
            lines.append(f"   💡 {', '.join(sell_reasons)}")

        lines.extend([
            "",
            format_price_target(pt, 'buy' if buy_score > sell_score else 'sell'),
            "",
        ])

        # Verdict
        if buy_score >= 7:
            lines.append("✅ **KHUYẾN NGHỊ: MUA**")
        elif sell_score >= 7:
            lines.append("📉 **KHUYẾN NGHỊ: BÁN**")
        elif buy_score >= 4:
            lines.append("👀 **KHUYẾN NGHỊ: THEO DÕI**")
        else:
            lines.append("⏸️ **KHUYẾN NGHỊ: CHỜ**")

        if not investable:
            lines.append("⚠️ _Thanh khoản thấp - Cẩn trọng!_")

        lines.extend([
            "",
            f"🔗 [Xem trên Fireant]({fireant_link})",
            "_📌 Phân tích kỹ thuật, không phải khuyến nghị đầu tư._",
        ])

        msg = "\n".join(lines)
        await update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi quét {symbol}: {e}")


async def cmd_top10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /top10 - Xem top 10 cổ phiếu có tín hiệu mạnh nhất (VN30)
    """
    from .config import WATCHLIST

    await update.message.reply_text("🔍 Đang quét VN30... Vui lòng chờ ~2 phút")

    results = []
    import time

    for symbol in WATCHLIST:
        try:
            df = fetch_data(symbol)
            if df is None:
                time.sleep(1.2)
                continue

            df = calculate_indicators(df)
            if not is_investable(df):
                time.sleep(1.2)
                continue

            score, reasons = check_signals(df)
            if score > 0:
                last = df.iloc[-1]
                results.append({
                    'symbol': symbol,
                    'score': score,
                    'reasons': reasons,
                    'price': last['close'],
                    'rsi': last['RSI'],
                })
            time.sleep(1.2)
        except Exception:
            continue

    results.sort(key=lambda x: x['score'], reverse=True)
    top10 = results[:10]

    if not top10:
        await update.message.reply_text("💤 Không có tín hiệu mua trong VN30.")
        return

    lines = ["🏆 **TOP 10 TÍN HIỆU VN30**", ""]
    for i, stock in enumerate(top10, 1):
        rsi_status = get_rsi_status(stock['rsi'])
        reasons_str = ", ".join(stock['reasons'][:2])
        lines.append(
            f"{i}. **{stock['symbol']}** | ⭐ {stock['score']} | "
            f"{stock['price']:,.0f} | RSI {stock['rsi']:.0f} {rsi_status}"
        )
        lines.append(f"   💡 {reasons_str}")
        lines.append("")

    lines.append("_📌 Phân tích kỹ thuật, không phải khuyến nghị đầu tư._")
    msg = "\n".join(lines)
    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /status - Kiểm tra trạng thái bot
    """
    from datetime import datetime
    import pytz
    tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz_vn)

    api_tier = "Community" if VNSTOCK_API_KEY else "Guest"
    
    lines = [
        "🤖 **TRẠNG THÁI BOT**",
        "",
        f"⏰ Thời gian: {now.strftime('%d/%m/%Y %H:%M')}",
        f"✅ Bot đang hoạt động",
        f"🔑 API tier: {api_tier}",
        f"📊 Phiên bản: v1.2.0",
        "",
        "📋 **Lịch quét tự động:**",
        "• Quick Scan: Mỗi 30 phút (9h-15h)",
        "• Full Scan: 10:00, 11:30, 14:00",
        "• Discovery: 15:30 hàng ngày",
    ]

    msg = "\n".join(lines)
    await update.message.reply_text(msg, parse_mode='Markdown')


async def cmd_performance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /performance - Xem hiệu suất bot
    """
    report = format_performance_report()
    await update.message.reply_text(report, parse_mode='Markdown')


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help - Hướng dẫn sử dụng
    """
    lines = [
        "📖 **HƯỚNG DẪN SỬ DỤNG BOT**",
        "",
        "🔍 /scan <MÃ> - Quét nhanh 1 mã",
        "   _Ví dụ: /scan FPT_",
        "",
        "🏆 /top10 - Top 10 tín hiệu VN30",
        "",
        "📊 /performance - Xem hiệu suất bot",
        "",
        "🤖 /status - Trạng thái bot",
        "",
        "📖 /help - Xem hướng dẫn này",
        "",
        "💡 **Giải thích điểm số:**",
        "• ⭐ Score MUA ≥ 7: Tín hiệu mạnh",
        "• ⭐ Score MUA 4-6: Theo dõi",
        "• 📉 Score BÁN ≥ 7: Cảnh báo bán",
        "",
        "_Antigravity Trading Bot v1.2.0_",
    ]

    msg = "\n".join(lines)
    await update.message.reply_text(msg, parse_mode='Markdown')


def run_bot():
    """Khởi chạy Telegram bot (polling mode)"""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN chưa được cấu hình!")
        return

    print("🤖 Starting Telegram Command Bot...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("top10", cmd_top10))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("performance", cmd_performance))
    app.add_handler(CommandHandler("help", cmd_help))

    print("✅ Bot started! Listening for commands...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
