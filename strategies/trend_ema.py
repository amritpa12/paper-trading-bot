import pandas as pd

def signal(df: pd.DataFrame):
    if df.empty or len(df) < 50:
        return None
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=10).mean()
    df["ema_slow"] = df["close"].ewm(span=30).mean()
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    if prev.ema_fast <= prev.ema_slow and latest.ema_fast > latest.ema_slow:
        return "buy"
    if prev.ema_fast >= prev.ema_slow and latest.ema_fast < latest.ema_slow:
        return "sell"
    return None
