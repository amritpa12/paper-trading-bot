import os
import time
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import yaml
import json

from broker import AlpacaBroker
from data import AlpacaData
from selector import pick_strategy
from risk import position_size, exceeded_daily_loss
from stats import daily_summary
from universe import load_symbol_universe
import csv

load_dotenv()

TZ = pytz.timezone(os.getenv("TIMEZONE", "America/New_York"))

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

symbols = load_symbol_universe(
    cfg.get("dynamic_universe", {}),
    cfg["symbols"],
)
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

LOG_FILE = "trades.csv"
STATUS_FILE = "status.json"


def write_status(state, last_action=None):
    payload = {
        "state": state,
        "last_action": last_action,
    }
    with open(STATUS_FILE, "w") as f:
        f.write(json.dumps(payload))


def log_trade(date, symbol, strategy, side, qty, entry, exit_price, pnl):
    header = ["date", "symbol", "strategy", "side", "qty", "entry", "exit", "pnl"]
    row = [date, symbol, strategy, side, qty, entry, exit_price, pnl]
    try:
        with open(LOG_FILE, "x", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(row)
    except FileExistsError:
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)


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
    last_summary_date = None

    while True:
        dt = now_et()
        if not market_open(dt):
            write_status("idle", "Market closed")
            # print daily summary once after close
            if dt.hour >= 16:
                today = dt.date().isoformat()
                if last_summary_date != today:
                    summary = daily_summary(today)
                    if summary:
                        print(f"Daily PnL {summary['date']}: {summary['total_pnl']:.2f} | Trades {summary['trades']} | Win {summary['win_rate']:.0%}")
                    last_summary_date = today
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
                write_status("running", f"No strategy selected for {symbol}")
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
                    write_status("running", f"BUY {symbol} x{qty} via {strat}")
                    print(f"BUY {symbol} x{qty} via {strat}")

            if sig == "sell" and symbol in held:
                pos = held[symbol]
                entry = float(pos.avg_entry_price)
                qty = abs(int(float(pos.qty)))
                broker.close_position(symbol)
                pnl = (last_price - entry) * qty
                log_trade(dt.date().isoformat(), symbol, strat, "sell", qty, entry, last_price, pnl)
                write_status("running", f"SELL {symbol} via {strat} | PnL {pnl:.2f}")
                print(f"SELL {symbol} via {strat} | PnL {pnl:.2f}")

        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    main_loop()
