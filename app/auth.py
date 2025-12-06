"""
Authentication and authorization for SpeakSharp API.

Provides JWT verification and user extraction from Supabase tokens.
"""

import os
import jwt
from typing import Optional
from fastapi import HTTPException, Header
from app.db import get_db


# Supabase JWT secret (from Supabase dashboard -> Settings -> API -> JWT Secret)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def verify_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify JWT token and extract user ID.

    Args:
        authorization: Authorization header with format "Bearer {token}"

    Returns:
        User ID (UUID as string) from the token's 'sub' claim

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    print(f"DEBUG verify_token called: authorization={'None' if authorization is None else authorization[:50]}")

    if not authorization:
        print("DEBUG verify_token: No authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Extract token from "Bearer {token}" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = parts[1]

    if not SUPABASE_JWT_SECRET:
        # In development, skip verification if JWT secret not configured
        # Extract user ID from token without verification (UNSAFE - dev only)
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
            return user_id
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    # Production: Verify token signature
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase tokens don't always have aud
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def optional_verify_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Optionally verify JWT token and extract user ID.

    Returns None if no authorization header is provided (instead of raising error).
    Useful for endpoints that can work with or without authentication.

    Args:
        authorization: Authorization header with format "Bearer {token}"

    Returns:
        User ID (UUID as string) from the token's 'sub' claim, or None if not authenticated

    Raises:
        HTTPException: If token is provided but invalid or expired
    """
    if not authorization:
        return None

    # If token is provided, verify it (reuse logic from verify_token)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = parts[1]

    if not SUPABASE_JWT_SECRET:
        # In development, skip verification if JWT secret not configured
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
            return user_id
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    # Production: Verify token signature
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_or_create_user(user_id: str, level: str = "A1") -> dict:
    """
    Get user profile or create if doesn't exist.

    This enables seamless onboarding - users are auto-created on first API call.
    New users automatically get a 14-day free trial.

    Args:
        user_id: User UUID from JWT token
        level: Default CEFR level for new users

    Returns:
        User profile dict
    """
    import uuid
    from datetime import datetime, timedelta
    db = get_db()

    # Convert string to UUID
    user_uuid = uuid.UUID(user_id)

    # Try to get existing user
    user = db.get_user(user_uuid)
    if user:
        return user

    # Create new user with defaults and 14-day trial
    trial_start = datetime.now()
    trial_end = trial_start + timedelta(days=14)

    user = db.create_user(
        user_id=user_uuid,
        level=level,
        native_language=None,
        goals={},
        interests=[],
    )

    # Set trial dates for new user
    db.update_user_profile(
        user_id=user_uuid,
        trial_start_date=trial_start,
        trial_end_date=trial_end,
    )

    # Fetch updated user profile
    user = db.get_user(user_uuid)

    return user


def add_user_xp(user_id: str, amount: int) -> int:
    """
    Add XP to a user's total and return new total.

    Args:
        user_id: User UUID from JWT token
        amount: Amount of XP to add

    Returns:
        New total XP
    """
    import uuid
    db = get_db()
    user_uuid = uuid.UUID(user_id)

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE user_profiles
                SET total_xp = COALESCE(total_xp, 0) + %s,
                    updated_at = NOW()
                WHERE user_id = %s
                RETURNING total_xp
            """, (amount, user_uuid))
            result = cur.fetchone()
            conn.commit()
            return result['total_xp'] if result else 0


def get_user_xp(user_id: str) -> int:
    """
    Get user's total XP.

    Args:
        user_id: User UUID from JWT token

    Returns:
        Total XP
    """
    import uuid
    db = get_db()
    user_uuid = uuid.UUID(user_id)

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(total_xp, 0) as total_xp
                FROM user_profiles
                WHERE user_id = %s
            """, (user_uuid,))
            result = cur.fetchone()
            return result['total_xp'] if result else 0
