# Paper Trading Bot (Alpaca)

Intraday paper-trading bot for **stocks/ETFs** using multiple strategies and a simple regime-aware selector.

## Features
- Alpaca paper trading (no real money)
- Multiple strategies (trend, mean reversion, breakout)
- Strategy scoring + selection
- Risk rules: **1–2% per trade** + **3/5/7 rule** (3% stop, 5% target, 7% max daily loss)

## Setup
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# add ALPACA_API_KEY + ALPACA_API_SECRET
```

## Run
```bash
python main.py
```

## Dashboard
```bash
python dashboard.py
```

## Files
- `main.py` — orchestrates loop
- `broker.py` — Alpaca trading wrapper
- `data.py` — market data utilities
- `strategies/` — strategy signals
- `selector.py` — picks the best strategy per symbol
- `risk.py` — position sizing + stops + daily loss guard

## Notes
- This is a learning/paper bot. No guarantee of performance.
- You can edit `config.yaml` to change symbols and risk settings.
