"""
Volatility Contraction Pattern (VCP) & Base Breakout Engine
============================================================
Detects:
1. Stage 2 / 52-Week High Breakouts
2. High-Tight Flag Breakouts (Super-Momentum)
3. Minervini Multi-Stage Volatility Contraction (VCP Breakout & VCP Coiling)
4. Stage 1 to 2 Early Base Transitions
5. Volume Dry-Up (VDU) Inside-Base Cheats
"""

import pandas as pd
import numpy as np
from config.settings import VCP_MAX_BASE_DEPTH_PCT, VOLUME_DRYUP_THRESHOLD, VOLUME_BREAKOUT_THRESHOLD

def detect_vcp_pattern(df):
    """
    Scans for VCP, 52W High Breakouts, High-Tight Flags, and Base Consolidations.
    Returns rich pattern metadata including exact pattern classification.
    """
    if df.empty or len(df) < 60:
        return {
            "is_vcp": False, "is_breakout": False, "vcp_score": 0,
            "pivot_price": 0.0, "pattern_name": "None", "contractions": 0,
            "is_vdu": False, "detail": "Insufficient history"
        }
        
    last = df.iloc[-1]
    close = float(last['Close'])
    vol = float(last['Volume'])
    vol50 = float(last.get('VOL50', 1))
    sma50 = float(last.get('SMA50', 0))
    sma150 = float(last.get('SMA150', 0))
    sma200 = float(last.get('SMA200', 0))
    high52 = float(last.get('High52W', close))
    
    # 1. Trend Template Alignment (Stage 2)
    stage2 = (close > sma50) and (sma50 > sma150) and (sma150 > sma200)
    
    # 2. Base Construction Analysis
    lookback = min(120, len(df))
    base_window = df.iloc[-lookback:]
    base_high = float(base_window['High'].max())
    base_low = float(base_window['Low'].min())
    base_depth_pct = (base_high - base_low) / max(1.0, base_high)
    
    # 3. Wave Contraction Analysis
    std30 = df['Close'].iloc[-30:].pct_change(fill_method=None).std()
    std15 = df['Close'].iloc[-15:].pct_change(fill_method=None).std()
    std5 = df['Close'].iloc[-5:].pct_change(fill_method=None).std()
    
    is_contracting = (std30 > std15) and (std15 > std5)
    contractions = 3 if is_contracting else (2 if std30 > std5 else 1)
    
    # 4. Volume Signatures
    min_vol_5d = float(df['Volume'].iloc[-5:].min())
    is_vdu = min_vol_5d < (vol50 * VOLUME_DRYUP_THRESHOLD)
    is_vol_surge = vol >= (vol50 * VOLUME_BREAKOUT_THRESHOLD)
    
    # 5. Base Tightness
    recent_range_pct = (float(df['High'].iloc[-3:].max()) - float(df['Low'].iloc[-3:].min())) / close
    is_tight = recent_range_pct < 0.045
    
    # 6. Pivot Price (Resistance of the most recent contraction)
    pivot_price = float(df['High'].iloc[-20:-1].max()) if len(df) >= 21 else float(df['High'].iloc[:-1].max())
    is_crossing_pivot = close >= (pivot_price * 0.995)
    
    # 7. Check for High-Tight Flag (Surge > 60% in 8 weeks, flag < 18%)
    prior_8w_low = float(df['Low'].iloc[-min(45, len(df)):-10].min()) if len(df) >= 45 else base_low
    prior_surge_pct = (base_high - prior_8w_low) / max(1.0, prior_8w_low)
    is_htf = (prior_surge_pct >= 0.55) and (base_depth_pct <= 0.20)
    
    # 8. Score Calculation (0 to 30 pts)
    vcp_score = 5
    if stage2: vcp_score += 8
    if base_depth_pct <= 0.22: vcp_score += 5
    if is_contracting: vcp_score += 4
    if is_vdu: vcp_score += 4
    if is_vol_surge: vcp_score += 5
    if is_tight: vcp_score += 4
    
    # 9. Granular Pattern Classification
    if is_htf and is_crossing_pivot and is_vol_surge:
        pattern_name = "High-Tight Flag Breakout"
    elif stage2 and (close >= high52 * 0.985) and is_vol_surge:
        pattern_name = "Stage 2 (52W High) Breakout"
    elif is_crossing_pivot and is_vol_surge and is_contracting:
        pattern_name = "VCP Pivot Breakout"
    elif is_contracting and is_tight and base_depth_pct <= 0.25:
        pattern_name = "VCP Coiling Base"
    elif is_vdu and is_tight and stage2:
        pattern_name = "Volume Dry-Up (VDU) Base"
    elif stage2 and is_vol_surge:
        pattern_name = "Stage 2 Momentum Thrust"
    elif base_depth_pct <= 0.25:
        pattern_name = "Base Consolidation"
    else:
        pattern_name = "None"
        
    is_valid_setup = (pattern_name != "None")
    detail = f"{pattern_name} | Contractions: {contractions}T | Depth: {base_depth_pct*100:.1f}% | VDU: {'Yes' if is_vdu else 'No'}"
    
    return {
        "is_vcp": is_valid_setup,
        "is_breakout": is_vol_surge and is_crossing_pivot,
        "vcp_score": min(30, vcp_score),
        "pattern_name": pattern_name,
        "pivot_price": round(pivot_price, 2),
        "contractions": contractions,
        "is_vdu": is_vdu,
        "base_depth_pct": round(base_depth_pct * 100, 1),
        "detail": detail
    }
