"""Fan Zone Profit Engine — Flask entrypoint.

Routes:
  GET  /         -> serves the static dark-theme UI (static/index.html)
  POST /agent    -> runs the agent for {"city": "..."} and returns the decision
  GET  /health   -> liveness probe for Cloud Run

Run locally:  python main.py   (or: gunicorn -b :8080 main:app)
Cloud Run injects PORT (8080).
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from agent import MatchNotFoundError, run_agent

load_dotenv()

app = Flask(__name__, static_folder="static")


@app.get("/")
def index():
    # static/index.html is owned by the frontend ticket (GLD-3). Serve it when
    # present; until that PR lands, return a minimal placeholder so the service
    # is self-contained and GET / never 500s.
    index_path = os.path.join(app.static_folder, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, "index.html")
    return (
        "<!doctype html><title>Fan Zone Profit Engine</title>"
        "<p>API is live. POST /agent with {\"city\": \"Dallas\"}.</p>",
        200,
        {"Content-Type": "text/html"},
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/agent")
def agent():
    body = request.get_json(silent=True) or {}
    city = (body.get("city") or "").strip()
    if not city:
        return jsonify({"error": "Field 'city' is required."}), 400
    try:
        return jsonify(run_agent(city))
    except MatchNotFoundError:
        return jsonify({"error": f"No upcoming match found for city '{city}'."}), 400
    except Exception as exc:  # noqa: BLE001 — surface a clean 500 to the client
        app.logger.exception("agent run failed")
        return jsonify({"error": "Internal error running agent.", "detail": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
