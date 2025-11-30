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

    Args:
        user_id: User UUID from JWT token
        level: Default CEFR level for new users

    Returns:
        User profile dict
    """
    import uuid
    db = get_db()

    # Convert string to UUID
    user_uuid = uuid.UUID(user_id)

    # Try to get existing user
    user = db.get_user(user_uuid)
    if user:
        return user

    # Create new user with defaults
    user = db.create_user(
        user_id=user_uuid,
        level=level,
        native_language=None,
        goals={},
        interests=[],
    )

    return user
