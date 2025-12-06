"""Mark all user profiles as onboarding complete"""
import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("ERROR: DATABASE_URL not set")
    exit(1)

print(f"Connecting to database...")

try:
    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Update all user profiles
            cur.execute("""
                UPDATE public.user_profile
                SET onboarding_completed = true
                WHERE onboarding_completed = false
                RETURNING user_id, onboarding_completed
            """)

            results = cur.fetchall()
            conn.commit()

            print(f"✅ Updated {len(results)} user profiles")
            for row in results:
                print(f"   - User {row['user_id']}: onboarding_completed = {row['onboarding_completed']}")

            if len(results) == 0:
                print("ℹ️  No users needed updating (all already complete)")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
