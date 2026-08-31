# 🏛️ NSE ALPHA BREAKOUT ENGINE v4.5
## Complete Quantitative System Specification & Operating Manual
*Self-Contained Reference Guide for Systematic Equities Trading*

---

## 1. SYSTEM OVERVIEW & CORE PHILOSOPHY

The **NSE Alpha Breakout Engine** is an institutional-grade quantitative trend-following and momentum breakout system designed specifically for the **National Stock Exchange of India (NSE)**.

### Core Principles:
1. **Asymmetric Risk/Reward (Minimum 1:4 to 1:7 R/R):** We do not chase extended +15% breakouts. We buy early "in-the-base" cheat setups (Pocket Pivots, Fibonacci Golden Pockets, Volatility Contraction Pivots) where the initial risk is tight (2% to 5%) and the upside is explosive.
2. **Dynamic Market Exposure (The Regime Shield):** In unfavorable or distribution market environments, position size is automatically throttled down to **25%** to prevent capital erosion during choppy drawdowns.
3. **Fixed-Fractional Mathematical Risk:** Every trade risks exactly **1.0% of total portfolio capital**, strictly protected by a **20% single-position capital allocation ceiling** and an **8.0% hard stop floor**.
4. **Chandelier ATR Trailing Stops:** Profits are allowed to compound undisturbed during massive Stage 2 trends, trailing by `Peak Price - (3 * ATR14)` and moving to breakeven automatically at `+8.0%` gain.

---

## 2. UNIVERSE SELECTION & LIQUIDITY FILTERS

The engine scans the **entire active NSE equity universe (~2,200+ stocks)** dynamically extracted from the daily official NSE Bhavcopy.

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
                  │              LIQUIDITY GATES                    │
                  │   • Minimum Close Price >= ₹20.0                │
                  │   • Minimum Daily Turnover >= ₹10 Lakhs         │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                             [ACTIVE UNIVERSE: ~2,200 STOCKS]
```

---

## 3. MARKET REGIME & BREADTH SCORING MODEL

Market Regime is evaluated daily using a **13-Point Composite Breadth Model** calculated across all active NSE stocks:

| Breadth Indicator | Threshold for 1 Point | Max Points |
|:---|:---|:---:|
| **% of Stocks > 50-day SMA** | `>= 50.0%` (2 pts) \| `>= 65.0%` (3 pts) | **3** |
| **% of Stocks > 150-day SMA** | `>= 50.0%` (2 pts) \| `>= 65.0%` (3 pts) | **3** |
| **% of Stocks > 200-day SMA** | `>= 50.0%` (2 pts) \| `>= 65.0%` (3 pts) | **3** |
| **52-Week High / Low Ratio** | `>= 1.5` (2 pts) \| `>= 3.0` (4 pts) | **4** |
| **TOTAL COMPOSITE SCORE** | | **13** |

### Exposure & Position Sizing Matrix:

| Regime Classification | Breadth Score | Position Sizing % | Action Protocol |
|:---|:---:|:---:|:---|
| 🟢 **CONFIRMED BULL** | **11 – 13** | **100%** *(Full Size)* | Aggressive buying. Full allocation to Elite 5. |
| 🟡 **BULL PAUSE / CAUTION** | **8 – 10** | **75%** *(Reduced)* | Selective buying. Focus only on APEX tier setups. |
| 🟠 **PRESSURE / WEAKNESS** | **5 – 7** | **50%** *(Half Size)* | Defensive stance. Tighten trailing stops. |
| 🔴 **DISTRIBUTION / BEAR** | **0 – 4** | **25%** *(Quarter Size)* | Strict capital preservation. No chasing. Raise cash. |

---

## 4. THE QUAD-PATTERN SETUP BLUEPRINT

The engine identifies 4 distinct institutional price-action setups:

### Setup A: Minervini Volatility Contraction Pattern (VCP)
* **Stage 2 Trend Template:** `Close > SMA50 > SMA150 > SMA200`.
* **Base Construction:** Base depth between 52-week high and base low must be `<= 28%` over a minimum of 4 weeks.
* **Wave Contraction:** Standard deviation of price changes contracts progressively: $\text{Std}(30d) > \text{Std}(15d) > \text{Std}(5d)$.
* **Volume Dry-Up (VDU):** Minimum volume in the last 5 days $< 40\%$ of the 50-day average volume ($\text{Vol} < 0.40 \times \text{VOL50}$).
* **Trigger:** Close crosses the pivot price (20-day high) on Volume $\ge 150\%$ of 50-day average volume.

### Setup B: Fibonacci Golden Pocket Pullback (0.50 – 0.618)
* **Impulse Leg:** Chronological upward thrust where $\text{Low Index} < \text{High Index}$ and prior surge $\ge +18\%$.
* **Golden Pocket Zone:** Current price pulls back into the retracement zone:
  $$\text{Fib 50.0\%} = \text{High} - (0.50 \times \text{Range})$$
  $$\text{Fib 61.8\%} = \text{High} - (0.618 \times \text{Range})$$
* **Moving Average Confluence:** Current price is within $\pm 2.0\%$ of the **20 EMA** or **50 SMA**.
* **Reversal Candle:** Low tests the Golden Pocket and closes in the upper 40% of the daily range.

### Setup C: Institutional Pocket Pivot
* **In-the-Base Accumulation:** Stock is resting within a multi-week base or pulling back to the 10 EMA / 20 EMA / 50 SMA.
* **Volume Footprint:** Today's up-volume is **greater than the highest down-day volume of the past 10 trading sessions**.
* **Moving Average Support:** Current close is above the 10 EMA or 20 EMA and within 3% of the moving average.

### Setup D: High-Tight Flag & Stage 2 Breakout
* **High-Tight Flag:** Explosive surge of $+60\%$ to $+100\%$ in 4 to 8 weeks followed by a shallow consolidation flag $\le 20\%$ deep.
* **Stage 2 (52W High) Breakout:** Price breaks within 1.5% of 52-week high on Volume $\ge 150\%$ of 50-day average.

---

## 5. THE 100-POINT ALPHA CONVERGENCE MATRIX

Every stock in the market is scored objectively out of 100 points:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     100-POINT ALPHA SCORING BREAKDOWN                       │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 1. Technical Pattern & Trend Setup   │ 30 Points Maximum                    │
│ 2. Volume Expansion & Delivery %     │ 25 Points Maximum                    │
│ 3. Clean Relative Strength (RS)      │ 20 Points Maximum                    │
│ 4. Fundamental Quality Gate          │ 15 Points Maximum                    │
│ 5. Sector Tailwind & Pole Position   │ 10 Points Maximum                    │
├──────────────────────────────────────┴──────────────────────────────────────┤
│ TOTAL MAXIMUM ALPHA SCORE: 100 POINTS                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Signal Decay Multiplier:
To prevent dead, stale setups from staying on the watchlist:
$$\text{Final Score} = \text{Raw Score} \times \text{Decay Multiplier}$$
* **Days 1 – 2 (Fresh Breakout):** Multiplier = `1.00` (100%)
* **Days 3 – 4:** Multiplier = `0.95` (95%)
* **Days 5 – 6:** Multiplier = `0.85` (85%)
* **Day 7+:** Multiplier = `0.75` (75% — Setup disqualified from Elite 5)

### The Elite 5 Selection Rules:
1. Must have **Alpha Score $\ge 60.0$** (Ranked by highest score).
2. Must pass the **Fundamental Quality Gate** ($\text{ROE} \ge 15.0\%$, $\text{Debt/Equity} \le 1.0$).
3. **Sector Diversity Rule:** Maximum of **2 stocks per sector** in the Elite 5 to eliminate concentration risk.

---

## 6. RISK MANAGEMENT & EXECUTION RULES

### Rule 1: Fixed-Fractional Position Sizing
$$\text{Shares} = \min\left( \left\lfloor \frac{\text{Capital} \times 1\% \times \text{Regime Multiplier}}{\text{Entry Price} - \text{Stop Loss}} \right\rfloor, \left\lfloor \frac{\text{Capital} \times 20\% \times \text{Regime Multiplier}}{\text{Entry Price}} \right\rfloor \right)$$

* **Fixed 1% Dollar Risk:** You never risk more than 1.0% of your account on a trade.
* **Strict 20% Single-Position Capital Cap:** No single stock can ever exceed 20% of total portfolio capital (protects against overnight gap-downs).

### Rule 2: Strict 8.0% Initial Hard Stop Floor
$$\text{Initial Stop Loss} = \max(\text{Structural Support}, \text{Entry} \times 0.92)$$
* No trade is ever initiated with a stop loss wider than **-8.0%**.

### Rule 3: Automatic Breakeven Escalation (+8% Rule)
* The moment a stock reaches **`+8.0%` profit from entry**, the stop loss is automatically moved to **Entry Price (Cost)**. The trade is now 100% risk-free.

### Rule 4: Chandelier ATR Trailing Stop
* As the stock advances into a massive trend, the stop loss trails at:
  $$\text{Trailing Stop} = \text{Peak Price} - (3.0 \times \text{ATR14})$$
* Never lower a trailing stop. It only ratchets upward.

---

## 7. AUTOMATION ARCHITECTURE & TELEGRAM INTEGRATION

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    24/7 CLOUD AUTOMATION ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. GitHub Actions Cloud VM wakes up at 21:00 IST (15:30 UTC) Mon-Fri.       │
│ 2. Downloads today's official NSE Bhavcopy directly from NSE servers.       │
│ 3. Ingests 1-year price data for 2,200+ equities via 12-batch downloader.   │
│ 4. Computes Market Regime, Sector Pole Position, and Quad-Patterns.         │
│ 5. Isolates The Elite 5 and updates performance/scorecard.md.               │
│ 6. Commits reports/Master_Alpha_Report_YYYYMMDD.md to GitHub repository.     │
│ 7. Dispatches instant formatted notification to Telegram (@srkdoc86_bot).   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. DAILY TRADER OPERATING SOP (Checklist)

### 🌙 Night Before (After 21:05 IST):
1. Open your **Telegram** chat with `@srkdoc86_bot`.
2. Review the **Market Regime** (e.g. `DISTRIBUTION -> 25% Sizing`).
3. Note **The Elite 5** focus candidates with their Entry, Stop Loss, and Calculated Position Sizes.

### ☀️ Morning (09:00 – 09:15 IST):
1. Log into your broker terminal (Zerodha, Groww, Upstox, Dhan, etc.).
2. Place **Buy Stop-Limit Orders** for the Elite 5 candidates at `Pivot Price + 0.2%`.
3. Set your GTT (Good-Till-Triggered) **Stop Loss** at the specified stop loss level.
4. **Execution Golden Rule:** If a stock gaps up $> +2.5\%$ above the pivot price at the open, **DO NOT CHASE**. Wait for an intraday pullback to the pivot.
