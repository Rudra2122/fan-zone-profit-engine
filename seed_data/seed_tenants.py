"""Seed the `tenant_catalog` collection with 8 fictional mall tenants."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

TENANTS = [
    {
        "tenant_id": "T-001",
        "name": "Estadio Grill",
        "category": "food_and_beverage",
        "avg_ticket_usd": 38,
        "capacity": 220,
        "fan_friendly": True,
    },
    {
        "tenant_id": "T-002",
        "name": "Copa Cafe",
        "category": "food_and_beverage",
        "avg_ticket_usd": 18,
        "capacity": 140,
        "fan_friendly": True,
    },
    {
        "tenant_id": "T-003",
        "name": "Maison Lumiere",
        "category": "luxury_goods",
        "avg_ticket_usd": 620,
        "capacity": 35,
        "fan_friendly": False,
    },
    {
        "tenant_id": "T-004",
        "name": "Atelier 22",
        "category": "luxury_goods",
        "avg_ticket_usd": 480,
        "capacity": 28,
        "fan_friendly": False,
    },
    {
        "tenant_id": "T-005",
        "name": "Pitch Perfect Sports",
        "category": "sportswear",
        "avg_ticket_usd": 95,
        "capacity": 180,
        "fan_friendly": True,
    },
    {
        "tenant_id": "T-006",
        "name": "Goal Threads",
        "category": "sportswear",
        "avg_ticket_usd": 72,
        "capacity": 160,
        "fan_friendly": True,
    },
    {
        "tenant_id": "T-007",
        "name": "Trophy Souvenirs",
        "category": "souvenirs",
        "avg_ticket_usd": 28,
        "capacity": 120,
        "fan_friendly": True,
    },
    {
        "tenant_id": "T-008",
        "name": "Fan Concierge",
        "category": "services",
        "avg_ticket_usd": 55,
        "capacity": 60,
        "fan_friendly": True,
    },
]


def main():
    uri = os.environ["MONGODB_URI"]
    client = MongoClient(uri)
    db = client["fanzone"]
    coll = db["tenant_catalog"]
    coll.delete_many({})
    coll.insert_many(TENANTS)
    coll.create_index("category")
    coll.create_index("tenant_id", unique=True)
    # Ensure agent_actions collection exists (empty)
    db["agent_actions"].create_index("created_at")
    print(f"Seeded {coll.count_documents({})} tenants into fanzone.tenant_catalog")
    print("Ensured fanzone.agent_actions collection exists (empty).")


if __name__ == "__main__":
    main()
