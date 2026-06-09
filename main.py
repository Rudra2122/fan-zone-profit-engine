"""Flask entry point for the Fan Zone Profit Engine."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from agent import run_agent

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

ALLOWED_CITIES = {"Dallas", "Los Angeles", "New York", "Miami", "San Francisco"}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/agent")
def agent_endpoint():
    payload = request.get_json(silent=True) or {}
    city = (payload.get("city") or "").strip()
    if city not in ALLOWED_CITIES:
        return jsonify({"error": f"Unsupported city: {city!r}"}), 400
    result = run_agent(city)
    status = 200 if "error" not in result else 502
    return jsonify(result), status


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
