"""
Data Pipeline Module
====================
Handles automated Bhavcopy downloading via jugaad-data and price matrix generation for ALL NSE equities via yfinance.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from jugaad_data.nse import bhavcopy_save

from config.settings import DATA_DIR, CONFIG_DIR, MIN_CLOSE_PRICE

BHAVCOPY_DIR = DATA_DIR / "bhavcopy"
BHAVCOPY_DIR.mkdir(parents=True, exist_ok=True)

EXCLUDED_PATTERNS = ['BEES', 'ETF', 'NIFTY', 'GOLD', 'SILVER', 'LIQUID', 'GILT', 'CPSE', 'BHARAT22', 'INDEX', 'IVZ', 'DUMMY']

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
    
    if expected_file.exists() and expected_file.stat().st_size > 1000:
        return pd.read_csv(expected_file)
    
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
        
    all_bhav = sorted(BHAVCOPY_DIR.glob("*bhav*.csv"), reverse=True)
    if all_bhav:
        print(f"  [Data] Using local Bhavcopy: {all_bhav[0].name}")
        return pd.read_csv(all_bhav[0])
    return pd.DataFrame()

def load_universe(bhav_df=None, min_turnover_lakhs=10.0):
    """
    Extracts ALL active equity symbols from the NSE Bhavcopy or fallback universe.
    Returns: list of '.NS' ticker symbols (e.g. ['RELIANCE.NS', 'DIVISLAB.NS', ...])
    """
    if bhav_df is not None and not bhav_df.empty:
        df = bhav_df.copy()
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Identify symbol and series columns
        sym_col = 'TCKRSYMB' if 'TCKRSYMB' in df.columns else ('SYMBOL' if 'SYMBOL' in df.columns else '')
        srs_col = 'SCTYSRS' if 'SCTYSRS' in df.columns else ('SERIES' if 'SERIES' in df.columns else '')
        val_col = 'TTLTRFVAL' if 'TTLTRFVAL' in df.columns else ('TOTTRDVAL' if 'TOTTRDVAL' in df.columns else '')
        cls_col = 'CLSPRIC' if 'CLSPRIC' in df.columns else ('CLOSE_PRICE' if 'CLOSE_PRICE' in df.columns else 'CLOSE')
        
        if sym_col and srs_col:
            # Filter equity series
            eq_mask = df[srs_col].astype(str).str.strip().isin(['EQ', 'BE', 'SM', 'ST'])
            df = df[eq_mask]
            
            # Filter out ETFs / Index instruments
            df = df[~df[sym_col].astype(str).str.upper().apply(lambda s: any(x in s for x in EXCLUDED_PATTERNS))]
            
            # Minimum price filter (> ₹15)
            if cls_col in df.columns:
                try: df = df[pd.to_numeric(df[cls_col], errors='coerce') >= MIN_CLOSE_PRICE]
                except: pass
                
            # Minimum Turnover Filter (₹10 Lakhs daily turnover to ensure liquidity)
            if val_col in df.columns:
                try: df = df[pd.to_numeric(df[val_col], errors='coerce') >= (min_turnover_lakhs * 100000.0)]
                except: pass
                
            symbols = df[sym_col].dropna().astype(str).str.strip().unique().tolist()
            print(f"  [Data] Dynamic Universe: Extracted {len(symbols)} active NSE equities from Bhavcopy.")
            return [f"{s}.NS" for s in symbols]
            
    # Fallback to universe.csv
    universe_path = CONFIG_DIR / "universe.csv"
    if universe_path.exists():
        df = pd.read_csv(universe_path)
        symbols = df['Symbol'].dropna().str.strip().tolist()
        return [f"{s}.NS" if not s.endswith(".NS") else s for s in symbols]
        
    return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "DIVISLAB.NS", "SUPRIYA.NS"]

def fetch_price_matrices(tickers, period="1y", batch_size=200):
    """
    Fetch OHLCV data via yfinance in batches for the complete universe.
    """
    total_tickers = len(tickers)
    print(f"  [Data] Ingesting {period} price matrices for {total_tickers} NSE symbols (Batches of {batch_size})...")
    
    matrices = {}
    batches = [tickers[i:i + batch_size] for i in range(0, total_tickers, batch_size)]
    
    for b_idx, batch in enumerate(batches, 1):
        print(f"    -> [Batch {b_idx}/{len(batches)}] Downloading {len(batch)} symbols...")
        try:
            raw_data = yf.download(batch, period=period, group_by='ticker', auto_adjust=False, progress=False)
        except Exception as e:
            print(f"    -> [Warn] Batch {b_idx} failed: {e}")
            continue
            
        for tkr in batch:
            try:
                df = raw_data[tkr] if isinstance(raw_data.columns, pd.MultiIndex) else raw_data
                if df is None or df.empty or len(df) < 50:
                    continue
                
                df = df.copy()
                close = df['Close']
                high = df['High']
                low = df['Low']
                vol = df['Volume']
                
                # Basic sanity check
                if close.isna().all() or (close == 0).all():
                    continue
                
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
                
                clean_sym = tkr.replace('.NS', '').strip().upper()
                matrices[clean_sym] = df
            except Exception:
                continue
                
    print(f"  [Data] Successfully processed {len(matrices)} clean active NSE equity series.")
    return matrices
