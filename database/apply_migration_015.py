#!/usr/bin/env python3
"""
Apply Migration 015: Session Analytics

Creates the session_results table for comprehensive session tracking.
"""

import os
import sys
import psycopg

# Add parent directory to path to import db module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import DatabaseConfig

def apply_migration():
    """Apply migration 015."""
    config = DatabaseConfig()

    print("Connecting to database...")
    conn = psycopg.connect(config.get_connection_string())

    try:
        print("Reading migration file...")
        migration_path = os.path.join(os.path.dirname(__file__), 'migration_015_session_analytics.sql')
        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        print("Applying migration 015...")
        with conn.cursor() as cur:
            cur.execute(migration_sql)

        conn.commit()
        print("Migration 015 applied successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error applying migration: {e}")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    apply_migration()
