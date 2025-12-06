#!/usr/bin/env python3
"""
Apply Migration 007: Notifications System
"""

import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def apply_migration():
    """Apply the notifications migration."""
    connection_string = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

    if not connection_string:
        print("Error: DATABASE_URL or SUPABASE_DB_URL not set")
        return False

    try:
        print("Connecting to database...")
        conn = psycopg.connect(connection_string)

        print("Reading migration file...")
        with open("database/migration_007_notifications.sql", "r") as f:
            migration_sql = f.read()

        print("Applying migration 007...")
        with conn.cursor() as cur:
            cur.execute(migration_sql)

        conn.commit()
        print("\n✅ Migration 007 applied successfully!")
        print("Notifications system is now ready to use.")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ Error applying migration: {e}")
        return False

if __name__ == "__main__":
    apply_migration()
