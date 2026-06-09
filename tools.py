"""Agent data tools — backed by MongoDB's MCP server (partner integration).

The four functions the agent calls in sequence. Every one goes through the
Model Context Protocol via `mcp_bridge` (MongoDB's official `mongodb-mcp-server`)
rather than the driver directly — `find` for reads, `insert-many` for the write.
The function signatures and return shapes are unchanged, so `agent.py` and the
POST /agent contract are untouched.

DB: fanzone (cluster worldcup-data)
Collections: matches, fan_profiles, tenant_catalog, agent_actions
"""

import uuid
from datetime import datetime, timezone

from mcp_bridge import bridge


def get_upcoming_match(city):
    """Return the next fixture scheduled in `city`, or None if none exists.

    Case-insensitive exact match; earliest upcoming fixture by date.
    """
    docs = bridge.find(
        "matches",
        filter={"city": {"$regex": f"^{city}$", "$options": "i"}},
        sort={"date": 1},
        limit=1,
        projection={"_id": 0},
    )
    return docs[0] if docs else None


def get_fan_spending_profiles(nationalities):
    """Return spend/fraud profiles for the given nationalities, in request order."""
    docs = bridge.find(
        "fan_profiles",
        filter={"nationality": {"$in": list(nationalities)}},
        projection={"_id": 0},
    )
    by_nat = {d["nationality"]: d for d in docs}
    return [by_nat[n] for n in nationalities if n in by_nat]


def get_relevant_tenants(categories):
    """Return tenants whose category is in `categories`, best matches first."""
    return bridge.find(
        "tenant_catalog",
        filter={"category": {"$in": list(categories)}},
        sort={"category": 1, "name": 1},
        projection={"_id": 0},
    )


def log_agent_action(action):
    """Persist an agent decision to agent_actions (via MCP) and return its id."""
    action_id = uuid.uuid4().hex
    doc = dict(action)
    doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    doc["action_id"] = action_id
    bridge.insert_many("agent_actions", [doc])
    return action_id
