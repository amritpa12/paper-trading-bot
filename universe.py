import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pandas as pd
import pytz
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient

CACHE_FILE = Path("universe_cache.json")
UTC = pytz.UTC


def _env_creds():
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_API_SECRET")
    paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"
    if not key or not secret:
        raise RuntimeError("Missing ALPACA_API_KEY/ALPACA_API_SECRET")
    return key, secret, paper


def _data_feed():
    feed = os.getenv("ALPACA_DATA_FEED", "iex").lower()
    return DataFeed.SIP if feed == "sip" else DataFeed.IEX


def _load_cache(ttl_minutes: int) -> List[str]:
    if not CACHE_FILE.exists():
        return []
    try:
        payload = json.loads(CACHE_FILE.read_text())
        ts = datetime.fromisoformat(payload.get("timestamp"))
        if datetime.utcnow() - ts > timedelta(minutes=ttl_minutes):
            return []
        return payload.get("symbols", [])
    except Exception:
        return []


def _save_cache(symbols: List[str]):
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbols": symbols,
    }
    CACHE_FILE.write_text(json.dumps(payload, indent=2))


def _chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _candidate_symbols(max_candidates: int) -> List[str]:
    key, secret, paper = _env_creds()
    client = TradingClient(key, secret, paper=paper)
    assets = client.get_all_assets(status="active", asset_class="us_equity")
    symbols = []
    for asset in assets:
        if not asset.tradable:
            continue
        if getattr(asset, "symbol", "").startswith("$"):
            continue
        symbols.append(asset.symbol)
        if len(symbols) >= max_candidates:
            break
    return symbols


def _fetch_volume_ranks(symbols: List[str], lookback_days: int, min_price: float, max_price: float):
    key, secret, _ = _env_creds()
    data_client = StockHistoricalDataClient(key, secret)
    end = datetime.now(UTC)
    start = end - timedelta(days=lookback_days)
    feed = _data_feed()

    rows = []
    for batch in _chunk(symbols, 50):
        req = StockBarsRequest(
            symbol_or_symbols=batch,
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            limit=lookback_days * len(batch),
            adjustment="raw",
            feed=feed,
        )
        bars = data_client.get_stock_bars(req).df
        if bars.empty:
            continue
        if isinstance(bars.index, pd.MultiIndex):
            bars = bars.reset_index()
        grouped = bars.groupby("symbol")
        for symbol, grp in grouped:
            grp = grp.sort_values("timestamp")
            last_close = grp.iloc[-1].close
            if last_close is None or not (min_price <= last_close <= max_price):
                continue
            avg_volume = grp.volume.mean()
            rows.append({
                "symbol": symbol,
                "avg_volume": float(avg_volume),
                "last_close": float(last_close),
            })
    return rows


def build_universe(cfg: dict) -> List[str]:
    max_symbols = cfg.get("max_symbols", 10)
    max_candidates = cfg.get("max_candidates", 200)
    lookback_days = cfg.get("lookback_days", 5)
    min_price = cfg.get("min_price", 5.0)
    max_price = cfg.get("max_price", 500.0)
    cache_minutes = cfg.get("cache_minutes", 60)

    cached = _load_cache(cache_minutes)
    if cached:
        return cached[:max_symbols]

    candidates = _candidate_symbols(max_candidates)
    ranks = _fetch_volume_ranks(candidates, lookback_days, min_price, max_price)
    if not ranks:
        return []
    ranks.sort(key=lambda r: r["avg_volume"], reverse=True)
    symbols = [r["symbol"] for r in ranks[:max_symbols]]
    _save_cache(symbols)
    return symbols


def load_symbol_universe(cfg: dict, fallback: List[str]) -> List[str]:
    if not cfg.get("enabled", False):
        return fallback
    try:
        symbols = build_universe(cfg)
        if symbols:
            print(f"[universe] Loaded dynamic symbols: {symbols}")
            return symbols
    except Exception as exc:
        print(f"[universe] Failed to build dynamic universe: {exc}")
    return fallback
