#!/usr/bin/env python3
"""
Database integration test script for SpeakSharp Core.

Tests:
- Database connection
- User CRUD operations
- SRS card operations
- Error logging
- Session management
- Database functions (get_due_cards, create_card_from_error, etc.)
"""

import uuid
import sys
from datetime import datetime

from app.db import Database, get_db


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message: str):
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"✗ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"  {message}")


def test_connection(db: Database) -> bool:
    """Test database connection."""
    print_header("Database Connection Test")

    try:
        if db.health_check():
            print_success("Database connection successful")
            return True
        else:
            print_error("Database health check failed")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        print_info("\nPlease ensure database is running and environment variables are set:")
        print_info("  DATABASE_URL or SUPABASE_DB_URL")
        print_info("  OR")
        print_info("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return False


def test_user_operations(db: Database, test_user_id: uuid.UUID) -> bool:
    """Test user CRUD operations."""
    print_header("User Operations Test")

    try:
        # Create user
        user = db.create_user(
            user_id=test_user_id,
            level="A1",
            native_language="Spanish",
            goals={"improve_speaking": True, "prepare_for_travel": True},
            interests=["travel", "food", "technology"]
        )
        print_success(f"Created user: {user['user_id']}")
        print_info(f"  Level: {user['level']}")
        print_info(f"  Native Language: {user['native_language']}")
        print_info(f"  Goals: {user['goals']}")
        print_info(f"  Interests: {user['interests']}")

        # Retrieve user
        retrieved = db.get_user(test_user_id)
        if retrieved and retrieved['user_id'] == test_user_id:
            print_success("Retrieved user successfully")
        else:
            print_error("Failed to retrieve user")
            return False

        # Update user level
        updated = db.update_user_level(test_user_id, "A2")
        if updated:
            print_success("Updated user level to A2")
            user = db.get_user(test_user_id)
            print_info(f"  New level: {user['level']}")
        else:
            print_error("Failed to update user level")
            return False

        return True

    except Exception as e:
        print_error(f"User operations failed: {e}")
        return False


def test_srs_operations(db: Database, test_user_id: uuid.UUID) -> tuple[bool, uuid.UUID]:
    """Test SRS card operations."""
    print_header("SRS Operations Test")

    card_id = None

    try:
        # Create SRS card
        card = db.create_srs_card(
            user_id=test_user_id,
            card_type="definition",
            front="What is the past tense of 'go'?",
            back="went",
            level="A1",
            source="lesson",
            difficulty=0.3,
            metadata={"lesson_id": "past_simple_irregular"}
        )
        card_id = card['card_id']
        print_success(f"Created SRS card: {card_id}")
        print_info(f"  Type: {card['card_type']}")
        print_info(f"  Front: {card['front']}")
        print_info(f"  Back: {card['back']}")
        print_info(f"  Next review: {card['next_review_date']}")

        # Create more cards for testing
        for i in range(3):
            db.create_srs_card(
                user_id=test_user_id,
                card_type="cloze",
                front=f"I ___ to the store yesterday. (go) [Test card {i+1}]",
                back="went",
                level="A1"
            )
        print_success("Created 3 additional test cards")

        # Get due cards
        due_cards = db.get_due_cards(test_user_id, limit=10)
        print_success(f"Retrieved {len(due_cards)} due cards")
        for idx, card in enumerate(due_cards[:3], 1):
            print_info(f"  Card {idx}: {card['front'][:50]}...")

        # Update card after review
        db.update_card_after_review(
            card_id=card_id,
            quality=4,  # Good recall
            response_time_ms=3500,
            user_response="went",
            correct=True
        )
        print_success("Recorded card review (quality=4)")

        # Check updated card
        updated_card = db.get_card(card_id)
        print_info(f"  New interval: {updated_card['interval_days']} days")
        print_info(f"  New ease factor: {updated_card['ease_factor']:.2f}")
        print_info(f"  Review count: {updated_card['review_count']}")

        return True, card_id

    except Exception as e:
        print_error(f"SRS operations failed: {e}")
        return False, card_id


def test_error_logging(db: Database, test_user_id: uuid.UUID, session_id: uuid.UUID) -> tuple[bool, uuid.UUID]:
    """Test error logging operations."""
    print_header("Error Logging Test")

    error_id = None

    try:
        # Log error
        error = db.log_error(
            user_id=test_user_id,
            error_type="grammar",
            user_sentence="I go to school yesterday",
            corrected_sentence="I went to school yesterday",
            explanation="Use past tense 'went' for completed actions in the past",
            session_id=session_id,
            source_type="scenario"
        )
        error_id = error['error_id']
        print_success(f"Logged error: {error_id}")
        print_info(f"  Type: {error['error_type']}")
        print_info(f"  User: {error['user_sentence']}")
        print_info(f"  Corrected: {error['corrected_sentence']}")

        # Log more errors
        errors_data = [
            ("vocab", "I want to do a picture", "I want to take a picture",
             "Use 'take a picture' not 'do a picture'"),
            ("grammar", "She don't like coffee", "She doesn't like coffee",
             "Use 'doesn't' with third person singular"),
        ]

        for error_type, user_sent, corrected, explanation in errors_data:
            db.log_error(
                user_id=test_user_id,
                error_type=error_type,
                user_sentence=user_sent,
                corrected_sentence=corrected,
                explanation=explanation,
                session_id=session_id
            )
        print_success(f"Logged {len(errors_data)} additional errors")

        # Get user errors
        user_errors = db.get_user_errors(test_user_id, limit=10)
        print_success(f"Retrieved {len(user_errors)} errors")

        # Get unrecycled errors
        unrecycled = db.get_user_errors(test_user_id, limit=10, unrecycled_only=True)
        print_success(f"Found {len(unrecycled)} unrecycled errors")

        # Create card from error
        if error_id:
            card_id = db.create_card_from_error(error_id)
            print_success(f"Created SRS card from error: {card_id}")

            # Verify error is marked as recycled
            updated_errors = db.get_user_errors(test_user_id, limit=10, unrecycled_only=True)
            print_info(f"  Unrecycled errors after card creation: {len(updated_errors)}")

        return True, error_id

    except Exception as e:
        print_error(f"Error logging failed: {e}")
        return False, error_id


def test_session_operations(db: Database, test_user_id: uuid.UUID) -> tuple[bool, uuid.UUID]:
    """Test session operations."""
    print_header("Session Operations Test")

    session_id = None

    try:
        # Create session
        session = db.create_session(
            user_id=test_user_id,
            session_type="scenario",
            metadata={
                "scenario_name": "café_ordering",
                "difficulty": "A1",
                "timestamp": datetime.now().isoformat()
            }
        )
        session_id = session['session_id']
        print_success(f"Created session: {session_id}")
        print_info(f"  Type: {session['session_type']}")
        print_info(f"  State: {session['state']}")
        print_info(f"  Started: {session['started_at']}")

        # Retrieve session
        retrieved = db.get_session(session_id)
        if retrieved:
            print_success("Retrieved session successfully")
        else:
            print_error("Failed to retrieve session")
            return False, session_id

        # Complete session
        completed = db.complete_session(session_id, duration_seconds=450)
        if completed:
            print_success("Completed session")
            final_session = db.get_session(session_id)
            print_info(f"  Duration: {final_session['duration_seconds']} seconds")
            print_info(f"  State: {final_session['state']}")
            print_info(f"  Completed: {final_session['completed_at']}")
        else:
            print_error("Failed to complete session")
            return False, session_id

        return True, session_id

    except Exception as e:
        print_error(f"Session operations failed: {e}")
        return False, session_id


def test_skill_operations(db: Database, test_user_id: uuid.UUID) -> bool:
    """Test skill graph operations."""
    print_header("Skill Graph Operations Test")

    try:
        # Update skill nodes
        skills = [
            ("grammar.past_simple", True, 10.0),
            ("vocab.travel", True, 8.0),
            ("grammar.articles", False, -5.0),
            ("pronunciation.th_sound", False, -3.0),
            ("fluency.hesitations", True, 5.0),
        ]

        for skill_key, success, delta in skills:
            db.update_skill_node(
                user_id=test_user_id,
                skill_key=skill_key,
                success=success,
                score_delta=delta
            )
        print_success(f"Updated {len(skills)} skill nodes")

        # Practice the same skill multiple times
        for _ in range(3):
            db.update_skill_node(
                user_id=test_user_id,
                skill_key="grammar.articles",
                success=True,
                score_delta=3.0
            )
        print_success("Practiced 'grammar.articles' 3 more times")

        # Get weakest skills
        weakest = db.get_weakest_skills(test_user_id, limit=5)
        print_success(f"Retrieved {len(weakest)} weakest skills:")
        for idx, skill in enumerate(weakest, 1):
            print_info(
                f"  {idx}. {skill['skill_key']}: "
                f"mastery={skill['mastery_score']:.1f}, "
                f"errors={skill['error_count']}"
            )

        return True

    except Exception as e:
        print_error(f"Skill operations failed: {e}")
        return False


def cleanup(db: Database, test_user_id: uuid.UUID):
    """Clean up test data."""
    print_header("Cleanup")

    try:
        # Note: In a real scenario, you'd want CASCADE deletes in your schema
        # For now, we'll just note that test data remains in the database
        print_info("Test data created with user_id: " + str(test_user_id))
        print_info("You may want to manually clean up test data from your database")
        print_info("or implement a cleanup function with proper CASCADE handling")

    except Exception as e:
        print_error(f"Cleanup warning: {e}")


def main():
    """Run all database integration tests."""
    print("\n" + "=" * 60)
    print("  SpeakSharp Database Integration Test Suite")
    print("=" * 60)

    # Initialize database
    db = get_db()

    # Test connection
    if not test_connection(db):
        print_error("\nDatabase connection failed. Aborting tests.")
        sys.exit(1)

    # Generate test user ID
    test_user_id = uuid.uuid4()
    print_info(f"\nTest User ID: {test_user_id}")

    # Run tests
    all_passed = True

    # Test users
    if not test_user_operations(db, test_user_id):
        all_passed = False

    # Test sessions (needed for error logging)
    session_success, session_id = test_session_operations(db, test_user_id)
    if not session_success:
        all_passed = False
        session_id = None

    # Test SRS
    srs_success, card_id = test_srs_operations(db, test_user_id)
    if not srs_success:
        all_passed = False

    # Test error logging
    if session_id:
        error_success, error_id = test_error_logging(db, test_user_id, session_id)
        if not error_success:
            all_passed = False

    # Test skills
    if not test_skill_operations(db, test_user_id):
        all_passed = False

    # Summary
    print_header("Test Summary")

    if all_passed:
        print_success("All tests passed!")
        print_info("\nDatabase integration is working correctly.")
        cleanup(db, test_user_id)
        sys.exit(0)
    else:
        print_error("Some tests failed!")
        print_info("\nPlease review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
