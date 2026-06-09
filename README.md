# Fan Zone Profit Engine

An AI agent that turns World Cup 2026 fixtures into fan-zone revenue and
operations plans. For a given host city it projects the inbound fan wave,
recommends tenant activations, sizes staffing, flags fraud risk, and estimates
captured revenue — with all data access going through **MongoDB's MCP server**
and a Vertex AI (Gemini 1.5 Pro) reasoning step.

## Stack

- **Flask** API (`main.py`) served by gunicorn
- **Vertex AI Reasoning Engine** — Gemini 1.5 Pro (`agent.py`)
- **MongoDB MCP server** (partner integration) — every data tool runs over the
  Model Context Protocol (`mcp_bridge.py` → `tools.py`)
- **MongoDB** Atlas cluster `worldcup-data`, db `fanzone`
- **Cloud Run** deploy (project `fan-zone-agent-2026`)

## Partner integration — MongoDB MCP (Model Context Protocol)

The agent does not touch the MongoDB driver at request time. Instead it talks
to MongoDB's official [`mongodb-mcp-server`](https://github.com/mongodb-js/mongodb-mcp-server)
over MCP: `mcp_bridge.py` spawns the server as a stdio child process and keeps a
single MCP session alive for the worker's lifetime; the four agent tools in
`tools.py` call MCP tools through it —

| Agent tool | MCP tool |
|---|---|
| `get_upcoming_match` / `get_fan_spending_profiles` / `get_relevant_tenants` | `find` |
| `log_agent_action` (the agent's write-back) | `insert-many` |

This is the "agent uses a partner's tools to accomplish a task" capability: the
agent both reads its grounding data and persists its decision via MCP. The
`POST /agent` response shape is unchanged.

## Layout

```
main.py              Flask entrypoint (GET /, POST /agent, GET /health)
agent.py             6-step agent pipeline + revenue/fraud logic
tools.py             4 agent tools — all routed through MongoDB MCP
mcp_bridge.py        long-lived MCP session to mongodb-mcp-server (stdio)
seed_data/           seed scripts for matches / fan_profiles / tenant_catalog
static/index.html    dark-theme UI (GLD-3, owned by frontend)
Dockerfile           python:3.11-slim + Node (hosts the MCP server), port 8080
```

## Local run

Requires **Node.js** on PATH (to host the MongoDB MCP server) in addition to
Python 3.11.

```bash
npm install -g mongodb-mcp-server     # or rely on `npx -y mongodb-mcp-server`
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set MONGODB_URI, GCP_PROJECT, MONGODB_MCP_CMD
python seed_data/seed_all.py  # seed all three collections
python main.py                # serves on :8080
```

`MONGODB_MCP_CMD` is how `mcp_bridge.py` launches the server (default
`mongodb-mcp-server`; set it to the full path or to `npx` if not on PATH).

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
