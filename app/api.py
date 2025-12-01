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

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.db import Database, get_db
from app.tutor_agent import TutorAgent
from app.voice_session import VoiceSession
from app.config import load_config
from app.models import TutorResponse
from app.auth import verify_token, optional_verify_token, get_or_create_user
from app.version import VERSION
from app.pronunciation import router as pronunciation_router


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
    native_language: Optional[str]
    goals: List[str]
    interests: List[str]
    daily_time_goal: Optional[int]
    onboarding_completed: bool
    full_name: Optional[str]
    trial_start_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    subscription_status: Optional[str]
    subscription_tier: Optional[str]
    created_at: datetime
    updated_at: datetime


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    user_id: Optional[uuid.UUID] = None
    level: str = "A1"
    native_language: Optional[str] = None
    goals: Optional[Dict[str, Any]] = None
    interests: Optional[List[str]] = None


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    level: Optional[str] = None
    native_language: Optional[str] = None
    goals: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    daily_time_goal: Optional[int] = None
    full_name: Optional[str] = None
    country: Optional[str] = None
    onboarding_completed: Optional[bool] = None
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_status: Optional[str] = None
    subscription_tier: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    database: str
    timestamp: datetime
    version: str


# Application lifecycle


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting SpeakSharp API...")
    db = get_db()
    if db.health_check():
        print("✓ Database connection successful")

        # Run migrations
        print("🔧 Running database migrations...")
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Migration: Add all onboarding and subscription columns
                    cur.execute("""
                        ALTER TABLE user_profiles
                        ADD COLUMN IF NOT EXISTS daily_time_goal INTEGER,
                        ADD COLUMN IF NOT EXISTS trial_start_date TIMESTAMPTZ,
                        ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMPTZ,
                        ADD COLUMN IF NOT EXISTS subscription_status TEXT,
                        ADD COLUMN IF NOT EXISTS subscription_tier TEXT
                    """)
                    conn.commit()
            print("✓ Migrations completed successfully")
        except Exception as e:
            print(f"⚠️  Migration warning: {e}")
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

# Register routers
app.include_router(pronunciation_router, prefix="/api", tags=["Pronunciation"])


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
        timestamp=datetime.now(),
        version=VERSION
    )


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


@app.get("/api/users/me", tags=["Users"])
async def get_current_user(
    request: Request,
    db: Database = Depends(get_database),
):
    """
    Get current user's profile from JWT token.

    Requires JWT authentication. User ID is extracted from the token.
    User profile is auto-created on first request if it doesn't exist.

    Returns:
        User profile
    """
    # Manually extract authorization header from request
    authorization = request.headers.get("authorization")
    print(f"DEBUG: get_current_user called with authorization={authorization[:50] if authorization else 'None'}")

    # Verify token and get user ID
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Extract token from "Bearer {token}" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = parts[1]

    # Decode token to get user ID (using same logic as verify_token)
    import jwt
    from app.auth import SUPABASE_JWT_SECRET

    try:
        if not SUPABASE_JWT_SECRET:
            # Development mode: decode without verification
            payload = jwt.decode(token, options={"verify_signature": False})
        else:
            # Production: verify signature
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )

        user_id_from_token = payload.get("sub")
        if not user_id_from_token:
            raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

        print(f"DEBUG: Got user_id from token: {user_id_from_token}")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    # Convert to UUID
    try:
        user_id = uuid.UUID(user_id_from_token)
        print(f"DEBUG: Converted to UUID: {user_id}")
    except Exception as e:
        print(f"DEBUG: UUID conversion failed: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid user_id from token: {str(e)}")

    # Auto-create user profile if doesn't exist
    try:
        print(f"DEBUG: Calling get_or_create_user with {str(user_id)}")
        user = get_or_create_user(str(user_id))
        print(f"DEBUG: Got user data: {user}")
        return user  # Return raw dict for now
    except Exception as e:
        import traceback
        print(f"DEBUG: Exception in get_or_create_user:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get/create user: {str(e)}")


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
            native_language=request.native_language,
            goals=request.goals,
            interests=request.interests,
            daily_time_goal=request.daily_time_goal,
            full_name=request.full_name,
            country=request.country,
            onboarding_completed=request.onboarding_completed,
            trial_start_date=request.trial_start_date,
            trial_end_date=request.trial_end_date,
            subscription_status=request.subscription_status,
            subscription_tier=request.subscription_tier
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


# Tutor Endpoints


from fastapi import Body

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

        # Get user level for tutor mode (beginner vs advanced)
        user_level = user.get('level', 'A1')

        # Run tutor
        tutor = TutorAgent()
        tutor_response: TutorResponse = tutor.process_user_input(
            text,
            context={
                "source": "api",
                "mode": "text",
                "scenario_id": scenario_id,
                "session_id": str(session_id),
                "user_id": str(user_id),
                "level": user_level,
                "raw_context": context_str,
            },
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

@app.post("/api/demo/grammar", tags=["Demo"])
async def demo_grammar(payload: dict = Body(...)):
    """
    Public demo endpoint for grammar checking.

    Does NOT require authentication. Used for landing page interactive demo.
    Does NOT log errors or create SRS cards.

    Returns grammar corrections for the provided text.
    """
    try:
        # Extract text from payload
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise HTTPException(status_code=400, detail="Invalid or missing text")

        # Run tutor agent with beginner level (A1) for demo
        tutor = TutorAgent()
        tutor_response: TutorResponse = tutor.process_user_input(
            text,
            context={
                "source": "demo",
                "mode": "text",
                "level": "A1",
            },
        )

        # Return only the corrected text and explanation
        # Format matches the demo's expected structure
        if tutor_response.errors:
            first_error = tutor_response.errors[0]
            return {
                "corrected": first_error.corrected_sentence,
                "explanation": first_error.explanation,
            }
        else:
            return {
                "corrected": text,
                "explanation": "Great! No errors found.",
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo grammar error: {e}")


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

        # Read TTS audio file and encode as base64
        import base64
        audio_base64 = None
        if result.tts_output_path:
            try:
                with open(result.tts_output_path, 'rb') as audio_file:
                    audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
            except Exception as e:
                print(f"Warning: Failed to read TTS audio: {e}")

        # Return response
        return {
            "transcript": result.recognized_text,
            "tutor_response": {
                "message": result.tutor_response.message,
                "errors": [e.model_dump() for e in result.tutor_response.errors],
                "micro_task": result.tutor_response.micro_task,
            },
            "audio_base64": audio_base64,
            "session_id": str(session_id),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice tutor error: {str(e)}")


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
            # Return zeros if no data found
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


# ============================================================================
# Achievements Endpoints
# ============================================================================

@app.get("/api/achievements", tags=["Achievements"])
async def get_all_achievements(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all available achievements.

    Returns list of all achievements with their details.
    """
    try:
        achievements = db.get_achievements()
        return {"achievements": achievements, "count": len(achievements)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get achievements: {str(e)}"
        )


@app.get("/api/achievements/mine", tags=["Achievements"])
async def get_my_achievements(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get current user's unlocked achievements.

    Returns list of achievements the user has unlocked.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        achievements = db.get_user_achievements(user_id)
        return {"achievements": achievements, "count": len(achievements)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user achievements: {str(e)}"
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

    Returns the daily goal with targets and actual progress.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        goal = db.get_daily_goal(user_id)

        if not goal:
            # Create default goal if doesn't exist
            goal = db.create_or_update_daily_goal(
                user_id,
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
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Update today's daily goal targets.

    Payload can include: target_study_minutes, target_lessons, target_reviews, target_drills
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        goal = db.create_or_update_daily_goal(
            user_id,
            target_study_minutes=payload.get("target_study_minutes"),
            target_lessons=payload.get("target_lessons"),
            target_reviews=payload.get("target_reviews"),
            target_drills=payload.get("target_drills")
        )

        return goal
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update daily goal: {str(e)}"
        )


# ============================================================================
# Referrals Endpoints
# ============================================================================

@app.get("/api/referrals/my-code", tags=["Referrals"])
async def get_my_referral_code(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get the authenticated user's referral code.

    Creates a code if the user doesn't have one yet.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        code_data = db.get_or_create_referral_code(user_id)
        return code_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get referral code: {str(e)}"
        )


@app.get("/api/referrals/stats", tags=["Referrals"])
async def get_referral_stats(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get the authenticated user's referral statistics.

    Returns referral code, total signups, and conversions.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        stats = db.get_referral_stats(user_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get referral stats: {str(e)}"
        )


@app.post("/api/referrals/claim", tags=["Referrals"])
async def claim_referral(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Claim a referral code for the current user.

    Payload: { "referral_code": "ABC12345" }
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    referral_code = payload.get("referral_code")
    if not referral_code:
        raise HTTPException(status_code=400, detail="Missing referral_code")

    try:
        success = db.claim_referral_code(user_id, referral_code)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Invalid referral code or already claimed"
            )

        return {"status": "success", "message": "Referral code claimed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to claim referral: {str(e)}"
        )


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
    user_id_from_token: Optional[str] = Depends(optional_verify_token),
):
    """
    Submit placement test answers and get results.

    Payload:
    {
        "answers": [0, 2, 1, 3, 0, ...]  // List of selected option indices
    }

    Returns level determination and feedback.

    Auth is optional - if authenticated, saves level to user profile.
    If not authenticated (during onboarding), just returns results.
    """
    from app.placement_test import placement_evaluator

    answers = payload.get("answers", [])

    if not answers or not isinstance(answers, list):
        raise HTTPException(status_code=400, detail="Invalid answers format")

    # Evaluate the test
    result = placement_evaluator.evaluate_test(answers)

    # Update user's level in database if authenticated
    if user_id_from_token:
        try:
            user_id = uuid.UUID(user_id_from_token)
            # Update user profile with determined level
            db.update_user_profile(
                user_id=user_id,
                level=result.level
            )
        except Exception as e:
            # Don't fail the request if DB update fails
            print(f"Warning: Failed to update user profile: {e}")

    return {
        "level": result.level,
        "score": result.score,
        "total_questions": len(answers),
        "strengths": result.strengths,
        "weaknesses": result.weaknesses,
        "recommendation": result.recommendation,
    }


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
