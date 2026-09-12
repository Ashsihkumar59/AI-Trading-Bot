import pandas as pd
import numpy as np

def detect_price_action(df):
    df['Body'] = abs(df['Close'] - df['Open'])
    df['Upper_Wick'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['Lower_Wick'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    df['Total_Length'] = df['High'] - df['Low']
    df['Total_Length'] = df['Total_Length'].replace(0, 0.001)

    df['is_Hammer'] = (df['Lower_Wick'] > (2 * df['Body'])) & (df['Upper_Wick'] < (0.1 * df['Total_Length']))
    df['is_Shooting_Star'] = (df['Upper_Wick'] > (2 * df['Body'])) & (df['Lower_Wick'] < (0.1 * df['Total_Length']))

    df['Vol_MA_20'] = df['Volume'].rolling(window=20).mean().replace(0, 1) # Safety zero division
    df['Smart_Money_Spike'] = df['Volume'] > (df['Vol_MA_20'] * 2.5)

    return df

def get_live_patterns(df):
    processed_df = detect_price_action(df.copy())
    latest_candle = processed_df.iloc[-1]
    
    patterns = []
    
    # Naya Volume Multiplier Logic
    vol_multiplier = latest_candle['Volume'] / latest_candle['Vol_MA_20']
    
    if latest_candle['is_Hammer']:
        patterns.append("Hammer 🔨 (Bullish)")
    if latest_candle['is_Shooting_Star']:
        patterns.append("Shooting Star 🌠 (Bearish)")
        
    if latest_candle['Smart_Money_Spike']:
        patterns.append(f"Institutional Volume Spike 🐳 ({vol_multiplier:.1f}x of Avg)")
    else:
        patterns.append(f"Normal Volume 📊 ({vol_multiplier:.1f}x of Avg)")
        
    return patterns