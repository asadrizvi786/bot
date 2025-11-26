from flask import Flask, jsonify, render_template
import pandas as pd
import requests
import os
from indicators import calculate_rsi, calculate_ema, calculate_macd
from config import API_KEY, NEWS_API_KEY, SYMBOL, TIMEFRAMES, NEWS_THRESHOLD

app = Flask(__name__)

# ------------------- Fetch Candle Data -------------------
def fetch_data(symbol, interval):
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": symbol, "interval": interval, "apikey": API_KEY, "outputsize": 60}
    r = requests.get(url, params=params)
    data = r.json()
    df = pd.DataFrame(data["values"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    numeric_cols = ["open","high","low","close"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.sort_values("datetime")
    return df

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
        sentiments = []
        for article in data.get("articles", []):
            title = article["title"].lower()
            score = 0
            for word in ["up","gain","bullish","rally","surge"]:
                if word in title: score += 1
            for word in ["down","loss","bearish","drop","fall"]:
                if word in title: score -= 1
            sentiments.append(score)
        return sum(sentiments)/len(sentiments) if sentiments else 0
    except:
        return 0

def generate_signal(rsi, ema20, ema50, macd, macd_signal, news_sentiment):
    votes_buy = 0
    votes_sell = 0
    if rsi < 30: votes_buy += 1
    if rsi > 70: votes_sell += 1
    if ema20 > ema50: votes_buy += 1
    else: votes_sell += 1
    if macd > macd_signal: votes_buy += 1
    else: votes_sell += 1
    if abs(news_sentiment) > NEWS_THRESHOLD:
        votes_buy *= 0.5
        votes_sell *= 0.5
    confidence = int((max(votes_buy,votes_sell)/3)*100)
    if votes_buy > votes_sell: return "BUY", confidence
    elif votes_sell > votes_buy: return "SELL", confidence
    else: return "NO TRADE", confidence

# ------------------- API Endpoint -------------------
@app.route("/signal")
def signal():
    results = []
    news_sentiment = fetch_news_sentiment()
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
            signal_text, confidence = generate_signal(rsi, ema20, ema50, macd, macd_signal, news_sentiment)
            results.append({
                "timeframe": tf,
                "rsi": round(rsi,2),
                "ema20": round(ema20,2),
                "ema50": round(ema50,2),
                "macd": round(macd,4),
                "news_sentiment": round(news_sentiment,2),
                "signal": signal_text,
                "confidence": confidence
            })
        except Exception as e:
            results.append({"timeframe": tf, "error": str(e)})
    return jsonify(results)

# ------------------- Frontend Page -------------------
@app.route("/")
def index():

    if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

