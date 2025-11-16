#!/usr/bin/env python3
"""
Test script for API endpoints.
"""

import requests
import json
import sys
from uuid import uuid4

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n" + "=" * 60)
    print("Testing GET /health")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✓ Health check passed")
    return response.json()


def test_create_user():
    """Test user creation."""
    print("\n" + "=" * 60)
    print("Testing POST /api/users")
    print("=" * 60)

    payload = {
        "level": "A1",
        "native_language": "Spanish",
        "goals": {"improve_speaking": True},
        "interests": ["travel", "food"]
    }

    print(f"Request payload:\n{json.dumps(payload, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/api/users",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    user_data = response.json()
    user_id = user_data["user_id"]

    print(f"✓ User created with ID: {user_id}")
    return user_id


def test_get_user(user_id):
    """Test getting user."""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/users/{user_id}")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/users/{user_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("✓ User retrieved successfully")
    return response.json()


def test_tutor_text(user_id):
    """Test text tutoring endpoint."""
    print("\n" + "=" * 60)
    print("Testing POST /api/tutor/text")
    print("=" * 60)

    payload = {
        "user_id": user_id,
        "text": "I go to school yesterday.",
        "scenario_id": "cafe_ordering",
        "context": "demo call from test script"
    }

    print(f"Request payload:\n{json.dumps(payload, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/api/tutor/text",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")

    if response.status_code != 200:
        print(f"Error response: {response.text}")
        assert False, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    # Validate response structure
    assert "message" in data, "Response missing 'message' field"
    assert "errors" in data, "Response missing 'errors' field"
    assert "session_id" in data, "Response missing 'session_id' field"

    print(f"\n✓ Tutor text endpoint passed")
    print(f"  Message: {data['message']}")
    print(f"  Errors found: {len(data['errors'])}")
    print(f"  Session ID: {data['session_id']}")

    if data.get('micro_task'):
        print(f"  Micro-task: {data['micro_task']}")

    return data


def test_get_srs_due(user_id):
    """Test getting due SRS cards."""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/srs/due/{user_id}")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/srs/due/{user_id}?limit=20")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print(f"✓ Got {data['count']} due cards")
    return data


def test_get_errors(user_id):
    """Test getting user errors."""
    print("\n" + "=" * 60)
    print(f"Testing GET /api/errors/{user_id}")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/errors/{user_id}?limit=50&unrecycled_only=false")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}...")
        print(f"✓ Got {data['count']} errors")
        return data
    else:
        print(f"Error: {response.text}")
        return None


def main():
    """Run all API tests."""
    print("\n" + "=" * 70)
    print("  SpeakSharp API Endpoint Tests")
    print("=" * 70)
    print(f"\nTesting against: {BASE_URL}")

    try:
        # Test 1: Health check
        test_health()

        # Test 2: Create user
        user_id = test_create_user()

        # Test 3: Get user
        test_get_user(user_id)

        # Test 4: Text tutoring (THE MAIN TEST)
        tutor_result = test_tutor_text(user_id)

        # Test 5: Get due SRS cards
        test_get_srs_due(user_id)

        # Test 6: Get errors
        test_get_errors(user_id)

        # Summary
        print("\n" + "=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)
        print("\n✅ All API tests passed!")
        print("\nKey results:")
        print(f"  • User ID: {user_id}")
        print(f"  • Tutor message: {tutor_result['message']}")
        print(f"  • Errors detected: {len(tutor_result['errors'])}")
        print(f"  • Session ID: {tutor_result['session_id']}")
        print("\n" + "=" * 70)

        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {BASE_URL}")
        print("   Make sure the API server is running:")
        print("   uvicorn app.api:app --reload")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
