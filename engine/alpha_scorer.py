"""
Alpha Scorer & Pre-Breakout Elite 5 Selector (v5.0)
===================================================
Implements the 100-Point Pre-Breakout Convergence Scoring Engine.
Penalizes late extended breakouts (> +4% above pivot) by -20 points.
Rewards tight pre-breakout volatility coils (NR7, Inside Bar, Doji, VDU, Squeeze).
Integrates F&O segment tagging.
"""

import pandas as pd
import numpy as np
from config.settings import (
    TIER_APEX_THRESHOLD, TIER_STRONG_THRESHOLD, TIER_CONFIRMED_THRESHOLD,
    MAX_SECTOR_CONCENTRATION
)
from engine.pattern_compression import detect_compression_pattern
from engine.pattern_vcp import detect_vcp_pattern
from engine.pattern_fibonacci import detect_fibonacci_golden_pocket
from engine.pattern_pocket_pivot import detect_pocket_pivot
from engine.fno_radar import is_fno_stock

def compute_alpha_score(symbol, df, bhav_row, fund_eval, sector_rank_df, signal_age=1, fno_set=None):
    """
    Computes the 100-Point Pre-Breakout Alpha Score for a single stock.
    """
    if df.empty or len(df) < 50:
        return None
        
    last = df.iloc[-1]
    close = float(last['Close'])
    vol = float(last['Volume'])
    vol50 = float(last.get('VOL50', 1.0))
    atr14 = float(last.get('ATR14', close * 0.03))
    deliv_pct = float(bhav_row.get('DELIV_PER', 40.0)) if bhav_row is not None else 40.0
    
    # -------------------------------------------------------------
    # 1. Pattern & Compression Analytics
    # -------------------------------------------------------------
    comp_res = detect_compression_pattern(df)
    vcp_res = detect_vcp_pattern(df)
    fib_res = detect_fibonacci_golden_pocket(df)
    pp_res = detect_pocket_pivot(df, deliv_pct)
    
    is_fno = is_fno_stock(symbol, fno_set)
    
    # -------------------------------------------------------------
    # LAYER 1: Technical Structure & Pre-Breakout Coiling (Max 30 pts)
    # -------------------------------------------------------------
    tech_pts = 0
    # Base Trend Template
    if close > last.get('SMA50', 0): tech_pts += 4
    if close > last.get('SMA200', 0): tech_pts += 4
    if last.get('SMA50', 0) > last.get('SMA200', 0): tech_pts += 4
    
    # Pre-Breakout Compression Points (up to 18 pts)
    tech_pts += min(18, int(comp_res['compression_score'] * 0.60))
    
    # -------------------------------------------------------------
    # LAYER 2: Volume Dry-Up & Institutional Footprint (Max 25 pts)
    # -------------------------------------------------------------
    vol_pts = 0
    vol_ratio = vol / max(1.0, vol50)
    
    # In pre-breakout setups, low volume (VDU) or Pocket Pivot accumulation is prized!
    if comp_res.get('is_vdu'): vol_pts += 12
    elif pp_res.get('is_pocket_pivot'): vol_pts += 10
    elif vol_ratio >= 1.5: vol_pts += 6
    else: vol_pts += 4
    
    if deliv_pct >= 55.0: vol_pts += 13
    elif deliv_pct >= 45.0: vol_pts += 9
    elif deliv_pct >= 35.0: vol_pts += 5
    
    # -------------------------------------------------------------
    # LAYER 3: Clean Relative Strength (RS) Rank (Max 20 pts)
    # -------------------------------------------------------------
    rs_pts = 0
    clean_rs = float(last.get('Clean_RS_Raw', 10.0))
    if clean_rs >= 30.0: rs_pts += 20
    elif clean_rs >= 20.0: rs_pts += 16
    elif clean_rs >= 12.0: rs_pts += 11
    elif clean_rs >= 5.0: rs_pts += 6
    
    # -------------------------------------------------------------
    # LAYER 4: Fundamental Quality Gate (Max 15 pts)
    # -------------------------------------------------------------
    fund_pts = fund_eval.get('fund_pts', 8)
    
    # -------------------------------------------------------------
    # LAYER 5: Sector Pole Position Tailwind (Max 10 pts)
    # -------------------------------------------------------------
    sector_pts = 0
    from engine.sector_pole import get_sector_for_symbol
    sec = get_sector_for_symbol(symbol)
    
    if not sector_rank_df.empty and 'sector' in sector_rank_df.columns:
        match = sector_rank_df[sector_rank_df['sector'] == sec]
        if not match.empty:
            cls = match['classification'].iloc[0]
            if cls == "POLE POSITION": sector_pts = 10
            elif cls == "IMPROVING": sector_pts = 6
            elif cls == "NEUTRAL": sector_pts = 3
    else:
        sector_pts = 4
        
    # Total Raw Alpha Score (Base 100)
    raw_alpha_score = tech_pts + vol_pts + rs_pts + fund_pts + sector_pts
    
    # -------------------------------------------------------------
    # THE EXTENSION PENALTY & LAUNCHPAD BOOST
    # -------------------------------------------------------------
    is_extended = comp_res.get('is_extended', False)
    dist_to_pivot = comp_res.get('dist_to_pivot_pct', 0.0)
    
    # If the stock has already exploded > 4.0% above its pivot, PENALIZE it!
    if is_extended:
        raw_alpha_score -= 20.0 # Heavy penalty: Do not buy extended tops!
    elif -3.8 <= dist_to_pivot <= 1.2:
        raw_alpha_score += 8.0  # Launchpad boost: Perfectly coiled under resistance!
        
    # F&O Liquidity bonus (Institutional grade, zero circuit lock)
    if is_fno:
        raw_alpha_score += 4.0
        
    # Clamp score to [0, 100]
    raw_alpha_score = max(0.0, min(100.0, raw_alpha_score))
    
    # Signal Decay Multiplier
    if signal_age <= 2: decay = 1.0
    elif signal_age <= 4: decay = 0.95
    elif signal_age <= 6: decay = 0.85
    else: decay = 0.75
    
    final_alpha_score = round(raw_alpha_score * decay, 1)
    
    # Conviction Tier Classification
    if final_alpha_score >= TIER_APEX_THRESHOLD: conviction = "APEX"
    elif final_alpha_score >= TIER_STRONG_THRESHOLD: conviction = "STRONG"
    elif final_alpha_score >= TIER_CONFIRMED_THRESHOLD: conviction = "CONFIRMED"
    else: conviction = "WATCHLIST"
    
    # Granular Setup Name Assignment
    comp_setup = comp_res.get('setup_type', 'None')
    if comp_setup not in ["None", "Consolidation Base", "Extended Past Pivot"]:
        primary_pattern = comp_setup
    elif pp_res.get('is_pocket_pivot'):
        primary_pattern = "Pocket Pivot"
    elif fib_res.get('is_fib_setup'):
        primary_pattern = "Fib Golden Pocket"
    elif vcp_res.get('pattern_name') not in ["None", "Base Consolidation"]:
        primary_pattern = vcp_res.get('pattern_name')
    else:
        primary_pattern = "Pre-Breakout Base"
        
    # Structural Pivot & Stop Loss
    pivot_p = comp_res.get('pivot_price', round(close * 1.01, 2))
    tight_stop = comp_res.get('tight_stop_loss', round(close * 0.94, 2))
    
    # Enforce maximum 8% initial stop floor
    hard_stop_floor = round(close * 0.92, 2)
    final_stop = round(max(hard_stop_floor, min(close * 0.985, tight_stop)), 2)
    
    return {
        "symbol": symbol,
        "sector": sec,
        "close": close,
        "pivot_price": pivot_p,
        "trigger_price": comp_res.get('trigger_price', round(close * 1.005, 2)),
        "stop_loss": final_stop,
        "alpha_score": final_alpha_score,
        "raw_score": raw_alpha_score,
        "conviction": conviction,
        "signal_age": signal_age,
        "pattern": primary_pattern,
        "is_coiled": comp_res.get('is_coiled', False),
        "is_extended": is_extended,
        "dist_to_pivot_pct": dist_to_pivot,
        "is_fno": is_fno,
        "is_nr7": comp_res.get('is_nr7', False),
        "is_inside_bar": comp_res.get('is_inside_bar', False),
        "is_vdu": comp_res.get('is_vdu', False),
        "tech_pts": tech_pts,
        "vol_pts": vol_pts,
        "rs_pts": rs_pts,
        "fund_pts": fund_pts,
        "sector_pts": sector_pts,
        "deliv_pct": round(deliv_pct, 1),
        "vol_ratio": round(vol_ratio, 2),
        "clean_rs": round(clean_rs, 1),
        "roe": fund_eval.get('roe', 0),
        "debt_equity": fund_eval.get('debt_equity', 0),
        "passes_fund_gate": fund_eval.get('passes_gate', False)
    }

def select_elite_five(scored_df):
    """
    Selects up to 5 top-ranked candidates prioritizing PRE-BREAKOUT COILING
    and enforcing sector diversification, positive Clean RS (>= 8.0), and fundamental excellence.
    Never selects already-extended stocks (>4% past pivot).
    """
    if scored_df.empty:
        return pd.DataFrame()
        
    # Reject already extended stocks!
    valid_pool = scored_df[scored_df['is_extended'] == False].copy()
    
    if valid_pool.empty:
        valid_pool = scored_df.copy()
        
    # Mandatory RS Gate: Coiling is only valid on market leaders (RS >= 8.0)
    elite_pool = valid_pool[
        (valid_pool['alpha_score'] >= 58.0) &
        (valid_pool['passes_fund_gate'] == True) &
        (valid_pool['signal_age'] <= 3) &
        (valid_pool['clean_rs'] >= 8.0)
    ].sort_values(
        by=['is_coiled', 'alpha_score', 'clean_rs'],
        ascending=[False, False, False]
    )
    
    if elite_pool.empty:
        # Fallback to RS >= 5.0
        elite_pool = valid_pool[valid_pool['clean_rs'] >= 5.0].sort_values(
            by=['is_coiled', 'alpha_score', 'clean_rs'],
            ascending=[False, False, False]
        )
        
    selected = []
    sector_counts = {}
    
    for _, row in elite_pool.iterrows():
        if len(selected) >= 5:
            break
        sec = row['sector']
        if sector_counts.get(sec, 0) >= MAX_SECTOR_CONCENTRATION:
            continue
        selected.append(row)
        sector_counts[sec] = sector_counts.get(sec, 0) + 1
        
    return pd.DataFrame(selected)
