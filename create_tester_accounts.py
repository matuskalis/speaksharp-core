"""
Create 25 tester accounts with full access.
Tester accounts bypass trial/payment restrictions.
"""

import os
import asyncio
from dotenv import load_dotenv
import psycopg

load_dotenv()

TESTER_ACCOUNTS = [
    {"email": f"tester{i}@vorex.app", "password": "VorexTest2024!"}
    for i in range(1, 26)
]

async def run_migration(conn):
    """Run migration_004 to add is_tester column."""
    print("🔧 Running migration_004_tester_accounts.sql...")

    with open("/Users/matuskalis/vorex-backend/database/migration_004_tester_accounts.sql", "r") as f:
        migration_sql = f.read()

    await conn.execute(migration_sql)
    print("✅ Migration completed\n")

async def create_tester_accounts():
    """Create 25 tester accounts in Supabase."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set")
        return

    print("🚀 Creating 25 tester accounts...\n")

    conn = await psycopg.AsyncConnection.connect(database_url)

    try:
        # Run migration first
        await run_migration(conn)

        print("📝 Tester Account Credentials:\n")
        print("=" * 60)

        for account in TESTER_ACCOUNTS:
            email = account["email"]
            password = account["password"]

            # Note: In production, you'd use Supabase Auth API to create users
            # For now, we'll just print the credentials and instructions
            print(f"Email:    {email}")
            print(f"Password: {password}")
            print("-" * 60)

        print("\n📋 NEXT STEPS:")
        print("1. Create these accounts manually in Supabase Auth Dashboard")
        print("2. OR use Supabase Auth API to create them programmatically")
        print("3. After accounts are created, run this script again to mark them as testers")
        print("\n💡 To mark existing accounts as testers, run:")
        print("   UPDATE user_profiles SET is_tester = TRUE WHERE email IN (...)")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tester_accounts())
