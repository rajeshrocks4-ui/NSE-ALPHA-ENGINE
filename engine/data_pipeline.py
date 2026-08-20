"""
Data Pipeline Module
====================
Handles automated Bhavcopy downloading via jugaad-data and price matrix generation via yfinance.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from jugaad_data.nse import bhavcopy_save

from config.settings import DATA_DIR, CONFIG_DIR, MIN_DAILY_TURNOVER_CR, MIN_CLOSE_PRICE

BHAVCOPY_DIR = DATA_DIR / "bhavcopy"
BHAVCOPY_DIR.mkdir(parents=True, exist_ok=True)

def get_last_trading_day(dt=None):
    """Return the most recent trading date (excluding weekends)."""
    if dt is None:
        dt = datetime.now()
    if dt.hour < 18:
        dt -= timedelta(days=1)
    while dt.weekday() > 4: # 5=Sat, 6=Sun
        dt -= timedelta(days=1)
    return dt

def fetch_latest_bhavcopy(dt=None):
    """Download full bhavcopy with delivery data."""
    target_dt = get_last_trading_day(dt)
    date_str = target_dt.strftime("%d%m%Y")
    expected_file = BHAVCOPY_DIR / f"sec_bhavdata_full_{date_str}.csv"
    
    # Check if already present
    if expected_file.exists() and expected_file.stat().st_size > 1000:
        return pd.read_csv(expected_file)
    
    # Also check legacy download folder
    legacy_folder = Path(r"C:\Users\rajes\Downloads\NSE SCANNER")
    if legacy_folder.exists():
        legacy_files = sorted(legacy_folder.glob(f"*bhav*{target_dt.strftime('%d%m%Y')}*.csv"), reverse=True)
        if legacy_files:
            return pd.read_csv(legacy_files[0])
            
    print(f"  [Data] Downloading NSE Bhavcopy for {target_dt.strftime('%d-%b-%Y')}...")
    try:
        bhavcopy_save(target_dt, str(BHAVCOPY_DIR))
        if expected_file.exists():
            return pd.read_csv(expected_file)
    except Exception as e:
        print(f"  [Warn] jugaad-data download failed: {e}")
        
    # Search for most recent bhavcopy available
    all_bhav = sorted(BHAVCOPY_DIR.glob("sec_bhavdata_full_*.csv"), reverse=True)
    if all_bhav:
        print(f"  [Data] Using fallback local Bhavcopy: {all_bhav[0].name}")
        return pd.read_csv(all_bhav[0])
    return pd.DataFrame()

def load_universe():
    """Load Nifty 500 tickers from config/universe.csv."""
    universe_path = CONFIG_DIR / "universe.csv"
    if universe_path.exists():
        df = pd.read_csv(universe_path)
        symbols = df['Symbol'].dropna().str.strip().tolist()
        return [f"{s}.NS" if not s.endswith(".NS") else s for s in symbols]
    return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "DIVISLAB.NS", "SUPRIYA.NS"]

def fetch_price_matrices(tickers, period="1y"):
    """
    Fetch OHLCV data via yfinance and return processed technical DataFrame per ticker.
    """
    print(f"  [Data] Fetching {period} price matrices for {len(tickers)} symbols...")
    try:
        raw_data = yf.download(tickers, period=period, group_by='ticker', auto_adjust=False, progress=False)
    except Exception as e:
        print(f"  [Error] yfinance download failed: {e}")
        return {}

    matrices = {}
    for tkr in tickers:
        try:
            df = raw_data[tkr] if isinstance(raw_data.columns, pd.MultiIndex) else raw_data
            if df.empty or len(df) < 50:
                continue
            
            df = df.copy()
            close = df['Close']
            high = df['High']
            low = df['Low']
            vol = df['Volume']
            
            # Key Moving Averages
            df['EMA10'] = close.ewm(span=10, adjust=False).mean()
            df['EMA20'] = close.ewm(span=20, adjust=False).mean()
            df['SMA50'] = close.rolling(50).mean()
            df['SMA150'] = close.rolling(150).mean()
            df['SMA200'] = close.rolling(200).mean()
            df['VOL50'] = vol.rolling(50).mean()
            
            # Turnover in Cr
            df['Turnover_Cr'] = (close * vol) / 10000000.0
            df['Turnover50_Cr'] = df['Turnover_Cr'].rolling(50).mean()
            
            # ATR (14-period)
            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            df['ATR14'] = tr.rolling(14).mean()
            df['ADR_Pct'] = (df['ATR14'] / close) * 100.0
            
            # 52-Week High & Low
            df['High52W'] = high.rolling(252, min_periods=50).max()
            df['Low52W'] = low.rolling(252, min_periods=50).min()
            df['Pct_From_52W_High'] = ((close - df['High52W']) / df['High52W']) * 100.0
            
            # Relative Strength (Clean RS: Return / Volatility)
            ret3m = close.pct_change(63, fill_method=None) * 100.0
            ret6m = close.pct_change(126, fill_method=None) * 100.0
            ret12m = close.pct_change(252, fill_method=None) * 100.0
            clean_mom = (0.40 * ret3m) + (0.30 * ret6m.fillna(ret3m)) + (0.30 * ret12m.fillna(ret6m.fillna(ret3m)))
            df['Clean_RS_Raw'] = clean_mom / df['ADR_Pct'].replace(0, np.nan)
            
            matrices[tkr.replace('.NS', '')] = df
        except Exception:
            continue
            
    print(f"  [Data] Successfully processed {len(matrices)} clean technical series.")
    return matrices
