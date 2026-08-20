"""
Pocket Pivot Module
===================
Detects institutional "in-the-base" Pocket Pivot accumulation signals before breakouts.
"""

import pandas as pd
import numpy as np

def detect_pocket_pivot(df, delivery_pct=None):
    """
    Checks if today qualifies as a Pocket Pivot Accumulation signature.
    Rule: Up-Volume > Max Down-Volume of the last 10 days while resting on/crossing 10/20 EMA.
    Returns: dict with is_pocket_pivot, pp_score (0 to 25), detail
    """
    if df.empty or len(df) < 15:
        return {"is_pocket_pivot": False, "pp_score": 0, "detail": "Insufficient history"}
        
    last = df.iloc[-1]
    close = last['Close']
    open_p = last['Open']
    vol_today = last['Volume']
    ema10 = last.get('EMA10', 0)
    ema20 = last.get('EMA20', 0)
    
    # Must be an up day (Green candle)
    if close < open_p or vol_today == 0:
        return {"is_pocket_pivot": False, "pp_score": 0, "detail": "Not an up-day"}
        
    # Must be near or above 10 EMA or 20 EMA
    near_ema = (close >= ema10 * 0.985) or (close >= ema20 * 0.985)
    if not near_ema:
        return {"is_pocket_pivot": False, "pp_score": 0, "detail": "Below key EMAs"}
        
    # Get preceding 10 days
    window_10d = df.iloc[-11:-1] # Exclude today
    
    # Find all down-days in the last 10 days
    down_days = window_10d[window_10d['Close'] < window_10d['Open']]
    
    if down_days.empty:
        max_down_vol = 0
    else:
        max_down_vol = down_days['Volume'].max()
        
    # Pocket Pivot condition: Today's up-volume > Max down-volume of last 10 days
    is_pp_volume = vol_today > max_down_vol
    
    if not is_pp_volume:
        return {"is_pocket_pivot": False, "pp_score": 0, "detail": "Volume did not exceed 10d down-volume peak"}
        
    # Score calculation (0 to 25 pts)
    pp_score = 15
    if close > ema10: pp_score += 5
    
    # Delivery bonus
    if delivery_pct is not None and delivery_pct >= 45.0:
        pp_score += 5
        
    detail = f"Pocket Pivot Confirmed | Vol vs 10d Down-Peak: {vol_today/max(1, max_down_vol):.2f}x | 10 EMA: {'Above' if close > ema10 else 'Near'}"
    
    return {
        "is_pocket_pivot": True,
        "pp_score": pp_score,
        "detail": detail
    }
