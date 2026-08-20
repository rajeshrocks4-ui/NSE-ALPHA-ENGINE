"""
Volatility Contraction Pattern (VCP) Module
============================================
Detects multi-stage volatility contractions, Base Consolidation, and Volume Dry-Up (VDU).
"""

import pandas as pd
import numpy as np
from config.settings import VCP_MAX_BASE_DEPTH_PCT, VOLUME_DRYUP_THRESHOLD

def detect_vcp_pattern(df):
    """
    Scans a technical price series for Mark Minervini style VCP coiling.
    Returns: dict with vcp_score (0 to 30), is_vcp, pivot_price, contractions_count, is_vdu
    """
    if df.empty or len(df) < 100:
        return {"is_vcp": False, "vcp_score": 0, "pivot_price": 0.0, "contractions": 0, "is_vdu": False, "detail": "Insufficient history"}
        
    last = df.iloc[-1]
    close = last['Close']
    sma50 = last.get('SMA50', 0)
    sma150 = last.get('SMA150', 0)
    sma200 = last.get('SMA200', 0)
    vol50 = last.get('VOL50', 1)
    
    # 1. Trend Template Gate (Stage 2)
    stage2 = (close > sma50) and (sma50 > sma150) and (sma150 > sma200)
    if not stage2:
        return {"is_vcp": False, "vcp_score": 0, "pivot_price": 0.0, "contractions": 0, "is_vdu": False, "detail": "Not Stage 2"}
        
    # 2. Base Depth & Consolidation Length
    lookback = min(120, len(df))
    base_window = df.iloc[-lookback:]
    base_high = base_window['High'].max()
    base_low = base_window['Low'].min()
    base_depth_pct = (base_high - base_low) / base_high
    
    if base_depth_pct > VCP_MAX_BASE_DEPTH_PCT:
        return {"is_vcp": False, "vcp_score": 5, "pivot_price": base_high, "contractions": 0, "is_vdu": False, "detail": f"Base too deep ({base_depth_pct*100:.1f}%)"}
        
    # 3. Wave Contraction Analysis (Last 3 swings)
    # Check volatility over 30d, 15d, 5d windows
    std30 = df['Close'].iloc[-30:].pct_change().std()
    std15 = df['Close'].iloc[-15:].pct_change().std()
    std5 = df['Close'].iloc[-5:].pct_change().std()
    
    is_contracting = (std30 > std15) and (std15 > std5)
    contractions = 3 if is_contracting else (2 if std30 > std5 else 1)
    
    # 4. Volume Dry-Up (VDU)
    min_vol_5d = df['Volume'].iloc[-5:].min()
    is_vdu = min_vol_5d < (vol50 * VOLUME_DRYUP_THRESHOLD)
    
    # 5. Base Tightness (Last 3 days range < 4%)
    recent_range_pct = (df['High'].iloc[-3:].max() - df['Low'].iloc[-3:].min()) / close
    is_tight = recent_range_pct < 0.045
    
    # 6. Pivot Price (Resistance of the most recent contraction)
    pivot_price = df['High'].iloc[-20:].max()
    
    # 7. VCP Score Calculation (0 to 30 pts)
    vcp_score = 10 # Base Stage 2
    if base_depth_pct <= 0.18: vcp_score += 5
    if is_contracting: vcp_score += 5
    if is_vdu: vcp_score += 5
    if is_tight: vcp_score += 5
    
    is_valid_vcp = (vcp_score >= 20)
    detail = f"{contractions}T VCP | Base: {base_depth_pct*100:.1f}% | VDU: {'Yes' if is_vdu else 'No'} | Tightness: {recent_range_pct*100:.1f}%"
    
    return {
        "is_vcp": is_valid_vcp,
        "vcp_score": vcp_score,
        "pivot_price": round(float(pivot_price), 2),
        "contractions": contractions,
        "is_vdu": is_vdu,
        "base_depth_pct": round(float(base_depth_pct * 100), 1),
        "detail": detail
    }
