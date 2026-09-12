import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
# Hum apne banaye hue custom environment ko import kar rahe hain
from trading_env import StockTradingEnv

def train_ai():
    print("🧠 AI Training Engine Start ho raha hai...")
    
    try:
        # 1. Apna feature-rich data load karo
        df = pd.read_csv('reliance_features.csv', index_col=0, parse_dates=True)
        
        # 2. Environment (Gym) setup karo
        # DummyVecEnv stable-baselines3 ka tarika hai environment ko optimize karne ka
        env = DummyVecEnv([lambda: StockTradingEnv(df)])
        
        # 3. The Brain (Model) Initialize karo
        # MlpPolicy matlab Multi-Layer Perceptron (Standard Neural Network)
        print("🤖 PPO Model initialize ho raha hai...")
        model = PPO("MlpPolicy", env, verbose=1, learning_rate=0.0003)
        
        # 4. Training Start
        # total_timesteps = 20000 matlab AI 20,000 din (steps) ki trading practice karega
        # Asli world-class bots ko millions of steps ke liye train karte hain, par abhi hum 20k rakhenge taaki jaldi ho jaye.
        print("🏋️‍♂️ Bot Gym mein practice kar raha hai. Isme thoda time lag sakta hai, please wait...")
        model.learn(total_timesteps=20000)
        
        # 5. Model ko Save karo
        model_name = "trained_reliance_bot"
        model.save(model_name)
        
        print(f"✅ Success! AI train ho chuka hai aur '{model_name}.zip' ke naam se save ho gaya hai.")
        
    except Exception as e:
        print(f"🚨 Training Error: {e}")

if __name__ == "__main__":
    train_ai()