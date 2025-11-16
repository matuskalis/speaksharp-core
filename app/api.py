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

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.db import Database, get_db
from app.tutor_agent import TutorAgent
from app.voice_session import VoiceSession
from app.config import load_config
from app.models import TutorResponse


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
    goals: Dict[str, Any]
    interests: List[str]
    created_at: datetime
    updated_at: datetime


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    user_id: Optional[uuid.UUID] = None
    level: str = "A1"
    native_language: Optional[str] = None
    goals: Optional[Dict[str, Any]] = None
    interests: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    database: str
    timestamp: datetime


# Application lifecycle


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting SpeakSharp API...")
    db = get_db()
    if db.health_check():
        print("✓ Database connection successful")
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


# Tutor Endpoints


from fastapi import Body

@app.post("/api/tutor/text", tags=["Tutor"])
async def tutor_text(
    payload: dict = Body(...),
    db: Database = Depends(get_database),
):
    """
    Process text input through the tutor agent.

    This version parses the JSON payload manually to avoid request-model
    validation issues while we debug.
    """
    try:
        # Extract fields from raw JSON
        try:
            user_id = uuid.UUID(str(payload.get("user_id")))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or missing user_id")

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

@app.post("/api/tutor/voice", response_model=TutorVoiceResponse, tags=["Tutor"])
async def tutor_voice(
    request: TutorVoiceRequest,
    db: Database = Depends(get_database)
):
    """
    Process voice input through the voice session.

    This endpoint:
    1. Validates user existence
    2. Processes audio through VoiceSession (ASR + Tutor + TTS)
    3. Logs transcript and errors
    4. Returns transcript, response, and audio URL

    Args:
        request: Voice tutoring request

    Returns:
        Voice response with transcript and audio
    """
    # Verify user exists
    user = db.get_user(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create or get session
    session_id = request.session_id
    if not session_id:
        session = db.create_session(
            user_id=request.user_id,
            session_type="voice_tutor"
        )
        session_id = session['session_id']

    try:
        # Load config and create voice session
        config = load_config()
        voice_session = VoiceSession(
            user_level=user['level'],
            config=config
        )

        # Process voice input
        # Note: For now, we simulate with a placeholder
        # In production, you'd handle actual audio file upload/streaming
        if request.audio_path:
            result = voice_session.process_voice_turn(
                audio_path=request.audio_path,
                context=""
            )
        else:
            # Placeholder for future audio_bytes handling
            raise HTTPException(
                status_code=400,
                detail="audio_path is required (audio_bytes not yet implemented)"
            )

        # Log transcript and errors
        transcript = result.get("transcript", "")

        for error in result.get("errors", []):
            try:
                db.log_error(
                    user_id=request.user_id,
                    error_type=error.get("type", "unknown"),
                    user_sentence=error.get("user_sentence", transcript),
                    corrected_sentence=error.get("corrected_sentence", ""),
                    explanation=error.get("explanation"),
                    session_id=session_id,
                    source_type="voice_tutor"
                )
            except Exception as e:
                print(f"Warning: Failed to log error to database: {e}")

        return TutorVoiceResponse(
            transcript=transcript,
            message=result.get("message", ""),
            errors=result.get("errors", []),
            audio_url=result.get("audio_path"),
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process voice: {str(e)}"
        )


# SRS Endpoints


@app.get("/api/srs/due/{user_id}", response_model=SRSDueResponse, tags=["SRS"])
async def get_due_cards(
    user_id: uuid.UUID,
    limit: int = 20,
    db: Database = Depends(get_database)
):
    """
    Get due SRS cards for review.

    Args:
        user_id: User UUID
        limit: Maximum number of cards to return

    Returns:
        List of due cards
    """
    # Verify user exists
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
    db: Database = Depends(get_database)
):
    """
    Submit a review for an SRS card.

    This updates the card using the SM-2 algorithm and logs the review.

    Args:
        request: SRS review request

    Returns:
        Success confirmation
    """
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


@app.get("/api/skills/weakest/{user_id}", tags=["Skills"])
async def get_weakest_skills(
    user_id: uuid.UUID,
    limit: int = 5,
    db: Database = Depends(get_database)
):
    """
    Get user's weakest skills.

    Args:
        user_id: User UUID
        limit: Maximum number of skills to return

    Returns:
        List of weakest skills
    """
    # Verify user exists
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
