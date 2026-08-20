"""
Fibonacci Golden Pocket Module
==============================
Detects 0.50 - 0.618 Fibonacci retracement pullbacks with 20 EMA / 50 SMA confluence.
"""

import pandas as pd
import numpy as np
from config.settings import FIB_GOLDEN_POCKET_LOW, FIB_GOLDEN_POCKET_HIGH, FIB_MA_TOLERANCE_PCT

def detect_fibonacci_golden_pocket(df):
    """
    Scans for high-RR pullback entries at the 50% - 61.8% Fibonacci zone.
    Returns: dict with is_fib_setup, fib_score (0 to 30), entry_zone, stop_loss, target_price
    """
    if df.empty or len(df) < 60:
        return {"is_fib_setup": False, "fib_score": 0, "fib_50": 0.0, "fib_618": 0.0, "stop_loss": 0.0, "detail": "Insufficient history"}
        
    last = df.iloc[-1]
    close = last['Close']
    ema20 = last.get('EMA20', 0)
    sma50 = last.get('SMA50', 0)
    
    # 1. Identify Swing High and Swing Low
    lookback = min(60, len(df))
    swing_window = df.iloc[-lookback:]
    swing_high = swing_window['High'].max()
    swing_low = swing_window['Low'].min()
    
    if swing_high <= swing_low or swing_high == 0:
        return {"is_fib_setup": False, "fib_score": 0, "detail": "Invalid swing"}
        
    impulse_move_pct = (swing_high - swing_low) / swing_low
    
    # Impulse move must be strong (+20% or more)
    if impulse_move_pct < 0.18:
        return {"is_fib_setup": False, "fib_score": 0, "detail": f"Weak impulse ({impulse_move_pct*100:.1f}%)"}
        
    # 2. Compute Fibonacci Retracements
    range_span = swing_high - swing_low
    fib_382 = swing_high - (0.382 * range_span)
    fib_500 = swing_high - (FIB_GOLDEN_POCKET_LOW * range_span)
    fib_618 = swing_high - (FIB_GOLDEN_POCKET_HIGH * range_span)
    fib_786 = swing_high - (0.786 * range_span)
    
    # 3. Check if current price is inside Golden Pocket zone [Fib 50% to 61.8%] (with slight tolerance)
    in_golden_pocket = (close <= (fib_382 * 1.02)) and (close >= (fib_618 * 0.98))
    
    if not in_golden_pocket:
        return {"is_fib_setup": False, "fib_score": 0, "detail": "Outside Golden Pocket"}
        
    # 4. Moving Average Confluence Check (Overlap with 20 EMA or 50 SMA)
    has_ema20_confluence = abs(close - ema20) / close <= FIB_MA_TOLERANCE_PCT
    has_sma50_confluence = abs(close - sma50) / close <= FIB_MA_TOLERANCE_PCT
    has_confluence = has_ema20_confluence or has_sma50_confluence
    
    # 5. Bullish Reversal Check (Hammer / Lower Shadow or Green Close)
    candle_body = abs(close - last['Open'])
    lower_shadow = min(close, last['Open']) - last['Low']
    is_reversal = (lower_shadow > candle_body) or (close > last['Open'])
    
    # 6. Fibonacci Alpha Score (0 to 30 pts)
    fib_score = 15 # Base Golden Pocket
    if has_confluence: fib_score += 8
    if is_reversal: fib_score += 7
    
    # Suggested Risk/Reward parameters
    stop_loss = round(float(fib_786), 2)
    target_price = round(float(swing_high * 1.05), 2)
    risk_pct = round(float((close - stop_loss) / close * 100), 2)
    reward_pct = round(float((target_price - close) / close * 100), 2)
    rr_ratio = round(reward_pct / max(0.5, risk_pct), 2)
    
    detail = f"Golden Pocket (50-61.8%) | MA Confluence: {'Yes' if has_confluence else 'No'} | Reversal: {'Yes' if is_reversal else 'No'} | Est. RR: 1:{rr_ratio}"
    
    return {
        "is_fib_setup": True,
        "fib_score": fib_score,
        "fib_50": round(float(fib_500), 2),
        "fib_618": round(float(fib_618), 2),
        "stop_loss": stop_loss,
        "target_price": target_price,
        "risk_pct": risk_pct,
        "rr_ratio": rr_ratio,
        "detail": detail
    }
