import os
import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

class AlpacaData:
    def __init__(self):
        key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_API_SECRET")
        self.feed = os.getenv("ALPACA_DATA_FEED", "iex").lower()
        self.client = StockHistoricalDataClient(key, secret)

    def _resolve_feed(self):
        if self.feed == "sip":
            return DataFeed.SIP
        return DataFeed.IEX

    def get_bars(self, symbol, start, end, timeframe_minutes=1):
        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=start,
            end=end,
            limit=10000,
            adjustment="raw",
            feed=self._resolve_feed(),
        )
        bars = self.client.get_stock_bars(req).df
        if bars.empty:
            return pd.DataFrame()
        if isinstance(bars.index, pd.MultiIndex):
            bars = bars.loc[symbol]
        bars = bars.reset_index()
        bars = bars.rename(columns={
            "timestamp": "time",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })
        return bars
