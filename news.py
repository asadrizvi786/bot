import requests
from config import API_KEY

def get_news_sentiment(symbol):
    url = f"https://api.twelvedata.com/news_sentiment?symbol={symbol}&apikey={API_KEY}"
    res = requests.get(url).json()

    if "data" not in res or len(res["data"]) == 0:
        return 0  # no danger

    # average sentiment from latest 5 articles
    sentiments = [float(n["sentiment"]) for n in res["data"][:5]]
    return sum(sentiments) / len(sentiments)
