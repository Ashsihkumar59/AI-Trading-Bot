import telebot
import yfinance as yf
import pandas as pd
import numpy as np
import os
import threading
from flask import Flask
from stable_baselines3 import PPO
import warnings

# Custom Modules
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator
from risk_engine import calculate_position_size, check_rrr_gatekeeper
from market_context import get_macro_trend, get_sector_trend
from price_action import get_live_patterns

warnings.filterwarnings('ignore')

TELEGRAM_BOT_TOKEN = "8819399480:AAGtp_wXJseHHK1rEu_d6bMNbMlULeRAlaQ"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 Jarvis Ultra-Pro is Alive on the Cloud!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

try:
    model = PPO.load("nifty_10yr_master_bot")
    print("🧠 Master Bot Brain Loaded Successfully!")
except Exception as e:
    print(f"⚠️ Model load error: {e}")

def calculate_14_features(ticker):
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    if df.empty:
        return None, 0
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
        
    close, high, low = df['Close'], df['High'], df['Low']
    open_price, volume = df['Open'], df['Volume']
    
    df['RSI_14'] = RSIIndicator(close=close, window=14).rsi()
    df['MACD'] = MACD(close=close, window_slow=26, window_fast=12, window_sign=9).macd()
    df['EMA_50'] = EMAIndicator(close=close, window=50).ema_indicator()
    df['ATR_14'] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
    
    df['Body'] = abs(close - open_price)
    df['Upper_Wick'] = high - np.maximum(open_price, close)
    df['Lower_Wick'] = np.minimum(open_price, close) - low
    df['Color'] = np.where(close > open_price, 1, -1)
    
    df['OBV'] = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
    rolling_vol = volume.rolling(window=10).mean()
    df['Volume_Trend'] = np.where(rolling_vol == 0, 1, volume / rolling_vol)
    
    ema_200 = EMAIndicator(close=close, window=200).ema_indicator()
    df['Macro_Trend'] = np.where(close > ema_200, 1, -1)
    
    rolling_high = high.rolling(window=20).max()
    rolling_low = low.rolling(window=20).min()
    df['Dist_to_Resistance'] = (rolling_high - close) / close
    df['Dist_to_Support'] = (close - rolling_low) / close
    
    df.dropna(inplace=True)
    
    features_list = [
        'Close', 'RSI_14', 'MACD', 'EMA_50', 'ATR_14', 'Body', 
        'Upper_Wick', 'Lower_Wick', 'Color', 'OBV', 'Volume_Trend', 
        'Macro_Trend', 'Dist_to_Resistance', 'Dist_to_Support'
    ]
    
    latest_data = df.iloc[-1][features_list].values.astype(np.float32)
    latest_data = np.nan_to_num(latest_data)
    
    current_price = df.iloc[-1]['Close']
    return latest_data, current_price

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 **JARVIS ULTRA-PRO ONLINE**\n\nCommands:\n👉 `/nse RELIANCE.NS` - AI Trade Analysis", parse_mode='Markdown')

@bot.message_handler(commands=['nse'])
def analyze_stock(message):
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.reply_to(message, "❌ Sahi format: `/nse RELIANCE.NS`")
            return
            
        ticker = command_parts[1].upper()
        bot.reply_to(message, f"🔍 Scanning 14-Point Radar for {ticker}...")
        
        live_features, current_price = calculate_14_features(ticker)
        if live_features is None:
            bot.reply_to(message, "❌ Data nahi mila. Ticker check kar.")
            return
            
        action_code, _ = model.predict(live_features, deterministic=True)
        tech_signal = "BUY 🟢" if action_code == 1 else "SELL 🔴" if action_code == 2 else "HOLD ⚪"
        
        final_decision = f"STRONG {tech_signal}" if "BUY" in tech_signal else tech_signal
        trade_logged = ""
        
        if action_code in [1, 2]: 
            action_str = "BUY" if action_code == 1 else "SELL"
            macro_trend = get_macro_trend(ticker)
            trend_str = "UP 🟢" if macro_trend == 1 else "DOWN 🔴" if macro_trend == -1 else "NEUTRAL ⚪"
            
            sector_trend, sector_name = get_sector_trend(ticker)
            sector_str = "UP 🟢" if sector_trend == 1 else "DOWN 🔴" if sector_trend == -1 else "NEUTRAL ⚪"
            
            mtf_approved = True
            reject_reason = ""
            
            # S/R Wall Check 🧱 (Naya feature)
            dist_to_res = live_features[12]
            dist_to_sup = live_features[13]
            
            if action_code == 1 and dist_to_res < 0.01:
                mtf_approved = False
                reject_reason = "Too close to Major Resistance Wall 🧱"
            elif action_code == 2 and dist_to_sup < 0.01:
                mtf_approved = False
                reject_reason = "Too close to Major Support Wall 🧱"
            
            # Trend Check
            if mtf_approved:
                if action_code == 1 and macro_trend == -1:
                    mtf_approved = False
                    reject_reason = f"Against 1H Macro Trend ({trend_str})"
                elif action_code == 2 and macro_trend == 1:
                    mtf_approved = False
                    reject_reason = f"Against 1H Macro Trend ({trend_str})"
                    
            # Sector Check
            if mtf_approved: 
                if action_code == 1 and sector_trend == -1:
                    mtf_approved = False
                    reject_reason = f"Against {sector_name} Sector Trend ({sector_str})"
                elif action_code == 2 and sector_trend == 1:
                    mtf_approved = False
                    reject_reason = f"Against {sector_name} Sector Trend ({sector_str})"

            if not mtf_approved:
                final_decision = f"REJECTED 🚫 ({reject_reason}. Changed to HOLD ⚪)"
                trade_logged = f"\n❌ Trade Rejected by Context Radar:\n📡 Reason: {reject_reason}"
            else:
                account_balance = 100000  
                atr_value = live_features[4]  
                
                if action_code == 1: 
                    sl_price = current_price - (1.5 * atr_value)
                    target_price = current_price + (3.0 * atr_value) 
                else: 
                    sl_price = current_price + (1.5 * atr_value)
                    target_price = current_price - (3.0 * atr_value)
                    
                is_approved, current_rrr = check_rrr_gatekeeper(current_price, sl_price, target_price)
                
                if not is_approved:
                    final_decision = f"REJECTED 🚫 (Poor RRR: 1:{current_rrr:.2f}. Changed to HOLD ⚪)"
                    trade_logged = "\n❌ Trade Rejected by Risk Gatekeeper."
                else:
                    qty = calculate_position_size(account_balance, current_price, sl_price)
                    
                    # 🛠️ UPGRADED EXCEL SHEET (SL, Target aur Status ke sath)
                    trade_data = pd.DataFrame([[pd.Timestamp.now(), ticker, action_str, qty, current_price, sl_price, target_price, "OPEN"]],
                                              columns=['Date', 'Ticker', 'Action', 'Quantity', 'Entry_Price', 'SL', 'Target', 'Status'])
                    file_name = "paper_trade_book.csv"
                    
                    if not os.path.isfile(file_name):
                        trade_data.to_csv(file_name, index=False)
                    else:
                        trade_data.to_csv(file_name, mode='a', header=False, index=False)
                        
                    trade_logged = f"\n✅ Paper Trade Logged: {action_str} {qty} Qty of {ticker} @ ₹{current_price:.2f}\n📡 {sector_name}: {sector_str} | 1H Trend: {trend_str}\n🛡️ SL: ₹{sl_price:.2f} | 🎯 Target: ₹{target_price:.2f}"

        # Module 3: Price Action Data fetch
        daily_df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if isinstance(daily_df.columns, pd.MultiIndex):
            daily_df.columns = daily_df.columns.droplevel(1)
            
        detected_patterns = get_live_patterns(daily_df)
        patterns_str = "\n".join([f"   👉 {p}" for p in detected_patterns])

        # Final Report Build
        report = f"""📊 {ticker} ULTRA-LEVEL REPORT 📊

💰 Current Price: ₹{current_price:.2f}

👁️ 3. Price Action & Volume:
{patterns_str}

⚙️ 1. Tech AI Signal: {tech_signal}
📰 2. News Mood: Neutral ⚪

🤖 MASTER AI DECISION: {final_decision}
{trade_logged}
"""
        bot.reply_to(message, report)
        
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")



# ==========================================
# 🛡️ 4. LIVE POSITION MANAGER (TRAILING ENGINE)
# ==========================================
active_chats = set()

@bot.message_handler(commands=['start_manager'])
def start_manager(message):
    chat_id = message.chat.id
    if chat_id not in active_chats:
        active_chats.add(chat_id)
        bot.reply_to(message, "🛡️ **Live Position Manager Started!**\nJarvis is now watching your trades 24/7. Risk management is fully AUTOMATED! 😎", parse_mode='Markdown')
        threading.Thread(target=position_manager_loop, args=(chat_id,), daemon=True).start()
    else:
        bot.reply_to(message, "⚠️ Manager is already running in the background!")

def position_manager_loop(chat_id):
    import time
    while True:
        try:
            if os.path.exists("paper_trade_book.csv"):
                df = pd.read_csv("paper_trade_book.csv")
                changes_made = False

                for index, row in df.iterrows():
                    if row['Status'] == 'OPEN':
                        ticker = row['Ticker']
                        action = row['Action']
                        entry_price = float(row['Entry_Price'])
                        sl_price = float(row['SL'])
                        target_price = float(row['Target'])

                        # Fetch Live Price (1-minute data)
                        live_data = yf.download(ticker, period="1d", interval="1m", progress=False)
                        if live_data.empty: continue
                        
                        live_price = float(live_data['Close'].iloc[-1].iloc[0] if isinstance(live_data.columns, pd.MultiIndex) else live_data['Close'].iloc[-1])

                        # ==========================
                        # 📈 BUY TRADE LOGIC
                        # ==========================
                        if action == 'BUY':
                            risk = entry_price - sl_price
                            reward_level = entry_price + risk # 1:1 Profit Level
                            
                            if live_price >= target_price:
                                df.at[index, 'Status'] = 'CLOSED (TARGET)'
                                bot.send_message(chat_id, f"🎯 **TARGET HIT!**\n{ticker} BUY trade closed at ₹{live_price:.2f}. Profit Booked! 💸", parse_mode='Markdown')
                                changes_made = True
                                
                            elif live_price <= sl_price:
                                df.at[index, 'Status'] = 'CLOSED (SL)'
                                bot.send_message(chat_id, f"🛑 **STOP LOSS HIT!**\n{ticker} BUY trade closed at ₹{live_price:.2f}.", parse_mode='Markdown')
                                changes_made = True
                                
                            elif live_price >= reward_level and sl_price < entry_price:
                                df.at[index, 'SL'] = entry_price
                                bot.send_message(chat_id, f"🛡️ **TRAILING SL ACTIVATED!**\n{ticker} has reached 1:1 Reward.\nMoved SL to Entry Price (₹{entry_price:.2f}). Your risk is now ZERO! 😎", parse_mode='Markdown')
                                changes_made = True

                        # ==========================
                        # 📉 SELL TRADE LOGIC
                        # ==========================
                        elif action == 'SELL':
                            risk = sl_price - entry_price
                            reward_level = entry_price - risk # 1:1 Profit Level
                            
                            if live_price <= target_price:
                                df.at[index, 'Status'] = 'CLOSED (TARGET)'
                                bot.send_message(chat_id, f"🎯 **TARGET HIT!**\n{ticker} SELL trade closed at ₹{live_price:.2f}. Profit Booked! 💸", parse_mode='Markdown')
                                changes_made = True
                                
                            elif live_price >= sl_price:
                                df.at[index, 'Status'] = 'CLOSED (SL)'
                                bot.send_message(chat_id, f"🛑 **STOP LOSS HIT!**\n{ticker} SELL trade closed at ₹{live_price:.2f}.", parse_mode='Markdown')
                                changes_made = True
                                
                            elif live_price <= reward_level and sl_price > entry_price:
                                df.at[index, 'SL'] = entry_price
                                bot.send_message(chat_id, f"🛡️ **TRAILING SL ACTIVATED!**\n{ticker} has reached 1:1 Reward.\nMoved SL to Entry Price (₹{entry_price:.2f}). Your risk is now ZERO! 😎", parse_mode='Markdown')
                                changes_made = True

                if changes_made:
                    df.to_csv("paper_trade_book.csv", index=False)

        except Exception as e:
            pass # Background errors ko chup-chap ignore karega taaki bot crash na ho
        
        time.sleep(60) # Har 60 seconds mein check karega
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling()