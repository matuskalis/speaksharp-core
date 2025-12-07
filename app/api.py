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
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import base64

from app.db import Database, get_db
from app.tutor_agent import TutorAgent
from app.voice_session import VoiceSession
from app.config import load_config
from app.models import TutorResponse
from app.auth import verify_token, optional_verify_token, get_or_create_user
from app.version import VERSION
from app.payments import StripePaymentService
# from app.pronunciation import router as pronunciation_router  # Temporarily disabled

import stripe
import os


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


# Payment Models

class CreateCheckoutSessionRequest(BaseModel):
    """Request model for creating Stripe checkout session."""
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Response model for checkout session."""
    session_id: str
    checkout_url: str


class PortalSessionRequest(BaseModel):
    """Request model for creating customer portal session."""
    return_url: str


class PortalSessionResponse(BaseModel):
    """Response model for portal session."""
    portal_url: str


class SubscriptionStatusResponse(BaseModel):
    """Response model for subscription status."""
    status: str
    tier: str
    message: Optional[str] = None
    subscription_id: Optional[str] = None
    billing_cycle: Optional[str] = None
    price_cents: Optional[int] = None
    currency: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancelled_at: Optional[str] = None
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    will_renew: Optional[bool] = None


class CancelSubscriptionRequest(BaseModel):
    """Request model for cancelling subscription."""
    reason: Optional[str] = None


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
# app.include_router(pronunciation_router, prefix="/api", tags=["Pronunciation"])  # Temporarily disabled


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
        raise HTTPException(status_code=400, detail="Invalid question_id")

    # Process the answer
    state = adaptive_placement_test.process_answer(state, question, answer)

    # Check if answer was correct (for frontend feedback)
    is_correct = answer == question.correct_answer

    # Update stored state
    _adaptive_test_sessions[session_id] = state.model_dump()

    if state.is_complete:
        # Test is complete - return final results
        result = adaptive_placement_test.evaluate_test(state)

        # Update user's level in database if authenticated
        if user_id_from_token:
            try:
                user_id = uuid.UUID(user_id_from_token)
                db.update_user_profile(
                    user_id=user_id,
                    level=result.level
                )
            except Exception as e:
                print(f"Warning: Failed to update user profile: {e}")

        # Clean up session
        del _adaptive_test_sessions[session_id]

        return {
            "is_complete": True,
            "answer_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "result": {
                "level": result.level,
                "score": result.score,
                "total_questions": result.total_questions,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "recommendation": result.recommendation,
            }
        }
    else:
        # Get next question
        next_question = adaptive_placement_test.get_next_question(state)

        if not next_question:
            # Edge case: no more questions but test not marked complete
            state.is_complete = True
            result = adaptive_placement_test.evaluate_test(state)

            if user_id_from_token:
                try:
                    user_id = uuid.UUID(user_id_from_token)
                    db.update_user_profile(user_id=user_id, level=result.level)
                except Exception:
                    pass

            del _adaptive_test_sessions[session_id]

            return {
                "is_complete": True,
                "answer_correct": is_correct,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "result": {
                    "level": result.level,
                    "score": result.score,
                    "total_questions": result.total_questions,
                    "strengths": result.strengths,
                    "weaknesses": result.weaknesses,
                    "recommendation": result.recommendation,
                }
            }

        return {
            "is_complete": False,
            "answer_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "current_level": state.current_level,
            "question_number": len(state.answers) + 1,
            "question": {
                "question_id": next_question.question_id,
                "question_text": next_question.question_text,
                "options": next_question.options,
                "level": next_question.level,
                "skill_type": next_question.skill_type,
            }
        }


# ============================================================================
# Learning Dashboard Endpoint
# ============================================================================

@app.get("/api/learning/dashboard", tags=["Learning"])
async def get_learning_dashboard(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get adaptive learning dashboard with personalized recommendations.

    Returns:
    - todayFocus: 3 prioritized tasks based on weak skills
    - skillScores: grammar/vocabulary/fluency/pronunciation scores (0-100)
    - progressPath: Current CEFR level, progress %, and ETA to next level
    - recentGrowth: 7-day activity heatmap
    - minutesStudiedToday: Today's study time
    - currentStreak: Current streak count
    - dailyGoal: Daily time goal in minutes
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        # Get user profile
        profile = db.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        # Get skill weaknesses
        weak_skills_data = db.get_weakest_skills(user_id, limit=3)
        weak_skills = [skill["skill_category"] for skill in weak_skills_data]

        # Calculate skill scores (0-100) based on mastery
        skill_scores = {
            "grammar": 75,
            "vocabulary": 68,
            "fluency": 82,
            "pronunciation": 71,
        }

        # Adjust scores based on actual weak skills data
        for skill_data in weak_skills_data:
            skill_cat = skill_data["skill_category"].lower()
            if skill_cat in skill_scores:
                # Lower score for weaker skills
                skill_scores[skill_cat] = int(skill_data["mastery_score"])

        # Generate 3 prioritized tasks based on weak skills
        today_focus = []
        task_templates = {
            "grammar": {
                "type": "lesson",
                "title": "Grammar Practice: Present Perfect",
                "duration": 10,
                "skill": "Grammar",
                "href": "/lessons"
            },
            "vocabulary": {
                "type": "drill",
                "title": "Vocabulary Building: Common Phrases",
                "duration": 8,
                "skill": "Vocabulary",
                "href": "/drills"
            },
            "fluency": {
                "type": "scenario",
                "title": "Conversation: At a Restaurant",
                "duration": 15,
                "skill": "Fluency",
                "href": "/scenarios"
            },
            "pronunciation": {
                "type": "drill",
                "title": "Pronunciation: Difficult Sounds",
                "duration": 12,
                "skill": "Pronunciation",
                "href": "/pronunciation"
            }
        }

        # Prioritize tasks based on weakest skills
        task_counter = 0
        for weak_skill in weak_skills:
            skill_key = weak_skill.lower()
            if skill_key in task_templates and task_counter < 3:
                task = task_templates[skill_key].copy()
                task["id"] = f"task-{task_counter + 1}"
                today_focus.append(task)
                task_counter += 1

        # Fill remaining slots with varied tasks
        if len(today_focus) < 3:
            default_tasks = [
                {
                    "id": "task-default-1",
                    "type": "scenario",
                    "title": "Daily Conversation Practice",
                    "duration": 10,
                    "skill": "Speaking",
                    "href": "/scenarios"
                },
                {
                    "id": "task-default-2",
                    "type": "lesson",
                    "title": "Review Lesson: Basic Tenses",
                    "duration": 8,
                    "skill": "Grammar",
                    "href": "/lessons"
                },
            ]
            for task in default_tasks:
                if len(today_focus) < 3:
                    today_focus.append(task)

        # Calculate CEFR progress
        cefr_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        current_level = profile["level"]
        current_index = cefr_levels.index(current_level) if current_level in cefr_levels else 0
        next_level = cefr_levels[current_index + 1] if current_index < len(cefr_levels) - 1 else current_level

        # Estimate progress (simplified - would use actual activity data)
        progress = 45  # 45% progress to next level
        days_to_next = 30  # Estimated days to next level

        # Get streak data
        streak_data = db.get_user_streak(user_id)
        current_streak = streak_data.get("current_streak", 0) if streak_data else 0

        # Get recent activity (last 7 days)
        from datetime import timedelta
        today = datetime.now().date()
        recent_growth = []

        for i in range(7):
            date = today - timedelta(days=6-i)
            # Simplified - would fetch actual session data
            minutes = 0
            if i >= 3:  # Some activity in last 4 days
                minutes = 15 if i % 2 == 0 else 20

            recent_growth.append({
                "date": date.isoformat(),
                "minutes": minutes
            })

        # Get today's goal
        daily_goal_data = db.get_daily_goal(user_id)
        daily_goal = profile.get("daily_time_goal", 30)
        minutes_today = 0  # Would fetch from actual session tracking

        if daily_goal_data:
            daily_goal = daily_goal_data.get("target_study_minutes", 30)
            minutes_today = daily_goal_data.get("actual_study_minutes", 0)

        return {
            "todayFocus": today_focus,
            "skillScores": skill_scores,
            "progressPath": {
                "current": current_level,
                "next": next_level,
                "progress": progress,
                "daysToNext": days_to_next
            },
            "recentGrowth": recent_growth,
            "minutesStudiedToday": minutes_today,
            "currentStreak": current_streak,
            "dailyGoal": daily_goal
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load learning dashboard: {str(e)}"
        )


# ============================================================================
# Content Library Endpoints (Database-backed)
# ============================================================================

@app.get("/api/content", tags=["Content"])
async def get_all_content(
    content_type: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 50,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get content from the content library.

    Query params:
    - content_type: Filter by type (lesson, scenario, monologue, journal, pronunciation_phrase)
    - level: Filter by CEFR level (A1, A2, B1, B2, C1, C2)
    - limit: Max results (default 50)

    Returns content items from the database.
    """
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Build query
                query = """
                    SELECT
                        content_id, content_type, title,
                        level_min, level_max, skill_targets,
                        content_data, metadata, created_at
                    FROM content_library
                    WHERE 1=1
                """
                params = []

                if content_type:
                    query += " AND content_type = %s"
                    params.append(content_type)

                if level:
                    query += " AND (level_min <= %s AND level_max >= %s)"
                    params.extend([level, level])

                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                content_items = [
                    {
                        "content_id": str(row['content_id']),
                        "content_type": row['content_type'],
                        "title": row['title'],
                        "level_min": row['level_min'],
                        "level_max": row['level_max'],
                        "skill_targets": row['skill_targets'],
                        "content_data": row['content_data'],
                        "metadata": row['metadata'],
                        "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    }
                    for row in rows
                ]

                return {
                    "content": content_items,
                    "count": len(content_items),
                    "filters": {
                        "content_type": content_type,
                        "level": level
                    }
                }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get content: {str(e)}"
        )


@app.get("/api/content/{content_id}", tags=["Content"])
async def get_content_by_id(
    content_id: uuid.UUID,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get a specific content item by ID.
    """
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        content_id, content_type, title,
                        level_min, level_max, skill_targets,
                        content_data, audio_url, metadata, created_at
                    FROM content_library
                    WHERE content_id = %s
                """, (str(content_id),))

                row = cursor.fetchone()

                if not row:
                    raise HTTPException(status_code=404, detail="Content not found")

                return {
                    "content_id": str(row['content_id']),
                    "content_type": row['content_type'],
                    "title": row['title'],
                    "level_min": row['level_min'],
                    "level_max": row['level_max'],
                    "skill_targets": row['skill_targets'],
                    "content_data": row['content_data'],
                    "audio_url": row['audio_url'],
                    "metadata": row['metadata'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get content: {str(e)}"
        )


@app.get("/api/content/type/{content_type}", tags=["Content"])
async def get_content_by_type(
    content_type: str,
    level: Optional[str] = None,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get all content of a specific type.

    Valid types: lesson, scenario, monologue, journal, pronunciation_phrase
    """
    valid_types = ["lesson", "scenario", "monologue", "journal", "pronunciation_phrase"]
    if content_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content_type. Must be one of: {valid_types}"
        )

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT
                        content_id, content_type, title,
                        level_min, level_max, skill_targets,
                        content_data, metadata, created_at
                    FROM content_library
                    WHERE content_type = %s
                """
                params = [content_type]

                if level:
                    query += " AND (level_min <= %s AND level_max >= %s)"
                    params.extend([level, level])

                query += " ORDER BY title ASC"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                content_items = [
                    {
                        "content_id": str(row['content_id']),
                        "content_type": row['content_type'],
                        "title": row['title'],
                        "level_min": row['level_min'],
                        "level_max": row['level_max'],
                        "skill_targets": row['skill_targets'],
                        "content_data": row['content_data'],
                        "metadata": row['metadata'],
                    }
                    for row in rows
                ]

                return {
                    "content": content_items,
                    "count": len(content_items),
                    "content_type": content_type
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get content: {str(e)}"
        )


@app.get("/api/content/summary", tags=["Content"])
async def get_content_summary(
    db: Database = Depends(get_database),
):
    """
    Get a summary of available content (public endpoint).

    Returns counts by content type and level.
    """
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Count by type
                cursor.execute("""
                    SELECT content_type, COUNT(*) as count
                    FROM content_library
                    GROUP BY content_type
                    ORDER BY content_type
                """)
                type_counts = {row['content_type']: row['count'] for row in cursor.fetchall()}

                # Count by level
                cursor.execute("""
                    SELECT level_min, COUNT(*) as count
                    FROM content_library
                    GROUP BY level_min
                    ORDER BY level_min
                """)
                level_counts = {row['level_min']: row['count'] for row in cursor.fetchall()}

                # Total count
                cursor.execute("SELECT COUNT(*) as total FROM content_library")
                total = cursor.fetchone()['total']

                return {
                    "total_content": total,
                    "by_type": type_counts,
                    "by_level": level_counts
                }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get content summary: {str(e)}"
        )


# Temporary admin endpoint for testing
@app.post("/api/admin/complete-onboarding", tags=["Admin"])
async def complete_onboarding(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Temporary endpoint to mark onboarding as complete for testing dashboard.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    try:
        query = """
            UPDATE user_profile
            SET onboarding_completed = true
            WHERE user_id = $1
            RETURNING onboarding_completed
        """
        result = await db.pool.fetchrow(query, user_id)

        if not result:
            raise HTTPException(status_code=404, detail="User profile not found")

        return {
            "success": True,
            "message": f"Onboarding marked complete for user {user_id}",
            "onboarding_completed": result["onboarding_completed"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update onboarding status: {str(e)}"
        )


# ========================================
# Payment Endpoints (Stripe Integration)
# ========================================

@app.post("/api/payments/create-checkout-session", response_model=CheckoutSessionResponse, tags=["Payments"])
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Create a Stripe checkout session for subscription purchase.

    Requires authentication. Returns a checkout URL to redirect the user to Stripe.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    payment_service = StripePaymentService(db)
    result = await payment_service.create_checkout_session(
        user_id=user_id,
        price_id=request.price_id,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )

    return CheckoutSessionResponse(**result)


@app.post("/api/payments/webhook", tags=["Payments"])
async def stripe_webhook(
    request: Request,
    db: Database = Depends(get_database),
):
    """
    Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe for subscription lifecycle events.
    No authentication required (verified via Stripe signature).
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")

    # Handle the event
    payment_service = StripePaymentService(db)
    result = await payment_service.handle_webhook_event(event)

    return result


@app.get("/api/payments/subscription", response_model=SubscriptionStatusResponse, tags=["Payments"])
async def get_subscription_status(
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Get the current user's subscription status.

    Returns subscription details including tier, status, billing info, and dates.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    payment_service = StripePaymentService(db)
    result = await payment_service.get_subscription_status(user_id)

    return SubscriptionStatusResponse(**result)


@app.post("/api/payments/cancel", tags=["Payments"])
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Cancel the current user's subscription.

    The subscription will remain active until the end of the current billing period.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    payment_service = StripePaymentService(db)
    result = await payment_service.cancel_subscription(user_id, request.reason)

    return result


@app.post("/api/payments/create-portal-session", response_model=PortalSessionResponse, tags=["Payments"])
async def create_portal_session(
    request: PortalSessionRequest,
    db: Database = Depends(get_database),
    user_id_from_token: str = Depends(verify_token),
):
    """
    Create a Stripe customer portal session.

    Returns a URL to redirect the user to Stripe's customer portal where they can
    manage their subscription, update payment methods, view invoices, etc.
    """
    try:
        user_id = uuid.UUID(user_id_from_token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id from token")

    payment_service = StripePaymentService(db)
    result = await payment_service.create_portal_session(user_id, request.return_url)

    return PortalSessionResponse(**result)


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
