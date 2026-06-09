# Fan Zone Profit Engine

An AI agent that turns World Cup 2026 fixtures into fan-zone revenue and
operations plans. For a given host city it projects the inbound fan wave,
recommends tenant activations, sizes staffing, flags fraud risk, and estimates
captured revenue — backed by MongoDB and a Vertex AI (Gemini 1.5 Pro)
reasoning step.

## Stack

- **Flask** API (`main.py`) served by gunicorn
- **Vertex AI Reasoning Engine** — Gemini 1.5 Pro (`agent.py`)
- **MongoDB** (Atlas cluster `worldcup-data`, db `fanzone`) via `tools.py`
- **Cloud Run** deploy (project `fan-zone-agent-2026`)

## Layout

```
main.py              Flask entrypoint (GET /, POST /agent, GET /health)
agent.py             6-step agent pipeline + revenue/fraud logic
tools.py             4 MongoDB tool functions
seed_data/           seed scripts for matches / fan_profiles / tenant_catalog
static/index.html    dark-theme UI (GLD-3, owned by frontend)
Dockerfile           python:3.11-slim, port 8080
```

## Local run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in MONGODB_URI + GCP_PROJECT
python seed_data/seed_all.py  # seed all three collections
python main.py                # serves on :8080
```

```bash
curl -s -X POST localhost:8080/agent \
  -H 'content-type: application/json' -d '{"city":"Dallas"}' | jq
```

## API

### `POST /agent`

Request: `{"city": "Dallas"}`

Response `200`:

```json
{
  "match_summary":     { "fixture": "...", "city": "...", "venue": "...", "date": "...", "home_team": "...", "away_team": "..." },
  "fan_wave":          { "total_fans": 0, "home_fans": 0, "away_fans": 0, "nationalities": [ { "nationality": "...", "count": 0, "avg_daily_spend_usd": 0, "top_spend_categories": ["..."], "fraud_risk_index": 0.0 } ] },
  "action_plan":       { "tenant_activations": [ { "tenant": "...", "category": "...", "reason": "..." } ], "staffing": "...", "campaigns": ["..."], "fraud_level": "low|medium|high" },
  "revenue_projection":{ "amount_usd": 0, "formula": "(home_fans*home_spend + away_fans*away_spend) * 0.65", "breakdown": { "home": 0, "away": 0, "capture_rate": 0.65 } },
  "fraud_alert":       { "level": "low|medium|high", "message": "..." },
  "reasoning":         "...",
  "action_id":         "..."
}
```

Errors: `400 {"error": "..."}` for a missing or unknown `city`.

### `GET /` — serves the dark-theme UI &nbsp; · &nbsp; `GET /health` — `{"status":"ok"}`

## Deploy (Cloud Run)

`MONGODB_URI` is read from Secret Manager; the service runs unauthenticated
with `min-instances 1`.

```bash
gcloud run deploy fan-zone-agent \
  --source . --project fan-zone-agent-2026 --region us-central1 \
  --allow-unauthenticated --min-instances 1 \
  --set-secrets MONGODB_URI=MONGODB_URI:latest \
  --set-env-vars GCP_PROJECT=fan-zone-agent-2026,GCP_REGION=us-central1
```

## License

MIT — see [LICENSE](LICENSE).
