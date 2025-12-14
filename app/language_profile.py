"""
User Language Profile System for Vorex.

Manages user language profiles including:
- Grammar weaknesses (tracked by error type)
- Phonetic weaknesses (IPA phoneme-level)
- CEFR levels per skill
- L1 interference patterns

Provides AI prompt injection for adaptive tutoring.
"""

import uuid
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GrammarWeakness:
    """A specific grammar weakness with tracking data."""
    error_type: str
    error_category: str
    error_count: int = 0
    correct_count: int = 0
    improving: bool = False
    mastered: bool = False
    example_errors: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class PhoneticWeakness:
    """A phoneme-level pronunciation weakness."""
    target_phoneme: str  # IPA symbol
    confused_with: List[str] = field(default_factory=list)
    error_rate: float = 1.0
    problem_words: List[str] = field(default_factory=list)


@dataclass
class CEFRLevels:
    """Per-skill CEFR levels."""
    speaking: str = "A1"
    listening: str = "A1"
    grammar: str = "A1"
    vocabulary: str = "A1"
    pronunciation: str = "A1"
    fluency: str = "A1"


@dataclass
class UserLanguageProfile:
    """Complete user language profile for adaptive tutoring."""
    user_id: uuid.UUID
    native_language: Optional[str] = None
    overall_level: str = "A1"
    cefr_levels: CEFRLevels = field(default_factory=CEFRLevels)
    grammar_weaknesses: List[GrammarWeakness] = field(default_factory=list)
    phonetic_weaknesses: List[PhoneticWeakness] = field(default_factory=list)
    l1_teaching_tips: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """
        Generate a prompt context string for AI injection.

        This creates a concise summary of the user's weaknesses
        that can be injected into AI system prompts.
        """
        parts = []

        # Add native language context
        if self.native_language:
            parts.append(f"Native language: {self.native_language}")

        # Add level info
        parts.append(f"Overall level: {self.overall_level}")

        # Add grammar weaknesses (top 3)
        if self.grammar_weaknesses:
            grammar_issues = [
                f"{w.error_type} ({w.error_count} errors)"
                for w in self.grammar_weaknesses[:3]
                if not w.mastered
            ]
            if grammar_issues:
                parts.append(f"Grammar struggles: {', '.join(grammar_issues)}")

        # Add phonetic weaknesses (top 3)
        if self.phonetic_weaknesses:
            phonetic_issues = [
                f"/{w.target_phoneme}/ (confuses with {'/'.join(w.confused_with[:2])})"
                for w in self.phonetic_weaknesses[:3]
                if w.error_rate > 0.3
            ]
            if phonetic_issues:
                parts.append(f"Pronunciation issues: {', '.join(phonetic_issues)}")

        # Add teaching tips
        if self.l1_teaching_tips:
            parts.append(f"Teaching tip: {self.l1_teaching_tips[0]}")

        return "\n".join(parts)

    def get_adaptive_instructions(self) -> str:
        """
        Generate adaptive tutoring instructions based on profile.

        These instructions tell the AI how to adjust its behavior
        based on the user's specific weaknesses.
        """
        instructions = []

        # Grammar-focused instructions
        if self.grammar_weaknesses:
            top_weakness = self.grammar_weaknesses[0]
            if top_weakness.error_type == "article_usage":
                instructions.append(
                    "Pay special attention to article usage (a/an/the). "
                    "If they omit or misuse articles, model correct usage naturally."
                )
            elif top_weakness.error_type == "verb_tenses":
                instructions.append(
                    "Focus on verb tense consistency. If they mix tenses, "
                    "gently model the correct tense in your response."
                )
            elif top_weakness.error_type == "prepositions":
                instructions.append(
                    "Watch for preposition errors. Model correct preposition "
                    "usage in your responses when relevant."
                )
            elif "subject_verb" in top_weakness.error_type:
                instructions.append(
                    "Note subject-verb agreement. If they say 'he go', "
                    "include 'he goes' naturally in your reply."
                )

        # Pronunciation-focused instructions
        if self.phonetic_weaknesses:
            top_phoneme = self.phonetic_weaknesses[0]
            if top_phoneme.target_phoneme in ['θ', 'ð']:
                instructions.append(
                    "Include words with 'th' sounds (think, this, three) "
                    "to give them practice opportunities."
                )
            elif top_phoneme.target_phoneme in ['v', 'w']:
                instructions.append(
                    "Use words with 'v' and 'w' sounds to help them "
                    "practice this distinction."
                )
            elif top_phoneme.target_phoneme in ['ɪ', 'iː']:
                instructions.append(
                    "Include words that contrast short 'i' (ship, bit) with "
                    "long 'ee' (sheep, beat) for practice."
                )

        # Level-based instructions
        if self.overall_level in ["A1", "A2"]:
            instructions.append(
                "Keep vocabulary simple and sentences short. "
                "Speak clearly and don't rush."
            )
        elif self.overall_level in ["B1", "B2"]:
            instructions.append(
                "Use varied vocabulary and some idiomatic expressions. "
                "Encourage longer responses."
            )
        elif self.overall_level in ["C1", "C2"]:
            instructions.append(
                "Use natural speech patterns, idioms, and nuanced vocabulary. "
                "Challenge them with complex topics."
            )

        return " ".join(instructions)


class LanguageProfileManager:
    """Manages user language profiles with database integration."""

    def __init__(self, db):
        """
        Initialize with database connection.

        Args:
            db: Database instance with get_connection() method
        """
        self.db = db

    def get_profile(self, user_id: uuid.UUID) -> UserLanguageProfile:
        """
        Get complete language profile for a user.

        Args:
            user_id: User UUID

        Returns:
            UserLanguageProfile with all tracked data
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Try to get profile from database function
                cur.execute(
                    "SELECT get_user_language_profile(%s) as profile",
                    (user_id,)
                )
                result = cur.fetchone()

                if result and result.get('profile'):
                    return self._parse_profile(user_id, result['profile'])

                # Return default profile if nothing found
                return self._get_default_profile(user_id, conn)

    def _parse_profile(
        self,
        user_id: uuid.UUID,
        profile_json: Dict[str, Any]
    ) -> UserLanguageProfile:
        """Parse database JSON into UserLanguageProfile object."""
        # Parse CEFR levels
        cefr_data = profile_json.get('cefr_by_skill', {})
        cefr_levels = CEFRLevels(
            speaking=cefr_data.get('speaking', 'A1'),
            listening=cefr_data.get('listening', 'A1'),
            grammar=cefr_data.get('grammar', 'A1'),
            vocabulary=cefr_data.get('vocabulary', 'A1'),
            pronunciation=cefr_data.get('pronunciation', 'A1'),
            fluency=cefr_data.get('fluency', 'A1')
        )

        # Parse grammar weaknesses
        grammar_weaknesses = []
        for gw in profile_json.get('grammar_weaknesses', []):
            grammar_weaknesses.append(GrammarWeakness(
                error_type=gw.get('type', ''),
                error_category=gw.get('category', ''),
                error_count=gw.get('count', 0),
                improving=gw.get('improving', False),
                example_errors=[gw.get('example')] if gw.get('example') else []
            ))

        # Parse phonetic weaknesses
        phonetic_weaknesses = []
        for pw in profile_json.get('phonetic_weaknesses', []):
            phonetic_weaknesses.append(PhoneticWeakness(
                target_phoneme=pw.get('phoneme', ''),
                confused_with=pw.get('confused_with', []),
                error_rate=pw.get('error_rate', 1.0),
                problem_words=pw.get('problem_words', [])
            ))

        # Get L1 tips
        l1_patterns = profile_json.get('l1_patterns', {})
        teaching_tips = l1_patterns.get('teaching_tips', [])

        return UserLanguageProfile(
            user_id=user_id,
            native_language=profile_json.get('native_language'),
            overall_level=profile_json.get('overall_level', 'A1'),
            cefr_levels=cefr_levels,
            grammar_weaknesses=grammar_weaknesses,
            phonetic_weaknesses=phonetic_weaknesses,
            l1_teaching_tips=teaching_tips or []
        )

    def _get_default_profile(
        self,
        user_id: uuid.UUID,
        conn
    ) -> UserLanguageProfile:
        """Get default profile from user_profiles table."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT native_language, level FROM user_profiles WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()

            return UserLanguageProfile(
                user_id=user_id,
                native_language=result.get('native_language') if result else None,
                overall_level=result.get('level', 'A1') if result else 'A1'
            )

    def record_grammar_error(
        self,
        user_id: uuid.UUID,
        error_type: str,
        error_category: str,
        user_sentence: str,
        corrected_sentence: str,
        native_language_related: bool = False
    ) -> Optional[uuid.UUID]:
        """
        Record a grammar error for the user.

        Args:
            user_id: User UUID
            error_type: Specific error type (e.g., 'article_usage')
            error_category: Category (e.g., 'articles', 'tense')
            user_sentence: What the user said
            corrected_sentence: The corrected version
            native_language_related: Whether this is L1 interference

        Returns:
            UUID of the recorded weakness
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT record_grammar_error(
                        %s, %s, %s, %s, %s, %s
                    )""",
                    (
                        user_id, error_type, error_category,
                        user_sentence, corrected_sentence,
                        native_language_related
                    )
                )
                result = cur.fetchone()
                return result[0] if result else None

    def record_grammar_correct(
        self,
        user_id: uuid.UUID,
        error_type: str
    ) -> None:
        """Record correct usage of a previously problematic grammar pattern."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT record_grammar_correct(%s, %s)",
                    (user_id, error_type)
                )

    def record_phoneme_error(
        self,
        user_id: uuid.UUID,
        target_phoneme: str,
        confused_with: Optional[str] = None,
        problem_word: Optional[str] = None,
        position: str = 'any'
    ) -> Optional[uuid.UUID]:
        """
        Record a pronunciation error at the phoneme level.

        Args:
            user_id: User UUID
            target_phoneme: The correct phoneme (IPA)
            confused_with: What they said instead
            problem_word: The word where error occurred
            position: Position in word ('initial', 'medial', 'final', 'any')

        Returns:
            UUID of the recorded weakness
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT record_phoneme_error(
                        %s, %s, %s, %s, %s
                    )""",
                    (user_id, target_phoneme, confused_with, problem_word, position)
                )
                result = cur.fetchone()
                return result[0] if result else None

    def update_cefr_level(
        self,
        user_id: uuid.UUID,
        skill: str,
        level: str,
        confidence: float = 0.5
    ) -> bool:
        """
        Update CEFR level for a specific skill.

        Args:
            user_id: User UUID
            skill: Skill name ('speaking', 'grammar', etc.)
            level: CEFR level (A1-C2)
            confidence: Confidence in this assessment (0-1)

        Returns:
            True if updated successfully
        """
        valid_skills = ['speaking', 'listening', 'grammar', 'vocabulary',
                        'pronunciation', 'fluency']
        if skill not in valid_skills:
            return False

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Ensure row exists
                cur.execute(
                    """INSERT INTO cefr_skill_levels (user_id)
                       VALUES (%s)
                       ON CONFLICT (user_id) DO NOTHING""",
                    (user_id,)
                )

                # Update specific skill
                cur.execute(f"""
                    UPDATE cefr_skill_levels
                    SET {skill}_level = %s,
                        {skill}_confidence = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                """, (level, confidence, user_id))

                return cur.rowcount > 0

    def get_prompt_injection(self, user_id: uuid.UUID) -> str:
        """
        Get the prompt injection text for AI conversations.

        This returns a formatted string that should be appended
        to AI system prompts to make them adaptive.

        Args:
            user_id: User UUID

        Returns:
            Formatted prompt injection string
        """
        profile = self.get_profile(user_id)

        context = profile.to_prompt_context()
        instructions = profile.get_adaptive_instructions()

        if not context and not instructions:
            return ""

        return f"""
=== USER LANGUAGE PROFILE ===
{context}

=== ADAPTIVE TUTORING INSTRUCTIONS ===
{instructions}
==============================
"""


# Grammar error type mappings for analysis
GRAMMAR_ERROR_TYPES = {
    "articles": [
        "article_omission",
        "article_overuse",
        "article_confusion",  # a vs an vs the
    ],
    "tenses": [
        "present_simple_error",
        "present_continuous_error",
        "past_simple_error",
        "past_continuous_error",
        "present_perfect_error",
        "past_perfect_error",
        "future_error",
        "tense_consistency",
    ],
    "agreement": [
        "subject_verb_agreement",
        "pronoun_agreement",
        "number_agreement",
    ],
    "prepositions": [
        "preposition_omission",
        "preposition_confusion",
        "preposition_overuse",
    ],
    "word_order": [
        "adjective_order",
        "adverb_placement",
        "question_word_order",
        "negative_word_order",
    ],
    "other": [
        "double_negative",
        "run_on_sentence",
        "fragment",
        "comma_splice",
        "parallelism",
    ]
}


# IPA phonemes commonly problematic for English learners
COMMON_PROBLEM_PHONEMES = {
    "θ": {"name": "voiceless th", "example": "think", "confused_with": ["s", "f", "t"]},
    "ð": {"name": "voiced th", "example": "this", "confused_with": ["d", "z", "v"]},
    "ɪ": {"name": "short i", "example": "ship", "confused_with": ["iː", "e"]},
    "iː": {"name": "long ee", "example": "sheep", "confused_with": ["ɪ"]},
    "æ": {"name": "a in cat", "example": "cat", "confused_with": ["e", "ɑː"]},
    "ʌ": {"name": "u in cup", "example": "cup", "confused_with": ["ʊ", "ɑː"]},
    "ə": {"name": "schwa", "example": "about", "confused_with": ["ʌ", "ɜː"]},
    "r": {"name": "r sound", "example": "red", "confused_with": ["l", "w"]},
    "l": {"name": "l sound", "example": "light", "confused_with": ["r", "n"]},
    "v": {"name": "v sound", "example": "very", "confused_with": ["b", "w", "f"]},
    "w": {"name": "w sound", "example": "water", "confused_with": ["v"]},
    "ŋ": {"name": "ng sound", "example": "sing", "confused_with": ["n", "ŋk"]},
    "ʃ": {"name": "sh sound", "example": "ship", "confused_with": ["s", "tʃ"]},
    "ʒ": {"name": "zh sound", "example": "measure", "confused_with": ["dʒ", "z"]},
    "tʃ": {"name": "ch sound", "example": "church", "confused_with": ["ʃ", "t"]},
    "dʒ": {"name": "j sound", "example": "judge", "confused_with": ["ʒ", "j"]},
}


def analyze_errors_from_ranking(
    ranking_result: Dict[str, Any],
    user_id: uuid.UUID,
    profile_manager: LanguageProfileManager
) -> None:
    """
    Analyze errors from a ranking AI result and record them.

    Args:
        ranking_result: Result from the ranking AI
        user_id: User UUID
        profile_manager: LanguageProfileManager instance
    """
    errors = ranking_result.get('errors', [])

    for error in errors:
        error_type = error.get('type', 'unknown')
        user_sentence = error.get('text', '')
        corrected = error.get('correction', '')

        # Categorize the error
        category = 'other'
        for cat, types in GRAMMAR_ERROR_TYPES.items():
            if any(t in error_type.lower() for t in types):
                category = cat
                break

        # Record the error
        if user_sentence and corrected:
            profile_manager.record_grammar_error(
                user_id=user_id,
                error_type=error_type,
                error_category=category,
                user_sentence=user_sentence,
                corrected_sentence=corrected
            )
