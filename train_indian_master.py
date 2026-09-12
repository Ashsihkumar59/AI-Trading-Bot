import yfinance as yf
import pandas as pd
from feature_engine import build_features

# BOHOT ZAROORI: Agar tumhara trading_env mein class ka naam kuch aur hai 
# (jaise CryptoTradingEnv), toh yahan 'TradingEnv' ki jagah woh naam likhna.
from trading_env import StockTradingEnv 
from stable_baselines3 import PPO

# 1. The Multi-Sector Indian Basket
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS"]
all_data = pd.DataFrame()

print("⏳ Downloading & Processing Indian Market Data...")
for ticker in tickers:
    print(f"Bana raha hu {ticker} ka data...")
    # Yahoo finance se data uthao
   # Yahoo finance se data uthao
    df = yf.download(ticker, start="2020-01-01", end="2026-08-30")
    
    # YEH 2 NAYI LINES ADD KARNI HAI (MultiIndex hatane ke liye)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Naya feature engine use karke features lagao
    df = build_features(df, f"{ticker}_features.csv")
    # Naya feature engine use karke features lagao
    df = build_features(df, f"{ticker}_features.csv")
    
    # Naya feature engine use karke features lagao
    df = build_features(df, f"{ticker}_features.csv")
    
    # Khali rows uda do
    df.dropna(inplace=True)
    
    # Master data mein jod do
    all_data = pd.concat([all_data, df])

print(f"✅ Total Data Points for Training: {len(all_data)}")

# 2. Gym Setup
env = StockTradingEnv(all_data)

# 3. Train The Master Brain
print("🧠 Training Indian Master AI... (Isme thoda time lagega)")
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=150000)

# 4. Save The Brain
model.save("indian_master_bot")
print("🚀 Boom! Indian Master Bot is Ready!")