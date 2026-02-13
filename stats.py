import pandas as pd
from datetime import datetime

LOG_FILE = "trades.csv"


def load_trades():
    try:
        return pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        return pd.DataFrame()


def daily_summary(date=None):
    df = load_trades()
    if df.empty:
        return None
    if date is None:
        date = datetime.utcnow().date().isoformat()
    day = df[df["date"] == date]
    if day.empty:
        return None
    total = day["pnl"].sum()
    wins = (day["pnl"] > 0).sum()
    losses = (day["pnl"] < 0).sum()
    return {
        "date": date,
        "trades": len(day),
        "total_pnl": float(total),
        "wins": int(wins),
        "losses": int(losses),
        "win_rate": float(wins / max(len(day), 1))
    }


def strategy_stats():
    df = load_trades()
    if df.empty:
        return None
    grouped = df.groupby("strategy").agg(
        trades=("pnl", "count"),
        total_pnl=("pnl", "sum"),
        avg_pnl=("pnl", "mean"),
        win_rate=("pnl", lambda s: (s > 0).mean()),
    ).reset_index()
    return grouped.sort_values("total_pnl", ascending=False)
