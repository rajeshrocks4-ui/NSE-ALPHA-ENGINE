"""
NSE Alpha Breakout Engine - Master Orchestrator (v5.0)
======================================================
Autonomous pipeline executing:
1. Dynamic Universe Ingestion from NSE Bhavcopy (All active NSE equities)
2. Market Regime & Breadth Evaluation (13-Point Composite Model)
3. Sector Relative Strength & Pole Position Ranking
4. Fundamental Quality Gate (ROE > 15%, D/E < 1.0)
5. Pre-Breakout Coiling & Volatility Compression Scoring (NR7, Inside Bar, Doji, VDU, Squeeze)
6. Institutional F&O Derivatives Radar (Futures & Call Option Squeeze Setups)
7. Dynamic Position Sizing & Chandelier ATR Trailing Stop Updates
8. Report Generation & Mobile Notifications (Telegram / Discord)
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config.settings import (
    ACCOUNT_CAPITAL, RISK_PER_TRADE_PCT, REPORTS_DIR,
    PERFORMANCE_DIR, BASE_DIR
)
from engine.data_pipeline import fetch_latest_bhavcopy, fetch_delivery_data, load_universe, fetch_price_matrices
from engine.market_regime import compute_market_regime
from engine.sector_pole import compute_sector_rankings
from engine.fundamental_gate import load_fundamental_cache, evaluate_fundamentals
from engine.alpha_scorer import compute_alpha_score, select_elite_five
from engine.risk_manager import calculate_position_size, update_performance_scorecard
from engine.fno_radar import get_fno_universe, generate_fno_radar_table
from engine.notifier import format_elite_five_alert, send_telegram_alert, send_discord_alert

def run_pipeline():
    today = datetime.now()
    today_str = today.strftime("%Y%m%d")
    today_display = today.strftime("%d %b %Y")
    
    print("=" * 80)
    print(f"  🏛️ NSE ALPHA BREAKOUT ENGINE v5.0 — {today_display}")
    print("  Pre-Breakout Coiling Engine & Institutional F&O Radar")
    print("  NR7 | Inside Bar | Doji | VDU | Bollinger Squeeze | Leading Sectors")
    print("=" * 80)
    
    # -------------------------------------------------------------
    # Step 1: Market Data Ingestion & Official Delivery Metrics
    # -------------------------------------------------------------
    print("\n[1/6] Ingesting Market Data & Delivery Position...")
    bhav_df = fetch_latest_bhavcopy()
    if bhav_df is None or bhav_df.empty:
        print("[Error] Failed to load Bhavcopy. Aborting scan.")
        return
        
    deliv_map = fetch_delivery_data()
    bhav_lookup = {}
    col_map = {str(c).upper(): c for c in bhav_df.columns}
    sym_col = col_map.get('TCKRSYMB', col_map.get('SYMBOL', ''))
    if sym_col:
        for _, row in bhav_df.iterrows():
            sym_clean = str(row[sym_col]).strip().upper()
            sym_key = f"{sym_clean}.NS"
            row_dict = row.to_dict()
            # Attach official delivery percentage from NSE MTO report
            if sym_key in deliv_map:
                row_dict['DELIV_PER'] = deliv_map[sym_key]
            elif sym_clean in deliv_map:
                row_dict['DELIV_PER'] = deliv_map[sym_clean]
            bhav_lookup[sym_key] = row_dict
            bhav_lookup[sym_clean] = row_dict
            
    universe_tickers = load_universe(bhav_df)
    price_matrices = fetch_price_matrices(universe_tickers, period="1y", batch_size=200)
    
    if not price_matrices:
        print("[Error] Failed to generate price matrices. Aborting scan.")
        return
        
    print(f"  [Data] Successfully processed {len(price_matrices)} clean active NSE equity series.")
    
    # -------------------------------------------------------------
    # Step 2: Market Regime & Breadth
    # -------------------------------------------------------------
    print("\n[2/6] Evaluating Market Regime & Breadth...")
    regime, regime_score, regime_metrics = compute_market_regime(price_matrices)
    print(f"  [+] Regime: {regime} (Score: {regime_score}/13) | Guideline: {regime_metrics['position_size_pct']}% Position Size")
    
    # -------------------------------------------------------------
    # Step 3: Sector Relative Strength & Pole Position
    # -------------------------------------------------------------
    print("\n[3/6] Computing Sector Rotation & Pole Position...")
    sector_df = compute_sector_rankings(price_matrices)
    pole_sectors = sector_df[sector_df['classification'] == "POLE POSITION"]['sector'].tolist() if not sector_df.empty else []
    print(f"  [+] Pole Position Sectors: {', '.join(pole_sectors) if pole_sectors else 'Broad Market Convergence'}")
    
    # -------------------------------------------------------------
    # Step 4: Fundamental Quality Cache & F&O Universe
    # -------------------------------------------------------------
    print("\n[4/6] Loading Fundamental Quality Cache & F&O Universe...")
    fund_cache = load_fundamental_cache()
    fno_set = get_fno_universe()
    print(f"  [+] Fundamental profiles loaded: {len(fund_cache)} stocks.")
    print(f"  [+] Active F&O Derivatives universe: {len(fno_set)} institutional stocks.")
    
    # -------------------------------------------------------------
    # Step 5: Pre-Breakout Alpha Scoring & Coiling Recognition
    # -------------------------------------------------------------
    print("\n[5/6] Executing 100-Point Pre-Breakout Coiling Matrix...")
    scored_results = []
    
    for symbol, df in price_matrices.items():
        bhav_row = bhav_lookup.get(symbol)
        fund_eval = evaluate_fundamentals(symbol, fund_cache)
        res = compute_alpha_score(symbol, df, bhav_row, fund_eval, sector_df, signal_age=1, fno_set=fno_set)
        if res:
            scored_results.append(res)
            
    scored_df = pd.DataFrame(scored_results)
    if scored_df.empty:
        print("[Warn] No candidates passed basic filters.")
        return
        
    scored_df = scored_df.sort_values(
        by=['is_coiled', 'alpha_score', 'clean_rs'],
        ascending=[False, False, False]
    ).reset_index(drop=True)
    
    elite_five = select_elite_five(scored_df)
    fno_radar = generate_fno_radar_table(scored_df, top_n=5)
    
    # -------------------------------------------------------------
    # Step 6: Risk Management & Report Generation
    # -------------------------------------------------------------
    print("\n[6/6] Updating Performance Scorecard & Generating Reports...")
    update_performance_scorecard(elite_five, price_matrices, today_str)
    
    # Generate Markdown Report
    report_file = REPORTS_DIR / f"Master_Alpha_Report_{today_str}.md"
    
    lines = [
        f"# 🎯 NSE Master Alpha Report — {today_display}",
        f"> **Alpha Engine v5.0** | Pre-Breakout Coiling Engine | Market Regime: **{regime}** ({regime_metrics['position_size_pct']}% Sizing)",
        "",
        "---",
        "## 💎 THE PRE-BREAKOUT ELITE 5 — COILED SPRINGS",
        "> **Catching explosive moves BEFORE they happen:** NR7 / Inside Bar / Doji / VDU / Squeeze + Near Pivot (-3.8% to +1.2%) + ROE > 15% + Sector Tailwind",
        "",
        "| Symbol | Segment | Sector | Setup Classification | Close | Buy Trigger | Stop Loss | Deliv % | Clean RS | Alpha Score | Est. Shares | Capital Req | R/R |",
        "|--------|:-------:|--------|----------------------|-------|:-----------:|-----------|:-------:|:--------:|:-----------:|:-----------:|:-----------:|:---:|"
    ]
    
    regime_mult = regime_metrics['position_size_pct'] / 100.0
    
    if not elite_five.empty:
        for _, r in elite_five.iterrows():
            shares, inv, risk_p = calculate_position_size(r['close'], r['stop_loss'], regime_mult)
            fno_badge = "🔥 `F&O`" if r.get('is_fno') else "⚡ `CASH`"
            trigger_p = r.get('trigger_price', r['close'] * 1.005)
            lines.append(
                f"| **{r['symbol']}** | {fno_badge} | {r['sector']} | `{r['pattern']}` | "
                f"₹{r['close']:.1f} | `₹{trigger_p:.1f}` | ₹{r['stop_loss']:.1f} | {r['deliv_pct']}% | {r['clean_rs']} | 🟢 **{r['alpha_score']:.1f}** | "
                f"{shares} | ₹{inv:,.0f} | 1:5+ |"
            )
    else:
        lines.append("| *No candidates met the strict pre-breakout coiling criteria today.* | | | | | | | | | | | | |")
        
    # F&O Derivatives Radar Section
    lines.extend([
        "",
        "---",
        "## ⚡ INSTITUTIONAL F&O DERIVATIVES RADAR",
        "> **Top 5 Liquid F&O Coils:** Infinite liquidity, zero circuit freeze, ideal for **Cash, Futures, or ATM/OTM Call Options** before IV surge.",
        "",
        "| Rank | Symbol | Sector | Setup Pattern | Close | Buy Trigger | Stop Loss | Deliv % | Clean RS | Alpha Score |",
        "|:----:|--------|--------|---------------|-------|:-----------:|-----------|:-------:|:--------:|:-----------:|"
    ])
    
    if not fno_radar.empty:
        for idx, r in fno_radar.iterrows():
            trigger_p = r.get('trigger_price', r['close'] * 1.005)
            lines.append(
                f"| {idx+1} | **{r['symbol']}** | {r['sector']} | `{r['pattern']}` | "
                f"₹{r['close']:.1f} | `₹{trigger_p:.1f}` | ₹{r['stop_loss']:.1f} | {r['deliv_pct']}% | {r['clean_rs']} | 🟢 **{r['alpha_score']:.1f}** |"
            )
    else:
        lines.append("| *No F&O stocks currently resting in launchpad coiling zone.* | | | | | | | | | |")
        
    # Market Regime Dashboard
    lines.extend([
        "",
        "---",
        f"## 📊 Market Regime Dashboard: {regime} ({regime_score}/13)",
        f"> **Action:** {regime_metrics['action']}",
        "",
        "| Indicator | Value | Status |",
        "|-----------|-------|--------|",
        f"| % Above 50 SMA | {regime_metrics['pct_above_50ma']}% | {'🟢 Bullish' if regime_metrics['pct_above_50ma'] >= 60 else ('🟡 Neutral' if regime_metrics['pct_above_50ma'] >= 45 else '🔴 Bearish')} |",
        f"| % Above 150 SMA | {regime_metrics['pct_above_150ma']}% | {'🟢 Bullish' if regime_metrics['pct_above_150ma'] >= 55 else ('🟡 Neutral' if regime_metrics['pct_above_150ma'] >= 40 else '🔴 Bearish')} |",
        f"| % Above 200 SMA | {regime_metrics['pct_above_200ma']}% | {'🟢 Bullish' if regime_metrics['pct_above_200ma'] >= 55 else ('🟡 Neutral' if regime_metrics['pct_above_200ma'] >= 40 else '🔴 Bearish')} |",
        f"| 52W High / Low Ratio | {regime_metrics['nh_nl_ratio']} | {'🟢 Bullish' if regime_metrics['nh_nl_ratio'] >= 2.0 else '🟡 Neutral'} |",
        "",
        "---",
        "## 🔥 Full Conviction Watchlist (APEX & STRONG Tiers)",
        "> *Unextended candidates with superior Relative Strength and Volume footprint.*",
        "",
        "| Rank | Symbol | Segment | Sector | Setup Pattern | Price | Stop Loss | Deliv % | Clean RS | Alpha Score |",
        "|:----:|--------|:-------:|--------|---------------|-------|-----------|:-------:|:--------:|:-----------:|"
    ])
    
    top_candidates = scored_df[
        (scored_df['conviction'].isin(['APEX', 'STRONG', 'CONFIRMED'])) &
        (scored_df['is_extended'] == False)
    ].head(15)
    
    for idx, r in top_candidates.iterrows():
        fno_badge = "F&O" if r.get('is_fno') else "CASH"
        lines.append(
            f"| {idx+1} | **{r['symbol']}** | `{fno_badge}` | {r['sector']} | `{r['pattern']}` | "
            f"₹{r['close']:.1f} | ₹{r['stop_loss']:.1f} | {r['deliv_pct']}% | {r['clean_rs']} | **{r['alpha_score']:.1f}** |"
        )
        
    lines.extend([
        "",
        "---",
        "## 📖 Pre-Breakout Execution Rules",
        "1. **Never buy extended > +4.0% past pivot:** The highest R/R trades happen inside the coil, NOT after the run.",
        "2. **Fixed 1.0% Account Risk & 20% Max Position:** Tight stops (1.5% to 3.0%) allow larger shares safely.",
        "3. **Chandelier ATR Trailing Stop:** Trail stops at `Peak Price - (3 * ATR14)` as stock advances into Stage 2.",
        "4. **Breakeven Rule:** When position reaches **+8.0%**, automatically move stop loss to entry price.",
        "",
        f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')} | Automated via GitHub Actions*"
    ])
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"\n[+] Master Alpha Report saved to: {report_file}")
    print(f"[+] Performance Scorecard updated in: performance/scorecard.md")
    
    # -------------------------------------------------------------
    # Step 7: Push Notifications (Telegram / Discord)
    # -------------------------------------------------------------
    alert_msg = format_elite_five_alert(elite_five, regime, regime_metrics, today_display, fno_radar)
    
    if send_telegram_alert(alert_msg):
        print("  [+] Dispatched Telegram notification successfully.")
    if send_discord_alert(alert_msg):
        print("  [+] Dispatched Discord notification successfully.")

if __name__ == "__main__":
    run_pipeline()
