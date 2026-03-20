"""
Performance Tracker Module
Theo dõi hiệu suất các tín hiệu đã phát
Lưu lịch sử tín hiệu và tính toán kết quả
"""
import json
import os
from datetime import datetime
import pytz


# File lưu trữ tín hiệu
SIGNALS_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'signals_history.json')


def _ensure_data_dir():
    """Tạo thư mục data nếu chưa có"""
    data_dir = os.path.dirname(SIGNALS_DB_PATH)
    os.makedirs(data_dir, exist_ok=True)


def _load_signals():
    """Load tín hiệu từ file JSON"""
    if not os.path.exists(SIGNALS_DB_PATH):
        return []
    try:
        with open(SIGNALS_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_signals(signals):
    """Lưu tín hiệu vào file JSON"""
    _ensure_data_dir()
    with open(SIGNALS_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(signals, f, ensure_ascii=False, indent=2, default=str)


def record_signal(symbol, signal_type, score, reasons, price, target_price=None, stop_loss=None):
    """
    Ghi nhận một tín hiệu mới.
    
    Args:
        symbol: Mã cổ phiếu
        signal_type: 'buy' hoặc 'sell'
        score: Điểm tín hiệu
        reasons: List các lý do
        price: Giá tại thời điểm phát tín hiệu
        target_price: Giá mục tiêu (optional)
        stop_loss: Mức cắt lỗ (optional)
    """
    tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz_vn)
    
    signal = {
        'id': f"{symbol}_{signal_type}_{now.strftime('%Y%m%d_%H%M')}",
        'symbol': symbol,
        'type': signal_type,
        'score': score,
        'reasons': reasons,
        'entry_price': price,
        'target_price': target_price,
        'stop_loss': stop_loss,
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%H:%M'),
        'status': 'active',  # active, hit_target, hit_stoploss, expired
        'result': None,  # sẽ cập nhật sau
        'result_pct': None,
        'days_held': 0,
    }
    
    signals = _load_signals()
    signals.append(signal)
    
    # Giới hạn lưu tối đa 500 tín hiệu gần nhất
    if len(signals) > 500:
        signals = signals[-500:]
    
    _save_signals(signals)
    print(f"📝 Recorded {signal_type} signal: {symbol} @ {price:,.0f}")
    
    return signal


def update_signal_results(fetch_data_func):
    """
    Cập nhật kết quả các tín hiệu đang active.
    Gọi hàm này mỗi ngày để theo dõi hiệu suất.
    
    Args:
        fetch_data_func: Hàm fetch_data để lấy giá hiện tại
    """
    signals = _load_signals()
    updated = 0
    
    for signal in signals:
        if signal['status'] != 'active':
            continue
            
        symbol = signal['symbol']
        entry_price = signal['entry_price']
        
        try:
            df = fetch_data_func(symbol, days=30)
            if df is None or df.empty:
                continue
                
            current_price = df.iloc[-1]['close']
            
            # Tính số ngày đã hold
            entry_date = datetime.strptime(signal['date'], '%Y-%m-%d')
            tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')
            now = datetime.now(tz_vn).replace(tzinfo=None)
            signal['days_held'] = (now - entry_date).days
            
            if signal['type'] == 'buy':
                result_pct = ((current_price - entry_price) / entry_price) * 100
                
                # Check hit target
                if signal.get('target_price') and current_price >= signal['target_price']:
                    signal['status'] = 'hit_target'
                    signal['result'] = 'WIN'
                    signal['result_pct'] = result_pct
                
                # Check hit stop loss
                elif signal.get('stop_loss') and current_price <= signal['stop_loss']:
                    signal['status'] = 'hit_stoploss'
                    signal['result'] = 'LOSS'
                    signal['result_pct'] = result_pct
                    
                # Expire after 20 trading days
                elif signal['days_held'] >= 30:
                    signal['status'] = 'expired'
                    signal['result'] = 'WIN' if result_pct > 0 else 'LOSS'
                    signal['result_pct'] = result_pct
                    
            else:  # sell
                result_pct = ((entry_price - current_price) / entry_price) * 100
                
                if signal.get('target_price') and current_price <= signal['target_price']:
                    signal['status'] = 'hit_target'
                    signal['result'] = 'WIN'
                    signal['result_pct'] = result_pct
                    
                elif signal.get('stop_loss') and current_price >= signal['stop_loss']:
                    signal['status'] = 'hit_stoploss'
                    signal['result'] = 'LOSS'
                    signal['result_pct'] = result_pct
                    
                elif signal['days_held'] >= 30:
                    signal['status'] = 'expired'
                    signal['result'] = 'WIN' if result_pct > 0 else 'LOSS'
                    signal['result_pct'] = result_pct
                    
            updated += 1
            
        except Exception as e:
            print(f"Error updating {symbol}: {e}")
            continue
    
    _save_signals(signals)
    print(f"📊 Updated {updated} active signals")
    return signals


def get_performance_stats():
    """
    Tính toán thống kê hiệu suất tổng thể.
    
    Returns:
        dict with win_rate, avg_return, total_signals, etc.
    """
    signals = _load_signals()
    
    if not signals:
        return {
            'total_signals': 0,
            'active': 0,
            'completed': 0,
            'win_rate': 0.0,
            'avg_return': 0.0,
            'best_signal': None,
            'worst_signal': None,
        }
    
    completed = [s for s in signals if s['status'] != 'active']
    active = [s for s in signals if s['status'] == 'active']
    wins = [s for s in completed if s.get('result') == 'WIN']
    losses = [s for s in completed if s.get('result') == 'LOSS']
    
    # Win rate
    win_rate = (len(wins) / len(completed) * 100) if completed else 0.0
    
    # Average return
    returns = [s.get('result_pct', 0) for s in completed if s.get('result_pct') is not None]
    avg_return = sum(returns) / len(returns) if returns else 0.0
    
    # Best & worst
    best = max(completed, key=lambda x: x.get('result_pct', 0)) if completed else None
    worst = min(completed, key=lambda x: x.get('result_pct', 0)) if completed else None
    
    return {
        'total_signals': len(signals),
        'active': len(active),
        'completed': len(completed),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': win_rate,
        'avg_return': avg_return,
        'best_signal': best,
        'worst_signal': worst,
        'hit_target_count': len([s for s in completed if s['status'] == 'hit_target']),
        'hit_stoploss_count': len([s for s in completed if s['status'] == 'hit_stoploss']),
    }


def format_performance_report():
    """Format báo cáo hiệu suất cho Telegram"""
    stats = get_performance_stats()
    
    if stats['total_signals'] == 0:
        return "📊 Chưa có dữ liệu hiệu suất."
    
    lines = [
        "📊 **BÁO CÁO HIỆU SUẤT BOT**",
        "",
        f"📋 Tổng tín hiệu: {stats['total_signals']}",
        f"🟢 Đang theo dõi: {stats['active']}",
        f"✅ Đã hoàn thành: {stats['completed']}",
        "",
    ]
    
    if stats['completed'] > 0:
        # Win rate emoji
        if stats['win_rate'] >= 60:
            wr_emoji = "🔥"
        elif stats['win_rate'] >= 45:
            wr_emoji = "✅"
        else:
            wr_emoji = "⚠️"
            
        lines.extend([
            f"{wr_emoji} Win Rate: {stats['win_rate']:.1f}%",
            f"📈 Lãi TB: {stats['avg_return']:+.1f}%",
            f"🎯 Hit Target: {stats['hit_target_count']}",
            f"🛑 Hit Stop Loss: {stats['hit_stoploss_count']}",
        ])
        
        if stats['best_signal']:
            b = stats['best_signal']
            lines.append(f"🏆 Best: {b['symbol']} ({b.get('result_pct', 0):+.1f}%)")
        if stats['worst_signal']:
            w = stats['worst_signal']
            lines.append(f"💀 Worst: {w['symbol']} ({w.get('result_pct', 0):+.1f}%)")
    
    lines.extend([
        "",
        "_📌 Hiệu suất quá khứ không đảm bảo kết quả tương lai._"
    ])
    
    return "\n".join(lines)
