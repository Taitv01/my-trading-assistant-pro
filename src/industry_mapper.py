"""
Industry Mapper Module - Maps stock symbols to their industries
Uses vnstock API with fallback to hardcoded mapping for reliability
"""
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Rate limiting
API_DELAY = 2.5

# ============================================================
# FALLBACK INDUSTRY MAPPING (Top ~130 liquid stocks)
# ============================================================
INDUSTRY_MAPPING = {
    # Ngân hàng (Banking)
    "Ngân hàng": [
        "ACB", "BID", "CTG", "HDB", "MBB", "SHB", "SSB", "STB", "TCB", "TPB",
        "VCB", "VIB", "VPB", "LPB", "EIB", "OCB", "MSB", "NAB", "VAB", "ABB",
        "BAB", "BVB", "PGB", "NVB", "KLB", "VBB"
    ],
    
    # Bất động sản (Real Estate)
    "Bất động sản": [
        "VHM", "VIC", "VRE", "NVL", "DXG", "DIG", "PDR", "KDH", "NLG", "DXS",
        "HDG", "CEO", "LDG", "NBB", "SCR", "HDC", "TDC", "KHG", "AGG", "KBC",
        "BCM", "IJC", "ITA", "SZC", "TIP", "PHR"
    ],
    
    # Chứng khoán (Securities)
    "Chứng khoán": [
        "SSI", "VND", "HCM", "VCI", "SHS", "MBS", "BSI", "AGR", "TVS", "ORS",
        "VIX", "CTS", "FTS", "APS", "BVS", "PSI", "DSC", "EVS"
    ],
    
    # Thép & Xây dựng (Steel & Construction)
    "Thép": [
        "HPG", "HSG", "NKG", "SMC", "TLH", "POM", "VIS", "TVN", "TIS", "VGS"
    ],
    "Xây dựng": [
        "CTD", "HBC", "VCG", "HUT", "FCN", "C47", "CII", "LCG", "VC3", "VCS"
    ],
    
    # Dầu khí (Oil & Gas)
    "Dầu khí": [
        "GAS", "PVD", "PVS", "BSR", "OIL", "PLX", "PVT", "PGD", "PGS", "PVC",
        "PVB", "PVG", "PXS", "PSH", "POS", "PGC", "PCT", "POW"
    ],
    
    # Điện (Electricity)
    "Điện": [
        "POW", "GEG", "REE", "PC1", "NT2", "PPC", "VSH", "SJD", "HND", "TBC",
        "BWE", "TV2", "HJS", "SHP", "HDG", "CHP", "QTP"
    ],
    
    # Công nghệ thông tin (Technology)
    "Công nghệ": [
        "FPT", "CMG", "FOX", "ITD", "SAM", "ELC", "TSC", "VGI", "ICT", "VTC",
        "SGT", "CTR", "ONE", "SRA", "DSE"
    ],
    
    # Tiêu dùng (Consumer)
    "Tiêu dùng": [
        "VNM", "MSN", "SAB", "QNS", "MCH", "KDF", "MCM", "VLC", "NET", "HVN",
        "PNJ", "MWG", "DGW", "FRT", "VJC"
    ],
    
    # Thủy sản (Seafood)
    "Thủy sản": [
        "VHC", "ANV", "MPC", "FMC", "CMX", "IDI", "ABT", "ACL", "HVG", "TS4"
    ],
    
    # Phân bón & Hóa chất (Fertilizer & Chemicals)
    "Hóa chất": [
        "DPM", "DCM", "DGC", "CSV", "LAS", "BFC", "SFG", "DDV", "HVT", "PCE"
    ],
    
    # Vận tải & Logistics
    "Vận tải": [
        "GMD", "VTP", "HAH", "VOS", "PVT", "TMS", "VNA", "STG", "VTO", "ASG"
    ],
    
    # Cao su (Rubber)
    "Cao su": [
        "GVR", "PHR", "DRI", "TRC", "DPR", "HRC", "BRR", "RTB", "SRC"
    ],
    
    # Bảo hiểm (Insurance)
    "Bảo hiểm": [
        "BVH", "PVI", "BMI", "BIC", "PTI", "VNR", "PGI", "PRE", "MIG", "ABI"
    ],
}

# Reverse mapping: symbol -> industry
_SYMBOL_TO_INDUSTRY: Dict[str, str] = {}
for industry, symbols in INDUSTRY_MAPPING.items():
    for symbol in symbols:
        _SYMBOL_TO_INDUSTRY[symbol] = industry


def get_industry_from_api(symbol: str) -> Optional[str]:
    """
    Get industry from vnstock API.
    Returns None if API fails.
    """
    try:
        from vnstock import Company
        company = Company(symbol=symbol, source='VCI')
        overview = company.overview()
        
        if overview is not None and not overview.empty:
            # Look for industry column
            if 'industry' in overview.columns:
                return overview['industry'].iloc[0]
            if 'icb_name' in overview.columns:
                return overview['icb_name'].iloc[0]
        return None
    except Exception:
        return None


def get_industry(symbol: str) -> str:
    """
    Get industry for a stock symbol.
    Uses fallback mapping first for speed, then API if not found.
    
    Returns:
        Industry name or "Khác" if unknown
    """
    # Try fallback mapping first (instant)
    if symbol in _SYMBOL_TO_INDUSTRY:
        return _SYMBOL_TO_INDUSTRY[symbol]
    
    # If not in fallback, try API (slow)
    api_industry = get_industry_from_api(symbol)
    if api_industry:
        return api_industry
    
    return "Khác"


def get_all_industries_from_api() -> Optional[Dict[str, str]]:
    """
    Fetch all industry mappings from vnstock API.
    Returns dict of {symbol: industry} or None if API fails.
    """
    try:
        from vnstock import Listing
        listing = Listing(source='VCI')
        df = listing.symbols_by_industries()
        
        if df is not None and not df.empty:
            result = {}
            # Expected columns: symbol, icb_name (or industry)
            symbol_col = 'symbol' if 'symbol' in df.columns else 'ticker'
            industry_col = 'icb_name' if 'icb_name' in df.columns else 'industry'
            
            if symbol_col in df.columns and industry_col in df.columns:
                for _, row in df.iterrows():
                    result[row[symbol_col]] = row[industry_col]
                return result
        return None
    except Exception as e:
        print(f"Error fetching industry data from API: {e}")
        return None


def analyze_industry_flow(signals: List[dict]) -> List[dict]:
    """
    Analyze money flow by industry based on stock signals.
    
    Args:
        signals: List of stock signals, each with 'symbol' key
        
    Returns:
        List of industries sorted by signal count, each with:
        - industry: Industry name
        - signal_count: Number of signals in this industry
        - stock_count: Number of unique stocks
        - symbols: List of stock symbols
    """
    if not signals:
        return []
    
    # Group signals by industry
    industry_data = defaultdict(lambda: {"count": 0, "symbols": set()})
    
    for signal in signals:
        symbol = signal.get('symbol', '')
        if not symbol:
            continue
            
        industry = get_industry(symbol)
        industry_data[industry]["count"] += 1
        industry_data[industry]["symbols"].add(symbol)
    
    # Convert to sorted list
    result = []
    for industry, data in industry_data.items():
        result.append({
            "industry": industry,
            "signal_count": data["count"],
            "stock_count": len(data["symbols"]),
            "symbols": list(data["symbols"])
        })
    
    # Sort by signal count descending
    result.sort(key=lambda x: x["signal_count"], reverse=True)
    
    return result


def get_top_industries(signals: List[dict], top_n: int = 5) -> List[dict]:
    """
    Get top N industries by money flow (signal count).
    
    Args:
        signals: List of stock signals
        top_n: Number of top industries to return
        
    Returns:
        Top N industries with signal counts
    """
    all_industries = analyze_industry_flow(signals)
    return all_industries[:top_n]
