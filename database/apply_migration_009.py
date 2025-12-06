#!/usr/bin/env python3
"""
Apply migration 009: Skill Definitions for Mastery Engine
Usage: python database/apply_migration_009.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg

def main():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    migration_path = os.path.join(os.path.dirname(__file__), "migration_009_skill_definitions.sql")

    if not os.path.exists(migration_path):
        print(f"ERROR: Migration file not found at {migration_path}")
        sys.exit(1)

    print(f"Reading migration from {migration_path}...")
    with open(migration_path, "r") as f:
        migration_sql = f.read()

    try:
        with psycopg.connect(database_url) as conn:
            print("Connected to database")

            with conn.cursor() as cur:
                print("Applying skill definitions migration...")
                cur.execute(migration_sql)
                conn.commit()
                print("Migration applied successfully!")

                # Verify
                cur.execute("SELECT COUNT(*) FROM skill_definitions;")
                count = cur.fetchone()[0]
                print(f"Skill definitions table has {count} rows")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
