import requests
import pandas as pd
import time
from config import API_KEY, NEWS_API_KEY, SYMBOL, TIMEFRAMES, REFRESH_SECONDS, NEWS_THRESHOLD, RISK_PERCENT
from indicators import calculate_rsi, calculate_ema, calculate_macd

# ------------------- Fetch Candle Data -------------------
def fetch_data(symbol, interval):
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": symbol, "interval": interval, "apikey": API_KEY, "outputsize": 60}
    r = requests.get(url, params=params)
    try:
        data = r.json()
    except Exception as e:
        raise RuntimeError(f"Error parsing JSON: {e}\nResponse Text: {r.text}")
    if "values" not in data:
        raise RuntimeError(f"Error fetching data: {data}")
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    numeric_cols = ["open","high","low","close"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("datetime")
    return df

# ------------------- Fetch News Sentiment -------------------
def fetch_news_sentiment():
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "gold OR XAUUSD",
        "apiKey": NEWS_API_KEY,
        "pageSize": 5,
        "sortBy": "publishedAt",
        "language": "en"
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if "articles" not in data:
            return 0
        sentiments = []
        for article in data["articles"]:
            title = article["title"].lower()
            score = 0
            positive_keywords = ["up", "gain", "bullish", "rally", "surge"]
            negative_keywords = ["down", "loss", "bearish", "drop", "fall"]
            for word in positive_keywords:
                if word in title: score += 1
            for word in negative_keywords:
                if word in title: score -= 1
            sentiments.append(score)
        return sum(sentiments)/len(sentiments) if sentiments else 0
    except Exception as e:
        print(f"Error fetching news: {e}")
        return 0

# ------------------- Generate Signal -------------------
def generate_signal(rsi, ema20, ema50, macd, macd_signal, news_sentiment):
    votes_buy = 0
    votes_sell = 0

    # RSI vote
    if rsi < 30: votes_buy += 1
    if rsi > 70: votes_sell += 1

    # EMA vote
    if ema20 > ema50: votes_buy += 1
    else: votes_sell += 1

    # MACD vote
    if macd > macd_signal: votes_buy += 1
    else: votes_sell += 1

    # News filter: reduce confidence if major news
    if abs(news_sentiment) > NEWS_THRESHOLD:
        votes_buy *= 0.5
        votes_sell *= 0.5

    confidence = int((max(votes_buy, votes_sell)/3)*100)

    if votes_buy > votes_sell:
        return "BUY", confidence
    elif votes_sell > votes_buy:
        return "SELL", confidence
    else:
        return "NO TRADE", confidence

# ------------------- Calculate SL/TP -------------------
def calculate_sl_tp(latest_price, signal):
    """
    Simple example: SL = risk% below/above entry
                    TP = 2x risk distance
    """
    risk_amount = latest_price * (RISK_PERCENT/100)
    if signal == "BUY":
        sl = latest_price - risk_amount
        tp = latest_price + 2*risk_amount
    elif signal == "SELL":
        sl = latest_price + risk_amount
        tp = latest_price - 2*risk_amount
    else:
        sl = tp = None
    return sl, tp

# ------------------- Run Bot -------------------
def run_bot():
    print("\n✅ XAU/USD Live Signal Bot with News + SL/TP Started ✅\n")
    while True:
        for tf in TIMEFRAMES:
            try:
                df = fetch_data(SYMBOL, tf)
                df["RSI"] = calculate_rsi(df)
                df["EMA20"] = calculate_ema(df, 20)
                df["EMA50"] = calculate_ema(df, 50)
                df["MACD"], df["MACD_SIGNAL"] = calculate_macd(df)

                latest = df.iloc[-1]
                rsi = latest["RSI"]
                ema20 = latest["EMA20"]
                ema50 = latest["EMA50"]
                macd = latest["MACD"]
                macd_signal = latest["MACD_SIGNAL"]
                close_price = latest["close"]

                news_sentiment = fetch_news_sentiment()

                signal, confidence = generate_signal(rsi, ema20, ema50, macd, macd_signal, news_sentiment)

                sl, tp = calculate_sl_tp(close_price, signal)

                print(f"XAU/USD ({tf}): RSI={rsi:.2f}, EMA20={ema20:.2f}, EMA50={ema50:.2f}, MACD={macd:.4f}")
                print(f"News Sentiment={news_sentiment:.2f} | Signal: {signal} | Confidence: {confidence}%")
                if sl and tp:
                    print(f"Suggested SL: {sl:.2f} | TP: {tp:.2f}\n")
                else:
                    print("No trade signal\n")

                time.sleep(1)  # small delay to avoid rate limit
            except Exception as e:
                print(f"Error fetching {tf} data: {e}")

        print(f"⏳ Waiting {REFRESH_SECONDS} seconds for next update...\n")
        time.sleep(REFRESH_SECONDS)

# ------------------- Main -------------------
if __name__ == "__main__":
    run_bot()
