"""
TTS (Text-to-Speech) client for SpeakSharp.

Supports OpenAI TTS with stub mode fallback.
"""

import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.config import config
from app.models import TTSResult


class TTSClient:
    """Wrapper for TTS API calls with retry logic and error handling."""

    def __init__(self):
        self.config = config.tts
        self.provider = self.config.provider
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate TTS client."""
        if not self.config.api_key:
            if config.enable_tts and config.debug_mode:
                print("⚠️  Warning: No TTS API key configured, using stub mode")
            return

        if self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.config.api_key)
            except ImportError:
                if config.debug_mode:
                    print("⚠️  openai package not installed. Install with: pip install openai")
                self.client = None

    def synthesize_to_file(self, text: str, output_path: str) -> TTSResult:
        """
        Synthesize text to speech and save to file.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file (will be .mp3)

        Returns:
            TTSResult with file path and metadata
        """
        if not config.enable_tts or not self.client:
            return self._stub_synthesize_to_file(text, output_path)

        for attempt in range(self.config.retry_attempts):
            try:
                if self.provider == "openai":
                    return self._synthesize_openai_to_file(text, output_path)
                else:
                    return self._stub_synthesize_to_file(text, output_path)

            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    if config.debug_mode:
                        print(f"⚠️  TTS call failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    if config.debug_mode:
                        print(f"❌ TTS call failed after {self.config.retry_attempts} attempts: {e}")
                    return self._stub_synthesize_to_file(text, output_path)

        return self._stub_synthesize_to_file(text, output_path)

    def synthesize_to_bytes(self, text: str) -> TTSResult:
        """
        Synthesize text to speech and return audio bytes.

        Args:
            text: Text to synthesize

        Returns:
            TTSResult with audio bytes and metadata
        """
        if not config.enable_tts or not self.client:
            return self._stub_synthesize_to_bytes(text)

        for attempt in range(self.config.retry_attempts):
            try:
                if self.provider == "openai":
                    return self._synthesize_openai_to_bytes(text)
                else:
                    return self._stub_synthesize_to_bytes(text)

            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    if config.debug_mode:
                        print(f"⚠️  TTS call failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    if config.debug_mode:
                        print(f"❌ TTS call failed after {self.config.retry_attempts} attempts: {e}")
                    return self._stub_synthesize_to_bytes(text)

        return self._stub_synthesize_to_bytes(text)

    def _synthesize_openai_to_file(self, text: str, output_path: str) -> TTSResult:
        """Synthesize using OpenAI TTS API and save to file."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] OpenAI TTS API call: {len(text)} chars")

        response = self.client.audio.speech.create(
            model=self.config.model,
            voice=self.config.voice,
            input=text,
            speed=self.config.speed,
            timeout=self.config.timeout
        )

        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Stream to file
        response.stream_to_file(output_path)

        return TTSResult(
            audio_bytes=None,
            file_path=output_path,
            provider="openai",
            duration=None,  # OpenAI doesn't provide duration
            characters=len(text)
        )

    def _synthesize_openai_to_bytes(self, text: str) -> TTSResult:
        """Synthesize using OpenAI TTS API and return bytes."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] OpenAI TTS API call: {len(text)} chars")

        response = self.client.audio.speech.create(
            model=self.config.model,
            voice=self.config.voice,
            input=text,
            speed=self.config.speed,
            timeout=self.config.timeout
        )

        # Read response bytes
        audio_bytes = response.read()

        return TTSResult(
            audio_bytes=audio_bytes,
            file_path=None,
            provider="openai",
            duration=None,
            characters=len(text)
        )

    def _stub_synthesize_to_file(self, text: str, output_path: str) -> TTSResult:
        """Stub synthesis for testing without API - creates placeholder file."""
        # Create placeholder audio file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write small placeholder
        placeholder = f"STUB AUDIO: {text[:50]}..."
        with open(output_path, "w") as f:
            f.write(placeholder)

        return TTSResult(
            audio_bytes=None,
            file_path=output_path,
            provider="stub",
            duration=len(text) / 150.0,  # Estimate ~150 chars per second
            characters=len(text)
        )

    def _stub_synthesize_to_bytes(self, text: str) -> TTSResult:
        """Stub synthesis to bytes."""
        placeholder = f"STUB AUDIO: {text[:50]}...".encode()

        return TTSResult(
            audio_bytes=placeholder,
            file_path=None,
            provider="stub",
            duration=len(text) / 150.0,
            characters=len(text)
        )


# Global client instance
tts_client = TTSClient()


if __name__ == "__main__":
    import tempfile

    print("TTS Client Test")
    print("=" * 60)

    print(f"\n🔧 Configuration:")
    print(f"  Provider: {config.tts.provider}")
    print(f"  Model: {config.tts.model}")
    print(f"  API Key: {'✓ Set' if config.tts.api_key else '✗ Not set'}")
    print(f"  Voice: {config.tts.voice}")
    print(f"  Speed: {config.tts.speed}")
    print(f"  TTS Enabled: {config.enable_tts}")

    print(f"\n📝 Testing stub mode...")
    client = TTSClient()

    # Test file synthesis
    test_texts = [
        "Hello! How can I help you today?",
        "I'd like to order a large cappuccino, please.",
        "Great job! You're making excellent progress with your English."
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text[:40]}...")

        # Test to file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        result = client.synthesize_to_file(text, tmp_path)
        print(f"  File: {result.file_path}")
        print(f"  Characters: {result.characters}")
        print(f"  Provider: {result.provider}")
        print(f"  Duration: {result.duration:.1f}s" if result.duration else "  Duration: N/A")

    # Test to bytes
    print(f"\nTest: synthesize_to_bytes")
    result = client.synthesize_to_bytes("This is a test.")
    print(f"  Bytes length: {len(result.audio_bytes) if result.audio_bytes else 0}")
    print(f"  Provider: {result.provider}")

    print("\n" + "=" * 60)
    print("✅ TTS Client initialized successfully!")

    if not config.tts.api_key and config.enable_tts:
        print("\n⚠️  Note: Running in stub mode. Set OPENAI_API_KEY to test real TTS.")
