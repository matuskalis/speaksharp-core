#!/usr/bin/env python3
"""
Seed initial achievements into the database.
Usage: python seed_achievements.py
"""

import os
import sys
import psycopg
from psycopg.rows import dict_row

# Initial achievement definitions
ACHIEVEMENTS = [
    {
        "achievement_key": "first_lesson",
        "title": "First Steps",
        "description": "Complete your first lesson",
        "category": "milestone",
        "points": 10,
        "tier": "bronze"
    },
    {
        "achievement_key": "first_error_fixed",
        "title": "Learning from Mistakes",
        "description": "Fix your first grammar error",
        "category": "milestone",
        "points": 5,
        "tier": "bronze"
    },
    {
        "achievement_key": "5_day_streak",
        "title": "Consistent Learner",
        "description": "Maintain a 5-day learning streak",
        "category": "streak",
        "points": 50,
        "tier": "bronze"
    },
    {
        "achievement_key": "10_day_streak",
        "title": "Dedicated Student",
        "description": "Maintain a 10-day learning streak",
        "category": "streak",
        "points": 100,
        "tier": "silver"
    },
    {
        "achievement_key": "30_day_streak",
        "title": "Streak Master",
        "description": "Maintain a 30-day learning streak",
        "category": "streak",
        "points": 300,
        "tier": "gold"
    },
    {
        "achievement_key": "100_errors_fixed",
        "title": "Error Eliminator",
        "description": "Fix 100 grammar errors",
        "category": "mastery",
        "points": 200,
        "tier": "silver"
    },
    {
        "achievement_key": "500_errors_fixed",
        "title": "Grammar Guardian",
        "description": "Fix 500 grammar errors",
        "category": "mastery",
        "points": 500,
        "tier": "gold"
    },
    {
        "achievement_key": "10_lessons_completed",
        "title": "Lesson Explorer",
        "description": "Complete 10 lessons",
        "category": "milestone",
        "points": 100,
        "tier": "bronze"
    },
    {
        "achievement_key": "50_lessons_completed",
        "title": "Lesson Master",
        "description": "Complete 50 lessons",
        "category": "milestone",
        "points": 500,
        "tier": "silver"
    },
    {
        "achievement_key": "100_reviews_completed",
        "title": "Review Champion",
        "description": "Complete 100 SRS reviews",
        "category": "milestone",
        "points": 200,
        "tier": "silver"
    },
    {
        "achievement_key": "perfect_week",
        "title": "Perfect Week",
        "description": "Meet your daily goals for 7 consecutive days",
        "category": "milestone",
        "points": 150,
        "tier": "silver"
    },
    {
        "achievement_key": "first_referral",
        "title": "Friend Bringer",
        "description": "Refer your first friend to SpeakSharp",
        "category": "social",
        "points": 100,
        "tier": "bronze"
    },
    {
        "achievement_key": "5_referrals",
        "title": "Community Builder",
        "description": "Refer 5 friends to SpeakSharp",
        "category": "social",
        "points": 500,
        "tier": "gold"
    },
    {
        "achievement_key": "level_up_b1",
        "title": "Intermediate Speaker",
        "description": "Reach B1 (Intermediate) level",
        "category": "milestone",
        "points": 300,
        "tier": "silver"
    },
    {
        "achievement_key": "level_up_b2",
        "title": "Upper-Intermediate Speaker",
        "description": "Reach B2 (Upper-Intermediate) level",
        "category": "milestone",
        "points": 500,
        "tier": "gold"
    },
    {
        "achievement_key": "level_up_c1",
        "title": "Advanced Speaker",
        "description": "Reach C1 (Advanced) level",
        "category": "milestone",
        "points": 1000,
        "tier": "platinum"
    },
    # XP Milestones
    {
        "achievement_key": "xp_100",
        "title": "XP Collector",
        "description": "Earn 100 total XP",
        "category": "milestone",
        "points": 25,
        "tier": "bronze"
    },
    {
        "achievement_key": "xp_500",
        "title": "XP Hunter",
        "description": "Earn 500 total XP",
        "category": "milestone",
        "points": 50,
        "tier": "bronze"
    },
    {
        "achievement_key": "xp_1000",
        "title": "XP Champion",
        "description": "Earn 1,000 total XP",
        "category": "milestone",
        "points": 100,
        "tier": "silver"
    },
    {
        "achievement_key": "xp_5000",
        "title": "XP Legend",
        "description": "Earn 5,000 total XP",
        "category": "milestone",
        "points": 250,
        "tier": "gold"
    },
    {
        "achievement_key": "xp_10000",
        "title": "XP Master",
        "description": "Earn 10,000 total XP",
        "category": "milestone",
        "points": 500,
        "tier": "platinum"
    },
    # Voice Practice
    {
        "achievement_key": "first_voice",
        "title": "Finding Your Voice",
        "description": "Complete your first voice practice session",
        "category": "voice",
        "points": 20,
        "tier": "bronze"
    },
    {
        "achievement_key": "voice_5",
        "title": "Voice Explorer",
        "description": "Complete 5 voice practice sessions",
        "category": "voice",
        "points": 50,
        "tier": "bronze"
    },
    {
        "achievement_key": "voice_25",
        "title": "Voice Enthusiast",
        "description": "Complete 25 voice practice sessions",
        "category": "voice",
        "points": 150,
        "tier": "silver"
    },
    {
        "achievement_key": "voice_100",
        "title": "Voice Master",
        "description": "Complete 100 voice practice sessions",
        "category": "voice",
        "points": 400,
        "tier": "gold"
    },
    # Pronunciation
    {
        "achievement_key": "pronunciation_80",
        "title": "Clear Speaker",
        "description": "Score 80% or higher on pronunciation",
        "category": "pronunciation",
        "points": 50,
        "tier": "bronze"
    },
    {
        "achievement_key": "pronunciation_90",
        "title": "Pronunciation Pro",
        "description": "Score 90% or higher on pronunciation",
        "category": "pronunciation",
        "points": 100,
        "tier": "silver"
    },
    {
        "achievement_key": "pronunciation_95",
        "title": "Native-Like",
        "description": "Score 95% or higher on pronunciation",
        "category": "pronunciation",
        "points": 200,
        "tier": "gold"
    },
    # Perfect Scores
    {
        "achievement_key": "perfect_lesson",
        "title": "Perfectionist",
        "description": "Complete a lesson with 100% accuracy",
        "category": "mastery",
        "points": 50,
        "tier": "bronze"
    },
    {
        "achievement_key": "perfect_5",
        "title": "Flawless Five",
        "description": "Complete 5 lessons with 100% accuracy",
        "category": "mastery",
        "points": 150,
        "tier": "silver"
    },
    {
        "achievement_key": "perfect_20",
        "title": "Perfect Record",
        "description": "Complete 20 lessons with 100% accuracy",
        "category": "mastery",
        "points": 400,
        "tier": "gold"
    },
    # Speed
    {
        "achievement_key": "speed_demon",
        "title": "Speed Demon",
        "description": "Complete a lesson in under 2 minutes",
        "category": "special",
        "points": 30,
        "tier": "bronze"
    },
    # Comeback
    {
        "achievement_key": "comeback_kid",
        "title": "Comeback Kid",
        "description": "Return after 7+ days away",
        "category": "special",
        "points": 50,
        "tier": "bronze"
    },
    # Learning Path
    {
        "achievement_key": "path_started",
        "title": "Journey Begins",
        "description": "Start your learning path",
        "category": "milestone",
        "points": 15,
        "tier": "bronze"
    },
    {
        "achievement_key": "unit_complete",
        "title": "Unit Master",
        "description": "Complete your first unit",
        "category": "milestone",
        "points": 75,
        "tier": "bronze"
    },
    {
        "achievement_key": "path_complete",
        "title": "Path Pioneer",
        "description": "Complete an entire learning path",
        "category": "milestone",
        "points": 500,
        "tier": "gold"
    }
]

def main():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    print("🌱 Seeding achievements into database...\n")

    try:
        with psycopg.connect(database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Check how many achievements already exist
                cur.execute("SELECT COUNT(*) as count FROM achievements")
                existing_count = cur.fetchone()['count']

                if existing_count > 0:
                    print(f"⚠️  Database already has {existing_count} achievements.")
                    print("   This script will skip duplicates and add new ones.\n")

                # Insert each achievement
                inserted = 0
                skipped = 0

                for ach in ACHIEVEMENTS:
                    try:
                        cur.execute("""
                            INSERT INTO achievements (
                                achievement_key, title, description,
                                category, points, tier
                            )
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (achievement_key) DO NOTHING
                            RETURNING achievement_id
                        """, (
                            ach["achievement_key"],
                            ach["title"],
                            ach["description"],
                            ach["category"],
                            ach["points"],
                            ach["tier"]
                        ))

                        result = cur.fetchone()
                        if result:
                            inserted += 1
                            tier_emoji = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}
                            emoji = tier_emoji.get(ach["tier"], "🏆")
                            print(f"   {emoji} {ach['title']} ({ach['points']} pts)")
                        else:
                            skipped += 1

                    except Exception as e:
                        print(f"   ❌ Failed to insert {ach['achievement_key']}: {e}")

                conn.commit()

                print(f"\n✅ Seeding complete!")
                print(f"   Inserted: {inserted} new achievements")
                print(f"   Skipped:  {skipped} existing achievements")
                print(f"   Total:    {inserted + skipped + (existing_count - skipped)} achievements in database\n")

                # Show breakdown by category
                cur.execute("""
                    SELECT category, COUNT(*) as count
                    FROM achievements
                    GROUP BY category
                    ORDER BY count DESC
                """)

                print("📊 Achievements by category:")
                for row in cur.fetchall():
                    print(f"   {row['category']}: {row['count']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
