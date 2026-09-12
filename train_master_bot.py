import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import os

# Teri environment file import kar rahe hain
# (Make sure 'trading_env.py' tere folder mein ho)
from trading_env import StockTradingEnv 

print("🚨 ULTRA-PRO MAX AI TRAINING INITIATED 🚨\n")

# 1. Master Data Load Karo
print("📥 Loading 10-Year NIFTY Master Data...")
df = pd.read_csv("NIFTY_MASTER_DATA.csv")

# Agar pehle se koi index column aa gaya hai toh usko hata do
if 'Unnamed: 0' in df.columns:
    df.drop('Unnamed: 0', axis=1, inplace=True)

# 2. AI ka Akhada (Environment) Taiyar Karo
print("⚙️ Setting up the Virtual Trading Environment...")
# DummyVecEnv ek wrapper hai jo AI ko environment samajhne mein madad karta hai
env = DummyVecEnv([lambda: StockTradingEnv(df)])

# 3. Naya 'Bhediya' (Wolf) AI Model Banao
print("🧠 Initializing PPO Deep Learning Model...")
model = PPO("MlpPolicy", env, verbose=1)

# 4. ASLI TRAINING SHURU (LAPTOP LOAD MODE)
print("\n🔥 TRAINING STARTED! (Laptop ka charger on rakhna!) 🔥")
# 100,000 steps ka chota test run kar rahe hain
model.learn(total_timesteps=100000) 

# 5. Model Save Karo
model.save("nifty_10yr_master_bot")
print("\n✅ SUCCESS: Training Complete! Naya 'nifty_10yr_master_bot.zip' save ho gaya hai.")