import pandas as pd

def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))


def signal(df: pd.DataFrame):
    if df.empty or len(df) < 20:
        return None
    df = df.copy()
    df["rsi"] = rsi(df["close"])
    latest = df.iloc[-1]
    if latest.rsi < 30:
        return "buy"
    if latest.rsi > 70:
        return "sell"
    return None
