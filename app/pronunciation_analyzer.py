"""
Enhanced Pronunciation Analysis for SpeakSharp.

Provides detailed, actionable pronunciation feedback using:
- Word-level timing from Whisper
- Phoneme-level scoring
- Common mispronunciation detection
- Improvement tracking over time
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
from dataclasses import dataclass

from app.models import WordTiming, ASRResult
from app.db import Database


@dataclass
class PronunciationTip:
    """Specific pronunciation guidance for a phoneme or word."""
    word: str
    issue: str
    tip: str
    phonetic: Optional[str] = None
    example: Optional[str] = None


@dataclass
class WordPronunciation:
    """Pronunciation assessment for a single word."""
    word: str
    score: float  # 0-100
    issues: List[str]
    timing: Optional[WordTiming] = None


@dataclass
class PronunciationFeedback:
    """Complete pronunciation feedback for an utterance."""
    overall_score: float  # 0-100
    word_scores: List[WordPronunciation]
    tips: List[PronunciationTip]
    encouragement: str
    problem_sounds: List[str]


# Common pronunciation issues for English learners
COMMON_MISPRONUNCIATIONS = {
    # TH sounds
    "the": {
        "common_errors": ["de", "da", "ze"],
        "tip": "Place your tongue between your teeth and blow air gently. It should feel like a soft vibration.",
        "phonetic": "/ðə/",
        "example": "Say 'the' like 'thuh', not 'duh'"
    },
    "think": {
        "common_errors": ["tink", "sink", "fink"],
        "tip": "Place your tongue between your teeth for the 'th' sound. Practice saying 'three, think, thought'.",
        "phonetic": "/θɪŋk/",
        "example": "Think starts with a soft 'th' sound, not 't'"
    },
    "this": {
        "common_errors": ["dis", "zis"],
        "tip": "Tongue between teeth, make it vibrate: 'th-th-this'",
        "phonetic": "/ðɪs/",
        "example": "This, that, these, those - all start with tongue between teeth"
    },

    # R sounds
    "right": {
        "common_errors": ["light", "wight"],
        "tip": "Curl your tongue back slightly without touching the roof of your mouth. The 'r' should be strong.",
        "phonetic": "/raɪt/",
        "example": "Right, read, run - practice making the 'r' sound"
    },
    "very": {
        "common_errors": ["wery", "bery"],
        "tip": "Touch your top teeth with your bottom lip for the 'v' sound, then curl tongue for 'r'.",
        "phonetic": "/ˈvɛri/",
        "example": "Very good - make sure to pronounce both 'v' and 'r' clearly"
    },

    # V/W confusion
    "water": {
        "common_errors": ["vater", "wafer"],
        "tip": "Round your lips for 'w', then say 'aw' sound. Not 'v' sound.",
        "phonetic": "/ˈwɔtər/",
        "example": "Water, want, will - lips should be rounded for 'w'"
    },
    "work": {
        "common_errors": ["vork"],
        "tip": "Start with rounded lips for 'w', not teeth-on-lip for 'v'.",
        "phonetic": "/wɜrk/",
        "example": "Work, word, world - all start with rounded 'w'"
    },

    # Final consonants
    "good": {
        "common_errors": ["goo", "gut"],
        "tip": "Don't drop the final 'd'! Touch your tongue to the roof of your mouth.",
        "phonetic": "/ɡʊd/",
        "example": "Good food - both words end with 'd'"
    },
    "want": {
        "common_errors": ["won", "wan"],
        "tip": "End with a clear 't' sound. Touch your tongue to the roof.",
        "phonetic": "/wɑnt/",
        "example": "I want it - pronounce the 't' clearly"
    },

    # Vowel sounds
    "can": {
        "common_errors": ["ken", "con"],
        "tip": "Open your mouth wider for the 'a' in 'can' - it's like 'cat', not 'ken'.",
        "phonetic": "/kæn/",
        "example": "Can you? - short 'a' sound, mouth wide"
    },
    "world": {
        "common_errors": ["word", "vorld"],
        "tip": "Say 'wer-uhld' with clear 'l' at the end. Round lips for 'w'.",
        "phonetic": "/wɜrld/",
        "example": "World, girl, pearl - similar 'er' sound"
    },

    # Consonant clusters
    "street": {
        "common_errors": ["steet", "seet"],
        "tip": "Three consonants: s-t-r together. Don't skip the 'r'.",
        "phonetic": "/strit/",
        "example": "Street, strong, straight - keep all three sounds"
    },
    "three": {
        "common_errors": ["tree", "free"],
        "tip": "Start with tongue between teeth for 'th', then add 'r'.",
        "phonetic": "/θri/",
        "example": "Three, throw, through - 'th' then 'r'"
    },
}


# Phoneme-level tips for common issues
PHONEME_TIPS = {
    "th": "Place your tongue between your teeth and blow air gently",
    "r": "Curl your tongue back without touching the roof of your mouth",
    "l": "Touch your tongue to the ridge behind your top teeth",
    "v": "Touch your top teeth with your bottom lip and vibrate",
    "w": "Round your lips like you're about to whistle",
    "p": "Press lips together then release with a puff of air",
    "b": "Like 'p' but with voice - feel the vibration",
    "s": "Tongue behind top teeth, make a hissing sound",
    "z": "Like 's' but with voice - feel the vibration",
    "sh": "Round lips slightly, make a 'shh' sound",
    "ch": "Like 'tsh' together - chin, church, cheese",
    "j": "Like 'dzh' together - jump, judge, just",
    "ng": "Sound comes through nose, tongue touches soft palate",
}


class PronunciationAnalyzer:
    """
    Analyzes pronunciation and provides specific, actionable feedback.

    Uses multiple data sources:
    - ASR word-level timestamps
    - Phoneme scoring from pronunciation_scorer
    - Historical pronunciation data
    - Common error patterns
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db

    def analyze_pronunciation(
        self,
        asr_result: ASRResult,
        reference_text: str,
        user_id: Optional[str] = None,
        phoneme_scores: Optional[List[Dict]] = None
    ) -> PronunciationFeedback:
        """
        Analyze pronunciation and generate specific feedback.

        Args:
            asr_result: ASR transcription result with word timings
            reference_text: What the user was trying to say
            user_id: User ID for historical tracking
            phoneme_scores: Optional phoneme-level scores from pronunciation_scorer

        Returns:
            PronunciationFeedback with scores, tips, and encouragement
        """
        # Compare transcribed text to reference
        transcribed_words = asr_result.text.lower().split()
        reference_words = reference_text.lower().split()

        # Analyze word-level pronunciation
        word_scores = self._analyze_words(
            transcribed_words,
            reference_words,
            asr_result.words,
            phoneme_scores
        )

        # Calculate overall score
        if word_scores:
            overall_score = sum(w.score for w in word_scores) / len(word_scores)
        else:
            overall_score = 50.0  # Neutral score if no data

        # Detect problem areas
        problem_sounds = self._detect_problem_sounds(
            transcribed_words,
            reference_words,
            phoneme_scores
        )

        # Generate specific tips
        tips = self._generate_tips(
            word_scores,
            problem_sounds,
            user_id
        )

        # Generate encouraging message
        encouragement = self._generate_encouragement(
            overall_score,
            tips,
            user_id
        )

        return PronunciationFeedback(
            overall_score=round(overall_score, 1),
            word_scores=word_scores,
            tips=tips,
            encouragement=encouragement,
            problem_sounds=problem_sounds
        )

    def _analyze_words(
        self,
        transcribed: List[str],
        reference: List[str],
        word_timings: Optional[List[WordTiming]],
        phoneme_scores: Optional[List[Dict]]
    ) -> List[WordPronunciation]:
        """Analyze pronunciation of individual words."""
        word_pronunciations = []

        # Simple alignment: assume same length or close
        max_len = max(len(transcribed), len(reference))

        for i in range(min(len(reference), max_len)):
            ref_word = reference[i] if i < len(reference) else ""
            trans_word = transcribed[i] if i < len(transcribed) else ""
            timing = word_timings[i] if word_timings and i < len(word_timings) else None

            if not ref_word:
                continue

            # Calculate word score
            score, issues = self._score_word(ref_word, trans_word, phoneme_scores)

            word_pronunciations.append(WordPronunciation(
                word=ref_word,
                score=score,
                issues=issues,
                timing=timing
            ))

        return word_pronunciations

    def _score_word(
        self,
        reference: str,
        transcribed: str,
        phoneme_scores: Optional[List[Dict]]
    ) -> Tuple[float, List[str]]:
        """Score a single word's pronunciation."""
        issues = []

        # Exact match - perfect score
        if reference == transcribed:
            return 100.0, issues

        # Check for common mispronunciations
        if reference in COMMON_MISPRONUNCIATIONS:
            common = COMMON_MISPRONUNCIATIONS[reference]
            if transcribed in common["common_errors"]:
                issues.append(f"Pronounced like '{transcribed}'")
                return 40.0, issues

        # Partial match - decent score
        if reference in transcribed or transcribed in reference:
            issues.append("Close but slightly different")
            return 70.0, issues

        # Check Levenshtein-like similarity
        similarity = self._calculate_similarity(reference, transcribed)

        if similarity > 0.7:
            return 75.0, issues
        elif similarity > 0.5:
            issues.append("Several sounds were different")
            return 55.0, issues
        else:
            issues.append("Very different from target")
            return 30.0, issues

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple character-level similarity."""
        if not s1 or not s2:
            return 0.0

        # Count matching characters in order
        matches = sum(1 for c1, c2 in zip(s1, s2) if c1 == c2)
        max_len = max(len(s1), len(s2))

        return matches / max_len if max_len > 0 else 0.0

    def _detect_problem_sounds(
        self,
        transcribed: List[str],
        reference: List[str],
        phoneme_scores: Optional[List[Dict]]
    ) -> List[str]:
        """Detect recurring problematic sounds."""
        problems = []

        # Check for th -> d/t substitution
        ref_text = " ".join(reference)
        trans_text = " ".join(transcribed)

        if "th" in ref_text and ("d" in trans_text or "t" in trans_text):
            # Check if 'the' became 'de' or similar
            if "the" in reference and ("de" in transcribed or "da" in transcribed):
                problems.append("th")

        # Check for r/l confusion
        if "r" in ref_text and "l" in trans_text:
            problems.append("r")
        elif "l" in ref_text and "r" in trans_text:
            problems.append("l")

        # Check for v/w confusion
        if "v" in ref_text and "w" in trans_text:
            problems.append("v")
        elif "w" in ref_text and "v" in trans_text:
            problems.append("w")

        # Use phoneme scores if available
        if phoneme_scores:
            for item in phoneme_scores:
                phoneme = item.get("phoneme", "")
                score = item.get("score", 100)

                if score < 60:  # Low score threshold
                    # Extract key sound
                    for sound in PHONEME_TIPS.keys():
                        if sound in phoneme:
                            if sound not in problems:
                                problems.append(sound)

        return problems[:3]  # Limit to top 3 problem sounds

    def _generate_tips(
        self,
        word_scores: List[WordPronunciation],
        problem_sounds: List[str],
        user_id: Optional[str]
    ) -> List[PronunciationTip]:
        """Generate specific, actionable pronunciation tips."""
        tips = []

        # Tips for poorly pronounced words
        for word_pron in word_scores:
            if word_pron.score < 70 and word_pron.word in COMMON_MISPRONUNCIATIONS:
                info = COMMON_MISPRONUNCIATIONS[word_pron.word]
                tips.append(PronunciationTip(
                    word=word_pron.word,
                    issue=f"Score: {word_pron.score:.0f}/100",
                    tip=info["tip"],
                    phonetic=info.get("phonetic"),
                    example=info.get("example")
                ))

        # Tips for problem sounds
        for sound in problem_sounds:
            if sound in PHONEME_TIPS and len(tips) < 3:
                tips.append(PronunciationTip(
                    word=f"'{sound}' sound",
                    issue="This sound needs practice",
                    tip=PHONEME_TIPS[sound],
                    phonetic=None,
                    example=None
                ))

        # If we have user history, add personalized tips
        if user_id and self.db and len(tips) < 3:
            historical_tips = self._get_historical_tips(user_id)
            tips.extend(historical_tips[:3 - len(tips)])

        return tips[:3]  # Limit to top 3 tips

    def _get_historical_tips(self, user_id: str) -> List[PronunciationTip]:
        """Get tips based on user's historical weak areas."""
        if not self.db:
            return []

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get recent weak phonemes
                    cur.execute("""
                        SELECT phoneme_scores
                        FROM pronunciation_attempts
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 10
                    """, (user_id,))

                    rows = cur.fetchall()

            # Aggregate phoneme scores
            phoneme_totals = {}
            for row in rows:
                scores = row.get("phoneme_scores", []) or []
                for item in scores:
                    ph = item.get("phoneme", "")
                    sc = item.get("score", 100)

                    if ph not in phoneme_totals:
                        phoneme_totals[ph] = []
                    phoneme_totals[ph].append(sc)

            # Find consistently weak phonemes
            weak_phonemes = []
            for phoneme, scores in phoneme_totals.items():
                avg_score = sum(scores) / len(scores)
                if avg_score < 70 and len(scores) >= 3:  # Consistent weakness
                    weak_phonemes.append((phoneme, avg_score))

            # Sort by score and generate tips
            weak_phonemes.sort(key=lambda x: x[1])
            tips = []

            for phoneme, score in weak_phonemes[:2]:
                # Try to match to known phoneme tips
                for sound, tip in PHONEME_TIPS.items():
                    if sound in phoneme.lower():
                        tips.append(PronunciationTip(
                            word=f"'{sound}' sound",
                            issue=f"Recurring challenge (avg: {score:.0f}/100)",
                            tip=tip,
                            phonetic=None,
                            example="Keep practicing - you're improving!"
                        ))
                        break

            return tips

        except Exception as e:
            print(f"Error getting historical tips: {e}")
            return []

    def _generate_encouragement(
        self,
        score: float,
        tips: List[PronunciationTip],
        user_id: Optional[str]
    ) -> str:
        """Generate encouraging but specific feedback message."""

        # Check for improvement if we have history
        improvement_note = ""
        if user_id and self.db:
            improvement = self._get_improvement_trend(user_id)
            if improvement > 5:
                improvement_note = f" Your pronunciation has improved by {improvement:.0f}% recently!"
            elif improvement > 0:
                improvement_note = " You're making steady progress!"

        # Generate score-based message
        if score >= 90:
            base_msg = "Excellent pronunciation!"
        elif score >= 80:
            base_msg = "Very good! Your pronunciation is quite clear."
        elif score >= 70:
            base_msg = "Good effort! You're pronouncing most words well."
        elif score >= 60:
            base_msg = "You're on the right track. Keep practicing these sounds."
        else:
            base_msg = "Don't worry - pronunciation takes practice! Focus on the tips below."

        # Add tip preview
        if tips:
            tip_preview = f" Focus on: {tips[0].word}."
        else:
            tip_preview = " Keep up the great work!"

        return base_msg + tip_preview + improvement_note

    def _get_improvement_trend(self, user_id: str) -> float:
        """Calculate recent improvement percentage."""
        if not self.db:
            return 0.0

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get last 10 scores
                    cur.execute("""
                        SELECT overall_score, created_at
                        FROM pronunciation_attempts
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 10
                    """, (user_id,))

                    rows = cur.fetchall()

            if len(rows) < 6:  # Need enough data
                return 0.0

            # Compare recent half vs older half
            recent_scores = [r["overall_score"] for r in rows[:5]]
            older_scores = [r["overall_score"] for r in rows[5:10]]

            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)

            improvement = recent_avg - older_avg
            return improvement

        except Exception as e:
            print(f"Error calculating improvement: {e}")
            return 0.0

    def get_pronunciation_stats(self, user_id: str) -> Dict:
        """
        Get comprehensive pronunciation statistics for a user.

        Returns:
            Dictionary with stats including:
            - Overall progress
            - Most improved words/sounds
            - Areas needing work
            - Practice recommendations
        """
        if not self.db:
            return {
                "error": "Database not available"
            }

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get all pronunciation attempts
                    cur.execute("""
                        SELECT
                            overall_score,
                            phoneme_scores,
                            phrase,
                            created_at
                        FROM pronunciation_attempts
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 50
                    """, (user_id,))

                    rows = cur.fetchall()

            if not rows:
                return {
                    "total_attempts": 0,
                    "message": "No pronunciation data yet. Start practicing!"
                }

            # Calculate overall stats
            all_scores = [r["overall_score"] for r in rows]
            recent_scores = [r["overall_score"] for r in rows[:10]]

            # Phoneme analysis
            phoneme_data = {}
            for row in rows:
                scores = row.get("phoneme_scores", []) or []
                for item in scores:
                    ph = item.get("phoneme", "")
                    sc = item.get("score", 0)

                    if ph not in phoneme_data:
                        phoneme_data[ph] = []
                    phoneme_data[ph].append(sc)

            # Find most improved phonemes
            most_improved = []
            for phoneme, scores in phoneme_data.items():
                if len(scores) >= 5:
                    # Compare first half vs second half
                    mid = len(scores) // 2
                    old_avg = sum(scores[mid:]) / len(scores[mid:])
                    new_avg = sum(scores[:mid]) / len(scores[:mid])
                    improvement = new_avg - old_avg

                    if improvement > 5:  # Significant improvement
                        most_improved.append({
                            "phoneme": phoneme,
                            "improvement": round(improvement, 1),
                            "current_score": round(new_avg, 1)
                        })

            most_improved.sort(key=lambda x: x["improvement"], reverse=True)

            # Find areas needing work
            weak_areas = []
            for phoneme, scores in phoneme_data.items():
                avg_score = sum(scores) / len(scores)
                if avg_score < 70 and len(scores) >= 3:
                    weak_areas.append({
                        "phoneme": phoneme,
                        "avg_score": round(avg_score, 1),
                        "attempts": len(scores)
                    })

            weak_areas.sort(key=lambda x: x["avg_score"])

            # Calculate trend
            if len(all_scores) >= 10:
                old_avg = sum(all_scores[-10:]) / 10
                new_avg = sum(all_scores[:10]) / 10
                trend = new_avg - old_avg
            else:
                trend = 0

            return {
                "total_attempts": len(rows),
                "current_average": round(sum(recent_scores) / len(recent_scores), 1),
                "overall_average": round(sum(all_scores) / len(all_scores), 1),
                "trend": round(trend, 1),
                "most_improved": most_improved[:5],
                "areas_needing_work": weak_areas[:5],
                "practice_suggestions": self._generate_practice_suggestions(weak_areas[:3])
            }

        except Exception as e:
            print(f"Error getting pronunciation stats: {e}")
            return {
                "error": str(e)
            }

    def _generate_practice_suggestions(self, weak_areas: List[Dict]) -> List[str]:
        """Generate specific practice suggestions based on weak areas."""
        suggestions = []

        for area in weak_areas:
            phoneme = area["phoneme"]

            # Match to known tips
            for sound, tip in PHONEME_TIPS.items():
                if sound in phoneme.lower():
                    suggestions.append(f"Practice the '{sound}' sound: {tip}")
                    break

        if not suggestions:
            suggestions.append("Keep practicing daily to improve your pronunciation!")

        return suggestions
