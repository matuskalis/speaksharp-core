from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class AppState(str, Enum):
    ONBOARDING = "onboarding"
    DAILY_REVIEW = "daily_review"
    SCENARIO_SESSION = "scenario_session"
    FREE_CHAT = "free_chat"
    FEEDBACK_REPORT = "feedback_report"


class ErrorType(str, Enum):
    GRAMMAR = "grammar"
    VOCAB = "vocab"
    FLUENCY = "fluency"
    PRONUNCIATION = "pronunciation_placeholder"
    STRUCTURE = "structure"


class CardType(str, Enum):
    DEFINITION = "definition"
    CLOZE = "cloze"
    PRODUCTION = "production"
    PRONUNCIATION = "pronunciation"
    ERROR_REPAIR = "error_repair"


class Error(BaseModel):
    type: ErrorType
    user_sentence: str
    corrected_sentence: str
    explanation: str


class PronunciationFeedbackItem(BaseModel):
    """Pronunciation feedback for display in tutor response."""
    word: str
    score: float
    issue: str
    tip: str
    phonetic: Optional[str] = None
    example: Optional[str] = None


class TutorResponse(BaseModel):
    message: str
    errors: List[Error] = []
    micro_task: Optional[str] = None
    scenario_complete: Optional[bool] = None
    success_evaluation: Optional[str] = None
    pronunciation_feedback: Optional[Dict[str, Any]] = None  # Pronunciation analysis


class ScenarioTemplate(BaseModel):
    scenario_id: str
    title: str
    level_min: str
    level_max: str
    situation_description: str
    user_goal: str
    task: str
    success_criteria: str
    difficulty_tags: List[str]
    user_variables: Dict[str, Any] = {}


class SRSCard(BaseModel):
    card_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    card_type: CardType
    front: str
    back: str
    level: str = "A1"
    source: str = "lesson"
    difficulty: float = 0.5
    next_review_date: datetime
    interval_days: int = 1
    ease_factor: float = 2.5
    review_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class SRSReview(BaseModel):
    review_id: UUID = Field(default_factory=uuid4)
    card_id: UUID
    user_id: UUID
    quality: int  # 0-5
    response_time_ms: int
    user_response: str
    correct: bool
    new_interval_days: int
    new_ease_factor: float
    reviewed_at: datetime = Field(default_factory=datetime.now)


class SkillNode(BaseModel):
    node_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    skill_category: str
    skill_key: str
    mastery_score: float = 0.0
    confidence: float = 0.0
    last_practiced: Optional[datetime] = None
    practice_count: int = 0
    error_count: int = 0
    success_count: int = 0


class UserProfile(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    level: str = "A1"
    goals: Dict[str, Any] = {}
    interests: List[str] = []
    native_language: str = "unknown"


class Session(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    session_type: str
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    state: str = "in_progress"


class WordTiming(BaseModel):
    """Word-level timing from ASR."""
    word: str
    start: float
    end: float
    confidence: Optional[float] = None


class ASRResult(BaseModel):
    """Result from ASR transcription."""
    text: str
    confidence: Optional[float] = None
    language: Optional[str] = None
    duration: Optional[float] = None
    words: Optional[List[WordTiming]] = None
    provider: str = "stub"


class TTSResult(BaseModel):
    """Result from TTS synthesis."""
    audio_bytes: Optional[bytes] = None
    file_path: Optional[str] = None
    provider: str = "stub"
    duration: Optional[float] = None
    characters: int = 0


class VoiceTurnResult(BaseModel):
    """Result from a complete voice interaction turn."""
    recognized_text: str
    tutor_response: TutorResponse
    tts_output_path: Optional[str] = None
    asr_confidence: Optional[float] = None
    processing_time_ms: int = 0
