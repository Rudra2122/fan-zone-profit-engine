"""Seed the `matches` collection with 5 World Cup 2026 fixtures."""
import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MATCHES = [
    {
        "match_id": "WC2026-DAL-001",
        "city": "Dallas",
        "venue": "AT&T Stadium",
        "kickoff_utc": datetime(2026, 6, 14, 20, 0),
        "stage": "Group Stage",
        "home_team": {"country": "Argentina", "nationality": "Argentina"},
        "away_team": {"country": "Mexico", "nationality": "Mexico"},
        "expected_home_fans": 28000,
        "expected_away_fans": 32000,
    },
    {
        "match_id": "WC2026-LAX-001",
        "city": "Los Angeles",
        "venue": "SoFi Stadium",
        "kickoff_utc": datetime(2026, 6, 15, 22, 0),
        "stage": "Group Stage",
        "home_team": {"country": "Brazil", "nationality": "Brazil"},
        "away_team": {"country": "Portugal", "nationality": "Portugal"},
        "expected_home_fans": 34000,
        "expected_away_fans": 22000,
    },
    {
        "match_id": "WC2026-NYC-001",
        "city": "New York",
        "venue": "MetLife Stadium",
        "kickoff_utc": datetime(2026, 6, 17, 19, 0),
        "stage": "Group Stage",
        "home_team": {"country": "France", "nationality": "France"},
        "away_team": {"country": "England", "nationality": "England"},
        "expected_home_fans": 30000,
        "expected_away_fans": 31000,
    },
    {
        "match_id": "WC2026-MIA-001",
        "city": "Miami",
        "venue": "Hard Rock Stadium",
        "kickoff_utc": datetime(2026, 6, 18, 21, 0),
        "stage": "Group Stage",
        "home_team": {"country": "Spain", "nationality": "Spain"},
        "away_team": {"country": "Morocco", "nationality": "Morocco"},
        "expected_home_fans": 26000,
        "expected_away_fans": 24000,
    },
    {
        "match_id": "WC2026-SFO-001",
        "city": "San Francisco",
        "venue": "Levi's Stadium",
        "kickoff_utc": datetime(2026, 6, 19, 20, 0),
        "stage": "Group Stage",
        "home_team": {"country": "USA", "nationality": "USA"},
        "away_team": {"country": "Germany", "nationality": "Germany"},
        "expected_home_fans": 35000,
        "expected_away_fans": 21000,
    },
]


def main():
    uri = os.environ["MONGODB_URI"]
    client = MongoClient(uri)
    db = client["fanzone"]
    coll = db["matches"]
    coll.delete_many({})
    coll.insert_many(MATCHES)
    coll.create_index("city")
    coll.create_index("kickoff_utc")
    print(f"Seeded {coll.count_documents({})} matches into fanzone.matches")


if __name__ == "__main__":
    main()
