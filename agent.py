"""Vertex AI reasoning agent for the Fan Zone Profit Engine.

Runs Gemini 1.5 Pro through Vertex AI. The agent is given access to four MongoDB
tools (declared as Vertex `FunctionDeclaration`s) and is instructed to follow a
fixed six-step plan that produces a structured revenue action plan for a mall.

Falls back to a fully deterministic local planner when Vertex AI credentials or
the SDK are unavailable — keeps the demo working offline.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from tools import (
    get_fan_spending_profiles,
    get_relevant_tenants,
    get_upcoming_match,
    log_agent_action,
)

load_dotenv()

GCP_PROJECT = os.environ.get("GCP_PROJECT", "fan-zone-agent-2026")
GCP_REGION = os.environ.get("GCP_REGION", "us-central1")
MODEL_NAME = "gemini-1.5-pro-002"

SYSTEM_INSTRUCTION = """\
You are the Fan Zone Profit Engine — a reasoning agent that prepares host-city
malls for 2026 FIFA World Cup matches.

You MUST follow these six steps in order, using the provided tools:
  1. Call get_upcoming_match(city) to look up the next fixture.
  2. Call get_fan_spending_profiles(nationalities) for the home AND away teams.
  3. Call get_relevant_tenants(categories) using the union of top_spend_categories.
  4. Compute revenue_projection_usd =
       (expected_home_fans * home_avg_daily_spend_usd
        + expected_away_fans * away_avg_daily_spend_usd) * 0.65
  5. Produce an action plan: tenant_activations, staffing_changes, campaigns,
     and a fraud_alert level (high if max fraud_risk_index > 0.15,
     medium if 0.10-0.15, otherwise low).
  6. Call log_agent_action(action_doc) to persist the decision.

Return a single JSON object with these top-level keys:
  match_summary, fan_wave, action_plan, revenue_projection, fraud_alert, reasoning.

Use US dollars, be specific, and keep reasoning under 5 sentences.
"""


# ---------------------------------------------------------------------------
# Vertex AI tool declarations
# ---------------------------------------------------------------------------

def _vertex_tool_declarations():
    from vertexai.generative_models import FunctionDeclaration, Tool

    decls = [
        FunctionDeclaration(
            name="get_upcoming_match",
            description="Look up the next upcoming match for a host city.",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        ),
        FunctionDeclaration(
            name="get_fan_spending_profiles",
            description="Return spending and fraud-risk profiles for the given fan nationalities.",
            parameters={
                "type": "object",
                "properties": {
                    "nationalities": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["nationalities"],
            },
        ),
        FunctionDeclaration(
            name="get_relevant_tenants",
            description="Return mall tenants whose category matches the requested fan spend categories.",
            parameters={
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                    }
                },
                "required": ["categories"],
            },
        ),
        FunctionDeclaration(
            name="log_agent_action",
            description="Persist the final action plan to the agent_actions collection.",
            parameters={
                "type": "object",
                "properties": {"action_doc": {"type": "object"}},
                "required": ["action_doc"],
            },
        ),
    ]
    return Tool(function_declarations=decls)


_TOOL_DISPATCH = {
    "get_upcoming_match": lambda args: get_upcoming_match(args["city"]),
    "get_fan_spending_profiles": lambda args: get_fan_spending_profiles(args["nationalities"]),
    "get_relevant_tenants": lambda args: get_relevant_tenants(args["categories"]),
    "log_agent_action": lambda args: log_agent_action(args["action_doc"]),
}


# ---------------------------------------------------------------------------
# Local deterministic planner (used as fallback)
# ---------------------------------------------------------------------------

def _fraud_level(max_risk: float) -> str:
    if max_risk > 0.15:
        return "high"
    if max_risk >= 0.10:
        return "medium"
    return "low"


def _build_plan(city: str) -> Dict[str, Any]:
    match = get_upcoming_match(city)
    if "error" in match:
        return {"error": match["error"]}

    home_nat = match["home_team"]["nationality"]
    away_nat = match["away_team"]["nationality"]
    profiles = get_fan_spending_profiles([home_nat, away_nat])
    by_nat = {p["nationality"]: p for p in profiles}
    home = by_nat[home_nat]
    away = by_nat[away_nat]

    categories = sorted(set(home["top_spend_categories"] + away["top_spend_categories"]))
    tenants = get_relevant_tenants(categories)

    home_fans = match["expected_home_fans"]
    away_fans = match["expected_away_fans"]
    revenue = (home_fans * home["avg_daily_spend_usd"]
               + away_fans * away["avg_daily_spend_usd"]) * 0.65

    max_risk = max(home["fraud_risk_index"], away["fraud_risk_index"])
    fraud_alert = _fraud_level(max_risk)

    tenant_activations = [
        {
            "tenant_id": t["tenant_id"],
            "name": t["name"],
            "category": t["category"],
            "action": "extend hours +3h, deploy fan-zone signage",
        }
        for t in tenants
    ]

    staffing_changes = [
        {"category": "food_and_beverage", "headcount_delta": "+35%"},
        {"category": "sportswear", "headcount_delta": "+50%"},
        {"category": "souvenirs", "headcount_delta": "+40%"},
        {"category": "services", "headcount_delta": "+15%"},
    ]

    campaigns = [
        f"{home_nat} pride pop-up at sportswear tenants (matchday -2h to +4h)",
        f"{away_nat} hospitality lounge near food court with bilingual concierge",
        "Match-ticket-as-coupon: 15% off purchases > $75 across fan_friendly tenants",
    ]

    action_plan = {
        "tenant_activations": tenant_activations,
        "staffing_changes": staffing_changes,
        "campaigns": campaigns,
    }

    match_summary = {
        "match_id": match["match_id"],
        "city": match["city"],
        "venue": match["venue"],
        "kickoff_utc": match["kickoff_utc"],
        "stage": match["stage"],
        "home_team": match["home_team"]["country"],
        "away_team": match["away_team"]["country"],
    }

    fan_wave = {
        "home": {
            "nationality": home_nat,
            "expected_fans": home_fans,
            "avg_daily_spend_usd": home["avg_daily_spend_usd"],
        },
        "away": {
            "nationality": away_nat,
            "expected_fans": away_fans,
            "avg_daily_spend_usd": away["avg_daily_spend_usd"],
        },
    }

    revenue_projection = {
        "amount_usd": round(revenue, 2),
        "formula": "(home_fans*home_spend + away_fans*away_spend) * 0.65",
        "capture_rate": 0.65,
    }

    reasoning = (
        f"{home_nat} hosts {away_nat} at {match['venue']}. "
        f"Combined wave of {home_fans + away_fans:,} fans skews toward "
        f"{', '.join(categories[:3])}. Capture model assumes 65% of fan daily spend "
        f"lands in-mall. Max fraud_risk_index {max_risk:.2f} → {fraud_alert} alert."
    )

    decision = {
        "match_summary": match_summary,
        "fan_wave": fan_wave,
        "action_plan": action_plan,
        "revenue_projection": revenue_projection,
        "fraud_alert": fraud_alert,
        "reasoning": reasoning,
    }
    log_agent_action({**decision, "source": "deterministic_fallback"})
    return decision


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_agent(city: str) -> Dict[str, Any]:
    """Run the agent for `city`. Tries Vertex AI, falls back to local planner."""
    vertex_exc: Exception | None = None
    try:
        return _run_vertex_agent(city)
    except Exception as exc:  # pragma: no cover - depends on credentials
        vertex_exc = exc
    try:
        plan = _build_plan(city)
    except Exception as exc:
        return {
            "error": (
                f"Could not reach data layer: {type(exc).__name__}: {exc}. "
                "Set MONGODB_URI in .env and seed the database."
            )
        }
    if isinstance(plan, dict) and "error" not in plan and vertex_exc is not None:
        plan["reasoning"] += f" (Vertex AI unavailable: {type(vertex_exc).__name__})"
    return plan


def _run_vertex_agent(city: str) -> Dict[str, Any]:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part

    vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
    tool = _vertex_tool_declarations()
    model = GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[tool],
    )
    chat = model.start_chat()
    prompt = (
        f"Prepare the mall in {city} for its next 2026 World Cup match. "
        "Follow the six-step plan and return the JSON object."
    )
    response = chat.send_message(prompt)

    # Tool-call loop. Bounded so a misbehaving model can't spin forever.
    for _ in range(8):
        function_calls = _extract_function_calls(response)
        if not function_calls:
            break
        responses: List[Part] = []
        for fc in function_calls:
            args = {k: v for k, v in fc.args.items()}
            tool_fn = _TOOL_DISPATCH.get(fc.name)
            result = tool_fn(args) if tool_fn else {"error": f"unknown tool {fc.name}"}
            responses.append(
                Part.from_function_response(name=fc.name, response={"content": result})
            )
        response = chat.send_message(responses)

    text = _final_text(response)
    decision = _parse_json_payload(text)
    if "reasoning" in decision and "source" not in decision:
        log_agent_action({**decision, "source": "vertex_gemini_1_5_pro"})
    return decision


def _extract_function_calls(response) -> List[Any]:
    calls: List[Any] = []
    for cand in getattr(response, "candidates", []) or []:
        content = getattr(cand, "content", None)
        for part in getattr(content, "parts", []) or []:
            fc = getattr(part, "function_call", None)
            if fc and fc.name:
                calls.append(fc)
    return calls


def _final_text(response) -> str:
    for cand in getattr(response, "candidates", []) or []:
        content = getattr(cand, "content", None)
        for part in getattr(content, "parts", []) or []:
            if getattr(part, "text", None):
                return part.text
    return getattr(response, "text", "") or ""


def _parse_json_payload(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return JSON: {text[:200]}")
    return json.loads(text[start : end + 1])
