# Fan Zone Profit Engine

An AI-agent web app that prepares host-city malls for **2026 FIFA World Cup**
matches. Pick a host city, and a Vertex AI / Gemini 1.5 Pro agent (wired to
MongoDB Atlas via the MongoDB MCP server) looks up the next match, profiles the
incoming fan wave, picks which mall tenants to activate, recommends staffing /
campaign moves, raises a fraud-risk alert, and prints a projected revenue
uplift in dollars.

## Stack

- **Backend** — Python 3.11, Flask
- **Agent** — Google Cloud Vertex AI, Gemini 1.5 Pro, Vertex AI Reasoning Engine
- **Data** — MongoDB Atlas + MongoDB Atlas MCP server
- **Frontend** — plain HTML / CSS / JS, dark theme
- **Deploy** — Cloud Run

## Folder structure

```
fan-zone-profit-engine/
├── LICENSE              # MIT
├── README.md
├── .env                 # local secrets (never commit)
├── .gitignore
├── main.py              # Flask app
├── agent.py             # Vertex AI agent + tool loop
├── tools.py             # 4 MongoDB-backed tool functions
├── seed_data/
│   ├── seed_matches.py
│   ├── seed_fan_profiles.py
│   └── seed_tenants.py
├── static/
│   └── index.html
├── requirements.txt
└── Dockerfile
```

## MongoDB layout

Database: **`fanzone`**

| Collection      | Purpose                                                    |
| --------------- | ---------------------------------------------------------- |
| `matches`       | 5 World Cup 2026 fixtures (Dallas, LA, NY, Miami, SF)      |
| `fan_profiles`  | 10 nationality spend & fraud-risk profiles                 |
| `tenant_catalog`| 8 fictional mall tenants across 5 categories               |
| `agent_actions` | Empty — written to by the agent on every run               |

## Local setup

```bash
# 1. clone & install
git clone https://github.com/<your-user>/fan-zone-profit-engine.git
cd fan-zone-profit-engine
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. configure secrets
cp .env .env.local   # or edit .env directly
#   MONGODB_URI=mongodb+srv://...
#   GCP_PROJECT=fan-zone-agent-2026
#   GCP_REGION=us-central1

# 3. seed Atlas
python seed_data/seed_matches.py
python seed_data/seed_fan_profiles.py
python seed_data/seed_tenants.py

# 4. auth to GCP for Vertex AI
gcloud auth application-default login
gcloud config set project fan-zone-agent-2026

# 5. run
python main.py
# → open http://localhost:8080
```

If Vertex AI credentials aren't configured the agent gracefully falls back to
a deterministic local planner that uses the same MongoDB tools, so the demo
still returns a full plan.

## Agent — 6-step plan

1. `get_upcoming_match(city)` — query `matches`.
2. `get_fan_spending_profiles(nationalities)` — query `fan_profiles` for the
   home & away nationalities.
3. `get_relevant_tenants(categories)` — query `tenant_catalog` for tenants
   matching the union of fan spend categories.
4. Compute
   `revenue_projection = (home_fans·home_spend + away_fans·away_spend) · 0.65`.
5. Build the action plan: tenant activations, staffing deltas, campaigns,
   and a fraud-alert level
   (`high` if max fraud_risk_index > 0.15, `medium` if 0.10–0.15, else `low`).
6. `log_agent_action(action_doc)` — persist to `agent_actions`.

Agent output is JSON with keys:
`match_summary`, `fan_wave`, `action_plan`, `revenue_projection`,
`fraud_alert`, `reasoning`.

## Deploy to Cloud Run

```bash
# 1. push the MongoDB URI to Secret Manager
gcloud secrets create MONGODB_URI --replication-policy=automatic
echo -n "mongodb+srv://..." | gcloud secrets versions add MONGODB_URI --data-file=-

# 2. build + deploy
gcloud run deploy fan-zone-profit-engine \
  --source . \
  --region us-central1 \
  --project fan-zone-agent-2026 \
  --allow-unauthenticated \
  --min-instances 1 \
  --set-env-vars GCP_PROJECT=fan-zone-agent-2026,GCP_REGION=us-central1 \
  --set-secrets MONGODB_URI=MONGODB_URI:latest
```

The deploy prints a live HTTPS URL — that is the demo link.

## API

`POST /agent`

```json
{ "city": "Dallas" }
```

Returns the JSON decision object described above.

`GET /healthz` → `{"status": "ok"}`

## License

[MIT](LICENSE).
