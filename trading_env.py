import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

class StockTradingEnv(gym.Env):
    """A stock trading environment with Volume Features & Balanced Psychology"""
    metadata = {'render.modes': ['human']}

    def __init__(self, df):
        super(StockTradingEnv, self).__init__()
        
        self.df = df
        self.reward_range = (-np.inf, np.inf)
        
        # 🚨 Ab 11 Features hain (OBV aur Volume_Trend add ho gaye)
       # 🚨 14 Ultimate Features (Macro Trend + S&R add ho gaye)
        self.features = [
            'Close', 'RSI_14', 'MACD', 'EMA_50', 'ATR_14', 'Body', 
            'Upper_Wick', 'Lower_Wick', 'Color', 'OBV', 'Volume_Trend', 
            'Macro_Trend', 'Dist_to_Resistance', 'Dist_to_Support'
        ]
        
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(len(self.features),), dtype=np.float32)

        self.initial_balance = 100000
        # Transaction cost wapas normal ki hai taaki normal trading kare
        self.transaction_cost = 0.002 

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.shares_held = 0
        self.current_step = 0
        
        self.total_trades = 0
        self.max_net_worth = self.initial_balance
        self.total_asset = self.initial_balance  # Testing script ke liye
        
        return self._next_observation(), {}

    def _next_observation(self):
        obs = self.df[self.features].iloc[self.current_step].values
        return obs.astype(np.float32)

    def step(self, action):
        current_price = self.df['Close'].iloc[self.current_step]
        prev_net_worth = self.net_worth

        # Execute Action
        if action == 1: # BUY
            if self.balance > 0: # Sirf tab kharido jab paisa ho (Over-buying block)
                shares_bought = self.balance / (current_price * (1 + self.transaction_cost))
                self.shares_held += shares_bought
                self.balance -= shares_bought * current_price * (1 + self.transaction_cost)
                self.total_trades += 1
            
        elif action == 2: # SELL
            if self.shares_held > 0: # Sirf tab becho jab shares hon
                self.balance += self.shares_held * current_price * (1 - self.transaction_cost)
                self.shares_held = 0
                self.total_trades += 1
            
        # Calculate Net Worth
        self.net_worth = self.balance + (self.shares_held * current_price)
        self.total_asset = self.net_worth
        
        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        # ==========================================
        # 🧠 BALANCED REWARD SYSTEM (AI PSYCHOLOGY)
        # ==========================================
        reward = self.net_worth - prev_net_worth  
        
        # Loss mein hold karne par halka sa dard (Panic nahi)
        if self.net_worth < self.initial_balance:
            reward -= 1 
            
        self.current_step += 1
        
        terminated = self.net_worth <= 0 or self.current_step >= len(self.df) - 1
        truncated = False
        
        obs = self._next_observation()
        
        return obs, reward, terminated, truncated, {}