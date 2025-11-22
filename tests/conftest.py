"""Pytest configuration and fixtures."""

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test database URL if not already set
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = (
            "postgresql://speaksharp_user:speaksharp_pass@localhost:5432/speaksharp_db"
        )

    # Ensure LLM/ASR/TTS run in stub mode for tests
    os.environ["SPEAKSHARP_ENABLE_LLM"] = "true"
    os.environ["SPEAKSHARP_ENABLE_ASR"] = "true"
    os.environ["SPEAKSHARP_ENABLE_TTS"] = "true"

    # Don't require API keys for tests (stub mode)
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = ""

    yield


@pytest.fixture
def client():
    """Create a test client for the API."""
    from app.api import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(client):
    """Create a test user and return their ID."""
    response = client.post(
        "/api/users",
        json={
            "level": "A1",
            "native_language": "Spanish",
            "goals": {"improve_speaking": True},
            "interests": ["travel", "food"]
        }
    )
    assert response.status_code == 200
    user_data = response.json()
    return user_data["user_id"]
