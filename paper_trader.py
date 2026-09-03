import pandas as pd
import os
from datetime import datetime

# Hamari virtual trading diary
TRADE_FILE = "paper_trade_book.csv"

def log_virtual_trade(ticker, action, price, quantity=10):
    try:
        # Agar file nahi hai, toh nayi file aur headings banao
        if not os.path.exists(TRADE_FILE):
            df = pd.DataFrame(columns=["Date", "Ticker", "Action", "Price", "Quantity", "Total_Value"])
            df.to_csv(TRADE_FILE, index=False)
        
        # Trade ki details
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_value = price * quantity
        
        # Naya trade record karo
        new_trade = pd.DataFrame([{
            "Date": timestamp,
            "Ticker": ticker,
            "Action": action,
            "Price": round(price, 2),
            "Quantity": quantity,
            "Total_Value": round(total_value, 2)
        }])
        
        # File ke end mein add (append) kar do
        new_trade.to_csv(TRADE_FILE, mode='a', header=False, index=False)
        
        return f"✅ Paper Trade Logged: {action} {quantity} Qty of {ticker} @ ₹{price:.2f}"
    
    except Exception as e:
        return f"⚠️ Trade Logging Error: {e}"

# --- YEH HISSA SIRF TESTING KE LIYE HAI ---
if __name__ == "__main__":
    print("📝 Testing Paper Trading Engine...")
    result1 = log_virtual_trade("RELIANCE.NS", "BUY", 2950.50, 10)
    print(result1)
    result2 = log_virtual_trade("TCS.NS", "SELL", 4100.25, 5)
    print(result2)
    print("👉 Check your folder, 'paper_trade_book.csv' file ban gayi hogi!")