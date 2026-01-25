"""
Discovery Scanner - Full market scan to discover new opportunities and industry money flow
Runs once daily at 13:30 VN time
"""
import time
import json
import os
from datetime import datetime
from collections import defaultdict
from vnstock import Listing, Quote
from .data_fetcher import fetch_data
from .indicators import calculate_indicators, check_signals
from .filters import is_investable
from .config import MIN_SCORE, UPCOM_HIGH_LIQUIDITY_THRESHOLD

# Rate limiting - Increased to 3s for better stability
API_DELAY_SECONDS = 3.0

# Batch processing settings
BATCH_SIZE = 100  # Save checkpoint every 100 stocks
CHECKPOINT_FILE = "discovery_checkpoint.json"

# Output file to store discovered stocks
DISCOVERY_CACHE_FILE = "discovery_cache.json"


def save_checkpoint(index, results, symbol_exchange_map):
    """Save current progress to checkpoint file"""
    checkpoint = {
        'last_index': index,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    try:
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, default=str)
        print(f"💾 Checkpoint saved at index {index}")
    except Exception as e:
        print(f"Warning: Could not save checkpoint: {e}")


def load_checkpoint():
    """Load previous checkpoint if exists"""
    if not os.path.exists(CHECKPOINT_FILE):
        return None
    try:
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        print(f"📂 Loaded checkpoint from index {checkpoint['last_index']} ({checkpoint['timestamp']})")
        return checkpoint
    except Exception as e:
        print(f"Warning: Could not load checkpoint: {e}")
        return None


def clear_checkpoint():
    """Clear checkpoint after successful completion"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            os.remove(CHECKPOINT_FILE)
            print("🧹 Checkpoint cleared")
        except Exception as e:
            print(f"Warning: Could not clear checkpoint: {e}")


def get_all_symbols_with_exchange():
    """
    Get all symbols with exchange info (HOSE, HNX, UPCOM).
    Returns dict mapping symbol -> exchange
    """
    try:
        listing = Listing(source='VCI')
        df = listing.symbols_by_exchange()
        
        # 'exchange' column contains: HSX, HNX, UPCOM
        if 'exchange' in df.columns and 'symbol' in df.columns:
            # Map HSX to HOSE for consistency
            exchange_map = {'HSX': 'HOSE', 'HNX': 'HNX', 'UPCOM': 'UPCOM'}
            result = {}
            for _, row in df.iterrows():
                symbol = row['symbol']
                exchange = exchange_map.get(row['exchange'], row['exchange'])
                result[symbol] = exchange
            return result
        else:
            print(f"Warning: Expected columns not found. Got: {df.columns.tolist()}")
            all_symbols = df['symbol'].tolist() if 'symbol' in df.columns else []
            return {s: 'UNKNOWN' for s in all_symbols}
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return {}


def analyze_stock_with_details(symbol, exchange='UNKNOWN'):
    """
    Analyze stock and return detailed data including volume metrics.
    
    Args:
        symbol: Stock symbol
        exchange: Exchange name (HOSE, HNX, UPCOM)
    """
    try:
        df = fetch_data(symbol)
        if df is None or len(df) < 20:
            return None
        
        df = calculate_indicators(df)
        
        # Calculate volume metrics
        last = df.iloc[-1]
        avg_vol_20 = df['volume'].tail(20).mean()
        avg_value_20 = (df['close'] * df['volume']).tail(20).mean() * 1000  # VND
        
        # Check if investable
        investable = is_investable(df)
        
        # UPCOM filtering: only include if high liquidity
        if exchange == 'UPCOM' and avg_value_20 < UPCOM_HIGH_LIQUIDITY_THRESHOLD:
            return None  # Skip low-liquidity UPCOM stocks
        
        # Get signal score
        score, reasons = check_signals(df)
        
        # Volume spike detection
        vol_ratio = last['volume'] / avg_vol_20 if avg_vol_20 > 0 else 0
        
        return {
            'symbol': symbol,
            'exchange': exchange,  # Add exchange info
            'score': score,
            'reasons': reasons,
            'price': last['close'],
            'rsi': last['RSI'],
            'macd': last['MACD'],
            'volume': last['volume'],
            'avg_value_20': avg_value_20,
            'vol_ratio': vol_ratio,
            'investable': investable,
            'has_signal': score >= MIN_SCORE
        }
    except Exception as e:
        return None


def run_discovery_scan():
    """
    Run full market discovery scan.
    Returns:
        - Top 20 stocks by score
        - Top 10 industries by money flow
        - List of new "hot" stocks not in current watchlist
    """
    print("="*50)
    print("DISCOVERY SCAN - Full Market Analysis")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Get all symbols with exchange info
    symbol_exchange_map = get_all_symbols_with_exchange()
    all_symbols = list(symbol_exchange_map.keys())
    total = len(all_symbols)
    print(f"Total symbols to scan: {total}")
    
    # Count by exchange
    exchange_counts = {}
    for ex in symbol_exchange_map.values():
        exchange_counts[ex] = exchange_counts.get(ex, 0) + 1
    print(f"Exchange breakdown: {exchange_counts}")
    
    # Try to load checkpoint
    checkpoint = load_checkpoint()
    start_index = 0
    results = []
    
    if checkpoint:
        start_index = checkpoint['last_index'] + 1
        results = checkpoint['results']
        print(f"▶️ Resuming from index {start_index} with {len(results)} previous results")
    
    # Analyze all stocks
    industry_volumes = defaultdict(lambda: {'total_value': 0, 'count': 0, 'signals': 0})
    
    # Rebuild industry_volumes from existing results
    for result in results:
        industry_key = result['symbol'][0]
        industry_volumes[industry_key]['total_value'] += result['avg_value_20']
        industry_volumes[industry_key]['count'] += 1
        if result['has_signal']:
            industry_volumes[industry_key]['signals'] += 1
    
    for i in range(start_index, total):
        symbol = all_symbols[i]
        
        if (i + 1) % 50 == 0:
            print(f"Progress: {i + 1}/{total} ({(i+1)*100/total:.1f}%)")
        
        exchange = symbol_exchange_map.get(symbol, 'UNKNOWN')
        result = analyze_stock_with_details(symbol, exchange)
        if result:
            results.append(result)
            
            # Aggregate by first letter (pseudo-industry grouping)
            industry_key = symbol[0]
            industry_volumes[industry_key]['total_value'] += result['avg_value_20']
            industry_volumes[industry_key]['count'] += 1
            if result['has_signal']:
                industry_volumes[industry_key]['signals'] += 1
        
        # Save checkpoint every BATCH_SIZE stocks
        if (i + 1) % BATCH_SIZE == 0:
            save_checkpoint(i, results, symbol_exchange_map)
    
    print(f"\nAnalyzed {len(results)} stocks successfully")
    
    # Sort by score
    results.sort(key=lambda x: (x['score'], x['avg_value_20']), reverse=True)
    
    # Top 20 stocks by score
    top_20_stocks = [r for r in results if r['has_signal']][:20]
    
    # Top stocks by volume spike (potential new opportunities)
    volume_spikes = sorted(
        [r for r in results if r['vol_ratio'] > 2.0 and r['investable']],
        key=lambda x: x['vol_ratio'],
        reverse=True
    )[:20]
    
    # Industry analysis
    industry_ranking = sorted(
        [
            {
                'industry': k,
                'total_value': v['total_value'],
                'stock_count': v['count'],
                'signal_count': v['signals'],
                'signal_ratio': v['signals'] / v['count'] if v['count'] > 0 else 0
            }
            for k, v in industry_volumes.items()
        ],
        key=lambda x: x['total_value'],
        reverse=True
    )[:10]
    
    # Prepare discovery report
    report = {
        'scan_time': datetime.now().isoformat(),
        'total_scanned': len(results),
        'top_20_stocks': top_20_stocks,
        'volume_spikes': volume_spikes,
        'top_industries': industry_ranking
    }
    
    try:
        with open(DISCOVERY_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        print(f"Discovery report saved to {DISCOVERY_CACHE_FILE}")
        # Clear checkpoint after successful completion
        clear_checkpoint()
    except Exception as e:
        print(f"Error saving cache: {e}")
    
    return report


def format_discovery_report(report):
    """Format discovery report for console output"""
    lines = [
        "DISCOVERY SCAN REPORT",
        f"Scanned: {report['total_scanned']} stocks",
        "=" * 40,
        "",
        "TOP 10 STOCKS BY SIGNAL:",
    ]
    
    for i, stock in enumerate(report['top_20_stocks'][:10], 1):
        exchange = stock.get('exchange', 'N/A')
        lines.append(f"{i}. [{exchange}] {stock['symbol']} | Score:{stock['score']} | RSI:{stock['rsi']:.0f}")
    
    lines.append("")
    lines.append("VOLUME SPIKE ALERTS:")
    
    for i, stock in enumerate(report['volume_spikes'][:5], 1):
        exchange = stock.get('exchange', 'N/A')
        lines.append(f"{i}. [{exchange}] {stock['symbol']} Vol x{stock['vol_ratio']:.1f}")
    
    lines.append("")
    lines.append("TOP INDUSTRIES BY VALUE:")
    
    for i, ind in enumerate(report['top_industries'][:5], 1):
        lines.append(f"{i}. Group {ind['industry']}: {ind['stock_count']} stocks, {ind['signal_count']} signals")
    
    return "\n".join(lines)
