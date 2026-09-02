# 🏛️ NSE ALPHA BREAKOUT ENGINE v5.1
## Complete Quantitative System Specification & Master Architecture Manual
*Self-Contained Institutional Reference Guide for Pre-Breakout Coiling & Trend Momentum*

---

## 1. SYSTEM OVERVIEW & THE PRE-BREAKOUT PARADIGM

The **NSE Alpha Breakout Engine v5.1** is an institutional-grade quantitative trading system designed exclusively for the **National Stock Exchange of India (NSE)**. 

### Core Paradigm Shift (v4.5 → v5.1):
> **We never chase extended breakouts after the explosive move has already happened.**
> Instead, we detect the **volatility compression coil BEFORE ignition** — catching stocks resting inside their base with Volume Dry-Up (VDU), Narrow Range 7 (NR7), and Inside Bars (IB) right at the launchpad zone (-3.8% to +1.2% from pivot).

### Five Master Pillars:
1. **Pre-Breakout Coiling Recognition:** Identifies structural energy buildup via NR7, Inside Bars, Double Inside Bars, Doji EMA Squeezes, and TTM Bollinger Band Squeezes before momentum bursts.
2. **Asymmetric Risk/Reward (1:5 to 1:8+ R/R):** Anchoring stops tightly below the compression candle low (1.5% to 3.0%) allows 3x to 5x larger share sizing within the identical 1% account risk envelope.
3. **Institutional F&O Derivatives Radar:** Dedicated continuous screening across all 210 liquid NSE F&O stocks for Cash, Futures, and ATM/OTM Call Option trades before Implied Volatility (IV) expands.
4. **Authentic Institutional Data Feed:** Direct integration with the official NSE MTO (Security-wise Delivery Position) report for genuine delivery percentage metrics and official Nifty Total Market industry classifications.
5. **Directional Uptrend & RS Quality Gate:** Rejects bearish breakdown coils (`Close < SMA50` and `Close < SMA200`) and enforces a mandatory Clean RS gate ($\ge 10.0$) so only leading market outperformers are selected.

---

## 2. UNIVERSE SELECTION & LIQUIDITY FILTERS

The engine dynamically filters the entire NSE universe (~2,200+ listed equities) from the daily official NSE Bhavcopy.

```
                  ┌─────────────────────────────────────────────────┐
                  │          FULL NSE BHAVCOPY (~3,600 ROWS)        │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                  ┌─────────────────────────────────────────────────┐
                  │              SERIES FILTER                      │
                  │   Keep only EQ (Equity), BE (Book Entry),       │
                  │   SM (SME), ST (Trade-to-Trade)                 │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                  ┌─────────────────────────────────────────────────┐
                  │              EXCLUSION FILTER                   │
                  │   Eliminate all ETFs, Index Funds, Bonds,       │
                  │   Mutual Funds (BEES, ETF, NIFTY, GOLD, LIQUID) │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                  ┌─────────────────────────────────────────────────┐
                  │              LIQUIDITY & CIRCUIT GATES          │
                  │   • Minimum Close Price >= ₹25.0                │
                  │   • Cash Equities: 50-day Turnover >= ₹3.0 Cr   │
                  │   • F&O Equities: 50-day Turnover >= ₹15.0 Cr   │
                  │   • Circuit Freeze Filter: High != Low or       │
                  │     Volume > 5,000 shares                       │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                             [ACTIVE UNIVERSE: ~1,800 STOCKS]
```

---

## 3. VOLATILITY COMPRESSION & SETUP PATTERNS

The engine scans for five high-probability pre-breakout compression patterns:

### A. NR7 (Narrow Range 7)
* **Definition:** Today's daily trading range `(High - Low)` is the narrowest of the last 7 sessions.
* **Physics:** Represents maximum volatility contraction and exhaustion of supply before sudden expansion.

### B. Inside Bar (IB) & Double Inside Bar
* **Definition:** Today's high is lower than yesterday's high, and today's low is higher than yesterday's low (`High <= Prev_High` and `Low >= Prev_Low`).
* **Double IB:** Two consecutive inside bars nested within the mother bar — represents extreme institutional coiling.

### C. Volume Dry-Up (VDU)
* **Definition:** Daily volume is $< 0.60 \times$ the 50-day moving average (`VOL50`).
* **Physics:** Proves that institutional sellers have finished liquidating; no floating supply remains to resist an upward breakout.

### D. TTM Bollinger Squeeze
* **Definition:** Bollinger Band width `(Upper BB - Lower BB) / SMA20` is within 15% of its 60-day minimum.
* **Physics:** Extreme price equilibrium preceding an explosive directional expansion.

### E. Launchpad Proximity Gate
* **Definition:** Price is resting between **-3.8% and +1.2%** of the structural base pivot (`Dist_to_Pivot_Pct`).
* **Penalty:** Stocks extended $> +4.0\%$ past pivot receive a **-20 point penalty** and are strictly disqualified from the Elite 5.

---

## 4. 100-POINT PRE-BREAKOUT ALPHA SCORING MATRIX

Every stock is evaluated across a 5-layer quantitative scoring rubric:

| Layer | Dimension | Max Points | Core Institutional Criteria |
|:---:|:---|:---:|:---|
| **1** | **Technical Structure & Coiling** | **30** | Base trend template (Close > 50SMA > 200SMA) + NR7 (+8) + Double Inside Bar (+8) + VDU (+5) + Squeeze (+4) |
| **2** | **Volume & Real Delivery Position** | **25** | Pocket Pivot (+10) OR VDU (+12) + Official NSE Delivery % $\ge 55\%$ (+13 pts) / $\ge 45\%$ (+9 pts) |
| **3** | **Clean Relative Strength (RS)** | **20** | Return / ADR Volatility vs Nifty: RS $\ge 25$ (+20 pts) / $\ge 15$ (+14 pts) / $\ge 8$ (+8 pts) |
| **4** | **Fundamental Quality Gate** | **15** | ROE $\ge 15\%$ (+8 pts), Debt/Equity $< 1.0$ (+7 pts). Unrated stocks zeroed out. |
| **5** | **Sector Pole Position** | **10** | Stock belongs to top 3 leading sectors by 3M/6M Clean RS tailwind. |
| **MOD** | **Launchpad Proximity Boost** | **+8** | Resting in tight launchpad zone (-3.8% to +1.2% from pivot). |
| **MOD** | **F&O Derivatives Boost** | **+4** | Member of 210 active NSE F&O universe (infinite liquidity). |
| **PEN** | **Extension Trap Penalty** | **-20** | Disqualifies any stock extended $> +4.0\%$ above pivot. |

---

## 5. RISK MANAGEMENT & EXECUTION RULES

### Position Sizing Formula:
$$\text{Position Risk} = \text{Total Capital (₹10 Lakh)} \times 1.0\% = ₹10,000$$
$$\text{Shares to Buy} = \frac{₹10,000 \times \text{Regime Multiplier}}{\text{Trigger Price} - \text{Stop Loss}}$$

### Execution Safeguards:
1. **Single Position Ceiling:** Never allocate more than **20% of total capital (₹2,00,000)** into any single position, regardless of how tight the stop loss is.
2. **Breakout Ignition Trigger:** Orders are triggered only when price trades **+0.2% above the mother bar / NR7 high** with volume expansion $\ge 1.4\times$ 50MA.
3. **Hard Stop Floor:** Stop losses are anchored below the NR7/Inside Bar candle low, with a maximum risk floor capped at **-8.0%**.
4. **Chandelier ATR Trailing Stop:** Once in profit, trail by `Peak Price - (3 * ATR14)`.
5. **Breakeven Rule:** When position gains **+8.0%**, immediately move stop loss to entry price (zero-risk free roll).

---

## 6. DAILY PRODUCTION PIPELINE (AUTOMATED AT 21:00 IST)

The system runs autonomously via Windows Task Scheduler (`run_daily_alpha.bat`) and GitHub Actions:

```
[1/6] Ingest Market Bhavcopy & Official MTO Delivery Data (archives.nseindia.com)
  │
[2/6] Evaluate Market Regime & Breadth (% above 50, 150, 200 SMA; NH/NL Ratio)
  │
[3/6] Compute Sector Rotation & Pole Position (Nifty Total Market Mapping)
  │
[4/6] Load Fundamental Quality Cache & F&O Universe (210 symbols)
  │
[5/6] Run 100-Point Pre-Breakout Coiling Recognition & Directional Trend Filter
  │
[6/6] Update Performance Scorecard, Generate Master Report & Dispatch Telegram Alerts
```
