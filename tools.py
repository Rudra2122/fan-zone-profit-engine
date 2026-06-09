"""MongoDB-backed tool functions exposed to the Vertex AI agent.

These four callables mirror the MongoDB Atlas MCP server's tool surface and are
the only way the agent reads or writes data.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DB_NAME = "fanzone"


@lru_cache(maxsize=1)
def _client() -> MongoClient:
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not set")
    return MongoClient(uri, serverSelectionTimeoutMS=8000)


def _db():
    return _client()[DB_NAME]


def _clean(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Drop Mongo ObjectId and coerce datetimes to ISO strings for JSON safety."""
    out: Dict[str, Any] = {}
    for k, v in doc.items():
        if k == "_id":
            continue
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, dict):
            out[k] = _clean(v)
        elif isinstance(v, list):
            out[k] = [_clean(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out


def get_upcoming_match(city: str) -> Dict[str, Any]:
    """Return the next scheduled match in `city`, or the soonest stored one."""
    now = datetime.utcnow()
    coll = _db()["matches"]
    doc = coll.find_one(
        {"city": city, "kickoff_utc": {"$gte": now}},
        sort=[("kickoff_utc", 1)],
    )
    if not doc:
        doc = coll.find_one({"city": city}, sort=[("kickoff_utc", 1)])
    if not doc:
        return {"error": f"No match found for city '{city}'"}
    return _clean(doc)


def get_fan_spending_profiles(nationalities: Iterable[str]) -> List[Dict[str, Any]]:
    """Return the spend/risk profile for each requested nationality."""
    natl = list(nationalities)
    docs = list(_db()["fan_profiles"].find({"nationality": {"$in": natl}}))
    return [_clean(d) for d in docs]


def get_relevant_tenants(categories: Iterable[str]) -> List[Dict[str, Any]]:
    """Return mall tenants whose category matches one of the fan spend categories."""
    cats = list(categories)
    docs = list(_db()["tenant_catalog"].find({"category": {"$in": cats}}))
    return [_clean(d) for d in docs]


def log_agent_action(action_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Persist the agent's decision into `agent_actions`. Returns the inserted id."""
    record = dict(action_doc)
    record["created_at"] = datetime.now(timezone.utc)
    result = _db()["agent_actions"].insert_one(record)
    return {"inserted_id": str(result.inserted_id)}
