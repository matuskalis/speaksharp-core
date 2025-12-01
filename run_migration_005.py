"""
Run migration 005 to add daily_time_goal column.
"""

import os
import asyncio
from dotenv import load_dotenv
import psycopg

load_dotenv()

async def run_migration():
    """Run migration_005_daily_time_goal.sql"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set")
        return

    print("🔧 Running migration_005_daily_time_goal.sql...")

    conn = await psycopg.AsyncConnection.connect(database_url)

    try:
        with open("database/migration_005_daily_time_goal.sql", "r") as f:
            migration_sql = f.read()

        await conn.execute(migration_sql)
        await conn.commit()
        print("✅ Migration completed successfully\n")
        print("✓ Added daily_time_goal column to user_profiles table")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
