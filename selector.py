import importlib
import numpy as np

STRATEGY_MODULES = {
    "trend_ema": "strategies.trend_ema",
    "mean_reversion_rsi": "strategies.mean_reversion_rsi",
    "breakout_orb": "strategies.breakout_orb",
}

def backtest_score(df, strategy_name, window=200):
    mod = importlib.import_module(STRATEGY_MODULES[strategy_name])
    if df is None or df.empty:
        return -1.0
    df = df.tail(window).copy()
    if len(df) < 30:
        return -1.0

    pnl = 0.0
    position = None
    entry = 0.0

    for i in range(30, len(df)):
        sub = df.iloc[: i + 1]
        sig = mod.signal(sub)
        price = sub.iloc[-1].close

        if position is None and sig == "buy":
            position = "long"
            entry = price
        elif position == "long" and sig == "sell":
            pnl += (price - entry)
            position = None

    return pnl


def pick_strategy(df, enabled, window=200, min_score=0.0):
    scores = {}
    for name in enabled:
        scores[name] = backtest_score(df, name, window=window)

    best = max(scores, key=scores.get)
    if scores[best] < min_score:
        return None, scores
    return best, scores
