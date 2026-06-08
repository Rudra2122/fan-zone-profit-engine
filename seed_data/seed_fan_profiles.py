"""Seed the `fan_profiles` collection — 10 nationalities.

Each profile: avg_daily_spend_usd, top_spend_categories, fraud_risk_index (0-1).
Categories align with tenant_catalog: food, luxury, sportswear, souvenirs.

Idempotent: clears and re-inserts. Run: python seed_data/seed_fan_profiles.py
"""

from _db import get_db

FAN_PROFILES = [
    {"nationality": "USA", "avg_daily_spend_usd": 165,
     "top_spend_categories": ["food", "sportswear"], "fraud_risk_index": 0.18},
    {"nationality": "Mexico", "avg_daily_spend_usd": 120,
     "top_spend_categories": ["food", "souvenirs"], "fraud_risk_index": 0.30},
    {"nationality": "Brazil", "avg_daily_spend_usd": 140,
     "top_spend_categories": ["sportswear", "food"], "fraud_risk_index": 0.42},
    {"nationality": "Argentina", "avg_daily_spend_usd": 130,
     "top_spend_categories": ["sportswear", "souvenirs"], "fraud_risk_index": 0.38},
    {"nationality": "England", "avg_daily_spend_usd": 175,
     "top_spend_categories": ["food", "luxury"], "fraud_risk_index": 0.22},
    {"nationality": "Netherlands", "avg_daily_spend_usd": 160,
     "top_spend_categories": ["food", "souvenirs"], "fraud_risk_index": 0.20},
    {"nationality": "Colombia", "avg_daily_spend_usd": 110,
     "top_spend_categories": ["food", "souvenirs"], "fraud_risk_index": 0.55},
    {"nationality": "Japan", "avg_daily_spend_usd": 190,
     "top_spend_categories": ["luxury", "souvenirs"], "fraud_risk_index": 0.08},
    {"nationality": "Germany", "avg_daily_spend_usd": 170,
     "top_spend_categories": ["food", "sportswear"], "fraud_risk_index": 0.15},
    {"nationality": "Saudi Arabia", "avg_daily_spend_usd": 240,
     "top_spend_categories": ["luxury", "food"], "fraud_risk_index": 0.12},
]


def main():
    db = get_db()
    db.fan_profiles.delete_many({})
    db.fan_profiles.insert_many([dict(p) for p in FAN_PROFILES])
    print(f"Seeded {len(FAN_PROFILES)} fan profiles into fanzone.fan_profiles")


if __name__ == "__main__":
    main()
