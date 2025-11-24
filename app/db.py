"""
Database integration module for SpeakSharp Core.

Provides connection management and helper functions for:
- User profiles (create/get)
- SRS cards (insert/update/get due)
- Error logs (insert)
- Sessions (create/update)

Uses psycopg for PostgreSQL/Supabase connections.
"""

import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row


class DatabaseConfig:
    """Database connection configuration."""

    def __init__(self):
        # Support both direct connection string and component-based config
        self.connection_string = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

        if not self.connection_string:
            # Build from components
            self.host = os.getenv("DB_HOST", "localhost")
            self.port = int(os.getenv("DB_PORT", "5432"))
            self.database = os.getenv("DB_NAME", "speaksharp")
            self.user = os.getenv("DB_USER", "postgres")
            self.password = os.getenv("DB_PASSWORD", "")

            self.connection_string = (
                f"postgresql://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}"
            )

    def get_connection_string(self) -> str:
        """Get the database connection string."""
        return self.connection_string


class Database:
    """Database operations wrapper for SpeakSharp."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database connection.

        Args:
            config: Optional DatabaseConfig. If None, loads from environment.
        """
        self.config = config or DatabaseConfig()
        self._connection_string = self.config.get_connection_string()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Yields:
            psycopg.Connection: Database connection with dict_row cursor factory.
        """
        conn = psycopg.connect(
            self._connection_string,
            row_factory=dict_row
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # User Profiles

    def create_user(
        self,
        user_id: uuid.UUID,
        level: str = "A1",
        native_language: Optional[str] = None,
        goals: Optional[Dict[str, Any]] = None,
        interests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user profile.

        Args:
            user_id: User UUID (typically from Supabase Auth)
            level: CEFR level (A1, A2, B1, B2, C1, C2)
            native_language: User's native language
            goals: User learning goals as JSON
            interests: List of user interests

        Returns:
            User profile dict
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_profiles (
                        user_id, level, native_language, goals, interests
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    user_id,
                    level,
                    native_language,
                    psycopg.types.json.Json(goals or {}),
                    psycopg.types.json.Json(interests or [])
                ))
                return cur.fetchone()

    def get_user(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID.

        Args:
            user_id: User UUID

        Returns:
            User profile dict or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM user_profiles WHERE user_id = %s",
                    (user_id,)
                )
                return cur.fetchone()

    def update_user_level(self, user_id: uuid.UUID, level: str) -> bool:
        """
        Update user's proficiency level.

        Args:
            user_id: User UUID
            level: New CEFR level

        Returns:
            True if updated, False if user not found
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET level = %s, updated_at = NOW()
                    WHERE user_id = %s
                """, (level, user_id))
                return cur.rowcount > 0

    def update_user_profile(
        self,
        user_id: uuid.UUID,
        level: Optional[str] = None,
        native_language: Optional[str] = None,
        full_name: Optional[str] = None,
        country: Optional[str] = None,
        onboarding_completed: Optional[bool] = None
    ) -> bool:
        """
        Update user profile fields.

        Args:
            user_id: User UUID
            level: New CEFR level (optional)
            native_language: New native language (optional)
            full_name: User's full name (optional)
            country: User's country (optional)
            onboarding_completed: Whether onboarding is complete (optional)

        Returns:
            True if updated, False if user not found
        """
        # Build dynamic update query
        updates = []
        params = []

        if level is not None:
            updates.append("level = %s")
            params.append(level)

        if native_language is not None:
            updates.append("native_language = %s")
            params.append(native_language)

        if full_name is not None:
            updates.append("full_name = %s")
            params.append(full_name)

        if country is not None:
            updates.append("country = %s")
            params.append(country)

        if onboarding_completed is not None:
            updates.append("onboarding_completed = %s")
            params.append(onboarding_completed)

        if not updates:
            # No fields to update
            return True

        updates.append("updated_at = NOW()")
        params.append(user_id)

        query = f"""
            UPDATE user_profiles
            SET {', '.join(updates)}
            WHERE user_id = %s
        """

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount > 0

    # SRS Cards

    def create_srs_card(
        self,
        user_id: uuid.UUID,
        card_type: str,
        front: str,
        back: str,
        level: str = "A1",
        source: Optional[str] = None,
        source_id: Optional[uuid.UUID] = None,
        difficulty: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new SRS card.

        Args:
            user_id: User UUID
            card_type: Type of card (definition, cloze, production, etc.)
            front: Front side of card
            back: Back side of card
            level: CEFR level
            source: Source type (error, lesson, scenario)
            source_id: ID of source record
            difficulty: Difficulty rating (0.0-1.0)
            metadata: Additional metadata as JSON

        Returns:
            Created card dict
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO srs_cards (
                        user_id, card_type, front, back, level,
                        source, source_id, difficulty, next_review_date, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    user_id,
                    card_type,
                    front,
                    back,
                    level,
                    source,
                    source_id,
                    difficulty,
                    datetime.now(),
                    psycopg.types.json.Json(metadata or {})
                ))
                return cur.fetchone()

    def get_due_cards(
        self,
        user_id: uuid.UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get due SRS cards for review.

        Args:
            user_id: User UUID
            limit: Maximum number of cards to return

        Returns:
            List of due cards
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM get_due_cards(%s, %s)
                """, (user_id, limit))
                return cur.fetchall()

    def update_card_after_review(
        self,
        card_id: uuid.UUID,
        quality: int,
        response_time_ms: Optional[int] = None,
        user_response: Optional[str] = None,
        correct: bool = True
    ) -> None:
        """
        Update SRS card after review using SM-2 algorithm.

        Args:
            card_id: Card UUID
            quality: Quality rating (0-5, SM-2 standard)
            response_time_ms: Response time in milliseconds
            user_response: User's actual response
            correct: Whether response was correct
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT update_card_after_review(%s, %s, %s, %s, %s)
                """, (card_id, quality, response_time_ms, user_response, correct))

    def get_card(self, card_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific SRS card by ID.

        Args:
            card_id: Card UUID

        Returns:
            Card dict or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM srs_cards WHERE card_id = %s",
                    (card_id,)
                )
                return cur.fetchone()

    # Error Logs

    def log_error(
        self,
        user_id: uuid.UUID,
        error_type: str,
        user_sentence: str,
        corrected_sentence: str,
        explanation: Optional[str] = None,
        session_id: Optional[uuid.UUID] = None,
        source_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a user error.

        Args:
            user_id: User UUID
            error_type: Type of error (grammar, vocab, fluency, etc.)
            user_sentence: Original user sentence
            corrected_sentence: Corrected version
            explanation: Explanation of the error
            session_id: Optional session UUID
            source_type: Source type (scenario, lesson, free_chat)

        Returns:
            Created error log dict
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO error_log (
                        user_id, session_id, error_type, source_type,
                        user_sentence, corrected_sentence, explanation
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    user_id,
                    session_id,
                    error_type,
                    source_type,
                    user_sentence,
                    corrected_sentence,
                    explanation
                ))
                return cur.fetchone()

    def create_card_from_error(self, error_id: uuid.UUID) -> uuid.UUID:
        """
        Create an SRS card from a logged error.

        Args:
            error_id: Error log UUID

        Returns:
            Created card UUID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT create_card_from_error(%s)",
                    (error_id,)
                )
                result = cur.fetchone()
                return result['create_card_from_error']

    def get_user_errors(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        unrecycled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get user's error history.

        Args:
            user_id: User UUID
            limit: Maximum number of errors to return
            unrecycled_only: If True, only return errors not yet recycled into cards

        Returns:
            List of error dicts
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if unrecycled_only:
                    cur.execute("""
                        SELECT * FROM error_log
                        WHERE user_id = %s AND recycled = FALSE
                        ORDER BY occurred_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                else:
                    cur.execute("""
                        SELECT * FROM error_log
                        WHERE user_id = %s
                        ORDER BY occurred_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                return cur.fetchall()

    # Sessions

    def create_session(
        self,
        user_id: uuid.UUID,
        session_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new session.

        Args:
            user_id: User UUID
            session_type: Type of session (scenario, lesson, free_chat, review)
            metadata: Additional session metadata

        Returns:
            Created session dict
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sessions (user_id, session_type, metadata)
                    VALUES (%s, %s, %s)
                    RETURNING *
                """, (
                    user_id,
                    session_type,
                    psycopg.types.json.Json(metadata or {})
                ))
                return cur.fetchone()

    def complete_session(
        self,
        session_id: uuid.UUID,
        duration_seconds: Optional[int] = None
    ) -> bool:
        """
        Mark a session as completed.

        Args:
            session_id: Session UUID
            duration_seconds: Session duration in seconds

        Returns:
            True if updated, False if session not found
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE sessions
                    SET completed_at = NOW(),
                        duration_seconds = %s,
                        state = 'completed'
                    WHERE session_id = %s
                """, (duration_seconds, session_id))
                return cur.rowcount > 0

    def get_session(self, session_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session dict or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM sessions WHERE session_id = %s",
                    (session_id,)
                )
                return cur.fetchone()

    # Streaks

    def get_user_streak(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get user's current streak information.

        Args:
            user_id: User UUID

        Returns:
            Streak dict with current_streak, longest_streak, last_active_date or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        current_streak_days,
                        longest_streak_days,
                        last_activity_date
                    FROM user_streaks
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()

                if result:
                    return {
                        "current_streak": result["current_streak_days"],
                        "longest_streak": result["longest_streak_days"],
                        "last_active_date": result["last_activity_date"].isoformat() if result["last_activity_date"] else None
                    }

                # If no streak record exists, return zeros
                return {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "last_active_date": None
                }

    # Achievements

    def get_achievements(self) -> List[Dict[str, Any]]:
        """
        Get all available achievements.

        Returns:
            List of achievement dicts
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM achievements
                    ORDER BY category, points
                """)
                return cur.fetchall()

    def get_user_achievements(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get user's unlocked achievements with details.

        Args:
            user_id: User UUID

        Returns:
            List of unlocked achievements with progress and unlock date
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        a.*,
                        ua.unlocked_at,
                        ua.progress
                    FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.achievement_id
                    WHERE ua.user_id = %s
                    ORDER BY ua.unlocked_at DESC
                """, (user_id,))
                return cur.fetchall()

    def unlock_achievement(
        self,
        user_id: uuid.UUID,
        achievement_key: str,
        progress: float = 100.0
    ) -> Optional[Dict[str, Any]]:
        """
        Unlock an achievement for a user.

        Args:
            user_id: User UUID
            achievement_key: Achievement key (e.g., "first_lesson")
            progress: Progress percentage (default 100.0)

        Returns:
            Created user_achievement dict or None if already unlocked
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get achievement_id from key
                cur.execute("""
                    SELECT achievement_id FROM achievements WHERE achievement_key = %s
                """, (achievement_key,))
                result = cur.fetchone()

                if not result:
                    return None

                achievement_id = result['achievement_id']

                # Try to insert (will fail if already exists due to UNIQUE constraint)
                try:
                    cur.execute("""
                        INSERT INTO user_achievements (user_id, achievement_id, progress, unlocked_at)
                        VALUES (%s, %s, %s, NOW())
                        RETURNING *
                    """, (user_id, achievement_id, progress))
                    return cur.fetchone()
                except Exception:
                    # Already unlocked
                    return None

    def has_achievement(self, user_id: uuid.UUID, achievement_key: str) -> bool:
        """
        Check if user has unlocked a specific achievement.

        Args:
            user_id: User UUID
            achievement_key: Achievement key

        Returns:
            True if unlocked, False otherwise
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM user_achievements ua
                    JOIN achievements a ON ua.achievement_id = a.achievement_id
                    WHERE ua.user_id = %s AND a.achievement_key = %s
                """, (user_id, achievement_key))
                return cur.fetchone() is not None

    # Daily Goals

    def get_daily_goal(self, user_id: uuid.UUID, goal_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Get daily goal for a specific date (defaults to today).

        Args:
            user_id: User UUID
            goal_date: Date for the goal (defaults to today)

        Returns:
            Daily goal dict or None if not found
        """
        if goal_date is None:
            goal_date = datetime.now().date()

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM daily_goals
                    WHERE user_id = %s AND goal_date = %s
                """, (user_id, goal_date))
                return cur.fetchone()

    def create_or_update_daily_goal(
        self,
        user_id: uuid.UUID,
        goal_date: Optional[datetime] = None,
        target_study_minutes: Optional[int] = None,
        target_lessons: Optional[int] = None,
        target_reviews: Optional[int] = None,
        target_drills: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create or update daily goal targets.

        Args:
            user_id: User UUID
            goal_date: Date for the goal (defaults to today)
            target_study_minutes: Target study time
            target_lessons: Target lessons count
            target_reviews: Target reviews count
            target_drills: Target drills count

        Returns:
            Created/updated daily goal dict
        """
        if goal_date is None:
            goal_date = datetime.now().date()

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Try to insert, update if exists
                cur.execute("""
                    INSERT INTO daily_goals (
                        user_id, goal_date,
                        target_study_minutes, target_lessons, target_reviews, target_drills
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, goal_date)
                    DO UPDATE SET
                        target_study_minutes = COALESCE(EXCLUDED.target_study_minutes, daily_goals.target_study_minutes),
                        target_lessons = COALESCE(EXCLUDED.target_lessons, daily_goals.target_lessons),
                        target_reviews = COALESCE(EXCLUDED.target_reviews, daily_goals.target_reviews),
                        target_drills = COALESCE(EXCLUDED.target_drills, daily_goals.target_drills),
                        updated_at = NOW()
                    RETURNING *
                """, (user_id, goal_date, target_study_minutes, target_lessons, target_reviews, target_drills))
                return cur.fetchone()

    def increment_daily_goal_progress(
        self,
        user_id: uuid.UUID,
        goal_date: Optional[datetime] = None,
        study_minutes: int = 0,
        lessons: int = 0,
        reviews: int = 0,
        drills: int = 0
    ) -> Dict[str, Any]:
        """
        Increment daily goal progress counters.

        Args:
            user_id: User UUID
            goal_date: Date for the goal (defaults to today)
            study_minutes: Minutes to add
            lessons: Lessons to add
            reviews: Reviews to add
            drills: Drills to add

        Returns:
            Updated daily goal dict
        """
        if goal_date is None:
            goal_date = datetime.now().date()

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create goal if doesn't exist, then increment
                cur.execute("""
                    INSERT INTO daily_goals (user_id, goal_date)
                    VALUES (%s, %s)
                    ON CONFLICT (user_id, goal_date) DO NOTHING
                """, (user_id, goal_date))

                cur.execute("""
                    UPDATE daily_goals
                    SET
                        actual_study_minutes = actual_study_minutes + %s,
                        actual_lessons = actual_lessons + %s,
                        actual_reviews = actual_reviews + %s,
                        actual_drills = actual_drills + %s,
                        updated_at = NOW()
                    WHERE user_id = %s AND goal_date = %s
                    RETURNING *
                """, (study_minutes, lessons, reviews, drills, user_id, goal_date))

                goal = cur.fetchone()

                # Update completion percentage
                if goal:
                    total_progress = 0
                    total_targets = 0

                    for target_key, actual_key in [
                        ('target_study_minutes', 'actual_study_minutes'),
                        ('target_lessons', 'actual_lessons'),
                        ('target_reviews', 'actual_reviews'),
                        ('target_drills', 'actual_drills')
                    ]:
                        target = goal.get(target_key, 0)
                        actual = goal.get(actual_key, 0)
                        if target and target > 0:
                            total_targets += 1
                            total_progress += min(100, (actual / target) * 100)

                    completion = (total_progress / total_targets) if total_targets > 0 else 0
                    completed = completion >= 100

                    cur.execute("""
                        UPDATE daily_goals
                        SET completion_percentage = %s, completed = %s
                        WHERE user_id = %s AND goal_date = %s
                        RETURNING *
                    """, (completion, completed, user_id, goal_date))

                    return cur.fetchone()

                return goal

    # Referrals

    def get_or_create_referral_code(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get user's referral code or create one if doesn't exist.

        Args:
            user_id: User UUID

        Returns:
            Referral code dict
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if user already has a code
                cur.execute("""
                    SELECT * FROM referral_codes WHERE user_id = %s AND is_active = TRUE
                """, (user_id,))
                existing = cur.fetchone()

                if existing:
                    return existing

                # Generate unique code (user_id first 8 chars)
                code = str(user_id).replace('-', '')[:8].upper()

                cur.execute("""
                    INSERT INTO referral_codes (user_id, code, is_active)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
                    RETURNING *
                """, (user_id, code))
                return cur.fetchone()

    def get_referral_stats(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get user's referral statistics.

        Args:
            user_id: User UUID

        Returns:
            Dict with total_signups, total_conversions, and referral_code
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get referral code
                code_data = self.get_or_create_referral_code(user_id)

                # Get conversion stats
                cur.execute("""
                    SELECT
                        COUNT(*) as total_signups,
                        COUNT(*) FILTER (WHERE converted = TRUE) as total_conversions
                    FROM referral_conversions
                    WHERE referrer_user_id = %s
                """, (user_id,))
                stats = cur.fetchone()

                return {
                    "referral_code": code_data['code'],
                    "total_signups": stats['total_signups'] if stats else 0,
                    "total_conversions": stats['total_conversions'] if stats else 0
                }

    def claim_referral_code(self, referred_user_id: uuid.UUID, referral_code: str) -> bool:
        """
        Claim a referral code for a new user.

        Args:
            referred_user_id: New user's UUID
            referral_code: Referral code to claim

        Returns:
            True if successful, False otherwise
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Find referrer by code
                cur.execute("""
                    SELECT user_id FROM referral_codes WHERE code = %s AND is_active = TRUE
                """, (referral_code,))
                referrer = cur.fetchone()

                if not referrer:
                    return False

                referrer_id = referrer['user_id']

                # Don't allow self-referral
                if referrer_id == referred_user_id:
                    return False

                try:
                    # Create conversion record
                    cur.execute("""
                        INSERT INTO referral_conversions (
                            referrer_user_id, referred_user_id, referral_code
                        )
                        VALUES (%s, %s, %s)
                    """, (referrer_id, referred_user_id, referral_code))

                    # Update total_signups counter
                    cur.execute("""
                        UPDATE referral_codes
                        SET total_signups = total_signups + 1
                        WHERE code = %s
                    """, (referral_code,))

                    return True
                except Exception:
                    return False

    # Skill Graph

    def update_skill_node(
        self,
        user_id: uuid.UUID,
        skill_key: str,
        success: bool,
        score_delta: float
    ) -> None:
        """
        Update a skill node (create if doesn't exist).

        Args:
            user_id: User UUID
            skill_key: Skill identifier
            success: Whether the practice was successful
            score_delta: Change in mastery score
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT update_skill_node(%s, %s, %s, %s)
                """, (user_id, skill_key, success, score_delta))

    def get_weakest_skills(
        self,
        user_id: uuid.UUID,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get user's weakest skills.

        Args:
            user_id: User UUID
            limit: Maximum number of skills to return

        Returns:
            List of skill dicts with skill_key, mastery_score, error_count
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM get_weakest_skills(%s, %s)
                """, (user_id, limit))
                return cur.fetchall()

    # Health Check

    def health_check(self) -> bool:
        """
        Perform a health check on the database connection.

        Returns:
            True if connection is healthy
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return cur.fetchone() is not None
        except Exception:
            return False


# Global database instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """
    Get the global database instance.

    Returns:
        Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == "__main__":
    """Test database connection and basic operations."""
    print("SpeakSharp Database Module Test")
    print("=" * 60)

    # Test connection
    db = get_db()
    print("\n🔌 Testing database connection...")

    try:
        if db.health_check():
            print("✓ Database connection successful!")
        else:
            print("✗ Database connection failed!")
            exit(1)
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        print("\nPlease set database environment variables:")
        print("  DATABASE_URL or SUPABASE_DB_URL")
        print("  OR")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        exit(1)

    # Test user creation
    print("\n👤 Testing user operations...")
    test_user_id = uuid.uuid4()

    try:
        user = db.create_user(
            user_id=test_user_id,
            level="A1",
            native_language="Spanish",
            goals={"improve_speaking": True},
            interests=["travel", "food"]
        )
        print(f"✓ Created user: {user['user_id']}")

        # Retrieve user
        retrieved = db.get_user(test_user_id)
        print(f"✓ Retrieved user: level={retrieved['level']}, native={retrieved['native_language']}")

    except Exception as e:
        print(f"✗ User operation failed: {e}")

    # Test SRS card creation
    print("\n🎴 Testing SRS card operations...")

    try:
        card = db.create_srs_card(
            user_id=test_user_id,
            card_type="definition",
            front="What is 'hello' in English?",
            back="A greeting",
            level="A1"
        )
        print(f"✓ Created SRS card: {card['card_id']}")

        # Get due cards
        due_cards = db.get_due_cards(test_user_id, limit=10)
        print(f"✓ Found {len(due_cards)} due cards")

    except Exception as e:
        print(f"✗ SRS operation failed: {e}")

    # Test error logging
    print("\n⚠️  Testing error logging...")

    try:
        error = db.log_error(
            user_id=test_user_id,
            error_type="grammar",
            user_sentence="I go to school yesterday",
            corrected_sentence="I went to school yesterday",
            explanation="Use past tense 'went' for actions in the past"
        )
        print(f"✓ Logged error: {error['error_id']}")

        # Create card from error
        card_id = db.create_card_from_error(error['error_id'])
        print(f"✓ Created card from error: {card_id}")

    except Exception as e:
        print(f"✗ Error logging failed: {e}")

    # Test session creation
    print("\n📊 Testing session operations...")

    try:
        session = db.create_session(
            user_id=test_user_id,
            session_type="scenario",
            metadata={"scenario_name": "café_ordering"}
        )
        print(f"✓ Created session: {session['session_id']}")

        # Complete session
        db.complete_session(session['session_id'], duration_seconds=300)
        print("✓ Completed session")

    except Exception as e:
        print(f"✗ Session operation failed: {e}")

    print("\n" + "=" * 60)
    print("✅ Database module test completed!")
