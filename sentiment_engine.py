import yfinance as yf
from groq import Groq

# Teri API Key (Testing ke liye)
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

def get_news_sentiment(ticker_symbol):
    try:
        # 1. Ticker ki latest news uthao
        ticker = yf.Ticker(ticker_symbol)
        news_data = ticker.news
        
        # Agar koi news nahi mili toh Neutral (0) return karo
        if not news_data:
            return 0, "No recent news found."

        # 2. Top 3 news headlines ko ek text mein combine karo
       # 2. Top 3 news headlines ko naye format se nikalna
        headlines = []
        for article in news_data[:3]:
            # Yahoo ne data ko 'content' ke andar daal diya hai
            if 'content' in article and 'title' in article['content']:
                headlines.append(article['content']['title'])
            else:
                headlines.append("Market Update")
            
        news_text = " | ".join(headlines)
            
        news_text = " | ".join(headlines)
        # 3. Groq AI ko prompt do (Batao use kya karna hai)
        prompt = f"""
        You are an expert Indian Stock Market (NSE) financial analyst. 
        Analyze the following recent news headlines for the stock '{ticker_symbol}':
        "{news_text}"
        
        Respond strictly with a single number:
        1 if the news is completely Bullish (Positive)
        -1 if the news is completely Bearish (Negative)
        0 if the news is Neutral, Mixed, or unrelated.
        """

        # 4. Groq se lightning-fast response lo
       # 4. Groq se lightning-fast response lo
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="qwen/qwen3.8-27b", # TERE ACCOUNT KA CONFIRMED MODEL
            temperature=0.1 
        )
        
        # AI ka answer (1, -1, or 0)
        result = chat_completion.choices[0].message.content.strip()
        
        # Output ko number mein convert karna
        if "-1" in result:
            return -1, news_text
        elif "1" in result:
            return 1, news_text
        else:
            return 0, news_text
            
    except Exception as e:
        print(f"⚠️ NLP Error: {e}")
        return 0, "Failed to analyze news."




    # --- YEH HUSSA SIRF TESTING KE LIYE HAI ---
if __name__ == "__main__":
    print("🤖 Jarvis NLP System Testing Start...")
    
    # Hum Reliance ka example le rahe hain
    score, headlines = get_news_sentiment("RELIANCE.NS")
    
    print("\n" + "="*50)
    print(f"📊 Sentiment Score: {score}")
    print(f"📰 Headlines Read: {headlines}")
    print("="*50 + "\n")