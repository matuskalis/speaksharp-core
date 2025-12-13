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
        goals: Optional[List[str]] = None,
        interests: Optional[List[str]] = None,
        daily_time_goal: Optional[int] = None,
        full_name: Optional[str] = None,
        country: Optional[str] = None,
        onboarding_completed: Optional[bool] = None,
        trial_start_date: Optional[datetime] = None,
        trial_end_date: Optional[datetime] = None,
        subscription_status: Optional[str] = None,
        subscription_tier: Optional[str] = None
    ) -> bool:
        """
        Update user profile fields.

        Args:
            user_id: User UUID
            level: New CEFR level (optional)
            native_language: New native language (optional)
            goals: User learning goals (optional)
            interests: User interests (optional)
            daily_time_goal: Daily time goal in minutes (optional)
            full_name: User's full name (optional)
            country: User's country (optional)
            onboarding_completed: Whether onboarding is complete (optional)
            trial_start_date: Trial start date (optional)
            trial_end_date: Trial end date (optional)
            subscription_status: Subscription status (optional)
            subscription_tier: Subscription tier (optional)

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

        if goals is not None:
            updates.append("goals = %s")
            params.append(psycopg.types.json.Json(goals))

        if interests is not None:
            updates.append("interests = %s")
            params.append(psycopg.types.json.Json(interests))

        if daily_time_goal is not None:
            updates.append("daily_time_goal = %s")
            params.append(daily_time_goal)

        if full_name is not None:
            updates.append("full_name = %s")
            params.append(full_name)

        if country is not None:
            updates.append("country = %s")
            params.append(country)

        if onboarding_completed is not None:
            updates.append("onboarding_completed = %s")
            params.append(onboarding_completed)

        if trial_start_date is not None:
            updates.append("trial_start_date = %s")
            params.append(trial_start_date)

        if trial_end_date is not None:
            updates.append("trial_end_date = %s")
            params.append(trial_end_date)

        if subscription_status is not None:
            updates.append("subscription_status = %s")
            params.append(subscription_status)

        if subscription_tier is not None:
            updates.append("subscription_tier = %s")
            params.append(subscription_tier)

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

    # Session Analytics

    def save_session_result(
        self,
        user_id: uuid.UUID,
        session_type: str,
        duration_seconds: int,
        words_spoken: int = 0,
        pronunciation_score: float = 0.0,
        fluency_score: float = 0.0,
        grammar_score: float = 0.0,
        topics: Optional[List[str]] = None,
        vocabulary_learned: Optional[List[str]] = None,
        areas_to_improve: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a completed session result with analytics data.

        Args:
            user_id: User UUID
            session_type: Type of session (conversation, pronunciation, roleplay)
            duration_seconds: Duration in seconds
            words_spoken: Number of words spoken
            pronunciation_score: Pronunciation score (0-100)
            fluency_score: Fluency score (0-100)
            grammar_score: Grammar score (0-100)
            topics: List of topics covered
            vocabulary_learned: List of vocabulary items learned
            areas_to_improve: List of areas needing improvement
            metadata: Additional session-specific data

        Returns:
            Created session result dict
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO session_results (
                        user_id, session_type, duration_seconds, words_spoken,
                        pronunciation_score, fluency_score, grammar_score,
                        topics, vocabulary_learned, areas_to_improve, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    user_id,
                    session_type,
                    duration_seconds,
                    words_spoken,
                    pronunciation_score,
                    fluency_score,
                    grammar_score,
                    topics or [],
                    vocabulary_learned or [],
                    areas_to_improve or [],
                    psycopg.types.json.Json(metadata or {})
                ))
                return cur.fetchone()

    def get_session_history(
        self,
        user_id: uuid.UUID,
        session_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get user's session history with optional filtering.

        Args:
            user_id: User UUID
            session_type: Optional filter by session type
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of session result dicts
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if session_type:
                    cur.execute("""
                        SELECT *
                        FROM session_results
                        WHERE user_id = %s AND session_type = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, session_type, limit, offset))
                else:
                    cur.execute("""
                        SELECT *
                        FROM session_results
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, limit, offset))
                return cur.fetchall()

    def get_session_stats(
        self,
        user_id: uuid.UUID,
        period: str = 'week'
    ) -> Dict[str, Any]:
        """
        Get aggregated session statistics for a user.

        Args:
            user_id: User UUID
            period: Time period ('week' or 'month')

        Returns:
            Dict with aggregated stats including:
            - total_sessions: Total number of sessions
            - total_duration: Total duration in seconds
            - avg_pronunciation: Average pronunciation score
            - avg_fluency: Average fluency score
            - avg_grammar: Average grammar score
            - sessions_by_type: Breakdown by session type
            - improvement_trends: Score trends over time
            - common_topics: Most common topics
            - areas_to_improve: Aggregated weak areas
        """
        days = 7 if period == 'week' else 30

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get aggregate stats
                cur.execute("""
                    SELECT
                        COUNT(*)::INTEGER as total_sessions,
                        COALESCE(SUM(duration_seconds), 0)::INTEGER as total_duration,
                        COALESCE(AVG(pronunciation_score), 0)::FLOAT as avg_pronunciation,
                        COALESCE(AVG(fluency_score), 0)::FLOAT as avg_fluency,
                        COALESCE(AVG(grammar_score), 0)::FLOAT as avg_grammar,
                        COALESCE(SUM(words_spoken), 0)::INTEGER as total_words_spoken
                    FROM session_results
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                """, (user_id, days))
                stats = cur.fetchone()

                # Get sessions by type
                cur.execute("""
                    SELECT
                        session_type,
                        COUNT(*)::INTEGER as count,
                        COALESCE(AVG(duration_seconds), 0)::INTEGER as avg_duration
                    FROM session_results
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY session_type
                """, (user_id, days))
                sessions_by_type = {
                    row['session_type']: {
                        'count': row['count'],
                        'avg_duration': row['avg_duration']
                    }
                    for row in cur.fetchall()
                }

                # Get daily score trends for improvement analysis
                cur.execute("""
                    SELECT
                        DATE(created_at) as date,
                        COALESCE(AVG(pronunciation_score), 0)::FLOAT as avg_pronunciation,
                        COALESCE(AVG(fluency_score), 0)::FLOAT as avg_fluency,
                        COALESCE(AVG(grammar_score), 0)::FLOAT as avg_grammar
                    FROM session_results
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY DATE(created_at)
                    ORDER BY date ASC
                """, (user_id, days))
                trends = [
                    {
                        'date': row['date'].isoformat() if row['date'] else None,
                        'pronunciation': row['avg_pronunciation'],
                        'fluency': row['avg_fluency'],
                        'grammar': row['avg_grammar']
                    }
                    for row in cur.fetchall()
                ]

                # Get most common topics
                cur.execute("""
                    SELECT UNNEST(topics) as topic, COUNT(*) as count
                    FROM session_results
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                        AND topics IS NOT NULL
                    GROUP BY topic
                    ORDER BY count DESC
                    LIMIT 10
                """, (user_id, days))
                common_topics = [
                    {'topic': row['topic'], 'count': row['count']}
                    for row in cur.fetchall()
                ]

                # Get aggregated areas to improve
                cur.execute("""
                    SELECT UNNEST(areas_to_improve) as area, COUNT(*) as count
                    FROM session_results
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                        AND areas_to_improve IS NOT NULL
                    GROUP BY area
                    ORDER BY count DESC
                    LIMIT 10
                """, (user_id, days))
                areas_to_improve = [
                    {'area': row['area'], 'count': row['count']}
                    for row in cur.fetchall()
                ]

                return {
                    'total_sessions': stats['total_sessions'] if stats else 0,
                    'total_duration': stats['total_duration'] if stats else 0,
                    'total_words_spoken': stats['total_words_spoken'] if stats else 0,
                    'avg_pronunciation': stats['avg_pronunciation'] if stats else 0.0,
                    'avg_fluency': stats['avg_fluency'] if stats else 0.0,
                    'avg_grammar': stats['avg_grammar'] if stats else 0.0,
                    'sessions_by_type': sessions_by_type,
                    'improvement_trends': trends,
                    'common_topics': common_topics,
                    'areas_to_improve': areas_to_improve
                }

    def get_warmup_content(
        self,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get personalized warmup content based on user's recent session performance.

        Args:
            user_id: User UUID

        Returns:
            Dict with warmup content:
            - practice_phrases: List of phrases to practice
            - focus_areas: List of areas to focus on
            - quick_quiz: List of quiz questions
            - last_session_summary: Summary of last session
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get last session
                cur.execute("""
                    SELECT *
                    FROM session_results
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id,))
                last_session = cur.fetchone()

                # Get weak areas from recent sessions
                cur.execute("""
                    SELECT UNNEST(areas_to_improve) as area, COUNT(*) as frequency
                    FROM session_results
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '7 days'
                        AND areas_to_improve IS NOT NULL
                    GROUP BY area
                    ORDER BY frequency DESC
                    LIMIT 5
                """, (user_id,))
                weak_areas = [row['area'] for row in cur.fetchall()]

                # Get vocabulary that needs reinforcement
                cur.execute("""
                    SELECT UNNEST(vocabulary_learned) as word, COUNT(*) as seen
                    FROM session_results
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '7 days'
                        AND vocabulary_learned IS NOT NULL
                    GROUP BY word
                    ORDER BY seen ASC
                    LIMIT 10
                """, (user_id,))
                vocab_to_practice = [row['word'] for row in cur.fetchall()]

                warmup_content = {
                    'focus_areas': weak_areas,
                    'vocabulary_review': vocab_to_practice,
                    'last_session_summary': None
                }

                if last_session:
                    warmup_content['last_session_summary'] = {
                        'session_type': last_session['session_type'],
                        'duration_seconds': last_session['duration_seconds'],
                        'pronunciation_score': last_session['pronunciation_score'],
                        'fluency_score': last_session['fluency_score'],
                        'grammar_score': last_session['grammar_score'],
                        'areas_to_improve': last_session['areas_to_improve'],
                        'created_at': last_session['created_at'].isoformat() if last_session['created_at'] else None
                    }

                return warmup_content

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

    def record_activity(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Record user activity and update their streak.

        This calls the database stored function `update_user_streak` which:
        - If first activity: creates streak record with 1 day
        - If already logged today: does nothing
        - If continuing from yesterday: increments streak
        - If streak broken (gap > 1 day): resets to 1

        Args:
            user_id: User UUID

        Returns:
            Updated streak dict with current_streak, longest_streak, last_active_date
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Call the stored function to update streak
                cur.execute("SELECT update_user_streak(%s)", (user_id,))

                # Now fetch the updated streak data
                cur.execute("""
                    SELECT
                        current_streak_days,
                        longest_streak_days,
                        last_activity_date,
                        total_days_active,
                        freeze_days_available
                    FROM user_streaks
                    WHERE user_id = %s
                """, (user_id,))
                result = cur.fetchone()

                if result:
                    return {
                        "current_streak": result["current_streak_days"],
                        "longest_streak": result["longest_streak_days"],
                        "last_active_date": result["last_activity_date"].isoformat() if result["last_activity_date"] else None,
                        "total_days_active": result["total_days_active"],
                        "freeze_days_available": result["freeze_days_available"],
                    }

                # Should not happen, but fallback
                return {
                    "current_streak": 1,
                    "longest_streak": 1,
                    "last_active_date": datetime.now().date().isoformat(),
                    "total_days_active": 1,
                    "freeze_days_available": 2,
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

    # Leaderboards

    def get_weekly_leaderboard(self, limit: int = 50, current_user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """
        Get top users by XP gained this week.

        Args:
            limit: Maximum number of users to return
            current_user_id: Optional user ID to include their rank even if not in top 50

        Returns:
            Dict with leaderboard entries and current user's rank
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get start of current week (Monday)
                cur.execute("""
                    WITH week_xp AS (
                        SELECT
                            up.user_id,
                            COALESCE(up.full_name, 'User') as display_name,
                            up.level,
                            COALESCE(SUM(
                                CASE
                                    WHEN s.completed_at >= DATE_TRUNC('week', NOW()) THEN 10
                                    ELSE 0
                                END
                            ), 0) as xp_this_week
                        FROM user_profiles up
                        LEFT JOIN sessions s ON up.user_id = s.user_id AND s.state = 'completed'
                        GROUP BY up.user_id, up.full_name, up.level
                    ),
                    ranked AS (
                        SELECT
                            user_id,
                            display_name,
                            xp_this_week,
                            level,
                            ROW_NUMBER() OVER (ORDER BY xp_this_week DESC, user_id) as rank
                        FROM week_xp
                        WHERE xp_this_week > 0
                    )
                    SELECT * FROM ranked
                    WHERE rank <= %s
                    ORDER BY rank
                """, (limit,))
                leaderboard = cur.fetchall()

                # Get current user's rank if not in top 50
                current_user_rank = None
                if current_user_id:
                    cur.execute("""
                        WITH week_xp AS (
                            SELECT
                                up.user_id,
                                COALESCE(up.full_name, 'User') as display_name,
                                up.level,
                                COALESCE(SUM(
                                    CASE
                                        WHEN s.completed_at >= DATE_TRUNC('week', NOW()) THEN 10
                                        ELSE 0
                                    END
                                ), 0) as xp_this_week
                            FROM user_profiles up
                            LEFT JOIN sessions s ON up.user_id = s.user_id AND s.state = 'completed'
                            GROUP BY up.user_id, up.full_name, up.level
                        ),
                        ranked AS (
                            SELECT
                                user_id,
                                display_name,
                                xp_this_week,
                                level,
                                ROW_NUMBER() OVER (ORDER BY xp_this_week DESC, user_id) as rank
                            FROM week_xp
                        )
                        SELECT * FROM ranked WHERE user_id = %s
                    """, (current_user_id,))
                    current_user_rank = cur.fetchone()

                return {
                    "leaderboard": leaderboard,
                    "current_user": current_user_rank
                }

    def get_monthly_leaderboard(self, limit: int = 50, current_user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """
        Get top users by XP gained this month.

        Args:
            limit: Maximum number of users to return
            current_user_id: Optional user ID to include their rank even if not in top 50

        Returns:
            Dict with leaderboard entries and current user's rank
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH month_xp AS (
                        SELECT
                            up.user_id,
                            COALESCE(up.full_name, 'User') as display_name,
                            up.level,
                            COALESCE(SUM(
                                CASE
                                    WHEN s.completed_at >= DATE_TRUNC('month', NOW()) THEN 10
                                    ELSE 0
                                END
                            ), 0) as xp_this_month
                        FROM user_profiles up
                        LEFT JOIN sessions s ON up.user_id = s.user_id AND s.state = 'completed'
                        GROUP BY up.user_id, up.full_name, up.level
                    ),
                    ranked AS (
                        SELECT
                            user_id,
                            display_name,
                            xp_this_month,
                            level,
                            ROW_NUMBER() OVER (ORDER BY xp_this_month DESC, user_id) as rank
                        FROM month_xp
                        WHERE xp_this_month > 0
                    )
                    SELECT * FROM ranked
                    WHERE rank <= %s
                    ORDER BY rank
                """, (limit,))
                leaderboard = cur.fetchall()

                current_user_rank = None
                if current_user_id:
                    cur.execute("""
                        WITH month_xp AS (
                            SELECT
                                up.user_id,
                                COALESCE(up.full_name, 'User') as display_name,
                                up.level,
                                COALESCE(SUM(
                                    CASE
                                        WHEN s.completed_at >= DATE_TRUNC('month', NOW()) THEN 10
                                        ELSE 0
                                    END
                                ), 0) as xp_this_month
                            FROM user_profiles up
                            LEFT JOIN sessions s ON up.user_id = s.user_id AND s.state = 'completed'
                            GROUP BY up.user_id, up.full_name, up.level
                        ),
                        ranked AS (
                            SELECT
                                user_id,
                                display_name,
                                xp_this_month,
                                level,
                                ROW_NUMBER() OVER (ORDER BY xp_this_month DESC, user_id) as rank
                            FROM month_xp
                        )
                        SELECT * FROM ranked WHERE user_id = %s
                    """, (current_user_id,))
                    current_user_rank = cur.fetchone()

                return {
                    "leaderboard": leaderboard,
                    "current_user": current_user_rank
                }

    def get_alltime_leaderboard(self, limit: int = 50, current_user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """
        Get top users by total XP (all time).

        Args:
            limit: Maximum number of users to return
            current_user_id: Optional user ID to include their rank even if not in top 50

        Returns:
            Dict with leaderboard entries and current user's rank
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH total_xp AS (
                        SELECT
                            up.user_id,
                            COALESCE(up.full_name, 'User') as display_name,
                            up.level,
                            COALESCE(COUNT(s.session_id) * 10, 0) as total_xp
                        FROM user_profiles up
                        LEFT JOIN sessions s ON up.user_id = s.user_id AND s.state = 'completed'
                        GROUP BY up.user_id, up.full_name, up.level
                    ),
                    ranked AS (
                        SELECT
                            user_id,
                            display_name,
                            total_xp,
                            level,
                            ROW_NUMBER() OVER (ORDER BY total_xp DESC, user_id) as rank
                        FROM total_xp
                        WHERE total_xp > 0
                    )
                    SELECT * FROM ranked
                    WHERE rank <= %s
                    ORDER BY rank
                """, (limit,))
                leaderboard = cur.fetchall()

                current_user_rank = None
                if current_user_id:
                    cur.execute("""
                        WITH total_xp AS (
                            SELECT
                                up.user_id,
                                COALESCE(up.full_name, 'User') as display_name,
                                up.level,
                                COALESCE(COUNT(s.session_id) * 10, 0) as total_xp
                            FROM user_profiles up
                            LEFT JOIN sessions s ON up.user_id = s.user_id AND s.state = 'completed'
                            GROUP BY up.user_id, up.full_name, up.level
                        ),
                        ranked AS (
                            SELECT
                                user_id,
                                display_name,
                                total_xp,
                                level,
                                ROW_NUMBER() OVER (ORDER BY total_xp DESC, user_id) as rank
                            FROM total_xp
                        )
                        SELECT * FROM ranked WHERE user_id = %s
                    """, (current_user_id,))
                    current_user_rank = cur.fetchone()

                return {
                    "leaderboard": leaderboard,
                    "current_user": current_user_rank
                }

    def get_streak_leaderboard(self, limit: int = 50, current_user_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """
        Get top users by current streak.

        Args:
            limit: Maximum number of users to return
            current_user_id: Optional user ID to include their rank even if not in top 50

        Returns:
            Dict with leaderboard entries and current user's rank
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH streak_data AS (
                        SELECT
                            up.user_id,
                            COALESCE(up.full_name, 'User') as display_name,
                            up.level,
                            COALESCE(us.current_streak_days, 0) as current_streak
                        FROM user_profiles up
                        LEFT JOIN user_streaks us ON up.user_id = us.user_id
                    ),
                    ranked AS (
                        SELECT
                            user_id,
                            display_name,
                            current_streak,
                            level,
                            ROW_NUMBER() OVER (ORDER BY current_streak DESC, user_id) as rank
                        FROM streak_data
                        WHERE current_streak > 0
                    )
                    SELECT * FROM ranked
                    WHERE rank <= %s
                    ORDER BY rank
                """, (limit,))
                leaderboard = cur.fetchall()

                current_user_rank = None
                if current_user_id:
                    cur.execute("""
                        WITH streak_data AS (
                            SELECT
                                up.user_id,
                                COALESCE(up.full_name, 'User') as display_name,
                                up.level,
                                COALESCE(us.current_streak_days, 0) as current_streak
                            FROM user_profiles up
                            LEFT JOIN user_streaks us ON up.user_id = us.user_id
                        ),
                        ranked AS (
                            SELECT
                                user_id,
                                display_name,
                                current_streak,
                                level,
                                ROW_NUMBER() OVER (ORDER BY current_streak DESC, user_id) as rank
                            FROM streak_data
                        )
                        SELECT * FROM ranked WHERE user_id = %s
                    """, (current_user_id,))
                    current_user_rank = cur.fetchone()

                return {
                    "leaderboard": leaderboard,
                    "current_user": current_user_rank
                }

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

    # Notifications

    def create_notification(
        self,
        user_id: uuid.UUID,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """
        Create a notification for a user.

        Args:
            user_id: User UUID
            notification_type: Type of notification (streak_risk, achievement, goal_complete, etc.)
            title: Notification title
            message: Notification message
            action_url: Optional URL to navigate to when clicked
            metadata: Optional additional data

        Returns:
            Created notification UUID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT create_notification(%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    notification_type,
                    title,
                    message,
                    action_url,
                    psycopg.types.json.Json(metadata or {})
                ))
                result = cur.fetchone()
                return result['create_notification']

    def get_notifications(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user (paginated, unread first).

        Args:
            user_id: User UUID
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            unread_only: If True, only return unread notifications

        Returns:
            List of notification dicts
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if unread_only:
                    cur.execute("""
                        SELECT * FROM user_notifications
                        WHERE user_id = %s AND read = FALSE
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, limit, offset))
                else:
                    cur.execute("""
                        SELECT * FROM user_notifications
                        WHERE user_id = %s
                        ORDER BY read ASC, created_at DESC
                        LIMIT %s OFFSET %s
                    """, (user_id, limit, offset))
                return cur.fetchall()

    def mark_notification_read(self, notification_id: uuid.UUID) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification UUID

        Returns:
            True if marked as read, False if not found or already read
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT mark_notification_read(%s)
                """, (notification_id,))
                # Check if the notification exists
                cur.execute("""
                    SELECT 1 FROM user_notifications WHERE notification_id = %s
                """, (notification_id,))
                return cur.fetchone() is not None

    def mark_all_notifications_read(self, user_id: uuid.UUID) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of notifications marked as read
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT mark_all_notifications_read(%s)
                """, (user_id,))
                result = cur.fetchone()
                return result['mark_all_notifications_read'] if result else 0

    def get_unread_notification_count(self, user_id: uuid.UUID) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of unread notifications
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT get_unread_notification_count(%s)
                """, (user_id,))
                result = cur.fetchone()
                return result['get_unread_notification_count'] if result else 0

    def notify_level_up(
        self,
        user_id: uuid.UUID,
        old_level: str,
        new_level: str
    ) -> None:
        """
        Create a level up notification for a user.

        Args:
            user_id: User UUID
            old_level: Previous CEFR level
            new_level: New CEFR level
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT notify_level_up(%s, %s, %s)
                """, (user_id, old_level, new_level))

    # Daily Challenges

    def get_daily_challenge(self, challenge_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get the daily challenge for a specific date (defaults to today).
        The same challenge is shown to all users for a given date.

        Args:
            challenge_date: Date for the challenge (defaults to today UTC)

        Returns:
            Daily challenge dict with type, description, goal, and reward_xp
        """
        if challenge_date is None:
            challenge_date = datetime.utcnow().date()
        elif isinstance(challenge_date, datetime):
            challenge_date = challenge_date.date()

        # Generate deterministic challenge based on date
        # Use date as seed to ensure same challenge for all users on same day
        import hashlib
        date_str = challenge_date.isoformat()
        hash_val = int(hashlib.md5(date_str.encode()).hexdigest(), 16)

        # Define challenge types
        challenges = [
            {
                "type": "complete_exercises",
                "title": "Exercise Champion",
                "description": "Complete 5 exercises today",
                "goal": 5,
                "reward_xp": 50,
                "icon": "target"
            },
            {
                "type": "correct_streak",
                "title": "Perfect Streak",
                "description": "Get 3 correct answers in a row",
                "goal": 3,
                "reward_xp": 40,
                "icon": "zap"
            },
            {
                "type": "study_time",
                "title": "Time Master",
                "description": "Practice for 10 minutes",
                "goal": 10,
                "reward_xp": 60,
                "icon": "clock"
            },
            {
                "type": "voice_tutor",
                "title": "Speaking Star",
                "description": "Try the voice tutor",
                "goal": 1,
                "reward_xp": 45,
                "icon": "mic"
            },
            {
                "type": "complete_reviews",
                "title": "Review Master",
                "description": "Complete 10 SRS card reviews",
                "goal": 10,
                "reward_xp": 50,
                "icon": "book"
            },
            {
                "type": "chat_turns",
                "title": "Conversation King",
                "description": "Have a 5-turn conversation with the AI tutor",
                "goal": 5,
                "reward_xp": 55,
                "icon": "message"
            },
        ]

        # Select challenge based on date hash
        challenge = challenges[hash_val % len(challenges)]

        return {
            **challenge,
            "date": date_str,
            "expires_at": f"{date_str}T23:59:59Z"
        }

    def get_user_challenge_progress(
        self,
        user_id: uuid.UUID,
        challenge_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's progress on today's challenge.

        Args:
            user_id: User UUID
            challenge_date: Date for the challenge (defaults to today UTC)

        Returns:
            Challenge progress dict or None if not started
        """
        if challenge_date is None:
            challenge_date = datetime.utcnow().date()
        elif isinstance(challenge_date, datetime):
            challenge_date = challenge_date.date()

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM daily_challenge_progress
                    WHERE user_id = %s AND challenge_date = %s
                """, (user_id, challenge_date))
                return cur.fetchone()

    def update_challenge_progress(
        self,
        user_id: uuid.UUID,
        challenge_type: str,
        progress: int,
        challenge_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update user's progress on daily challenge.

        Args:
            user_id: User UUID
            challenge_type: Type of challenge
            progress: Current progress value
            challenge_date: Date for the challenge (defaults to today UTC)

        Returns:
            Updated challenge progress dict
        """
        if challenge_date is None:
            challenge_date = datetime.utcnow().date()
        elif isinstance(challenge_date, datetime):
            challenge_date = challenge_date.date()

        # Get the challenge definition
        challenge = self.get_daily_challenge(challenge_date)

        # Check if this is the right challenge type for today
        if challenge["type"] != challenge_type:
            # Wrong challenge type for today, don't update
            return self.get_user_challenge_progress(user_id, challenge_date) or {}

        goal = challenge["goal"]
        completed = progress >= goal

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO daily_challenge_progress (
                        user_id, challenge_date, challenge_type, progress, goal, completed
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, challenge_date)
                    DO UPDATE SET
                        progress = GREATEST(daily_challenge_progress.progress, EXCLUDED.progress),
                        completed = (GREATEST(daily_challenge_progress.progress, EXCLUDED.progress) >= EXCLUDED.goal),
                        updated_at = NOW()
                    RETURNING *
                """, (user_id, challenge_date, challenge_type, progress, goal, completed))
                return cur.fetchone()

    def complete_daily_challenge(
        self,
        user_id: uuid.UUID,
        challenge_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Mark daily challenge as complete and award bonus XP.

        Args:
            user_id: User UUID
            challenge_date: Date for the challenge (defaults to today UTC)

        Returns:
            Completed challenge record or None if already completed
        """
        if challenge_date is None:
            challenge_date = datetime.utcnow().date()
        elif isinstance(challenge_date, datetime):
            challenge_date = challenge_date.date()

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if already completed
                cur.execute("""
                    SELECT completed FROM daily_challenge_progress
                    WHERE user_id = %s AND challenge_date = %s
                """, (user_id, challenge_date))
                result = cur.fetchone()

                if result and result['completed']:
                    return None  # Already completed

                # Mark as complete
                cur.execute("""
                    UPDATE daily_challenge_progress
                    SET completed = TRUE, completed_at = NOW(), updated_at = NOW()
                    WHERE user_id = %s AND challenge_date = %s AND progress >= goal
                    RETURNING *
                """, (user_id, challenge_date))

                return cur.fetchone()

    def get_challenge_history(
        self,
        user_id: uuid.UUID,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user's challenge completion history.

        Args:
            user_id: User UUID
            limit: Maximum number of records to return

        Returns:
            List of challenge progress records
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM daily_challenge_progress
                    WHERE user_id = %s
                    ORDER BY challenge_date DESC
                    LIMIT %s
                """, (user_id, limit))
                return cur.fetchall()

    def get_challenge_streak(self, user_id: uuid.UUID) -> int:
        """
        Get user's current daily challenge completion streak.

        Args:
            user_id: User UUID

        Returns:
            Number of consecutive days with completed challenges
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH RECURSIVE date_series AS (
                        SELECT CURRENT_DATE as check_date, 0 as days_back
                        UNION ALL
                        SELECT check_date - 1, days_back + 1
                        FROM date_series
                        WHERE days_back < 365
                    )
                    SELECT COUNT(*) as streak
                    FROM date_series ds
                    LEFT JOIN daily_challenge_progress dcp
                        ON dcp.user_id = %s
                        AND dcp.challenge_date = ds.check_date
                        AND dcp.completed = TRUE
                    WHERE ds.check_date <= CURRENT_DATE
                        AND dcp.completed IS NOT NULL
                        AND NOT EXISTS (
                            SELECT 1 FROM date_series ds2
                            LEFT JOIN daily_challenge_progress dcp2
                                ON dcp2.user_id = %s
                                AND dcp2.challenge_date = ds2.check_date
                                AND dcp2.completed = TRUE
                            WHERE ds2.check_date > ds.check_date
                                AND ds2.check_date <= CURRENT_DATE
                                AND dcp2.completed IS NULL
                        )
                """, (user_id, user_id))
                result = cur.fetchone()
                return result['streak'] if result else 0

    # Conversation Memory

    def save_conversation_turn(
        self,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        turn_number: int,
        user_message: str,
        tutor_response: str,
        context_type: Optional[str] = None,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> uuid.UUID:
        """
        Save a conversation turn to the database.

        Args:
            user_id: User UUID
            session_id: Session UUID
            turn_number: Sequential turn number in the session
            user_message: User's message text
            tutor_response: Tutor's response text
            context_type: Type of context (scenario, lesson, free_chat, etc.)
            context_id: ID of the specific context (scenario_id, lesson_id, etc.)
            metadata: Additional metadata (errors, topics, etc.)

        Returns:
            Created conversation UUID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT save_conversation_turn(%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    session_id,
                    turn_number,
                    user_message,
                    tutor_response,
                    context_type,
                    context_id,
                    psycopg.types.json.Json(metadata or {})
                ))
                result = cur.fetchone()
                return result['save_conversation_turn']

    def get_recent_conversations(
        self,
        user_id: uuid.UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation turns for a user.

        Args:
            user_id: User UUID
            limit: Maximum number of turns to return

        Returns:
            List of conversation turn dicts
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM get_recent_conversations(%s, %s)
                """, (user_id, limit))
                return cur.fetchall()

    def get_session_conversations(
        self,
        session_id: uuid.UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get conversation turns for a specific session.
        This is used to maintain context within a single conversation session.

        Args:
            session_id: Session UUID
            limit: Maximum number of turns to return

        Returns:
            List of conversation turn dicts ordered by turn_number
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        turn_id,
                        user_id,
                        session_id,
                        turn_number,
                        user_message,
                        tutor_response,
                        context_type,
                        context_id,
                        metadata,
                        created_at
                    FROM conversation_memory
                    WHERE session_id = %s
                    ORDER BY turn_number ASC
                    LIMIT %s
                """, (session_id, limit))
                return cur.fetchall()

    def get_conversation_context(
        self,
        user_id: uuid.UUID,
        lookback_days: int = 7,
        limit: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation context summary for a user.

        Provides summary of recent conversations including:
        - Total conversation count
        - Recent topics/contexts
        - Most active context type

        Args:
            user_id: User UUID
            lookback_days: Number of days to look back
            limit: Limit for recent conversations

        Returns:
            Context summary dict or None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM get_conversation_context(%s, %s, %s)
                """, (user_id, lookback_days, limit))
                result = cur.fetchone()
                if result:
                    return {
                        "total_conversations": result['total_conversations'],
                        "recent_topics": result['recent_topics'],
                        "context_summary": result['context_summary']
                    }
                return None

    def get_conversation_by_context(
        self,
        user_id: uuid.UUID,
        context_type: str,
        context_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversations filtered by context type and optional context ID.

        Args:
            user_id: User UUID
            context_type: Context type (scenario, lesson, free_chat, etc.)
            context_id: Optional specific context ID
            limit: Maximum number of turns to return

        Returns:
            List of conversation turn dicts
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM get_conversation_by_context(%s, %s, %s, %s)
                """, (user_id, context_type, context_id, limit))
                return cur.fetchall()

    def clear_conversation_history(
        self,
        user_id: uuid.UUID,
        before_date: Optional[datetime] = None
    ) -> int:
        """
        Clear conversation history for a user.

        Args:
            user_id: User UUID
            before_date: Optional date - only clear conversations before this date

        Returns:
            Number of conversations deleted
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT clear_conversation_history(%s, %s)
                """, (user_id, before_date))
                result = cur.fetchone()
                return result['clear_conversation_history'] if result else 0

    # Daily Challenges

    def get_daily_challenges(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get or create today's daily challenges for a user.

        Args:
            user_id: User UUID

        Returns:
            Daily challenges dict with all 3 challenges and their progress
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Try to get existing challenges for today
                cur.execute("""
                    SELECT * FROM daily_challenges
                    WHERE user_id = %s AND challenge_date = CURRENT_DATE
                """, (user_id,))
                result = cur.fetchone()

                # If no challenges exist, create them
                if not result:
                    cur.execute("""
                        INSERT INTO daily_challenges (user_id, challenge_date)
                        VALUES (%s, CURRENT_DATE)
                        ON CONFLICT (user_id, challenge_date) DO NOTHING
                        RETURNING *
                    """, (user_id,))
                    result = cur.fetchone()

                    # Fetch again if INSERT didn't return (concurrent insert)
                    if not result:
                        cur.execute("""
                            SELECT * FROM daily_challenges
                            WHERE user_id = %s AND challenge_date = CURRENT_DATE
                        """, (user_id,))
                        result = cur.fetchone()

                return dict(result) if result else None

    def update_daily_challenge_progress(
        self,
        user_id: uuid.UUID,
        lessons_completed: int = 0,
        best_score: int = 0,
        xp_earned: int = 0,
        speaking_sessions: int = 0
    ) -> Dict[str, Any]:
        """
        Update daily challenge progress and check for completions.

        Args:
            user_id: User UUID
            lessons_completed: Number of lessons completed this update
            best_score: Best score achieved this update
            xp_earned: XP earned this update
            speaking_sessions: Number of speaking sessions this update

        Returns:
            Dict with completion status and rewards
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Ensure today's challenges exist
                cur.execute("""
                    INSERT INTO daily_challenges (user_id, challenge_date)
                    VALUES (%s, CURRENT_DATE)
                    ON CONFLICT (user_id, challenge_date) DO NOTHING
                """, (user_id,))

                # Get current state
                cur.execute("""
                    SELECT * FROM daily_challenges
                    WHERE user_id = %s AND challenge_date = CURRENT_DATE
                """, (user_id,))
                challenge = cur.fetchone()

                if not challenge:
                    return {"error": "Could not find or create daily challenges"}

                result = {
                    "core_just_completed": False,
                    "accuracy_just_completed": False,
                    "stretch_just_completed": False,
                    "total_xp_earned": 0,
                    "earned_freeze_token": False
                }

                # Update Core Challenge (lessons completed)
                if not challenge['core_completed'] and lessons_completed > 0:
                    new_progress = challenge['core_progress'] + lessons_completed
                    cur.execute("""
                        UPDATE daily_challenges
                        SET core_progress = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_progress, challenge['id']))

                    if new_progress >= challenge['core_target']:
                        cur.execute("""
                            UPDATE daily_challenges
                            SET core_completed = TRUE, core_completed_at = NOW()
                            WHERE id = %s
                        """, (challenge['id'],))
                        result['core_just_completed'] = True
                        result['total_xp_earned'] += challenge['core_xp_reward']

                # Update Accuracy Challenge (best score)
                if not challenge['accuracy_completed'] and best_score > 0:
                    new_progress = max(challenge['accuracy_progress'], best_score)
                    cur.execute("""
                        UPDATE daily_challenges
                        SET accuracy_progress = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_progress, challenge['id']))

                    if best_score >= challenge['accuracy_target']:
                        cur.execute("""
                            UPDATE daily_challenges
                            SET accuracy_completed = TRUE, accuracy_completed_at = NOW()
                            WHERE id = %s
                        """, (challenge['id'],))
                        result['accuracy_just_completed'] = True
                        result['total_xp_earned'] += challenge['accuracy_xp_reward']

                # Update Stretch Challenge (XP or speaking)
                if not challenge['stretch_completed']:
                    new_xp_progress = challenge['stretch_xp_progress'] + xp_earned
                    new_speaking_progress = challenge['stretch_speaking_progress'] + speaking_sessions
                    cur.execute("""
                        UPDATE daily_challenges
                        SET stretch_xp_progress = %s, stretch_speaking_progress = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (new_xp_progress, new_speaking_progress, challenge['id']))

                    if new_xp_progress >= challenge['stretch_xp_target'] or \
                       new_speaking_progress >= challenge['stretch_speaking_target']:
                        cur.execute("""
                            UPDATE daily_challenges
                            SET stretch_completed = TRUE, stretch_completed_at = NOW()
                            WHERE id = %s
                        """, (challenge['id'],))
                        result['stretch_just_completed'] = True
                        result['total_xp_earned'] += challenge['stretch_xp_reward']

                        # Grant streak freeze token
                        if challenge['stretch_gives_freeze_token']:
                            cur.execute("""
                                INSERT INTO streak_freeze_tokens (user_id)
                                VALUES (%s)
                            """, (user_id,))
                            result['earned_freeze_token'] = True

                # Check if all completed
                cur.execute("""
                    UPDATE daily_challenges
                    SET all_completed = (core_completed AND accuracy_completed AND stretch_completed)
                    WHERE id = %s
                """, (challenge['id'],))

                return result

    def get_streak_freeze_count(self, user_id: uuid.UUID) -> int:
        """
        Get number of available streak freeze tokens for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of unused freeze tokens
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) as count FROM streak_freeze_tokens
                    WHERE user_id = %s AND used = FALSE
                """, (user_id,))
                result = cur.fetchone()
                return result['count'] if result else 0

    def use_streak_freeze_token(self, user_id: uuid.UUID) -> bool:
        """
        Use a streak freeze token.

        Args:
            user_id: User UUID

        Returns:
            True if a token was used, False if no tokens available
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Find the oldest unused token
                cur.execute("""
                    SELECT id FROM streak_freeze_tokens
                    WHERE user_id = %s AND used = FALSE
                    ORDER BY earned_at ASC
                    LIMIT 1
                """, (user_id,))
                result = cur.fetchone()

                if not result:
                    return False

                # Mark it as used
                cur.execute("""
                    UPDATE streak_freeze_tokens
                    SET used = TRUE, used_at = NOW()
                    WHERE id = %s
                """, (result['id'],))

                return True

    # ============================================================================
    # Friends System Methods
    # ============================================================================

    def get_user_friend_code(self, user_id: uuid.UUID) -> str:
        """
        Get or create friend code for a user.

        Args:
            user_id: User UUID

        Returns:
            8-character friend code
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if user already has a code
                cur.execute("SELECT friend_code FROM user_profiles WHERE user_id = %s", (user_id,))
                result = cur.fetchone()

                if result and result['friend_code']:
                    return result['friend_code']

                # Generate new code
                chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
                import random
                while True:
                    code = ''.join(random.choice(chars) for _ in range(8))
                    try:
                        cur.execute("""
                            UPDATE user_profiles SET friend_code = %s WHERE user_id = %s
                        """, (code, user_id))
                        return code
                    except Exception:
                        # Code collision, try again
                        continue

    def search_users(self, searcher_id: uuid.UUID, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search users by username, display name, or friend code.

        Args:
            searcher_id: ID of user performing search
            query: Search query
            limit: Max results

        Returns:
            List of matching users with friendship status
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        up.user_id,
                        up.username,
                        up.display_name,
                        up.friend_code,
                        up.level,
                        up.total_xp,
                        COALESCE(us.streak_days, 0) as streak_days,
                        EXISTS(
                            SELECT 1 FROM friendships f
                            WHERE ((f.user_id = %s AND f.friend_id = up.user_id)
                               OR (f.friend_id = %s AND f.user_id = up.user_id))
                              AND f.status = 'accepted'
                        ) as is_friend,
                        (
                            SELECT f.status FROM friendships f
                            WHERE (f.user_id = %s AND f.friend_id = up.user_id)
                               OR (f.friend_id = %s AND f.user_id = up.user_id)
                            LIMIT 1
                        ) as friendship_status
                    FROM user_profiles up
                    LEFT JOIN user_streaks us ON us.user_id = up.user_id
                    WHERE up.user_id != %s
                      AND (
                        LOWER(up.username) LIKE LOWER(%s)
                        OR LOWER(up.display_name) LIKE LOWER(%s)
                        OR UPPER(up.friend_code) = UPPER(%s)
                      )
                    ORDER BY
                        CASE WHEN UPPER(up.friend_code) = UPPER(%s) THEN 0 ELSE 1 END,
                        CASE WHEN LOWER(up.username) = LOWER(%s) THEN 0 ELSE 1 END,
                        up.total_xp DESC
                    LIMIT %s
                """, (
                    searcher_id, searcher_id, searcher_id, searcher_id, searcher_id,
                    query + '%', '%' + query + '%', query,
                    query, query, limit
                ))
                return [dict(row) for row in cur.fetchall()]

    def get_friends_list(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get list of friends with their today's stats.

        Args:
            user_id: User UUID

        Returns:
            List of friends with XP and lesson counts
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        up.user_id,
                        up.username,
                        up.display_name,
                        up.level,
                        up.total_xp,
                        COALESCE(us.streak_days, 0) as streak_days,
                        COALESCE(
                            (SELECT SUM(xp_earned)::INTEGER FROM xp_transactions
                             WHERE xp_transactions.user_id = up.user_id AND DATE(created_at) = CURRENT_DATE),
                            0
                        ) as xp_today,
                        COALESCE(
                            (SELECT COUNT(*)::INTEGER FROM learning_path_progress
                             WHERE learning_path_progress.user_id = up.user_id
                               AND DATE(completed_at) = CURRENT_DATE AND completed = TRUE),
                            0
                        ) as lessons_today,
                        f.accepted_at as friend_since
                    FROM friendships f
                    JOIN user_profiles up ON (
                        CASE WHEN f.user_id = %s THEN f.friend_id ELSE f.user_id END = up.user_id
                    )
                    LEFT JOIN user_streaks us ON us.user_id = up.user_id
                    WHERE (f.user_id = %s OR f.friend_id = %s)
                      AND f.status = 'accepted'
                    ORDER BY xp_today DESC, up.total_xp DESC
                """, (user_id, user_id, user_id))
                return [dict(row) for row in cur.fetchall()]

    def get_pending_friend_requests(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get pending friend requests received by user.

        Args:
            user_id: User UUID

        Returns:
            List of pending requests
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        f.id as request_id,
                        up.user_id,
                        up.username,
                        up.display_name,
                        up.level,
                        up.total_xp,
                        f.created_at as requested_at
                    FROM friendships f
                    JOIN user_profiles up ON f.user_id = up.user_id
                    WHERE f.friend_id = %s AND f.status = 'pending'
                    ORDER BY f.created_at DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    def send_friend_request(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> Dict[str, Any]:
        """
        Send a friend request or accept existing one.

        Args:
            user_id: ID of user sending request
            friend_id: ID of user receiving request

        Returns:
            Result with status
        """
        if user_id == friend_id:
            return {'success': False, 'error': 'Cannot add yourself'}

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Check for existing friendship
                cur.execute("""
                    SELECT * FROM friendships
                    WHERE (user_id = %s AND friend_id = %s)
                       OR (user_id = %s AND friend_id = %s)
                """, (user_id, friend_id, friend_id, user_id))
                existing = cur.fetchone()

                if existing:
                    if existing['status'] == 'accepted':
                        return {'success': False, 'error': 'Already friends'}
                    elif existing['status'] == 'blocked':
                        return {'success': False, 'error': 'Cannot add this user'}
                    elif existing['status'] == 'pending':
                        # If the other person sent request, accept it
                        if existing['user_id'] == friend_id:
                            cur.execute("""
                                UPDATE friendships
                                SET status = 'accepted', accepted_at = NOW()
                                WHERE id = %s
                            """, (existing['id'],))
                            return {'success': True, 'status': 'accepted'}
                        else:
                            return {'success': False, 'error': 'Request already sent'}

                # Create new request
                cur.execute("""
                    INSERT INTO friendships (user_id, friend_id, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id
                """, (user_id, friend_id))
                return {'success': True, 'status': 'pending'}

    def accept_friend_request(self, user_id: uuid.UUID, requester_id: uuid.UUID) -> bool:
        """
        Accept a friend request.

        Args:
            user_id: ID of user accepting
            requester_id: ID of user who sent request

        Returns:
            True if accepted successfully
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE friendships
                    SET status = 'accepted', accepted_at = NOW()
                    WHERE user_id = %s AND friend_id = %s AND status = 'pending'
                """, (requester_id, user_id))
                return cur.rowcount > 0

    def decline_friend_request(self, user_id: uuid.UUID, requester_id: uuid.UUID) -> bool:
        """
        Decline/delete a friend request.

        Args:
            user_id: ID of user declining
            requester_id: ID of user who sent request

        Returns:
            True if deleted successfully
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM friendships
                    WHERE user_id = %s AND friend_id = %s AND status = 'pending'
                """, (requester_id, user_id))
                return cur.rowcount > 0

    def remove_friend(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> bool:
        """
        Remove a friend.

        Args:
            user_id: User ID
            friend_id: Friend to remove

        Returns:
            True if removed successfully
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM friendships
                    WHERE ((user_id = %s AND friend_id = %s)
                       OR (user_id = %s AND friend_id = %s))
                      AND status = 'accepted'
                """, (user_id, friend_id, friend_id, user_id))
                return cur.rowcount > 0

    def get_friend_profile(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get detailed friend profile with 7-day activity.

        Args:
            user_id: ID of user viewing
            friend_id: ID of friend to view

        Returns:
            Friend profile with activity data
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get basic profile
                cur.execute("""
                    SELECT
                        up.user_id,
                        up.username,
                        up.display_name,
                        up.friend_code,
                        up.level,
                        up.total_xp,
                        COALESCE(us.streak_days, 0) as streak_days,
                        COALESCE(us.longest_streak, 0) as longest_streak,
                        EXISTS(
                            SELECT 1 FROM friendships f
                            WHERE ((f.user_id = %s AND f.friend_id = up.user_id)
                               OR (f.friend_id = %s AND f.user_id = up.user_id))
                              AND f.status = 'accepted'
                        ) as is_friend
                    FROM user_profiles up
                    LEFT JOIN user_streaks us ON us.user_id = up.user_id
                    WHERE up.user_id = %s
                """, (user_id, user_id, friend_id))
                profile = cur.fetchone()

                if not profile:
                    return None

                result = dict(profile)

                # Get today's stats
                cur.execute("""
                    SELECT COALESCE(SUM(xp_earned), 0)::INTEGER as xp_today
                    FROM xp_transactions
                    WHERE user_id = %s AND DATE(created_at) = CURRENT_DATE
                """, (friend_id,))
                xp_result = cur.fetchone()
                result['xp_today'] = xp_result['xp_today'] if xp_result else 0

                cur.execute("""
                    SELECT COUNT(*)::INTEGER as lessons_today
                    FROM learning_path_progress
                    WHERE user_id = %s AND DATE(completed_at) = CURRENT_DATE AND completed = TRUE
                """, (friend_id,))
                lessons_result = cur.fetchone()
                result['lessons_today'] = lessons_result['lessons_today'] if lessons_result else 0

                # Get last 7 days activity
                cur.execute("""
                    SELECT
                        d.day::DATE as date,
                        COALESCE(xp.total, 0) as xp,
                        COALESCE(lp.count, 0) as lessons
                    FROM generate_series(CURRENT_DATE - INTERVAL '6 days', CURRENT_DATE, '1 day') as d(day)
                    LEFT JOIN (
                        SELECT DATE(created_at) as day, SUM(xp_earned)::INTEGER as total
                        FROM xp_transactions
                        WHERE user_id = %s AND DATE(created_at) >= CURRENT_DATE - INTERVAL '6 days'
                        GROUP BY DATE(created_at)
                    ) xp ON xp.day = d.day::DATE
                    LEFT JOIN (
                        SELECT DATE(completed_at) as day, COUNT(*)::INTEGER as count
                        FROM learning_path_progress
                        WHERE user_id = %s AND DATE(completed_at) >= CURRENT_DATE - INTERVAL '6 days' AND completed = TRUE
                        GROUP BY DATE(completed_at)
                    ) lp ON lp.day = d.day::DATE
                    ORDER BY d.day
                """, (friend_id, friend_id))
                result['last_7_days_activity'] = [dict(row) for row in cur.fetchall()]

                return result

    def create_friend_challenge(self, challenger_id: uuid.UUID, challenged_id: uuid.UUID, challenge_type: str) -> Dict[str, Any]:
        """
        Create an async friend challenge.

        Args:
            challenger_id: ID of challenger
            challenged_id: ID of challenged friend
            challenge_type: 'beat_xp_today' or 'more_lessons_today'

        Returns:
            Challenge details or error
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Verify they are friends
                cur.execute("""
                    SELECT 1 FROM friendships
                    WHERE ((user_id = %s AND friend_id = %s)
                       OR (user_id = %s AND friend_id = %s))
                      AND status = 'accepted'
                """, (challenger_id, challenged_id, challenged_id, challenger_id))
                if not cur.fetchone():
                    return {'success': False, 'error': 'Users are not friends'}

                # Check for existing challenge today
                cur.execute("""
                    SELECT id FROM friend_challenges
                    WHERE challenger_id = %s
                      AND challenged_id = %s
                      AND challenge_type = %s
                      AND challenge_date = CURRENT_DATE
                      AND status IN ('pending', 'accepted')
                """, (challenger_id, challenged_id, challenge_type))
                if cur.fetchone():
                    return {'success': False, 'error': 'Challenge already exists for today'}

                # Create challenge
                cur.execute("""
                    INSERT INTO friend_challenges (challenger_id, challenged_id, challenge_type, challenge_date)
                    VALUES (%s, %s, %s, CURRENT_DATE)
                    RETURNING id, challenge_type, challenge_date, status, xp_reward
                """, (challenger_id, challenged_id, challenge_type))
                result = cur.fetchone()
                return {'success': True, 'challenge': dict(result)}

    def get_friend_challenges(self, user_id: uuid.UUID) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get friend challenges for a user (sent and received).

        Args:
            user_id: User UUID

        Returns:
            Dict with 'sent' and 'received' challenge lists
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get challenges sent by user
                cur.execute("""
                    SELECT
                        fc.*,
                        up.username as challenged_username,
                        up.display_name as challenged_display_name
                    FROM friend_challenges fc
                    JOIN user_profiles up ON up.user_id = fc.challenged_id
                    WHERE fc.challenger_id = %s
                      AND fc.challenge_date >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY fc.created_at DESC
                """, (user_id,))
                sent = [dict(row) for row in cur.fetchall()]

                # Get challenges received by user
                cur.execute("""
                    SELECT
                        fc.*,
                        up.username as challenger_username,
                        up.display_name as challenger_display_name
                    FROM friend_challenges fc
                    JOIN user_profiles up ON up.user_id = fc.challenger_id
                    WHERE fc.challenged_id = %s
                      AND fc.challenge_date >= CURRENT_DATE - INTERVAL '7 days'
                    ORDER BY fc.created_at DESC
                """, (user_id,))
                received = [dict(row) for row in cur.fetchall()]

                return {'sent': sent, 'received': received}

    def respond_to_challenge(self, user_id: uuid.UUID, challenge_id: uuid.UUID, accept: bool) -> bool:
        """
        Accept or decline a friend challenge.

        Args:
            user_id: ID of user responding
            challenge_id: Challenge ID
            accept: True to accept, False to decline

        Returns:
            True if successful
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                new_status = 'accepted' if accept else 'declined'
                cur.execute("""
                    UPDATE friend_challenges
                    SET status = %s, accepted_at = CASE WHEN %s THEN NOW() ELSE NULL END
                    WHERE id = %s AND challenged_id = %s AND status = 'pending'
                """, (new_status, accept, challenge_id, user_id))
                return cur.rowcount > 0

    def update_challenge_scores(self, challenge_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Update scores for a challenge and determine winner if complete.

        Args:
            challenge_id: Challenge ID

        Returns:
            Updated challenge data
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Get challenge
                cur.execute("SELECT * FROM friend_challenges WHERE id = %s", (challenge_id,))
                challenge = cur.fetchone()

                if not challenge or challenge['status'] not in ('pending', 'accepted'):
                    return None

                # Calculate scores based on challenge type
                if challenge['challenge_type'] == 'beat_xp_today':
                    cur.execute("""
                        SELECT COALESCE(SUM(xp_earned), 0)::INTEGER as score
                        FROM xp_transactions WHERE user_id = %s AND DATE(created_at) = %s
                    """, (challenge['challenger_id'], challenge['challenge_date']))
                    challenger_score = cur.fetchone()['score']

                    cur.execute("""
                        SELECT COALESCE(SUM(xp_earned), 0)::INTEGER as score
                        FROM xp_transactions WHERE user_id = %s AND DATE(created_at) = %s
                    """, (challenge['challenged_id'], challenge['challenge_date']))
                    challenged_score = cur.fetchone()['score']
                else:  # more_lessons_today
                    cur.execute("""
                        SELECT COUNT(*)::INTEGER as score
                        FROM learning_path_progress
                        WHERE user_id = %s AND DATE(completed_at) = %s AND completed = TRUE
                    """, (challenge['challenger_id'], challenge['challenge_date']))
                    challenger_score = cur.fetchone()['score']

                    cur.execute("""
                        SELECT COUNT(*)::INTEGER as score
                        FROM learning_path_progress
                        WHERE user_id = %s AND DATE(completed_at) = %s AND completed = TRUE
                    """, (challenge['challenged_id'], challenge['challenge_date']))
                    challenged_score = cur.fetchone()['score']

                # Determine winner if challenge day is over
                from datetime import date
                winner_id = None
                new_status = challenge['status']

                if challenge['challenge_date'] < date.today() and challenge['status'] == 'accepted':
                    if challenger_score > challenged_score:
                        winner_id = challenge['challenger_id']
                    elif challenged_score > challenger_score:
                        winner_id = challenge['challenged_id']
                    new_status = 'completed'

                # Update challenge
                cur.execute("""
                    UPDATE friend_challenges
                    SET challenger_score = %s, challenged_score = %s, winner_id = %s, status = %s,
                        completed_at = CASE WHEN %s = 'completed' THEN NOW() ELSE completed_at END
                    WHERE id = %s
                    RETURNING *
                """, (challenger_score, challenged_score, winner_id, new_status, new_status, challenge_id))
                return dict(cur.fetchone()) if cur.rowcount > 0 else None

    def use_friend_invite_link(self, invite_code: str, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Use a friend invite link to add friend.

        Args:
            invite_code: The invite code
            user_id: ID of user using the link

        Returns:
            Result with friend info or error
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Find the invite link
                cur.execute("""
                    SELECT fil.*, up.user_id as inviter_id, up.display_name as inviter_name
                    FROM friend_invite_links fil
                    JOIN user_profiles up ON up.user_id = fil.user_id
                    WHERE fil.invite_code = %s AND fil.is_active = TRUE
                      AND (fil.expires_at IS NULL OR fil.expires_at > NOW())
                      AND (fil.max_uses IS NULL OR fil.uses_count < fil.max_uses)
                """, (invite_code.upper(),))
                invite = cur.fetchone()

                if not invite:
                    return {'success': False, 'error': 'Invalid or expired invite link'}

                if invite['inviter_id'] == user_id:
                    return {'success': False, 'error': 'Cannot use your own invite link'}

                # Add friend (using send_friend_request logic)
                result = self.send_friend_request(user_id, invite['inviter_id'])

                if result['success']:
                    # Increment uses count
                    cur.execute("""
                        UPDATE friend_invite_links SET uses_count = uses_count + 1 WHERE id = %s
                    """, (invite['id'],))

                return {**result, 'inviter_name': invite['inviter_name']}

    def create_friend_invite_link(self, user_id: uuid.UUID) -> str:
        """
        Create a shareable friend invite link.

        Args:
            user_id: User creating the link

        Returns:
            12-character invite code
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
                import random
                while True:
                    code = ''.join(random.choice(chars) for _ in range(12))
                    try:
                        cur.execute("""
                            INSERT INTO friend_invite_links (user_id, invite_code)
                            VALUES (%s, %s)
                            RETURNING invite_code
                        """, (user_id, code))
                        return code
                    except Exception:
                        continue

    # ============================================================================
    # Activity Heatmap Methods
    # ============================================================================

    def get_activity_heatmap(self, user_id: uuid.UUID, days: int = 365) -> List[Dict[str, Any]]:
        """
        Get daily activity data for heatmap (past N days).

        Args:
            user_id: User UUID
            days: Number of days to look back (default 365)

        Returns:
            List of {date, xp, lessons, sessions} for each day
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        d.day::DATE as date,
                        COALESCE(xp.total, 0) as xp,
                        COALESCE(lp.count, 0) as lessons,
                        COALESCE(sess.count, 0) as sessions
                    FROM generate_series(CURRENT_DATE - INTERVAL '%s days', CURRENT_DATE, '1 day') as d(day)
                    LEFT JOIN (
                        SELECT DATE(created_at) as day, SUM(xp_earned)::INTEGER as total
                        FROM xp_transactions
                        WHERE user_id = %s AND DATE(created_at) >= CURRENT_DATE - INTERVAL '%s days'
                        GROUP BY DATE(created_at)
                    ) xp ON xp.day = d.day::DATE
                    LEFT JOIN (
                        SELECT DATE(completed_at) as day, COUNT(*)::INTEGER as count
                        FROM learning_path_progress
                        WHERE user_id = %s AND DATE(completed_at) >= CURRENT_DATE - INTERVAL '%s days' AND completed = TRUE
                        GROUP BY DATE(completed_at)
                    ) lp ON lp.day = d.day::DATE
                    LEFT JOIN (
                        SELECT DATE(created_at) as day, COUNT(*)::INTEGER as count
                        FROM sessions
                        WHERE user_id = %s AND DATE(created_at) >= CURRENT_DATE - INTERVAL '%s days'
                        GROUP BY DATE(created_at)
                    ) sess ON sess.day = d.day::DATE
                    ORDER BY d.day
                """, (days, user_id, days, user_id, days, user_id, days))
                return [dict(row) for row in cur.fetchall()]

    def get_learning_insights(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get learning insights: best study times, error patterns, streaks.

        Args:
            user_id: User UUID

        Returns:
            Dict with insights data
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                insights = {}

                # Best study hour (by XP earned)
                cur.execute("""
                    SELECT EXTRACT(HOUR FROM created_at)::INTEGER as hour, SUM(xp_earned)::INTEGER as total
                    FROM xp_transactions
                    WHERE user_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY EXTRACT(HOUR FROM created_at)
                    ORDER BY total DESC
                    LIMIT 3
                """, (user_id,))
                best_hours = [dict(row) for row in cur.fetchall()]
                insights['best_study_hours'] = best_hours

                # Best study day (by XP earned)
                cur.execute("""
                    SELECT EXTRACT(DOW FROM created_at)::INTEGER as day_of_week, SUM(xp_earned)::INTEGER as total
                    FROM xp_transactions
                    WHERE user_id = %s AND created_at >= CURRENT_DATE - INTERVAL '90 days'
                    GROUP BY EXTRACT(DOW FROM created_at)
                    ORDER BY total DESC
                """, (user_id,))
                day_performance = [dict(row) for row in cur.fetchall()]
                insights['day_performance'] = day_performance

                # Error patterns (by type over last 30 days)
                cur.execute("""
                    SELECT error_type, COUNT(*)::INTEGER as count,
                           DATE(created_at) as date
                    FROM errors
                    WHERE user_id = %s AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY error_type, DATE(created_at)
                    ORDER BY date
                """, (user_id,))
                error_trends = [dict(row) for row in cur.fetchall()]
                insights['error_trends'] = error_trends

                # Skill progression (top 5 improving skills)
                cur.execute("""
                    SELECT skill_key, skill_category, mastery_score, practice_count, error_count,
                           last_practiced
                    FROM skill_mastery
                    WHERE user_id = %s
                    ORDER BY last_practiced DESC
                    LIMIT 10
                """, (user_id,))
                skill_progress = [dict(row) for row in cur.fetchall()]
                insights['skill_progress'] = skill_progress

                # Study streaks stats
                cur.execute("""
                    SELECT streak_days, longest_streak, last_activity_date
                    FROM user_streaks
                    WHERE user_id = %s
                """, (user_id,))
                streak_data = cur.fetchone()
                if streak_data:
                    insights['streak'] = dict(streak_data)
                else:
                    insights['streak'] = {'streak_days': 0, 'longest_streak': 0, 'last_activity_date': None}

                # Total stats
                cur.execute("""
                    SELECT
                        COALESCE(SUM(xp_earned), 0)::INTEGER as total_xp,
                        COUNT(*)::INTEGER as total_sessions
                    FROM xp_transactions
                    WHERE user_id = %s
                """, (user_id,))
                total_stats = cur.fetchone()
                insights['total_xp'] = total_stats['total_xp'] if total_stats else 0
                insights['total_sessions'] = total_stats['total_sessions'] if total_stats else 0

                cur.execute("""
                    SELECT COUNT(*)::INTEGER as total_lessons
                    FROM learning_path_progress
                    WHERE user_id = %s AND completed = TRUE
                """, (user_id,))
                lesson_stats = cur.fetchone()
                insights['total_lessons'] = lesson_stats['total_lessons'] if lesson_stats else 0

                return insights

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
