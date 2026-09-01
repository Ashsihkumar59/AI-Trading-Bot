import sys
sys.stdout.reconfigure(encoding='utf-8')
import telebot
import yfinance as yf
import pandas as pd
import numpy as np
import csv
import os
from stable_baselines3 import PPO
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
import warnings
from datetime import datetime
from feature_engine import build_features
# Apna naya Indian bot load karo
indian_model = PPO.load("indian_master_bot") 

# Features list jo model ko chahiye
indian_features = ['RSI', 'MACD', 'MACD_Signal', 'OBV', 'EMA_200', 'SMA_20', 'SMA_50', 'BB_High', 'BB_Low']

warnings.filterwarnings('ignore')

# 🔴 APNA TOKEN YAHAN DALO 🔴
TELEGRAM_BOT_TOKEN = "8819399480:AAGtp_wXJseHHK1rEu_d6bMNbMlULeRAlaQ" 

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
LOG_FILE = "ai_signal_log.csv"

def log_trade_signal(date, ticker, price, action_hint, sl, tp):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Date_Time', 'Ticker', 'Price', 'Signal', 'Stop_Loss', 'Take_Profit'])
        writer.writerow([date, ticker, price, action_hint, sl, tp])

def analyze_market(ticker):
    try:
        model = PPO.load("trained_reliance_bot")
        # Crypto ke liye recent 100 days ka data chahiye S&R nikalne ke liye
        df = yf.download(ticker, period="100d", interval="1h", progress=False)
        
        if df.empty:
            return f"❌ Data nahi mila {ticker} ke liye."
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(inplace=True)
        
        close, high, low, open_price, volume = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
        
        # --- 1. Basic Indicators ---
        df['RSI_14'] = RSIIndicator(close=close, window=14).rsi()
        df['MACD'] = MACD(close=close, window_slow=26, window_fast=12, window_sign=9).macd()
        df['EMA_50'] = EMAIndicator(close=close, window=50).ema_indicator()
        df['ATR_14'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        
        # --- 2. Candlesticks ---
        df['Body'] = abs(close - open_price)
        df['Upper_Wick'] = high - np.maximum(open_price, close)
        df['Lower_Wick'] = np.minimum(open_price, close) - low
        df['Color'] = np.where(close > open_price, 1, -1)
        
        # --- 3. Institutional Volume ---
        df['OBV'] = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
        rolling_vol = volume.rolling(window=10).mean()
        df['Volume_Trend'] = np.where(rolling_vol == 0, 1, volume / rolling_vol)
        
        # --- 4. 🦅 EAGLE EYE & S/R (THE NEW UPGRADES) ---
        ema_200 = EMAIndicator(close=close, window=200).ema_indicator()
        df['Macro_Trend'] = np.where(close > ema_200, 1, -1)
        
        rolling_high = high.rolling(window=20).max()
        rolling_low = low.rolling(window=20).min()
        df['Dist_to_Resistance'] = (rolling_high - close) / close
        df['Dist_to_Support'] = (close - rolling_low) / close
        
        df.dropna(inplace=True)
        latest_data = df.iloc[-1]
        
        # 🚨 THE ULTIMATE 14 FEATURES 🚨
        features = [
            'Close', 'RSI_14', 'MACD', 'EMA_50', 'ATR_14', 'Body', 
            'Upper_Wick', 'Lower_Wick', 'Color', 'OBV', 'Volume_Trend', 
            'Macro_Trend', 'Dist_to_Resistance', 'Dist_to_Support'
        ]
        
        obs = latest_data[features].values.astype(np.float32)
        
        action, _ = model.predict(obs)
        action_val = int(action)
        
        ltp = latest_data['Close']
        atr_val = latest_data['ATR_14']
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        stop_loss = 0
        take_profit = 0
        
        if action_val == 1:
            hint = "🚀 BUY SIGNAL"
            stop_loss = ltp - (1.5 * atr_val)
            take_profit = ltp + (3.0 * atr_val)
        elif action_val == 2:
            hint = "💸 SELL SIGNAL"
            stop_loss = ltp + (1.5 * atr_val)
            take_profit = ltp - (3.0 * atr_val)
        else:
            hint = "✋ HOLD / WAIT"
            
        macro_status = "🟢 Bullish" if latest_data['Macro_Trend'] == 1 else "🔴 Bearish"
        
        msg = (
            f"🤖 *ULTIMATE AI ANALYSIS (14-Point Radar)* 🤖\n\n"
            f"🪙 *Asset:* {ticker}\n"
            f"💵 *Price:* ${ltp:,.2f}\n"
            f"📈 *Macro Trend (200 EMA):* {macro_status}\n"
            f"📊 *RSI:* {latest_data['RSI_14']:.1f} | 🌊 *Vol:* {latest_data['Volume_Trend']:.1f}x\n"
            f"🎯 *ACTION:* {hint}\n"
        )
        
        if action_val != 0:
            msg += (
                f"\n🛡️ *Stop-Loss:* ${stop_loss:,.2f}\n"
                f"💰 *Target:* ${take_profit:,.2f}\n"
            )
            
        log_trade_signal(current_time, ticker, round(ltp, 2), hint, round(stop_loss, 2), round(take_profit, 2))
        return msg

    except Exception as e:
        return f"🚨 Error analyzing {ticker}: {e}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hello Boss! Main aapka Ultimate AI Trading Assistant hu.\n\nKise analyze karna hai? Type karo:\n`/btc` - Bitcoin ke liye\n`/rel` - Reliance ke liye")

@bot.message_handler(commands=['btc'])
def handle_btc(message):
    bot.reply_to(message, "⏳ Ruko Boss, Bitcoin ka 14-point data check kar raha hu...")
    result_msg = analyze_market("BTC-USD")
    bot.send_message(message.chat.id, result_msg, parse_mode="Markdown")

@bot.message_handler(commands=['rel'])
def handle_rel(message):
    bot.reply_to(message, "⏳ Ruko Boss, Reliance ka data check kar raha hu...")
    result_msg = analyze_market("RELIANCE.NS").replace("$", "₹") 
    bot.send_message(message.chat.id, result_msg, parse_mode="Markdown")

@bot.message_handler(commands=['nse'])
def handle_nse(message):
    try:
        # User ka message padho (e.g., "/nse RELIANCE.NS")
        ticker = message.text.split(" ")[1].upper()
        bot.reply_to(message, f"🔍 Jarvis Scanning {ticker} on Indian Market...")
        
        # Latest data download karo
        df = yf.download(ticker, period="3mo", interval="1d")
        
        # MultiIndex fix (Jo abhi theek kiya tha)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Naye indicators lagao
        df = build_features(df, f"{ticker}_live.csv")
        df.dropna(inplace=True)
        
        # Aaj ka data AI ko dikhao
        latest_data = df[indian_features].iloc[-1].values
        action, _ = indian_model.predict(latest_data)
        
        # Signal Decode karo (Assumption: 0=Hold, 1=Buy, 2=Sell)
        if action == 1:
            signal = "🟢 STRONG BUY (Market Upar Jayega!)"
        elif action == 2:
            signal = "🔴 SELL / SHORT (Market Girega!)"
        else:
            signal = "⚪ HOLD (Abhi Shanti Rakho)"
            
        bot.reply_to(message, f"📊 **{ticker} Analysis Complete**\n\n🤖 AI Signal: {signal}\n\n*Trade at your own risk, Boss!*")
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error Boss! Asli problem yeh hai: {str(e)}")

# --- THE CLOUD KEEP-ALIVE HACK ---
import threading
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Jarvis is Alive on the Cloud!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    print("🤖 ULTIMATE Jarvis is starting...")
    
    # Flask web server ko background thread mein start karo
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Telegram bot ko main thread mein start karo
    bot.polling(none_stop=True)