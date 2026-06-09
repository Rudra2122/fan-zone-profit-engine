"""Seed the `fan_profiles` collection with 10 nationality spending profiles."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

PROFILES = [
    {
        "nationality": "Argentina",
        "avg_daily_spend_usd": 185,
        "top_spend_categories": ["food_and_beverage", "sportswear", "souvenirs"],
        "fraud_risk_index": 0.09,
        "luxury_spend_likelihood": 0.32,
    },
    {
        "nationality": "France",
        "avg_daily_spend_usd": 245,
        "top_spend_categories": ["luxury_goods", "food_and_beverage", "services"],
        "fraud_risk_index": 0.07,
        "luxury_spend_likelihood": 0.61,
    },
    {
        "nationality": "Brazil",
        "avg_daily_spend_usd": 165,
        "top_spend_categories": ["food_and_beverage", "souvenirs", "sportswear"],
        "fraud_risk_index": 0.12,
        "luxury_spend_likelihood": 0.28,
    },
    {
        "nationality": "Mexico",
        "avg_daily_spend_usd": 140,
        "top_spend_categories": ["food_and_beverage", "souvenirs", "sportswear"],
        "fraud_risk_index": 0.11,
        "luxury_spend_likelihood": 0.22,
    },
    {
        "nationality": "England",
        "avg_daily_spend_usd": 210,
        "top_spend_categories": ["food_and_beverage", "sportswear", "services"],
        "fraud_risk_index": 0.16,
        "luxury_spend_likelihood": 0.44,
    },
    {
        "nationality": "Germany",
        "avg_daily_spend_usd": 220,
        "top_spend_categories": ["luxury_goods", "sportswear", "services"],
        "fraud_risk_index": 0.06,
        "luxury_spend_likelihood": 0.55,
    },
    {
        "nationality": "USA",
        "avg_daily_spend_usd": 230,
        "top_spend_categories": ["food_and_beverage", "sportswear", "services"],
        "fraud_risk_index": 0.08,
        "luxury_spend_likelihood": 0.48,
    },
    {
        "nationality": "Spain",
        "avg_daily_spend_usd": 195,
        "top_spend_categories": ["food_and_beverage", "luxury_goods", "souvenirs"],
        "fraud_risk_index": 0.10,
        "luxury_spend_likelihood": 0.51,
    },
    {
        "nationality": "Morocco",
        "avg_daily_spend_usd": 115,
        "top_spend_categories": ["souvenirs", "food_and_beverage", "services"],
        "fraud_risk_index": 0.18,
        "luxury_spend_likelihood": 0.19,
    },
    {
        "nationality": "Portugal",
        "avg_daily_spend_usd": 175,
        "top_spend_categories": ["food_and_beverage", "luxury_goods", "souvenirs"],
        "fraud_risk_index": 0.09,
        "luxury_spend_likelihood": 0.46,
    },
]


def main():
    uri = os.environ["MONGODB_URI"]
    client = MongoClient(uri)
    db = client["fanzone"]
    coll = db["fan_profiles"]
    coll.delete_many({})
    coll.insert_many(PROFILES)
    coll.create_index("nationality", unique=True)
    print(f"Seeded {coll.count_documents({})} fan profiles into fanzone.fan_profiles")


if __name__ == "__main__":
    main()
