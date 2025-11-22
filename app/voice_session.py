"""
Voice session orchestration for SpeakSharp.

Wires together ASR, TutorAgent, and TTS into a complete voice interaction.
"""

import time
import tempfile
from pathlib import Path
from typing import Union, Optional, Dict, Any, Literal
from uuid import UUID

from app.asr_client import asr_client
from app.tts_client import tts_client
from app.tutor_agent import TutorAgent
from app.models import VoiceTurnResult, TutorResponse


class VoiceSession:
    """
    Orchestrates a voice interaction: ASR → Tutor → TTS.

    Handles audio input, processes through tutor, and generates audio response.
    """

    def __init__(
        self,
        user_level: str = "A1",
        mode: Literal["scenario", "free_chat", "drill", "lesson"] = "free_chat",
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize voice session.

        Args:
            user_level: User's CEFR level (A1-C2)
            mode: Session mode (scenario, free_chat, drill, lesson)
            context: Optional context dict (scenario_id, drill_type, etc.)
        """
        self.user_level = user_level
        self.mode = mode
        self.context = context or {}
        self.tutor = TutorAgent()

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

        # Step 3: TTS - synthesize tutor response (optional)
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
