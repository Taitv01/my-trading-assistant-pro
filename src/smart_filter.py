"""
Smart Filter Module - Filter stocks by liquidity and industry money flow
"""
import time
from vnstock import Listing, Quote
from datetime import datetime, timedelta


# Rate limiting
API_DELAY = 2.5


def get_all_symbols_with_industry():
    """Get all symbols with their industry classification"""
    try:
        listing = Listing(source='VCI')
        df = listing.symbols_by_industries()
        # Expected columns: symbol, organ_name, icb_code, icb_name, etc.
        return df
    except Exception as e:
        print(f"Error fetching industry data: {e}")
        return None


def get_top_liquid_stocks(n=500):
    """
    Get top N stocks by average trading value (liquidity) in last 50 sessions.
    Returns list of symbols sorted by liquidity.
    """
    print(f"Fetching top {n} liquid stocks...")
    
    # Get all symbols first
    listing = Listing(source='VCI')
    all_symbols_df = listing.all_symbols()
    all_symbols = all_symbols_df['symbol'].tolist()
    
    print(f"Total symbols: {len(all_symbols)}")
    
    # Calculate average trading value for each stock
    liquidity_data = []
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=70)).strftime('%Y-%m-%d')  # ~50 trading days
    
    for i, symbol in enumerate(all_symbols):
        if (i + 1) % 100 == 0:
            print(f"Liquidity check: {i + 1}/{len(all_symbols)}")
        
        try:
            quote = Quote(symbol=symbol, source='VCI')
            df = quote.history(start=start_date, end=end_date, interval='1D')
            
            if df is not None and len(df) >= 20:
                # Calculate average trading value (price * volume)
                df['trading_value'] = df['close'] * df['volume'] * 1000  # *1000 to convert to VND
                avg_value = df['trading_value'].tail(50).mean()
                
                if avg_value > 0:
                    liquidity_data.append({
                        'symbol': symbol,
                        'avg_trading_value': avg_value
                    })
        except Exception as e:
            pass  # Skip failed symbols silently
        
        time.sleep(API_DELAY)
    
    # Sort by liquidity and take top N
    liquidity_data.sort(key=lambda x: x['avg_trading_value'], reverse=True)
    top_symbols = [item['symbol'] for item in liquidity_data[:n]]
    
    print(f"Found {len(top_symbols)} liquid stocks")
    return top_symbols


def get_top_industries_by_money_flow(n=10, days=50):
    """
    Get top N industries by money flow in last X days.
    Returns list of industry codes/names.
    
    Note: This is a simplified version. Full implementation would require
    aggregating trading value by industry which needs per-stock data.
    """
    # For now, return major Vietnam industries known for high money flow
    # This can be enhanced later with real data aggregation
    TOP_INDUSTRIES = [
        "Ngan hang",           # Banking
        "Bat dong san",        # Real Estate
        "Chung khoan",         # Securities
        "Thep",                # Steel
        "Dien",                # Electricity
        "Xay dung",            # Construction
        "Cong nghe thong tin", # IT
        "Ban le",              # Retail
        "Dau khi",             # Oil & Gas
        "Thuy san",            # Seafood
    ]
    return TOP_INDUSTRIES[:n]


def get_smart_watchlist(top_n_stocks=500):
    """
    Get smart watchlist: Top N stocks by liquidity.
    
    Args:
        top_n_stocks: Number of top liquid stocks to include
    
    Returns:
        List of symbols
    """
    print("Building smart watchlist...")
    
    # For faster execution, use a pre-defined list of known liquid stocks
    # This avoids the slow liquidity calculation
    KNOWN_LIQUID_STOCKS = [
        # VN30
        "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
        "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
        "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
        # HNX30 + Other liquid stocks
        "SHS", "PVS", "IDC", "NVB", "HUT", "TNG", "CEO", "PVI", "BAB", "DTD",
        "PLC", "LAS", "VCS", "NBC", "BVS", "HLD", "L14", "PVB", "VCG", "HBC",
        # Other popular stocks
        "DGW", "DXG", "DIG", "PDR", "VIX", "HCM", "VND", "KDH", "NLG", "DPM",
        "DCM", "PNJ", "MPC", "VHC", "ANV", "HAG", "HNG", "DBC", "PAN", "GMD",
        "VTP", "VCI", "AGG", "KBC", "NKG", "HSG", "SMC", "TLG", "VGC", "BWE",
        # Banking & Finance
        "LPB", "EIB", "OCB", "MSB", "NAB", "VAB", "ABB", "BAB", "BVB", "PGB",
        # Real Estate
        "NVL", "DXS", "HDG", "CEO", "LDG", "NBB", "SCR", "HDC", "TDC", "KHG",
        # Securities
        "VND", "HCM", "SSI", "VCI", "SHS", "MBS", "BSI", "AGR", "TVS", "ORS",
        # Steel & Construction
        "HPG", "HSG", "NKG", "SMC", "TLH", "POM", "VIS", "TVN", "TIS", "CTD",
        # Technology
        "FPT", "CMG", "FOX", "ITD", "SAM", "ELC", "TSC", "VGI", "ICT", "VTC",
        # Energy
        "GAS", "PVD", "PVS", "BSR", "OIL", "PLX", "PVT", "PGD", "PGS", "PVC",
        # Consumer
        "VNM", "MSN", "SAB", "QNS", "MCH", "KDF", "MCM", "VLC", "NET", "HVN",
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_stocks = []
    for stock in KNOWN_LIQUID_STOCKS:
        if stock not in seen:
            seen.add(stock)
            unique_stocks.append(stock)
    
    # Limit to requested number
    result = unique_stocks[:top_n_stocks]
    print(f"Smart watchlist: {len(result)} stocks")
    
    return result
