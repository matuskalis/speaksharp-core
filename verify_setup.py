#!/usr/bin/env python3
"""
Quick verification script for SpeakSharp Core setup.

Checks:
- Python dependencies
- Module imports
- Configuration
- Database connectivity (if configured)
- File structure
"""

import sys
import os
from pathlib import Path

# Add app directory to path for relative imports
sys.path.insert(0, str(Path(__file__).parent / "app"))


def check_mark(passed: bool) -> str:
    """Return check mark or X based on pass/fail."""
    return "✓" if passed else "✗"


def print_header(title: str):
    """Print section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def check_dependencies():
    """Check if all required dependencies are installed."""
    print_header("Dependency Check")

    deps = {
        "pydantic": "pydantic",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "psycopg": "psycopg",
        "dotenv": "python-dotenv",
    }

    optional_deps = {
        "openai": "openai",
        "anthropic": "anthropic",
    }

    all_passed = True

    for name, package in deps.items():
        try:
            __import__(name)
            print(f"{check_mark(True)} {package}")
        except ImportError:
            print(f"{check_mark(False)} {package} - MISSING (run: pip install {package})")
            all_passed = False

    print("\nOptional dependencies:")
    for name, package in optional_deps.items():
        try:
            __import__(name)
            print(f"{check_mark(True)} {package}")
        except ImportError:
            print(f"{check_mark(False)} {package} - Optional for LLM/Voice features")

    return all_passed


def check_modules():
    """Check if all app modules can be imported."""
    print_header("Module Import Check")

    modules = [
        "app.config",
        "app.models",
        "app.lessons",
        "app.scenarios",
        "app.srs_system",
        "app.tutor_agent",
        "app.state_machine",
        "app.llm_client",
        "app.asr_client",
        "app.tts_client",
        "app.voice_session",
        "app.db",
        "app.api",
    ]

    all_passed = True

    for module in modules:
        try:
            __import__(module)
            print(f"{check_mark(True)} {module}")
        except ImportError as e:
            print(f"{check_mark(False)} {module} - ERROR: {e}")
            all_passed = False

    return all_passed


def check_configuration():
    """Check configuration."""
    print_header("Configuration Check")

    try:
        from app.config import load_config

        config = load_config()

        print(f"{check_mark(True)} Configuration loaded")
        print(f"\nLLM:")
        print(f"  Provider: {config.llm.provider}")
        print(f"  Model: {config.llm.model}")
        print(f"  API Key: {check_mark(config.llm.api_key is not None)} {'Set' if config.llm.api_key else 'Not set'}")
        print(f"  Enabled: {config.enable_llm}")

        print(f"\nASR:")
        print(f"  Provider: {config.asr.provider}")
        print(f"  API Key: {check_mark(config.asr.api_key is not None)} {'Set' if config.asr.api_key else 'Not set'}")
        print(f"  Enabled: {config.enable_asr}")

        print(f"\nTTS:")
        print(f"  Provider: {config.tts.provider}")
        print(f"  API Key: {check_mark(config.tts.api_key is not None)} {'Set' if config.tts.api_key else 'Not set'}")
        print(f"  Enabled: {config.enable_tts}")

        if not config.llm.api_key and config.enable_llm:
            print(f"\n⚠️  LLM enabled but no API key - will use stub mode")

        return True

    except Exception as e:
        print(f"{check_mark(False)} Configuration error: {e}")
        return False


def check_database():
    """Check database connectivity."""
    print_header("Database Check")

    # Check environment variables
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    db_configured = db_url is not None

    if not db_configured:
        # Check component-based config
        db_host = os.getenv("DB_HOST")
        db_configured = db_host is not None

    print(f"{check_mark(db_configured)} Database environment configured")

    if not db_configured:
        print("\n⚠️  No database configuration found")
        print("   Set DATABASE_URL or DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        print("   Database features will not work without configuration")
        return False

    try:
        from app.db import get_db

        db = get_db()
        if db.health_check():
            print(f"{check_mark(True)} Database connection successful")
            return True
        else:
            print(f"{check_mark(False)} Database connection failed")
            return False

    except Exception as e:
        print(f"{check_mark(False)} Database error: {e}")
        print("\n⚠️  Database configured but connection failed")
        print("   Make sure the database is running and schema is loaded")
        print("   Run: psql speaksharp < database/schema.sql")
        return False


def check_file_structure():
    """Check if all required files exist."""
    print_header("File Structure Check")

    required_files = [
        "app/config.py",
        "app/db.py",
        "app/api.py",
        "app/lessons.py",
        "app/scenarios.py",
        "app/srs_system.py",
        "app/tutor_agent.py",
        "app/llm_client.py",
        "app/asr_client.py",
        "app/tts_client.py",
        "app/voice_session.py",
        "database/schema.sql",
        "demo_integration.py",
        "test_db_integration.py",
        "test_llm_modes.py",
        "test_voice_modes.py",
        "requirements.txt",
        "README.md",
    ]

    all_exist = True

    for file_path in required_files:
        exists = Path(file_path).exists()
        print(f"{check_mark(exists)} {file_path}")
        if not exists:
            all_exist = False

    return all_exist


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("  SpeakSharp Core - Setup Verification")
    print("=" * 60)

    results = {
        "Dependencies": check_dependencies(),
        "Modules": check_modules(),
        "Configuration": check_configuration(),
        "Database": check_database(),
        "Files": check_file_structure(),
    }

    # Summary
    print_header("Summary")

    all_passed = all(results.values())

    for check, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{check_mark(passed)} {check}: {status}")

    print("\n" + "=" * 60)

    if all_passed:
        print("✅ All checks passed!")
        print("\nYou can now:")
        print("  1. Run demos: python demo_integration.py")
        print("  2. Test database: python test_db_integration.py")
        print("  3. Start API: python -m app.api")
        print("  4. View API docs: http://localhost:8000/docs")
    else:
        print("⚠️  Some checks failed")
        print("\nPlease review the errors above and:")
        print("  1. Install missing dependencies: pip install -r requirements.txt")
        print("  2. Configure database: export DATABASE_URL=...")
        print("  3. (Optional) Configure API keys: export OPENAI_API_KEY=...")

    print("=" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
