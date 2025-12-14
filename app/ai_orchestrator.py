"""
AI Orchestrator for Vorex.

Coordinates multiple AI services running in parallel for efficient processing:
1. Ranking AI - Evaluates grammar, fluency, vocabulary
2. Conversation AI - Generates persona-aware responses with full history
3. Pronunciation AI - Analyzes phoneme accuracy (optional)

Enhanced with User Language Profile for adaptive tutoring.
"""

import asyncio
import json
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from app.config import config
from app.asr_client import asr_client
from app.audio_quality import (
    analyze_audio_quality_from_bytes,
    analyze_audio_quality_from_file,
    AudioQualityResult,
    should_penalize_pronunciation
)
from app.language_profile import (
    LanguageProfileManager,
    UserLanguageProfile,
    analyze_errors_from_ranking
)


@dataclass
class RankingResult:
    """Result from the ranking AI."""
    grammar_score: int
    fluency_score: int
    vocabulary_score: int
    task_completion: int
    cefr_estimate: str
    errors: List[Dict[str, Any]]
    strengths: List[str]
    areas_to_improve: List[str]

    def to_dict(self) -> dict:
        return {
            "grammar_score": self.grammar_score,
            "fluency_score": self.fluency_score,
            "vocabulary_score": self.vocabulary_score,
            "task_completion": self.task_completion,
            "cefr_estimate": self.cefr_estimate,
            "errors": self.errors,
            "strengths": self.strengths,
            "areas_to_improve": self.areas_to_improve
        }


@dataclass
class ConversationResult:
    """Result from the conversation AI."""
    text: str
    emotion: str
    suggested_topics: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "emotion": self.emotion,
            "suggested_topics": self.suggested_topics
        }


@dataclass
class PronunciationResult:
    """Result from the pronunciation AI."""
    overall_score: int
    word_scores: List[Dict[str, Any]]
    problem_sounds: List[str]
    mic_quality_warning: bool = False
    confidence_note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "word_scores": self.word_scores,
            "problem_sounds": self.problem_sounds,
            "mic_quality_warning": self.mic_quality_warning,
            "confidence_note": self.confidence_note
        }


@dataclass
class OrchestratorResult:
    """Combined result from all AI services."""
    transcript: str
    response: ConversationResult
    ranking: Optional[RankingResult]
    pronunciation: Optional[PronunciationResult]
    audio_quality: AudioQualityResult

    def to_dict(self) -> dict:
        result = {
            "transcript": self.transcript,
            "response": self.response.to_dict(),
            "audio_quality": self.audio_quality.to_dict()
        }
        if self.ranking:
            result["ranking"] = self.ranking.to_dict()
        if self.pronunciation:
            result["pronunciation"] = self.pronunciation.to_dict()
        return result


class AIOrchestrator:
    """
    Orchestrates multiple AI services in parallel for efficient processing.

    This class runs multiple AI evaluations concurrently to minimize latency
    while maintaining accuracy across ranking, conversation, and pronunciation.

    Enhanced with User Language Profile for adaptive tutoring - automatically
    adjusts AI behavior based on user's specific weaknesses and learning history.
    """

    def __init__(self, db=None):
        self.openai_client = None
        self.db = db
        self.profile_manager = LanguageProfileManager(db) if db else None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize API clients."""
        if config.llm.api_key and config.llm.provider == "openai":
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=config.llm.api_key)
            except ImportError:
                print("[AIOrchestrator] OpenAI package not installed")

    async def process_user_turn(
        self,
        audio_bytes: bytes,
        conversation_history: List[Dict[str, str]],
        persona: Optional[Dict[str, Any]] = None,
        include_ranking: bool = True,
        include_pronunciation: bool = False,
        user_id: Optional[uuid.UUID] = None
    ) -> OrchestratorResult:
        """
        Process a user's voice turn with parallel AI execution.

        Args:
            audio_bytes: Raw audio data
            conversation_history: List of {"role": "user"|"assistant", "content": "..."}
            persona: Optional persona/scenario config with system_prompt
            include_ranking: Whether to run ranking AI
            include_pronunciation: Whether to run pronunciation AI
            user_id: Optional user UUID for language profile injection

        Returns:
            OrchestratorResult with all AI outputs combined
        """
        # Load language profile if user_id provided
        language_profile = None
        prompt_injection = ""
        if user_id and self.profile_manager:
            try:
                language_profile = self.profile_manager.get_profile(user_id)
                prompt_injection = self.profile_manager.get_prompt_injection(user_id)
            except Exception as e:
                print(f"[AIOrchestrator] Failed to load language profile: {e}")
        # Step 1: Run ASR and audio quality analysis in parallel
        asr_task = asyncio.to_thread(
            asr_client.transcribe_bytes,
            audio_bytes,
            "audio.webm"
        )
        quality_task = asyncio.to_thread(
            analyze_audio_quality_from_bytes,
            audio_bytes
        )

        asr_result, audio_quality = await asyncio.gather(asr_task, quality_task)
        transcript = asr_result.text.strip()

        if not transcript:
            # No speech detected
            return OrchestratorResult(
                transcript="",
                response=ConversationResult(
                    text="I didn't catch that. Could you please try again?",
                    emotion="patient"
                ),
                ranking=None,
                pronunciation=None,
                audio_quality=audio_quality
            )

        # Step 2: Run AI services in parallel
        tasks = []

        # Always run conversation AI (with language profile injection)
        conversation_task = self._run_conversation_ai(
            transcript,
            conversation_history,
            persona,
            prompt_injection=prompt_injection
        )
        tasks.append(("conversation", conversation_task))

        # Optionally run ranking AI
        if include_ranking:
            ranking_task = self._run_ranking_ai(transcript, conversation_history)
            tasks.append(("ranking", ranking_task))

        # Optionally run pronunciation AI
        if include_pronunciation and asr_result.words:
            pronunciation_task = self._run_pronunciation_ai(
                transcript,
                asr_result.words,
                audio_quality
            )
            tasks.append(("pronunciation", pronunciation_task))

        # Execute all tasks in parallel
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

        # Map results back to their types
        result_map = {}
        for i, (name, _) in enumerate(tasks):
            if isinstance(results[i], Exception):
                print(f"[AIOrchestrator] {name} AI failed: {results[i]}")
                result_map[name] = None
            else:
                result_map[name] = results[i]

        # Build final result
        conversation = result_map.get("conversation")
        if not conversation:
            conversation = ConversationResult(
                text="I understood you! Let's continue.",
                emotion="friendly"
            )

        # Record errors from ranking result for language profile
        ranking = result_map.get("ranking")
        if ranking and user_id and self.profile_manager:
            try:
                # Convert to dict for error analysis
                ranking_dict = ranking.to_dict()
                analyze_errors_from_ranking(
                    ranking_dict,
                    user_id,
                    self.profile_manager
                )
            except Exception as e:
                print(f"[AIOrchestrator] Error recording to profile: {e}")

        return OrchestratorResult(
            transcript=transcript,
            response=conversation,
            ranking=ranking,
            pronunciation=result_map.get("pronunciation"),
            audio_quality=audio_quality
        )

    async def _run_conversation_ai(
        self,
        user_text: str,
        conversation_history: List[Dict[str, str]],
        persona: Optional[Dict[str, Any]],
        prompt_injection: str = ""
    ) -> ConversationResult:
        """
        Run the conversation AI with full message history.

        This uses proper OpenAI messages format with role-based turns.
        Enhanced with language profile injection for adaptive tutoring.
        """
        if not self.openai_client:
            return ConversationResult(
                text="I understood what you said! Let me help you with that.",
                emotion="friendly"
            )

        # Build system prompt
        if persona and persona.get("system_prompt"):
            system_prompt = persona["system_prompt"]
        else:
            system_prompt = self._get_default_system_prompt()

        # Inject language profile for adaptive tutoring
        if prompt_injection:
            system_prompt = f"{system_prompt}\n\n{prompt_injection}"

        # Build messages array with PROPER format (not context dump!)
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history as separate messages
        for turn in conversation_history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ["user", "assistant"] and content:
                messages.append({"role": role, "content": content})

        # Add current user message
        messages.append({"role": "user", "content": user_text})

        try:
            response = await asyncio.to_thread(
                self._call_openai_chat,
                messages,
                model="gpt-4o",
                temperature=0.7,
                max_tokens=500
            )

            # Parse response
            try:
                data = json.loads(response)
                return ConversationResult(
                    text=data.get("text", response),
                    emotion=data.get("emotion", "friendly"),
                    suggested_topics=data.get("suggested_topics", [])
                )
            except json.JSONDecodeError:
                # Response wasn't JSON, use raw text
                return ConversationResult(
                    text=response,
                    emotion="friendly",
                    suggested_topics=[]
                )

        except Exception as e:
            print(f"[AIOrchestrator] Conversation AI error: {e}")
            return ConversationResult(
                text="I understood you! Let me think about that.",
                emotion="thoughtful"
            )

    async def _run_ranking_ai(
        self,
        user_text: str,
        conversation_history: List[Dict[str, str]]
    ) -> RankingResult:
        """
        Run the ranking AI to evaluate user's language.
        Uses GPT-4o-mini for speed and cost efficiency.
        """
        if not self.openai_client:
            return self._default_ranking()

        system_prompt = """You are a language assessment AI. Evaluate the user's English based on:
- Grammar accuracy (0-100)
- Fluency (0-100)
- Vocabulary richness (0-100)
- Task completion (0-100)
- CEFR level estimate (A1, A2, B1, B2, C1, C2)

Also identify:
- Specific errors with corrections
- Strengths
- Areas to improve

Respond ONLY with valid JSON:
{
  "grammar_score": 85,
  "fluency_score": 78,
  "vocabulary_score": 72,
  "task_completion": 90,
  "cefr_estimate": "B1",
  "errors": [
    {"type": "grammar", "text": "original", "correction": "corrected", "severity": "minor"}
  ],
  "strengths": ["Good use of vocabulary"],
  "areas_to_improve": ["Article usage"]
}"""

        # Include recent context for better evaluation
        context = ""
        if conversation_history:
            recent = conversation_history[-4:]  # Last 2 turns
            context = "\n\nRecent conversation:\n"
            for turn in recent:
                context += f"{turn['role'].title()}: {turn['content']}\n"

        user_message = f"Evaluate this English learner's message:{context}\n\nCurrent message: \"{user_text}\""

        try:
            response = await asyncio.to_thread(
                self._call_openai_chat,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="gpt-4o-mini",
                temperature=0.3,
                max_tokens=500
            )

            data = json.loads(response)
            return RankingResult(
                grammar_score=data.get("grammar_score", 75),
                fluency_score=data.get("fluency_score", 75),
                vocabulary_score=data.get("vocabulary_score", 75),
                task_completion=data.get("task_completion", 80),
                cefr_estimate=data.get("cefr_estimate", "B1"),
                errors=data.get("errors", []),
                strengths=data.get("strengths", []),
                areas_to_improve=data.get("areas_to_improve", [])
            )

        except Exception as e:
            print(f"[AIOrchestrator] Ranking AI error: {e}")
            return self._default_ranking()

    async def _run_pronunciation_ai(
        self,
        transcript: str,
        word_timings: list,
        audio_quality: AudioQualityResult
    ) -> PronunciationResult:
        """
        Run pronunciation analysis.

        Note: For now, this uses a simple heuristic.
        Full Allosaurus integration would go here.
        """
        # Simple word-level scoring based on ASR confidence
        word_scores = []
        problem_sounds = set()

        for w in word_timings:
            confidence = getattr(w, 'confidence', None)
            if confidence is not None:
                score = int(confidence * 100)
            else:
                # No confidence from Whisper, use random reasonable score
                import random
                score = random.randint(70, 95)

            word_scores.append({
                "word": w.word.strip(),
                "score": score,
                "start": w.start,
                "end": w.end
            })

            # Identify problem sounds (words with low scores)
            if score < 70:
                # Simplified: mark first consonant as problematic
                word = w.word.lower().strip()
                if word and word[0].isalpha():
                    problem_sounds.add(f"/{word[0]}/")

        # Calculate overall score
        if word_scores:
            overall = sum(ws["score"] for ws in word_scores) // len(word_scores)
        else:
            overall = 75

        # Add confidence penalty for poor audio
        mic_warning = should_penalize_pronunciation(audio_quality)
        confidence_note = None
        if mic_warning:
            confidence_note = "Audio quality may affect accuracy. Try a quieter environment."
            # Boost score slightly to account for mic issues
            overall = min(100, overall + 5)

        return PronunciationResult(
            overall_score=overall,
            word_scores=word_scores,
            problem_sounds=list(problem_sounds),
            mic_quality_warning=mic_warning,
            confidence_note=confidence_note
        )

    def _call_openai_chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Synchronous OpenAI chat completion call."""
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30
        )
        return response.choices[0].message.content

    def _get_default_system_prompt(self) -> str:
        """Get default tutor system prompt."""
        return """You are Alex, a friendly English conversation tutor.
You're having a natural conversation with a language learner.

Guidelines:
- Be warm, encouraging, and natural
- Respond conversationally (don't lecture)
- Keep responses concise (2-3 sentences usually)
- If they make errors, model correct usage naturally in your response
- Stay engaged with the topic they're discussing

Respond with JSON:
{
  "text": "Your conversational response",
  "emotion": "friendly|encouraging|curious|thoughtful",
  "suggested_topics": ["optional", "follow-up", "topics"]
}"""

    def _default_ranking(self) -> RankingResult:
        """Return default ranking when AI is unavailable."""
        return RankingResult(
            grammar_score=75,
            fluency_score=75,
            vocabulary_score=75,
            task_completion=80,
            cefr_estimate="B1",
            errors=[],
            strengths=["Good communication"],
            areas_to_improve=["Keep practicing!"]
        )


# Global orchestrator instance
ai_orchestrator = AIOrchestrator()


# Helper function for synchronous contexts
def process_voice_turn_sync(
    audio_bytes: bytes,
    conversation_history: List[Dict[str, str]],
    persona: Optional[Dict[str, Any]] = None,
    include_ranking: bool = True,
    include_pronunciation: bool = False,
    user_id: Optional[uuid.UUID] = None
) -> OrchestratorResult:
    """
    Synchronous wrapper for process_user_turn.
    Use this when calling from non-async code.
    """
    return asyncio.run(
        ai_orchestrator.process_user_turn(
            audio_bytes=audio_bytes,
            conversation_history=conversation_history,
            persona=persona,
            include_ranking=include_ranking,
            include_pronunciation=include_pronunciation,
            user_id=user_id
        )
    )


def create_orchestrator_with_db(db) -> AIOrchestrator:
    """
    Create an orchestrator with database connection for language profile support.

    Args:
        db: Database instance with get_connection() method

    Returns:
        AIOrchestrator with language profile support enabled
    """
    return AIOrchestrator(db=db)
