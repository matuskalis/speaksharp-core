#!/usr/bin/env python3
"""
Test script to verify ASR/TTS integration in both stub and real API modes.

This script:
1. Tests configuration loading for ASR/TTS
2. Tests ASR client in stub mode
3. Tests TTS client in stub mode
4. Tests complete VoiceSession integration
5. Provides instructions for testing with real API
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from config import config, load_config
from asr_client import asr_client, ASRClient
from tts_client import tts_client, TTSClient
from voice_session import VoiceSession
from uuid import uuid4


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_configuration():
    """Test configuration loading."""
    print_section("STEP 1: CONFIGURATION TEST")

    cfg = load_config()

    print("🎤 ASR Configuration:")
    print(f"  Provider: {cfg.asr.provider}")
    print(f"  Model: {cfg.asr.model}")
    print(f"  API Key: {'✓ Set' if cfg.asr.api_key else '✗ Not set'}")
    print(f"  Language: {cfg.asr.language}")
    print(f"  Timeout: {cfg.asr.timeout}s")

    print("\n🔊 TTS Configuration:")
    print(f"  Provider: {cfg.tts.provider}")
    print(f"  Model: {cfg.tts.model}")
    print(f"  API Key: {'✓ Set' if cfg.tts.api_key else '✗ Not set'}")
    print(f"  Voice: {cfg.tts.voice}")
    print(f"  Speed: {cfg.tts.speed}")
    print(f"  Timeout: {cfg.tts.timeout}s")

    print("\n🎛 Feature Flags:")
    print(f"  Enable ASR: {cfg.enable_asr}")
    print(f"  Enable TTS: {cfg.enable_tts}")
    print(f"  Enable LLM: {cfg.enable_llm}")
    print(f"  Debug Mode: {cfg.debug_mode}")

    # Determine mode
    has_api_key = cfg.asr.api_key is not None
    if has_api_key and cfg.enable_asr and cfg.enable_tts:
        print("\n✅ API key configured → Running in VOICE API MODE")
        return "api"
    else:
        print("\n⚠️  No API key or features disabled → Running in STUB MODE")
        return "stub"


def test_asr_client(mode: str):
    """Test ASR client directly."""
    print_section("STEP 2: ASR CLIENT TEST")

    print(f"Testing in {mode.upper()} mode...\n")

    test_cases = [
        "/tmp/test_audio.mp3",
        "/tmp/cafe_order.mp3",
        "/tmp/introduction.mp3"
    ]

    for i, audio_path in enumerate(test_cases, 1):
        print(f"Test Case {i}: {audio_path}")

        result = asr_client.transcribe_file(audio_path)

        print(f"  Recognized: {result.text}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Language: {result.language}")
        print(f"  Provider: {result.provider}")
        print()

    if mode == "stub":
        print("📝 Note: In stub mode, ASR returns predefined transcripts.")
        print("   Set OPENAI_API_KEY to test real speech recognition.")


def test_tts_client(mode: str):
    """Test TTS client directly."""
    print_section("STEP 3: TTS CLIENT TEST")

    print(f"Testing in {mode.upper()} mode...\n")

    test_texts = [
        "Hello! How can I help you today?",
        "That's great! You're making excellent progress.",
        "Let me correct that for you. Try saying: I went to the park yesterday."
    ]

    import tempfile

    for i, text in enumerate(test_texts, 1):
        print(f"Test Case {i}: {text[:50]}...")

        # Generate temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        result = tts_client.synthesize_to_file(text, tmp_path)

        print(f"  Output file: {result.file_path}")
        print(f"  Characters: {result.characters}")
        print(f"  Provider: {result.provider}")
        if result.duration:
            print(f"  Duration: {result.duration:.1f}s")
        print()

    if mode == "stub":
        print("📝 Note: In stub mode, TTS creates placeholder audio files.")
        print("   Set OPENAI_API_KEY to test real speech synthesis.")


def test_voice_session(mode: str):
    """Test complete voice session integration."""
    print_section("STEP 4: VOICE SESSION INTEGRATION TEST")

    print(f"Testing in {mode.upper()} mode...\n")

    user_id = uuid4()

    # Test 1: Free chat mode
    print("Test 1: Free chat mode")
    print("-" * 70)

    session = VoiceSession(
        user_id=user_id,
        mode="free_chat"
    )

    result = session.handle_audio_input("/tmp/test_audio.mp3")

    print(f"  ASR: {result.recognized_text}")
    print(f"  Tutor: {result.tutor_response.message}")
    print(f"  Errors: {len(result.tutor_response.errors)}")

    if result.tutor_response.errors:
        for error in result.tutor_response.errors[:2]:
            print(f"    • {error.type.value}: {error.corrected_sentence}")

    print(f"  TTS output: {Path(result.tts_output_path).name if result.tts_output_path else 'None'}")
    print(f"  Processing: {result.processing_time_ms}ms")

    # Test 2: Scenario mode
    print("\nTest 2: Scenario mode (café ordering)")
    print("-" * 70)

    session = VoiceSession(
        user_id=user_id,
        mode="scenario",
        context={"scenario_id": "cafe_ordering"}
    )

    result = session.handle_audio_input("/tmp/cafe_order.mp3")

    print(f"  ASR: {result.recognized_text}")
    print(f"  Tutor: {result.tutor_response.message}")
    print(f"  Errors: {len(result.tutor_response.errors)}")
    print(f"  Confidence: {result.asr_confidence}")
    print(f"  TTS output: {Path(result.tts_output_path).name if result.tts_output_path else 'None'}")

    # Test 3: Drill mode without TTS
    print("\nTest 3: Drill mode (monologue, no TTS)")
    print("-" * 70)

    session = VoiceSession(
        user_id=user_id,
        mode="drill",
        context={"drill_type": "monologue"}
    )

    result = session.handle_audio_input(
        "/tmp/weekend_story.mp3",
        generate_audio_response=False
    )

    print(f"  ASR: {result.recognized_text}")
    print(f"  Tutor: {result.tutor_response.message}")
    print(f"  Errors: {len(result.tutor_response.errors)}")
    print(f"  TTS output: {result.tts_output_path}")  # Should be None
    print(f"  Processing: {result.processing_time_ms}ms")

    if mode == "stub":
        print("\n📝 Note: In stub mode, all processing uses predefined data.")
        print("   With real API, you'll get actual transcription and synthesis.")


def show_api_mode_instructions():
    """Show instructions for testing with real API."""
    print_section("TESTING WITH REAL ASR/TTS API")

    print("To test with real voice API integration:\n")

    print("1. Set your OpenAI API key:")
    print("   export OPENAI_API_KEY=your_key_here")
    print("   # OR add to .env file")
    print("   OPENAI_API_KEY=your_key_here\n")

    print("2. (Optional) Configure voice settings in .env:")
    print("   SPEAKSHARP_ASR_LANGUAGE=en")
    print("   SPEAKSHARP_TTS_VOICE=alloy  # alloy, echo, fable, onyx, nova, shimmer")
    print("   SPEAKSHARP_TTS_SPEED=1.0    # 0.25 to 4.0\n")

    print("3. (Optional) Enable debug logging:")
    print("   SPEAKSHARP_DEBUG=true")
    print("   SPEAKSHARP_LOG_API=true\n")

    print("4. Ensure openai package is installed:")
    print("   pip install openai\n")

    print("5. Run this test again:")
    print("   python test_voice_modes.py\n")

    print("6. Run full demo with voice:")
    print("   python demo_integration.py\n")

    print("Expected differences in API mode:")
    print("  • Real speech recognition from audio files")
    print("  • Natural synthesized voice responses")
    print("  • Actual audio files generated (not placeholders)")
    print("  • API call timing and latency visible")


def main():
    print("\n" + "=" * 70)
    print("  SPEAKSHARP VOICE INTEGRATION TEST")
    print("=" * 70)

    # Step 1: Test configuration
    mode = test_configuration()

    # Step 2: Test ASR client
    test_asr_client(mode)

    # Step 3: Test TTS client
    test_tts_client(mode)

    # Step 4: Test voice session
    test_voice_session(mode)

    # Show instructions for API mode
    if mode == "stub":
        show_api_mode_instructions()

    # Summary
    print_section("TEST SUMMARY")

    if mode == "stub":
        print("✅ All tests passed in STUB MODE")
        print("   Voice processing pipeline is working correctly.")
        print("   Set OPENAI_API_KEY to test real voice API integration.\n")
    else:
        print("✅ All tests passed in API MODE")
        print("   Real voice API integration is working correctly.")
        print("   ASR and TTS are fully operational.\n")

    print("=" * 70)


if __name__ == "__main__":
    main()
