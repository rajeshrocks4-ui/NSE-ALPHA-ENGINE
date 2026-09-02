"""
Sector Rotation & Pole Position Engine (v5.0)
==============================================
Ranks sectors by Clean Relative Strength to detect leading institutional themes.
Supports comprehensive mapping for 1,980+ NSE stocks using official Nifty Total Market indices.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
NIFTY_MASTER_CSV = CONFIG_DIR / "nifty_industry_master.csv"
SECTOR_MAP_PATH = Path(r"C:\Users\rajes\Music\nse_sector_map.json")
ICHARTS_CSV = Path(r"C:\Users\rajes\Downloads\ICHARTS\19012026\FuturesOI_27JAN26_Scan_combined_oi__16_1_2026.csv")

# Core fallback mapping
DEFAULT_SECTOR_MAP = {
    "DIVISLAB": "Healthcare", "SUPRIYA": "Healthcare", "LUPIN": "Healthcare", "APOLLOHOSP": "Healthcare",
    "TORNTPHARM": "Healthcare", "AUROPHARMA": "Healthcare", "ZYDUSLIFE": "Healthcare", "GLENMARK": "Healthcare",
    "TCS": "Information Technology", "INFY": "Information Technology", "WIPRO": "Information Technology",
    "HCLTECH": "Information Technology", "OFSS": "Information Technology", "PERSISTENT": "Information Technology",
    "HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", "SBIN": "Financial Services",
    "KOTAKBANK": "Financial Services", "KARURVYSYA": "Financial Services", "MCX": "Financial Services",
    "MOTHERSON": "Automobile & Auto Components", "TITAN": "Consumer Durables", "MARUTI": "Automobile & Auto Components",
    "TATAMOTORS": "Automobile & Auto Components", "RELIANCE": "Oil Gas & Consumable Fuels", "ONGC": "Oil Gas & Consumable Fuels",
    "NTPC": "Power", "POWERGRID": "Power", "TATASTEEL": "Metals & Mining", "JSWSTEEL": "Metals & Mining",
    "HINDALCO": "Metals & Mining", "BEL": "Capital Goods", "HAL": "Capital Goods", "LT": "Construction",
    "SIEMENS": "Capital Goods"
}

_CACHED_SECTOR_MAP = None

def load_sector_map():
    """
    Builds and caches a comprehensive sector mapping dictionary for ~2,000+ NSE symbols.
    Maps both 'SYMBOL' and 'SYMBOL.NS'.
    """
    global _CACHED_SECTOR_MAP
    if _CACHED_SECTOR_MAP is not None:
        return _CACHED_SECTOR_MAP
        
    s_map = {}
    
    # 1. Base default dictionary
    for k, v in DEFAULT_SECTOR_MAP.items():
        sym = k.strip().upper()
        s_map[sym] = v
        s_map[f"{sym}.NS"] = v
        
    # 2. Official Nifty Total Market industry classification
    if NIFTY_MASTER_CSV.exists():
        try:
            df = pd.read_csv(NIFTY_MASTER_CSV)
            if 'Symbol' in df.columns and 'Industry' in df.columns:
                for _, row in df.iterrows():
                    sym = str(row['Symbol']).strip().upper()
                    ind = str(row['Industry']).strip()
                    if sym and ind:
                        s_map[sym] = ind
                        s_map[f"{sym}.NS"] = ind
        except Exception:
            pass
            
    # 3. Existing sector map JSON
    if SECTOR_MAP_PATH.exists():
        try:
            with open(SECTOR_MAP_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                for k, v in d.items():
                    sym = str(k).strip().upper()
                    ind = str(v).strip()
                    if sym and ind and ind.lower() != "unknown":
                        s_map[sym] = ind
                        s_map[f"{sym}.NS"] = ind
        except Exception:
            pass
            
    # 4. Futures OI / ICharts mapping
    if ICHARTS_CSV.exists():
        try:
            df = pd.read_csv(ICHARTS_CSV)
            if 'Symbol' in df.columns and 'Sector' in df.columns:
                for _, row in df.iterrows():
                    sym = str(row['Symbol']).strip().upper()
                    sec = str(row['Sector']).strip()
                    if sym not in s_map or s_map[sym] == "General":
                        s_map[sym] = sec
                        s_map[f"{sym}.NS"] = sec
        except Exception:
            pass
            
    _CACHED_SECTOR_MAP = s_map
    return _CACHED_SECTOR_MAP

def get_sector_for_symbol(symbol):
    """
    Get sector for a single symbol, handling both 'SYMBOL' and 'SYMBOL.NS'.
    """
    s_map = load_sector_map()
    clean_sym = symbol.replace('.NS', '').strip().upper()
    
    if clean_sym in s_map:
        return s_map[clean_sym]
    if symbol in s_map:
        return s_map[symbol]
        
    return "General"

def compute_sector_rankings(price_matrices):
    """
    Groups symbols by sector and computes aggregate 3M/6M Clean RS.
    """
    sector_scores = {}
    
    for symbol, df in price_matrices.items():
        if df.empty or len(df) < 50:
            continue
        sec = get_sector_for_symbol(symbol)
        last_rs = df['Clean_RS_Raw'].iloc[-1]
        if pd.isna(last_rs):
            continue
            
        if sec not in sector_scores:
            sector_scores[sec] = []
        sector_scores[sec].append(last_rs)
        
    rankings = []
    for sec, scores in sector_scores.items():
        if not scores: continue
        avg_score = float(np.mean(scores))
        rankings.append({
            "sector": sec,
            "raw_score": avg_score,
            "stock_count": len(scores)
        })
        
    df_sec = pd.DataFrame(rankings)
    if df_sec.empty:
        return pd.DataFrame()
        
    df_sec = df_sec.sort_values("raw_score", ascending=False).reset_index(drop=True)
    df_sec['rank'] = df_sec.index + 1
    
    # Classify Pole Position
    def classify(row):
        r = row['rank']
        if r <= 3: return "POLE POSITION"
        elif r <= 7: return "IMPROVING"
        elif r <= 15: return "NEUTRAL"
        else: return "FADING/LAGGING"
        
    df_sec['classification'] = df_sec.apply(classify, axis=1)
    return df_sec
