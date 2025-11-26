def calculate_confidence(buys, sells):
    total = buys + sells
    if total == 0:
        return 0
    return int((buys / total) * 100)
