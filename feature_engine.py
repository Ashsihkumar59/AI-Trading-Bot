import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator

def build_features(input_file, output_file):
    print("⚙️ Data Load kar rahe hain... Eagle Eye + Support/Resistance add ho raha hai...")
    
    try:
        df = pd.read_csv(input_file, index_col=0, parse_dates=True, low_memory=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.dropna(inplace=True)
        
        close, high, low, open_price, volume = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
        
        # --- 1. Basic Indicators & Candlesticks ---
        df['RSI_14'] = RSIIndicator(close=close, window=14).rsi()
        macd = MACD(close=close, window_slow=26, window_fast=12, window_sign=9)
        df['MACD'] = macd.macd()
        df['EMA_50'] = EMAIndicator(close=close, window=50).ema_indicator()
        df['ATR_14'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        
        df['Body'] = abs(close - open_price)
        df['Upper_Wick'] = high - np.maximum(open_price, close)
        df['Lower_Wick'] = np.minimum(open_price, close) - low
        df['Color'] = np.where(close > open_price, 1, -1)
        
        # --- 2. Institutional Volume ---
        df['OBV'] = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
        rolling_vol = volume.rolling(window=10).mean()
        df['Volume_Trend'] = np.where(rolling_vol == 0, 1, volume / rolling_vol)
        
        # --- 3. 🦅 EAGLE EYE (MACRO TREND) ---
        print("📈 Macro Trend (200 EMA) Calculate ho raha hai...")
        ema_200 = EMAIndicator(close=close, window=200).ema_indicator()
        # Agar price 200 EMA ke upar hai toh 1 (Bullish), warna -1 (Bearish)
        df['Macro_Trend'] = np.where(close > ema_200, 1, -1)
        
        # --- 4. 🧱 SUPPORT & RESISTANCE ---
        print("🧱 AI ko Support aur Resistance draw karna sikha rahe hain...")
        # Pichle 20 periods ka High = Resistance, Low = Support
        rolling_high = high.rolling(window=20).max()
        rolling_low = low.rolling(window=20).min()
        
        # AI ko absolute price nahi, doori (% distance) chahiye hoti hai
        df['Dist_to_Resistance'] = (rolling_high - close) / close
        df['Dist_to_Support'] = (close - rolling_low) / close
        
        df.dropna(inplace=True)
        df.to_csv(output_file)
        
        print(f"✅ Success! Data is ready with 14 Ultimate Features: {output_file}")
        
    except Exception as e:
        print(f"🚨 System Error: {e}")

if __name__ == "__main__":
    build_features("reliance_market_data.csv", "reliance_features.csv")