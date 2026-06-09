"""MongoDB-backed tools for the Fan Zone Profit Engine agent.

Four functions the agent calls in sequence:
  1. get_upcoming_match(city)            -> the next fixture in that city
  2. get_fan_spending_profiles(nats)     -> spend/fraud profiles per nationality
  3. get_relevant_tenants(categories)    -> tenants matching the fans' spend categories
  4. log_agent_action(action)            -> persist the agent's decision

The Mongo client is created lazily and cached so the module imports cleanly
even when MONGODB_URI is unset (e.g. during unit tests, where the collection
accessors are monkeypatched).

DB: fanzone (cluster worldcup-data)
Collections: matches, fan_profiles, tenant_catalog, agent_actions
"""

import os
from datetime import datetime, timezone

from pymongo import MongoClient

DB_NAME = "fanzone"

_client = None
_db = None


def get_db():
    """Return the fanzone database handle, creating the client on first use."""
    global _client, _db
    if _db is None:
        uri = os.environ.get("MONGODB_URI")
        if not uri:
            raise RuntimeError(
                "MONGODB_URI is not set — cannot connect to MongoDB. "
                "Set it in .env (local) or via Secret Manager (Cloud Run)."
            )
        _client = MongoClient(uri)
        _db = _client[DB_NAME]
    return _db


def get_upcoming_match(city):
    """Return the next fixture scheduled in `city`, or None if none exists.

    Case-insensitive exact match on the city name. When multiple fixtures
    exist for a city, the earliest upcoming one (by date) is returned.
    """
    db = get_db()
    return db.matches.find_one(
        {"city": {"$regex": f"^{city}$", "$options": "i"}},
        sort=[("date", 1)],
        projection={"_id": 0},
    )


def get_fan_spending_profiles(nationalities):
    """Return spend/fraud profiles for the given list of nationalities.

    Preserves the order requested by the caller so home/away mapping stays
    deterministic. Nationalities with no profile are simply omitted.
    """
    db = get_db()
    docs = db.fan_profiles.find(
        {"nationality": {"$in": list(nationalities)}},
        projection={"_id": 0},
    )
    by_nat = {d["nationality"]: d for d in docs}
    return [by_nat[n] for n in nationalities if n in by_nat]


def get_relevant_tenants(categories):
    """Return tenants whose category is in `categories`, best matches first."""
    db = get_db()
    docs = db.tenant_catalog.find(
        {"category": {"$in": list(categories)}},
        projection={"_id": 0},
        sort=[("category", 1), ("name", 1)],
    )
    return list(docs)


def log_agent_action(action):
    """Persist an agent decision to agent_actions and return its string id."""
    db = get_db()
    doc = dict(action)
    doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    result = db.agent_actions.insert_one(doc)
    return str(result.inserted_id)
