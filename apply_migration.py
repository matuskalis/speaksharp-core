#!/usr/bin/env python3
"""
Apply migration to Railway PostgreSQL
Usage: python apply_migration.py
"""

import os
import sys
import psycopg

def main():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    migration_path = os.path.join(os.path.dirname(__file__), "database", "migration_001_comprehensive_tracking.sql")

    if not os.path.exists(migration_path):
        print(f"❌ ERROR: Migration file not found at {migration_path}")
        sys.exit(1)

    print(f"📖 Reading migration from {migration_path}...")
    with open(migration_path, "r") as f:
        migration_sql = f.read()

    print(f"📊 Migration size: {len(migration_sql)} characters\n")

    try:
        with psycopg.connect(database_url) as conn:
            print("✅ Connected successfully!\n")

            with conn.cursor() as cur:
                print("🚀 Applying comprehensive tracking migration...")
                print("   This adds 13 new tables and enhances user_profiles\n")

                cur.execute(migration_sql)
                conn.commit()

                print("✅ Migration applied successfully!\n")

                # Show what was added
                print("📋 New data you're now collecting:\n")

                additions = [
                    ("👤 User Profile", "Full name, age, country, occupation, timezone, learning goals"),
                    ("📊 Session Analytics", "Device type, OS, browser, IP, location, screen resolution"),
                    ("🔥 Streaks & Goals", "Daily streaks, weekly goals, freeze days, activity tracking"),
                    ("🏆 Achievements", "Gamification badges, progress tracking, point system"),
                    ("🎯 Daily Goals", "Study time, lessons, reviews, drills with completion tracking"),
                    ("💰 Subscriptions", "Tier, billing cycle, Stripe integration, trial tracking"),
                    ("👥 Referrals", "Referral codes, conversions, rewards"),
                    ("⚡ Feature Usage", "Which features used, how often, success rates, duration"),
                    ("💬 Feedback", "Bug reports, feature requests, ratings, support tickets"),
                    ("🧪 A/B Testing", "Experiment assignments, conversions, variant tracking"),
                    ("🔔 Notifications", "Email/push preferences, reminder times"),
                    ("📈 Analytics Views", "Pre-built queries for user engagement, DAU, feature popularity")
                ]

                for category, details in additions:
                    print(f"   {category}")
                    print(f"      └─ {details}\n")

                # Verify new tables
                cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename;
                """)

                tables = cur.fetchall()
                print(f"\n✅ Total tables in database: {len(tables)}\n")

                print("🎉 Comprehensive tracking is now ACTIVE!\n")
                print("Next steps:")
                print("   1. Update backend API to collect new fields")
                print("   2. Update frontend forms to capture user data")
                print("   3. Build analytics dashboard")
                print("   4. Set up automated reports")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
