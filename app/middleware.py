"""
Middleware for automatic tracking and analytics.
Silently collects session data without impacting user experience.
"""

import uuid
from datetime import datetime
from fastapi import Request
from user_agents import parse
import httpx

from app.db import get_db


async def track_session_middleware(request: Request, call_next):
    """
    Middleware to automatically track user sessions with device/browser info.
    Runs silently in the background - user never sees this.
    """
    response = await call_next(request)

    # Only track API calls (not health checks or root)
    if request.url.path.startswith("/api/"):
        # Extract user_id from authorization if present
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header:
            # Parse JWT to get user_id (implement based on your auth)
            # For now, we'll skip if we can't get it
            pass

        # Get device/browser info from User-Agent
        user_agent_string = request.headers.get("user-agent", "")
        user_agent = parse(user_agent_string)

        # Extract device info
        device_type = "desktop"
        if user_agent.is_mobile:
            device_type = "mobile"
        elif user_agent.is_tablet:
            device_type = "tablet"

        os = f"{user_agent.os.family} {user_agent.os.version_string}"
        browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"

        # Get IP address
        ip_address = request.client.host if request.client else None

        # Get geolocation from IP (async, don't block response)
        # We'll do this in background - not blocking the request
        try:
            # Store session analytics
            db = get_db()
            if user_id and db:
                # This would insert into session_analytics table
                # For now, just log it
                print(f"[Analytics] User: {user_id}, Device: {device_type}, OS: {os}, Browser: {browser}")
        except Exception as e:
            # Never let tracking break the actual request
            print(f"[Analytics] Error: {e}")

    return response


def get_client_ip(request: Request) -> str:
    """Extract client IP from request headers."""
    # Check common proxy headers
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


async def get_geo_from_ip(ip: str) -> dict:
    """
    Get country/city from IP address using ipapi.co (free, no auth required).
    Returns dict with country_code and city.
    """
    if ip in ["127.0.0.1", "localhost", "unknown"]:
        return {"country_code": "LOCAL", "city": "Local"}

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"https://ipapi.co/{ip}/json/")
            if response.status_code == 200:
                data = response.json()
                return {
                    "country_code": data.get("country_code", "unknown"),
                    "city": data.get("city", "unknown"),
                    "country": data.get("country_name", "unknown")
                }
    except Exception:
        pass

    return {"country_code": "unknown", "city": "unknown"}


def track_feature_usage(user_id: uuid.UUID, feature_name: str, action: str, metadata: dict = None):
    """
    Silent background function to track which features users actually use.
    Called automatically throughout the app.

    Examples:
    - track_feature_usage(user_id, "text_tutor", "submitted", {"word_count": 50})
    - track_feature_usage(user_id, "voice_tutor", "completed", {"duration": 30})
    - track_feature_usage(user_id, "srs_review", "card_reviewed", {"quality": 4})
    """
    try:
        db = get_db()
        if db:
            # Insert into feature_usage table
            # This runs async, doesn't block the user
            print(f"[FeatureUsage] User {user_id}: {feature_name} - {action}")
    except Exception as e:
        print(f"[FeatureUsage] Error: {e}")
