"""
Risk Manager & Position Sizer
=============================
Calculates fixed-fractional position sizes and dynamic Chandelier ATR trailing stops.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from config.settings import (
    ACCOUNT_CAPITAL, RISK_PER_TRADE_PCT, ATR_STOP_MULTIPLIER,
    PERFORMANCE_DIR, BREAKEVEN_TRIGGER_PCT
)

TRADE_HISTORY_FILE = PERFORMANCE_DIR / "trade_history.csv"
SCORECARD_FILE = PERFORMANCE_DIR / "scorecard.md"

def calculate_position_size(entry_price, stop_price, regime_multiplier=1.0):
    """
    Computes exact shares to buy risking fixed 1.0% account capital adjusted by market regime.
    """
    if entry_price <= stop_price or entry_price <= 0:
        return 0, 0.0, 0.0
        
    dollar_risk = (ACCOUNT_CAPITAL * RISK_PER_TRADE_PCT) * regime_multiplier
    risk_per_share = entry_price - stop_price
    
    shares = int(np.floor(dollar_risk / risk_per_share))
    total_investment = round(shares * entry_price, 2)
    risk_pct_on_entry = round((risk_per_share / entry_price) * 100.0, 2)
    
    return shares, total_investment, risk_pct_on_entry

def update_performance_scorecard(today_picks_df, price_matrices, today_str):
    """
    Updates the trade history journal and generates the Markdown Scorecard.
    """
    if TRADE_HISTORY_FILE.exists():
        try: history_df = pd.read_csv(TRADE_HISTORY_FILE)
        except: history_df = pd.DataFrame()
    else:
        history_df = pd.DataFrame()
        
    # Append new picks
    new_entries = []
    if not today_picks_df.empty:
        for _, row in today_picks_df.iterrows():
            sym = row['symbol']
            entry_p = float(row['close'])
            stop_p = float(row.get('stop_loss', entry_p * 0.95))
            shares, inv, risk_pct = calculate_position_size(entry_p, stop_p)
            
            new_entries.append({
                "entry_date": today_str,
                "symbol": sym,
                "conviction": row['conviction'],
                "pattern": row['pattern'],
                "entry_price": entry_p,
                "stop_price": stop_p,
                "current_price": entry_p,
                "peak_price": entry_p,
                "shares": shares,
                "investment": inv,
                "risk_pct": risk_pct,
                "pnl_pct": 0.0,
                "status": "OPEN",
                "days_held": 0
            })
            
    if new_entries:
        new_df = pd.DataFrame(new_entries)
        if not history_df.empty:
            # Avoid duplicate same-day entries
            mask = ~new_df['symbol'].isin(history_df[history_df['entry_date'] == today_str]['symbol'])
            history_df = pd.concat([history_df, new_df[mask]], ignore_index=True)
        else:
            history_df = new_df
            
    # Mark to market and trailing stop update
    if not history_df.empty and price_matrices:
        for idx, row in history_df[history_df['status'] == 'OPEN'].iterrows():
            sym = row['symbol']
            df_hist = price_matrices.get(sym)
            if df_hist is not None and not df_hist.empty:
                curr_p = float(df_hist['Close'].iloc[-1])
                new_peak = max(float(row.get('peak_price', row['entry_price'])), float(df_hist['High'].iloc[-1]))
                entry_p = float(row['entry_price'])
                
                # Trailing Stop Calculation
                atr14 = float(df_hist.get('ATR14', pd.Series([curr_p * 0.03])).iloc[-1])
                trailing_stop = round(new_peak - (ATR_STOP_MULTIPLIER * atr14), 2)
                
                # Move to breakeven if up +8%
                if (new_peak - entry_p) / entry_p >= BREAKEVEN_TRIGGER_PCT:
                    trailing_stop = max(trailing_stop, entry_p)
                    
                cur_stop = max(float(row['stop_price']), trailing_stop)
                
                pnl = round(((curr_p - entry_p) / entry_p) * 100.0, 2)
                
                history_df.at[idx, 'current_price'] = curr_p
                history_df.at[idx, 'peak_price'] = new_peak
                history_df.at[idx, 'stop_price'] = cur_stop
                history_df.at[idx, 'pnl_pct'] = pnl
                history_df.at[idx, 'days_held'] = int(row.get('days_held', 0)) + 1
                
                # Check Stop Out
                if curr_p <= cur_stop:
                    history_df.at[idx, 'status'] = 'STOPPED_OUT'
                    
        history_df.to_csv(TRADE_HISTORY_FILE, index=False)
        
    # Generate Scorecard Markdown
    lines = [
        "# 🛡️ Real-Time Performance & P&L Scorecard",
        f"> **Last Updated:** {today_str} | **Chandelier ATR Trailing Stops Active**",
        "",
        "## Overall Portfolio Statistics",
    ]
    
    if not history_df.empty:
        total_trades = len(history_df)
        open_pos = len(history_df[history_df['status'] == 'OPEN'])
        closed = history_df[history_df['status'] != 'OPEN']
        
        lines.append(f"- **Total Signal Journal Entries:** {total_trades}")
        lines.append(f"- **Currently Open Positions:** {open_pos}")
        
        if not closed.empty:
            wins = len(closed[closed['pnl_pct'] > 0])
            win_rate = (wins / len(closed)) * 100.0
            avg_win = closed[closed['pnl_pct'] > 0]['pnl_pct'].mean() if wins > 0 else 0
            avg_loss = closed[closed['pnl_pct'] <= 0]['pnl_pct'].mean() if len(closed) - wins > 0 else 0
            rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            lines.append(f"- **Closed Trade Win Rate:** {win_rate:.1f}% ({wins}/{len(closed)})")
            lines.append(f"- **Average Winner:** 🟢 +{avg_win:.2f}%")
            lines.append(f"- **Average Loser:** 🔴 {avg_loss:.2f}%")
            lines.append(f"- **Realized Risk/Reward (R/R):** 1 : {rr_ratio:.2f}")
            
        lines.append("")
        lines.append("## Top 5 Active Open Runners")
        lines.append("| Symbol | Pattern | Entry | Current | Peak | Stop Loss | P&L % | Days |")
        lines.append("|--------|---------|-------|---------|------|-----------|-------|------|")
        
        top_open = history_df[history_df['status'] == 'OPEN'].sort_values("pnl_pct", ascending=False).head(5)
        for _, r in top_open.iterrows():
            lines.append(f"| **{r['symbol']}** | {r['pattern']} | ₹{r['entry_price']:.1f} | ₹{r['current_price']:.1f} | ₹{r['peak_price']:.1f} | ₹{r['stop_price']:.1f} | 🟢 **+{r['pnl_pct']:.2f}%** | {r['days_held']}d |")
            
    with open(SCORECARD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    return SCORECARD_FILE
