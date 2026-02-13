import pandas as pd

def signal(df: pd.DataFrame):
    if df.empty or len(df) < 30:
        return None
    # Use first 15 minutes as opening range
    opening = df.iloc[:15]
    high = opening["high"].max()
    low = opening["low"].min()
    latest = df.iloc[-1]
    if latest.close > high:
        return "buy"
    if latest.close < low:
        return "sell"
    return None
