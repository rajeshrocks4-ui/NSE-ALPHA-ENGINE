"""
Pre-Breakout Volatility Compression Engine (v5.0)
=================================================
Identifies stocks in maximum compression / launchpad state BEFORE explosive breakouts occur.

Setups Detected:
1. NR7 (Narrowest Range in 7 Days) - Toby Crabel Volatility Compression
2. NR4 (Narrowest Range in 4 Days)
3. Inside Bar (IB) & Double Inside Bar (II / NR4-IB)
4. Doji / Ultra-Tight Real Body (<0.7%) at Key EMAs (10 EMA / 20 EMA)
5. Volume Dry-Up (VDU < 40% 50MA) - Float Absorption
6. Bollinger Band Squeeze (TTM Squeeze)
7. Launchpad Proximity Gate (within -3.8% to +1.2% of pivot; penalizes > +4% extended)
"""

import pandas as pd
import numpy as np
from config.settings import (
    NR7_PERIOD, NR4_PERIOD, DOJI_BODY_THRESHOLD, TIGHT_RANGE_THRESHOLD,
    VOLUME_DRYUP_THRESHOLD, MAX_EXTENSION_ABOVE_PIVOT_PCT,
    LAUNCHPAD_ZONE_MIN, LAUNCHPAD_ZONE_MAX
)

def detect_compression_pattern(df):
    """
    Evaluates price series for pre-breakout coiling, NR7/Inside Bar compression,
    and proximity to pivot resistance.
    
    Returns: dict with compression_score (0 to 30), setup_type, is_coiled, 
             is_extended, pivot_price, tight_stop_loss, detail
    """
    if df.empty or len(df) < 50:
        return {
            "is_coiled": False, "is_extended": False, "compression_score": 0,
            "setup_type": "None", "pivot_price": 0.0, "tight_stop_loss": 0.0,
            "dist_to_pivot_pct": 0.0, "detail": "Insufficient data"
        }
        
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    close = float(last['Close'])
    open_p = float(last['Open'])
    high = float(last['High'])
    low = float(last['Low'])
    vol = float(last['Volume'])
    vol50 = float(last.get('VOL50', 1.0))
    ema10 = float(last.get('EMA10', close))
    ema20 = float(last.get('EMA20', close))
    sma50 = float(last.get('SMA50', close))
    sma200 = float(last.get('SMA200', close))
    atr14 = float(last.get('ATR14', close * 0.03))
    
    # -------------------------------------------------------------
    # 1. Base Pivot Resistance & Extension Calculation
    # -------------------------------------------------------------
    # Pivot is the highest high of the prior 20 sessions (excluding today)
    pivot_price = float(df['High'].iloc[-21:-1].max()) if len(df) >= 22 else float(df['High'].iloc[:-1].max())
    if pivot_price <= 0:
        pivot_price = close * 1.01
        
    dist_to_pivot_pct = ((close - pivot_price) / pivot_price) * 100.0
    
    # Check if stock has ALREADY broken out and is extended
    is_extended = (close > pivot_price * (1.0 + MAX_EXTENSION_ABOVE_PIVOT_PCT))
    
    # Check if stock is in the Pre-Breakout Launchpad Zone (-3.8% to +1.2%)
    is_in_launchpad = (LAUNCHPAD_ZONE_MIN * 100.0 <= dist_to_pivot_pct <= LAUNCHPAD_ZONE_MAX * 100.0)
    
    # -------------------------------------------------------------
    # 2. Daily Ranges & Volatility Compression Mechanics
    # -------------------------------------------------------------
    ranges = (df['High'] - df['Low']).values
    today_range = high - low
    today_range_pct = today_range / max(0.01, close)
    real_body = abs(close - open_p)
    real_body_pct = real_body / max(0.01, close)
    
    # NR7: Today's range is the smallest of the last 7 sessions
    is_nr7 = False
    if len(ranges) >= NR7_PERIOD:
        is_nr7 = (today_range <= min(ranges[-NR7_PERIOD:-1]))
        
    # NR4: Today's range is the smallest of the last 4 sessions
    is_nr4 = False
    if len(ranges) >= NR4_PERIOD:
        is_nr4 = (today_range <= min(ranges[-NR4_PERIOD:-1]))
        
    # Inside Bar (IB): Today is completely contained inside yesterday's range
    prev_high = float(prev['High'])
    prev_low = float(prev['Low'])
    is_inside_bar = (high <= prev_high * 1.002) and (low >= prev_low * 0.998)
    
    # Double Inside Bar (II): Both today and yesterday were inside bars
    is_double_ib = False
    if len(df) >= 3:
        p2_high = float(df['High'].iloc[-3])
        p2_low = float(df['Low'].iloc[-3])
        prev_was_ib = (prev_high <= p2_high * 1.002) and (prev_low >= p2_low * 0.998)
        is_double_ib = is_inside_bar and prev_was_ib
        
    # Doji / Ultra-Tight Candle
    is_doji = (real_body_pct <= DOJI_BODY_THRESHOLD) and (today_range_pct <= TIGHT_RANGE_THRESHOLD)
    is_tight_range = (today_range_pct <= TIGHT_RANGE_THRESHOLD)
    
    # Volume Dry-Up (VDU): Float absorption
    is_vdu = (vol < vol50 * VOLUME_DRYUP_THRESHOLD) and (vol > 0)
    
    # Moving Average Coil / Support: Price resting right on 10 EMA, 20 EMA, or 50 SMA
    near_ema10 = abs(close - ema10) / ema10 <= 0.015
    near_ema20 = abs(close - ema20) / ema20 <= 0.018
    near_sma50 = abs(close - sma50) / sma50 <= 0.020
    ma_coiling = (near_ema10 or near_ema20 or near_sma50) and (close >= sma200)
    
    # Bollinger Bandwidth Squeeze (TTM Squeeze principle)
    sma20 = df['Close'].rolling(20).mean()
    std20 = df['Close'].rolling(20).std()
    upper_bb = sma20 + (2.0 * std20)
    lower_bb = sma20 - (2.0 * std20)
    bb_width = (upper_bb - lower_bb) / sma20
    
    is_bb_squeeze = False
    if len(bb_width) >= 60:
        min_width_60 = float(bb_width.iloc[-60:].min())
        curr_width = float(bb_width.iloc[-1])
        is_bb_squeeze = curr_width <= (min_width_60 * 1.15) # Within 15% of 60-day minimum width
        
    # -------------------------------------------------------------
    # 3. Compression Score (0 to 30 Points)
    # -------------------------------------------------------------
    comp_score = 0
    if is_in_launchpad: comp_score += 6
    if is_nr7: comp_score += 8
    elif is_nr4: comp_score += 4
    
    if is_double_ib: comp_score += 8
    elif is_inside_bar: comp_score += 6
    
    if is_vdu: comp_score += 5
    if is_doji or is_tight_range: comp_score += 4
    if is_bb_squeeze: comp_score += 4
    if ma_coiling: comp_score += 3
    
    comp_score = min(30, comp_score)
    
    # -------------------------------------------------------------
    # 4. Primary Setup Name Classification
    # -------------------------------------------------------------
    if is_double_ib and is_in_launchpad:
        setup_type = "Double Inside Bar Squeeze"
    elif is_nr7 and is_inside_bar and is_in_launchpad:
        setup_type = "NR7-Inside Bar Launchpad"
    elif is_nr7 and is_in_launchpad:
        setup_type = "NR7 Pre-Breakout Coiling"
    elif is_inside_bar and is_in_launchpad:
        setup_type = "Inside Bar Coiling"
    elif is_doji and ma_coiling and is_in_launchpad:
        setup_type = "Doji EMA Squeeze"
    elif is_bb_squeeze and is_vdu:
        setup_type = "TTM Bollinger Squeeze"
    elif is_vdu and is_in_launchpad:
        setup_type = "VDU Launchpad Base"
    elif is_in_launchpad and is_tight_range:
        setup_type = "Pre-Breakout Coiling"
    elif is_extended:
        setup_type = "Extended Past Pivot"
    else:
        setup_type = "Consolidation Base"
        
    is_coiled = (comp_score >= 14) and (not is_extended) and is_in_launchpad
    
    # -------------------------------------------------------------
    # 5. Tight Structural Stop Loss Calculation
    # -------------------------------------------------------------
    # In an Inside Bar / NR7 setup, stop is right below the mother bar or NR7 candle low!
    if is_inside_bar:
        tight_stop = round(min(low, prev_low) * 0.995, 2)
    elif is_nr7:
        tight_stop = round(low * 0.993, 2)
    else:
        tight_stop = round(min(low, ema20 * 0.985), 2)
        
    # Safeguard: Stop loss must be below close, and never wider than -8%
    stop_distance_pct = (close - tight_stop) / close
    if stop_distance_pct > 0.08:
        tight_stop = round(close * 0.92, 2)
    elif tight_stop >= close:
        tight_stop = round(close - (1.5 * atr14), 2)
        
    detail = (
        f"{setup_type} | Dist to Pivot: {dist_to_pivot_pct:+.1f}% | "
        f"NR7: {'Yes' if is_nr7 else 'No'} | IB: {'Yes' if is_inside_bar else 'No'} | "
        f"VDU: {'Yes' if is_vdu else 'No'} | Range: {today_range_pct*100:.1f}%"
    )
    
    return {
        "is_coiled": is_coiled,
        "is_extended": is_extended,
        "compression_score": comp_score,
        "setup_type": setup_type,
        "pivot_price": round(pivot_price, 2),
        "tight_stop_loss": round(tight_stop, 2),
        "dist_to_pivot_pct": round(dist_to_pivot_pct, 1),
        "is_nr7": is_nr7,
        "is_inside_bar": is_inside_bar,
        "is_vdu": is_vdu,
        "is_bb_squeeze": is_bb_squeeze,
        "detail": detail
    }
