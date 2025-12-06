"""
Diagnostic Test Module for Adaptive Placement.

Implements an adaptive placement test that:
1. Starts at A2 level
2. Adjusts difficulty based on performance
3. Seeds initial mastery (P(L)) based on results
"""

import uuid
import random
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from app.exercises import EXERCISES, Exercise


# =============================================================================
# DIAGNOSTIC EXERCISE POOL
# =============================================================================

# Define which exercises are diagnostic (high-signal, clear right/wrong)
# Selected: 8 per level, single skill_key, grammar + core vocab focus
DIAGNOSTIC_EXERCISE_IDS = {
    # A1 Level (~8 exercises)
    "A1": [
        "mc-gram-a1-001",  # I ___ a student (am) - present simple affirmative
        "mc-gram-a1-002",  # She ___ breakfast (eats) - third person -s
        "mc-gram-a1-003",  # ___ you like coffee? (Do) - present simple question
        "mc-gram-a1-004",  # There ___ two books (are) - there is/are
        "mc-gram-a1-011",  # This is ___ umbrella (an) - articles a/an
        "mc-gram-a1-014",  # The book is ___ the table (on) - prepositions place
        "mc-vocab-a1-001", # Weather vocabulary
        "mc-vocab-a1-007", # Food vocabulary
    ],
    # A2 Level (~8 exercises)
    "A2": [
        "mc-gram-a2-003",  # This is ___ interesting book (the most) - comparatives
        "mc-gram-a2-006",  # He is ___ than his brother (taller) - comparatives -er
        "mc-gram-a2-007",  # We ___ to visit Paris (are going) - future going to
        "mc-gram-a2-009",  # She ___ the email yesterday (sent) - past simple
        "mc-gram-a2-010",  # You ___ wear a seatbelt (must) - modal must
        "mc-gram-a2-011",  # He ___ like coffee (doesn't) - present simple negative
        "mc-vocab-a2-001", # Feelings vocabulary
        "mc-vocab-a2-009", # Directions vocabulary
    ],
    # B1 Level (~8 exercises)
    "B1": [
        "mc-gram-b1-001",  # If it rains (conditional)
        "mc-gram-b1-006",  # You should (modal should)
        "mc-gram-b1-007",  # I would (modal would)
        "mc-gram-b1-012",  # Future will
        "mc-gram-b1-015",  # Unless (conditional)
        "mc-vocab-b1-001", # Work vocabulary
        "mc-vocab-b1-006", # Phrasal verbs - look after
        "mc-vocab-b1-009", # Directions vocabulary
    ],
}

# Flatten to get all diagnostic IDs
ALL_DIAGNOSTIC_IDS = (
    DIAGNOSTIC_EXERCISE_IDS["A1"] +
    DIAGNOSTIC_EXERCISE_IDS["A2"] +
    DIAGNOSTIC_EXERCISE_IDS["B1"]
)


def get_diagnostic_exercises_by_level(level: str) -> List[Exercise]:
    """Get all diagnostic exercises for a specific level."""
    if level not in DIAGNOSTIC_EXERCISE_IDS:
        return []
    return [
        EXERCISES[eid] for eid in DIAGNOSTIC_EXERCISE_IDS[level]
        if eid in EXERCISES
    ]


def get_all_diagnostic_exercises() -> List[Exercise]:
    """Get all diagnostic exercises across all levels."""
    return [EXERCISES[eid] for eid in ALL_DIAGNOSTIC_IDS if eid in EXERCISES]


def is_diagnostic_exercise(exercise_id: str) -> bool:
    """Check if an exercise is a diagnostic exercise."""
    return exercise_id in ALL_DIAGNOSTIC_IDS


# =============================================================================
# DIAGNOSTIC SESSION DATA MODEL
# =============================================================================

@dataclass
class DiagnosticSession:
    """
    Represents an adaptive diagnostic test session.

    Algorithm:
    - Start at A1 level
    - 2 correct in a row at level → promote to next level
    - 1 mistake → second chance (confirmation question)
    - 2 mistakes at level → that's the ceiling, stop
    - Clear B1 (2 correct) → place at B1, stop
    """
    session_id: uuid.UUID
    user_id: uuid.UUID
    status: str  # 'in_progress' | 'completed'
    current_level: str  # 'A1' | 'A2' | 'B1'
    questions_answered: int
    max_questions: int  # Soft cap for safety (hard stop at 25)
    stats: Dict[str, Dict[str, int]]  # {"A1": {"correct": 0, "total": 0}, ...}
    user_level: Optional[str]  # Final determined level
    started_at: datetime
    completed_at: Optional[datetime]
    # New adaptive fields
    streak: int = 0  # Consecutive correct at current level
    mistakes_at_level: int = 0  # Mistakes at current level
    highest_passed: Optional[str] = None  # Highest level passed (2 correct)
    in_confirmation: bool = False  # Waiting for second chance after mistake

    @classmethod
    def create_new(cls, user_id: uuid.UUID) -> "DiagnosticSession":
        """Create a new adaptive diagnostic session."""
        return cls(
            session_id=uuid.uuid4(),
            user_id=user_id,
            status="in_progress",
            current_level="A1",  # Start at A1 (truly adaptive)
            questions_answered=0,
            max_questions=25,  # Safety cap
            stats={
                "A1": {"correct": 0, "total": 0},
                "A2": {"correct": 0, "total": 0},
                "B1": {"correct": 0, "total": 0},
            },
            user_level=None,
            started_at=datetime.utcnow(),
            completed_at=None,
            streak=0,
            mistakes_at_level=0,
            highest_passed=None,
            in_confirmation=False,
        )


@dataclass
class DiagnosticAnswer:
    """Represents a single answer in a diagnostic session."""
    id: uuid.UUID
    session_id: uuid.UUID
    question_index: int
    exercise_id: str
    skill_key: str
    level: str
    user_answer: str
    is_correct: bool
    created_at: datetime


# =============================================================================
# ADAPTIVE ALGORITHM
# =============================================================================

# Level order for promotion/demotion
LEVEL_ORDER = ["A1", "A2", "B1"]


class DiagnosticEngine:
    """
    Truly adaptive diagnostic test algorithm.

    Rules:
    - Start at A1
    - 2 correct in a row → promote to next level, reset streak
    - 1 mistake → enter confirmation mode (second chance)
    - Pass confirmation → continue at same level, reset mistakes
    - Fail confirmation (2 mistakes at level) → ceiling found, stop
    - Clear B1 (2 correct) → place at B1, stop
    - Max 25 questions for safety
    """

    def __init__(self, db):
        self.db = db

    def select_next_question(
        self,
        session: DiagnosticSession,
        used_exercise_ids: List[str]
    ) -> Optional[Exercise]:
        """
        Select the next question from current level only.
        """
        used_set = set(used_exercise_ids)

        # ONLY pick from current level (truly adaptive)
        candidates = get_diagnostic_exercises_by_level(session.current_level)
        candidates = [ex for ex in candidates if ex.exercise_id not in used_set]

        if not candidates:
            # No more questions at this level - check adjacent levels
            level_idx = LEVEL_ORDER.index(session.current_level)

            # Try level below if available
            if level_idx > 0:
                below = LEVEL_ORDER[level_idx - 1]
                candidates = get_diagnostic_exercises_by_level(below)
                candidates = [ex for ex in candidates if ex.exercise_id not in used_set]

            # If still none, try level above
            if not candidates and level_idx < len(LEVEL_ORDER) - 1:
                above = LEVEL_ORDER[level_idx + 1]
                candidates = get_diagnostic_exercises_by_level(above)
                candidates = [ex for ex in candidates if ex.exercise_id not in used_set]

        if not candidates:
            return None

        return random.choice(candidates)

    def grade_answer(self, exercise: Exercise, user_answer: str) -> bool:
        """Grade a user's answer against the correct answer."""
        correct = exercise.correct_answer.strip().lower()
        user = user_answer.strip().lower()
        return user == correct

    def update_session_after_answer(
        self,
        session: DiagnosticSession,
        exercise: Exercise,
        is_correct: bool
    ) -> DiagnosticSession:
        """
        Update session state after an answer using adaptive algorithm.
        """
        level = exercise.level

        # Update stats
        session.stats[level]["total"] += 1
        if is_correct:
            session.stats[level]["correct"] += 1
        session.questions_answered += 1

        # Apply adaptive logic
        if is_correct:
            session = self._handle_correct(session)
        else:
            session = self._handle_incorrect(session)

        # Check stop conditions
        if self._should_stop(session):
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session.user_level = self._compute_user_level(session)

        return session

    def _handle_correct(self, session: DiagnosticSession) -> DiagnosticSession:
        """Handle a correct answer."""
        session.streak += 1

        # If we were in confirmation mode, we passed - reset mistakes
        if session.in_confirmation:
            session.in_confirmation = False
            session.mistakes_at_level = 0
            # Don't count confirmation towards streak
            session.streak = 1

        # 2 correct in a row → passed this level
        if session.streak >= 2:
            session.highest_passed = session.current_level

            # Promote to next level if possible
            level_idx = LEVEL_ORDER.index(session.current_level)
            if level_idx < len(LEVEL_ORDER) - 1:
                session.current_level = LEVEL_ORDER[level_idx + 1]
                session.streak = 0
                session.mistakes_at_level = 0
            # If already at B1 and passed, we're done (will trigger stop)

        return session

    def _handle_incorrect(self, session: DiagnosticSession) -> DiagnosticSession:
        """Handle an incorrect answer."""
        session.streak = 0
        session.mistakes_at_level += 1

        if session.in_confirmation:
            # Failed confirmation - this is their ceiling
            # Will trigger stop condition
            pass
        else:
            # First mistake - enter confirmation mode
            session.in_confirmation = True

        return session

    def _should_stop(self, session: DiagnosticSession) -> bool:
        """
        Check if the diagnostic test should stop.

        Stop conditions:
        1. Max questions reached (safety cap)
        2. 2 mistakes at current level (ceiling found)
        3. Passed B1 (highest level achieved)
        """
        # Safety cap
        if session.questions_answered >= session.max_questions:
            return True

        # Ceiling found: 2 mistakes at level
        if session.mistakes_at_level >= 2:
            return True

        # Passed B1 (highest level)
        if session.highest_passed == "B1" and session.streak >= 2:
            return True

        return False

    def _compute_user_level(self, session: DiagnosticSession) -> str:
        """
        Compute the user's final level using finalize_diagnostic_placement.
        """
        return finalize_diagnostic_placement(session)


def finalize_diagnostic_placement(session: DiagnosticSession) -> str:
    """
    Single function to determine final placement from any stop condition.

    This is the ONLY place that computes final placement.

    Logic:
    - highest_passed is set ONLY when user gets 2 consecutive correct at a level
    - If highest_passed is set, that's their placement
    - If highest_passed is None (never passed any level), default to A1

    Stop conditions that call this:
    1. "2 mistakes at level X" → placement = highest_passed or A1
    2. "passed B1 (2 correct at B1)" → placement = B1 (highest_passed = B1)
    3. "max questions reached" → placement = highest_passed or A1
    """
    if session.highest_passed is not None:
        return session.highest_passed

    # User never passed any level (struggled at A1)
    # They're a true beginner
    return "A1"


# =============================================================================
# MASTERY SEEDING
# =============================================================================

# Default P(L) based on user_level and skill CEFR level
DEFAULT_PL = {
    "A1": {  # User is A1 level
        "A1": 0.7,
        "A2": 0.4,
        "B1": 0.2,
    },
    "A2": {  # User is A2 level
        "A1": 0.85,
        "A2": 0.6,
        "B1": 0.35,
    },
    "B1": {  # User is B1 level
        "A1": 0.9,
        "A2": 0.75,
        "B1": 0.5,
    },
}


def seed_initial_mastery(
    db,
    user_id: uuid.UUID,
    user_level: str,
    diagnostic_answers: List[DiagnosticAnswer]
):
    """
    Seed initial mastery for all A1-B1 skills based on diagnostic results.

    Step 1: Set base P(L) for all skills based on user_level
    Step 2: Refine tested skills using BKT with diagnostic answers
    """
    # Step 1: Get all skills and set base P(L)
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Get all active skills
            cur.execute("""
                SELECT skill_key, cefr_level
                FROM skill_definitions
                WHERE is_active = TRUE
                  AND cefr_level IN ('A1', 'A2', 'B1')
            """)
            skills = cur.fetchall()

            # Insert/update base P(L) for each skill
            for row in skills:
                if isinstance(row, dict):
                    skill_key = row['skill_key']
                    skill_level = row['cefr_level']
                else:
                    skill_key = row[0]
                    skill_level = row[1]

                base_pl = DEFAULT_PL.get(user_level, DEFAULT_PL["A1"]).get(skill_level, 0.3)

                # Upsert skill mastery
                cur.execute("""
                    INSERT INTO skill_graph_nodes (
                        node_id, user_id, skill_category, skill_key,
                        mastery_score, p_learned, p_transit,
                        practice_count, success_count, error_count
                    )
                    VALUES (
                        gen_random_uuid(), %s, 'diagnostic', %s,
                        %s, %s, 0.15,
                        0, 0, 0
                    )
                    ON CONFLICT (user_id, skill_key) DO UPDATE SET
                        p_learned = %s,
                        mastery_score = %s
                """, (
                    str(user_id), skill_key,
                    base_pl * 100, base_pl,
                    base_pl, base_pl * 100
                ))

            conn.commit()

    # Step 2: Refine tested skills with BKT using diagnostic answers
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            for answer in diagnostic_answers:
                # Use the existing BKT update function
                cur.execute(
                    "SELECT update_skill_bkt(%s, %s, %s)",
                    (str(user_id), answer.skill_key, answer.is_correct)
                )
            conn.commit()


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

class DiagnosticRepository:
    """Database operations for diagnostic sessions."""

    def __init__(self, db):
        self.db = db

    def create_session(self, session: DiagnosticSession) -> DiagnosticSession:
        """Insert a new diagnostic session."""
        # Store adaptive state in stats for backwards compatibility
        stats_with_adaptive = {
            **session.stats,
            "_adaptive": {
                "streak": session.streak,
                "mistakes_at_level": session.mistakes_at_level,
                "highest_passed": session.highest_passed,
                "in_confirmation": session.in_confirmation,
            }
        }
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO diagnostic_sessions (
                        session_id, user_id, status, current_level,
                        questions_answered, max_questions, stats,
                        started_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(session.session_id),
                    str(session.user_id),
                    session.status,
                    session.current_level,
                    session.questions_answered,
                    session.max_questions,
                    json.dumps(stats_with_adaptive),
                    session.started_at,
                ))
                conn.commit()
        return session

    def get_session(self, session_id: uuid.UUID) -> Optional[DiagnosticSession]:
        """Get a diagnostic session by ID."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT session_id, user_id, status, current_level,
                           questions_answered, max_questions, stats,
                           user_level, started_at, completed_at
                    FROM diagnostic_sessions
                    WHERE session_id = %s
                """, (str(session_id),))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_session(row)

    def _row_to_session(self, row) -> DiagnosticSession:
        """Convert a database row to DiagnosticSession."""
        if isinstance(row, dict):
            stats_raw = row['stats'] if isinstance(row['stats'], dict) else json.loads(row['stats'])
            session_id = uuid.UUID(row['session_id']) if isinstance(row['session_id'], str) else row['session_id']
            user_id = uuid.UUID(row['user_id']) if isinstance(row['user_id'], str) else row['user_id']
            status = row['status']
            current_level = row['current_level']
            questions_answered = row['questions_answered']
            max_questions = row['max_questions']
            user_level = row['user_level']
            started_at = row['started_at']
            completed_at = row['completed_at']
        else:
            stats_raw = row[6] if isinstance(row[6], dict) else json.loads(row[6])
            session_id = uuid.UUID(row[0]) if isinstance(row[0], str) else row[0]
            user_id = uuid.UUID(row[1]) if isinstance(row[1], str) else row[1]
            status = row[2]
            current_level = row[3]
            questions_answered = row[4]
            max_questions = row[5]
            user_level = row[7]
            started_at = row[8]
            completed_at = row[9]

        # Extract adaptive state from stats
        adaptive = stats_raw.pop("_adaptive", {})
        streak = adaptive.get("streak", 0)
        mistakes_at_level = adaptive.get("mistakes_at_level", 0)
        highest_passed = adaptive.get("highest_passed", None)
        in_confirmation = adaptive.get("in_confirmation", False)

        return DiagnosticSession(
            session_id=session_id,
            user_id=user_id,
            status=status,
            current_level=current_level,
            questions_answered=questions_answered,
            max_questions=max_questions,
            stats=stats_raw,
            user_level=user_level,
            started_at=started_at,
            completed_at=completed_at,
            streak=streak,
            mistakes_at_level=mistakes_at_level,
            highest_passed=highest_passed,
            in_confirmation=in_confirmation,
        )

    def update_session(self, session: DiagnosticSession) -> None:
        """Update a diagnostic session."""
        # Store adaptive state in stats for backwards compatibility
        stats_with_adaptive = {
            **session.stats,
            "_adaptive": {
                "streak": session.streak,
                "mistakes_at_level": session.mistakes_at_level,
                "highest_passed": session.highest_passed,
                "in_confirmation": session.in_confirmation,
            }
        }
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE diagnostic_sessions
                    SET status = %s,
                        current_level = %s,
                        questions_answered = %s,
                        stats = %s,
                        user_level = %s,
                        completed_at = %s
                    WHERE session_id = %s
                """, (
                    session.status,
                    session.current_level,
                    session.questions_answered,
                    json.dumps(stats_with_adaptive),
                    session.user_level,
                    session.completed_at,
                    str(session.session_id),
                ))
                conn.commit()

    def add_answer(self, answer: DiagnosticAnswer) -> None:
        """Add a diagnostic answer."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO diagnostic_answers (
                        id, session_id, question_index, exercise_id,
                        skill_key, level, user_answer, is_correct, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(answer.id),
                    str(answer.session_id),
                    answer.question_index,
                    answer.exercise_id,
                    answer.skill_key,
                    answer.level,
                    answer.user_answer,
                    answer.is_correct,
                    answer.created_at,
                ))
                conn.commit()

    def get_used_exercise_ids(self, session_id: uuid.UUID) -> List[str]:
        """Get list of exercise IDs already used in this session."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT exercise_id
                    FROM diagnostic_answers
                    WHERE session_id = %s
                """, (str(session_id),))
                rows = cur.fetchall()

                if not rows:
                    return []

                if isinstance(rows[0], dict):
                    return [row['exercise_id'] for row in rows]
                else:
                    return [row[0] for row in rows]

    def get_session_answers(self, session_id: uuid.UUID) -> List[DiagnosticAnswer]:
        """Get all answers for a session."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, session_id, question_index, exercise_id,
                           skill_key, level, user_answer, is_correct, created_at
                    FROM diagnostic_answers
                    WHERE session_id = %s
                    ORDER BY question_index
                """, (str(session_id),))
                rows = cur.fetchall()

                answers = []
                for row in rows:
                    if isinstance(row, dict):
                        answers.append(DiagnosticAnswer(
                            id=uuid.UUID(row['id']) if isinstance(row['id'], str) else row['id'],
                            session_id=uuid.UUID(row['session_id']) if isinstance(row['session_id'], str) else row['session_id'],
                            question_index=row['question_index'],
                            exercise_id=row['exercise_id'],
                            skill_key=row['skill_key'],
                            level=row['level'],
                            user_answer=row['user_answer'],
                            is_correct=row['is_correct'],
                            created_at=row['created_at'],
                        ))
                    else:
                        answers.append(DiagnosticAnswer(
                            id=uuid.UUID(row[0]) if isinstance(row[0], str) else row[0],
                            session_id=uuid.UUID(row[1]) if isinstance(row[1], str) else row[1],
                            question_index=row[2],
                            exercise_id=row[3],
                            skill_key=row[4],
                            level=row[5],
                            user_answer=row[6],
                            is_correct=row[7],
                            created_at=row[8],
                        ))
                return answers

    def get_active_session_for_user(self, user_id: uuid.UUID) -> Optional[DiagnosticSession]:
        """Get any in-progress diagnostic session for a user."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT session_id, user_id, status, current_level,
                           questions_answered, max_questions, stats,
                           user_level, started_at, completed_at
                    FROM diagnostic_sessions
                    WHERE user_id = %s AND status = 'in_progress'
                    ORDER BY started_at DESC
                    LIMIT 1
                """, (str(user_id),))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_session(row)
