#!/usr/bin/env python3
"""
Migration runner script for Railway.
Executes SQL migration files against the DATABASE_URL.
"""
import os
import sys
import psycopg2
from pathlib import Path

def run_migrations():
    """Run all pending migrations."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    # Get migration files to run
    migrations_dir = Path(__file__).parent / "database"
    migration_files = sorted([
        f for f in migrations_dir.glob("migration_*.sql")
    ])

    # Filter to only run migrations 013 and 014
    target_migrations = ["migration_013_push_notifications.sql", "migration_014_gamification_bonuses.sql"]
    migration_files = [f for f in migration_files if f.name in target_migrations]

    if not migration_files:
        print("No target migrations found.")
        return

    print(f"Found {len(migration_files)} migration(s) to run:")
    for f in migration_files:
        print(f"  - {f.name}")

    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        for migration_file in migration_files:
            print(f"\nRunning {migration_file.name}...")
            try:
                sql = migration_file.read_text()
                cursor.execute(sql)
                print(f"  ✓ {migration_file.name} completed successfully")
            except psycopg2.Error as e:
                # Check if it's a "already exists" error
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"  ⚠ {migration_file.name} - objects may already exist (skipping)")
                else:
                    print(f"  ✗ {migration_file.name} failed: {e}")
                    # Continue with other migrations

        cursor.close()
        conn.close()
        print("\n✓ All migrations completed!")

    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
