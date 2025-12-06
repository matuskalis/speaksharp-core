"""
Content Seeder Script

Seeds all existing content (lessons, scenarios, drills, phrases) into the database.
Run this once to populate the content_library table.
"""

import os
import json
import psycopg2
from psycopg2.extras import Json, execute_values
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import existing content
from app.lessons import LESSON_LIBRARY
from app.scenarios import SCENARIO_TEMPLATES
from app.drills import MONOLOGUE_PROMPTS, JOURNAL_PROMPTS
from app.data.practice_phrases import PRACTICE_PHRASES


def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL must be set")
    return psycopg2.connect(database_url)


def check_exists(cursor, content_type: str, identifier_key: str, identifier_value: str) -> bool:
    """Check if content already exists."""
    cursor.execute("""
        SELECT content_id FROM content_library
        WHERE content_type = %s AND metadata->>%s = %s
    """, (content_type, identifier_key, identifier_value))
    return cursor.fetchone() is not None


def check_exists_by_title(cursor, content_type: str, title: str) -> bool:
    """Check if content already exists by title."""
    cursor.execute("""
        SELECT content_id FROM content_library
        WHERE content_type = %s AND title = %s
    """, (content_type, title))
    return cursor.fetchone() is not None


def seed_lessons(cursor):
    """Seed grammar lessons into content_library."""
    print("\n📚 Seeding Lessons...")
    added = 0

    for lesson_id, lesson in LESSON_LIBRARY.items():
        if check_exists(cursor, "lesson", "lesson_id", lesson_id):
            print(f"  ⏭️  Lesson '{lesson.title}' already exists, skipping")
            continue

        content_data = {
            "lesson_id": lesson.lesson_id,
            "context": lesson.context,
            "target_language": lesson.target_language,
            "explanation": lesson.explanation,
            "examples": lesson.examples,
            "controlled_practice": [
                {
                    "task_type": task.task_type,
                    "prompt": task.prompt,
                    "expected_pattern": task.expected_pattern,
                    "example_answer": task.example_answer
                }
                for task in lesson.controlled_practice
            ],
            "freer_production": {
                "task_type": lesson.freer_production.task_type,
                "prompt": lesson.freer_production.prompt,
                "example_answer": lesson.freer_production.example_answer
            },
            "summary": lesson.summary
        }

        metadata = {
            "duration_minutes": lesson.duration_minutes,
            "lesson_id": lesson.lesson_id
        }

        cursor.execute("""
            INSERT INTO content_library
            (content_type, title, level_min, level_max, skill_targets, content_data, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "lesson",
            lesson.title,
            lesson.level,
            lesson.level,
            Json(lesson.skill_targets),
            Json(content_data),
            Json(metadata)
        ))
        print(f"  ✅ Added: {lesson.title} ({lesson.level})")
        added += 1

    print(f"  Total lessons added: {added}/{len(LESSON_LIBRARY)}")


def seed_scenarios(cursor):
    """Seed role-play scenarios into content_library."""
    print("\n🎭 Seeding Scenarios...")
    added = 0

    for scenario_id, scenario in SCENARIO_TEMPLATES.items():
        if check_exists(cursor, "scenario", "scenario_id", scenario_id):
            print(f"  ⏭️  Scenario '{scenario.title}' already exists, skipping")
            continue

        content_data = {
            "scenario_id": scenario.scenario_id,
            "situation_description": scenario.situation_description,
            "user_goal": scenario.user_goal,
            "task": scenario.task,
            "success_criteria": scenario.success_criteria,
            "difficulty_tags": scenario.difficulty_tags,
            "user_variables": scenario.user_variables
        }

        metadata = {
            "scenario_id": scenario.scenario_id
        }

        cursor.execute("""
            INSERT INTO content_library
            (content_type, title, level_min, level_max, skill_targets, content_data, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "scenario",
            scenario.title,
            scenario.level_min,
            scenario.level_max,
            Json(scenario.difficulty_tags),
            Json(content_data),
            Json(metadata)
        ))
        print(f"  ✅ Added: {scenario.title} ({scenario.level_min}-{scenario.level_max})")
        added += 1

    print(f"  Total scenarios added: {added}/{len(SCENARIO_TEMPLATES)}")


def seed_monologue_prompts(cursor):
    """Seed monologue prompts into content_library."""
    print("\n🎤 Seeding Monologue Prompts...")
    added = 0

    for prompt_id, prompt in MONOLOGUE_PROMPTS.items():
        if check_exists(cursor, "monologue", "prompt_id", prompt_id):
            print(f"  ⏭️  Monologue '{prompt_id}' already exists, skipping")
            continue

        content_data = {
            "prompt_id": prompt.prompt_id,
            "text": prompt.text,
            "category": prompt.category,
            "time_limit_seconds": prompt.time_limit_seconds
        }

        metadata = {
            "prompt_id": prompt.prompt_id,
            "category": prompt.category
        }

        cursor.execute("""
            INSERT INTO content_library
            (content_type, title, level_min, level_max, skill_targets, content_data, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "monologue",
            f"Monologue: {prompt.text[:50]}...",
            prompt.level,
            prompt.level,
            Json(["speaking", "fluency", prompt.category]),
            Json(content_data),
            Json(metadata)
        ))
        print(f"  ✅ Added: {prompt_id} ({prompt.level})")
        added += 1

    print(f"  Total monologue prompts added: {added}/{len(MONOLOGUE_PROMPTS)}")


def seed_journal_prompts(cursor):
    """Seed journal prompts into content_library."""
    print("\n✍️  Seeding Journal Prompts...")
    added = 0

    for prompt_id, prompt in JOURNAL_PROMPTS.items():
        if check_exists(cursor, "journal", "prompt_id", prompt_id):
            print(f"  ⏭️  Journal '{prompt_id}' already exists, skipping")
            continue

        content_data = {
            "prompt_id": prompt.prompt_id,
            "text": prompt.text,
            "category": prompt.category,
            "min_words": prompt.min_words
        }

        metadata = {
            "prompt_id": prompt.prompt_id,
            "category": prompt.category
        }

        cursor.execute("""
            INSERT INTO content_library
            (content_type, title, level_min, level_max, skill_targets, content_data, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "journal",
            f"Journal: {prompt.text[:50]}...",
            prompt.level,
            prompt.level,
            Json(["writing", prompt.category]),
            Json(content_data),
            Json(metadata)
        ))
        print(f"  ✅ Added: {prompt_id} ({prompt.level})")
        added += 1

    print(f"  Total journal prompts added: {added}/{len(JOURNAL_PROMPTS)}")


def seed_practice_phrases(cursor):
    """Seed pronunciation practice phrases into content_library."""
    print("\n🗣️  Seeding Practice Phrases...")
    added = 0

    for i, phrase in enumerate(PRACTICE_PHRASES):
        if check_exists_by_title(cursor, "pronunciation_phrase", phrase["text"]):
            print(f"  ⏭️  Phrase '{phrase['text'][:30]}...' already exists, skipping")
            continue

        content_data = {
            "text": phrase["text"],
            "phonemes": phrase["phonemes"]
        }

        metadata = {
            "phrase_index": i,
            "phonemes": phrase["phonemes"]
        }

        cursor.execute("""
            INSERT INTO content_library
            (content_type, title, level_min, level_max, skill_targets, content_data, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "pronunciation_phrase",
            phrase["text"],
            "A1",
            "C2",
            Json(["pronunciation"] + phrase["phonemes"]),
            Json(content_data),
            Json(metadata)
        ))
        print(f"  ✅ Added: {phrase['text'][:40]}...")
        added += 1

    print(f"  Total phrases added: {added}/{len(PRACTICE_PHRASES)}")


def get_content_counts(cursor):
    """Get counts by content type."""
    counts = {}
    for content_type in ["lesson", "scenario", "monologue", "journal", "pronunciation_phrase"]:
        cursor.execute("""
            SELECT COUNT(*) FROM content_library WHERE content_type = %s
        """, (content_type,))
        counts[content_type] = cursor.fetchone()[0]
    return counts


def main():
    """Main function to seed all content."""
    print("=" * 60)
    print("🌱 CONTENT SEEDER")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")

    # Get database connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return

    # Seed all content
    try:
        seed_lessons(cursor)
        seed_scenarios(cursor)
        seed_monologue_prompts(cursor)
        seed_journal_prompts(cursor)
        seed_practice_phrases(cursor)

        # Commit all changes
        conn.commit()

        print("\n" + "=" * 60)
        print("✅ CONTENT SEEDING COMPLETE!")
        print("=" * 60)

        # Summary
        counts = get_content_counts(cursor)
        print(f"\n📊 Content Summary:")
        total = 0
        for content_type, count in counts.items():
            print(f"  - {content_type}: {count}")
            total += count
        print(f"\n  Total content items: {total}")

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
