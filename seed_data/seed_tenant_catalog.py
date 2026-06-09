"""Seed the `tenant_catalog` collection — 8 tenants.

Categories: food, luxury, sportswear, souvenirs (2 tenants each).

Idempotent: clears and re-inserts. Run: python seed_data/seed_tenant_catalog.py
"""

from _db import get_db

TENANTS = [
    {"name": "Stadium Street Eats", "category": "food",
     "capacity": 1200, "avg_ticket_usd": 28},
    {"name": "Goal Line Grill", "category": "food",
     "capacity": 900, "avg_ticket_usd": 34},
    {"name": "Maison Or Lounge", "category": "luxury",
     "capacity": 150, "avg_ticket_usd": 320},
    {"name": "Heritage Watch Bar", "category": "luxury",
     "capacity": 120, "avg_ticket_usd": 450},
    {"name": "Pitch Perfect Apparel", "category": "sportswear",
     "capacity": 600, "avg_ticket_usd": 85},
    {"name": "Kit & Cleats", "category": "sportswear",
     "capacity": 500, "avg_ticket_usd": 95},
    {"name": "World Cup Memories", "category": "souvenirs",
     "capacity": 800, "avg_ticket_usd": 22},
    {"name": "Flag & Scarf Co.", "category": "souvenirs",
     "capacity": 700, "avg_ticket_usd": 18},
]


def main():
    db = get_db()
    db.tenant_catalog.delete_many({})
    db.tenant_catalog.insert_many([dict(t) for t in TENANTS])
    print(f"Seeded {len(TENANTS)} tenants into fanzone.tenant_catalog")


if __name__ == "__main__":
    main()
