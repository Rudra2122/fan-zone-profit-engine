"""Seed the `matches` collection — 5 World Cup 2026 fixtures.

Idempotent: clears and re-inserts. Run: python seed_data/seed_matches.py
"""

from _db import get_db

MATCHES = [
    {
        "city": "Dallas",
        "fixture": "USA vs Mexico",
        "venue": "AT&T Stadium",
        "date": "2026-06-15",
        "home_team": "USA",
        "away_team": "Mexico",
        "home_team_nationality": "USA",
        "away_team_nationality": "Mexico",
        "home_fans": 48000,
        "away_fans": 32000,
    },
    {
        "city": "Los Angeles",
        "fixture": "Brazil vs Argentina",
        "venue": "SoFi Stadium",
        "date": "2026-06-18",
        "home_team": "Brazil",
        "away_team": "Argentina",
        "home_team_nationality": "Brazil",
        "away_team_nationality": "Argentina",
        "home_fans": 35000,
        "away_fans": 35000,
    },
    {
        "city": "New York",
        "fixture": "England vs Netherlands",
        "venue": "MetLife Stadium",
        "date": "2026-06-20",
        "home_team": "England",
        "away_team": "Netherlands",
        "home_team_nationality": "England",
        "away_team_nationality": "Netherlands",
        "home_fans": 41000,
        "away_fans": 28000,
    },
    {
        "city": "Miami",
        "fixture": "Mexico vs Colombia",
        "venue": "Hard Rock Stadium",
        "date": "2026-06-22",
        "home_team": "Mexico",
        "away_team": "Colombia",
        "home_team_nationality": "Mexico",
        "away_team_nationality": "Colombia",
        "home_fans": 39000,
        "away_fans": 26000,
    },
    {
        "city": "San Francisco",
        "fixture": "Japan vs Germany",
        "venue": "Levi's Stadium",
        "date": "2026-06-24",
        "home_team": "Japan",
        "away_team": "Germany",
        "home_team_nationality": "Japan",
        "away_team_nationality": "Germany",
        "home_fans": 30000,
        "away_fans": 31000,
    },
]


def main():
    db = get_db()
    db.matches.delete_many({})
    db.matches.insert_many([dict(m) for m in MATCHES])
    print(f"Seeded {len(MATCHES)} matches into fanzone.matches")


if __name__ == "__main__":
    main()
