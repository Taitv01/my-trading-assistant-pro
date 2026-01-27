"""
Market Scanner Module - Full market scan logic for HOSE, HNX, UPCOM
"""
import pandas as pd
import time
from vnstock import Listing
from .data_fetcher import fetch_data
from .indicators import calculate_indicators, check_signals
from .filters import is_investable
from .config import MIN_SCORE
from .smart_filter import get_smart_watchlist
from .industry_mapper import analyze_industry_flow

# Rate limiting: vnstock Guest limit is 30 requests/minute
# We add 2.5 second delay to stay safely under limit (24 requests/min)
API_DELAY_SECONDS = 2.5


def get_all_symbols(use_smart_filter=True):
    """
    Fetch stock symbols for scanning.
    
    Args:
        use_smart_filter: If True, use smart watchlist (~150 liquid stocks).
                         If False, fetch all ~1700 symbols.
    """
    if use_smart_filter:
        return get_smart_watchlist()
    
    try:
        listing = Listing(source='VCI')
        df = listing.all_symbols()
        return df['symbol'].tolist()
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return []


def analyze_stock(symbol):
    """Analyze a single stock and return its score and data"""
    try:
        df = fetch_data(symbol)
        if df is None:
            return None
        
        df = calculate_indicators(df)
        
        if not is_investable(df):
            return None
        
        score, reasons = check_signals(df)
        
        if score > 0:
            last = df.iloc[-1]
            return {
                'symbol': symbol,
                'score': score,
                'reasons': reasons,
                'price': last['close'],
                'rsi': last['RSI'],
                'macd': last['MACD'],
                'volume': last['volume']
            }
        return None
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None


def analyze_market(symbols=None, max_stocks=None):
    """
    Analyze entire market and return top stocks and industries.
    
    Args:
        symbols: List of symbols to analyze. If None, fetches all.
        max_stocks: Limit number of stocks to analyze (for testing).
    
    Returns:
        tuple: (top_10_stocks, top_3_industries)
    """
    if symbols is None:
        symbols = get_all_symbols()
    
    if max_stocks:
        symbols = symbols[:max_stocks]
    
    print(f"Analyzing {len(symbols)} symbols...")
    
    results = []
    
    for i, symbol in enumerate(symbols):
        if (i + 1) % 25 == 0:
            print(f"Progress: {i + 1}/{len(symbols)}")
        
        result = analyze_stock(symbol)
        if result:
            results.append(result)
        
        # Rate limiting
        time.sleep(API_DELAY_SECONDS)
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Top 10 stocks
    top_10_stocks = results[:10]
    
    # === MỚI: Phân tích dòng tiền theo ngành ===
    top_industries = analyze_industry_flow(results)
    top_3_industries = top_industries[:3]
    
    print(f"\n📊 TOP NGÀNH CÓ TÍN HIỆU:")
    for i, ind in enumerate(top_3_industries, 1):
        symbols_preview = ', '.join(ind['symbols'][:3])
        print(f"  {i}. {ind['industry']}: {ind['signal_count']} tín hiệu ({symbols_preview}...)")
    
    print(f"\nAnalysis complete. Found {len(results)} stocks with signals.")
    
    return top_10_stocks, top_3_industries


def format_top_stocks_report(top_stocks):
    """Format top stocks into a readable message"""
    if not top_stocks:
        return "No buy signals found."
    
    lines = ["TOP 10 STOCKS:"]
    lines.append("=" * 30)
    
    for i, stock in enumerate(top_stocks, 1):
        reasons_str = ", ".join(stock['reasons']) if stock['reasons'] else "Score > 0"
        lines.append(
            f"{i}. {stock['symbol']} - Score: {stock['score']} - "
            f"Price: {stock['price']:,.0f} - RSI: {stock['rsi']:.1f}"
        )
        lines.append(f"   Reason: {reasons_str}")
    
    return "\n".join(lines)
