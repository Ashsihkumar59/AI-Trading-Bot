import pandas as pd
import numpy as np
from stable_baselines3 import PPO
# Is baar DummyVecEnv use nahi karenge!
from trading_env import StockTradingEnv

def test_ai():
    print("🔍 TRUE AI Testing Engine (Bug Fixed)...")
    
    try:
        df = pd.read_csv('reliance_features.csv', index_col=0, parse_dates=True)
        
        # Seedha apna Gym environment load karo
        env = StockTradingEnv(df)
        
        print("🧠 Trained Brain load kar rahe hain...")
        model = PPO.load("trained_reliance_bot")
        
        obs, info = env.reset()
        done = False
        
        action_counts = {0: 0, 1: 0, 2: 0}
        
        print("📈 Bot apni history ki trades check kar raha hai...")
        
        # Proper Gymnasium loop
        while not done:
            # AI action lega (Bina kisi wrapper ke)
            action, _states = model.predict(obs)
            
            # Action count record karna
            action_val = int(action)
            action_counts[action_val] += 1
            
            # Gym environment mein step lena
            obs, reward, terminated, truncated, info = env.step(action_val)
            done = terminated or truncated
            
        # Ab humein asli total_asset milega bina reset hue!
        final_portfolio = env.total_asset
        initial_portfolio = env.initial_balance
        profit = final_portfolio - initial_portfolio
        
        print("\n" + "="*40)
        print("📊 TRUE FINAL TRADING REPORT")
        print("="*40)
        print(f"💰 Initial Capital: ₹{initial_portfolio:,.2f}")
        print(f"💵 Final Capital:   ₹{final_portfolio:,.2f}")
        
        if profit > 0:
            print(f"🚀 TRUE Profit:     ₹{profit:,.2f} ({(profit/initial_portfolio)*100:.2f}%)")
        elif profit < 0:
            print(f"📉 TRUE Loss:       ₹{profit:,.2f} ({(profit/initial_portfolio)*100:.2f}%)")
        else:
            print(f"😐 No Profit/No Loss: ₹0.00")
            
        print("-" * 40)
        print("🤖 Bot ki Actions ki Report:")
        print(f"✋ HOLD (Kuch nahi kiya): {action_counts[0]} baar")
        print(f"🛒 BUY (Kharida):         {action_counts[1]} baar")
        print(f"💸 SELL (Becha):          {action_counts[2]} baar")
        print("="*40)

    except Exception as e:
        print(f"🚨 Testing Error: {e}")

if __name__ == "__main__":
    test_ai()