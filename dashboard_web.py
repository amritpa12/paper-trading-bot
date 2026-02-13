from flask import Flask, jsonify, send_from_directory
from stats import daily_summary, strategy_stats, load_trades
import json
from pathlib import Path

app = Flask(__name__, static_folder="web")

STATUS_FILE = Path("status.json")

@app.get("/api/status")
def api_status():
    if STATUS_FILE.exists():
        return jsonify(json.loads(STATUS_FILE.read_text()))
    return jsonify({"status": "idle"})

@app.get("/api/trades")
def api_trades():
    df = load_trades()
    return jsonify(df.tail(50).to_dict(orient="records"))

@app.get("/api/daily")
def api_daily():
    s = daily_summary()
    return jsonify(s or {})

@app.get("/api/strategies")
def api_strategies():
    s = strategy_stats()
    if s is None:
        return jsonify([])
    return jsonify(s.to_dict(orient="records"))

@app.get("/")
def root():
    return send_from_directory("web", "index.html")

@app.get("/<path:path>")
def static_proxy(path):
    return send_from_directory("web", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
