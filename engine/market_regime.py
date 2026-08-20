"""
Market Regime Module
====================
Determines the macroeconomic market posture (Bull vs Distribution) and position sizing guide.
"""

import pandas as pd
import numpy as np

def compute_market_regime(price_matrices):
    """
    Computes overall market breadth and assigns a regime score from 0 to 13.
    """
    if not price_matrices:
        return "UNKNOWN", 5, "Maintain 50% position sizing due to missing market breadth data."
        
    above_50ma = 0
    above_150ma = 0
    above_200ma = 0
    near_52w_high = 0
    near_52w_low = 0
    total_valid = 0
    
    for symbol, df in price_matrices.items():
        if df.empty or len(df) < 50:
            continue
        last = df.iloc[-1]
        c = last['Close']
        if pd.isna(c): continue
        
        total_valid += 1
        if pd.notna(last.get('SMA50')) and c > last['SMA50']: above_50ma += 1
        if pd.notna(last.get('SMA150')) and c > last['SMA150']: above_150ma += 1
        if pd.notna(last.get('SMA200')) and c > last['SMA200']: above_200ma += 1
        if pd.notna(last.get('Pct_From_52W_High')) and last['Pct_From_52W_High'] >= -15.0: near_52w_high += 1
        if pd.notna(last.get('Pct_From_52W_High')) and last['Pct_From_52W_High'] <= -35.0: near_52w_low += 1
        
    if total_valid == 0:
        return "UNKNOWN", 5, "Insufficient valid records."
        
    pct_50 = (above_50ma / total_valid) * 100.0
    pct_150 = (above_150ma / total_valid) * 100.0
    pct_200 = (above_200ma / total_valid) * 100.0
    nh_nl_ratio = (near_52w_high / max(1, near_52w_low))
    
    # 13-Point Regime Scoring Model
    score = 0
    if pct_50 >= 70: score += 3
    elif pct_50 >= 55: score += 2
    elif pct_50 >= 45: score += 1
    
    if pct_150 >= 65: score += 3
    elif pct_150 >= 50: score += 2
    elif pct_150 >= 40: score += 1
    
    if pct_200 >= 60: score += 3
    elif pct_200 >= 50: score += 2
    elif pct_200 >= 40: score += 1
    
    if nh_nl_ratio >= 3.0: score += 4
    elif nh_nl_ratio >= 1.5: score += 2
    elif nh_nl_ratio >= 1.0: score += 1
    
    # Classification
    if score >= 11:
        regime = "BULL_POWER"
        action = "Full Aggressive Trading (100% position size). Focus on fresh Stage 2 breakouts."
        size_pct = 100
    elif score >= 8:
        regime = "BULL_PAUSE"
        action = "Normal Operations (80% position size). Be selective, trail stops."
        size_pct = 80
    elif score >= 5:
        regime = "CAUTION"
        action = "Defensive Stance (50% position size). Tight stops, take partial profits."
        size_pct = 50
    elif score >= 2:
        regime = "DISTRIBUTION"
        action = "Capital Preservation (25% position size). No aggressive buys. Raise cash."
        size_pct = 25
    else:
        regime = "BEAR"
        action = "100% Cash / Defensive. Avoid long breakouts until regime reverses."
        size_pct = 0
        
    metrics = {
        "pct_above_50ma": round(pct_50, 1),
        "pct_above_150ma": round(pct_150, 1),
        "pct_above_200ma": round(pct_200, 1),
        "nh_nl_ratio": round(nh_nl_ratio, 2),
        "regime_score": score,
        "regime": regime,
        "action": action,
        "position_size_pct": size_pct
    }
    return regime, score, metrics
