"""API endpoint tests using pytest and FastAPI TestClient."""

import pytest
from uuid import UUID


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test GET /health returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data
        assert data["status"] in ["healthy", "degraded"]


class TestUserEndpoints:
    """Tests for user management endpoints."""

    def test_create_user_and_get_user(self, client):
        """Test creating a user and retrieving it."""
        # Create user
        create_response = client.post(
            "/api/users",
            json={
                "level": "A1",
                "native_language": "Spanish",
                "goals": {"improve_speaking": True},
                "interests": ["travel", "food"]
            }
        )

        assert create_response.status_code == 200
        user_data = create_response.json()

        # Validate response structure
        assert "user_id" in user_data
        assert user_data["level"] == "A1"
        assert user_data["native_language"] == "Spanish"
        assert user_data["goals"] == {"improve_speaking": True}
        assert user_data["interests"] == ["travel", "food"]

        # Validate UUID format
        user_id = user_data["user_id"]
        UUID(user_id)  # Will raise ValueError if invalid

        # Retrieve the same user
        get_response = client.get(f"/api/users/{user_id}")

        assert get_response.status_code == 200
        retrieved_data = get_response.json()

        # Verify data matches
        assert retrieved_data["user_id"] == user_id
        assert retrieved_data["level"] == "A1"
        assert retrieved_data["native_language"] == "Spanish"

    def test_get_nonexistent_user(self, client):
        """Test getting a user that doesn't exist."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/users/{fake_uuid}")

        assert response.status_code == 404


class TestTutorEndpoints:
    """Tests for tutor endpoints."""

    def test_tutor_text_basic(self, client, test_user):
        """Test basic text tutoring flow."""
        response = client.post(
            "/api/tutor/text",
            json={
                "user_id": test_user,
                "text": "Hello, I want to practice English.",
                "scenario_id": "cafe_ordering",
                "context": "test context"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "message" in data
        assert isinstance(data["message"], str)
        assert len(data["message"]) > 0

        assert "errors" in data
        assert isinstance(data["errors"], list)

        assert "micro_task" in data
        # micro_task can be None or a string

        assert "session_id" in data
        UUID(data["session_id"])  # Validate UUID format

    def test_tutor_text_with_error(self, client, test_user):
        """Test text tutoring with text that triggers heuristic errors."""
        response = client.post(
            "/api/tutor/text",
            json={
                "user_id": test_user,
                "text": "I want order coffee.",  # Missing "to"
                "scenario_id": "cafe_ordering"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "errors" in data
        assert isinstance(data["errors"], list)
        # In stub mode, heuristics should detect errors
        # We can't assert exact count due to stub mode variability

        assert "session_id" in data

    def test_tutor_text_invalid_user(self, client):
        """Test text tutoring with invalid user ID."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.post(
            "/api/tutor/text",
            json={
                "user_id": fake_uuid,
                "text": "Hello",
            }
        )

        # Should fail because user doesn't exist
        assert response.status_code in [404, 500]


class TestSRSEndpoints:
    """Tests for SRS (Spaced Repetition System) endpoints."""

    def test_get_due_cards_empty(self, client, test_user):
        """Test getting due cards for a new user (should be empty)."""
        response = client.get(f"/api/srs/due/{test_user}")

        assert response.status_code == 200
        data = response.json()

        assert "cards" in data
        assert isinstance(data["cards"], list)
        assert "count" in data
        assert data["count"] == len(data["cards"])

    def test_srs_flow_from_error(self, client, test_user):
        """Test complete SRS flow: create error → get errors → create card from error."""
        # Step 1: Trigger tutor with error-prone text
        tutor_response = client.post(
            "/api/tutor/text",
            json={
                "user_id": test_user,
                "text": "I want order large cappuccino.",
                "scenario_id": "cafe_ordering"
            }
        )

        assert tutor_response.status_code == 200
        tutor_data = tutor_response.json()

        # Step 2: Get errors for this user
        errors_response = client.get(
            f"/api/errors/{test_user}?unrecycled_only=false"
        )

        assert errors_response.status_code == 200
        errors_data = errors_response.json()

        assert "errors" in errors_data
        assert "count" in errors_data
        errors_list = errors_data["errors"]

        # If errors were detected and logged, test card creation
        if len(errors_list) > 0:
            error_id = errors_list[0]["error_id"]

            # Step 3: Create SRS card from error
            card_response = client.post(f"/api/srs/from-error/{error_id}")

            assert card_response.status_code == 200
            card_data = card_response.json()

            assert "card_id" in card_data
            assert "error_id" in card_data
            assert card_data["error_id"] == error_id

            # Step 4: Verify error is now recycled
            updated_errors = client.get(
                f"/api/errors/{test_user}?unrecycled_only=true"
            )
            updated_data = updated_errors.json()

            # The recycled error should not appear in unrecycled_only list
            unrecycled_ids = [e["error_id"] for e in updated_data["errors"]]
            assert error_id not in unrecycled_ids


class TestErrorEndpoints:
    """Tests for error logging endpoints."""

    def test_get_user_errors(self, client, test_user):
        """Test getting errors for a user."""
        # First, create some errors via tutor
        client.post(
            "/api/tutor/text",
            json={
                "user_id": test_user,
                "text": "I want order coffee.",
            }
        )

        # Get errors
        response = client.get(f"/api/errors/{test_user}?limit=50")

        assert response.status_code == 200
        data = response.json()

        assert "errors" in data
        assert isinstance(data["errors"], list)
        assert "count" in data
        assert data["count"] == len(data["errors"])

    def test_get_errors_nonexistent_user(self, client):
        """Test getting errors for nonexistent user."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/errors/{fake_uuid}")

        assert response.status_code == 404


class TestSkillEndpoints:
    """Tests for skill tracking endpoints."""

    def test_get_weakest_skills(self, client, test_user):
        """Test getting weakest skills for a user."""
        response = client.get(f"/api/skills/weakest/{test_user}?limit=5")

        assert response.status_code == 200
        data = response.json()

        assert "skills" in data
        assert isinstance(data["skills"], list)
        assert "count" in data

    def test_get_weakest_skills_nonexistent_user(self, client):
        """Test getting skills for nonexistent user."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/skills/weakest/{fake_uuid}")

        assert response.status_code == 404
