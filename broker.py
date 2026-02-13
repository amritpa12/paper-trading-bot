import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

class AlpacaBroker:
    def __init__(self):
        key = os.getenv("ALPACA_API_KEY")
        secret = os.getenv("ALPACA_API_SECRET")
        paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"
        self.client = TradingClient(key, secret, paper=paper)

    def account(self):
        return self.client.get_account()

    def positions(self):
        return self.client.get_all_positions()

    def submit_market_order(self, symbol, qty, side):
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        return self.client.submit_order(order)

    def close_position(self, symbol):
        return self.client.close_position(symbol)
