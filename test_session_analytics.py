#!/usr/bin/env python3
"""
Test script for Session Analytics API endpoints.

This script demonstrates how to use the session analytics endpoints
and provides example test cases.
"""

import uuid
import json
from datetime import datetime

# Example test data
SAMPLE_SESSION_RESULT = {
    "session_type": "conversation",
    "duration_seconds": 420,
    "words_spoken": 180,
    "pronunciation_score": 88.0,
    "fluency_score": 82.5,
    "grammar_score": 85.0,
    "topics": ["restaurant", "ordering food", "dietary restrictions"],
    "vocabulary_learned": ["allergic", "vegetarian", "spicy", "recommend"],
    "areas_to_improve": ["articles (a/an/the)", "polite requests"],
    "metadata": {
        "scenario_id": "restaurant-ordering",
        "ai_tutor_mode": "patient",
        "user_level": "B1"
    }
}

SAMPLE_PRONUNCIATION_SESSION = {
    "session_type": "pronunciation",
    "duration_seconds": 180,
    "words_spoken": 50,
    "pronunciation_score": 75.5,
    "fluency_score": 70.0,
    "grammar_score": 80.0,
    "topics": ["th sounds", "r sounds"],
    "vocabulary_learned": ["through", "three", "think", "brother"],
    "areas_to_improve": ["th sound pronunciation", "word stress"],
    "metadata": {
        "focus_phoneme": "th",
        "difficulty": "intermediate"
    }
}

SAMPLE_ROLEPLAY_SESSION = {
    "session_type": "roleplay",
    "duration_seconds": 600,
    "words_spoken": 250,
    "pronunciation_score": 90.0,
    "fluency_score": 85.0,
    "grammar_score": 87.5,
    "topics": ["job interview", "professional communication", "questions and answers"],
    "vocabulary_learned": ["strengths", "weaknesses", "experience", "qualifications"],
    "areas_to_improve": ["formal language", "expressing past achievements"],
    "metadata": {
        "scenario_id": "job-interview-tech",
        "job_role": "software engineer",
        "difficulty": "advanced"
    }
}


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_save_session():
    """Test the POST /api/sessions/save endpoint."""
    print_section("TEST 1: Save Session Result")

    print("Sample Request Body for Conversation Session:")
    print(json.dumps(SAMPLE_SESSION_RESULT, indent=2))

    print("\nExpected Response:")
    expected_response = {
        **SAMPLE_SESSION_RESULT,
        "session_result_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    print(json.dumps(expected_response, indent=2, default=str))

    print("\nCURL Command:")
    print("""
curl -X POST http://localhost:8000/api/sessions/save \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
    """.format(json.dumps(SAMPLE_SESSION_RESULT)))


def test_get_history():
    """Test the GET /api/sessions/history endpoint."""
    print_section("TEST 2: Get Session History")

    print("Example Query Parameters:")
    print("  - session_type=conversation (optional)")
    print("  - limit=10 (optional, default: 20, max: 100)")
    print("  - offset=0 (optional, default: 0)")

    print("\nCURL Command (All Sessions):")
    print("""
curl -X GET "http://localhost:8000/api/sessions/history?limit=10&offset=0" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """)

    print("\nCURL Command (Filtered by Type):")
    print("""
curl -X GET "http://localhost:8000/api/sessions/history?session_type=conversation&limit=5" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """)

    print("\nExpected Response Structure:")
    sample_response = {
        "sessions": [
            {
                "session_result_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                **SAMPLE_SESSION_RESULT,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ],
        "total": 1,
        "limit": 10,
        "offset": 0
    }
    print(json.dumps(sample_response, indent=2, default=str))


def test_get_stats():
    """Test the GET /api/sessions/stats endpoint."""
    print_section("TEST 3: Get Session Statistics")

    print("Query Parameters:")
    print("  - period: 'week' or 'month' (default: 'week')")

    print("\nCURL Command (Weekly Stats):")
    print("""
curl -X GET "http://localhost:8000/api/sessions/stats?period=week" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """)

    print("\nCURL Command (Monthly Stats):")
    print("""
curl -X GET "http://localhost:8000/api/sessions/stats?period=month" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """)

    print("\nExpected Response Structure:")
    sample_stats = {
        "total_sessions": 15,
        "total_duration": 4500,
        "total_words_spoken": 1800,
        "avg_pronunciation": 84.2,
        "avg_fluency": 79.5,
        "avg_grammar": 81.8,
        "sessions_by_type": {
            "conversation": {"count": 8, "avg_duration": 320},
            "pronunciation": {"count": 4, "avg_duration": 180},
            "roleplay": {"count": 3, "avg_duration": 400}
        },
        "improvement_trends": [
            {
                "date": "2025-12-06",
                "pronunciation": 82.0,
                "fluency": 76.5,
                "grammar": 80.0
            },
            {
                "date": "2025-12-07",
                "pronunciation": 83.5,
                "fluency": 78.0,
                "grammar": 81.0
            }
        ],
        "common_topics": [
            {"topic": "travel", "count": 12},
            {"topic": "business", "count": 8}
        ],
        "areas_to_improve": [
            {"area": "past tense usage", "count": 6},
            {"area": "prepositions", "count": 4}
        ]
    }
    print(json.dumps(sample_stats, indent=2))


def test_get_warmup():
    """Test the GET /api/sessions/warmup endpoint."""
    print_section("TEST 4: Get Warmup Content")

    print("CURL Command:")
    print("""
curl -X GET "http://localhost:8000/api/sessions/warmup" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """)

    print("\nExpected Response Structure:")
    sample_warmup = {
        "focus_areas": [
            "past tense usage",
            "prepositions",
            "pronunciation of 'th' sounds"
        ],
        "vocabulary_review": [
            "reservation",
            "available",
            "amenities",
            "confirm",
            "deposit"
        ],
        "last_session_summary": {
            "session_type": "conversation",
            "duration_seconds": 300,
            "pronunciation_score": 85.5,
            "fluency_score": 78.0,
            "grammar_score": 82.5,
            "areas_to_improve": ["past tense usage", "prepositions"],
            "created_at": datetime.now().isoformat()
        }
    }
    print(json.dumps(sample_warmup, indent=2, default=str))


def test_all_session_types():
    """Show examples of all session types."""
    print_section("TEST 5: All Session Types Examples")

    print("1. CONVERSATION SESSION:")
    print(json.dumps(SAMPLE_SESSION_RESULT, indent=2))

    print("\n2. PRONUNCIATION SESSION:")
    print(json.dumps(SAMPLE_PRONUNCIATION_SESSION, indent=2))

    print("\n3. ROLEPLAY SESSION:")
    print(json.dumps(SAMPLE_ROLEPLAY_SESSION, indent=2))


def main():
    """Run all test demonstrations."""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  SESSION ANALYTICS API - TEST EXAMPLES".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)

    test_save_session()
    test_get_history()
    test_get_stats()
    test_get_warmup()
    test_all_session_types()

    print("\n" + "=" * 80)
    print("  NEXT STEPS")
    print("=" * 80)
    print("""
1. Apply the database migration:
   python3 database/apply_migration_015.py

2. Start the backend server:
   uvicorn app.api2:app --reload

3. Test the endpoints using the curl commands above or visit:
   http://localhost:8000/docs

4. Replace YOUR_JWT_TOKEN with a valid JWT token from Supabase Auth

5. View the full API documentation:
   /Users/matuskalis/vorex-backend/SESSION_ANALYTICS_API.md
    """)

    print("\n" + "*" * 80 + "\n")


if __name__ == "__main__":
    main()
