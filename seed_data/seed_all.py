"""Run all three seed scripts in order. Run: python seed_data/seed_all.py"""

import seed_matches
import seed_fan_profiles
import seed_tenant_catalog

if __name__ == "__main__":
    seed_matches.main()
    seed_fan_profiles.main()
    seed_tenant_catalog.main()
    print("All collections seeded.")
