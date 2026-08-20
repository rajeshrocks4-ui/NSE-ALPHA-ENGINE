"""
Sector Rotation & Pole Position Engine
=======================================
Ranks sectors by Clean Relative Strength to detect leading institutional themes.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

SECTOR_MAP_PATH = Path(r"C:\Users\rajes\Music\nse_sector_map.json")

# Fallback sector map for major symbols
DEFAULT_SECTOR_MAP = {
    "DIVISLAB": "Healthcare", "SUPRIYA": "Healthcare", "LUPIN": "Healthcare", "APOLLOHOSP": "Healthcare",
    "TORNTPHARM": "Healthcare", "AUROPHARMA": "Healthcare", "ZYDUSLIFE": "Healthcare", "GLENMARK": "Healthcare",
    "TCS": "Technology", "INFY": "Technology", "WIPRO": "Technology", "HCLTECH": "Technology", "OFSS": "Technology",
    "HDFCBANK": "Financial Services", "ICICIBANK": "Financial Services", "SBIN": "Financial Services", "KOTAKBANK": "Financial Services",
    "MOTHERSON": "Consumer Cyclical", "TITAN": "Consumer Cyclical", "MARUTI": "Consumer Cyclical", "TATAMOTORS": "Consumer Cyclical",
    "RELIANCE": "Energy", "ONGC": "Energy", "NTPC": "Energy", "POWERGRID": "Energy",
    "TATASTEEL": "Basic Materials", "JSWSTEEL": "Basic Materials", "HINDALCO": "Basic Materials",
    "BEL": "Industrials", "HAL": "Industrials", "LT": "Industrials", "SIEMENS": "Industrials"
}

def load_sector_map():
    """Load sector mapping from JSON or fallback dictionary."""
    if SECTOR_MAP_PATH.exists():
        try:
            with open(SECTOR_MAP_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_SECTOR_MAP

def compute_sector_rankings(price_matrices):
    """
    Groups symbols by sector and computes aggregate 3M/6M Clean RS.
    """
    sector_map = load_sector_map()
    sector_scores = {}
    
    for symbol, df in price_matrices.items():
        if df.empty or len(df) < 50:
            continue
        sec = sector_map.get(symbol, "General")
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
        if r <= 2: return "POLE POSITION"
        elif r <= 5: return "IMPROVING"
        elif r <= 10: return "NEUTRAL"
        else: return "FADING/LAGGING"
        
    df_sec['classification'] = df_sec.apply(classify, axis=1)
    return df_sec

def get_sector_for_symbol(symbol):
    """Get sector for a single symbol."""
    sector_map = load_sector_map()
    return sector_map.get(symbol, "General")
