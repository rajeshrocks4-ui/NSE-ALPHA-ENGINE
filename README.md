# 🏛️ NSE Alpha Breakout Engine v4.5
### Automated Institutional-Grade Systematic Trading System

An institutional breakout trading system designed for the National Stock Exchange of India (NSE). 
Combines **Multi-Stage Volatility Contraction (VCP)**, **Fibonacci 50–61.8% Golden Pocket Pullbacks**, **Institutional Pocket Pivots**, **Sector Pole Position Rotation**, and **Fixed-Fractional Asymmetric Risk Sizing**.

---

## ⚡ Key Highlights

* **Quad-Engine Pattern Detection:**
  1. **VCP Coiling:** Multi-stage contraction with Volume Dry-Up (VDU < 40% of 50 MA).
  2. **Fibonacci Golden Pocket:** Low-risk pullbacks to 0.50–0.618 Fib with 20 EMA / 50 SMA confluence.
  3. **Pocket Pivot:** Institutional accumulation footprints before breakouts.
  4. **Stage 1 to 2 Base Breakout:** Structural accumulation transitions.
* **100-Point Convergence Model:** Ranks candidates objectively across Technical Structure (30), Flow & Delivery (25), Relative Strength (20), Fundamentals (15), and Sector Tailwind (10).
* **The Elite 5:** Daily high-conviction focus list enforcing fundamental excellence (ROE > 15%, D/E < 1.0) and sector diversification (max 2 per sector).
* **Automated Cloud Runner:** Runs daily on GitHub Actions at 21:00 IST (15:30 UTC), committing fresh Markdown reports and updating the trade journal.

---

## 🚀 Quickstart

### 1. Installation
```bash
git clone https://github.com/<YOUR_USERNAME>/nse-alpha-engine.git
cd nse-alpha-engine
pip install -r requirements.txt
```

### 2. Run the Daily Scan
```bash
python main.py
```

---

## 📊 System Architecture

```text
nse-alpha-engine/
│
├── .github/workflows/
│   └── daily_scan.yml            # 21:00 IST Automated Cloud Runner
│
├── config/
│   ├── settings.py               # Risk %, ATR multipliers, Sector limits
│   └── universe.csv              # Nifty 500 liquid equity universe
│
├── engine/
│   ├── data_pipeline.py          # Bhavcopy & yfinance loaders
│   ├── market_regime.py          # Breadth & 13-pt regime evaluator
│   ├── sector_pole.py            # Sector Relative Strength & Pole Position
│   ├── pattern_vcp.py            # Minervini VCP & Volume Dry-Up detector
│   ├── pattern_fibonacci.py      # 0.50 - 0.618 Golden Pocket + MA confluence
│   ├── pattern_pocket_pivot.py   # Pocket Pivot institutional accumulation
│   ├── fundamental_gate.py       # ROE > 15%, D/E < 1.0, quality gating
│   ├── alpha_scorer.py           # 100-pt scoring & Elite 5 selector
│   └── risk_manager.py           # Fixed-fractional sizing & Chandelier trailing stops
│
├── reports/                      # Auto-generated daily markdown reports
├── performance/                  # Trade journal & performance scorecard
├── main.py                       # Single-command orchestrator
├── requirements.txt
└── README.md
```

---

## 🛡️ Asymmetric Risk Management Rules

1. **Fixed 1% Account Risk:** We never risk arbitrary sums. Every position size is mathematically calculated:
   $$\text{Shares} = \left\lfloor \frac{\text{Capital} \times 1\%}{\text{Entry} - \text{Stop Loss}} \right\rfloor$$
2. **Chandelier ATR Trailing Stop:** For winning positions, stop loss dynamically trails at $\text{Peak Price} - (3 \times \text{ATR}_{14})$.
3. **Breakeven Rule:** When a stock achieves **+8.0%**, the stop loss moves to cost price.
