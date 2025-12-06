import os
import uuid
import random
from typing import Any, Dict, List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query
from starlette import status
import psycopg

from app.db import Database, get_db
from app.auth import verify_token
from app.pronunciation_scorer import PronunciationScorer
from app.pronunciation_analyzer import PronunciationAnalyzer
from app.data.practice_phrases import PRACTICE_PHRASES

router = APIRouter()


def _get_user_weak_phonemes(
    db: Database, user_id: str, limit_attempts: int = 20, bottom_n: int = 3
) -> List[str]:
    """Compute bottom-N phonemes from recent attempts on demand."""
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT phoneme_scores
                FROM pronunciation_attempts
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit_attempts),
            )
            rows = cur.fetchall()

    phoneme_totals = {}  # {phoneme: {"sum": float, "count": int}}

    for row in rows:
        scores_list = row["phoneme_scores"] or []
        for item in scores_list:
            ph = item.get("phoneme")
            sc = float(item.get("score", 0.0))
            if not ph:
                continue
            if ph not in phoneme_totals:
                phoneme_totals[ph] = {"sum": 0.0, "count": 0}
            phoneme_totals[ph]["sum"] += sc
            phoneme_totals[ph]["count"] += 1

    if not phoneme_totals:
        return []

    # Compute averages
    avg_scores = [
        (ph, totals["sum"] / totals["count"]) for ph, totals in phoneme_totals.items()
    ]

    # Sort by avg ascending, take bottom_n
    avg_scores.sort(key=lambda x: x[1])
    weak = [ph for ph, _ in avg_scores[:bottom_n]]
    return weak


@router.post("/pronunciation/score")
async def score_pronunciation(
    audio_file: UploadFile = File(...),
    reference_text: str = Form(...),
    db: Database = Depends(get_db),
    user_id_from_token: str = Depends(verify_token),
) -> Dict[str, Any]:
    if not reference_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reference_text is required",
        )

    # Save to temp
    tmp_filename = f"{uuid.uuid4()}.webm"
    tmp_path = os.path.join("/tmp", tmp_filename)

    try:
        contents = await audio_file.read()
        with open(tmp_path, "wb") as f:
            f.write(contents)

        scorer = PronunciationScorer()
        result = scorer.score_audio(tmp_path, reference_text)

        # Persist attempt
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO pronunciation_attempts (user_id, phrase, phoneme_scores, overall_score)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_id_from_token,
                        reference_text,
                        psycopg.types.json.Json(result["phoneme_scores"]),
                        result["overall_score"],
                    ),
                )

        return result

    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            # Silent cleanup failure; not worth crashing the request
            pass


@router.get("/pronunciation/weak-phonemes")
async def get_weak_phonemes(
    db: Database = Depends(get_db),
    user_id_from_token: str = Depends(verify_token),
    limit_attempts: int = Query(20, ge=1, le=200),
    bottom_n: int = Query(3, ge=1, le=10),
) -> Dict[str, Any]:
    """Get user's weak phonemes based on recent attempts."""
    weak = _get_user_weak_phonemes(db, user_id_from_token, limit_attempts, bottom_n)
    return {"weak_phonemes": weak}


@router.get("/pronunciation/daily-phrase")
async def get_daily_phrase(
    db: Database = Depends(get_db),
    user_id_from_token: str = Depends(verify_token),
) -> Dict[str, Any]:
    """Get a practice phrase targeting user's weak phonemes."""
    weak = _get_user_weak_phonemes(db, user_id_from_token, limit_attempts=20, bottom_n=3)

    # If no history yet, just return a random phrase
    if not weak:
        phrase = random.choice(PRACTICE_PHRASES)
        return {
            "text": phrase["text"],
            "target_phonemes": phrase["phonemes"],
        }

    # Try to find phrases that contain at least one weak phoneme
    candidates = [
        p
        for p in PRACTICE_PHRASES
        if any(ph in p["phonemes"] for ph in weak)
    ]

    if not candidates:
        phrase = random.choice(PRACTICE_PHRASES)
    else:
        phrase = random.choice(candidates)

    return {
        "text": phrase["text"],
        "target_phonemes": phrase["phonemes"],
    }


@router.get("/pronunciation/summary")
async def get_summary(
    db: Database = Depends(get_db),
    user_id_from_token: str = Depends(verify_token),
) -> Dict[str, Any]:
    """Get user's pronunciation practice summary statistics."""
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Total attempts
            cur.execute(
                "SELECT COUNT(*) FROM pronunciation_attempts WHERE user_id = %s",
                (user_id_from_token,),
            )
            total_attempts = cur.fetchone()[0]

            # Last 7 days stats
            cur.execute(
                """
                SELECT COUNT(*), AVG(overall_score)
                FROM pronunciation_attempts
                WHERE user_id = %s AND created_at >= NOW() - INTERVAL '7 days'
                """,
                (user_id_from_token,),
            )
            row = cur.fetchone()
            last_7d_attempts = row[0] or 0
            last_7d_avg_score = float(row[1]) if row[1] is not None else 0.0

            # Weakest 5 phonemes (all-time)
            cur.execute(
                "SELECT phoneme_scores FROM pronunciation_attempts WHERE user_id = %s",
                (user_id_from_token,),
            )
            rows = cur.fetchall()

    phoneme_totals = {}
    for row in rows:
        scores_list = row["phoneme_scores"] or []
        for item in scores_list:
            ph = item.get("phoneme")
            sc = float(item.get("score", 0.0))
            if not ph:
                continue
            if ph not in phoneme_totals:
                phoneme_totals[ph] = {"sum": 0.0, "count": 0}
            phoneme_totals[ph]["sum"] += sc
            phoneme_totals[ph]["count"] += 1

    # Compute averages and sort
    phoneme_avgs = [
        {
            "phoneme": ph,
            "avg_score": round(totals["sum"] / totals["count"], 1),
            "attempts": totals["count"],
        }
        for ph, totals in phoneme_totals.items()
    ]
    phoneme_avgs.sort(key=lambda x: x["avg_score"])
    weakest_phonemes = phoneme_avgs[:5]

    return {
        "total_attempts": total_attempts,
        "last_7d_avg_score": round(last_7d_avg_score, 1),
        "last_7d_attempts": last_7d_attempts,
        "weakest_phonemes": weakest_phonemes,
    }


@router.get("/pronunciation/stats")
async def get_pronunciation_stats(
    db: Database = Depends(get_db),
    user_id_from_token: str = Depends(verify_token),
) -> Dict[str, Any]:
    """
    Get comprehensive pronunciation statistics with improvement tracking.

    Returns detailed analytics including:
    - Overall progress and trends
    - Most improved words/phonemes
    - Areas needing work
    - Personalized practice recommendations
    """
    analyzer = PronunciationAnalyzer(db=db)
    return analyzer.get_pronunciation_stats(user_id_from_token)
