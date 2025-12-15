"""
Conversation Replay with Coaching Annotations.

Provides timestamped transcript review with:
- Error highlights and corrections
- Pronunciation feedback
- Grammar explanations
- Suggested improvements
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid
import json


@dataclass
class CoachingAnnotation:
    """Single coaching annotation on the transcript."""
    id: str
    timestamp_start: float  # seconds into recording
    timestamp_end: float
    annotation_type: str  # error, improvement, praise, pronunciation
    original_text: str
    corrected_text: Optional[str]
    explanation: str
    severity: str  # minor, moderate, major
    category: str  # grammar, vocabulary, pronunciation, fluency

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "type": self.annotation_type,
            "original": self.original_text,
            "corrected": self.corrected_text,
            "explanation": self.explanation,
            "severity": self.severity,
            "category": self.category,
        }


@dataclass
class TranscriptSegment:
    """A segment of the conversation transcript."""
    id: str
    role: str  # user, assistant
    text: str
    start_time: float
    end_time: float
    word_timings: List[Dict[str, Any]] = field(default_factory=list)
    annotations: List[CoachingAnnotation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "word_timings": self.word_timings,
            "annotations": [a.to_dict() for a in self.annotations],
        }


@dataclass
class SessionReplay:
    """Complete conversation session with coaching replay."""
    session_id: str
    user_id: str
    scenario_name: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    segments: List[TranscriptSegment]
    summary: Dict[str, Any]  # Overall session stats

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "scenario": self.scenario_name,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "segments": [s.to_dict() for s in self.segments],
            "summary": self.summary,
            "duration_seconds": self._calculate_duration(),
            "total_annotations": sum(len(s.annotations) for s in self.segments),
        }

    def _calculate_duration(self) -> float:
        if self.segments:
            return self.segments[-1].end_time - self.segments[0].start_time
        return 0.0


class ConversationReplayBuilder:
    """
    Builds replay data from conversation sessions.

    Collects turn-by-turn data during a session, then generates
    coaching annotations for replay.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        scenario_name: Optional[str] = None
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id or ""
        self.scenario_name = scenario_name
        self.started_at = datetime.utcnow()
        self.segments: List[TranscriptSegment] = []
        self._current_time = 0.0

    def add_user_turn(
        self,
        transcript: str,
        word_timings: List[Dict[str, Any]] = None,
        ranking_result: Optional[Dict] = None,
        pronunciation_result: Optional[Dict] = None,
        duration: float = 0.0
    ) -> TranscriptSegment:
        """
        Add a user turn and generate coaching annotations.

        Args:
            transcript: The user's transcribed speech
            word_timings: List of {word, start, end, confidence}
            ranking_result: AI ranking with errors
            pronunciation_result: Pronunciation analysis
            duration: Duration of audio in seconds
        """
        start_time = self._current_time
        end_time = start_time + duration

        segment = TranscriptSegment(
            id=str(uuid.uuid4()),
            role="user",
            text=transcript,
            start_time=start_time,
            end_time=end_time,
            word_timings=word_timings or [],
            annotations=[],
        )

        # Generate annotations from ranking result
        if ranking_result:
            annotations = self._generate_grammar_annotations(
                ranking_result, start_time, word_timings
            )
            segment.annotations.extend(annotations)

        # Generate annotations from pronunciation result
        if pronunciation_result:
            pron_annotations = self._generate_pronunciation_annotations(
                pronunciation_result, start_time
            )
            segment.annotations.extend(pron_annotations)

        self.segments.append(segment)
        self._current_time = end_time + 0.5  # Small gap between turns
        return segment

    def add_assistant_turn(
        self,
        text: str,
        duration: float = 0.0
    ) -> TranscriptSegment:
        """Add an assistant turn (tutor response)."""
        start_time = self._current_time
        end_time = start_time + duration

        segment = TranscriptSegment(
            id=str(uuid.uuid4()),
            role="assistant",
            text=text,
            start_time=start_time,
            end_time=end_time,
            word_timings=[],
            annotations=[],
        )

        self.segments.append(segment)
        self._current_time = end_time + 0.5
        return segment

    def _generate_grammar_annotations(
        self,
        ranking_result: Dict,
        base_time: float,
        word_timings: Optional[List[Dict]]
    ) -> List[CoachingAnnotation]:
        """Generate coaching annotations from grammar errors."""
        annotations = []

        errors = ranking_result.get("errors", [])
        for error in errors:
            error_type = error.get("type", "grammar")
            original = error.get("text", error.get("user_sentence", ""))
            corrected = error.get("correction", error.get("corrected_sentence", ""))
            explanation = error.get("explanation", "")
            severity = error.get("severity", "minor")

            # Try to find word timing for this error
            timestamp = base_time
            if word_timings and original:
                for wt in word_timings:
                    if original.lower() in wt.get("word", "").lower():
                        timestamp = wt.get("start", base_time)
                        break

            annotation = CoachingAnnotation(
                id=str(uuid.uuid4()),
                timestamp_start=timestamp,
                timestamp_end=timestamp + 1.0,
                annotation_type="error",
                original_text=original,
                corrected_text=corrected,
                explanation=explanation or f"Consider using: '{corrected}'",
                severity=severity,
                category=error_type,
            )
            annotations.append(annotation)

        # Add praise for strengths
        strengths = ranking_result.get("strengths", [])
        for i, strength in enumerate(strengths[:2]):  # Max 2 praise annotations
            annotations.append(CoachingAnnotation(
                id=str(uuid.uuid4()),
                timestamp_start=base_time,
                timestamp_end=base_time + 0.5,
                annotation_type="praise",
                original_text="",
                corrected_text=None,
                explanation=strength,
                severity="positive",
                category="feedback",
            ))

        return annotations

    def _generate_pronunciation_annotations(
        self,
        pronunciation_result: Dict,
        base_time: float
    ) -> List[CoachingAnnotation]:
        """Generate annotations from pronunciation analysis."""
        annotations = []

        # L1 patterns detected
        l1_patterns = pronunciation_result.get("l1_patterns", [])
        for pattern in l1_patterns[:3]:  # Max 3 pattern annotations
            annotations.append(CoachingAnnotation(
                id=str(uuid.uuid4()),
                timestamp_start=base_time,
                timestamp_end=base_time + 0.5,
                annotation_type="pronunciation",
                original_text=pattern.get("phoneme", ""),
                corrected_text=pattern.get("pattern", ""),
                explanation=f"Watch this sound: {pattern.get('pattern', '')}. "
                           f"Examples: {', '.join(pattern.get('examples', [])[:2])}",
                severity="moderate" if pattern.get("count", 0) >= 2 else "minor",
                category="pronunciation",
            ))

        # Word-level feedback
        word_scores = pronunciation_result.get("word_scores", [])
        for ws in word_scores:
            if ws.get("score", 100) < 70:
                annotations.append(CoachingAnnotation(
                    id=str(uuid.uuid4()),
                    timestamp_start=ws.get("start", base_time),
                    timestamp_end=ws.get("end", base_time + 0.5),
                    annotation_type="pronunciation",
                    original_text=ws.get("word", ""),
                    corrected_text=None,
                    explanation=f"Try practicing '{ws.get('word', '')}' more clearly.",
                    severity="minor",
                    category="pronunciation",
                ))

        # Recommendations
        recommendations = pronunciation_result.get("recommendations", [])
        for rec in recommendations[:1]:  # Max 1 recommendation
            annotations.append(CoachingAnnotation(
                id=str(uuid.uuid4()),
                timestamp_start=base_time,
                timestamp_end=base_time + 0.5,
                annotation_type="improvement",
                original_text="",
                corrected_text=None,
                explanation=rec,
                severity="tip",
                category="pronunciation",
            ))

        return annotations

    def build_replay(self) -> SessionReplay:
        """Build the final replay object with summary."""
        ended_at = datetime.utcnow()

        # Calculate summary statistics
        total_errors = 0
        errors_by_type = {}
        total_praise = 0

        for segment in self.segments:
            for ann in segment.annotations:
                if ann.annotation_type == "error":
                    total_errors += 1
                    errors_by_type[ann.category] = errors_by_type.get(ann.category, 0) + 1
                elif ann.annotation_type == "praise":
                    total_praise += 1

        user_segments = [s for s in self.segments if s.role == "user"]
        total_user_words = sum(len(s.text.split()) for s in user_segments)

        summary = {
            "total_turns": len(self.segments),
            "user_turns": len(user_segments),
            "total_user_words": total_user_words,
            "total_errors": total_errors,
            "errors_by_type": errors_by_type,
            "total_praise": total_praise,
            "accuracy_estimate": max(0, 100 - (total_errors * 5)),  # Rough estimate
        }

        return SessionReplay(
            session_id=self.session_id,
            user_id=self.user_id,
            scenario_name=self.scenario_name,
            started_at=self.started_at,
            ended_at=ended_at,
            segments=self.segments,
            summary=summary,
        )


class ReplayManager:
    """
    Manages conversation replays with database persistence.
    """

    def __init__(self, db=None):
        self.db = db
        self._active_sessions: Dict[str, ConversationReplayBuilder] = {}

    def start_session(
        self,
        user_id: str,
        scenario_name: Optional[str] = None
    ) -> str:
        """Start a new replay session."""
        session_id = str(uuid.uuid4())
        builder = ConversationReplayBuilder(
            session_id=session_id,
            user_id=user_id,
            scenario_name=scenario_name
        )
        self._active_sessions[session_id] = builder
        return session_id

    def add_turn(
        self,
        session_id: str,
        role: str,
        text: str,
        word_timings: Optional[List[Dict]] = None,
        ranking_result: Optional[Dict] = None,
        pronunciation_result: Optional[Dict] = None,
        duration: float = 0.0
    ) -> Optional[TranscriptSegment]:
        """Add a turn to an active session."""
        builder = self._active_sessions.get(session_id)
        if not builder:
            return None

        if role == "user":
            return builder.add_user_turn(
                transcript=text,
                word_timings=word_timings,
                ranking_result=ranking_result,
                pronunciation_result=pronunciation_result,
                duration=duration
            )
        else:
            return builder.add_assistant_turn(text=text, duration=duration)

    def end_session(self, session_id: str) -> Optional[SessionReplay]:
        """End session and return replay data."""
        builder = self._active_sessions.pop(session_id, None)
        if not builder:
            return None

        replay = builder.build_replay()

        # Persist to database if available
        if self.db:
            try:
                self._save_replay(replay)
            except Exception as e:
                print(f"[ReplayManager] Failed to save replay: {e}")

        return replay

    def get_replay(self, session_id: str) -> Optional[SessionReplay]:
        """Retrieve a replay from database."""
        if not self.db:
            return None

        try:
            return self._load_replay(session_id)
        except Exception as e:
            print(f"[ReplayManager] Failed to load replay: {e}")
            return None

    def get_user_replays(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get list of user's recent replays (summary only)."""
        if not self.db:
            return []

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT session_id, scenario_name, started_at, ended_at, summary
                        FROM conversation_replays
                        WHERE user_id = %s
                        ORDER BY started_at DESC
                        LIMIT %s
                    """, (str(user_id), limit))

                    rows = cur.fetchall()
                    return [
                        {
                            "session_id": row[0],
                            "scenario": row[1],
                            "started_at": row[2].isoformat() if row[2] else None,
                            "ended_at": row[3].isoformat() if row[3] else None,
                            "summary": row[4],
                        }
                        for row in rows
                    ]
        except Exception as e:
            print(f"[ReplayManager] Failed to get user replays: {e}")
            return []

    def _save_replay(self, replay: SessionReplay):
        """Save replay to database."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversation_replays
                    (session_id, user_id, scenario_name, started_at, ended_at, segments, summary)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        ended_at = EXCLUDED.ended_at,
                        segments = EXCLUDED.segments,
                        summary = EXCLUDED.summary
                """, (
                    replay.session_id,
                    replay.user_id,
                    replay.scenario_name,
                    replay.started_at,
                    replay.ended_at,
                    json.dumps([s.to_dict() for s in replay.segments]),
                    json.dumps(replay.summary),
                ))
                conn.commit()

    def _load_replay(self, session_id: str) -> Optional[SessionReplay]:
        """Load replay from database."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT session_id, user_id, scenario_name, started_at, ended_at,
                           segments, summary
                    FROM conversation_replays
                    WHERE session_id = %s
                """, (session_id,))

                row = cur.fetchone()
                if not row:
                    return None

                segments_data = row[5] if isinstance(row[5], list) else json.loads(row[5])
                segments = []
                for sd in segments_data:
                    annotations = [
                        CoachingAnnotation(
                            id=a["id"],
                            timestamp_start=a["timestamp_start"],
                            timestamp_end=a["timestamp_end"],
                            annotation_type=a["type"],
                            original_text=a["original"],
                            corrected_text=a.get("corrected"),
                            explanation=a["explanation"],
                            severity=a["severity"],
                            category=a["category"],
                        )
                        for a in sd.get("annotations", [])
                    ]
                    segments.append(TranscriptSegment(
                        id=sd["id"],
                        role=sd["role"],
                        text=sd["text"],
                        start_time=sd["start_time"],
                        end_time=sd["end_time"],
                        word_timings=sd.get("word_timings", []),
                        annotations=annotations,
                    ))

                return SessionReplay(
                    session_id=row[0],
                    user_id=row[1],
                    scenario_name=row[2],
                    started_at=row[3],
                    ended_at=row[4],
                    segments=segments,
                    summary=row[6] if isinstance(row[6], dict) else json.loads(row[6]),
                )


# Global replay manager instance
replay_manager = ReplayManager()


def create_replay_manager_with_db(db) -> ReplayManager:
    """Create a replay manager with database support."""
    return ReplayManager(db=db)
