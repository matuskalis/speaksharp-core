"""Quick script to mark onboarding as complete for testing"""
import os
import psycopg

def update_onboarding():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return

    print(f"Connecting to database...")

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Get the most recent user from auth.users (Supabase)
                cur.execute("SELECT id FROM auth.users ORDER BY created_at DESC LIMIT 1")
                result = cur.fetchone()

                if result:
                    user_id = result[0]
                    print(f"Found user: {user_id}")

                    # Update onboarding_completed in public schema
                    cur.execute(
                        "UPDATE public.user_profile SET onboarding_completed = true WHERE user_id = %s",
                        (user_id,)
                    )
                    conn.commit()
                    print(f"✅ Onboarding marked complete for user {user_id}")

                    # Verify update
                    cur.execute(
                        "SELECT onboarding_completed FROM public.user_profile WHERE user_id = %s",
                        (user_id,)
                    )
                    verification = cur.fetchone()
                    if verification:
                        print(f"Verification: onboarding_completed = {verification[0]}")
                else:
                    print("No users found in database")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_onboarding()
