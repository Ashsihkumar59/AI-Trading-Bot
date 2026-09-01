import pandas as pd
import ta

def build_features(df, output_file=None):
    # Data ki copy bana rahe hain taaki koi purana error na aaye
    data = df.copy()

    # 1. RSI
    data['RSI'] = ta.momentum.RSIIndicator(close=data['Close'], window=14).rsi()

    # 2. MACD
    macd = ta.trend.MACD(close=data['Close'])
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()

    # 3. OBV (On Balance Volume)
    if 'Volume' in data.columns:
        data['OBV'] = ta.volume.OnBalanceVolumeIndicator(close=data['Close'], volume=data['Volume']).on_balance_volume()
    else:
        data['OBV'] = 0

    # 4. 200 EMA (Macro Trend)
    data['EMA_200'] = ta.trend.EMAIndicator(close=data['Close'], window=200).ema_indicator()

    # 5. Baaki Basic Indicators
    data['SMA_20'] = ta.trend.SMAIndicator(close=data['Close'], window=20).sma_indicator()
    data['SMA_50'] = ta.trend.SMAIndicator(close=data['Close'], window=50).sma_indicator()
    
    bb = ta.volatility.BollingerBands(close=data['Close'], window=20, window_dev=2)
    data['BB_High'] = bb.bollinger_hband()
    data['BB_Low'] = bb.bollinger_lband()
    
    # Missing values ko cover karna
    data.bfill(inplace=True)
    data.fillna(0, inplace=True)

    # Agar CSV save karni hai toh karega
    if output_file:
        data.to_csv(output_file)

    # Yeh dekho, yahan exactly data return ho raha hai!
    return data