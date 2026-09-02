"""
Institutional F&O (Futures & Options) Derivatives Radar
========================================================
Identifies high-liquidity F&O stocks coiling in tight volatility compression.
Ideal for Cash, Futures, and ATM/OTM Call Option buying before explosive moves.
"""

import os
import re
from pathlib import Path
import pandas as pd
from config.settings import DATA_DIR

BHAVCOPY_DIR = DATA_DIR / "bhavcopy"

# Master baseline of active NSE F&O equities (updated dynamically)
MASTER_FNO_SYMBOLS = {
    '360ONE', 'ABB', 'ABCAPITAL', 'ADANIENSOL', 'ADANIENT', 'ADANIGREEN', 'ADANIPORTS',
    'ADANIPOWER', 'ALKEM', 'AMBER', 'AMBUJACEM', 'ANGELONE', 'APLAPOLLO', 'APOLLOHOSP',
    'APOLLOTYRE', 'ASHOKLEY', 'ASIANPAINT', 'ASTRAL', 'ATUL', 'AUBANK', 'AUROPHARMA',
    'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BALKRISIND', 'BANDHANBNK',
    'BANKBARODA', 'BANKINDIA', 'BEL', 'BERGEPAINT', 'BHARATFORG', 'BHARTIARTL',
    'BHEL', 'BIOCON', 'BOSCHLTD', 'BPCL', 'BRITANNIA', 'BSOFT', 'CANBK', 'CANFINHOME',
    'CDSL', 'CHAMBLFERT', 'CHOLAFIN', 'CIPLA', 'COALINDIA', 'COFORGE', 'COLPAL',
    'CONCOR', 'COROMANDEL', 'CROMPTON', 'CUMMINSIND', 'DABUR', 'DALBHARAT', 'DEEPAKNTR',
    'DELHIVERY', 'DIVISLAB', 'DIXON', 'DLF', 'DRREDDY', 'EICHERMOT', 'ESCORTS',
    'EXIDEIND', 'FEDERALBNK', 'GAIL', 'GLENMARK', 'GMRINFRA', 'GNFC', 'GODREJCP',
    'GODREJPROP', 'GRANULES', 'GRASIM', 'GUJGASLTD', 'HAL', 'HAVELLS', 'HCLTECH',
    'HDFCAMC', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDCOPPER',
    'HINDPETRO', 'HINDUNILVR', 'HUDCO', 'ICICIBANK', 'ICICIGI', 'ICICIPRULI', 'IDEA',
    'IDFCFIRSTB', 'IEX', 'IGL', 'INDHOTEL', 'INDIAMART', 'INDIANB', 'INDIGO',
    'INDUSINDBK', 'INDUSTOWER', 'INFY', 'IOC', 'IPCALAB', 'IRCTC', 'IREDA', 'IRFC',
    'ITC', 'JINDALSTEL', 'JIOFIN', 'JKCEMENT', 'JSWENERGY', 'JSWSTEEL', 'JUBLFOOD',
    'KALYANKJIL', 'KOTAKBANK', 'L&TFH', 'LALPATHLAB', 'LAURUSLABS', 'LICHSGFIN',
    'LICI', 'LTIM', 'LT', 'LUPIN', 'M&M', 'M&MFIN', 'MANAPPURAM', 'MARICO', 'MARUTI',
    'MAXHEALTH', 'MCX', 'METROPOLIS', 'MFSL', 'MGL', 'MOTHERSON', 'MPHASIS',
    'MRF', 'MUTHOOTFIN', 'NATIONALUM', 'NAUKRI', 'NAVINFLUOR', 'NBCC', 'NCC',
    'NESTLEIND', 'NMDC', 'NTPC', 'OBEROIRLTY', 'OFSS', 'OIL', 'ONGC', 'PAGEIND',
    'PATANJALI', 'PERSISTENT', 'PETRONET', 'PFC', 'PHOENIXLTD', 'PIDILITIND', 'PIIND',
    'PNB', 'PNBHOUSING', 'POLICYBZR', 'POLYCAB', 'POONAWALLA', 'POWERGRID', 'PRESTIGE',
    'PVRINOX', 'RAMCOCEM', 'RBLBANK', 'RECLTD', 'RELIANCE', 'SAIL', 'SBICARD',
    'SBILIFE', 'SBIN', 'SHREECEM', 'SHRIRAMFIN', 'SIEMENS', 'SJVN', 'SOLARINDS',
    'SONACOMS', 'SRF', 'SUNPHARMA', 'SUNTV', 'SUPREMEIND', 'SUZLON', 'SYNGENE',
    'TATACHEM', 'TATACOMM', 'TATACONSUM', 'TATAELXSI', 'TATAMOTORS', 'TATAPOWER',
    'TATASTEEL', 'TCS', 'TECHM', 'TIINDIA', 'TITAN', 'TORNTPHARM', 'TORNTPOWER',
    'TRENT', 'TVSMOTOR', 'UBL', 'ULTRACEMCO', 'UNIONBANK', 'UNITDSPR', 'UPL',
    'VBL', 'VEDL', 'VOLTAS', 'WIPRO', 'YESBANK', 'ZOMATO', 'ZYDUSLIFE'
}

def get_fno_universe():
    """
    Returns the set of active F&O equity ticker symbols.
    Attempts to parse local FO files from data/bhavcopy first, falling back to master list.
    """
    fno_symbols = set(MASTER_FNO_SYMBOLS)
    
    # Check if any fo*.csv exists in data/bhavcopy
    for fo_file in BHAVCOPY_DIR.glob("*[Ff][Oo]*.csv"):
        try:
            df = pd.read_csv(fo_file)
            if 'CONTRACT_D' in df.columns:
                contracts = df['CONTRACT_D'].dropna().tolist()
                for c in contracts:
                    m = re.match(r'FUTSTK([A-Z0-9&-]+?)\d{2}-[A-Z]{3}-\d{4}', str(c))
                    if m:
                        fno_symbols.add(m.group(1).strip())
        except Exception:
            continue
            
    return fno_symbols

def is_fno_stock(symbol, fno_set=None):
    """
    Checks whether a symbol (with or without .NS) is eligible in the F&O segment.
    """
    if fno_set is None:
        fno_set = get_fno_universe()
        
    clean_sym = symbol.replace('.NS', '').strip().upper()
    return clean_sym in fno_set

def generate_fno_radar_table(scored_df, top_n=5):
    """
    Filters and formats the top F&O pre-breakout compression setups.
    """
    if scored_df.empty or 'is_fno' not in scored_df.columns:
        return pd.DataFrame()
        
    fno_df = scored_df[scored_df['is_fno'] == True].copy()
    
    # Prioritize coiled pre-breakout launchpads
    if 'is_coiled' in fno_df.columns:
        fno_df = fno_df.sort_values(
            by=['is_coiled', 'alpha_score', 'clean_rs'],
            ascending=[False, False, False]
        )
    else:
        fno_df = fno_df.sort_values(by='alpha_score', ascending=False)
        
    return fno_df.head(top_n)
