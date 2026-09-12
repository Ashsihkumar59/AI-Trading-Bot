import yfinance as yf
import pandas as pd
from ta.trend import EMAIndicator

def get_macro_trend(ticker):
    """
    Higher timeframe (1-Hour) ka data fetch karke Macro Trend nikalta hai.
    Returns: 1 (Bullish/UP), -1 (Bearish/DOWN), or 0 (Neutral/Error)
    """
    try:
        # 1. Fetch 1-Hour data for the last 1 month
        df_1h = yf.download(ticker, period="1mo", interval="1h", progress=False)
        
        if df_1h.empty:
            return 0
        
        # Yahoo Finance MultiIndex fix
        if isinstance(df_1h.columns, pd.MultiIndex):
            df_1h.columns = df_1h.columns.droplevel(1)
            
        # 2. Calculate 50-period EMA on the 1-Hour chart (The Macro Boss)
        df_1h['EMA_50_1H'] = EMAIndicator(close=df_1h['Close'], window=50).ema_indicator()
        df_1h.dropna(inplace=True)
        
        if df_1h.empty:
            return 0
            
        # 3. Get the latest 1-Hour Close and EMA
        latest_close = df_1h.iloc[-1]['Close']
        latest_ema = df_1h.iloc[-1]['EMA_50_1H']
        
        # 4. The Institutional Verdict
        if latest_close > latest_ema:
            return 1  # Trend is strongly UP 🟢
        elif latest_close < latest_ema:
            return -1 # Trend is strongly DOWN 🔴
        else:
            return 0
            
    except Exception as e:
        print(f"⚠️ MTF Error for {ticker}: {e}")
        return 0



def get_sector_trend(ticker):
    """
    Stock ke hisaab se uska parent sector (Nifty Bank, Nifty IT, ya Nifty 50) 
    identify karta hai aur uska trend check karta hai.
    Returns: trend (1, -1, 0) aur sector_name
    """
    # 1. Sector Mapping (Dada kaun hai?)
    bank_stocks = ['SBIN.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'KOTAKBANK.NS']
    it_stocks = ['TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS']
    
    if ticker in bank_stocks:
        sector_ticker = '^NSEBANK'  # Nifty Bank Index
        sector_name = "BANKNIFTY"
    elif ticker in it_stocks:
        sector_ticker = '^CNXIT'    # Nifty IT Index
        sector_name = "NIFTY IT"
    else:
        sector_ticker = '^NSEI'     # Default Broad Market (Nifty 50)
        sector_name = "NIFTY 50"
        
    try:
        # 2. Fetch Sector Data (1-Hour Chart)
        df_sector = yf.download(sector_ticker, period="1mo", interval="1h", progress=False)
        
        if df_sector.empty:
            return 0, sector_name
            
        if isinstance(df_sector.columns, pd.MultiIndex):
            df_sector.columns = df_sector.columns.droplevel(1)
            
        # 3. Calculate Sector 50-EMA
        df_sector['EMA_50'] = EMAIndicator(close=df_sector['Close'], window=50).ema_indicator()
        df_sector.dropna(inplace=True)
        
        if df_sector.empty:
            return 0, sector_name
            
        latest_close = df_sector.iloc[-1]['Close']
        latest_ema = df_sector.iloc[-1]['EMA_50']
        
        # 4. Sector Verdict
        if latest_close > latest_ema:
            return 1, sector_name   # Sector UP 🟢
        elif latest_close < latest_ema:
            return -1, sector_name  # Sector DOWN 🔴
        else:
            return 0, sector_name
            
    except Exception as e:
        print(f"⚠️ Sector Error for {sector_ticker}: {e}")
        return 0, sector_name