"""
Alpha Scorer & Elite 5 Selector
===============================
Implements the 100-Point Multi-Layer Convergence Scoring Engine and selects The Elite 5.
"""

import pandas as pd
import numpy as np
from config.settings import (
    TIER_APEX_THRESHOLD, TIER_STRONG_THRESHOLD, TIER_CONFIRMED_THRESHOLD,
    MAX_SECTOR_CONCENTRATION
)

def compute_alpha_score(symbol, df, bhav_row, fund_eval, sector_rank_df, signal_age=1):
    """
    Computes the 100-Point Institutional Alpha Score for a single stock.
    """
    if df.empty or len(df) < 50:
        return None
        
    last = df.iloc[-1]
    close = float(last['Close'])
    vol = float(last['Volume'])
    vol50 = float(last.get('VOL50', 1))
    
    # -------------------------------------------------------------
    # LAYER 1: Technical Structure & Patterns (Max 30 pts)
    # -------------------------------------------------------------
    from engine.pattern_vcp import detect_vcp_pattern
    from engine.pattern_fibonacci import detect_fibonacci_golden_pocket
    from engine.pattern_pocket_pivot import detect_pocket_pivot
    
    deliv_pct = float(bhav_row.get('DELIV_PER', 40.0)) if bhav_row is not None else 40.0
    
    vcp_res = detect_vcp_pattern(df)
    fib_res = detect_fibonacci_golden_pocket(df)
    pp_res = detect_pocket_pivot(df, deliv_pct)
    
    tech_pts = 0
    # Base Trend Template
    if close > last.get('SMA50', 0): tech_pts += 5
    if close > last.get('SMA200', 0): tech_pts += 5
    if last.get('SMA50', 0) > last.get('SMA200', 0): tech_pts += 5
    
    # Best Pattern Bonus
    pattern_score = max(vcp_res['vcp_score'], fib_res['fib_score'], pp_res['pp_score'])
    tech_pts += min(15, int(pattern_score / 2.0))
    
    # -------------------------------------------------------------
    # LAYER 2: Volume & Institutional Delivery (Max 25 pts)
    # -------------------------------------------------------------
    vol_pts = 0
    vol_ratio = vol / max(1.0, vol50)
    
    if vol_ratio >= 2.0: vol_pts += 12
    elif vol_ratio >= 1.5: vol_pts += 8
    elif vol_ratio >= 1.0: vol_pts += 5
    
    if deliv_pct >= 55.0: vol_pts += 13
    elif deliv_pct >= 45.0: vol_pts += 8
    elif deliv_pct >= 35.0: vol_pts += 4
    
    # -------------------------------------------------------------
    # LAYER 3: Relative Strength Clean Rank (Max 20 pts)
    # -------------------------------------------------------------
    rs_pts = 0
    clean_rs = float(last.get('Clean_RS_Raw', 10.0))
    if clean_rs >= 30.0: rs_pts += 20
    elif clean_rs >= 20.0: rs_pts += 15
    elif clean_rs >= 12.0: rs_pts += 10
    elif clean_rs >= 5.0: rs_pts += 5
    
    # -------------------------------------------------------------
    # LAYER 4: Fundamental Quality Gate (Max 15 pts)
    # -------------------------------------------------------------
    fund_pts = fund_eval.get('fund_pts', 10)
    
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
        sector_pts = 5
        
    # Total Raw Alpha Score (Max 100)
    raw_alpha_score = tech_pts + vol_pts + rs_pts + fund_pts + sector_pts
    
    # Signal Decay Multiplier (Prevents zombie setups)
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
    
    # Pattern tag
    primary_pattern = "VCP Coiling" if vcp_res['is_vcp'] else ("Fib Golden Pocket" if fib_res['is_fib_setup'] else ("Pocket Pivot" if pp_res['is_pocket_pivot'] else "Base Consolidation"))
    
    # Structural Stop Loss & Pivot Price
    atr14 = float(last.get('ATR14', close * 0.03))
    vcp_pivot = vcp_res.get('pivot_price', 0.0)
    fib_pivot = fib_res.get('fib_50', 0.0)
    pivot_p = vcp_pivot if vcp_pivot > 0 else (fib_pivot if fib_pivot > 0 else round(close * 1.01, 2))
    
    suggested_stop = fib_res.get('stop_loss', 0.0) if fib_res.get('is_fib_setup') and fib_res.get('stop_loss', 0) > 0 else round(close - (2.5 * atr14), 2)
    
    return {
        "symbol": symbol,
        "sector": sec,
        "close": close,
        "pivot_price": pivot_p,
        "stop_loss": suggested_stop,
        "alpha_score": final_alpha_score,
        "raw_score": raw_alpha_score,
        "conviction": conviction,
        "signal_age": signal_age,
        "pattern": primary_pattern,
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
    Selects up to 5 top-ranked candidates enforcing sector diversification and fundamental excellence.
    """
    if scored_df.empty:
        return pd.DataFrame()
        
    # Strict Filters: Alpha >= 70, Fund Gate Passed, Signal Age <= 3
    elite_pool = scored_df[
        (scored_df['alpha_score'] >= 70.0) &
        (scored_df['passes_fund_gate'] == True) &
        (scored_df['signal_age'] <= 3)
    ].sort_values("alpha_score", ascending=False)
    
    if elite_pool.empty:
        # Fallback to top scored if strict pool is narrow
        elite_pool = scored_df.sort_values("alpha_score", ascending=False)
        
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
