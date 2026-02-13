import os
import time
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import yaml

from broker import AlpacaBroker
from data import AlpacaData
from selector import pick_strategy
from risk import position_size, exceeded_daily_loss

load_dotenv()

TZ = pytz.timezone(os.getenv("TIMEZONE", "America/New_York"))

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

symbols = cfg["symbols"]
interval_minutes = cfg["interval_minutes"]
lookback_days = cfg["lookback_days"]
max_positions = cfg["max_positions"]

risk_cfg = cfg["risk"]
selector_cfg = cfg["selector"]

strategy_cfg = cfg["strategies"]
enabled_strategies = [s["name"] for s in strategy_cfg if s.get("enabled")]

broker = AlpacaBroker()
data = AlpacaData()

start_equity = None


def now_et():
    return datetime.now(TZ)


def market_open(dt):
    # simple guard: trade 9:35-15:55 ET
    if dt.weekday() >= 5:
        return False
    if dt.hour < 9 or dt.hour > 15:
        return False
    if dt.hour == 9 and dt.minute < 35:
        return False
    if dt.hour == 15 and dt.minute > 55:
        return False
    return True


def main_loop():
    global start_equity
    acct = broker.account()
    start_equity = float(acct.equity)

    while True:
        dt = now_et()
        if not market_open(dt):
            time.sleep(60)
            continue

        acct = broker.account()
        equity = float(acct.equity)
        if exceeded_daily_loss(start_equity, equity, risk_cfg["max_daily_loss_pct"]):
            print("Daily loss limit hit. Halting.")
            break

        positions = broker.positions()
        held = {p.symbol: p for p in positions}

        for symbol in symbols:
            start = dt - timedelta(days=lookback_days)
            bars = data.get_bars(symbol, start, dt)
            if bars.empty:
                continue

            strat, scores = pick_strategy(
                bars,
                enabled_strategies,
                window=selector_cfg["score_window_bars"],
                min_score=selector_cfg["min_score"],
            )
            if strat is None:
                continue

            # get signal from chosen strategy
            mod = __import__(f"strategies.{strat}", fromlist=["signal"])
            sig = mod.signal(bars)
            last_price = bars.iloc[-1].close

            if sig == "buy" and symbol not in held and len(held) < max_positions:
                qty = position_size(
                    equity,
                    last_price,
                    risk_cfg["per_trade_risk_pct"],
                    risk_cfg["stop_loss_pct"],
                )
                if qty > 0:
                    broker.submit_market_order(symbol, qty, "buy")
                    print(f"BUY {symbol} x{qty} via {strat}")

            if sig == "sell" and symbol in held:
                broker.close_position(symbol)
                print(f"SELL {symbol} via {strat}")

        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    main_loop()
