#!/usr/bin/env python3
"""
NSE Alpha Engine - Master Orchestrator
======================================
Coordinates the Quad-Engine Breakout Pipeline:
1. Data Pipeline (Bhavcopy + yfinance)
2. Market Regime & Position Sizing
3. Sector Pole Position
4. VCP / Fibonacci / Pocket Pivot Detection
5. Fundamental Quality Gating
6. 100-Point Alpha Scoring & The Elite 5
7. Real-Time Risk Management & Scorecard
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# Add root directory to python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure UTF-8 output on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config.settings import REPORTS_DIR, ACCOUNT_CAPITAL
from engine.data_pipeline import fetch_latest_bhavcopy, load_universe, fetch_price_matrices
from engine.market_regime import compute_market_regime
from engine.sector_pole import compute_sector_rankings
from engine.fundamental_gate import load_fundamental_cache, evaluate_fundamentals
from engine.alpha_scorer import compute_alpha_score, select_elite_five
from engine.risk_manager import update_performance_scorecard, calculate_position_size

def run_pipeline():
    today_str = datetime.now().strftime("%Y%m%d")
    today_display = datetime.now().strftime("%d %b %Y")
    
    print("=" * 80)
    print(f"  🏛️ NSE ALPHA BREAKOUT ENGINE v4.5 — {today_display}")
    print("  Quad-Engine: VCP Coiling | Fib Golden Pocket | Pocket Pivot | Stage 2 Base")
    print("=" * 80)
    
    # -------------------------------------------------------------
    # Step 1: Load Data
    # -------------------------------------------------------------
    print("\n[1/6] Ingesting Market Data...")
    bhav_df = fetch_latest_bhavcopy()
    bhav_lookup = {}
    if not bhav_df.empty:
        bhav_df.columns = [c.strip().upper() for c in bhav_df.columns]
        sym_col = 'TCKRSYMB' if 'TCKRSYMB' in bhav_df.columns else ('SYMBOL' if 'SYMBOL' in bhav_df.columns else '')
        if sym_col:
            clean_bhav = bhav_df.drop_duplicates(subset=[sym_col])
            bhav_lookup = clean_bhav.set_index(sym_col).to_dict(orient='index')
        print(f"  [+] Loaded Bhavcopy: {len(bhav_df)} entries with delivery metrics.")
        
    tickers = load_universe(bhav_df=bhav_df)
    price_matrices = fetch_price_matrices(tickers, period="1y")
    
    if not price_matrices:
        print("[Error] No price matrices available. Exiting.")
        return
        
    # -------------------------------------------------------------
    # Step 2: Market Regime & Sizing
    # -------------------------------------------------------------
    print("\n[2/6] Evaluating Market Regime & Breadth...")
    regime, regime_score, regime_metrics = compute_market_regime(price_matrices)
    print(f"  [+] Regime: {regime} (Score: {regime_score}/13) | Guideline: {regime_metrics['position_size_pct']}% Position Size")
    
    # -------------------------------------------------------------
    # Step 3: Sector Rotation & Pole Position
    # -------------------------------------------------------------
    print("\n[3/6] Computing Sector Rotation & Pole Position...")
    sector_df = compute_sector_rankings(price_matrices)
    if not sector_df.empty:
        pole_sectors = sector_df[sector_df['classification'] == "POLE POSITION"]['sector'].tolist()
        print(f"  [+] Pole Position Sectors: {', '.join(pole_sectors) if pole_sectors else 'None'}")
        
    # -------------------------------------------------------------
    # Step 4: Fundamental Quality Gate
    # -------------------------------------------------------------
    print("\n[4/6] Loading Fundamental Quality Cache...")
    fund_cache = load_fundamental_cache()
    print(f"  [+] Fundamental profiles loaded: {len(fund_cache)} stocks.")
    
    # -------------------------------------------------------------
    # Step 5: Alpha Scoring & Pattern Recognition
    # -------------------------------------------------------------
    print("\n[5/6] Executing 100-Point Alpha Convergence Matrix...")
    scored_results = []
    
    for symbol, df in price_matrices.items():
        bhav_row = bhav_lookup.get(symbol)
        fund_eval = evaluate_fundamentals(symbol, fund_cache)
        res = compute_alpha_score(symbol, df, bhav_row, fund_eval, sector_df, signal_age=1)
        if res:
            scored_results.append(res)
            
    scored_df = pd.DataFrame(scored_results)
    if scored_df.empty:
        print("[Warn] No candidates passed basic filters.")
        return
        
    scored_df = scored_df.sort_values("alpha_score", ascending=False).reset_index(drop=True)
    elite_five = select_elite_five(scored_df)
    
    # -------------------------------------------------------------
    # Step 6: Risk Management & Report Generation
    # -------------------------------------------------------------
    print("\n[6/6] Updating Performance Scorecard & Generating Reports...")
    update_performance_scorecard(elite_five, price_matrices, today_str)
    
    # Generate Markdown Report
    report_file = REPORTS_DIR / f"Master_Alpha_Report_{today_str}.md"
    
    lines = [
        f"# 🎯 NSE Master Alpha Report — {today_display}",
        f"> **Alpha Engine v4.5** | Quad-Engine Convergence | Market Regime: **{regime}** ({regime_metrics['position_size_pct']}% Sizing)",
        "",
        "---",
        "## 💎 THE ELITE 5 — RIPE TO BUY",
        "> **Mathematical Convergence:** VCP / Fib Golden Pocket / Pocket Pivot + ROE > 15% + D/E < 1.0 + Sector Tailwind",
        "",
        "| Symbol | Sector | Pattern | Price | Stop Loss | Alpha Score | Est. Shares | Capital Req | R/R |",
        "|--------|--------|---------|-------|-----------|-------------|-------------|-------------|-----|"
    ]
    
    regime_mult = regime_metrics['position_size_pct'] / 100.0
    
    if not elite_five.empty:
        for _, r in elite_five.iterrows():
            shares, inv, risk_p = calculate_position_size(r['close'], r['stop_loss'], regime_mult)
            lines.append(f"| **{r['symbol']}** | {r['sector']} | `{r['pattern']}` | ₹{r['close']:.1f} | ₹{r['stop_loss']:.1f} | 🟢 **{r['alpha_score']:.1f}** | {shares} | ₹{inv:,.0f} | 1:4+ |")
    else:
        lines.append("| *No candidates met the 100% strict convergence today.* | | | | | | | | |")
        
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
        "## 🔥 Top Conviction Setups (APEX & STRONG Tiers)",
        "",
        "| Rank | Symbol | Sector | Pattern | Price | Stop Loss | Deliv % | Clean RS | Alpha Score |",
        "|------|--------|--------|---------|-------|-----------|---------|----------|-------------|"
    ])
    
    top_candidates = scored_df[scored_df['conviction'].isin(['APEX', 'STRONG', 'CONFIRMED'])].head(15)
    for idx, r in top_candidates.iterrows():
        lines.append(f"| {idx+1} | **{r['symbol']}** | {r['sector']} | `{r['pattern']}` | ₹{r['close']:.1f} | ₹{r['stop_loss']:.1f} | {r['deliv_pct']}% | {r['clean_rs']} | **{r['alpha_score']:.1f}** |")
        
    lines.extend([
        "",
        "---",
        "## 📖 Asymmetric Execution Rules",
        "1. **Never exceed fixed 1.0% Account Risk** per individual position.",
        "2. **Chandelier ATR Trailing Stop:** Trail stops at `Peak Price - (3 * ATR14)` as stock advances.",
        "3. **Breakeven Rule:** When position is up **+8.0%**, automatically move stop loss to entry price.",
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
    from engine.notifier import format_elite_five_alert, send_telegram_alert, send_discord_alert
    alert_msg = format_elite_five_alert(elite_five, regime, regime_metrics, today_display)
    
    if send_telegram_alert(alert_msg):
        print("  [+] Dispatched Telegram notification successfully.")
    if send_discord_alert(alert_msg):
        print("  [+] Dispatched Discord notification successfully.")

if __name__ == "__main__":
    run_pipeline()
