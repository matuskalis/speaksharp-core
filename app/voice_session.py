"""
Voice session orchestration for SpeakSharp.

Wires together ASR, TutorAgent, and TTS into a complete voice interaction.
Supports streaming TTS for reduced latency.
"""

import time
import tempfile
from pathlib import Path
from typing import Union, Optional, Dict, Any, Literal, Iterator, Generator
from uuid import UUID

from app.asr_client import asr_client
from app.tts_client import tts_client
from app.tutor_agent import TutorAgent
from app.models import VoiceTurnResult, TutorResponse
from app.pronunciation_analyzer import PronunciationAnalyzer
from app.pronunciation_scorer import PronunciationScorer
from app.db import Database


class VoiceSession:
    """
    Orchestrates a voice interaction: ASR → Tutor → TTS.

    Handles audio input, processes through tutor, and generates audio response.
    """

    def __init__(
        self,
        user_level: str = "A1",
        mode: Literal["scenario", "free_chat", "drill", "lesson"] = "free_chat",
        context: Optional[Dict[str, Any]] = None,
        db: Optional[Database] = None,
        user_id: Optional[str] = None,
        enable_pronunciation_feedback: bool = True
    ):
        """
        Initialize voice session.

        Args:
            user_level: User's CEFR level (A1-C2)
            mode: Session mode (scenario, free_chat, drill, lesson)
            context: Optional context dict (scenario_id, drill_type, etc.)
            db: Optional database connection for pronunciation tracking
            user_id: Optional user ID for personalized pronunciation feedback
            enable_pronunciation_feedback: Whether to analyze and provide pronunciation feedback
        """
        self.user_level = user_level
        self.mode = mode
        self.context = context or {}
        self.tutor = TutorAgent()
        self.db = db
        self.user_id = user_id
        self.enable_pronunciation_feedback = enable_pronunciation_feedback

        if enable_pronunciation_feedback:
            self.pronunciation_analyzer = PronunciationAnalyzer(db=db)
            self.pronunciation_scorer = PronunciationScorer()

    def handle_audio_input(
        self,
        audio_input: Union[str, bytes],
        generate_audio_response: bool = True
    ) -> VoiceTurnResult:
        """
        Process a complete voice interaction turn.

        Pipeline:
        1. ASR: audio → text
        2. Tutor: text → TutorResponse
        3. TTS: TutorResponse.message → audio (optional)

        Args:
            audio_input: Path to audio file or audio bytes
            generate_audio_response: Whether to generate TTS audio

        Returns:
            VoiceTurnResult with recognized text, tutor response, and optional audio
        """
        start_time = time.time()

        # Step 1: ASR - transcribe audio to text
        if isinstance(audio_input, str):
            asr_result = asr_client.transcribe_file(audio_input)
        elif isinstance(audio_input, bytes):
            # Extract filename from context if available
            filename = self.context.get("filename", "audio.webm")
            asr_result = asr_client.transcribe_bytes(audio_input, filename=filename)
        else:
            raise ValueError(f"Invalid audio_input type: {type(audio_input)}")

        recognized_text = asr_result.text

        # Step 2: Pronunciation Analysis (if enabled)
        pronunciation_feedback = None
        phoneme_scores = None

        if self.enable_pronunciation_feedback and self.user_id:
            try:
                # Get reference text if available (e.g., from drill or lesson context)
                reference_text = self.context.get("reference_text", recognized_text)

                # Get detailed phoneme scores using pronunciation scorer
                import tempfile
                import os

                # Save audio to temp file for pronunciation scoring
                if isinstance(audio_input, bytes):
                    temp_audio_path = os.path.join(tempfile.gettempdir(), f"pron_{int(time.time())}.webm")
                    with open(temp_audio_path, 'wb') as f:
                        f.write(audio_input)
                    audio_path = temp_audio_path
                else:
                    audio_path = audio_input

                # Score pronunciation
                pron_score_result = self.pronunciation_scorer.score_audio(audio_path, reference_text)
                phoneme_scores = pron_score_result.get("phoneme_scores", [])

                # Analyze pronunciation and generate feedback
                pron_analysis = self.pronunciation_analyzer.analyze_pronunciation(
                    asr_result=asr_result,
                    reference_text=reference_text,
                    user_id=self.user_id,
                    phoneme_scores=phoneme_scores
                )

                # Store pronunciation attempt in database
                if self.db and phoneme_scores:
                    import psycopg
                    with self.db.get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                INSERT INTO pronunciation_attempts (user_id, phrase, phoneme_scores, overall_score)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (
                                    self.user_id,
                                    reference_text,
                                    psycopg.types.json.Json(phoneme_scores),
                                    pron_analysis.overall_score
                                )
                            )

                # Format feedback for tutor response
                pronunciation_feedback = {
                    "overall_score": pron_analysis.overall_score,
                    "encouragement": pron_analysis.encouragement,
                    "tips": [
                        {
                            "word": tip.word,
                            "issue": tip.issue,
                            "tip": tip.tip,
                            "phonetic": tip.phonetic,
                            "example": tip.example
                        }
                        for tip in pron_analysis.tips
                    ],
                    "problem_sounds": pron_analysis.problem_sounds,
                    "word_scores": [
                        {
                            "word": ws.word,
                            "score": ws.score,
                            "issues": ws.issues
                        }
                        for ws in pron_analysis.word_scores[:5]  # Top 5 words
                    ]
                }

                # Clean up temp file
                if isinstance(audio_input, bytes) and os.path.exists(temp_audio_path):
                    try:
                        os.remove(temp_audio_path)
                    except:
                        pass

            except Exception as e:
                print(f"Warning: Pronunciation analysis failed: {e}")
                # Continue without pronunciation feedback
                pronunciation_feedback = None

        # Step 3: Tutor - process text through tutor agent
        tutor_context = {
            "mode": self.mode,
            "level": self.user_level,
            **self.context
        }

        tutor_response = self.tutor.process_user_input(
            recognized_text,
            context=tutor_context
        )

        # Add pronunciation feedback to tutor response
        if pronunciation_feedback:
            tutor_response.pronunciation_feedback = pronunciation_feedback

            # Enhance tutor message with pronunciation tips if score is below 80
            if pronunciation_feedback["overall_score"] < 80 and pronunciation_feedback["tips"]:
                tip = pronunciation_feedback["tips"][0]
                pron_tip_text = f"\n\nPronunciation tip: {tip['tip']}"
                if tip.get("example"):
                    pron_tip_text += f" {tip['example']}"
                tutor_response.message += pron_tip_text

        # Step 4: TTS - synthesize tutor response (optional)
        tts_output_path = None

        if generate_audio_response and tutor_response.message:
            # Generate temp file for TTS output
            tts_output_path = self._generate_tts_output_path()

            tts_result = tts_client.synthesize_to_file(
                tutor_response.message,
                tts_output_path
            )

            # Use the file path from TTS result
            tts_output_path = tts_result.file_path

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        return VoiceTurnResult(
            recognized_text=recognized_text,
            tutor_response=tutor_response,
            tts_output_path=tts_output_path,
            asr_confidence=asr_result.confidence,
            processing_time_ms=processing_time_ms
        )

    def _generate_tts_output_path(self) -> str:
        """Generate temporary path for TTS output."""
        # Create temp directory if needed
        temp_dir = Path(tempfile.gettempdir()) / "speaksharp" / "tts"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamped filename
        timestamp = int(time.time() * 1000)
        filename = f"tutor_response_{timestamp}.mp3"

        return str(temp_dir / filename)

    def handle_audio_input_streaming(
        self,
        audio_input: Union[str, bytes]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process voice input with streaming TTS response.

        Pipeline:
        1. ASR: audio → text (blocking)
        2. Tutor: text → TutorResponse (blocking)
        3. TTS: TutorResponse.message → streaming audio chunks

        Args:
            audio_input: Path to audio file or audio bytes

        Yields:
            Dictionaries with streaming response data:
            - type: "transcript" | "tutor_response" | "audio_start" | "audio_chunk" | "audio_end" | "complete"
            - data: Relevant data for the event type

        This enables the client to:
        - Display transcript immediately after ASR
        - Show tutor response text immediately
        - Start playing audio as soon as first chunk arrives
        """
        start_time = time.time()

        # Step 1: ASR - transcribe audio to text
        if isinstance(audio_input, str):
            asr_result = asr_client.transcribe_file(audio_input)
        elif isinstance(audio_input, bytes):
            filename = self.context.get("filename", "audio.webm")
            asr_result = asr_client.transcribe_bytes(audio_input, filename=filename)
        else:
            raise ValueError(f"Invalid audio_input type: {type(audio_input)}")

        recognized_text = asr_result.text

        # Yield transcript immediately
        yield {
            "type": "transcript",
            "data": {
                "text": recognized_text,
                "confidence": asr_result.confidence
            }
        }

        # Step 2: Tutor - process text through tutor agent
        tutor_context = {
            "mode": self.mode,
            "level": self.user_level,
            **self.context
        }

        tutor_response = self.tutor.process_user_input(
            recognized_text,
            context=tutor_context
        )

        # Yield tutor response immediately
        yield {
            "type": "tutor_response",
            "data": {
                "message": tutor_response.message,
                "errors": [
                    {
                        "type": e.type.value,
                        "user_sentence": e.user_sentence,
                        "corrected_sentence": e.corrected_sentence,
                        "explanation": e.explanation
                    }
                    for e in tutor_response.errors
                ],
                "micro_task": tutor_response.micro_task
            }
        }

        # Step 3: TTS - stream audio response
        if tutor_response.message:
            yield {
                "type": "audio_start",
                "data": {
                    "text": tutor_response.message
                }
            }

            # Stream audio chunks
            for chunk in tts_client.synthesize_streaming(tutor_response.message):
                yield {
                    "type": "audio_chunk",
                    "data": {
                        "chunk": chunk
                    }
                }

            yield {
                "type": "audio_end",
                "data": {}
            }

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Yield completion
        yield {
            "type": "complete",
            "data": {
                "processing_time_ms": processing_time_ms,
                "asr_confidence": asr_result.confidence
            }
        }

    def handle_audio_input_streaming_sentences(
        self,
        audio_input: Union[str, bytes]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process voice input with sentence-by-sentence streaming TTS.

        This provides the lowest perceived latency by streaming audio
        sentence-by-sentence as soon as each sentence is synthesized.

        Pipeline:
        1. ASR: audio → text (blocking)
        2. Tutor: text → TutorResponse (blocking)
        3. TTS: Stream each sentence separately

        Args:
            audio_input: Path to audio file or audio bytes

        Yields:
            Dictionaries with streaming response data including sentence boundaries
        """
        start_time = time.time()

        # Step 1: ASR
        if isinstance(audio_input, str):
            asr_result = asr_client.transcribe_file(audio_input)
        elif isinstance(audio_input, bytes):
            filename = self.context.get("filename", "audio.webm")
            asr_result = asr_client.transcribe_bytes(audio_input, filename=filename)
        else:
            raise ValueError(f"Invalid audio_input type: {type(audio_input)}")

        # Yield transcript
        yield {
            "type": "transcript",
            "data": {
                "text": asr_result.text,
                "confidence": asr_result.confidence
            }
        }

        # Step 2: Tutor
        tutor_context = {
            "mode": self.mode,
            "level": self.user_level,
            **self.context
        }

        tutor_response = self.tutor.process_user_input(
            asr_result.text,
            context=tutor_context
        )

        # Yield tutor response
        yield {
            "type": "tutor_response",
            "data": {
                "message": tutor_response.message,
                "errors": [
                    {
                        "type": e.type.value,
                        "user_sentence": e.user_sentence,
                        "corrected_sentence": e.corrected_sentence,
                        "explanation": e.explanation
                    }
                    for e in tutor_response.errors
                ],
                "micro_task": tutor_response.micro_task
            }
        }

        # Step 3: Stream TTS sentence-by-sentence
        if tutor_response.message:
            for sentence_text, audio_chunks in tts_client.synthesize_sentences_streaming(
                tutor_response.message
            ):
                # Signal sentence start
                yield {
                    "type": "sentence_start",
                    "data": {
                        "text": sentence_text
                    }
                }

                # Stream audio chunks for this sentence
                for chunk in audio_chunks:
                    yield {
                        "type": "audio_chunk",
                        "data": {
                            "chunk": chunk
                        }
                    }

                # Signal sentence end
                yield {
                    "type": "sentence_end",
                    "data": {}
                }

        # Completion
        yield {
            "type": "complete",
            "data": {
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "asr_confidence": asr_result.confidence
            }
        }


if __name__ == "__main__":
    from uuid import uuid4

    print("Voice Session Test")
    print("=" * 60)

    # Create test session
    user_id = uuid4()

    print("\n📝 Test 1: Free chat mode")
    print("-" * 60)

    session = VoiceSession(
        user_id=user_id,
        mode="free_chat"
    )

    # Test with stub audio file path
    result = session.handle_audio_input("/tmp/test_audio.mp3")

    print(f"Recognized: {result.recognized_text}")
    print(f"Tutor: {result.tutor_response.message}")
    print(f"Errors found: {len(result.tutor_response.errors)}")
    if result.tutor_response.errors:
        for error in result.tutor_response.errors[:2]:
            print(f"  • {error.type.value}: {error.explanation[:60]}...")
    print(f"TTS output: {result.tts_output_path}")
    print(f"Processing time: {result.processing_time_ms}ms")

    print("\n📝 Test 2: Scenario mode")
    print("-" * 60)

    session = VoiceSession(
        user_id=user_id,
        mode="scenario",
        context={"scenario_id": "cafe_ordering"}
    )

    result = session.handle_audio_input("/tmp/cafe_order.mp3")

    print(f"Recognized: {result.recognized_text}")
    print(f"Tutor: {result.tutor_response.message}")
    print(f"Errors found: {len(result.tutor_response.errors)}")
    print(f"TTS output: {result.tts_output_path}")
    print(f"Confidence: {result.asr_confidence}")

    print("\n📝 Test 3: Drill mode (without TTS)")
    print("-" * 60)

    session = VoiceSession(
        user_id=user_id,
        mode="drill",
        context={"drill_type": "monologue"}
    )

    result = session.handle_audio_input(
        "/tmp/weekend_story.mp3",
        generate_audio_response=False
    )

    print(f"Recognized: {result.recognized_text}")
    print(f"Tutor: {result.tutor_response.message}")
    print(f"Errors found: {len(result.tutor_response.errors)}")
    print(f"TTS output: {result.tts_output_path}")  # Should be None
    print(f"Processing time: {result.processing_time_ms}ms")

    print("\n" + "=" * 60)
    print("✅ Voice Session tests complete!")
    print("\nNote: Tests run in stub mode by default.")
    print("Set OPENAI_API_KEY to test with real ASR/TTS.")
