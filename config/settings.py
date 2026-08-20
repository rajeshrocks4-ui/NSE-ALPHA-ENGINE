"""
NSE Alpha Engine - Configuration Settings
=========================================
Universal constants, scoring thresholds, and risk parameters.
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
ENGINE_DIR = BASE_DIR / "engine"
REPORTS_DIR = BASE_DIR / "reports"
PERFORMANCE_DIR = BASE_DIR / "performance"
DATA_DIR = BASE_DIR / "data"

# Create required directories
for d in [REPORTS_DIR, PERFORMANCE_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Risk & Capital Management
ACCOUNT_CAPITAL = 1000000.0       # Base model portfolio: ₹10,00,000 (10 Lakh)
RISK_PER_TRADE_PCT = 0.01         # Fixed 1.0% account risk per trade (₹10,000)
MAX_PORTFOLIO_RISK_PCT = 0.06     # Maximum 6.0% total open portfolio heat
MAX_SECTOR_CONCENTRATION = 2      # Max 2 stocks per sector in Elite 5
MAX_OPEN_POSITIONS = 8            # Maximum concurrent positions in Bull regime
DISTRIBUTION_POSITION_SIZE_PCT = 0.25 # 25% sizing in Distribution regime

# Stop Loss & Trailing Rules
MAX_INITIAL_STOP_PCT = 0.08       # Hard cap: Never risk more than 8% on initial entry
ATR_STOP_MULTIPLIER = 3.0         # Chandelier Trailing Stop (Peak Price - 3 * ATR14)
BREAKEVEN_TRIGGER_PCT = 0.08      # Move stop to breakeven when price reaches +8%

# Liquidity & Volume Filters
MIN_DAILY_TURNOVER_CR = 5.0       # Minimum ₹5 Crore average daily turnover
MIN_CLOSE_PRICE = 20.0            # Exclude penny stocks below ₹20
VOLUME_DRYUP_THRESHOLD = 0.40     # VDU: Volume < 40% of 50-day average
VOLUME_BREAKOUT_THRESHOLD = 1.50  # Breakout: Volume >= 150% of 50-day average
MIN_DELIVERY_PCT = 40.0           # Minimum 40% delivery on breakout

# Pattern Thresholds
VCP_MAX_BASE_DEPTH_PCT = 0.28     # Maximum 28% depth from 52W High to Base Low
VCP_MIN_BASE_WEEKS = 4            # Minimum 4 weeks base consolidation
FIB_GOLDEN_POCKET_LOW = 0.50      # 50% Fibonacci retracement
FIB_GOLDEN_POCKET_HIGH = 0.618    # 61.8% Fibonacci retracement
FIB_MA_TOLERANCE_PCT = 0.02       # 2% tolerance for MA overlap (20 EMA / 50 SMA)

# Fundamental Quality Gate
MIN_ROE_PCT = 15.0                # Minimum 15% Return on Equity
MAX_DEBT_TO_EQUITY = 1.0          # Maximum 1.0 Debt-to-Equity ratio
MIN_FUND_SCORE = 70.0             # Minimum 70/100 Fundamental Quality Score

# Conviction Tier Thresholds (0 - 100 Alpha Score)
TIER_APEX_THRESHOLD = 90.0
TIER_STRONG_THRESHOLD = 75.0
TIER_CONFIRMED_THRESHOLD = 60.0
