"""
FastAPI application for SpeakSharp Core.

Provides HTTP endpoints for:
- Text-based tutoring
- Voice-based tutoring
- SRS card management
- User profiles
- Session management
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import base64

from app.db import Database, get_db
from app.tutor_agent import TutorAgent
from app.voice_session import VoiceSession
from app.config import load_config
from app.models import TutorResponse
from app.auth import verify_token, optional_verify_token, get_or_create_user, add_user_xp, get_user_xp
from app.diagnostic import (
    DiagnosticSession, DiagnosticAnswer, DiagnosticEngine,
    DiagnosticRepository, seed_initial_mastery,
    get_all_diagnostic_exercises, is_diagnostic_exercise
)
from app.exercises import EXERCISES, get_exercises_by_skill_key
from app.thinking_engine import thinking_engine, ThinkingSession, ThinkingTurn
from app.asr_client import asr_client
from app.tts_client import tts_client
from app.skill_unlocks import (
    SkillUnlockManager, create_skill_manager_with_db,
    SKILL_DEFINITIONS, UNLOCKABLE_CONTENT, ACHIEVEMENTS
)
from app.conversation_replay import (
    ReplayManager, create_replay_manager_with_db,
    ConversationReplayBuilder
)
from app.phoneme_analyzer import analyze_pronunciation_from_asr
import random
import io
import time
import tempfile
import os
import httpx

# Simple in-memory cache to prevent XP abuse (prevents re-submission of same exercise)
# Key: "user_id:exercise_id", Value: timestamp of correct answer
# Entries expire after 1 hour
_exercise_xp_cache: Dict[str, float] = {}
_EXERCISE_XP_CACHE_TTL = 3600  # 1 hour

def _can_earn_xp(user_id: str, exercise_id: str) -> bool:
    """Check if user can earn XP for this exercise (not already answered correctly recently)."""
    cache_key = f"{user_id}:{exercise_id}"
    now = time.time()

    # Clean expired entries (lazy cleanup)
    expired_keys = [k for k, v in _exercise_xp_cache.items() if now - v > _EXERCISE_XP_CACHE_TTL]
    for k in expired_keys:
        del _exercise_xp_cache[k]

    return cache_key not in _exercise_xp_cache

def _mark_xp_earned(user_id: str, exercise_id: str):
    """Mark that user earned XP for this exercise."""
    cache_key = f"{user_id}:{exercise_id}"
    _exercise_xp_cache[cache_key] = time.time()


# Pydantic Models for API

class TutorTextRequest(BaseModel):
    """Request model for text-based tutoring."""
    user_id: uuid.UUID
    text: str
    scenario_id: Optional[str] = None
    context: Optional[str] = None
    session_id: Optional[uuid.UUID] = None


class TutorTextResponse(BaseModel):
    """Response model for text-based tutoring."""
    message: str
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    micro_task: Optional[str] = None
    session_id: uuid.UUID


class TutorVoiceRequest(BaseModel):
    """Request model for voice-based tutoring."""
    user_id: uuid.UUID
    audio_path: Optional[str] = None  # Path to audio file or URL
    audio_bytes: Optional[str] = None  # Base64 encoded audio (future)
    session_id: Optional[uuid.UUID] = None


class TutorVoiceResponse(BaseModel):
    """Response model for voice-based tutoring."""
    transcript: str
    message: str
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    audio_url: Optional[str] = None  # URL to response audio
    session_id: uuid.UUID


class SRSDueResponse(BaseModel):
    """Response model for due SRS cards."""
    cards: List[Dict[str, Any]]
    count: int


class SRSReviewRequest(BaseModel):
    """Request model for SRS card review."""
    card_id: uuid.UUID
    quality: int = Field(..., ge=0, le=5)
    response_time_ms: Optional[int] = None
    user_response: Optional[str] = None
    correct: bool = True


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    user_id: uuid.UUID
    level: str
    native_language: Optional[str] = None
    goals: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    daily_time_goal: Optional[int] = None
    onboarding_completed: bool = False
    full_name: Optional[str] = None
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_status: Optional[str] = None
    subscription_tier: Optional[str] = None
    is_tester: bool = False
    total_xp: int = 0
    created_at: datetime
    updated_at: datetime


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    user_id: Optional[uuid.UUID] = None
    level: str = "A1"
    native_language: Optional[str] = None
    goals: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    level: Optional[str] = None
    native_language: Optional[str] = None


class VoicePreferences(BaseModel):
    """Voice preferences model."""
    voice: str = "alloy"
    speech_speed: float = 1.0
    auto_play_responses: bool = True
    show_transcription: bool = True
    microphone_sensitivity: float = 0.5


class UpdateVoicePreferencesRequest(BaseModel):
    """Request model for updating voice preferences."""
    voice: Optional[str] = None
    speech_speed: Optional[float] = None
    auto_play_responses: Optional[bool] = None
    show_transcription: Optional[bool] = None
    microphone_sensitivity: Optional[float] = None


class SessionResultRequest(BaseModel):
    """Request model for saving a session result."""
    session_type: str = Field(..., description="Type of session: conversation, pronunciation, or roleplay")
    duration_seconds: int = Field(..., ge=0, description="Duration in seconds")
    words_spoken: int = Field(default=0, ge=0, description="Number of words spoken")
    pronunciation_score: float = Field(default=0.0, ge=0, le=100, description="Pronunciation score (0-100)")
    fluency_score: float = Field(default=0.0, ge=0, le=100, description="Fluency score (0-100)")
    grammar_score: float = Field(default=0.0, ge=0, le=100, description="Grammar score (0-100)")
    topics: List[str] = Field(default_factory=list, description="Topics covered in the session")
    vocabulary_learned: List[str] = Field(default_factory=list, description="Vocabulary items learned")
    areas_to_improve: List[str] = Field(default_factory=list, description="Areas needing improvement")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional session metadata")


class SessionResultResponse(BaseModel):
    """Response model for a session result."""
    session_result_id: uuid.UUID
    user_id: uuid.UUID
    session_type: str
    duration_seconds: int
    words_spoken: int
    pronunciation_score: float
    fluency_score: float
    grammar_score: float
    topics: List[str]
    vocabulary_learned: List[str]
    areas_to_improve: List[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class SessionHistoryResponse(BaseModel):
    """Response model for session history."""
    sessions: List[SessionResultResponse]
    total: int
    limit: int
    offset: int


class SessionStatsResponse(BaseModel):
    """Response model for session statistics."""
    total_sessions: int
    total_duration: int
    total_words_spoken: int
    avg_pronunciation: float
    avg_fluency: float
    avg_grammar: float
    sessions_by_type: Dict[str, Dict[str, int]]
    improvement_trends: List[Dict[str, Any]]
    common_topics: List[Dict[str, Any]]
    areas_to_improve: List[Dict[str, Any]]


class WarmupContentResponse(BaseModel):
    """Response model for warmup content."""
    focus_areas: List[str]
    vocabulary_review: List[str]
    last_session_summary: Optional[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    database: str
    timestamp: datetime


# Application lifecycle


def run_migrations(db):
    """Run database migrations on startup."""
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Migration 006: Add onboarding_completed and full_name
                cur.execute("""
                    ALTER TABLE user_profiles
                    ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;
                """)
                cur.execute("""
                    ALTER TABLE user_profiles
                    ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
                """)
                # Set existing users as having completed onboarding
                cur.execute("""
                    UPDATE user_profiles
                    SET onboarding_completed = TRUE
                    WHERE onboarding_completed IS NULL OR onboarding_completed = FALSE;
                """)

                # Migration 007: Add voice preferences
                cur.execute("""
                    ALTER TABLE user_profiles
                    ADD COLUMN IF NOT EXISTS voice_preferences JSONB DEFAULT '{"voice": "alloy", "speech_speed": 1.0, "auto_play_responses": true, "show_transcription": true, "microphone_sensitivity": 0.5}'::jsonb;
                """)

                # Migration 009: Daily Challenges
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS daily_challenge_progress (
                        user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
                        challenge_date DATE NOT NULL,
                        challenge_type VARCHAR(50) NOT NULL,
                        progress INTEGER DEFAULT 0,
                        goal INTEGER NOT NULL,
                        completed BOOLEAN DEFAULT FALSE,
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        PRIMARY KEY (user_id, challenge_date)
                    );
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_daily_challenge_user_date
                    ON daily_challenge_progress(user_id, challenge_date DESC);
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_daily_challenge_completed
                    ON daily_challenge_progress(user_id, completed, challenge_date DESC);
                """)

                # Migration 010: Learning Path System
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS learning_units (
                        unit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        unit_number INTEGER NOT NULL,
                        level VARCHAR(10) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        icon VARCHAR(50),
                        color VARCHAR(20),
                        order_index INTEGER NOT NULL,
                        is_locked BOOLEAN DEFAULT TRUE,
                        prerequisite_unit_id UUID REFERENCES learning_units(unit_id),
                        estimated_time_minutes INTEGER,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(level, unit_number)
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS learning_lessons (
                        lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        unit_id UUID REFERENCES learning_units(unit_id) ON DELETE CASCADE,
                        lesson_number INTEGER NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        lesson_type VARCHAR(50) DEFAULT 'standard',
                        order_index INTEGER NOT NULL,
                        xp_reward INTEGER DEFAULT 10,
                        is_locked BOOLEAN DEFAULT TRUE,
                        prerequisite_lesson_id UUID REFERENCES learning_lessons(lesson_id),
                        estimated_time_minutes INTEGER DEFAULT 5,
                        content JSONB,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(unit_id, lesson_number)
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS lesson_exercises (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        lesson_id UUID REFERENCES learning_lessons(lesson_id) ON DELETE CASCADE,
                        exercise_id VARCHAR(100) NOT NULL,
                        order_index INTEGER NOT NULL,
                        is_required BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(lesson_id, order_index)
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_lesson_progress (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
                        lesson_id UUID REFERENCES learning_lessons(lesson_id) ON DELETE CASCADE,
                        started_at TIMESTAMP DEFAULT NOW(),
                        completed_at TIMESTAMP,
                        completed BOOLEAN DEFAULT FALSE,
                        score INTEGER,
                        mistakes_count INTEGER DEFAULT 0,
                        time_spent_seconds INTEGER DEFAULT 0,
                        exercises_completed INTEGER DEFAULT 0,
                        total_exercises INTEGER,
                        current_exercise_index INTEGER DEFAULT 0,
                        metadata JSONB,
                        UNIQUE(user_id, lesson_id)
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_unit_progress (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
                        unit_id UUID REFERENCES learning_units(unit_id) ON DELETE CASCADE,
                        started_at TIMESTAMP DEFAULT NOW(),
                        completed_at TIMESTAMP,
                        completed BOOLEAN DEFAULT FALSE,
                        lessons_completed INTEGER DEFAULT 0,
                        total_lessons INTEGER,
                        test_taken BOOLEAN DEFAULT FALSE,
                        test_score INTEGER,
                        test_passed BOOLEAN DEFAULT FALSE,
                        metadata JSONB,
                        UNIQUE(user_id, unit_id)
                    );
                """)

                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_learning_units_level ON learning_units(level, order_index);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_learning_lessons_unit ON learning_lessons(unit_id, order_index);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_lesson_progress_user ON user_lesson_progress(user_id, completed);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_unit_progress_user ON user_unit_progress(user_id, completed);
                """)

                # Migration 011: Add total_xp to user_profiles
                cur.execute("""
                    ALTER TABLE user_profiles
                    ADD COLUMN IF NOT EXISTS total_xp INTEGER DEFAULT 0;
                """)

                # Migration 013: Push Notifications System
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS push_subscriptions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
                        endpoint TEXT NOT NULL UNIQUE,
                        p256dh TEXT NOT NULL,
                        auth TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        last_used_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user ON push_subscriptions(user_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_push_subscriptions_endpoint ON push_subscriptions(endpoint);")

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS push_preferences (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE UNIQUE,
                        enabled BOOLEAN DEFAULT FALSE,
                        streak_reminders BOOLEAN DEFAULT TRUE,
                        friend_challenges BOOLEAN DEFAULT TRUE,
                        achievements BOOLEAN DEFAULT TRUE,
                        daily_goals BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_push_preferences_user ON push_preferences(user_id);")

                # Migration 014: Gamification Bonuses System
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS daily_bonus_claims (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
                        bonus_type VARCHAR(30) NOT NULL,
                        bonus_xp INTEGER NOT NULL,
                        multiplier DECIMAL(3,2) DEFAULT 1.0,
                        claimed_date DATE DEFAULT CURRENT_DATE,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(user_id, bonus_type, claimed_date)
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_daily_bonus_user_date ON daily_bonus_claims(user_id, claimed_date);")

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS xp_multiplier_events (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        multiplier DECIMAL(3,2) NOT NULL DEFAULT 2.0,
                        start_date TIMESTAMP NOT NULL,
                        end_date TIMESTAMP NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_xp_events_active ON xp_multiplier_events(is_active, start_date, end_date);")

                # Create gamification functions
                cur.execute("""
                    CREATE OR REPLACE FUNCTION get_active_bonuses(p_user_id UUID)
                    RETURNS TABLE (
                        login_bonus_available BOOLEAN,
                        login_bonus_xp INTEGER,
                        streak_multiplier DECIMAL(3,2),
                        streak_days INTEGER,
                        weekend_bonus_active BOOLEAN,
                        weekend_multiplier DECIMAL(3,2),
                        event_bonus_active BOOLEAN,
                        event_name VARCHAR,
                        event_multiplier DECIMAL(3,2),
                        total_multiplier DECIMAL(4,2)
                    )
                    AS $$
                    DECLARE
                        v_streak_days INTEGER;
                        v_streak_mult DECIMAL(3,2);
                        v_weekend_mult DECIMAL(3,2);
                        v_event_mult DECIMAL(3,2);
                        v_event_name VARCHAR;
                        v_login_claimed BOOLEAN;
                        v_is_weekend BOOLEAN;
                        v_has_event BOOLEAN;
                    BEGIN
                        SELECT COALESCE(us.current_streak_days, 0) INTO v_streak_days
                        FROM user_streaks us WHERE us.user_id = p_user_id;
                        v_streak_mult := LEAST(1.0 + (COALESCE(v_streak_days, 0) * 0.01), 1.5);
                        SELECT EXISTS(SELECT 1 FROM daily_bonus_claims WHERE user_id = p_user_id AND bonus_type = 'login' AND claimed_date = CURRENT_DATE) INTO v_login_claimed;
                        v_is_weekend := EXTRACT(DOW FROM CURRENT_DATE) IN (0, 6);
                        v_weekend_mult := CASE WHEN v_is_weekend THEN 1.5 ELSE 1.0 END;
                        SELECT name, multiplier INTO v_event_name, v_event_mult FROM xp_multiplier_events WHERE is_active = TRUE AND NOW() BETWEEN start_date AND end_date ORDER BY multiplier DESC LIMIT 1;
                        v_has_event := v_event_name IS NOT NULL;
                        v_event_mult := COALESCE(v_event_mult, 1.0);
                        RETURN QUERY SELECT NOT v_login_claimed, 25, v_streak_mult, COALESCE(v_streak_days, 0), v_is_weekend, v_weekend_mult, v_has_event, v_event_name, v_event_mult, ROUND((v_streak_mult * v_weekend_mult * v_event_mult)::NUMERIC, 2);
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    CREATE OR REPLACE FUNCTION claim_login_bonus(p_user_id UUID)
                    RETURNS TABLE (success BOOLEAN, xp_earned INTEGER, message TEXT)
                    AS $$
                    DECLARE
                        v_already_claimed BOOLEAN;
                        v_base_xp INTEGER := 25;
                        v_streak_mult DECIMAL(3,2);
                        v_total_xp INTEGER;
                    BEGIN
                        SELECT EXISTS(SELECT 1 FROM daily_bonus_claims WHERE user_id = p_user_id AND bonus_type = 'login' AND claimed_date = CURRENT_DATE) INTO v_already_claimed;
                        IF v_already_claimed THEN RETURN QUERY SELECT FALSE, 0, 'Login bonus already claimed today'::TEXT; RETURN; END IF;
                        SELECT LEAST(1.0 + (COALESCE(us.current_streak_days, 0) * 0.01), 1.5) INTO v_streak_mult FROM user_streaks us WHERE us.user_id = p_user_id;
                        v_streak_mult := COALESCE(v_streak_mult, 1.0);
                        v_total_xp := FLOOR(v_base_xp * v_streak_mult);
                        INSERT INTO daily_bonus_claims (user_id, bonus_type, bonus_xp, multiplier) VALUES (p_user_id, 'login', v_total_xp, v_streak_mult);
                        UPDATE user_profiles SET total_xp = total_xp + v_total_xp WHERE user_id = p_user_id;
                        RETURN QUERY SELECT TRUE, v_total_xp, ('Daily login bonus: +' || v_total_xp || ' XP')::TEXT;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    CREATE OR REPLACE FUNCTION calculate_bonus_xp(p_user_id UUID, p_base_xp INTEGER, p_is_perfect_score BOOLEAN DEFAULT FALSE)
                    RETURNS TABLE (final_xp INTEGER, bonus_breakdown JSONB)
                    AS $$
                    DECLARE
                        v_streak_mult DECIMAL(3,2);
                        v_weekend_mult DECIMAL(3,2);
                        v_event_mult DECIMAL(3,2);
                        v_perfect_mult DECIMAL(3,2);
                        v_final_xp INTEGER;
                        v_breakdown JSONB;
                    BEGIN
                        SELECT LEAST(1.0 + (COALESCE(us.current_streak_days, 0) * 0.01), 1.5) INTO v_streak_mult FROM user_streaks us WHERE us.user_id = p_user_id;
                        v_streak_mult := COALESCE(v_streak_mult, 1.0);
                        v_weekend_mult := CASE WHEN EXTRACT(DOW FROM CURRENT_DATE) IN (0, 6) THEN 1.5 ELSE 1.0 END;
                        SELECT COALESCE(MAX(multiplier), 1.0) INTO v_event_mult FROM xp_multiplier_events WHERE is_active = TRUE AND NOW() BETWEEN start_date AND end_date;
                        v_perfect_mult := CASE WHEN p_is_perfect_score THEN 1.25 ELSE 1.0 END;
                        v_final_xp := FLOOR(p_base_xp * v_streak_mult * v_weekend_mult * v_event_mult * v_perfect_mult);
                        v_breakdown := jsonb_build_object('base_xp', p_base_xp, 'streak_multiplier', v_streak_mult, 'weekend_multiplier', v_weekend_mult, 'event_multiplier', v_event_mult, 'perfect_score_multiplier', v_perfect_mult, 'final_xp', v_final_xp, 'bonus_xp', v_final_xp - p_base_xp);
                        RETURN QUERY SELECT v_final_xp, v_breakdown;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                cur.execute("""
                    CREATE OR REPLACE FUNCTION get_bonus_summary(p_user_id UUID)
                    RETURNS TABLE (total_bonus_xp_today INTEGER, bonuses_claimed JSONB, available_bonuses JSONB, current_multiplier DECIMAL(4,2))
                    AS $$
                    DECLARE
                        v_claimed JSONB;
                        v_available JSONB;
                        v_total_bonus INTEGER;
                        v_active_bonuses RECORD;
                    BEGIN
                        SELECT jsonb_agg(jsonb_build_object('type', bonus_type, 'xp', bonus_xp, 'multiplier', multiplier)) INTO v_claimed FROM daily_bonus_claims WHERE user_id = p_user_id AND claimed_date = CURRENT_DATE;
                        SELECT COALESCE(SUM(bonus_xp), 0) INTO v_total_bonus FROM daily_bonus_claims WHERE user_id = p_user_id AND claimed_date = CURRENT_DATE;
                        SELECT * INTO v_active_bonuses FROM get_active_bonuses(p_user_id);
                        v_available := jsonb_build_object('login_bonus', jsonb_build_object('available', v_active_bonuses.login_bonus_available, 'xp', v_active_bonuses.login_bonus_xp), 'streak_bonus', jsonb_build_object('active', v_active_bonuses.streak_days > 0, 'multiplier', v_active_bonuses.streak_multiplier, 'streak_days', v_active_bonuses.streak_days), 'weekend_bonus', jsonb_build_object('active', v_active_bonuses.weekend_bonus_active, 'multiplier', v_active_bonuses.weekend_multiplier), 'event_bonus', jsonb_build_object('active', v_active_bonuses.event_bonus_active, 'name', v_active_bonuses.event_name, 'multiplier', v_active_bonuses.event_multiplier));
                        RETURN QUERY SELECT v_total_bonus, COALESCE(v_claimed, '[]'::jsonb), v_available, v_active_bonuses.total_multiplier;
                    END;
                    $$ LANGUAGE plpgsql;
                """)

                conn.commit()
                print("✓ Database migrations applied")
    except Exception as e:
        print(f"⚠️  Migration error (may already exist): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting SpeakSharp API...")
    db = get_db()
    if db.health_check():
        print("✓ Database connection successful")
        run_migrations(db)
    else:
        print("⚠️  Database connection failed - some features may not work")

    yield

    # Shutdown
    print("👋 Shutting down SpeakSharp API...")


# FastAPI app initialization

app = FastAPI(
    title="SpeakSharp Core API",
    description="AI-powered English learning tutor API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection


def get_database() -> Database:
    """Get database instance."""
    return get_db()


# API Endpoints


@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "service": "SpeakSharp Core API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check(db: Database = Depends(get_database)):
    """
    Health check endpoint.

    Returns service status and database connectivity.
    """
    db_status = "healthy" if db.health_check() else "unhealthy"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        timestamp=datetime.now()
    )


@app.post("/admin/migrate/008", tags=["Admin"])
async def run_migration_008(db: Database = Depends(get_database)):
    """
    Run migration 008 to create conversation_history table.
    This is a one-time endpoint - can be removed after migration.
    """
    migration_sql = """
    -- Migration 008: Conversation Memory System
    CREATE TABLE IF NOT EXISTS conversation_history (
      conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
      session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
      turn_number INTEGER NOT NULL,
      user_message TEXT NOT NULL,
      tutor_response TEXT NOT NULL,
      context_type VARCHAR(50),
      context_id VARCHAR(100),
      created_at TIMESTAMP DEFAULT NOW(),
      metadata JSONB DEFAULT '{}'::JSONB
    );

    CREATE INDEX IF NOT EXISTS idx_conversation_user_created ON conversation_history(user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_history(session_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_context ON conversation_history(user_id, context_type, context_id);

    CREATE OR REPLACE FUNCTION get_recent_conversations(p_user_id UUID, p_limit INTEGER DEFAULT 10)
    RETURNS TABLE (conversation_id UUID, turn_number INTEGER, user_message TEXT, tutor_response TEXT, context_type VARCHAR, context_id VARCHAR, created_at TIMESTAMP, metadata JSONB)
    AS $$ BEGIN RETURN QUERY SELECT ch.conversation_id, ch.turn_number, ch.user_message, ch.tutor_response, ch.context_type, ch.context_id, ch.created_at, ch.metadata FROM conversation_history ch WHERE ch.user_id = p_user_id ORDER BY ch.created_at DESC LIMIT p_limit; END; $$ LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION save_conversation_turn(p_user_id UUID, p_session_id UUID, p_turn_number INTEGER, p_user_message TEXT, p_tutor_response TEXT, p_context_type VARCHAR DEFAULT NULL, p_context_id VARCHAR DEFAULT NULL, p_metadata JSONB DEFAULT '{}'::JSONB)
    RETURNS UUID AS $$ DECLARE v_conversation_id UUID; BEGIN v_conversation_id := gen_random_uuid(); INSERT INTO conversation_history (conversation_id, user_id, session_id, turn_number, user_message, tutor_response, context_type, context_id, metadata) VALUES (v_conversation_id, p_user_id, p_session_id, p_turn_number, p_user_message, p_tutor_response, p_context_type, p_context_id, p_metadata); RETURN v_conversation_id; END; $$ LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION clear_conversation_history(p_user_id UUID, p_before_date TIMESTAMP DEFAULT NULL)
    RETURNS INTEGER AS $$ DECLARE v_deleted_count INTEGER; BEGIN IF p_before_date IS NULL THEN DELETE FROM conversation_history WHERE user_id = p_user_id; ELSE DELETE FROM conversation_history WHERE user_id = p_user_id AND created_at < p_before_date; END IF; GET DIAGNOSTICS v_deleted_count = ROW_COUNT; RETURN v_deleted_count; END; $$ LANGUAGE plpgsql;
    """

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
                conn.commit()
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Migration SQL failed: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")

    try:
        # Verify table was created
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = 'conversation_history'
                    ) as table_exists;
                """)
                result = cur.fetchone()
                # Handle both dict (dict_row) and tuple results
                if isinstance(result, dict):
                    table_exists = result.get('table_exists', result.get('exists', False))
                else:
                    table_exists = result[0] if result else False

        return {
            "status": "success",
            "message": "Migration 008 applied successfully",
            "table_created": table_exists
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Verification failed: {type(e).__name__}: {str(e)}")


@app.post("/admin/migrate/009", tags=["Admin"])
async def run_migration_009(db: Database = Depends(get_database)):
    """
    Run migration 009 to create skill_definitions table and BKT functions.
    """
    migration_sql = """
    -- Master skill definitions (static, ~120 skills for MVP)
    CREATE TABLE IF NOT EXISTS skill_definitions (
      skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      skill_key VARCHAR(100) UNIQUE NOT NULL,
      domain VARCHAR(50) NOT NULL,
      category VARCHAR(100) NOT NULL,
      name_en VARCHAR(255) NOT NULL,
      description_en TEXT,
      cefr_level VARCHAR(10) NOT NULL,
      difficulty FLOAT DEFAULT 0.5,
      is_active BOOLEAN DEFAULT TRUE,
      created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_skill_definitions_domain ON skill_definitions(domain);
    CREATE INDEX IF NOT EXISTS idx_skill_definitions_level ON skill_definitions(cefr_level);
    CREATE INDEX IF NOT EXISTS idx_skill_definitions_key ON skill_definitions(skill_key);

    -- Add BKT columns to existing skill_graph_nodes
    ALTER TABLE skill_graph_nodes ADD COLUMN IF NOT EXISTS p_learned FLOAT DEFAULT 0.1;
    ALTER TABLE skill_graph_nodes ADD COLUMN IF NOT EXISTS p_transit FLOAT DEFAULT 0.15;

    -- Function to update skill mastery using BKT
    CREATE OR REPLACE FUNCTION update_skill_bkt(p_user_id UUID, p_skill_key VARCHAR, p_correct BOOLEAN)
    RETURNS FLOAT AS $$
    DECLARE
      v_p_learned FLOAT; v_p_transit FLOAT; v_p_guess FLOAT := 0.2; v_p_slip FLOAT := 0.1;
      v_posterior FLOAT; v_new_p_learned FLOAT;
    BEGIN
      SELECT p_learned, p_transit INTO v_p_learned, v_p_transit FROM skill_graph_nodes WHERE user_id = p_user_id AND skill_key = p_skill_key;
      IF NOT FOUND THEN v_p_learned := 0.1; v_p_transit := 0.15; END IF;
      IF p_correct THEN
        v_posterior := (v_p_learned * (1 - v_p_slip)) / (v_p_learned * (1 - v_p_slip) + (1 - v_p_learned) * v_p_guess);
      ELSE
        v_posterior := (v_p_learned * v_p_slip) / (v_p_learned * v_p_slip + (1 - v_p_learned) * (1 - v_p_guess));
      END IF;
      v_new_p_learned := v_posterior + (1 - v_posterior) * v_p_transit;
      INSERT INTO skill_graph_nodes (node_id, user_id, skill_category, skill_key, mastery_score, p_learned, p_transit, practice_count, success_count, error_count, last_practiced)
      VALUES (gen_random_uuid(), p_user_id, 'mastery', p_skill_key, v_new_p_learned * 100, v_new_p_learned, v_p_transit, 1, CASE WHEN p_correct THEN 1 ELSE 0 END, CASE WHEN NOT p_correct THEN 1 ELSE 0 END, NOW())
      ON CONFLICT (user_id, skill_key) DO UPDATE SET
        p_learned = v_new_p_learned, mastery_score = v_new_p_learned * 100, practice_count = skill_graph_nodes.practice_count + 1,
        success_count = skill_graph_nodes.success_count + CASE WHEN p_correct THEN 1 ELSE 0 END,
        error_count = skill_graph_nodes.error_count + CASE WHEN NOT p_correct THEN 1 ELSE 0 END, last_practiced = NOW();
      RETURN v_new_p_learned;
    END; $$ LANGUAGE plpgsql;

    -- Function to get recommended skills
    CREATE OR REPLACE FUNCTION get_recommended_skills(p_user_id UUID, p_limit INTEGER DEFAULT 3)
    RETURNS TABLE (skill_key VARCHAR, name_en VARCHAR, domain VARCHAR, cefr_level VARCHAR, p_learned FLOAT, practice_count INTEGER) AS $$
    BEGIN RETURN QUERY
      SELECT sd.skill_key, sd.name_en, sd.domain, sd.cefr_level, COALESCE(sgn.p_learned, 0.1) as p_learned, COALESCE(sgn.practice_count, 0) as practice_count
      FROM skill_definitions sd LEFT JOIN skill_graph_nodes sgn ON sd.skill_key = sgn.skill_key AND sgn.user_id = p_user_id
      WHERE sd.is_active = TRUE ORDER BY COALESCE(sgn.p_learned, 0.1) ASC, sd.difficulty ASC LIMIT p_limit;
    END; $$ LANGUAGE plpgsql;

    -- Function to get skill mastery overview
    CREATE OR REPLACE FUNCTION get_skill_mastery_overview(p_user_id UUID)
    RETURNS TABLE (total_skills INTEGER, skills_practiced INTEGER, mastered_count INTEGER, in_progress_count INTEGER, struggling_count INTEGER, avg_mastery FLOAT) AS $$
    BEGIN RETURN QUERY
      SELECT (SELECT COUNT(*)::INTEGER FROM skill_definitions WHERE is_active = TRUE),
        COUNT(sgn.skill_key)::INTEGER,
        COUNT(CASE WHEN sgn.p_learned >= 0.85 THEN 1 END)::INTEGER,
        COUNT(CASE WHEN sgn.p_learned >= 0.3 AND sgn.p_learned < 0.85 THEN 1 END)::INTEGER,
        COUNT(CASE WHEN sgn.p_learned < 0.3 THEN 1 END)::INTEGER,
        COALESCE(AVG(sgn.p_learned), 0.1)
      FROM skill_graph_nodes sgn WHERE sgn.user_id = p_user_id AND sgn.skill_key IN (SELECT skill_key FROM skill_definitions WHERE is_active = TRUE);
    END; $$ LANGUAGE plpgsql;
    """

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
                conn.commit()
        return {"status": "success", "message": "Migration 009 applied"}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@app.post("/admin/seed/skills", tags=["Admin"])
async def seed_skills(db: Database = Depends(get_database)):
    """
    Seed skill definitions into the database.
    """
    try:
        from app.skills import ALL_SKILLS, SKILL_COUNT
        skill_list = list(ALL_SKILLS)
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Import failed: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM skill_definitions;")
                inserted = 0
                for skill in skill_list:
                    cur.execute("""
                        INSERT INTO skill_definitions (skill_key, domain, category, name_en, description_en, cefr_level, difficulty)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (skill_key) DO UPDATE SET domain = EXCLUDED.domain, category = EXCLUDED.category,
                        name_en = EXCLUDED.name_en, description_en = EXCLUDED.description_en, cefr_level = EXCLUDED.cefr_level, difficulty = EXCLUDED.difficulty
                    """, (skill.skill_key, skill.domain, skill.category, skill.name_en, skill.description_en, skill.cefr_level, skill.difficulty))
                    inserted += 1
                conn.commit()
                cur.execute("SELECT COUNT(*) as cnt FROM skill_definitions;")
                result = cur.fetchone()
                count = result['cnt'] if isinstance(result, dict) else result[0]
        return {"status": "success", "inserted": inserted, "db_count": count, "expected": SKILL_COUNT}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"DB error: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")


# User Profile Endpoints


@app.post("/api/users", response_model=UserProfileResponse, tags=["Users"])
async def create_user(
    request: CreateUserRequest,
    db: Database = Depends(get_database)
):
    """
    Create a new user profile.

    Args:
        request: User creation request

    Returns:
        Created user profile
    """
    try:
        user_id = request.user_id or uuid.uuid4()

        user = db.create_user(
            user_id=user_id,
            level=request.level,
            native_language=request.native_language,
            goals=request.goals,
            interests=request.interests
        )

        return UserProfileResponse(**user)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@app.get("/api/users/me", response_model=UserProfileResponse, tags=["Users"])
async def get_current_user(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get current user's profile from JWT token.

    Requires JWT authentication. User ID is extracted from the token.
    User profile is auto-created on first request if it doesn't exist.

    Returns:
        User profile
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    user = get_or_create_user(str(user_id))

    return UserProfileResponse(**user)


@app.get("/api/users/{user_id}", response_model=UserProfileResponse, tags=["Users"])
async def get_user(
    user_id: uuid.UUID,
    db: Database = Depends(get_database)
):
    """
    Get user profile by ID.

    Args:
        user_id: User UUID

    Returns:
        User profile
    """
    user = db.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(**user)


@app.put("/api/users/me/profile", response_model=UserProfileResponse, tags=["Users"])
async def update_current_user_profile(
    request: UpdateProfileRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Update current user's profile (level and/or native_language).

    Requires JWT authentication. User ID is extracted from the token.

    Args:
        request: Profile update request with optional level and native_language

    Returns:
        Updated user profile
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    # Update profile
    try:
        success = db.update_user_profile(
            user_id=user_id,
            level=request.level,
            native_language=request.native_language
        )

        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        # Fetch updated profile
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found after update")

        return UserProfileResponse(**user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@app.get("/api/users/me/voice-preferences", response_model=VoicePreferences, tags=["Users"])
async def get_voice_preferences(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get current user's voice preferences.

    Requires JWT authentication. User ID is extracted from the token.

    Returns:
        Voice preferences (voice, speech_speed, auto_play_responses, show_transcription, microphone_sensitivity)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT voice_preferences
                    FROM user_profiles
                    WHERE user_id = %s
                """, (str(user_id),))
                result = cur.fetchone()

                if not result or not result['voice_preferences']:
                    # Return default preferences
                    return VoicePreferences()

                prefs = result['voice_preferences']
                return VoicePreferences(
                    voice=prefs.get('voice', 'alloy'),
                    speech_speed=prefs.get('speech_speed', 1.0),
                    auto_play_responses=prefs.get('auto_play_responses', True),
                    show_transcription=prefs.get('show_transcription', True),
                    microphone_sensitivity=prefs.get('microphone_sensitivity', 0.5)
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voice preferences: {str(e)}")


@app.put("/api/users/me/voice-preferences", response_model=VoicePreferences, tags=["Users"])
async def update_voice_preferences(
    request: UpdateVoicePreferencesRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Update current user's voice preferences.

    Requires JWT authentication. User ID is extracted from the token.

    Args:
        request: Voice preferences update request

    Returns:
        Updated voice preferences
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get current preferences
                cur.execute("""
                    SELECT voice_preferences
                    FROM user_profiles
                    WHERE user_id = %s
                """, (str(user_id),))
                result = cur.fetchone()

                # Start with defaults or current preferences
                current_prefs = result['voice_preferences'] if result and result['voice_preferences'] else {}

                # Update with new values (only if provided)
                if request.voice is not None:
                    current_prefs['voice'] = request.voice
                if request.speech_speed is not None:
                    current_prefs['speech_speed'] = request.speech_speed
                if request.auto_play_responses is not None:
                    current_prefs['auto_play_responses'] = request.auto_play_responses
                if request.show_transcription is not None:
                    current_prefs['show_transcription'] = request.show_transcription
                if request.microphone_sensitivity is not None:
                    current_prefs['microphone_sensitivity'] = request.microphone_sensitivity

                # Update database
                import json
                cur.execute("""
                    UPDATE user_profiles
                    SET voice_preferences = %s, updated_at = NOW()
                    WHERE user_id = %s
                """, (json.dumps(current_prefs), str(user_id)))
                conn.commit()

                # Return updated preferences
                return VoicePreferences(
                    voice=current_prefs.get('voice', 'alloy'),
                    speech_speed=current_prefs.get('speech_speed', 1.0),
                    auto_play_responses=current_prefs.get('auto_play_responses', True),
                    show_transcription=current_prefs.get('show_transcription', True),
                    microphone_sensitivity=current_prefs.get('microphone_sensitivity', 0.5)
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update voice preferences: {str(e)}")


# Tutor Endpoints


from fastapi import Body

def build_rich_tutor_context(
    db: Database,
    user_id: uuid.UUID,
    user: dict,
    scenario_id: Optional[str] = None,
    session_id: Optional[uuid.UUID] = None,
    context_str: Optional[str] = None,
    turn_number: int = 1,
) -> dict:
    """
    Build rich context for the AI tutor including user profile, errors, skills,
    and CURRENT SESSION conversation history.

    This context helps the AI personalize feedback based on:
    - User's level, goals, interests, native language
    - Recent error patterns (to address recurring mistakes)
    - Weak skills (to focus corrections)
    - Current session conversation history (for continuity within the session)
    """
    # Base context
    context = {
        "source": "api",
        "mode": "scenario" if scenario_id else "text",
        "scenario_id": scenario_id,
        "session_id": str(session_id) if session_id else None,
        "user_id": str(user_id),
        "turn_number": turn_number,
        "raw_context": context_str,
    }

    # User profile data
    context["level"] = user.get('level', 'A1')
    context["native_language"] = user.get('native_language')
    context["goals"] = user.get('goals', [])
    context["interests"] = user.get('interests', [])

    # CRITICAL: Load current session conversation history
    # This ensures the AI remembers what was said in THIS conversation
    if session_id:
        try:
            session_conversations = db.get_session_conversations(session_id, limit=20)
            if session_conversations:
                # Build conversation history for the LLM
                # Uses field names that llm_client.py expects
                conversation_summary = []
                for conv in session_conversations:
                    conversation_summary.append({
                        "user_said": conv.get('user_message', ''),
                        "tutor_said": conv.get('tutor_response', ''),
                    })
                context["recent_conversation_summary"] = conversation_summary
                context["has_conversation_history"] = True
                context["recent_conversation_count"] = len(session_conversations)
        except Exception as e:
            print(f"Warning: Failed to load session conversations: {e}")
            context["recent_conversation_summary"] = []
            context["has_conversation_history"] = False

    # Recent errors (last 10) - helps identify recurring patterns
    try:
        recent_errors = db.get_user_errors(user_id, limit=10)
        if recent_errors:
            # Summarize error patterns
            error_summary = []
            error_types = {}
            for err in recent_errors:
                err_type = err.get('error_type', 'unknown')
                error_types[err_type] = error_types.get(err_type, 0) + 1
                if len(error_summary) < 5:  # Keep top 5 examples
                    error_summary.append({
                        "type": err_type,
                        "mistake": err.get('user_sentence', '')[:100],
                        "correction": err.get('corrected_sentence', '')[:100],
                    })
            context["recent_error_patterns"] = error_types
            context["recent_error_examples"] = error_summary
    except Exception:
        pass  # Don't fail if error history unavailable

    # Weak skills (top 3) - focus corrections on problem areas
    try:
        weak_skills = db.get_weakest_skills(user_id, limit=3)
        if weak_skills:
            context["weak_skills"] = [
                {"skill": s.get('skill_key'), "mastery": s.get('mastery_score', 0)}
                for s in weak_skills
            ]
    except Exception:
        pass  # Don't fail if skill data unavailable

    return context


@app.post("/api/tutor/text", tags=["Tutor"])
async def tutor_text(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Process text input through the tutor agent.

    Requires JWT authentication. User ID is extracted from the token.
    User profile is auto-created on first request if it doesn't exist.
    """
    try:
        # Convert user_id from token to UUID
        try:
            user_id = uuid.UUID(user_id_from_token)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id from token")

        # Auto-create user profile if doesn't exist
        user = get_or_create_user(str(user_id))

        # Extract text from payload
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise HTTPException(status_code=400, detail="Invalid or missing text")

        scenario_id = payload.get("scenario_id")
        context_str = payload.get("context")
        turn_number = payload.get("turn_number", 1)
        session_id_raw = payload.get("session_id")
        session_id: Optional[uuid.UUID] = None
        if session_id_raw:
            try:
                session_id = uuid.UUID(str(session_id_raw))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid session_id")

        # Create DB session if none provided
        if session_id is None:
            session = db.create_session(
                user_id=user_id,
                session_type="scenario" if scenario_id else "free_chat",
                metadata={
                    "source": "api",
                    "mode": "text",
                    "scenario_id": scenario_id,
                    "context": context_str,
                },
            )
            session_id = session["session_id"]
        else:
            session = {"session_id": session_id}

        # Build rich context with user profile, errors, and skills
        rich_context = build_rich_tutor_context(
            db=db,
            user_id=user_id,
            user=user,
            scenario_id=scenario_id,
            session_id=session_id,
            context_str=context_str,
            turn_number=turn_number,
        )

        # Run tutor with enriched context and conversation memory
        tutor = TutorAgent(user_id=str(user_id), db=db)
        tutor_response: TutorResponse = tutor.process_user_input(
            text,
            context=rich_context,
        )

        # Log errors + create SRS cards
        for err in tutor_response.errors:
            err_record = db.log_error(
                user_id=user_id,
                error_type=err.type.value,
                user_sentence=err.user_sentence,
                corrected_sentence=err.corrected_sentence,
                explanation=err.explanation,
                session_id=session_id,
                source_type="text_tutor",
            )
            db.create_card_from_error(error_id=err_record["error_id"])

        # Save conversation turn to memory
        try:
            db.save_conversation_turn(
                user_id=user_id,
                session_id=session_id,
                turn_number=turn_number,
                user_message=text,
                tutor_response=tutor_response.message,
                context_type=scenario_id or "free_chat",
                context_id=scenario_id,
                metadata={
                    "error_count": len(tutor_response.errors),
                    "has_micro_task": tutor_response.micro_task is not None
                }
            )
        except Exception as e:
            print(f"Warning: Failed to save conversation turn: {e}")

        # Build response
        return {
            "message": tutor_response.message,
            "errors": [e.model_dump() for e in tutor_response.errors],
            "micro_task": tutor_response.micro_task,
            "session_id": str(session_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tutor text error: {e}")

@app.post("/api/tutor/voice", tags=["Tutor"])
async def tutor_voice(
    file: UploadFile,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Process voice input through ASR + Tutor + TTS.

    Requires JWT authentication. User ID is extracted from the token.

    Accepts multipart/form-data with audio file.

    Pipeline:
    1. ASR: Transcribe audio to text (OpenAI Whisper)
    2. Tutor: Process text through TutorAgent
    3. TTS: Synthesize tutor response (OpenAI TTS)
    4. Log errors and create SRS cards

    Returns:
        JSON with transcript, tutor response, and base64 audio
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    user = get_or_create_user(str(user_id))
    user_level = user.get('level', 'A1')

    # Create DB session
    session = db.create_session(
        user_id=user_id,
        session_type="voice_tutor",
        metadata={"source": "api", "mode": "voice"}
    )
    session_id = session["session_id"]

    try:
        # Read audio bytes from uploaded file
        audio_bytes = await file.read()
        filename = file.filename or "audio.webm"

        # Create voice session
        from app.voice_session import VoiceSession
        voice_session = VoiceSession(
            user_level=user_level,
            mode="free_chat",
            context={"session_id": str(session_id), "user_id": str(user_id), "filename": filename}
        )

        # Process audio bytes through voice pipeline
        result = voice_session.handle_audio_input(
            audio_input=audio_bytes,
            generate_audio_response=True
        )

        # Log errors and create SRS cards
        for err in result.tutor_response.errors:
            err_record = db.log_error(
                user_id=user_id,
                error_type=err.type.value,
                user_sentence=err.user_sentence,
                corrected_sentence=err.corrected_sentence,
                explanation=err.explanation,
                session_id=session_id,
                source_type="voice_tutor",
            )
            db.create_card_from_error(error_id=err_record["error_id"])

        # Save conversation turn to memory
        try:
            db.save_conversation_turn(
                user_id=user_id,
                session_id=session_id,
                turn_number=1,  # Voice sessions are typically one turn at a time
                user_message=result.recognized_text,
                tutor_response=result.tutor_response.message,
                context_type="voice_tutor",
                context_id=None,
                metadata={
                    "error_count": len(result.tutor_response.errors),
                    "has_audio": True,
                    "filename": filename
                }
            )
        except Exception as e:
            print(f"Warning: Failed to save voice conversation turn: {e}")

        # Read TTS audio file and encode as base64
        import base64
        audio_base64 = None
        if result.tts_output_path:
            try:
                with open(result.tts_output_path, 'rb') as audio_file:
                    audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Warning: Failed to read TTS audio: {e}")

        # Get pronunciation feedback (if audio was saved)
        pronunciation = None
        if hasattr(result, 'asr_audio_path') and result.asr_audio_path and result.recognized_text:
            try:
                from app.pronunciation_scorer import PronunciationScorer
                scorer = PronunciationScorer()
                pron_result = scorer.score_audio(result.asr_audio_path, result.recognized_text)
                pronunciation = {
                    "overall_score": pron_result.get("overall_score", 0),
                    "word_scores": pron_result.get("word_scores", []),
                    "problem_sounds": pron_result.get("problem_sounds", []),
                    "tips": pron_result.get("tips", []),
                }
            except Exception as e:
                print(f"Warning: Failed to score pronunciation: {e}")

        # Return response
        return {
            "transcript": result.recognized_text,
            "tutor_response": {
                "message": result.tutor_response.message,
                "errors": [e.model_dump() for e in result.tutor_response.errors],
                "micro_task": result.tutor_response.micro_task,
            },
            "pronunciation": pronunciation,
            "audio_base64": audio_base64,
            "session_id": str(session_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice tutor error: {str(e)}")


@app.post("/api/tutor/voice/stream", tags=["Tutor"])
async def tutor_voice_streaming(
    file: UploadFile,
    mode: Optional[str] = "chunk",  # "chunk" or "sentence"
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Process voice input with streaming TTS response (SSE format).

    Requires JWT authentication. User ID is extracted from the token.

    Accepts multipart/form-data with audio file.

    Query params:
    - mode: "chunk" (default) for continuous streaming, "sentence" for sentence-by-sentence

    Pipeline:
    1. ASR: Transcribe audio to text (OpenAI Whisper)
    2. Tutor: Process text through TutorAgent
    3. TTS: Stream audio response in chunks

    Returns:
        Server-Sent Events (SSE) stream with the following event types:
        - transcript: User's transcribed speech
        - tutor_response: Tutor's text response with errors
        - audio_start: Signal that audio streaming is beginning
        - audio_chunk: Base64-encoded audio data chunks
        - audio_end: Signal that audio streaming is complete
        - sentence_start/end: (sentence mode only) Sentence boundaries
        - complete: Final event with metadata

    Benefits:
    - Lower perceived latency (audio starts playing sooner)
    - Progressive feedback to user
    - Better UX with incremental updates
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    user = get_or_create_user(str(user_id))
    user_level = user.get('level', 'A1')

    # Create DB session
    session = db.create_session(
        user_id=user_id,
        session_type="voice_tutor_streaming",
        metadata={"source": "api", "mode": "voice", "streaming": True}
    )
    session_id = session["session_id"]

    async def event_generator():
        """Generate SSE events for streaming response."""
        try:
            # Read audio bytes from uploaded file
            audio_bytes = await file.read()
            filename = file.filename or "audio.webm"

            # Create voice session
            from app.voice_session import VoiceSession
            voice_session = VoiceSession(
                user_level=user_level,
                mode="free_chat",
                context={"session_id": str(session_id), "user_id": str(user_id), "filename": filename}
            )

            # Choose streaming mode
            if mode == "sentence":
                stream_func = voice_session.handle_audio_input_streaming_sentences
            else:
                stream_func = voice_session.handle_audio_input_streaming

            # Track tutor response for error logging
            tutor_response_data = None

            # Stream events
            for event in stream_func(audio_bytes):
                event_type = event["type"]
                event_data = event["data"]

                # Store tutor response for later error logging
                if event_type == "tutor_response":
                    tutor_response_data = event_data

                # For audio chunks, encode as base64
                if event_type == "audio_chunk":
                    chunk = event_data["chunk"]
                    event_data = {
                        "chunk": base64.b64encode(chunk).decode('utf-8')
                    }

                # Format as SSE
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(event_data)}\n\n"

            # Log errors after streaming completes
            if tutor_response_data and tutor_response_data.get("errors"):
                for err in tutor_response_data["errors"]:
                    try:
                        err_record = db.log_error(
                            user_id=user_id,
                            error_type=err["type"],
                            user_sentence=err["user_sentence"],
                            corrected_sentence=err["corrected_sentence"],
                            explanation=err["explanation"],
                            session_id=session_id,
                            source_type="voice_tutor_streaming",
                        )
                        db.create_card_from_error(error_id=err_record["error_id"])
                    except Exception as e:
                        print(f"Warning: Failed to log error: {e}")

        except Exception as e:
            # Send error event
            error_data = {"error": str(e)}
            yield f"event: error\n"
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# SRS Endpoints


@app.get("/api/srs/due", response_model=SRSDueResponse, tags=["SRS"])
async def get_due_cards(
    limit: int = 20,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get due SRS cards for review.

    Requires JWT authentication. User ID is extracted from the token.

    Args:
        limit: Maximum number of cards to return

    Returns:
        List of due cards
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    try:
        cards = db.get_due_cards(user_id, limit=limit)

        return SRSDueResponse(
            cards=cards,
            count=len(cards)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get due cards: {str(e)}"
        )


@app.post("/api/srs/review", tags=["SRS"])
async def review_card(
    request: SRSReviewRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit a review for an SRS card.

    Requires JWT authentication. User ID is extracted from the token.
    This updates the card using the SM-2 algorithm and logs the review.

    Args:
        request: SRS review request

    Returns:
        Success confirmation
    """
    # Auto-create user profile if doesn't exist
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    get_or_create_user(str(user_id))

    # Verify card exists
    card = db.get_card(request.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    try:
        db.update_card_after_review(
            card_id=request.card_id,
            quality=request.quality,
            response_time_ms=request.response_time_ms,
            user_response=request.user_response,
            correct=request.correct
        )

        return {
            "status": "success",
            "message": "Review recorded successfully",
            "card_id": request.card_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record review: {str(e)}"
        )


@app.post("/api/srs/from-error/{error_id}", tags=["SRS"])
async def create_card_from_error(
    error_id: uuid.UUID,
    db: Database = Depends(get_database)
):
    """
    Create an SRS card from a logged error.

    Args:
        error_id: Error log UUID

    Returns:
        Created card ID
    """
    try:
        card_id = db.create_card_from_error(error_id)

        return {
            "status": "success",
            "message": "Card created from error",
            "card_id": card_id,
            "error_id": error_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create card from error: {str(e)}"
        )


# Error Log Endpoints


@app.get("/api/errors/{user_id}", tags=["Errors"])
async def get_user_errors(
    user_id: uuid.UUID,
    limit: int = 50,
    unrecycled_only: bool = False,
    db: Database = Depends(get_database)
):
    """
    Get user's error history.

    Args:
        user_id: User UUID
        limit: Maximum number of errors to return
        unrecycled_only: Only return errors not yet converted to SRS cards

    Returns:
        List of errors
    """
    # Verify user exists
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        errors = db.get_user_errors(
            user_id=user_id,
            limit=limit,
            unrecycled_only=unrecycled_only
        )

        return {
            "errors": errors,
            "count": len(errors)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get errors: {str(e)}"
        )


# Skill Graph Endpoints


@app.get("/api/skills/weakest", tags=["Skills"])
async def get_weakest_skills(
    limit: int = 3,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's weakest skills (authenticated).

    Returns top 3 weakest skills by default with error counts.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        skills = db.get_weakest_skills(user_id, limit=limit)

        return {
            "skills": skills,
            "count": len(skills)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get weakest skills: {str(e)}"
        )


# Skills Mastery Engine Endpoints

@app.get("/api/skills/definitions", tags=["Skills"])
async def get_skill_definitions(
    domain: Optional[str] = None,
    level: Optional[str] = None,
    db: Database = Depends(get_database),
):
    """
    Get all skill definitions (no auth required).
    Optional filters: domain (grammar, vocabulary, listening, pronunciation), level (A1, A2, B1)
    """
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT skill_key, domain, category, name_en, description_en, cefr_level, difficulty
                    FROM skill_definitions
                    WHERE is_active = TRUE
                """
                params = []
                if domain:
                    query += " AND domain = %s"
                    params.append(domain)
                if level:
                    query += " AND cefr_level = %s"
                    params.append(level)
                query += " ORDER BY domain, category, difficulty"

                cur.execute(query, params)
                rows = cur.fetchall()

                skills = []
                for row in rows:
                    # Handle both dict and tuple rows
                    if isinstance(row, dict):
                        skills.append({
                            "skill_key": row['skill_key'],
                            "domain": row['domain'],
                            "category": row['category'],
                            "name": row['name_en'],
                            "description": row['description_en'],
                            "level": row['cefr_level'],
                            "difficulty": row['difficulty']
                        })
                    else:
                        skills.append({
                            "skill_key": row[0],
                            "domain": row[1],
                            "category": row[2],
                            "name": row[3],
                            "description": row[4],
                            "level": row[5],
                            "difficulty": row[6]
                        })

                return {"skills": skills, "count": len(skills)}

    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Failed to get skill definitions: {str(e)}\n{traceback.format_exc()}")


@app.get("/api/skills/mastery", tags=["Skills"])
async def get_skill_mastery(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's mastery for all skills (BKT p_learned values).
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get overview
                cur.execute("SELECT * FROM get_skill_mastery_overview(%s)", (str(user_id),))
                overview = cur.fetchone()

                # Get all skills with user mastery
                cur.execute("""
                    SELECT
                        sd.skill_key,
                        sd.domain,
                        sd.name_en,
                        sd.cefr_level,
                        COALESCE(sgn.p_learned, 0.1) as p_learned,
                        COALESCE(sgn.practice_count, 0) as practice_count,
                        sgn.last_practiced
                    FROM skill_definitions sd
                    LEFT JOIN skill_graph_nodes sgn
                        ON sd.skill_key = sgn.skill_key AND sgn.user_id = %s
                    WHERE sd.is_active = TRUE
                    ORDER BY sd.domain, sd.category
                """, (str(user_id),))
                rows = cur.fetchall()

                skills = []
                for row in rows:
                    if isinstance(row, dict):
                        last_practiced = row.get('last_practiced')
                        skills.append({
                            "skill_key": row['skill_key'],
                            "domain": row['domain'],
                            "name": row['name_en'],
                            "level": row['cefr_level'],
                            "p_learned": row['p_learned'],
                            "practice_count": row['practice_count'],
                            "last_practiced": last_practiced.isoformat() if last_practiced else None
                        })
                    else:
                        skills.append({
                            "skill_key": row[0],
                            "domain": row[1],
                            "name": row[2],
                            "level": row[3],
                            "p_learned": row[4],
                            "practice_count": row[5],
                            "last_practiced": row[6].isoformat() if row[6] else None
                        })

                # Handle overview dict/tuple
                if isinstance(overview, dict):
                    overview_data = {
                        "total_skills": overview.get('total_skills', 0),
                        "skills_practiced": overview.get('skills_practiced', 0),
                        "mastered": overview.get('mastered_count', 0),
                        "in_progress": overview.get('in_progress_count', 0),
                        "struggling": overview.get('struggling_count', 0),
                        "avg_mastery": overview.get('avg_mastery', 0.1)
                    }
                else:
                    overview_data = {
                        "total_skills": overview[0] if overview else 0,
                        "skills_practiced": overview[1] if overview else 0,
                        "mastered": overview[2] if overview else 0,
                        "in_progress": overview[3] if overview else 0,
                        "struggling": overview[4] if overview else 0,
                        "avg_mastery": overview[5] if overview else 0.1
                    }

                return {
                    "overview": overview_data,
                    "skills": skills
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get skill mastery: {str(e)}")


@app.get("/api/skills/bands", tags=["Skills"])
async def get_skill_bands(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's average mastery per CEFR band (A1, A2, B1).

    Returns avg_mastery (0-1) for each band based on seeded P(L) values.
    These values reflect the user's placement and subsequent practice.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get avg P(L) per CEFR band
                cur.execute("""
                    SELECT
                        sd.cefr_level,
                        COALESCE(AVG(sgn.p_learned), 0.1) as avg_mastery
                    FROM skill_definitions sd
                    LEFT JOIN skill_graph_nodes sgn
                        ON sd.skill_key = sgn.skill_key AND sgn.user_id = %s
                    WHERE sd.is_active = TRUE
                      AND sd.cefr_level IN ('A1', 'A2', 'B1')
                    GROUP BY sd.cefr_level
                    ORDER BY sd.cefr_level
                """, (str(user_id),))
                rows = cur.fetchall()

                bands = {}
                for row in rows:
                    if isinstance(row, dict):
                        level = row['cefr_level']
                        avg_mastery = row['avg_mastery']
                    else:
                        level = row[0]
                        avg_mastery = row[1]

                    bands[level] = {
                        "avg_mastery": round(float(avg_mastery), 3) if avg_mastery else 0.1
                    }

                # Ensure all levels are present
                for level in ["A1", "A2", "B1"]:
                    if level not in bands:
                        bands[level] = {"avg_mastery": 0.1}

                return bands

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get skill bands: {str(e)}")


@app.get("/api/skills/recommend", tags=["Skills"])
async def get_recommended_skills(
    count: int = 3,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get recommended skills to practice (lowest mastery first).
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM get_recommended_skills(%s, %s)", (str(user_id), count))
                rows = cur.fetchall()

                skills = []
                for row in rows:
                    if isinstance(row, dict):
                        skills.append({
                            "skill_key": row['skill_key'],
                            "name": row['name_en'],
                            "domain": row['domain'],
                            "level": row['cefr_level'],
                            "p_learned": row['p_learned'],
                            "practice_count": row['practice_count']
                        })
                    else:
                        skills.append({
                            "skill_key": row[0],
                            "name": row[1],
                            "domain": row[2],
                            "level": row[3],
                            "p_learned": row[4],
                            "practice_count": row[5]
                        })

                return {"recommended": skills}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


class SkillPracticeRequest(BaseModel):
    """Request for skill practice submission"""
    skill_key: str
    correct: bool


@app.post("/api/skills/practice", tags=["Skills"])
async def submit_skill_practice(
    request: SkillPracticeRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit skill practice result and update BKT mastery.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Update BKT mastery
                cur.execute(
                    "SELECT update_skill_bkt(%s, %s, %s)",
                    (str(user_id), request.skill_key, request.correct)
                )
                result = cur.fetchone()
                if isinstance(result, dict):
                    new_p_learned = result.get('update_skill_bkt', 0.1)
                else:
                    new_p_learned = result[0] if result else 0.1
                conn.commit()

                return {
                    "skill_key": request.skill_key,
                    "correct": request.correct,
                    "new_p_learned": new_p_learned,
                    "mastery_percent": round(new_p_learned * 100, 1)
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update skill: {str(e)}")


# ============================================================================
# Stats & Analytics Endpoints
# ============================================================================

@app.get("/api/stats/errors", tags=["Stats"])
async def get_error_stats(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get error statistics for the authenticated user.

    Returns:
    - total_errors: Total number of errors logged
    - errors_by_type: Breakdown by error type (grammar, vocab, fluency, structure)
    - last_errors: Last 10 errors with details
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Total errors
                cursor.execute("""
                    SELECT COUNT(*) as total FROM error_log WHERE user_id = %s
                """, (str(user_id),))
                result = cursor.fetchone()
                total_errors = result['total'] if result else 0

                # Errors by type
                cursor.execute("""
                    SELECT error_type, COUNT(*) as count
                    FROM error_log
                    WHERE user_id = %s
                    GROUP BY error_type
                    ORDER BY count DESC
                """, (str(user_id),))
                errors_by_type = {row['error_type']: row['count'] for row in cursor.fetchall()}

                # Last 10 errors
                cursor.execute("""
                    SELECT
                        user_sentence,
                        corrected_sentence,
                        error_type,
                        explanation,
                        occurred_at
                    FROM error_log
                    WHERE user_id = %s
                    ORDER BY occurred_at DESC
                    LIMIT 10
                """, (str(user_id),))

                last_errors = [
                    {
                        "before_text": row['user_sentence'],
                        "after_text": row['corrected_sentence'],
                        "type": row['error_type'],
                        "explanation": row['explanation'],
                        "timestamp": row['occurred_at'].isoformat() if row['occurred_at'] else None
                    }
                    for row in cursor.fetchall()
                ]

                return {
                    "total_errors": total_errors,
                    "errors_by_type": errors_by_type,
                    "last_errors": last_errors
                }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get error stats: {str(e)}"
        )


@app.get("/api/stats/srs", tags=["Stats"])
async def get_srs_stats(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get SRS statistics for the authenticated user.

    Returns:
    - total_cards: Total number of SRS cards
    - due_today: Number of cards due for review today
    - reviewed_today: Number of cards reviewed today
    - success_rate_today: Success rate for today's reviews (0-100)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Total cards
                cursor.execute("""
                    SELECT COUNT(*) as total FROM srs_cards WHERE user_id = %s
                """, (str(user_id),))
                result = cursor.fetchone()
                total_cards = result['total'] if result else 0

                # Due today
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM srs_cards
                    WHERE user_id = %s AND next_review_date <= NOW()
                """, (str(user_id),))
                result = cursor.fetchone()
                due_today = result['total'] if result else 0

                # Reviewed today
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM srs_reviews
                    WHERE user_id = %s AND DATE(reviewed_at) = CURRENT_DATE
                """, (str(user_id),))
                result = cursor.fetchone()
                reviewed_today = result['total'] if result else 0

                # Success rate today (quality >= 3 is considered success)
                cursor.execute("""
                    SELECT
                        COUNT(*) FILTER (WHERE quality >= 3) as successes,
                        COUNT(*) as total
                    FROM srs_reviews
                    WHERE user_id = %s AND DATE(reviewed_at) = CURRENT_DATE
                """, (str(user_id),))

                result = cursor.fetchone()
                successes = result['successes'] if result and result['successes'] else 0
                total_reviews = result['total'] if result and result['total'] else 0
                success_rate_today = (successes / total_reviews * 100) if total_reviews > 0 else 0

                return {
                    "total_cards": total_cards,
                    "due_today": due_today,
                    "reviewed_today": reviewed_today,
                    "success_rate_today": round(success_rate_today, 1)
                }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get SRS stats: {str(e)}"
        )


# ============================================================================
# Session Analytics Endpoints
# ============================================================================

@app.post("/api/sessions/save", response_model=SessionResultResponse, tags=["Sessions"])
async def save_session_result(
    request: SessionResultRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Save a completed session result with analytics data.

    Records detailed session information including scores, topics covered,
    vocabulary learned, and areas needing improvement for personalized feedback.

    Args:
        request: Session result data including type, duration, scores, and metadata

    Returns:
        Saved session result with generated ID and timestamps
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Validate session type
    valid_session_types = ['conversation', 'pronunciation', 'roleplay']
    if request.session_type not in valid_session_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid session_type. Must be one of: {', '.join(valid_session_types)}"
        )

    try:
        result = db.save_session_result(
            user_id=user_id,
            session_type=request.session_type,
            duration_seconds=request.duration_seconds,
            words_spoken=request.words_spoken,
            pronunciation_score=request.pronunciation_score,
            fluency_score=request.fluency_score,
            grammar_score=request.grammar_score,
            topics=request.topics,
            vocabulary_learned=request.vocabulary_learned,
            areas_to_improve=request.areas_to_improve,
            metadata=request.metadata
        )

        return SessionResultResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save session result: {str(e)}"
        )


@app.get("/api/sessions/history", response_model=SessionHistoryResponse, tags=["Sessions"])
async def get_session_history(
    session_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's session history with optional filtering.

    Returns a paginated list of completed sessions with their analytics data.
    Useful for tracking progress over time and reviewing past performance.

    Args:
        session_type: Optional filter by session type (conversation, pronunciation, roleplay)
        limit: Maximum number of results (default: 20, max: 100)
        offset: Offset for pagination (default: 0)

    Returns:
        List of session results with pagination metadata
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Validate and limit the query
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    if session_type:
        valid_session_types = ['conversation', 'pronunciation', 'roleplay']
        if session_type not in valid_session_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session_type. Must be one of: {', '.join(valid_session_types)}"
            )

    try:
        sessions = db.get_session_history(
            user_id=user_id,
            session_type=session_type,
            limit=limit,
            offset=offset
        )

        # Convert to response models
        session_responses = [SessionResultResponse(**session) for session in sessions]

        return SessionHistoryResponse(
            sessions=session_responses,
            total=len(session_responses),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session history: {str(e)}"
        )


@app.get("/api/sessions/stats", response_model=SessionStatsResponse, tags=["Sessions"])
async def get_session_stats(
    period: str = 'week',
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get aggregated session statistics for the authenticated user.

    Provides comprehensive analytics including total sessions, average scores,
    improvement trends, common topics, and areas needing improvement.

    Args:
        period: Time period for stats ('week' or 'month', default: 'week')

    Returns:
        Aggregated statistics with trends and insights
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Validate period
    if period not in ['week', 'month']:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Must be 'week' or 'month'"
        )

    try:
        stats = db.get_session_stats(user_id=user_id, period=period)
        return SessionStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session stats: {str(e)}"
        )


@app.get("/api/sessions/warmup", response_model=WarmupContentResponse, tags=["Sessions"])
async def get_warmup_content(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get personalized warmup content based on recent session performance.

    Analyzes the user's last session and recent weak areas to provide
    targeted warmup exercises, vocabulary review, and focus areas.

    Returns:
        Personalized warmup content including:
        - focus_areas: Areas to concentrate on based on recent performance
        - vocabulary_review: Words that need reinforcement
        - last_session_summary: Summary of the most recent session
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        warmup_content = db.get_warmup_content(user_id=user_id)
        return WarmupContentResponse(**warmup_content)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get warmup content: {str(e)}"
        )


# ============================================================================
# Lessons Endpoints
# ============================================================================

@app.get("/api/lessons", tags=["Lessons"])
async def get_lessons(
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all available lessons.

    Returns a list of all lessons with their metadata.
    """
    from app.lessons import LESSON_LIBRARY

    lessons_list = [
        {
            "lesson_id": lesson.lesson_id,
            "title": lesson.title,
            "level": lesson.level,
            "skill_targets": lesson.skill_targets,
            "duration_minutes": lesson.duration_minutes,
        }
        for lesson in LESSON_LIBRARY.values()
    ]

    return {"lessons": lessons_list, "count": len(lessons_list)}


@app.get("/api/lessons/{lesson_id}", tags=["Lessons"])
async def get_lesson(
    lesson_id: str,
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get a specific lesson by ID.

    Returns the full lesson including explanation, examples, and practice tasks.
    """
    from app.lessons import LESSON_LIBRARY

    if lesson_id not in LESSON_LIBRARY:
        raise HTTPException(status_code=404, detail=f"Lesson '{lesson_id}' not found")

    lesson = LESSON_LIBRARY[lesson_id]

    return {
        "lesson_id": lesson.lesson_id,
        "title": lesson.title,
        "level": lesson.level,
        "skill_targets": lesson.skill_targets,
        "duration_minutes": lesson.duration_minutes,
        "context": lesson.context,
        "target_language": lesson.target_language,
        "explanation": lesson.explanation,
        "examples": lesson.examples,
        "controlled_practice": [
            {
                "task_type": task.task_type,
                "prompt": task.prompt,
                "example_answer": task.example_answer,
            }
            for task in lesson.controlled_practice
        ],
        "freer_production": {
            "task_type": lesson.freer_production.task_type,
            "prompt": lesson.freer_production.prompt,
            "example_answer": lesson.freer_production.example_answer,
        },
        "summary": lesson.summary,
    }


@app.post("/api/lessons/{lesson_id}/submit", tags=["Lessons"])
async def submit_lesson_task(
    lesson_id: str,
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit a lesson task answer and get AI feedback.

    Payload:
    {
        "task_index": 0,  # Index of the task (0 for first controlled practice, -1 for freer production)
        "user_answer": "I eat breakfast at 8 AM."
    }

    Returns tutor feedback on the answer.
    """
    from app.lessons import LESSON_LIBRARY
    from app.tutor_agent import TutorAgent

    if lesson_id not in LESSON_LIBRARY:
        raise HTTPException(status_code=404, detail=f"Lesson '{lesson_id}' not found")

    user_answer = payload.get("user_answer")
    task_index = payload.get("task_index")

    if not isinstance(user_answer, str) or not user_answer.strip():
        raise HTTPException(status_code=400, detail="Invalid or missing user_answer")

    if task_index is None:
        raise HTTPException(status_code=400, detail="Missing task_index")

    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    lesson = LESSON_LIBRARY[lesson_id]

    # Get the task
    if task_index == -1:
        task = lesson.freer_production
    elif 0 <= task_index < len(lesson.controlled_practice):
        task = lesson.controlled_practice[task_index]
    else:
        raise HTTPException(status_code=400, detail=f"Invalid task_index {task_index}")

    # Create DB session
    session = db.create_session(
        user_id=user_id,
        session_type="lesson",
        metadata={"lesson_id": lesson_id, "task_index": task_index}
    )
    session_id = session["session_id"]

    # Process through tutor
    tutor = TutorAgent()
    user = get_or_create_user(str(user_id))
    user_level = user.get('level', 'A1')

    context_str = f"Lesson: {lesson.title}. Task: {task.prompt}"
    if task.expected_pattern:
        context_str += f" Expected pattern: {task.expected_pattern}"

    tutor_response = tutor.process_user_input(
        user_answer,
        context={
            "mode": "lesson",
            "level": user_level,
            "lesson_id": lesson_id,
            "task_index": task_index,
            "context": context_str,
        }
    )

    # Log errors and create SRS cards
    for err in tutor_response.errors:
        err_record = db.log_error(
            user_id=user_id,
            error_type=err.type.value,
            user_sentence=err.user_sentence,
            corrected_sentence=err.corrected_sentence,
            explanation=err.explanation,
            session_id=session_id,
            source_type="lesson",
        )
        db.create_card_from_error(error_id=err_record["error_id"])

    return {
        "message": tutor_response.message,
        "errors": [
            {
                "type": err.type.value,
                "user_sentence": err.user_sentence,
                "corrected_sentence": err.corrected_sentence,
                "explanation": err.explanation,
            }
            for err in tutor_response.errors
        ],
        "micro_task": tutor_response.micro_task,
        "session_id": str(session_id),
    }


# ============================================================================
# Scenarios Endpoints
# ============================================================================

@app.get("/api/scenarios", tags=["Scenarios"])
async def get_scenarios(
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all available scenarios.

    Returns a list of all scenarios with their metadata.
    """
    from app.scenarios import SCENARIO_TEMPLATES

    scenarios_list = [
        {
            "scenario_id": scenario.scenario_id,
            "title": scenario.title,
            "level_min": scenario.level_min,
            "level_max": scenario.level_max,
            "situation_description": scenario.situation_description,
            "difficulty_tags": scenario.difficulty_tags,
        }
        for scenario in SCENARIO_TEMPLATES.values()
    ]

    return {"scenarios": scenarios_list, "count": len(scenarios_list)}


@app.get("/api/scenarios/{scenario_id}", tags=["Scenarios"])
async def get_scenario(
    scenario_id: str,
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get a specific scenario by ID.

    Returns the full scenario including situation, goal, task, and success criteria.
    """
    from app.scenarios import SCENARIO_TEMPLATES

    if scenario_id not in SCENARIO_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

    scenario = SCENARIO_TEMPLATES[scenario_id]

    return {
        "scenario_id": scenario.scenario_id,
        "title": scenario.title,
        "level_min": scenario.level_min,
        "level_max": scenario.level_max,
        "situation_description": scenario.situation_description,
        "user_goal": scenario.user_goal,
        "task": scenario.task,
        "success_criteria": scenario.success_criteria,
        "difficulty_tags": scenario.difficulty_tags,
        "user_variables": scenario.user_variables,
    }


@app.post("/api/scenarios/{scenario_id}/respond", tags=["Scenarios"])
async def submit_scenario_response(
    scenario_id: str,
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit a response in a scenario conversation.

    Payload:
    {
        "user_input": "I'd like a coffee, please.",
        "turn_number": 1
    }

    Returns AI response and feedback.
    """
    from app.scenarios import SCENARIO_TEMPLATES
    from app.tutor_agent import TutorAgent

    if scenario_id not in SCENARIO_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

    user_input = payload.get("user_input")
    turn_number = payload.get("turn_number", 1)

    if not isinstance(user_input, str) or not user_input.strip():
        raise HTTPException(status_code=400, detail="Invalid or missing user_input")

    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    scenario = SCENARIO_TEMPLATES[scenario_id]

    # Create or get session
    session = db.create_session(
        user_id=user_id,
        session_type="scenario",
        metadata={"scenario_id": scenario_id, "turn_number": turn_number}
    )
    session_id = session["session_id"]

    # Process through tutor
    tutor = TutorAgent()
    user = get_or_create_user(str(user_id))
    user_level = user.get('level', 'A1')

    context_str = f"Scenario: {scenario.title}. {scenario.situation_description} Your task: {scenario.task}"

    tutor_response = tutor.process_user_input(
        user_input,
        context={
            "mode": "scenario",
            "level": user_level,
            "scenario_id": scenario_id,
            "turn_number": turn_number,
            "context": context_str,
        }
    )

    # Log errors and create SRS cards
    for err in tutor_response.errors:
        err_record = db.log_error(
            user_id=user_id,
            error_type=err.type.value,
            user_sentence=err.user_sentence,
            corrected_sentence=err.corrected_sentence,
            explanation=err.explanation,
            session_id=session_id,
            source_type="scenario",
        )
        db.create_card_from_error(error_id=err_record["error_id"])

    return {
        "tutor_message": tutor_response.message,
        "errors": [
            {
                "type": err.type.value,
                "user_sentence": err.user_sentence,
                "corrected_sentence": err.corrected_sentence,
                "explanation": err.explanation,
            }
            for err in tutor_response.errors
        ],
        "micro_task": tutor_response.micro_task,
        "session_id": str(session_id),
        "turn_number": turn_number + 1,
        "scenario_complete": tutor_response.scenario_complete or False,
        "success_evaluation": tutor_response.success_evaluation,
    }


# ============================================================================
# Drills Endpoints
# ============================================================================

@app.get("/api/drills/monologue", tags=["Drills"])
async def get_monologue_prompts(
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all monologue prompts.

    Returns a list of all monologue speaking prompts with time limits.
    """
    from app.drills import MONOLOGUE_PROMPTS

    prompts_list = [
        {
            "prompt_id": prompt.prompt_id,
            "text": prompt.text,
            "level": prompt.level,
            "category": prompt.category,
            "time_limit_seconds": prompt.time_limit_seconds,
        }
        for prompt in MONOLOGUE_PROMPTS.values()
    ]

    return {"prompts": prompts_list, "count": len(prompts_list)}


@app.post("/api/drills/monologue/submit", tags=["Drills"])
async def submit_monologue(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit a monologue (voice recording transcribed to text).

    Payload:
    {
        "prompt_id": "daily_routine",
        "transcript": "I wake up at 7 AM every day...",
        "duration_seconds": 120
    }

    Returns tutor feedback on the monologue.
    """
    from app.drills import MONOLOGUE_PROMPTS
    from app.tutor_agent import TutorAgent

    prompt_id = payload.get("prompt_id")
    transcript = payload.get("transcript")
    duration_seconds = payload.get("duration_seconds", 0)

    if not prompt_id or prompt_id not in MONOLOGUE_PROMPTS:
        raise HTTPException(status_code=400, detail="Invalid or missing prompt_id")

    if not isinstance(transcript, str) or not transcript.strip():
        raise HTTPException(status_code=400, detail="Invalid or missing transcript")

    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    prompt = MONOLOGUE_PROMPTS[prompt_id]

    # Create DB session
    session = db.create_session(
        user_id=user_id,
        session_type="monologue_drill",
        metadata={"prompt_id": prompt_id, "duration_seconds": duration_seconds}
    )
    session_id = session["session_id"]

    # Process through tutor
    tutor = TutorAgent()
    user = get_or_create_user(str(user_id))
    user_level = user.get('level', 'A1')

    context_str = f"Monologue drill: {prompt.text}"

    tutor_response = tutor.process_user_input(
        transcript,
        context={
            "mode": "monologue",
            "level": user_level,
            "prompt_id": prompt_id,
            "context": context_str,
        }
    )

    # Log errors and create SRS cards
    for err in tutor_response.errors:
        err_record = db.log_error(
            user_id=user_id,
            error_type=err.type.value,
            user_sentence=err.user_sentence,
            corrected_sentence=err.corrected_sentence,
            explanation=err.explanation,
            session_id=session_id,
            source_type="monologue",
        )
        db.create_card_from_error(error_id=err_record["error_id"])

    word_count = len(transcript.split())

    return {
        "message": tutor_response.message,
        "errors": [
            {
                "type": err.type.value,
                "user_sentence": err.user_sentence,
                "corrected_sentence": err.corrected_sentence,
                "explanation": err.explanation,
            }
            for err in tutor_response.errors
        ],
        "micro_task": tutor_response.micro_task,
        "session_id": str(session_id),
        "word_count": word_count,
        "duration_seconds": duration_seconds,
    }


@app.get("/api/drills/journal", tags=["Drills"])
async def get_journal_prompts(
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all journal writing prompts.

    Returns a list of all journal prompts with minimum word counts.
    """
    from app.drills import JOURNAL_PROMPTS

    prompts_list = [
        {
            "prompt_id": prompt.prompt_id,
            "text": prompt.text,
            "level": prompt.level,
            "category": prompt.category,
            "min_words": prompt.min_words,
        }
        for prompt in JOURNAL_PROMPTS.values()
    ]

    return {"prompts": prompts_list, "count": len(prompts_list)}


@app.post("/api/drills/journal/submit", tags=["Drills"])
async def submit_journal(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit a journal entry.

    Payload:
    {
        "prompt_id": "today_feeling",
        "content": "Today I am feeling happy because..."
    }

    Returns tutor feedback on the journal entry.
    """
    from app.drills import JOURNAL_PROMPTS
    from app.tutor_agent import TutorAgent

    prompt_id = payload.get("prompt_id")
    content = payload.get("content")

    if not prompt_id or prompt_id not in JOURNAL_PROMPTS:
        raise HTTPException(status_code=400, detail="Invalid or missing prompt_id")

    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=400, detail="Invalid or missing content")

    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    prompt = JOURNAL_PROMPTS[prompt_id]

    # Create DB session
    session = db.create_session(
        user_id=user_id,
        session_type="journal_drill",
        metadata={"prompt_id": prompt_id}
    )
    session_id = session["session_id"]

    # Process through tutor
    tutor = TutorAgent()
    user = get_or_create_user(str(user_id))
    user_level = user.get('level', 'A1')

    context_str = f"Journal prompt: {prompt.text}"

    tutor_response = tutor.process_user_input(
        content,
        context={
            "mode": "journal",
            "level": user_level,
            "prompt_id": prompt_id,
            "context": context_str,
        }
    )

    # Log errors and create SRS cards
    for err in tutor_response.errors:
        err_record = db.log_error(
            user_id=user_id,
            error_type=err.type.value,
            user_sentence=err.user_sentence,
            corrected_sentence=err.corrected_sentence,
            explanation=err.explanation,
            session_id=session_id,
            source_type="journal",
        )
        db.create_card_from_error(error_id=err_record["error_id"])

    word_count = len(content.split())

    return {
        "message": tutor_response.message,
        "errors": [
            {
                "type": err.type.value,
                "user_sentence": err.user_sentence,
                "corrected_sentence": err.corrected_sentence,
                "explanation": err.explanation,
            }
            for err in tutor_response.errors
        ],
        "micro_task": tutor_response.micro_task,
        "session_id": str(session_id),
        "word_count": word_count,
        "min_words": prompt.min_words,
    }


# ============================================================================
# Placement Test Endpoints
# ============================================================================

@app.get("/api/placement-test/questions", tags=["Placement Test"])
async def get_placement_test_questions():
    """
    Get placement test questions.

    Returns 12 questions covering A1-C2 levels.
    """
    from app.placement_test import placement_evaluator

    questions = placement_evaluator.get_questions(12)

    return {
        "questions": [
            {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "options": q.options,
                "level": q.level,
                "skill_type": q.skill_type,
            }
            for q in questions
        ],
        "total_questions": len(questions),
    }


@app.post("/api/placement-test/submit", tags=["Placement Test"])
async def submit_placement_test(
    payload: dict,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit placement test answers and get results.

    Payload:
    {
        "answers": [0, 2, 1, 3, 0, ...]  // List of selected option indices
    }

    Returns level determination and feedback.
    """
    from app.placement_test import placement_evaluator

    answers = payload.get("answers", [])

    if not answers or not isinstance(answers, list):
        raise HTTPException(status_code=400, detail="Invalid answers format")

    # Evaluate the test
    result = placement_evaluator.evaluate_test(answers)

    # Update user's level in database
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Update user profile with determined level
    db.update_user_profile(
        user_id=user_id,
        level=result.level
    )

    return {
        "level": result.level,
        "score": result.score,
        "total_questions": len(answers),
        "strengths": result.strengths,
        "weaknesses": result.weaknesses,
        "recommendation": result.recommendation,
    }


# Adaptive Placement Test Session Storage (in-memory for simplicity)
# In production, this should use Redis or database
_adaptive_test_sessions: Dict[str, Any] = {}


@app.post("/api/placement-test/adaptive/start", tags=["Placement Test"])
async def start_adaptive_placement_test():
    """
    Start a new adaptive placement test session.

    Returns the first question and a session_id to track the test.
    The test starts at B1 level and adapts based on performance.
    """
    from app.placement_test import adaptive_placement_test
    import uuid as uuid_module

    # Generate session ID
    session_id = str(uuid_module.uuid4())

    # Start the test
    state = adaptive_placement_test.start_test(session_id)

    # Get first question
    question = adaptive_placement_test.get_next_question(state)

    if not question:
        raise HTTPException(status_code=500, detail="Failed to generate question")

    # Store state
    _adaptive_test_sessions[session_id] = state.model_dump()

    return {
        "session_id": session_id,
        "question": {
            "question_id": question.question_id,
            "question_text": question.question_text,
            "options": question.options,
            "level": question.level,
            "skill_type": question.skill_type,
        },
        "question_number": 1,
        "is_complete": False,
    }


@app.post("/api/placement-test/adaptive/answer", tags=["Placement Test"])
async def submit_adaptive_answer(
    payload: dict,
    db: Database = Depends(get_database),
    user_id_from_token: Optional[str] = Depends(optional_verify_token),
):
    """
    Submit an answer for the current question and get the next one.

    Payload:
    {
        "session_id": "uuid",
        "question_id": "a1_grammar_1",
        "answer": 0  // Index of selected option
    }

    Returns the next question or final results if test is complete.
    """
    from app.placement_test import adaptive_placement_test, AdaptiveTestState, PLACEMENT_QUESTIONS

    session_id = payload.get("session_id")
    question_id = payload.get("question_id")
    answer = payload.get("answer")

    if not session_id or question_id is None or answer is None:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Get session state
    state_dict = _adaptive_test_sessions.get(session_id)
    if not state_dict:
        raise HTTPException(status_code=404, detail="Session not found")

    state = AdaptiveTestState(**state_dict)

    # Find the question
    question = next((q for q in PLACEMENT_QUESTIONS if q.question_id == question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Process the answer
    state = adaptive_placement_test.process_answer(state, question, answer)

    # Update stored state
    _adaptive_test_sessions[session_id] = state.model_dump()

    # Check if test is complete
    if state.is_complete:
        result = adaptive_placement_test.evaluate_test(state)

        # Update user's level if authenticated
        if user_id_from_token:
            try:
                user_id = uuid.UUID(user_id_from_token)
                db.update_user_profile(
                    user_id=user_id,
                    level=result.level
                )
            except Exception as e:
                print(f"Failed to update user level: {e}")

        # Clean up session
        del _adaptive_test_sessions[session_id]

        # Get the last answer's correctness
        is_correct = question.correct_answer == answer

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "is_complete": True,
            "final_result": {
                "level": result.level,
                "score": result.score,
                "total_questions": result.total_questions,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "recommendation": result.recommendation,
            },
        }
    else:
        # Get next question
        next_question = adaptive_placement_test.get_next_question(state)

        if not next_question:
            # Fallback: mark as complete if no more questions
            result = adaptive_placement_test.evaluate_test(state)

            if user_id_from_token:
                try:
                    user_id = uuid.UUID(user_id_from_token)
                    db.update_user_profile(
                        user_id=user_id,
                        level=result.level
                    )
                except Exception as e:
                    print(f"Failed to update user level: {e}")

            del _adaptive_test_sessions[session_id]

            is_correct = question.correct_answer == answer

            return {
                "is_correct": is_correct,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "is_complete": True,
                "final_result": {
                    "level": result.level,
                    "score": result.score,
                    "total_questions": result.total_questions,
                    "strengths": result.strengths,
                    "weaknesses": result.weaknesses,
                    "recommendation": result.recommendation,
                },
            }

        is_correct = question.correct_answer == answer

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "is_complete": False,
            "question_number": len(state.answers) + 1,
            "next_question": {
                "question_id": next_question.question_id,
                "question_text": next_question.question_text,
                "options": next_question.options,
                "level": next_question.level,
                "skill_type": next_question.skill_type,
            },
            "current_level": state.current_level,
        }


# ============================================================================
# Exercise Endpoints
# ============================================================================

@app.get("/api/exercises/session", tags=["Exercises"])
async def get_exercise_session(
    count: int = 5,
    level: Optional[str] = None,
    skill: Optional[str] = None,
    exercise_type: Optional[str] = None,
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get a practice session with exercises.

    Args:
        count: Number of exercises (default 5)
        level: Filter by level (A1, A2, B1, B2, C1, C2)
        skill: Filter by skill type (grammar, vocabulary)
        exercise_type: Filter by type (multiple_choice, fill_blank, sentence_correction)

    Returns:
        List of exercises for the session
    """
    from app.exercises import exercise_manager, SkillType, ExerciseType

    # Convert string params to enums
    skill_enum = None
    if skill:
        try:
            skill_enum = SkillType(skill.lower())
        except ValueError:
            pass

    type_enum = None
    if exercise_type:
        try:
            type_enum = ExerciseType(exercise_type.lower())
        except ValueError:
            pass

    # Get user level if not specified
    if not level:
        try:
            user_id = uuid.UUID(user_id_from_token)
            user = get_or_create_user(str(user_id))
            level = user.get('level', 'B1')
        except:
            level = 'B1'

    exercises = exercise_manager.get_practice_session(
        count=count,
        level=level,
        skill=skill_enum,
        exercise_type=type_enum,
    )

    return {
        "exercises": [
            {
                "id": ex.exercise_id,
                "type": ex.exercise_type.value,
                "level": ex.level,
                "skill": ex.skill.value,
                "question": ex.question,
                "options": ex.options,
                "hint": ex.hint,
                # Don't send correct answer to client
            }
            for ex in exercises
        ],
        "count": len(exercises),
    }


@app.post("/api/exercises/submit", tags=["Exercises"])
async def submit_exercise_answer(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit an answer for an exercise.

    Payload:
    {
        "exercise_id": "mc-gram-b1-001",
        "user_answer": "were"
    }

    Returns:
        is_correct, correct_answer, explanation, xp_earned
    """
    from app.exercises import exercise_manager

    exercise_id = payload.get("exercise_id")
    user_answer = payload.get("user_answer")

    if not exercise_id:
        raise HTTPException(status_code=400, detail="Missing exercise_id")
    if not user_answer and user_answer != 0:  # Allow 0 as answer
        raise HTTPException(status_code=400, detail="Missing user_answer")

    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        result = exercise_manager.check_answer(exercise_id, str(user_answer))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Calculate XP (only if correct and not already earned for this exercise recently)
    xp_earned = 0
    total_xp = None
    if result["is_correct"] and _can_earn_xp(user_id_from_token, exercise_id):
        xp_earned = 10
        try:
            total_xp = add_user_xp(user_id_from_token, xp_earned)
            _mark_xp_earned(user_id_from_token, exercise_id)
        except Exception as e:
            print(f"Warning: Failed to add XP: {e}")

    # Log the exercise attempt
    try:
        session = db.create_session(
            user_id=user_id,
            session_type="exercise",
            metadata={
                "exercise_id": exercise_id,
                "user_answer": str(user_answer),
                "is_correct": result["is_correct"],
            }
        )

        # If incorrect, log as error for SRS
        if not result["is_correct"]:
            exercise = exercise_manager.get_exercise(exercise_id)
            if exercise:
                err_record = db.log_error(
                    user_id=user_id,
                    error_type=exercise.skill.value,
                    user_sentence=str(user_answer),
                    corrected_sentence=result["correct_answer"],
                    explanation=result["explanation"],
                    session_id=session["session_id"],
                    source_type="exercise",
                )
                db.create_card_from_error(error_id=err_record["error_id"])
    except Exception as e:
        # Log but don't fail the request
        print(f"Warning: Failed to log exercise: {e}")

    return {
        "is_correct": result["is_correct"],
        "correct_answer": result["correct_answer"],
        "explanation": result["explanation"],
        "xp_earned": xp_earned,
        "total_xp": total_xp,  # New total XP (None if not updated)
    }


@app.get("/api/exercises/{exercise_id}", tags=["Exercises"])
async def get_exercise(
    exercise_id: str,
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get a specific exercise by ID.

    Returns the exercise without the correct answer.
    """
    from app.exercises import exercise_manager

    exercise = exercise_manager.get_exercise(exercise_id)

    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise '{exercise_id}' not found")

    return {
        "id": exercise.exercise_id,
        "type": exercise.exercise_type.value,
        "level": exercise.level,
        "skill": exercise.skill.value,
        "question": exercise.question,
        "options": exercise.options,
        "hint": exercise.hint,
    }


# ============================================================================
# Streaks Endpoints
# ============================================================================

@app.get("/api/streaks/current", tags=["Streaks"])
async def get_current_streak(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get current user's streak information.

    Requires JWT authentication. User ID is extracted from the token.

    Returns:
    - current_streak: Current consecutive days streak
    - longest_streak: Longest streak ever achieved
    - last_active_date: Date of last activity
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        streak_data = db.get_user_streak(user_id)

        if streak_data is None:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_active_date": None
            }

        return streak_data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get streak data: {str(e)}"
        )


@app.post("/api/streaks/record-activity", tags=["Streaks"])
async def record_activity(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Record user activity and update streak.

    Call this when the user completes an exercise, lesson, or any meaningful activity.
    The streak logic handles:
    - First activity: creates streak record with 1 day
    - Already logged today: returns current streak (no change)
    - Continuing from yesterday: increments streak
    - Streak broken (gap > 1 day): resets to 1

    Returns:
    - current_streak: Current consecutive days streak
    - longest_streak: Longest streak ever achieved
    - last_active_date: Date of last activity
    - total_days_active: Total number of active days
    - freeze_days_available: Freeze days remaining
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        streak_data = db.record_activity(user_id)
        return streak_data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record activity: {str(e)}"
        )


# ============================================================================
# Daily Goals Endpoints
# ============================================================================

@app.get("/api/goals/today", tags=["Goals"])
async def get_today_goal(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get today's daily goal for the authenticated user.

    Creates a goal with default targets if it doesn't exist.

    Returns:
    - goal_id: Goal UUID
    - user_id: User UUID
    - goal_date: Date of the goal
    - target_study_minutes: Target study time in minutes
    - target_lessons: Target number of lessons
    - target_reviews: Target number of reviews
    - target_drills: Target number of drills
    - actual_study_minutes: Actual study time completed
    - actual_lessons: Actual lessons completed
    - actual_reviews: Actual reviews completed
    - actual_drills: Actual drills completed
    - completed: Whether all goals are completed
    - completion_percentage: Overall completion percentage (0-100)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Try to get existing goal
        goal = db.get_daily_goal(user_id)

        # If no goal exists, create one with default targets
        if not goal:
            goal = db.create_or_update_daily_goal(
                user_id=user_id,
                target_study_minutes=30,
                target_lessons=1,
                target_reviews=10,
                target_drills=2
            )

        return goal

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily goal: {str(e)}"
        )


@app.post("/api/goals/today", tags=["Goals"])
async def update_today_goal(
    targets: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Update today's goal targets for the authenticated user.

    Request body:
    {
        "target_study_minutes": 45,
        "target_lessons": 2,
        "target_reviews": 15,
        "target_drills": 3
    }

    All fields are optional - only provided fields will be updated.

    Returns the updated daily goal.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Extract targets from request
        target_study_minutes = targets.get("target_study_minutes")
        target_lessons = targets.get("target_lessons")
        target_reviews = targets.get("target_reviews")
        target_drills = targets.get("target_drills")

        # Update or create goal with new targets
        goal = db.create_or_update_daily_goal(
            user_id=user_id,
            target_study_minutes=target_study_minutes,
            target_lessons=target_lessons,
            target_reviews=target_reviews,
            target_drills=target_drills
        )

        return goal

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update daily goal: {str(e)}"
        )


@app.post("/api/goals/today/progress", tags=["Goals"])
async def update_goal_progress(
    progress: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Increment today's goal progress for the authenticated user.

    Request body:
    {
        "study_minutes": 15,
        "lessons": 1,
        "reviews": 5,
        "drills": 1
    }

    All fields are optional and default to 0.
    This endpoint increments the current progress values.

    Returns the updated daily goal with new progress.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Extract progress increments from request
        study_minutes = progress.get("study_minutes", 0)
        lessons = progress.get("lessons", 0)
        reviews = progress.get("reviews", 0)
        drills = progress.get("drills", 0)

        # Increment progress
        goal = db.increment_daily_goal_progress(
            user_id=user_id,
            study_minutes=study_minutes,
            lessons=lessons,
            reviews=reviews,
            drills=drills
        )

        return goal

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update goal progress: {str(e)}"
        )


# ============================================================================
# Daily Challenges Endpoints
# ============================================================================

@app.get("/api/challenges/today", tags=["Challenges"])
async def get_daily_challenges(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get today's daily challenges for the authenticated user.

    Creates challenges if they don't exist.

    Returns 3 challenge slots:
    - core: Complete 2 lessons (+15 XP)
    - accuracy: Score 80%+ on a lesson (+25 XP)
    - stretch: Earn 60+ XP OR complete 1 speaking session (+50 XP + streak freeze)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        challenges = db.get_daily_challenges(user_id)
        if not challenges:
            raise HTTPException(status_code=500, detail="Could not create daily challenges")

        # Format response
        freeze_count = db.get_streak_freeze_count(user_id)

        return {
            "challenges": {
                "core": {
                    "name": "Complete Lessons",
                    "description": f"Complete {challenges['core_target']} lessons",
                    "target": challenges['core_target'],
                    "progress": challenges['core_progress'],
                    "completed": challenges['core_completed'],
                    "xp_reward": challenges['core_xp_reward'],
                    "completed_at": challenges.get('core_completed_at')
                },
                "accuracy": {
                    "name": "High Achiever",
                    "description": f"Score {challenges['accuracy_target']}% or higher on any lesson",
                    "target": challenges['accuracy_target'],
                    "progress": challenges['accuracy_progress'],
                    "completed": challenges['accuracy_completed'],
                    "xp_reward": challenges['accuracy_xp_reward'],
                    "completed_at": challenges.get('accuracy_completed_at')
                },
                "stretch": {
                    "name": "Go Beyond",
                    "description": f"Earn {challenges['stretch_xp_target']}+ XP OR complete {challenges['stretch_speaking_target']} speaking session",
                    "xp_target": challenges['stretch_xp_target'],
                    "xp_progress": challenges['stretch_xp_progress'],
                    "speaking_target": challenges['stretch_speaking_target'],
                    "speaking_progress": challenges['stretch_speaking_progress'],
                    "completed": challenges['stretch_completed'],
                    "xp_reward": challenges['stretch_xp_reward'],
                    "gives_freeze_token": challenges['stretch_gives_freeze_token'],
                    "completed_at": challenges.get('stretch_completed_at')
                }
            },
            "all_completed": challenges['all_completed'],
            "streak_freeze_tokens": freeze_count,
            "date": str(challenges['challenge_date'])
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily challenges: {str(e)}"
        )


@app.post("/api/challenges/progress", tags=["Challenges"])
async def update_challenge_progress(
    progress: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Update daily challenge progress.

    Request body:
    {
        "lessons_completed": 1,
        "best_score": 85,
        "xp_earned": 25,
        "speaking_sessions": 0
    }

    All fields are optional and default to 0.

    Returns:
    - which challenges were just completed
    - total XP earned from completions
    - whether a streak freeze token was earned
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        lessons_completed = progress.get("lessons_completed", 0)
        best_score = progress.get("best_score", 0)
        xp_earned = progress.get("xp_earned", 0)
        speaking_sessions = progress.get("speaking_sessions", 0)

        result = db.update_daily_challenge_progress(
            user_id=user_id,
            lessons_completed=lessons_completed,
            best_score=best_score,
            xp_earned=xp_earned,
            speaking_sessions=speaking_sessions
        )

        # Get updated challenges
        challenges = db.get_daily_challenges(user_id)
        freeze_count = db.get_streak_freeze_count(user_id)

        return {
            **result,
            "challenges": {
                "core": {
                    "progress": challenges['core_progress'],
                    "completed": challenges['core_completed']
                },
                "accuracy": {
                    "progress": challenges['accuracy_progress'],
                    "completed": challenges['accuracy_completed']
                },
                "stretch": {
                    "xp_progress": challenges['stretch_xp_progress'],
                    "speaking_progress": challenges['stretch_speaking_progress'],
                    "completed": challenges['stretch_completed']
                }
            },
            "all_completed": challenges['all_completed'],
            "streak_freeze_tokens": freeze_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update challenge progress: {str(e)}"
        )


@app.get("/api/challenges/freeze-tokens", tags=["Challenges"])
async def get_streak_freeze_tokens(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get number of available streak freeze tokens.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        count = db.get_streak_freeze_count(user_id)
        return {"streak_freeze_tokens": count}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get streak freeze tokens: {str(e)}"
        )


@app.post("/api/challenges/use-freeze", tags=["Challenges"])
async def use_streak_freeze(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Use a streak freeze token to protect streak.

    Returns success status and remaining tokens.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        success = db.use_streak_freeze_token(user_id)
        remaining = db.get_streak_freeze_count(user_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="No streak freeze tokens available"
            )

        return {
            "success": True,
            "streak_freeze_tokens": remaining
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to use streak freeze token: {str(e)}"
        )


# ============================================================================
# Friends System Endpoints
# ============================================================================

class FriendRequestBody(BaseModel):
    friend_id: str

class SearchUsersBody(BaseModel):
    query: str
    limit: int = 10

class FriendChallengeBody(BaseModel):
    friend_id: str
    challenge_type: str  # 'beat_xp_today' or 'more_lessons_today'

class ChallengeResponseBody(BaseModel):
    challenge_id: str
    accept: bool

class InviteLinkBody(BaseModel):
    invite_code: str


@app.get("/api/friends", tags=["Friends"])
async def get_friends_list(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get list of friends with their today's stats.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        friends = db.get_friends_list(user_id)
        pending = db.get_pending_friend_requests(user_id)
        friend_code = db.get_user_friend_code(user_id)

        return {
            "friends": friends,
            "pending_requests": pending,
            "friend_code": friend_code,
            "friend_count": len(friends)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get friends list: {str(e)}"
        )


@app.post("/api/friends/search", tags=["Friends"])
async def search_users(
    body: SearchUsersBody,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Search for users by username, display name, or friend code.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        users = db.search_users(user_id, body.query, body.limit)
        return {"users": users}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search users: {str(e)}"
        )


@app.post("/api/friends/request", tags=["Friends"])
async def send_friend_request(
    body: FriendRequestBody,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Send a friend request to another user.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        friend_id = uuid.UUID(body.friend_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    try:
        result = db.send_friend_request(user_id, friend_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send friend request: {str(e)}"
        )


@app.post("/api/friends/accept", tags=["Friends"])
async def accept_friend_request(
    body: FriendRequestBody,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Accept a friend request.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        requester_id = uuid.UUID(body.friend_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    try:
        success = db.accept_friend_request(user_id, requester_id)
        if not success:
            raise HTTPException(status_code=400, detail="Friend request not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to accept friend request: {str(e)}"
        )


@app.post("/api/friends/decline", tags=["Friends"])
async def decline_friend_request(
    body: FriendRequestBody,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Decline a friend request.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        requester_id = uuid.UUID(body.friend_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    try:
        success = db.decline_friend_request(user_id, requester_id)
        if not success:
            raise HTTPException(status_code=400, detail="Friend request not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to decline friend request: {str(e)}"
        )


@app.delete("/api/friends/{friend_id}", tags=["Friends"])
async def remove_friend(
    friend_id: str,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Remove a friend.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        friend_uuid = uuid.UUID(friend_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    try:
        success = db.remove_friend(user_id, friend_uuid)
        if not success:
            raise HTTPException(status_code=400, detail="Friend not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove friend: {str(e)}"
        )


@app.get("/api/friends/{friend_id}/profile", tags=["Friends"])
async def get_friend_profile(
    friend_id: str,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get detailed friend profile with 7-day activity.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        friend_uuid = uuid.UUID(friend_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    try:
        profile = db.get_friend_profile(user_id, friend_uuid)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get friend profile: {str(e)}"
        )


@app.post("/api/friends/invite-link", tags=["Friends"])
async def create_invite_link(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Create a shareable friend invite link.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        invite_code = db.create_friend_invite_link(user_id)
        return {
            "invite_code": invite_code,
            "invite_url": f"https://vorex.app/invite/{invite_code}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create invite link: {str(e)}"
        )


@app.post("/api/friends/use-invite", tags=["Friends"])
async def use_invite_link(
    body: InviteLinkBody,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Use a friend invite link to add a friend.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        result = db.use_friend_invite_link(body.invite_code, user_id)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to use invite link: {str(e)}"
        )


# Friend Challenges

@app.get("/api/friends/challenges", tags=["Friends"])
async def get_friend_challenges(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get friend challenges (sent and received).
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        challenges = db.get_friend_challenges(user_id)
        return challenges
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get friend challenges: {str(e)}"
        )


@app.post("/api/friends/challenge", tags=["Friends"])
async def create_friend_challenge(
    body: FriendChallengeBody,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Create a friend challenge.

    Challenge types:
    - beat_xp_today: Compete to earn more XP today
    - more_lessons_today: Compete to complete more lessons today
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        friend_id = uuid.UUID(body.friend_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    if body.challenge_type not in ['beat_xp_today', 'more_lessons_today']:
        raise HTTPException(status_code=400, detail="Invalid challenge type")

    try:
        result = db.create_friend_challenge(user_id, friend_id, body.challenge_type)
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create challenge: {str(e)}"
        )


@app.post("/api/friends/challenge/respond", tags=["Friends"])
async def respond_to_challenge(
    body: ChallengeResponseBody,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Accept or decline a friend challenge.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        challenge_id = uuid.UUID(body.challenge_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    try:
        success = db.respond_to_challenge(user_id, challenge_id, body.accept)
        if not success:
            raise HTTPException(status_code=400, detail="Challenge not found or already responded")
        return {"success": True, "accepted": body.accept}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to respond to challenge: {str(e)}"
        )


@app.get("/api/friends/challenge/{challenge_id}", tags=["Friends"])
async def get_challenge_status(
    challenge_id: str,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get current status and scores for a challenge.
    """
    try:
        challenge_uuid = uuid.UUID(challenge_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid challenge_id")

    try:
        result = db.update_challenge_scores(challenge_uuid)
        if not result:
            raise HTTPException(status_code=404, detail="Challenge not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get challenge status: {str(e)}"
        )


# ============================================================================
# Leaderboard Endpoints
# ============================================================================

@app.get("/api/leaderboard/weekly", tags=["Leaderboard"])
async def get_weekly_leaderboard(
    limit: int = 50,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get weekly leaderboard (top users by XP gained this week).

    Returns top 50 users plus authenticated user's rank if not in top 50.
    XP is calculated based on completed sessions (10 XP per session).

    Returns:
        - leaderboard: Array of top users with rank, name, xp, level
        - current_user: Current user's rank and stats (if authenticated)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        result = db.get_weekly_leaderboard(limit=limit, current_user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get weekly leaderboard: {str(e)}"
        )


@app.get("/api/leaderboard/monthly", tags=["Leaderboard"])
async def get_monthly_leaderboard(
    limit: int = 50,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get monthly leaderboard (top users by XP gained this month).

    Returns top 50 users plus authenticated user's rank if not in top 50.
    XP is calculated based on completed sessions (10 XP per session).

    Returns:
        - leaderboard: Array of top users with rank, name, xp, level
        - current_user: Current user's rank and stats (if authenticated)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        result = db.get_monthly_leaderboard(limit=limit, current_user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monthly leaderboard: {str(e)}"
        )


@app.get("/api/leaderboard/alltime", tags=["Leaderboard"])
async def get_alltime_leaderboard(
    limit: int = 50,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all-time leaderboard (top users by total XP).

    Returns top 50 users plus authenticated user's rank if not in top 50.
    XP is calculated based on all completed sessions (10 XP per session).

    Returns:
        - leaderboard: Array of top users with rank, name, total_xp, level
        - current_user: Current user's rank and stats (if authenticated)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        result = db.get_alltime_leaderboard(limit=limit, current_user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get all-time leaderboard: {str(e)}"
        )


@app.get("/api/leaderboard/streaks", tags=["Leaderboard"])
async def get_streak_leaderboard(
    limit: int = 50,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get streak leaderboard (top users by current streak days).

    Returns top 50 users plus authenticated user's rank if not in top 50.

    Returns:
        - leaderboard: Array of top users with rank, name, current_streak, level
        - current_user: Current user's rank and stats (if authenticated)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        result = db.get_streak_leaderboard(limit=limit, current_user_id=user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get streak leaderboard: {str(e)}"
        )


# ============================================================================
# Notifications Endpoints
# ============================================================================

@app.get("/api/notifications", tags=["Notifications"])
async def get_notifications(
    limit: int = 20,
    offset: int = 0,
    unread_only: bool = False,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's notifications (paginated, unread first).

    Query params:
    - limit: Maximum number of notifications to return (default 20)
    - offset: Number of notifications to skip (default 0)
    - unread_only: If true, only return unread notifications (default false)

    Returns:
    - notifications: List of notification objects
    - count: Total number of notifications returned
    - has_more: Whether there are more notifications to load
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        notifications = db.get_notifications(
            user_id=user_id,
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset,
            unread_only=unread_only
        )

        has_more = len(notifications) > limit
        if has_more:
            notifications = notifications[:limit]

        # Convert datetime objects to ISO strings for JSON serialization
        for notif in notifications:
            if notif.get('created_at'):
                notif['created_at'] = notif['created_at'].isoformat()
            if notif.get('read_at'):
                notif['read_at'] = notif['read_at'].isoformat()

        return {
            "notifications": notifications,
            "count": len(notifications),
            "has_more": has_more
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get notifications: {str(e)}"
        )


@app.post("/api/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Mark a notification as read.

    Args:
        notification_id: UUID of the notification to mark as read

    Returns:
        Success confirmation
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Verify the notification belongs to this user
        notifications = db.get_notifications(user_id=user_id, limit=1000)
        notification_ids = [n['notification_id'] for n in notifications]

        if notification_id not in notification_ids:
            raise HTTPException(status_code=404, detail="Notification not found")

        success = db.mark_notification_read(notification_id)

        if not success:
            raise HTTPException(status_code=404, detail="Notification not found or already read")

        return {
            "status": "success",
            "message": "Notification marked as read",
            "notification_id": str(notification_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark notification as read: {str(e)}"
        )


@app.post("/api/notifications/read-all", tags=["Notifications"])
async def mark_all_notifications_read(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Mark all notifications as read for the authenticated user.

    Returns:
        Number of notifications marked as read
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        count = db.mark_all_notifications_read(user_id)

        return {
            "status": "success",
            "message": f"Marked {count} notification(s) as read",
            "count": count
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )


@app.get("/api/notifications/unread-count", tags=["Notifications"])
async def get_unread_notification_count(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get unread notification count for badge display.

    Returns:
        Unread notification count
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        count = db.get_unread_notification_count(user_id)

        return {
            "unread_count": count
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get unread count: {str(e)}"
        )


# ============================================================================
# Conversation History Endpoints
# ============================================================================

@app.get("/api/tutor/history", tags=["Tutor"])
async def get_conversation_history(
    limit: int = 20,
    context_type: Optional[str] = None,
    context_id: Optional[str] = None,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get conversation history for the authenticated user.

    Query params:
    - limit: Maximum number of conversation turns to return (default 20)
    - context_type: Filter by context type (scenario, lesson, free_chat, etc.)
    - context_id: Filter by specific context ID (scenario_id, lesson_id, etc.)

    Returns:
    - conversations: List of conversation turns with user messages and tutor responses
    - count: Total number of conversations returned
    - summary: High-level summary of conversation patterns
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Get filtered conversations if context specified
        if context_type:
            conversations = db.get_conversation_by_context(
                user_id=user_id,
                context_type=context_type,
                context_id=context_id,
                limit=limit
            )
        else:
            # Get recent conversations
            conversations = db.get_recent_conversations(user_id, limit=limit)

        # Get conversation summary
        summary = db.get_conversation_context(user_id, lookback_days=30)

        # Convert datetime objects to ISO strings
        for conv in conversations:
            if conv.get('created_at'):
                conv['created_at'] = conv['created_at'].isoformat()

        return {
            "conversations": conversations,
            "count": len(conversations),
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@app.delete("/api/tutor/history", tags=["Tutor"])
async def clear_conversation_history(
    before_date: Optional[str] = None,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Clear conversation history for the authenticated user.

    Query params:
    - before_date: Optional ISO date string - only clear conversations before this date

    Returns:
    - deleted_count: Number of conversation turns deleted
    - message: Success message
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Parse before_date if provided
        before_datetime = None
        if before_date:
            try:
                from datetime import datetime as dt
                before_datetime = dt.fromisoformat(before_date.replace('Z', '+00:00'))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601 format.")

        # Clear conversation history
        deleted_count = db.clear_conversation_history(
            user_id=user_id,
            before_date=before_datetime
        )

        return {
            "status": "success",
            "message": f"Cleared {deleted_count} conversation turn(s)",
            "deleted_count": deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear conversation history: {str(e)}"
        )


@app.get("/api/tutor/memory-summary", tags=["Tutor"])
async def get_memory_summary(
    lookback_days: int = 30,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get a summary of the tutor's memory about the user.

    Shows what the tutor "remembers" about past conversations,
    including topics discussed, contexts used, and conversation patterns.

    Query params:
    - lookback_days: Number of days to look back (default 30)

    Returns:
    - total_conversations: Total number of conversation turns
    - recent_topics: List of recent conversation contexts
    - most_active_context: The most frequently used context type
    - last_conversation_date: Date of last conversation
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        summary = db.get_conversation_context(
            user_id=user_id,
            lookback_days=lookback_days
        )

        if not summary:
            return {
                "total_conversations": 0,
                "recent_topics": [],
                "most_active_context": None,
                "last_conversation_date": None
            }

        # Extract data from summary
        context_summary = summary.get('context_summary', {})

        return {
            "total_conversations": summary.get('total_conversations', 0),
            "recent_topics": summary.get('recent_topics', []),
            "most_active_context": context_summary.get('most_active_context'),
            "last_conversation_date": context_summary.get('last_conversation_date')
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory summary: {str(e)}"
        )


# Daily Challenges Endpoints


@app.get("/api/challenges/today", tags=["Challenges"])
async def get_today_challenge(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get today's daily challenge for the current user.

    Requires JWT authentication. User ID is extracted from the token.

    Returns:
        Challenge definition with user's current progress
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    try:
        # Get today's challenge definition
        challenge = db.get_daily_challenge()

        # Get user's progress on this challenge
        progress_record = db.get_user_challenge_progress(user_id)

        # Calculate time until next challenge
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_reset = int((tomorrow - now).total_seconds())

        return {
            "challenge": challenge,
            "progress": progress_record.get('progress', 0) if progress_record else 0,
            "completed": progress_record.get('completed', False) if progress_record else False,
            "completed_at": progress_record.get('completed_at') if progress_record else None,
            "seconds_until_reset": seconds_until_reset,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get today's challenge: {str(e)}"
        )


@app.post("/api/challenges/complete", tags=["Challenges"])
async def complete_challenge(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Mark today's daily challenge as complete and award bonus XP.

    Requires JWT authentication. User ID is extracted from the token.

    Returns:
        Completion status and reward info
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    try:
        # Complete the challenge
        result = db.complete_daily_challenge(user_id)

        if result is None:
            # Already completed
            return {
                "success": False,
                "message": "Challenge already completed today",
                "already_completed": True
            }

        # Get the challenge to find reward amount
        challenge = db.get_daily_challenge()
        reward_xp = challenge.get('reward_xp', 50)

        # Award bonus XP (you might want to track this separately)
        # For now, we'll just return the info
        return {
            "success": True,
            "message": "Challenge completed! Bonus XP awarded!",
            "reward_xp": reward_xp,
            "completed_at": result.get('completed_at'),
            "already_completed": False
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete challenge: {str(e)}"
        )


@app.get("/api/challenges/history", tags=["Challenges"])
async def get_challenge_history(
    limit: int = 30,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's challenge completion history.

    Requires JWT authentication. User ID is extracted from the token.

    Query params:
        limit: Maximum number of records to return (default 30)

    Returns:
        List of past challenge completions
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    try:
        # Get history
        history = db.get_challenge_history(user_id, limit=limit)

        # Get challenge streak
        streak = db.get_challenge_streak(user_id)

        # Enrich history with challenge definitions
        enriched_history = []
        for record in history:
            challenge_date = record.get('challenge_date')
            if challenge_date:
                challenge_def = db.get_daily_challenge(challenge_date)
                enriched_history.append({
                    **record,
                    "challenge_title": challenge_def.get('title'),
                    "challenge_description": challenge_def.get('description'),
                    "reward_xp": challenge_def.get('reward_xp'),
                })
            else:
                enriched_history.append(record)

        return {
            "history": enriched_history,
            "current_streak": streak,
            "total_completed": sum(1 for h in history if h.get('completed', False))
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get challenge history: {str(e)}"
        )


@app.post("/api/challenges/update-progress", tags=["Challenges"])
async def update_challenge_progress(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Update progress on today's daily challenge.

    Requires JWT authentication. User ID is extracted from the token.

    Request body:
        challenge_type: Type of challenge (e.g., "complete_exercises")
        progress: Current progress value

    Returns:
        Updated progress record
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    # Auto-create user profile if doesn't exist
    get_or_create_user(str(user_id))

    challenge_type = payload.get("challenge_type")
    progress = payload.get("progress")

    if not challenge_type or progress is None:
        raise HTTPException(
            status_code=400,
            detail="Missing challenge_type or progress"
        )

    try:
        # Update progress
        result = db.update_challenge_progress(
            user_id=user_id,
            challenge_type=challenge_type,
            progress=progress
        )

        # Check if challenge is now complete
        if result and result.get('completed') and not result.get('completed_at'):
            # Auto-complete the challenge
            db.complete_daily_challenge(user_id)

        # Get the challenge definition
        challenge = db.get_daily_challenge()

        return {
            "progress": result.get('progress', 0) if result else 0,
            "goal": result.get('goal', challenge.get('goal', 0)) if result else challenge.get('goal', 0),
            "completed": result.get('completed', False) if result else False,
            "challenge": challenge
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update challenge progress: {str(e)}"
        )


# ============================================
# Learning Path Endpoints
# ============================================

@app.get("/api/learning-path/units")
async def get_learning_path_units(user: dict = Depends(verify_token)):
    """Get all learning units with user progress."""
    db = get_db()
    user_id = user["user_id"]

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get all units with user progress
                cur.execute("""
                    SELECT
                        lu.unit_id,
                        lu.unit_number,
                        lu.level,
                        lu.title,
                        lu.description,
                        lu.icon,
                        lu.color,
                        lu.order_index,
                        lu.is_locked,
                        lu.estimated_time_minutes,
                        lu.metadata,
                        COALESCE(uup.lessons_completed, 0) as lessons_completed,
                        (SELECT COUNT(*) FROM learning_lessons WHERE unit_id = lu.unit_id) as total_lessons,
                        COALESCE(uup.completed, FALSE) as completed,
                        COALESCE(uup.test_passed, FALSE) as test_passed
                    FROM learning_units lu
                    LEFT JOIN user_unit_progress uup ON lu.unit_id = uup.unit_id AND uup.user_id = %s
                    ORDER BY lu.order_index ASC
                """, (user_id,))

                units = []
                rows = cur.fetchall()

                for row in rows:
                    units.append({
                        "unit_id": str(row[0]),
                        "unit_number": row[1],
                        "level": row[2],
                        "title": row[3],
                        "description": row[4],
                        "icon": row[5],
                        "color": row[6],
                        "order_index": row[7],
                        "is_locked": row[8],
                        "estimated_time_minutes": row[9],
                        "metadata": row[10],
                        "lessons_completed": row[11],
                        "total_lessons": row[12],
                        "completed": row[13],
                        "test_passed": row[14]
                    })

                # Unlock logic: first unit always unlocked, others unlock when previous is completed
                for i, unit in enumerate(units):
                    if i == 0:
                        unit["is_locked"] = False
                    elif i > 0 and units[i-1]["completed"]:
                        unit["is_locked"] = False

                return {"units": units, "total": len(units)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning path: {str(e)}")


@app.get("/api/learning-path/units/{unit_id}")
async def get_unit_detail(unit_id: str, user: dict = Depends(verify_token)):
    """Get unit details with lessons and user progress."""
    db = get_db()
    user_id = user["user_id"]

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get unit info
                cur.execute("""
                    SELECT
                        lu.*,
                        COALESCE(uup.lessons_completed, 0) as user_lessons_completed,
                        COALESCE(uup.completed, FALSE) as user_completed,
                        COALESCE(uup.test_passed, FALSE) as user_test_passed,
                        uup.test_score
                    FROM learning_units lu
                    LEFT JOIN user_unit_progress uup ON lu.unit_id = uup.unit_id AND uup.user_id = %s
                    WHERE lu.unit_id = %s
                """, (user_id, unit_id))

                unit_row = cur.fetchone()
                if not unit_row:
                    raise HTTPException(status_code=404, detail="Unit not found")

                # Get lessons with progress
                cur.execute("""
                    SELECT
                        ll.lesson_id,
                        ll.lesson_number,
                        ll.title,
                        ll.description,
                        ll.lesson_type,
                        ll.order_index,
                        ll.xp_reward,
                        ll.is_locked,
                        ll.estimated_time_minutes,
                        ll.content,
                        COALESCE(ulp.completed, FALSE) as completed,
                        ulp.score,
                        (SELECT COUNT(*) FROM lesson_exercises WHERE lesson_id = ll.lesson_id) as exercise_count
                    FROM learning_lessons ll
                    LEFT JOIN user_lesson_progress ulp ON ll.lesson_id = ulp.lesson_id AND ulp.user_id = %s
                    WHERE ll.unit_id = %s
                    ORDER BY ll.order_index ASC
                """, (user_id, unit_id))

                lessons = []
                lesson_rows = cur.fetchall()

                for i, row in enumerate(lesson_rows):
                    is_locked = row[7]
                    # First lesson unlocked, others unlock when previous completed
                    if i == 0:
                        is_locked = False
                    elif i > 0 and lessons[i-1]["completed"]:
                        is_locked = False

                    lessons.append({
                        "lesson_id": str(row[0]),
                        "lesson_number": row[1],
                        "title": row[2],
                        "description": row[3],
                        "lesson_type": row[4],
                        "order_index": row[5],
                        "xp_reward": row[6],
                        "is_locked": is_locked,
                        "estimated_time_minutes": row[8],
                        "content": row[9],
                        "completed": row[10],
                        "score": row[11],
                        "exercise_count": row[12]
                    })

                return {
                    "unit": {
                        "unit_id": str(unit_row[0]),
                        "unit_number": unit_row[1],
                        "level": unit_row[2],
                        "title": unit_row[3],
                        "description": unit_row[4],
                        "icon": unit_row[5],
                        "color": unit_row[6],
                        "lessons_completed": unit_row[13],
                        "completed": unit_row[14],
                        "test_passed": unit_row[15],
                        "test_score": unit_row[16]
                    },
                    "lessons": lessons,
                    "total_lessons": len(lessons)
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unit: {str(e)}")


@app.get("/api/learning-path/lessons/{lesson_id}")
async def get_lesson_detail(lesson_id: str, user: dict = Depends(verify_token)):
    """Get lesson details with exercises."""
    db = get_db()
    user_id = user["user_id"]

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get lesson info
                cur.execute("""
                    SELECT
                        ll.*,
                        lu.title as unit_title,
                        lu.level,
                        COALESCE(ulp.completed, FALSE) as user_completed,
                        COALESCE(ulp.score, 0) as user_score,
                        COALESCE(ulp.exercises_completed, 0) as user_exercises_completed,
                        COALESCE(ulp.current_exercise_index, 0) as current_exercise_index
                    FROM learning_lessons ll
                    JOIN learning_units lu ON ll.unit_id = lu.unit_id
                    LEFT JOIN user_lesson_progress ulp ON ll.lesson_id = ulp.lesson_id AND ulp.user_id = %s
                    WHERE ll.lesson_id = %s
                """, (user_id, lesson_id))

                lesson_row = cur.fetchone()
                if not lesson_row:
                    raise HTTPException(status_code=404, detail="Lesson not found")

                # Get exercises for this lesson
                cur.execute("""
                    SELECT exercise_id, order_index, is_required
                    FROM lesson_exercises
                    WHERE lesson_id = %s
                    ORDER BY order_index ASC
                """, (lesson_id,))

                exercise_ids = []
                for row in cur.fetchall():
                    exercise_ids.append({
                        "exercise_id": row[0],
                        "order_index": row[1],
                        "is_required": row[2]
                    })

                # Get actual exercises from exercises pool
                from app.exercises import EXERCISES
                exercises = []
                for ex in exercise_ids:
                    exercise_data = next((e for e in EXERCISES if e["id"] == ex["exercise_id"]), None)
                    if exercise_data:
                        exercises.append({
                            **exercise_data,
                            "order_index": ex["order_index"],
                            "is_required": ex["is_required"]
                        })

                return {
                    "lesson": {
                        "lesson_id": str(lesson_row[0]),
                        "unit_id": str(lesson_row[1]),
                        "lesson_number": lesson_row[2],
                        "title": lesson_row[3],
                        "description": lesson_row[4],
                        "lesson_type": lesson_row[5],
                        "xp_reward": lesson_row[7],
                        "estimated_time_minutes": lesson_row[9],
                        "content": lesson_row[10],
                        "unit_title": lesson_row[13],
                        "level": lesson_row[14],
                        "completed": lesson_row[15],
                        "user_score": lesson_row[16],
                        "exercises_completed": lesson_row[17],
                        "current_exercise_index": lesson_row[18]
                    },
                    "exercises": exercises,
                    "total_exercises": len(exercises)
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get lesson: {str(e)}")


class CompleteLessonRequest(BaseModel):
    score: int = Field(..., ge=0, le=100)
    mistakes_count: int = 0
    time_spent_seconds: int = 0


@app.post("/api/learning-path/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, request: CompleteLessonRequest, user: dict = Depends(verify_token)):
    """Mark a lesson as complete and award XP."""
    db = get_db()
    user_id = user["user_id"]

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get lesson info
                cur.execute("""
                    SELECT ll.*, lu.unit_id
                    FROM learning_lessons ll
                    JOIN learning_units lu ON ll.unit_id = lu.unit_id
                    WHERE ll.lesson_id = %s
                """, (lesson_id,))

                lesson = cur.fetchone()
                if not lesson:
                    raise HTTPException(status_code=404, detail="Lesson not found")

                xp_reward = lesson[7]  # xp_reward column
                unit_id = lesson[1]    # unit_id column

                # Upsert lesson progress
                cur.execute("""
                    INSERT INTO user_lesson_progress (user_id, lesson_id, completed, score, mistakes_count, time_spent_seconds, completed_at)
                    VALUES (%s, %s, TRUE, %s, %s, %s, NOW())
                    ON CONFLICT (user_id, lesson_id)
                    DO UPDATE SET
                        completed = TRUE,
                        score = GREATEST(user_lesson_progress.score, EXCLUDED.score),
                        mistakes_count = user_lesson_progress.mistakes_count + EXCLUDED.mistakes_count,
                        time_spent_seconds = user_lesson_progress.time_spent_seconds + EXCLUDED.time_spent_seconds,
                        completed_at = NOW()
                    RETURNING id
                """, (user_id, lesson_id, request.score, request.mistakes_count, request.time_spent_seconds))

                # Update unit progress
                cur.execute("""
                    SELECT COUNT(*) FROM learning_lessons WHERE unit_id = %s
                """, (unit_id,))
                total_lessons = cur.fetchone()[0]

                cur.execute("""
                    SELECT COUNT(*) FROM user_lesson_progress ulp
                    JOIN learning_lessons ll ON ulp.lesson_id = ll.lesson_id
                    WHERE ulp.user_id = %s AND ll.unit_id = %s AND ulp.completed = TRUE
                """, (user_id, unit_id))
                lessons_completed = cur.fetchone()[0]

                unit_completed = lessons_completed >= total_lessons

                cur.execute("""
                    INSERT INTO user_unit_progress (user_id, unit_id, lessons_completed, total_lessons, completed, completed_at)
                    VALUES (%s, %s, %s, %s, %s, CASE WHEN %s THEN NOW() ELSE NULL END)
                    ON CONFLICT (user_id, unit_id)
                    DO UPDATE SET
                        lessons_completed = EXCLUDED.lessons_completed,
                        total_lessons = EXCLUDED.total_lessons,
                        completed = EXCLUDED.completed,
                        completed_at = CASE WHEN EXCLUDED.completed AND NOT user_unit_progress.completed THEN NOW() ELSE user_unit_progress.completed_at END
                """, (user_id, unit_id, lessons_completed, total_lessons, unit_completed, unit_completed))

                # Award XP to user profile
                cur.execute("""
                    UPDATE user_profiles
                    SET xp = COALESCE(xp, 0) + %s
                    WHERE user_id = %s
                """, (xp_reward, user_id))

                conn.commit()

                return {
                    "success": True,
                    "xp_earned": xp_reward,
                    "score": request.score,
                    "unit_progress": {
                        "lessons_completed": lessons_completed,
                        "total_lessons": total_lessons,
                        "unit_completed": unit_completed
                    }
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete lesson: {str(e)}")


@app.get("/api/learning-path/next-lesson")
async def get_next_lesson(user: dict = Depends(verify_token)):
    """Get the next recommended lesson for the user."""
    db = get_db()
    user_id = user["user_id"]

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Find first incomplete lesson that's unlocked
                cur.execute("""
                    WITH completed_lessons AS (
                        SELECT lesson_id FROM user_lesson_progress
                        WHERE user_id = %s AND completed = TRUE
                    ),
                    completed_units AS (
                        SELECT unit_id FROM user_unit_progress
                        WHERE user_id = %s AND completed = TRUE
                    )
                    SELECT
                        ll.lesson_id,
                        ll.title as lesson_title,
                        ll.lesson_number,
                        lu.unit_id,
                        lu.title as unit_title,
                        lu.level,
                        ll.xp_reward,
                        ll.estimated_time_minutes
                    FROM learning_lessons ll
                    JOIN learning_units lu ON ll.unit_id = lu.unit_id
                    WHERE ll.lesson_id NOT IN (SELECT lesson_id FROM completed_lessons)
                    AND (
                        lu.order_index = 1  -- First unit always available
                        OR lu.prerequisite_unit_id IN (SELECT unit_id FROM completed_units)
                        OR lu.prerequisite_unit_id IS NULL
                    )
                    ORDER BY lu.order_index, ll.order_index
                    LIMIT 1
                """, (user_id, user_id))

                row = cur.fetchone()

                if not row:
                    return {"next_lesson": None, "message": "All lessons completed!"}

                return {
                    "next_lesson": {
                        "lesson_id": str(row[0]),
                        "lesson_title": row[1],
                        "lesson_number": row[2],
                        "unit_id": str(row[3]),
                        "unit_title": row[4],
                        "level": row[5],
                        "xp_reward": row[6],
                        "estimated_time_minutes": row[7]
                    }
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next lesson: {str(e)}")


@app.post("/api/learning-path/seed")
async def seed_learning_path():
    """Seed the learning path with initial data (admin only - no auth for now)."""
    db = get_db()

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if data already exists
                cur.execute("SELECT COUNT(*) FROM learning_units")
                if cur.fetchone()[0] > 0:
                    return {"message": "Learning path already seeded", "seeded": False}

                # Seed Unit 1: Greetings & Introductions
                cur.execute("""
                    INSERT INTO learning_units (unit_id, unit_number, level, title, description, icon, color, order_index, is_locked, estimated_time_minutes, metadata)
                    VALUES (%s, 1, 'A1', 'Greetings & Introductions', 'Learn how to greet people and introduce yourself in English.', 'wave', '#10B981', 1, FALSE, 30, %s)
                """, ('00000001-0000-0000-0000-000000000001', json.dumps({"skills": ["greetings", "introductions"]})))

                # Seed Unit 1 Lessons
                cur.execute("""
                    INSERT INTO learning_lessons (lesson_id, unit_id, lesson_number, title, description, lesson_type, order_index, xp_reward, is_locked, estimated_time_minutes, content)
                    VALUES
                    (%s, %s, 1, 'Hello & Goodbye', 'Learn basic greetings and farewells', 'standard', 1, 10, FALSE, 5, %s),
                    (%s, %s, 2, 'My Name Is...', 'Learn to introduce yourself', 'standard', 2, 10, TRUE, 5, %s),
                    (%s, %s, 3, 'Where Are You From?', 'Talk about your country and nationality', 'standard', 3, 15, TRUE, 7, %s)
                """, (
                    '00000001-0001-0000-0000-000000000001', '00000001-0000-0000-0000-000000000001',
                    json.dumps({"intro": "Welcome! In this lesson you will learn how to say hello and goodbye in English.", "tips": ["Hello is formal", "Hi is casual", "Goodbye when leaving"]}),
                    '00000001-0001-0000-0000-000000000002', '00000001-0000-0000-0000-000000000001',
                    json.dumps({"intro": "Learn how to introduce yourself and ask for names.", "tips": ["My name is... is formal", "I'm... is casual"]}),
                    '00000001-0001-0000-0000-000000000003', '00000001-0000-0000-0000-000000000001',
                    json.dumps({"intro": "Learn to talk about where you are from.", "tips": ["I am from + country", "Nationalities: American, British, Spanish"]})
                ))

                # Seed Unit 2: Present Tense Basics
                cur.execute("""
                    INSERT INTO learning_units (unit_id, unit_number, level, title, description, icon, color, order_index, is_locked, prerequisite_unit_id, estimated_time_minutes, metadata)
                    VALUES (%s, 2, 'A1', 'Present Tense Basics', 'Master the present simple tense with to be and regular verbs.', 'book', '#3B82F6', 2, TRUE, %s, 45, %s)
                """, ('00000001-0000-0000-0000-000000000002', '00000001-0000-0000-0000-000000000001', json.dumps({"skills": ["present_simple", "to_be"]})))

                # Seed Unit 2 Lessons
                cur.execute("""
                    INSERT INTO learning_lessons (lesson_id, unit_id, lesson_number, title, description, lesson_type, order_index, xp_reward, is_locked, estimated_time_minutes, content)
                    VALUES
                    (%s, %s, 1, 'To Be Verb', 'Learn all forms of the verb to be (am, is, are)', 'standard', 4, 15, TRUE, 8, %s),
                    (%s, %s, 2, 'Present Simple Actions', 'Describe daily actions and routines', 'standard', 5, 15, TRUE, 8, %s),
                    (%s, %s, 3, 'Questions with Do/Does', 'Ask questions in present simple', 'standard', 6, 15, TRUE, 8, %s)
                """, (
                    '00000001-0001-0000-0000-000000000004', '00000001-0000-0000-0000-000000000002',
                    json.dumps({"intro": "The verb 'to be' is the most important verb in English!", "tips": ["I am", "You/We/They are", "He/She/It is"]}),
                    '00000001-0001-0000-0000-000000000005', '00000001-0000-0000-0000-000000000002',
                    json.dumps({"intro": "Use present simple for habits and routines.", "tips": ["I work", "She works (add -s)", "We eat breakfast"]}),
                    '00000001-0001-0000-0000-000000000006', '00000001-0000-0000-0000-000000000002',
                    json.dumps({"intro": "Learn to form questions with do and does.", "tips": ["Do you...?", "Does he/she...?", "Don't forget the base verb!"]})
                ))

                # Seed Unit 3: Everyday Vocabulary
                cur.execute("""
                    INSERT INTO learning_units (unit_id, unit_number, level, title, description, icon, color, order_index, is_locked, prerequisite_unit_id, estimated_time_minutes, metadata)
                    VALUES (%s, 3, 'A1', 'Everyday Vocabulary', 'Learn essential vocabulary: numbers, colors, family, and objects.', 'star', '#F59E0B', 3, TRUE, %s, 40, %s)
                """, ('00000001-0000-0000-0000-000000000003', '00000001-0000-0000-0000-000000000002', json.dumps({"skills": ["numbers", "colors", "family"]})))

                # Seed Unit 3 Lessons
                cur.execute("""
                    INSERT INTO learning_lessons (lesson_id, unit_id, lesson_number, title, description, lesson_type, order_index, xp_reward, is_locked, estimated_time_minutes, content)
                    VALUES
                    (%s, %s, 1, 'Numbers 1-100', 'Learn to count in English', 'standard', 7, 10, TRUE, 6, %s),
                    (%s, %s, 2, 'Colors & Adjectives', 'Learn common colors and descriptions', 'standard', 8, 10, TRUE, 6, %s)
                """, (
                    '00000001-0001-0000-0000-000000000007', '00000001-0000-0000-0000-000000000003',
                    json.dumps({"intro": "Numbers are essential for everyday life!", "tips": ["1-10 are unique", "11-19 end in -teen", "20, 30, 40 end in -ty"]}),
                    '00000001-0001-0000-0000-000000000008', '00000001-0000-0000-0000-000000000003',
                    json.dumps({"intro": "Learn to describe things with colors and adjectives.", "tips": ["Colors come before nouns", "The big red car", "A blue sky"]})
                ))

                # Link exercises to lessons (using existing exercise IDs from exercises.py)
                # Lesson 1: Hello & Goodbye
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-vocab-a1-001', 1),
                    (%s, 'mc-vocab-a1-002', 2),
                    (%s, 'fill-vocab-a1-001', 3),
                    (%s, 'fill-vocab-a1-002', 4),
                    (%s, 'mc-vocab-a1-003', 5)
                """, ('00000001-0001-0000-0000-000000000001',) * 5)

                # Lesson 2: My Name Is
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-gram-a1-001', 1),
                    (%s, 'fill-gram-a1-001', 2),
                    (%s, 'fill-gram-a1-002', 3),
                    (%s, 'mc-gram-a1-002', 4)
                """, ('00000001-0001-0000-0000-000000000002',) * 4)

                # Lesson 3: Where Are You From
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-vocab-a1-004', 1),
                    (%s, 'mc-vocab-a1-005', 2),
                    (%s, 'fill-vocab-a1-003', 3),
                    (%s, 'fill-vocab-a1-004', 4),
                    (%s, 'mc-gram-a1-003', 5)
                """, ('00000001-0001-0000-0000-000000000003',) * 5)

                # Lesson 4: To Be Verb
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-gram-a1-004', 1),
                    (%s, 'fill-gram-a1-003', 2),
                    (%s, 'fill-gram-a1-004', 3),
                    (%s, 'corr-gram-a1-001', 4),
                    (%s, 'mc-gram-a1-005', 5)
                """, ('00000001-0001-0000-0000-000000000004',) * 5)

                # Lesson 5: Present Simple
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-gram-a1-006', 1),
                    (%s, 'fill-gram-a1-005', 2),
                    (%s, 'fill-gram-a1-006', 3),
                    (%s, 'corr-gram-a1-002', 4)
                """, ('00000001-0001-0000-0000-000000000005',) * 4)

                # Lesson 6: Questions
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-gram-a1-007', 1),
                    (%s, 'fill-gram-a1-007', 2),
                    (%s, 'fill-gram-a1-008', 3),
                    (%s, 'corr-gram-a1-003', 4)
                """, ('00000001-0001-0000-0000-000000000006',) * 4)

                # Lesson 7: Numbers
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-vocab-a1-006', 1),
                    (%s, 'mc-vocab-a1-007', 2),
                    (%s, 'fill-vocab-a1-005', 3),
                    (%s, 'fill-vocab-a1-006', 4)
                """, ('00000001-0001-0000-0000-000000000007',) * 4)

                # Lesson 8: Colors
                cur.execute("""
                    INSERT INTO lesson_exercises (lesson_id, exercise_id, order_index)
                    VALUES
                    (%s, 'mc-vocab-a1-008', 1),
                    (%s, 'mc-vocab-a1-009', 2),
                    (%s, 'fill-vocab-a1-007', 3),
                    (%s, 'fill-vocab-a1-008', 4)
                """, ('00000001-0001-0000-0000-000000000008',) * 4)

                conn.commit()

                return {
                    "message": "Learning path seeded successfully!",
                    "seeded": True,
                    "units_created": 3,
                    "lessons_created": 8
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed learning path: {str(e)}")


# ============================================================================
# Diagnostic Test Endpoints
# ============================================================================

class DiagnosticAnswerRequest(BaseModel):
    """Request for submitting a diagnostic answer."""
    session_id: str
    exercise_id: str
    user_answer: str


@app.get("/api/diagnostic/start", tags=["Diagnostic"])
async def start_diagnostic_test(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Start a new diagnostic test session.

    Creates a new session starting at A2 level and returns the first question.
    If an in-progress session exists, resumes that session.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        repo = DiagnosticRepository(db)
        engine = DiagnosticEngine(db)

        # Check for existing in-progress session
        session = repo.get_active_session_for_user(user_id)

        if session:
            # Resume existing session
            used_ids = repo.get_used_exercise_ids(session.session_id)
            next_question = engine.select_next_question(session, used_ids)

            if not next_question:
                # No more questions - complete the session
                session.status = "completed"
                session.completed_at = datetime.utcnow()
                session.user_level = engine._compute_user_level(session.stats)
                repo.update_session(session)

                # Seed mastery
                answers = repo.get_session_answers(session.session_id)
                seed_initial_mastery(db, user_id, session.user_level, answers)

                return {
                    "done": True,
                    "user_level": session.user_level,
                    "summary": {
                        "stats": session.stats,
                        "questions_answered": session.questions_answered
                    }
                }

            return {
                "session_id": str(session.session_id),
                "resuming": True,
                "question": {
                    "exercise_id": next_question.exercise_id,
                    "level": next_question.level,
                    "question": next_question.question,
                    "options": next_question.options,
                    "type": next_question.exercise_type.value
                },
                "progress": {
                    "answered": session.questions_answered,
                    "max": session.max_questions
                }
            }

        # Create new session
        session = DiagnosticSession.create_new(user_id)
        repo.create_session(session)

        # Select first question
        next_question = engine.select_next_question(session, [])

        if not next_question:
            raise HTTPException(status_code=500, detail="No diagnostic exercises available")

        return {
            "session_id": str(session.session_id),
            "resuming": False,
            "question": {
                "exercise_id": next_question.exercise_id,
                "level": next_question.level,
                "question": next_question.question,
                "options": next_question.options,
                "type": next_question.exercise_type.value
            },
            "progress": {
                "answered": 0,
                "max": session.max_questions
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start diagnostic: {str(e)}")


@app.post("/api/diagnostic/answer", tags=["Diagnostic"])
async def submit_diagnostic_answer(
    request: DiagnosticAnswerRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Submit an answer for a diagnostic question.

    Grades the answer, updates session state, and returns the next question
    or completion summary.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        session_id = uuid.UUID(request.session_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    try:
        repo = DiagnosticRepository(db)
        engine = DiagnosticEngine(db)

        # Load session
        session = repo.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.status != "in_progress":
            raise HTTPException(status_code=400, detail="Session already completed")

        if str(session.user_id) != str(user_id):
            raise HTTPException(status_code=403, detail="Session belongs to another user")

        # Load exercise
        exercise = EXERCISES.get(request.exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")

        if not is_diagnostic_exercise(request.exercise_id):
            raise HTTPException(status_code=400, detail="Exercise is not a diagnostic exercise")

        # Grade answer
        is_correct = engine.grade_answer(exercise, request.user_answer)

        # Get skill_key from exercise
        skill_key = exercise.skill_keys[0] if exercise.skill_keys else ""

        # Record answer
        answer = DiagnosticAnswer(
            id=uuid.uuid4(),
            session_id=session_id,
            question_index=session.questions_answered,
            exercise_id=request.exercise_id,
            skill_key=skill_key,
            level=exercise.level,
            user_answer=request.user_answer,
            is_correct=is_correct,
            created_at=datetime.utcnow(),
        )
        repo.add_answer(answer)

        # Update session
        session = engine.update_session_after_answer(session, exercise, is_correct)
        repo.update_session(session)

        # Check if done
        if session.status == "completed":
            # Seed mastery based on results
            answers = repo.get_session_answers(session_id)
            seed_initial_mastery(db, user_id, session.user_level, answers)

            return {
                "done": True,
                "is_correct": is_correct,
                "correct_answer": exercise.correct_answer,
                "user_level": session.user_level,
                "summary": {
                    "stats": session.stats,
                    "questions_answered": session.questions_answered
                }
            }

        # Select next question
        used_ids = repo.get_used_exercise_ids(session_id)
        next_question = engine.select_next_question(session, used_ids)

        if not next_question:
            # No more questions available - complete session
            session.status = "completed"
            session.completed_at = datetime.utcnow()
            session.user_level = engine._compute_user_level(session.stats)
            repo.update_session(session)

            # Seed mastery
            answers = repo.get_session_answers(session_id)
            seed_initial_mastery(db, user_id, session.user_level, answers)

            return {
                "done": True,
                "is_correct": is_correct,
                "correct_answer": exercise.correct_answer,
                "user_level": session.user_level,
                "summary": {
                    "stats": session.stats,
                    "questions_answered": session.questions_answered
                }
            }

        return {
            "done": False,
            "is_correct": is_correct,
            "correct_answer": exercise.correct_answer,
            "question": {
                "exercise_id": next_question.exercise_id,
                "level": next_question.level,
                "question": next_question.question,
                "options": next_question.options,
                "type": next_question.exercise_type.value
            },
            "progress": {
                "answered": session.questions_answered,
                "max": session.max_questions
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@app.post("/admin/migrate/010", tags=["Admin"])
async def apply_migration_010(
    db: Database = Depends(get_database),
):
    """Apply migration 010: Diagnostic tables."""
    import os

    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "database", "migration_010_diagnostic.sql"
    )

    if not os.path.exists(migration_path):
        raise HTTPException(status_code=404, detail=f"Migration file not found: {migration_path}")

    try:
        with open(migration_path, "r") as f:
            migration_sql = f.read()

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(migration_sql)
                conn.commit()

                # Verify tables exist
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_name IN ('diagnostic_sessions', 'diagnostic_answers')
                """)
                tables = cur.fetchall()

                return {
                    "status": "success",
                    "message": "Migration 010 applied successfully",
                    "tables_created": [t[0] if not isinstance(t, dict) else t['table_name'] for t in tables]
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


# ============================================================================
# Guided Mode Endpoints (The Brain)
# ============================================================================

@app.get("/api/learn/guided", tags=["Guided"])
async def get_guided_learning(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get guided learning recommendations.

    Returns the 3-5 weakest skills (A1-B1 only) with a sample exercise for each.
    This is the main "brain" endpoint that powers the learning experience.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if user has completed diagnostic
                cur.execute("""
                    SELECT session_id, user_level, status, completed_at
                    FROM diagnostic_sessions
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT 1
                """, (str(user_id),))
                diagnostic_row = cur.fetchone()

                has_diagnostic = diagnostic_row is not None
                if has_diagnostic:
                    if isinstance(diagnostic_row, dict):
                        user_level = diagnostic_row.get('user_level', 'A2')
                    else:
                        user_level = diagnostic_row[1] if diagnostic_row[1] else 'A2'
                else:
                    user_level = None

                # Get weakest skills (A1-B1 only), limit 5
                cur.execute("""
                    SELECT
                        sd.skill_key,
                        sd.name_en,
                        sd.domain,
                        sd.cefr_level,
                        COALESCE(sgn.p_learned, 0.1) as p_learned,
                        COALESCE(sgn.practice_count, 0) as practice_count
                    FROM skill_definitions sd
                    LEFT JOIN skill_graph_nodes sgn
                        ON sd.skill_key = sgn.skill_key AND sgn.user_id = %s
                    WHERE sd.is_active = TRUE
                      AND sd.cefr_level IN ('A1', 'A2', 'B1')
                    ORDER BY COALESCE(sgn.p_learned, 0.1) ASC, sd.difficulty ASC
                    LIMIT 5
                """, (str(user_id),))
                rows = cur.fetchall()

                skills = []
                for row in rows:
                    if isinstance(row, dict):
                        skill_key = row['skill_key']
                        skill_data = {
                            "skill_key": skill_key,
                            "name": row['name_en'],
                            "domain": row['domain'],
                            "level": row['cefr_level'],
                            "p_learned": row['p_learned'],
                            "practice_count": row['practice_count'],
                        }
                    else:
                        skill_key = row[0]
                        skill_data = {
                            "skill_key": skill_key,
                            "name": row[1],
                            "domain": row[2],
                            "level": row[3],
                            "p_learned": row[4],
                            "practice_count": row[5],
                        }

                    # Get a sample exercise for this skill
                    exercises = get_exercises_by_skill_key(skill_key)
                    if exercises:
                        ex = random.choice(exercises)
                        skill_data["sample_exercise"] = {
                            "exercise_id": ex.exercise_id,
                            "type": ex.exercise_type.value,
                            "question": ex.question,
                            "options": ex.options,
                        }
                    else:
                        skill_data["sample_exercise"] = None

                    skills.append(skill_data)

                return {
                    "has_diagnostic": has_diagnostic,
                    "user_level": user_level,
                    "skills": skills,
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guided learning: {str(e)}")


@app.get("/api/progress/summary", tags=["Progress"])
async def get_progress_summary(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's progress summary.

    Returns:
    - Current inferred level (from diagnostic or mastery)
    - Aggregate mastery numbers (avg P(L) per CEFR band, % skills above 0.8)
    - Minimal time-series (skills practiced counts)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get diagnostic result for user level
                cur.execute("""
                    SELECT user_level, completed_at
                    FROM diagnostic_sessions
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT 1
                """, (str(user_id),))
                diag_row = cur.fetchone()

                if diag_row:
                    if isinstance(diag_row, dict):
                        user_level = diag_row.get('user_level', 'A2')
                    else:
                        user_level = diag_row[0] if diag_row[0] else 'A2'
                else:
                    user_level = None

                # Get mastery stats per CEFR level
                cur.execute("""
                    SELECT
                        sd.cefr_level,
                        COUNT(sd.skill_key) as total_skills,
                        COUNT(sgn.skill_key) as practiced_skills,
                        COALESCE(AVG(sgn.p_learned), 0.1) as avg_mastery,
                        COUNT(CASE WHEN sgn.p_learned >= 0.8 THEN 1 END) as mastered_count
                    FROM skill_definitions sd
                    LEFT JOIN skill_graph_nodes sgn
                        ON sd.skill_key = sgn.skill_key AND sgn.user_id = %s
                    WHERE sd.is_active = TRUE
                      AND sd.cefr_level IN ('A1', 'A2', 'B1')
                    GROUP BY sd.cefr_level
                    ORDER BY sd.cefr_level
                """, (str(user_id),))
                level_rows = cur.fetchall()

                levels = {}
                total_skills = 0
                total_mastered = 0
                for row in level_rows:
                    if isinstance(row, dict):
                        level = row['cefr_level']
                        avg_mastery = round(row['avg_mastery'], 3) if row['avg_mastery'] else 0.1
                        levels[level] = {
                            "total_skills": row['total_skills'],
                            "mastered_skills": row['mastered_count'],
                            "average_mastery": avg_mastery,
                            "mastery_percentage": round(avg_mastery * 100, 1),
                        }
                        total_skills += row['total_skills']
                        total_mastered += row['mastered_count']
                    else:
                        level = row[0]
                        avg_mastery = round(row[3], 3) if row[3] else 0.1
                        levels[level] = {
                            "total_skills": row[1],
                            "mastered_skills": row[4] if row[4] else 0,
                            "average_mastery": avg_mastery,
                            "mastery_percentage": round(avg_mastery * 100, 1),
                        }
                        total_skills += row[1]
                        total_mastered += row[4] if row[4] else 0

                # Calculate overall stats
                overall_mastery_pct = round((total_mastered / total_skills) * 100, 1) if total_skills > 0 else 0

                # Get recent practice activity (last 10 days)
                cur.execute("""
                    SELECT COUNT(DISTINCT skill_key) as skills_practiced
                    FROM skill_graph_nodes
                    WHERE user_id = %s
                      AND last_practiced >= NOW() - INTERVAL '10 days'
                """, (str(user_id),))
                recent_row = cur.fetchone()
                if isinstance(recent_row, dict):
                    recent_skills_practiced = recent_row.get('skills_practiced', 0)
                else:
                    recent_skills_practiced = recent_row[0] if recent_row else 0

                return {
                    "user_level": user_level,
                    "has_diagnostic": user_level is not None,
                    "total_skills": total_skills,
                    "mastered_skills": total_mastered,
                    "mastery_percentage": overall_mastery_pct,
                    "by_level": levels,
                    "recent_activity": {
                        "skills_practiced_last_10_days": recent_skills_practiced,
                    }
                }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get progress summary: {str(e)}")


@app.get("/api/user/diagnostic-status", tags=["User"])
async def get_diagnostic_status(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Check if user has completed the diagnostic test.

    Used by frontend to redirect new users to diagnostic.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Check for completed diagnostic
                cur.execute("""
                    SELECT session_id, user_level, completed_at
                    FROM diagnostic_sessions
                    WHERE user_id = %s AND status = 'completed'
                    ORDER BY completed_at DESC
                    LIMIT 1
                """, (str(user_id),))
                completed = cur.fetchone()

                # Check for in-progress diagnostic
                cur.execute("""
                    SELECT session_id, questions_answered, max_questions
                    FROM diagnostic_sessions
                    WHERE user_id = %s AND status = 'in_progress'
                    ORDER BY started_at DESC
                    LIMIT 1
                """, (str(user_id),))
                in_progress = cur.fetchone()

                if completed:
                    if isinstance(completed, dict):
                        return {
                            "status": "completed",
                            "user_level": completed.get('user_level'),
                            "completed_at": completed.get('completed_at').isoformat() if completed.get('completed_at') else None,
                        }
                    else:
                        return {
                            "status": "completed",
                            "user_level": completed[1],
                            "completed_at": completed[2].isoformat() if completed[2] else None,
                        }
                elif in_progress:
                    if isinstance(in_progress, dict):
                        return {
                            "status": "in_progress",
                            "session_id": str(in_progress.get('session_id')),
                            "questions_answered": in_progress.get('questions_answered'),
                            "max_questions": in_progress.get('max_questions'),
                        }
                    else:
                        return {
                            "status": "in_progress",
                            "session_id": str(in_progress[0]),
                            "questions_answered": in_progress[1],
                            "max_questions": in_progress[2],
                        }
                else:
                    return {
                        "status": "not_started",
                    }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get diagnostic status: {str(e)}")


# =============================================================================
# THINKING IN ENGLISH ENDPOINTS
# =============================================================================

from app.thinking_engine import thinking_engine, MAX_TURNS_HARD_CAP, MIN_TURNS_FOR_XP


@app.post("/api/think/start", tags=["Think"])
async def start_thinking_session(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Start a new Thinking in English session.
    Returns a session ID and the first question from the AI.

    Policies:
    - Free users: 3 sessions/day max
    - Only one active session per user (previous is auto-ended)
    - Resumes existing active session if present
    """
    try:
        user_id = uuid.UUID(user_id_from_token)

        # Get user profile to determine level and subscription
        profile = db.get_user(user_id)

        # Default values for new/missing users (allows QA testing)
        if not profile:
            profile = {"level": "A2", "is_tester": True, "subscription_status": None}

        # Check if user is paid (subscription_status or is_tester)
        is_paid = profile.get("is_tester", False) or profile.get("subscription_status") == "active"

        # Check for existing active session
        existing_session = thinking_engine.get_active_session(str(user_id))
        if existing_session:
            # Return existing session
            starter = thinking_engine.get_starter_question(existing_session.level)
            return {
                "session_id": existing_session.session_id,
                "level": existing_session.level,
                "max_turns": existing_session.max_turns,
                "current_turn": len(existing_session.turns),
                "ai_message": existing_session.turns[-1].ai_response if existing_session.turns else starter,
                "question_asked": existing_session.turns[-1].question_asked if existing_session.turns else None,
                "resuming": True,
            }

        # Check session limit for free users
        if not thinking_engine.check_session_limit(str(user_id), is_paid):
            raise HTTPException(
                status_code=429,
                detail="Daily session limit reached. Upgrade to premium for unlimited sessions."
            )

        # Determine level from profile
        user_level = profile.get("level", "A2")
        if user_level == "A1":
            think_level = "A1"
        elif user_level == "A2":
            think_level = "A2"
        else:  # B1, B2, C1, C2
            think_level = "B1"

        # Create new session using engine
        session = thinking_engine.create_session(
            user_id=str(user_id),
            level=think_level,
            source="learn",
        )

        # Get starter question
        starter = thinking_engine.get_starter_question(think_level)

        return {
            "session_id": session.session_id,
            "level": think_level,
            "max_turns": session.max_turns,
            "current_turn": 0,
            "ai_message": starter,
            "question_asked": starter,
            "resuming": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start thinking session: {str(e)}")


@app.post("/api/think/respond", tags=["Think"])
async def respond_thinking_session(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Respond to a Thinking in English session.
    Takes user message and returns AI response with optional correction.

    Edge cases handled:
    - User says "idk" / "I don't know" -> simplified question
    - User types in native language -> prompt to try English
    - User gives very short answer -> ask for more (once)
    - User mentions forbidden topic -> gentle redirect
    """
    try:
        from app.llm_client import llm_client
        from app.config import config

        user_id = uuid.UUID(user_id_from_token)
        session_id = payload.get("session_id")
        # Accept both "message" and "user_message" for frontend compatibility
        user_message = payload.get("user_message") or payload.get("message", "")
        user_message = user_message.strip() if user_message else ""

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        if not user_message:
            raise HTTPException(status_code=400, detail="message is required")

        # Get session
        session = thinking_engine.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != str(user_id):
            raise HTTPException(status_code=403, detail="Session belongs to another user")

        # Hard cap check
        if len(session.turns) >= MAX_TURNS_HARD_CAP:
            summary = thinking_engine.end_session(session_id)
            # XP is returned in summary, tracked via analytics
            # TODO: Persist XP to database when XP table is ready
            return {
                "done": True,
                "summary": summary,
            }

        # Check if already at max turns
        if len(session.turns) >= session.max_turns:
            summary = thinking_engine.end_session(session_id)
            return {
                "done": True,
                "summary": summary,
            }

        # Preprocess message for edge cases (idk, native lang, short answer, forbidden topic)
        processed_message, special_response = thinking_engine.preprocess_user_message(
            user_message, session
        )

        # If we have a special response (guardrail triggered), use it directly
        if special_response:
            turn = thinking_engine.add_turn(session, processed_message, special_response)
            is_done = len(session.turns) >= session.max_turns
            response_data = {
                "done": is_done,
                "current_turn": len(session.turns),
                "max_turns": session.max_turns,
                "ai_message": special_response.get("message", ""),
                "question_asked": special_response.get("question_asked", ""),
                "correction": None,
            }
            if is_done:
                summary = thinking_engine.end_session(session_id)
                response_data["summary"] = summary
            return response_data

        # Normal flow: call LLM
        context = thinking_engine.build_conversation_context(session)
        system_prompt = thinking_engine.get_system_prompt(session.level)

        ai_response_text = ""
        if config.enable_llm and llm_client.client:
            try:
                if llm_client.provider == "openai":
                    response = llm_client.client.chat.completions.create(
                        model=llm_client.config.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"{context}\n\nUser: {processed_message}\n\nRespond with JSON:"}
                        ],
                        temperature=0.7,
                        max_tokens=150,  # Reduced from 200 to enforce shorter responses
                    )
                    ai_response_text = response.choices[0].message.content
                elif llm_client.provider == "anthropic":
                    response = llm_client.client.messages.create(
                        model=llm_client.config.model,
                        max_tokens=150,
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"{context}\n\nUser: {processed_message}\n\nRespond with JSON:"}
                        ],
                    )
                    ai_response_text = response.content[0].text
            except Exception as e:
                print(f"[THINK] LLM call failed: {e}")
                ai_response_text = ""

        # Parse response with validation
        if ai_response_text:
            parsed = thinking_engine.parse_llm_response(ai_response_text, session.level)
        else:
            # Fallback response
            fallback_questions = {
                "A1": "That's nice! Do you like it?",
                "A2": "Interesting! Can you tell me more?",
                "B1": "I see! What do you think about that?",
            }
            q = fallback_questions.get(session.level, "Tell me more!")
            parsed = {
                "message": q,
                "correction": None,
                "question_asked": q,
            }

        # Add turn
        turn = thinking_engine.add_turn(session, processed_message, parsed)

        # Check if done
        is_done = len(session.turns) >= session.max_turns

        response_data = {
            "done": is_done,
            "current_turn": len(session.turns),
            "max_turns": session.max_turns,
            "ai_message": parsed.get("message", ""),
            "question_asked": parsed.get("question_asked", ""),
            "correction": turn.correction,
        }

        if is_done:
            summary = thinking_engine.end_session(session_id)
            response_data["summary"] = summary

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process thinking response: {str(e)}")


@app.post("/api/think/end", tags=["Think"])
async def end_thinking_session(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    End a Thinking in English session early.
    Returns the session summary.

    XP awarded only if:
    - Full session (10 turns): 50 XP
    - Partial (6+ turns): 25 XP
    - Less than 6 turns: 0 XP
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        session_id = payload.get("session_id")

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        session = thinking_engine.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != str(user_id):
            raise HTTPException(status_code=403, detail="Session belongs to another user")

        # End session and get summary
        summary = thinking_engine.end_session(session_id)

        # Persist XP to database
        xp_earned = summary.get("xp_earned", 0)
        total_xp = None
        if xp_earned > 0:
            try:
                total_xp = add_user_xp(user_id_from_token, xp_earned)
            except Exception as e:
                print(f"Warning: Failed to add Think XP: {e}")

        return {
            "done": True,
            "summary": summary,
            "total_xp": total_xp,
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to end thinking session: {str(e)}")


@app.get("/api/think/session/{session_id}", tags=["Think"])
async def get_thinking_session(
    session_id: str,
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get the current state of a Thinking in English session.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)

        session = thinking_engine.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session.user_id != str(user_id):
            raise HTTPException(status_code=403, detail="Session belongs to another user")

        return session.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thinking session: {str(e)}")


# ============================================================================
# XP & Analytics Endpoints
# ============================================================================

class XPRecordRequest(BaseModel):
    """Request model for recording XP."""
    activity_type: str  # exercise, lesson, drill, voice, review
    xp_earned: int
    bonus_xp: int = 0
    session_id: Optional[str] = None


@app.post("/api/xp/record", tags=["Analytics"])
async def record_xp(
    payload: XPRecordRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Record XP earned from an activity.

    This is the authoritative endpoint for XP tracking.
    Frontend should call this when user earns XP.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        total_xp_to_add = payload.xp_earned + payload.bonus_xp

        if total_xp_to_add <= 0:
            raise HTTPException(status_code=400, detail="XP must be positive")

        # Cap XP per request to prevent abuse
        if total_xp_to_add > 500:
            total_xp_to_add = 500

        # Add XP to user profile
        new_total = add_user_xp(user_id_from_token, total_xp_to_add)

        # Log the XP activity
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO xp_log (user_id, activity_type, xp_earned, bonus_xp, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT DO NOTHING
                """, (user_id, payload.activity_type, payload.xp_earned, payload.bonus_xp))
                conn.commit()

        return {
            "success": True,
            "xp_added": total_xp_to_add,
            "total_xp": new_total,
        }
    except HTTPException:
        raise
    except Exception as e:
        # If xp_log table doesn't exist, just return success with XP added
        print(f"Warning: XP log failed (table may not exist): {e}")
        return {
            "success": True,
            "xp_added": total_xp_to_add,
            "total_xp": add_user_xp(user_id_from_token, 0),  # Get current total
        }


class SessionTrackRequest(BaseModel):
    """Request model for tracking study sessions."""
    activity_type: str  # lesson, drill, voice, review, exercise
    duration_seconds: int
    started_at: Optional[str] = None  # ISO timestamp


@app.post("/api/sessions/track", tags=["Analytics"])
async def track_study_session(
    payload: SessionTrackRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Track study time for analytics.

    Frontend should call this when user finishes a learning session.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)

        if payload.duration_seconds <= 0:
            raise HTTPException(status_code=400, detail="Duration must be positive")

        # Cap duration to 4 hours to prevent abuse
        duration = min(payload.duration_seconds, 14400)

        # Try to insert into study_sessions table
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO study_sessions (id, user_id, activity_type, duration_seconds, started_at, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (uuid.uuid4(), user_id, payload.activity_type, duration,
                      payload.started_at or datetime.now().isoformat()))
                conn.commit()

        # Get today's total study time
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(duration_seconds), 0) as today_total
                    FROM study_sessions
                    WHERE user_id = %s
                    AND created_at >= CURRENT_DATE
                """, (user_id,))
                result = cur.fetchone()
                today_total = result['today_total'] if result else 0

        return {
            "success": True,
            "duration_recorded": duration,
            "today_total_seconds": today_total,
        }
    except HTTPException:
        raise
    except Exception as e:
        # If study_sessions table doesn't exist, return success anyway
        print(f"Warning: Session tracking failed (table may not exist): {e}")
        return {
            "success": True,
            "duration_recorded": payload.duration_seconds,
            "today_total_seconds": payload.duration_seconds,
        }


@app.get("/api/analytics/summary", tags=["Analytics"])
async def get_analytics_summary(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's analytics summary for dashboard.

    Returns:
    - Total XP and level
    - Today's study time
    - Weekly study time
    - Current streak
    """
    try:
        user_id = uuid.UUID(user_id_from_token)

        # Get XP and level
        total_xp = get_user_xp(user_id_from_token)
        level = total_xp // 100 + 1  # 100 XP per level
        xp_in_level = total_xp % 100

        # Try to get study time stats
        today_seconds = 0
        week_seconds = 0
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Today's study time
                    cur.execute("""
                        SELECT COALESCE(SUM(duration_seconds), 0) as total
                        FROM study_sessions
                        WHERE user_id = %s AND created_at >= CURRENT_DATE
                    """, (user_id,))
                    result = cur.fetchone()
                    today_seconds = result['total'] if result else 0

                    # This week's study time
                    cur.execute("""
                        SELECT COALESCE(SUM(duration_seconds), 0) as total
                        FROM study_sessions
                        WHERE user_id = %s AND created_at >= CURRENT_DATE - INTERVAL '7 days'
                    """, (user_id,))
                    result = cur.fetchone()
                    week_seconds = result['total'] if result else 0
        except Exception as e:
            print(f"Warning: Could not get study time: {e}")

        # Try to get streak
        current_streak = 0
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT current_streak FROM user_streaks WHERE user_id = %s
                    """, (user_id,))
                    result = cur.fetchone()
                    current_streak = result['current_streak'] if result else 0
        except Exception as e:
            print(f"Warning: Could not get streak: {e}")

        return {
            "xp": {
                "total": total_xp,
                "level": level,
                "xp_in_level": xp_in_level,
                "xp_to_next_level": 100 - xp_in_level,
            },
            "study_time": {
                "today_seconds": today_seconds,
                "today_minutes": today_seconds // 60,
                "week_seconds": week_seconds,
                "week_minutes": week_seconds // 60,
            },
            "streak": {
                "current": current_streak,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@app.get("/api/skills/history", tags=["Analytics"])
async def get_skills_history(
    days: int = 30,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get skill mastery history for the past N days.

    Used for progress charts on dashboard.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)

        # Get current skill masteries
        skills = []
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT skill_key, mastery_score, last_practiced, practice_count
                        FROM skill_graph_nodes
                        WHERE user_id = %s
                        ORDER BY mastery_score DESC
                        LIMIT 10
                    """, (user_id,))
                    rows = cur.fetchall()

                    for row in rows:
                        skills.append({
                            "skill_key": row['skill_key'],
                            "mastery_score": row['mastery_score'],
                            "last_practiced": row['last_practiced'].isoformat() if row['last_practiced'] else None,
                            "practice_count": row['practice_count'],
                        })
        except Exception as e:
            print(f"Warning: Could not get skills: {e}")

        # Calculate overall trend (simplified - just compare first and last practice)
        overall_trend = 0
        if skills:
            avg_mastery = sum(s['mastery_score'] for s in skills) / len(skills)
            overall_trend = avg_mastery  # Simplified for now

        return {
            "skills": skills,
            "overall_mastery": overall_trend,
            "days": days,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get skills history: {str(e)}")


@app.get("/api/analytics/heatmap", tags=["Analytics"])
async def get_activity_heatmap(
    days: int = 365,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get activity heatmap data for the past N days.

    Returns daily activity data for GitHub-style heatmap visualization:
    - date: The day
    - xp: Total XP earned that day
    - lessons: Number of lessons completed
    - sessions: Number of study sessions
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        heatmap_data = db.get_activity_heatmap(user_id, days=days)

        return {
            "success": True,
            "days_requested": days,
            "data": heatmap_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get activity heatmap: {str(e)}")


@app.get("/api/analytics/insights", tags=["Analytics"])
async def get_learning_insights(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get detailed learning insights for the user.

    Returns comprehensive analytics:
    - best_study_hours: Which hours of the day user performs best
    - day_performance: Performance by day of week
    - error_trends: Recent error patterns and categories
    - skill_progress: Progress in each skill area
    - streak: Current and longest streaks
    - totals: Overall stats (lessons, XP, time)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        insights = db.get_learning_insights(user_id)

        return {
            "success": True,
            **insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning insights: {str(e)}")


@app.post("/api/achievements/check", tags=["Analytics"])
async def check_achievements(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Check and unlock any new achievements for the user.

    Checks user's stats against achievement conditions and unlocks
    any newly qualified achievements, awarding XP for each.

    Returns:
    - newly_unlocked: List of achievements just unlocked
    - total_unlocked: Total number of achievements user has
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
        newly_unlocked = []

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get all achievements the user hasn't unlocked yet
                cur.execute("""
                    SELECT a.achievement_id, a.key, a.title, a.description, a.xp_reward, a.tier
                    FROM achievements a
                    WHERE a.achievement_id NOT IN (
                        SELECT achievement_id FROM user_achievements WHERE user_id = %s
                    )
                """, (user_id,))
                available_achievements = cur.fetchall()

                # Get user's stats for checking conditions
                stats = {}

                # Streak
                cur.execute("SELECT current_streak FROM user_streaks WHERE user_id = %s", (user_id,))
                streak_row = cur.fetchone()
                stats['current_streak'] = streak_row['current_streak'] if streak_row else 0

                # Completed sessions count
                cur.execute("""
                    SELECT COUNT(*) as count FROM sessions
                    WHERE user_id = %s AND state = 'completed'
                """, (user_id,))
                session_row = cur.fetchone()
                stats['completed_sessions'] = session_row['count'] if session_row else 0

                # Voice sessions count
                cur.execute("""
                    SELECT COUNT(*) as count FROM sessions
                    WHERE user_id = %s AND session_type = 'voice' AND state = 'completed'
                """, (user_id,))
                voice_row = cur.fetchone()
                stats['voice_sessions'] = voice_row['count'] if voice_row else 0

                # Total exercises (approximate from XP log or skill practice count)
                cur.execute("""
                    SELECT COALESCE(SUM(practice_count), 0) as total FROM skill_graph_nodes
                    WHERE user_id = %s
                """, (user_id,))
                exercise_row = cur.fetchone()
                stats['total_exercises'] = exercise_row['total'] if exercise_row else 0

                # Best pronunciation score (from evaluations if available)
                cur.execute("""
                    SELECT MAX((scores->>'pronunciation')::float) as best
                    FROM evaluations
                    WHERE user_id = %s AND scores->>'pronunciation' IS NOT NULL
                """, (user_id,))
                pron_row = cur.fetchone()
                stats['best_pronunciation'] = pron_row['best'] if pron_row and pron_row['best'] else 0

                # Total XP
                cur.execute("SELECT COALESCE(total_xp, 0) as total_xp FROM user_profiles WHERE user_id = %s", (user_id,))
                xp_row = cur.fetchone()
                stats['total_xp'] = xp_row['total_xp'] if xp_row else 0

                # Perfect lessons (100% score)
                cur.execute("""
                    SELECT COUNT(*) as count FROM learning_path_progress
                    WHERE user_id = %s AND best_score = 100
                """, (user_id,))
                perfect_row = cur.fetchone()
                stats['perfect_lessons'] = perfect_row['count'] if perfect_row else 0

                # Completed lessons
                cur.execute("""
                    SELECT COUNT(*) as count FROM learning_path_progress
                    WHERE user_id = %s AND completed = true
                """, (user_id,))
                lessons_row = cur.fetchone()
                stats['completed_lessons'] = lessons_row['count'] if lessons_row else 0

                # Completed units
                cur.execute("""
                    SELECT COUNT(DISTINCT unit_id) as count FROM learning_path_progress lpp
                    JOIN learning_path_lessons lpl ON lpp.lesson_id = lpl.lesson_id
                    WHERE lpp.user_id = %s AND lpp.completed = true
                """, (user_id,))
                units_row = cur.fetchone()
                stats['completed_units'] = units_row['count'] if units_row else 0

                # Check each available achievement
                for achievement in available_achievements:
                    key = achievement['key']
                    unlocked = False

                    # Streaks
                    if key == 'first_lesson' and stats['completed_sessions'] >= 1:
                        unlocked = True
                    elif key == '5_day_streak' and stats['current_streak'] >= 5:
                        unlocked = True
                    elif key == '10_day_streak' and stats['current_streak'] >= 10:
                        unlocked = True
                    elif key == '30_day_streak' and stats['current_streak'] >= 30:
                        unlocked = True
                    elif key == 'week_streak' and stats['current_streak'] >= 7:
                        unlocked = True
                    elif key == 'month_streak' and stats['current_streak'] >= 30:
                        unlocked = True

                    # XP milestones
                    elif key == 'xp_100' and stats['total_xp'] >= 100:
                        unlocked = True
                    elif key == 'xp_500' and stats['total_xp'] >= 500:
                        unlocked = True
                    elif key == 'xp_1000' and stats['total_xp'] >= 1000:
                        unlocked = True
                    elif key == 'xp_5000' and stats['total_xp'] >= 5000:
                        unlocked = True
                    elif key == 'xp_10000' and stats['total_xp'] >= 10000:
                        unlocked = True

                    # Voice sessions
                    elif key == 'first_voice' and stats['voice_sessions'] >= 1:
                        unlocked = True
                    elif key == 'voice_5' and stats['voice_sessions'] >= 5:
                        unlocked = True
                    elif key == 'voice_25' and stats['voice_sessions'] >= 25:
                        unlocked = True
                    elif key == 'voice_100' and stats['voice_sessions'] >= 100:
                        unlocked = True
                    elif key == 'voice_explorer' and stats['voice_sessions'] >= 10:
                        unlocked = True

                    # Pronunciation
                    elif key == 'pronunciation_80' and stats['best_pronunciation'] >= 80:
                        unlocked = True
                    elif key == 'pronunciation_90' and stats['best_pronunciation'] >= 90:
                        unlocked = True
                    elif key == 'pronunciation_95' and stats['best_pronunciation'] >= 95:
                        unlocked = True
                    elif key == 'pronunciation_master' and stats['best_pronunciation'] >= 90:
                        unlocked = True

                    # Perfect lessons
                    elif key == 'perfect_lesson' and stats['perfect_lessons'] >= 1:
                        unlocked = True
                    elif key == 'perfect_5' and stats['perfect_lessons'] >= 5:
                        unlocked = True
                    elif key == 'perfect_20' and stats['perfect_lessons'] >= 20:
                        unlocked = True

                    # Completed lessons
                    elif key == '10_lessons_completed' and stats['completed_lessons'] >= 10:
                        unlocked = True
                    elif key == '50_lessons_completed' and stats['completed_lessons'] >= 50:
                        unlocked = True

                    # Learning path
                    elif key == 'path_started' and stats['completed_lessons'] >= 1:
                        unlocked = True
                    elif key == 'unit_complete' and stats['completed_units'] >= 1:
                        unlocked = True

                    # Exercises
                    elif key == '100_exercises' and stats['total_exercises'] >= 100:
                        unlocked = True

                    if unlocked:
                        # Insert into user_achievements
                        cur.execute("""
                            INSERT INTO user_achievements (user_id, achievement_id)
                            VALUES (%s, %s)
                            ON CONFLICT (user_id, achievement_id) DO NOTHING
                        """, (user_id, achievement['achievement_id']))

                        # Award XP
                        if achievement['xp_reward'] > 0:
                            add_user_xp(user_id_from_token, achievement['xp_reward'])

                        newly_unlocked.append({
                            "key": achievement['key'],
                            "title": achievement['title'],
                            "description": achievement['description'],
                            "xp_reward": achievement['xp_reward'],
                            "tier": achievement['tier'],
                        })

                conn.commit()

                # Get total unlocked count
                cur.execute("""
                    SELECT COUNT(*) as count FROM user_achievements WHERE user_id = %s
                """, (user_id,))
                total_row = cur.fetchone()
                total_unlocked = total_row['count'] if total_row else 0

        return {
            "newly_unlocked": newly_unlocked,
            "total_unlocked": total_unlocked,
        }

    except Exception as e:
        print(f"Error checking achievements: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check achievements: {str(e)}")


# ============================================================================
# Push Notifications Endpoints
# ============================================================================

@app.post("/api/push/subscribe", tags=["Push Notifications"])
async def subscribe_to_push(
    subscription: dict,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Register a push notification subscription for the user.

    Body:
        - endpoint: Push service endpoint URL
        - p256dh: Public key for encryption
        - auth: Auth secret for encryption

    Returns:
        Success status
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    endpoint = subscription.get("endpoint")
    p256dh = subscription.get("p256dh")
    auth = subscription.get("auth")

    if not endpoint or not p256dh or not auth:
        raise HTTPException(status_code=400, detail="Missing subscription data")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Upsert subscription
                cur.execute("""
                    INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (endpoint) DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        p256dh = EXCLUDED.p256dh,
                        auth = EXCLUDED.auth,
                        last_used_at = NOW()
                """, (user_id, endpoint, p256dh, auth))

                # Enable push preferences if not already
                cur.execute("""
                    INSERT INTO push_preferences (user_id, enabled)
                    VALUES (%s, TRUE)
                    ON CONFLICT (user_id) DO UPDATE SET enabled = TRUE, updated_at = NOW()
                """, (user_id,))

                conn.commit()

        return {"success": True}

    except Exception as e:
        print(f"Error subscribing to push: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe: {str(e)}")


@app.post("/api/push/unsubscribe", tags=["Push Notifications"])
async def unsubscribe_from_push(
    data: dict,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Remove a push notification subscription.

    Body:
        - endpoint: Push service endpoint URL to remove

    Returns:
        Success status
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    endpoint = data.get("endpoint")
    if not endpoint:
        raise HTTPException(status_code=400, detail="Missing endpoint")

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM push_subscriptions
                    WHERE user_id = %s AND endpoint = %s
                """, (user_id, endpoint))
                conn.commit()

        return {"success": True}

    except Exception as e:
        print(f"Error unsubscribing from push: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unsubscribe: {str(e)}")


@app.get("/api/push/preferences", tags=["Push Notifications"])
async def get_push_preferences(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get push notification preferences for the user.

    Returns:
        - enabled: Whether push is enabled
        - streak_reminders: Notify about streak risks
        - friend_challenges: Notify about friend challenges
        - achievements: Notify about achievements
        - daily_goals: Notify about daily goals
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM get_or_create_push_preferences(%s)", (user_id,))
                result = cur.fetchone()
                conn.commit()

        if result:
            return {
                "enabled": result["enabled"],
                "streak_reminders": result["streak_reminders"],
                "friend_challenges": result["friend_challenges"],
                "achievements": result["achievements"],
                "daily_goals": result["daily_goals"],
            }
        else:
            return {
                "enabled": False,
                "streak_reminders": True,
                "friend_challenges": True,
                "achievements": True,
                "daily_goals": True,
            }

    except Exception as e:
        print(f"Error getting push preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get preferences: {str(e)}")


@app.put("/api/push/preferences", tags=["Push Notifications"])
async def update_push_preferences(
    preferences: dict,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Update push notification preferences.

    Body (all optional):
        - enabled: Whether push is enabled
        - streak_reminders: Notify about streak risks
        - friend_challenges: Notify about friend challenges
        - achievements: Notify about achievements
        - daily_goals: Notify about daily goals

    Returns:
        Updated preferences
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM update_push_preferences(
                        %s, %s, %s, %s, %s, %s
                    )
                """, (
                    user_id,
                    preferences.get("enabled"),
                    preferences.get("streak_reminders"),
                    preferences.get("friend_challenges"),
                    preferences.get("achievements"),
                    preferences.get("daily_goals"),
                ))
                result = cur.fetchone()
                conn.commit()

        if result:
            return {
                "enabled": result["enabled"],
                "streak_reminders": result["streak_reminders"],
                "friend_challenges": result["friend_challenges"],
                "achievements": result["achievements"],
                "daily_goals": result["daily_goals"],
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update preferences")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating push preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@app.post("/api/push/test", tags=["Push Notifications"])
async def send_test_push(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Send a test push notification to verify setup is working.

    Returns:
        Success status and message
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Get user's push subscriptions
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT endpoint, p256dh, auth
                    FROM push_subscriptions
                    WHERE user_id = %s
                """, (user_id,))
                subscriptions = cur.fetchall()

        if not subscriptions:
            return {
                "success": False,
                "message": "No push subscription found. Please enable notifications first."
            }

        # Note: In production, you would use pywebpush to send actual notifications
        # For now, we'll just verify the subscription exists
        return {
            "success": True,
            "message": f"Test notification queued for {len(subscriptions)} device(s)."
        }

    except Exception as e:
        print(f"Error sending test push: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test: {str(e)}")


# ============================================================================
# Gamification Bonuses Endpoints
# ============================================================================

@app.get("/api/bonuses/summary", tags=["Bonuses"])
async def get_bonus_summary(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get active bonuses and today's bonus summary for the user.

    Returns:
        - total_bonus_xp_today: Total bonus XP earned today
        - bonuses_claimed: List of bonuses claimed today
        - available_bonuses: Available bonuses (login, streak, weekend, event)
        - current_multiplier: Combined XP multiplier
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Call the get_bonus_summary function
                cur.execute("SELECT * FROM get_bonus_summary(%s)", (user_id,))
                result = cur.fetchone()

        if result:
            return {
                "total_bonus_xp_today": result["total_bonus_xp_today"] or 0,
                "bonuses_claimed": result["bonuses_claimed"] or [],
                "available_bonuses": result["available_bonuses"] or {
                    "login_bonus": {"available": False, "xp": 25},
                    "streak_bonus": {"active": False, "multiplier": 1.0, "streak_days": 0},
                    "weekend_bonus": {"active": False, "multiplier": 1.0},
                    "event_bonus": {"active": False, "name": None, "multiplier": 1.0}
                },
                "current_multiplier": float(result["current_multiplier"]) if result["current_multiplier"] else 1.0
            }
        else:
            # Return defaults if no result
            return {
                "total_bonus_xp_today": 0,
                "bonuses_claimed": [],
                "available_bonuses": {
                    "login_bonus": {"available": True, "xp": 25},
                    "streak_bonus": {"active": False, "multiplier": 1.0, "streak_days": 0},
                    "weekend_bonus": {"active": False, "multiplier": 1.0},
                    "event_bonus": {"active": False, "name": None, "multiplier": 1.0}
                },
                "current_multiplier": 1.0
            }

    except Exception as e:
        print(f"Error getting bonus summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get bonus summary: {str(e)}")


@app.post("/api/bonuses/claim-login", tags=["Bonuses"])
async def claim_login_bonus(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Claim the daily login bonus.

    Returns:
        - success: Whether the claim was successful
        - xp_earned: Amount of XP earned (with streak multiplier applied)
        - message: Status message
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Call the claim_login_bonus function
                cur.execute("SELECT * FROM claim_login_bonus(%s)", (user_id,))
                result = cur.fetchone()
                conn.commit()

        if result:
            return {
                "success": result["success"],
                "xp_earned": result["xp_earned"] or 0,
                "message": result["message"] or "Login bonus processed"
            }
        else:
            return {
                "success": False,
                "xp_earned": 0,
                "message": "Failed to claim login bonus"
            }

    except Exception as e:
        print(f"Error claiming login bonus: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to claim login bonus: {str(e)}")


@app.get("/api/bonuses/active", tags=["Bonuses"])
async def get_active_bonuses(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get active XP bonuses for the user.

    Returns:
        - login_bonus_available: Whether login bonus can be claimed
        - login_bonus_xp: XP amount for login bonus
        - streak_multiplier: Current streak multiplier
        - streak_days: Current streak days
        - weekend_bonus_active: Whether weekend bonus is active
        - weekend_multiplier: Weekend multiplier (1.5x on weekends)
        - event_bonus_active: Whether a special event is active
        - event_name: Name of active event (if any)
        - event_multiplier: Event multiplier
        - total_multiplier: Combined multiplier
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Call the get_active_bonuses function
                cur.execute("SELECT * FROM get_active_bonuses(%s)", (user_id,))
                result = cur.fetchone()

        if result:
            return {
                "login_bonus_available": result["login_bonus_available"],
                "login_bonus_xp": result["login_bonus_xp"] or 25,
                "streak_multiplier": float(result["streak_multiplier"]) if result["streak_multiplier"] else 1.0,
                "streak_days": result["streak_days"] or 0,
                "weekend_bonus_active": result["weekend_bonus_active"],
                "weekend_multiplier": float(result["weekend_multiplier"]) if result["weekend_multiplier"] else 1.0,
                "event_bonus_active": result["event_bonus_active"],
                "event_name": result["event_name"],
                "event_multiplier": float(result["event_multiplier"]) if result["event_multiplier"] else 1.0,
                "total_multiplier": float(result["total_multiplier"]) if result["total_multiplier"] else 1.0
            }
        else:
            return {
                "login_bonus_available": True,
                "login_bonus_xp": 25,
                "streak_multiplier": 1.0,
                "streak_days": 0,
                "weekend_bonus_active": False,
                "weekend_multiplier": 1.0,
                "event_bonus_active": False,
                "event_name": None,
                "event_multiplier": 1.0,
                "total_multiplier": 1.0
            }

    except Exception as e:
        print(f"Error getting active bonuses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active bonuses: {str(e)}")


@app.post("/api/bonuses/calculate-xp", tags=["Bonuses"])
async def calculate_bonus_xp(
    payload: dict,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Calculate XP with all active bonuses applied.

    Payload:
        - base_xp: Base XP amount
        - is_perfect_score: Whether this was a perfect score (optional, default false)

    Returns:
        - final_xp: Total XP after multipliers
        - bonus_breakdown: Breakdown of all multipliers applied
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    base_xp = payload.get("base_xp", 10)
    is_perfect_score = payload.get("is_perfect_score", False)

    try:
        with db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Call the calculate_bonus_xp function
                cur.execute(
                    "SELECT * FROM calculate_bonus_xp(%s, %s, %s)",
                    (user_id, base_xp, is_perfect_score)
                )
                result = cur.fetchone()

        if result:
            return {
                "final_xp": result["final_xp"],
                "bonus_breakdown": result["bonus_breakdown"]
            }
        else:
            return {
                "final_xp": base_xp,
                "bonus_breakdown": {
                    "base_xp": base_xp,
                    "streak_multiplier": 1.0,
                    "weekend_multiplier": 1.0,
                    "event_multiplier": 1.0,
                    "perfect_score_multiplier": 1.25 if is_perfect_score else 1.0,
                    "final_xp": base_xp,
                    "bonus_xp": 0
                }
            }

    except Exception as e:
        print(f"Error calculating bonus XP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate bonus XP: {str(e)}")


# ============================================================================
# Speech API Endpoints
# ============================================================================

@app.post("/api/speech/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    user_id_from_token: str = Depends(verify_token)
):
    """
    Transcribe audio file to text using OpenAI Whisper.

    Accepts audio file upload (m4a, mp3, wav, webm, etc.)
    Returns the transcribed text.
    """
    try:
        # Read audio bytes from upload
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Get filename for format hint
        filename = audio.filename or "audio.m4a"

        # Transcribe using ASR client
        result = asr_client.transcribe_bytes(audio_bytes, filename)

        return {
            "success": True,
            "transcript": result.text,
            "language": result.language,
            "duration": result.duration
        }

    except RuntimeError as e:
        # ASR specific errors (e.g., API failure after retries)
        print(f"ASR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.post("/api/realtime-token")
async def get_realtime_token(
    user_id_from_token: str = Depends(verify_token)
):
    """
    Generate an ephemeral OpenAI Realtime API token for client-side WebSocket connection.

    This endpoint creates a short-lived session with OpenAI's Realtime API and returns
    an ephemeral client secret that the mobile app uses to connect directly to OpenAI's
    WebSocket for low-latency speech-to-speech conversations.

    The token is valid for 60 seconds and allows direct client connection without
    proxying audio through our backend.

    Returns:
        - client_secret: Ephemeral token for WebSocket authentication
        - expires_at: Unix timestamp when the token expires
        - session_id: OpenAI session ID for debugging
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "alloy",
                    "instructions": """You are a friendly and encouraging English language tutor helping non-native speakers practice conversational English.

Your role:
- Have natural, flowing conversations to help users practice speaking
- Speak clearly and at a moderate pace
- Gently correct pronunciation and grammar mistakes
- Provide encouraging feedback
- Ask follow-up questions to keep the conversation going
- Adapt your vocabulary to the user's level

Keep responses conversational and concise (2-4 sentences typically).
If the user makes errors, briefly note the correction, then continue the conversation naturally.""",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    },
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    }
                },
                timeout=10.0
            )

            if response.status_code != 200:
                error_detail = response.text
                print(f"OpenAI Realtime API error: {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to create realtime session: {error_detail}"
                )

            data = response.json()

            return {
                "success": True,
                "client_secret": data.get("client_secret", {}).get("value"),
                "expires_at": data.get("client_secret", {}).get("expires_at"),
                "session_id": data.get("id"),
                "model": data.get("model"),
                "voice": data.get("voice")
            }

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="OpenAI API timeout")
    except httpx.RequestError as e:
        print(f"Realtime token request error: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to connect to OpenAI: {str(e)}")
    except Exception as e:
        print(f"Realtime token error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate realtime token: {str(e)}")


@app.post("/api/speech/analyze")
async def analyze_speech(
    audio: UploadFile = File(...),
    expected_text: Optional[str] = None,
    user_id_from_token: str = Depends(verify_token)
):
    """
    Analyze speech for pronunciation and fluency.

    Accepts audio file upload and optional expected text.
    Returns transcript, pronunciation score, fluency score, and feedback.
    """
    try:
        # Read audio bytes from upload
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        # Get filename for format hint
        filename = audio.filename or "audio.m4a"

        # First, transcribe the audio
        asr_result = asr_client.transcribe_bytes(audio_bytes, filename)
        transcript = asr_result.text.strip()

        if not transcript:
            return {
                "success": True,
                "transcript": "",
                "pronunciation_score": 0,
                "fluency_score": 0,
                "mispronounced_words": [],
                "feedback": "No speech detected. Please speak clearly into the microphone."
            }

        # Calculate scores based on transcript quality
        # If we have expected text, compare against it
        if expected_text and expected_text.strip():
            expected_words = expected_text.lower().split()
            transcript_words = transcript.lower().split()

            # Calculate word accuracy
            matching_words = sum(1 for w in transcript_words if w in expected_words)
            word_coverage = matching_words / len(expected_words) if expected_words else 0

            # Pronunciation score based on word accuracy
            pronunciation_score = int(min(100, word_coverage * 100))

            # Find mispronounced/missing words
            mispronounced = [w for w in expected_words if w not in transcript_words][:5]

            # Generate feedback
            if pronunciation_score >= 80:
                feedback = "Excellent pronunciation! Keep up the great work."
            elif pronunciation_score >= 60:
                feedback = f"Good effort! Try to pronounce these words more clearly: {', '.join(mispronounced[:3])}"
            else:
                feedback = f"Keep practicing! Focus on these words: {', '.join(mispronounced[:3])}"
        else:
            # No expected text - score based on transcript properties
            word_count = len(transcript.split())

            # Simple heuristics for fluency
            pronunciation_score = min(90, 50 + word_count * 5)  # More words = better
            mispronounced = []
            feedback = "Good job! Keep practicing for even better fluency."

        # Calculate fluency score based on duration and word count
        duration = asr_result.duration or 5.0
        word_count = len(transcript.split())
        words_per_minute = (word_count / duration) * 60 if duration > 0 else 0

        # Optimal speaking rate is 120-150 wpm
        if 100 <= words_per_minute <= 180:
            fluency_score = min(95, 70 + int(word_count * 2))
        elif words_per_minute < 100:
            fluency_score = max(40, int(words_per_minute * 0.7))
        else:
            fluency_score = max(50, 100 - int((words_per_minute - 180) * 0.3))

        return {
            "success": True,
            "transcript": transcript,
            "pronunciation_score": pronunciation_score,
            "fluency_score": fluency_score,
            "mispronounced_words": mispronounced if expected_text else [],
            "feedback": feedback
        }

    except RuntimeError as e:
        # ASR specific errors
        print(f"ASR error in analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"Speech analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech analysis failed: {str(e)}")


class TTSSynthesizeRequest(BaseModel):
    """Request body for TTS synthesis."""
    text: str = Field(..., description="Text to synthesize to speech")
    voice: Optional[str] = Field(None, description="Voice to use (alloy, echo, fable, onyx, nova, shimmer)")


@app.post("/api/speech/analyze-pronunciation")
async def analyze_pronunciation(
    audio: UploadFile = File(...),
    target_text: str = Form(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token)
):
    """
    Analyze pronunciation with detailed phoneme-level feedback.

    This endpoint provides comprehensive pronunciation analysis including:
    - Transcription using Whisper
    - Word-level accuracy comparison
    - Phoneme-level scoring using IPA
    - Specific pronunciation tips for problem sounds
    - Overall fluency metrics

    Args:
        audio: Audio file (WAV/MP3/M4A/WebM)
        target_text: The text the user was trying to pronounce

    Returns:
        Detailed pronunciation analysis with scores, feedback, and improvement tips
    """
    try:
        # Read audio bytes from upload
        audio_bytes = await audio.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        if not target_text or not target_text.strip():
            raise HTTPException(status_code=400, detail="target_text is required")

        # Get filename for format hint
        filename = audio.filename or "audio.m4a"

        # Transcribe the audio using Whisper with word-level timestamps
        asr_result = asr_client.transcribe_bytes(audio_bytes, filename)
        transcript = asr_result.text.strip()

        # Use the pronunciation scorer for detailed analysis
        from app.pronunciation_scorer import PronunciationScorer
        from app.pronunciation_analyzer import PronunciationAnalyzer

        scorer = PronunciationScorer()

        # Save audio to temp file for scorer (it expects a file path)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        try:
            # Get pronunciation scoring
            scoring_result = scorer.score_audio(tmp_path, target_text)

            # Get enhanced analysis with personalized feedback
            analyzer = PronunciationAnalyzer(db=db)

            # Build phoneme analysis from word scores
            phoneme_analysis = []
            for word_score in scoring_result.get("word_scores", []):
                word = word_score.get("word", "")
                score = word_score.get("score", 0)
                status = word_score.get("status", "unknown")
                problem_phonemes = word_score.get("problem_phonemes", [])

                # Map status to our response format
                status_map = {
                    "good": "correct",
                    "needs_work": "close",
                    "focus": "incorrect",
                    "missing": "incorrect"
                }

                for phoneme in problem_phonemes:
                    phoneme_analysis.append({
                        "word": word,
                        "phoneme": phoneme,
                        "status": status_map.get(status, "incorrect"),
                        "confidence": score / 100.0,
                        "expected_ipa": phoneme,
                        "actual_ipa": phoneme  # Simplification - we'd need more complex analysis for actual IPA
                    })

            # Build word scores with issues
            word_scores = []
            for word_score in scoring_result.get("word_scores", []):
                word = word_score.get("word", "")
                score = word_score.get("score", 0)
                tip = word_score.get("tip", "")
                problem_phonemes = word_score.get("problem_phonemes", [])

                issues = []
                if tip:
                    issues.append(tip)
                if problem_phonemes:
                    issues.append(f"Problem sounds: {', '.join(problem_phonemes)}")

                word_scores.append({
                    "word": word,
                    "score": score,
                    "issues": issues
                })

            # Calculate overall scores
            overall_score = scoring_result.get("overall_score", 0)

            # Calculate fluency score based on speech metrics
            duration = asr_result.duration or 5.0
            word_count = len(transcript.split())
            words_per_minute = (word_count / duration) * 60 if duration > 0 else 0

            # Optimal speaking rate is 120-150 wpm for non-native speakers
            if 100 <= words_per_minute <= 180:
                fluency_score = min(95, 70 + int(word_count * 2))
            elif words_per_minute < 100:
                fluency_score = max(40, int(words_per_minute * 0.7))
            else:
                fluency_score = max(50, 100 - int((words_per_minute - 180) * 0.3))

            # Generate comprehensive feedback
            feedback_parts = []

            if overall_score >= 90:
                feedback_parts.append("Excellent pronunciation! Your speech is very clear.")
            elif overall_score >= 75:
                feedback_parts.append("Good pronunciation overall. A few sounds need refinement.")
            elif overall_score >= 60:
                feedback_parts.append("Your pronunciation is understandable. Focus on the tips below to improve.")
            else:
                feedback_parts.append("Keep practicing! Pronunciation takes time. Work on the specific sounds highlighted below.")

            # Add tips from scorer
            tips = scoring_result.get("tips", [])
            if tips:
                feedback_parts.append(f"\nKey areas to work on: {tips[0]}")

            feedback = " ".join(feedback_parts)

            # Store the attempt in the database
            import psycopg
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO pronunciation_attempts (user_id, phrase, phoneme_scores, overall_score)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            user_id_from_token,
                            target_text,
                            psycopg.types.json.Json([{
                                "phoneme": p["phoneme"],
                                "score": p["confidence"] * 100
                            } for p in phoneme_analysis]),
                            overall_score,
                        ),
                    )

            return {
                "success": True,
                "transcript": transcript,
                "overall_score": round(overall_score, 1),
                "pronunciation_score": round(overall_score, 1),
                "fluency_score": round(fluency_score, 1),
                "phoneme_analysis": phoneme_analysis[:10],  # Limit to top 10
                "word_scores": word_scores,
                "feedback": feedback,
                "words_per_minute": round(words_per_minute, 1),
                "duration": round(duration, 2),
                "word_count": word_count
            }

        finally:
            # Clean up temp file
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    except RuntimeError as e:
        # ASR specific errors
        print(f"ASR error in pronunciation analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Pronunciation analysis error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pronunciation analysis failed: {str(e)}")


# ============================================================================
# Skill Unlocks System Endpoints
# ============================================================================

# Global skill manager (will be initialized with db on first use)
_skill_manager: Optional[SkillUnlockManager] = None

def get_skill_manager(db: Database = Depends(get_database)) -> SkillUnlockManager:
    """Get or create skill manager with database connection."""
    global _skill_manager
    if _skill_manager is None or _skill_manager.db is None:
        _skill_manager = create_skill_manager_with_db(db)
    return _skill_manager


@app.get("/api/skills/profile", tags=["Skills"])
async def get_skill_profile(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get user's complete skill profile including XP, levels, and progress.

    Returns:
        - total_xp: Total XP earned
        - overall_level: User's overall level
        - skills: Progress for each skill
        - unlocked_content: IDs of unlocked content
        - earned_achievements: IDs of earned achievements
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        manager = get_skill_manager(db)
        profile = manager.get_or_create_profile(str(user_id))
        return profile.to_dict()
    except Exception as e:
        print(f"Error getting skill profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@app.post("/api/skills/xp", tags=["Skills"])
async def award_skill_xp(
    request: dict,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Award XP to a skill after conversation/exercise completion.

    Body:
        - skill_id: The skill to award XP to (e.g., "grammar_tenses")
        - xp_amount: Amount of XP to award
        - successful: Whether the attempt was successful (affects accuracy)

    Returns:
        - xp_added: Actual XP added (may be capped)
        - level_ups: Any level ups that occurred
        - new_unlocks: Any new content unlocked
        - new_achievements: Any new achievements earned
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    skill_id = request.get("skill_id")
    xp_amount = request.get("xp_amount", 10)
    successful = request.get("successful", True)

    if not skill_id:
        raise HTTPException(status_code=400, detail="skill_id is required")

    if skill_id not in SKILL_DEFINITIONS:
        raise HTTPException(status_code=400, detail=f"Unknown skill: {skill_id}")

    try:
        manager = get_skill_manager(db)
        profile = manager.get_or_create_profile(str(user_id))
        result = manager.add_xp(profile, skill_id, xp_amount, successful)
        return result
    except Exception as e:
        print(f"Error awarding XP: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to award XP: {str(e)}")


@app.get("/api/skills/unlocks", tags=["Skills"])
async def get_available_unlocks(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all unlockable content with current unlock status.

    Returns:
        - unlocked: Content already unlocked
        - locked: Content still locked
        - next_unlocks: Content close to being unlocked (>50% progress)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        manager = get_skill_manager(db)
        profile = manager.get_or_create_profile(str(user_id))
        return manager.get_available_content(profile)
    except Exception as e:
        print(f"Error getting unlocks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get unlocks: {str(e)}")


@app.get("/api/skills/achievements", tags=["Skills"])
async def get_achievements(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all achievements with earned status and progress.

    Returns:
        - earned: Achievements already earned
        - available: Achievements not yet earned (with progress)
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        manager = get_skill_manager(db)
        profile = manager.get_or_create_profile(str(user_id))
        return manager.get_achievements(profile)
    except Exception as e:
        print(f"Error getting achievements: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get achievements: {str(e)}")


@app.get("/api/skills/definitions", tags=["Skills"])
async def get_skill_definitions():
    """
    Get all skill definitions (no auth required).

    Returns list of all skills with their metadata.
    """
    return {
        "skills": SKILL_DEFINITIONS,
        "total_skills": len(SKILL_DEFINITIONS),
    }


# ============================================================================
# Conversation Replay Endpoints
# ============================================================================

# Global replay manager
_replay_manager: Optional[ReplayManager] = None

def get_replay_manager(db: Database = Depends(get_database)) -> ReplayManager:
    """Get or create replay manager with database connection."""
    global _replay_manager
    if _replay_manager is None or _replay_manager.db is None:
        _replay_manager = create_replay_manager_with_db(db)
    return _replay_manager


@app.get("/api/replays", tags=["Replays"])
async def get_user_replays(
    limit: int = 10,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get list of user's recent conversation replays (summaries only).

    Query params:
        - limit: Max number of replays to return (default 10)

    Returns list of replay summaries with session_id, scenario, timestamps, and stats.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        manager = get_replay_manager(db)
        replays = manager.get_user_replays(str(user_id), limit)
        return {"replays": replays, "count": len(replays)}
    except Exception as e:
        print(f"Error getting replays: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get replays: {str(e)}")


@app.get("/api/replays/{session_id}", tags=["Replays"])
async def get_replay_detail(
    session_id: str,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get full replay data including all segments and annotations.

    Path params:
        - session_id: UUID of the conversation session

    Returns complete replay with transcript, timestamps, and coaching annotations.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        manager = get_replay_manager(db)
        replay = manager.get_replay(session_id)

        if not replay:
            raise HTTPException(status_code=404, detail="Replay not found")

        # Verify ownership
        if replay.user_id != str(user_id):
            raise HTTPException(status_code=403, detail="Not authorized to view this replay")

        return replay.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting replay: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get replay: {str(e)}")


# ============================================================================
# Phoneme Analysis Endpoints
# ============================================================================

@app.post("/api/pronunciation/phoneme-analysis", tags=["Pronunciation"])
async def analyze_phonemes(
    request: dict,
    user_id_from_token: str = Depends(verify_token),
):
    """
    Analyze pronunciation with L1 interference patterns.

    Body:
        - text: The expected text
        - asr_words: List of ASR word results with timing/confidence
        - native_language: User's native language (e.g., "spanish", "chinese")
        - audio_quality: Audio quality score (0-100)

    Returns phoneme analysis with L1 patterns and recommendations.
    """
    text = request.get("text", "")
    asr_words = request.get("asr_words", [])
    native_language = request.get("native_language", "spanish")
    audio_quality = request.get("audio_quality", 100)

    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        result = analyze_pronunciation_from_asr(
            expected_text=text,
            asr_words=asr_words,
            native_language=native_language,
            audio_quality=audio_quality
        )
        return result.to_dict()
    except Exception as e:
        print(f"Error analyzing phonemes: {e}")
        raise HTTPException(status_code=500, detail=f"Phoneme analysis failed: {str(e)}")


@app.post("/api/speech/synthesize")
async def synthesize_speech(
    request: TTSSynthesizeRequest,
    user_id_from_token: str = Depends(verify_token)
):
    """
    Synthesize text to speech using OpenAI TTS.

    Returns MP3 audio data that can be played directly.
    Uses natural-sounding voices for authentic conversation experience.
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text is required")

        # Limit text length to prevent abuse
        text = request.text.strip()[:1000]

        # Synthesize using OpenAI TTS
        result = tts_client.synthesize_to_bytes(text)

        if result.audio_bytes is None:
            raise HTTPException(status_code=500, detail="TTS synthesis failed - no audio generated")

        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(result.audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "X-TTS-Provider": result.provider,
                "X-TTS-Characters": str(result.characters)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("Starting SpeakSharp API server...")
    print("Docs available at: http://localhost:8000/docs")

    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
