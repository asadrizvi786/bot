def generate_signal(rsi, ema_short, ema_long, macd, signal, news_score):
    votes_buy = 0
    votes_sell = 0

    # RSI
    if rsi < 30: votes_buy += 1
    if rsi > 70: votes_sell += 1

    # EMA Trend
    if ema_short > ema_long: votes_buy += 1
    else: votes_sell += 1

    # MACD
    if macd > signal: votes_buy += 1
    else: votes_sell += 1

    # News filter
    if news_score < 0: votes_sell += 1  # negative = bearish
    if news_score > 0: votes_buy += 1   # positive = bullish

    # Confidence %
    confidence = int((max(votes_buy, votes_sell) / 4) * 100)

    # Final output
    if max(votes_buy, votes_sell) < 3:
        return "⚠️ NO TRADE", confidence

    if votes_buy > votes_sell:
        return "✅ BUY", confidence
    else:
        return "❌ SELL", confidence
