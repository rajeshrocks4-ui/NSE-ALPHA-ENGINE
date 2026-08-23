"""
Fundamental Quality Gate Module
===============================
Extracts fundamental metrics (ROE, Debt/Equity, Operating Margins) and applies quality gating.
"""

import os
import pickle
from pathlib import Path
import pandas as pd
from config.settings import MIN_ROE_PCT, MAX_DEBT_TO_EQUITY, MIN_FUND_SCORE

FUND_CACHE_DIR = Path(r"C:\Users\rajes\Music\NSE_Data\Fundamental_Cache")

def load_fundamental_cache():
    """
    Loads all cached fundamental files into a dictionary.
    Returns: dict {symbol: {'roe': float, 'debt_equity': float, 'fund_score': float, 'fund_tier': str}}
    """
    cache = {}
    if not FUND_CACHE_DIR.exists():
        return cache
        
    for pkl_file in FUND_CACHE_DIR.glob("*.pkl"):
        try:
            with open(pkl_file, "rb") as f:
                data = pickle.load(f)
                sym = data.get("symbol", "").strip().upper()
                if not sym: continue
                
                info = data.get("info", {})
                roe = info.get("returnOnEquity")
                de = info.get("debtToEquity")
                
                try: roe_pct = float(roe) * 100.0 if roe is not None else 0.0
                except: roe_pct = 0.0
                
                try: de_val = float(de) / 100.0 if de is not None else 0.0
                except: de_val = 0.0
                
                # Check legacy score
                fund_score = float(data.get("score", 70.0))
                fund_tier = data.get("tier", "PRIME")
                
                cache[sym] = {
                    "roe": round(roe_pct, 2),
                    "debt_equity": round(de_val, 2),
                    "fund_score": fund_score,
                    "fund_tier": fund_tier
                }
        except Exception:
            continue
            
    return cache

def evaluate_fundamentals(symbol, fund_cache):
    """
    Evaluates a single stock against the fundamental quality gate.
    Returns: dict with fund_pts (0 to 15), passes_gate (bool), roe, debt_equity
    """
    is_rated = symbol.upper() in fund_cache
    if not is_rated:
        return {
            "fund_pts": 4,
            "passes_gate": False,
            "roe": 0.0,
            "debt_equity": 0.0,
            "fund_score": 50.0,
            "is_rated": False
        }
        
    metrics = fund_cache.get(symbol.upper(), {})
    roe = metrics.get("roe", 0.0)
    debt_eq = metrics.get("debt_equity", 0.0)
    fund_score = metrics.get("fund_score", 60.0)
    
    passes_gate = (roe >= MIN_ROE_PCT) and (debt_eq <= MAX_DEBT_TO_EQUITY)
    
    # Fundamental points allocation (0 to 15 pts)
    pts = 3 # Baseline
    if roe >= 20.0: pts += 4
    elif roe >= 15.0: pts += 2
    
    if debt_eq <= 0.2: pts += 4
    elif debt_eq <= 0.8: pts += 2
    
    if fund_score >= 80: pts += 4
    elif fund_score >= 70: pts += 2
    
    return {
        "fund_pts": min(15, pts),
        "passes_gate": passes_gate,
        "roe": roe,
        "debt_equity": debt_eq,
        "fund_score": fund_score,
        "is_rated": True
    }
