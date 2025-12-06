#!/usr/bin/env python3
"""
Seed skill definitions into the database
Usage: python seed_skills.py
"""

import os
import sys
import psycopg

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.skills import ALL_SKILLS, SKILL_COUNT

def main():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    print(f"Seeding {SKILL_COUNT} skills into database...")

    try:
        with psycopg.connect(database_url) as conn:
            print("Connected to database")

            with conn.cursor() as cur:
                # Clear existing skills
                cur.execute("DELETE FROM skill_definitions;")
                print("Cleared existing skill definitions")

                # Insert all skills
                inserted = 0
                for skill in ALL_SKILLS:
                    cur.execute("""
                        INSERT INTO skill_definitions
                        (skill_key, domain, category, name_en, description_en, cefr_level, difficulty)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (skill_key) DO UPDATE SET
                            domain = EXCLUDED.domain,
                            category = EXCLUDED.category,
                            name_en = EXCLUDED.name_en,
                            description_en = EXCLUDED.description_en,
                            cefr_level = EXCLUDED.cefr_level,
                            difficulty = EXCLUDED.difficulty
                    """, (
                        skill.skill_key,
                        skill.domain,
                        skill.category,
                        skill.name_en,
                        skill.description_en,
                        skill.cefr_level,
                        skill.difficulty
                    ))
                    inserted += 1

                conn.commit()
                print(f"Inserted {inserted} skills")

                # Verify by domain
                cur.execute("""
                    SELECT domain, COUNT(*) as count
                    FROM skill_definitions
                    GROUP BY domain
                    ORDER BY domain
                """)
                print("\nSkills by domain:")
                for row in cur.fetchall():
                    print(f"  {row[0]}: {row[1]}")

                # Verify by level
                cur.execute("""
                    SELECT cefr_level, COUNT(*) as count
                    FROM skill_definitions
                    GROUP BY cefr_level
                    ORDER BY cefr_level
                """)
                print("\nSkills by CEFR level:")
                for row in cur.fetchall():
                    print(f"  {row[0]}: {row[1]}")

                print("\nSkill seeding complete!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
