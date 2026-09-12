import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class StockTradingEnv(gym.Env):
    """🤖 Jarvis Ultra-Pro AI Trading Environment"""
    metadata = {'render_modes': ['human']}

    def __init__(self, df):
        super(StockTradingEnv, self).__init__()

        # Data ko reset kar rahe hain taaki index 0 se shuru ho
        self.df = df.reset_index(drop=True)
        
        # 🚨 THE 14-POINT RADAR FEATURES 🚨
        self.features = [
            'Close', 'RSI_14', 'MACD', 'EMA_50', 'ATR_14', 'Body', 
            'Upper_Wick', 'Lower_Wick', 'Color', 'OBV', 'Volume_Trend', 
            'Macro_Trend', 'Dist_to_Resistance', 'Dist_to_Support'
        ]
        
        # Actions: 0 = HOLD, 1 = BUY, 2 = SELL
        self.action_space = spaces.Discrete(3)
        
        # AI ki Aankhein: 14 Features dekhne ke liye Box Space
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(14,), dtype=np.float32
        )
        
        # Virtual Account Details (Training ke liye ₹1 Lakh ki capital)
        self.initial_balance = 100000.0 
        self.balance = self.initial_balance
        self.shares_held = 0
        self.net_worth = self.initial_balance
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.shares_held = 0
        self.net_worth = self.initial_balance
        self.current_step = 0
        
        return self._next_observation(), {}

    def _next_observation(self):
        # Current step ka data uthao
        obs = self.df.loc[self.current_step, self.features].values.astype(np.float32)
        
        # Agar koi data missing (NaN) ho toh use 0 kar do (AI crash na ho)
        obs = np.nan_to_num(obs)
        return obs

    def step(self, action):
        current_price = self.df.loc[self.current_step, 'Close']
        prev_net_worth = self.net_worth
        
        # ⚙️ EXECUTE ACTION
        if action == 1: # 🟢 BUY
            if self.balance > current_price:
                # Jitne shares aa sakte hain, kharid lo
                shares_bought = int(self.balance / current_price)
                self.balance -= shares_bought * current_price
                self.shares_held += shares_bought
                
        elif action == 2: # 🔴 SELL
            if self.shares_held > 0:
                # Saare shares bech do
                self.balance += self.shares_held * current_price
                self.shares_held = 0
        
        # 🧮 NET WORTH & REWARD CALCULATION
        self.net_worth = self.balance + (self.shares_held * current_price)
        
        # Reward = Profit ya Loss (Net worth kitni badhi ya ghati)
        reward = self.net_worth - prev_net_worth
        
        self.current_step += 1
        
        # Check karo kya data khatam ho gaya?
        terminated = self.current_step >= len(self.df) - 1
        
        # Agar capital 0 ho gayi (Bankrupt), toh training rok do
        if self.net_worth <= 0:
            terminated = True
            
        truncated = False
        
        info = {
            'step': self.current_step,
            'net_worth': self.net_worth,
            'action': action
        }
        
        return self._next_observation(), float(reward), terminated, truncated, info