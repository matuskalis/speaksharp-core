#!/usr/bin/env python3
"""
Apply migration 008: Conversation Memory System

This migration creates the conversation_history table and related functions
to enable the Voice Tutor to remember past sessions.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_db


def apply_migration_008():
    """Apply migration 008 to add conversation memory."""
    print("=" * 60)
    print("Applying Migration 008: Conversation Memory System")
    print("=" * 60)

    db = get_db()

    # Check database connection
    print("\n1. Checking database connection...")
    if not db.health_check():
        print("   ERROR: Database connection failed!")
        print("   Please check your DATABASE_URL or SUPABASE_DB_URL environment variable.")
        return False

    print("   SUCCESS: Database connected")

    # Read migration file
    migration_file = Path(__file__).parent / "migration_008_conversation_memory.sql"
    print(f"\n2. Reading migration file: {migration_file.name}")

    if not migration_file.exists():
        print(f"   ERROR: Migration file not found: {migration_file}")
        return False

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print(f"   SUCCESS: Migration file loaded ({len(migration_sql)} bytes)")

    # Apply migration
    print("\n3. Applying migration...")
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
                conn.commit()
        print("   SUCCESS: Migration applied successfully")
    except Exception as e:
        print(f"   ERROR: Failed to apply migration: {e}")
        return False

    # Verify migration
    print("\n4. Verifying migration...")
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if conversation_history table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'conversation_history'
                    );
                """)
                table_exists = cur.fetchone()[0]

                if table_exists:
                    print("   SUCCESS: conversation_history table created")
                else:
                    print("   ERROR: conversation_history table not found")
                    return False

                # Check if functions exist
                functions_to_check = [
                    'get_recent_conversations',
                    'get_conversation_context',
                    'save_conversation_turn',
                    'clear_conversation_history',
                    'get_conversation_by_context'
                ]

                for func_name in functions_to_check:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM pg_proc
                            WHERE proname = %s
                        );
                    """, (func_name,))
                    func_exists = cur.fetchone()[0]

                    if func_exists:
                        print(f"   SUCCESS: Function {func_name}() created")
                    else:
                        print(f"   WARNING: Function {func_name}() not found")

    except Exception as e:
        print(f"   ERROR: Verification failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("Migration 008 completed successfully!")
    print("=" * 60)
    print("\nConversation memory features:")
    print("  - conversation_history table stores all tutor conversations")
    print("  - Tutor can now reference past sessions")
    print("  - API endpoints available:")
    print("    * GET /api/tutor/history - View conversation history")
    print("    * DELETE /api/tutor/history - Clear history")
    print("    * GET /api/tutor/memory-summary - See what tutor remembers")
    print("\n")

    return True


if __name__ == "__main__":
    success = apply_migration_008()
    sys.exit(0 if success else 1)
