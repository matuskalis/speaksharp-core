"""
ASR (Automatic Speech Recognition) client for SpeakSharp.

Supports OpenAI Whisper with stub mode fallback.
"""

import time
from pathlib import Path
from typing import Union
from datetime import datetime

from app.config import config
from app.models import ASRResult


class ASRClient:
    """Wrapper for ASR API calls with retry logic and error handling."""

    def __init__(self):
        self.config = config.asr
        self.provider = self.config.provider
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate ASR client."""
        if not self.config.api_key:
            if config.enable_asr and config.debug_mode:
                print("⚠️  Warning: No ASR API key configured, using stub mode")
            return

        if self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.config.api_key)
            except ImportError:
                if config.debug_mode:
                    print("⚠️  openai package not installed. Install with: pip install openai")
                self.client = None

    def transcribe_file(self, file_path: str) -> ASRResult:
        """
        Transcribe audio file to text.

        Args:
            file_path: Path to audio file (mp3, mp4, mpeg, mpga, m4a, wav, webm)

        Returns:
            ASRResult with transcribed text and metadata
        """
        if not config.enable_asr or not self.client:
            return self._stub_transcribe_file(file_path)

        for attempt in range(self.config.retry_attempts):
            try:
                if self.provider == "openai":
                    return self._transcribe_openai_file(file_path)
                else:
                    return self._stub_transcribe_file(file_path)

            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    if config.debug_mode:
                        print(f"⚠️  ASR call failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    if config.debug_mode:
                        print(f"❌ ASR call failed after {self.config.retry_attempts} attempts: {e}")
                    return self._stub_transcribe_file(file_path)

        return self._stub_transcribe_file(file_path)

    def transcribe_bytes(self, audio_bytes: bytes, filename: str = "audio.mp3") -> ASRResult:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Audio data as bytes
            filename: Filename hint for the audio format

        Returns:
            ASRResult with transcribed text and metadata
        """
        if not config.enable_asr or not self.client:
            return self._stub_transcribe_bytes(audio_bytes)

        for attempt in range(self.config.retry_attempts):
            try:
                if self.provider == "openai":
                    return self._transcribe_openai_bytes(audio_bytes, filename)
                else:
                    return self._stub_transcribe_bytes(audio_bytes)

            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    if config.debug_mode:
                        print(f"⚠️  ASR call failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    if config.debug_mode:
                        print(f"❌ ASR call failed after {self.config.retry_attempts} attempts: {e}")
                    return self._stub_transcribe_bytes(audio_bytes)

        return self._stub_transcribe_bytes(audio_bytes)

    def _transcribe_openai_file(self, file_path: str) -> ASRResult:
        """Transcribe using OpenAI Whisper API from file."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] OpenAI Whisper API call: {file_path}")

        with open(file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.config.model,
                file=audio_file,
                language=self.config.language,
                response_format="verbose_json",
                timeout=self.config.timeout
            )

        return ASRResult(
            text=response.text,
            confidence=None,  # Whisper doesn't provide overall confidence
            language=response.language if hasattr(response, 'language') else self.config.language,
            duration=response.duration if hasattr(response, 'duration') else None,
            words=None,  # Could parse segments if needed
            provider="openai"
        )

    def _transcribe_openai_bytes(self, audio_bytes: bytes, filename: str) -> ASRResult:
        """Transcribe using OpenAI Whisper API from bytes."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] OpenAI Whisper API call: {len(audio_bytes)} bytes")

        # OpenAI API expects a file-like object
        from io import BytesIO
        audio_file = BytesIO(audio_bytes)
        audio_file.name = filename

        response = self.client.audio.transcriptions.create(
            model=self.config.model,
            file=audio_file,
            language=self.config.language,
            response_format="verbose_json",
            timeout=self.config.timeout
        )

        return ASRResult(
            text=response.text,
            confidence=None,
            language=response.language if hasattr(response, 'language') else self.config.language,
            duration=response.duration if hasattr(response, 'duration') else None,
            words=None,
            provider="openai"
        )

    def _stub_transcribe_file(self, file_path: str) -> ASRResult:
        """Stub transcription for testing without API."""
        # Deterministic stub based on file name
        file_name = Path(file_path).stem

        stub_transcripts = {
            "test_audio": "Hello, I want to order a coffee please.",
            "cafe_order": "I'd like a large cappuccino and a croissant.",
            "introduction": "Hi, my name is Sarah. I'm from Brazil and I'm learning English.",
            "weekend_story": "Last weekend I went to the park with my friends. We played football and had a picnic.",
        }

        text = stub_transcripts.get(file_name, "This is a stub transcription for testing.")

        return ASRResult(
            text=text,
            confidence=0.95,
            language="en",
            duration=5.0,
            words=None,
            provider="stub"
        )

    def _stub_transcribe_bytes(self, audio_bytes: bytes) -> ASRResult:
        """Stub transcription from bytes."""
        return ASRResult(
            text="This is a stub transcription from audio bytes.",
            confidence=0.95,
            language="en",
            duration=5.0,
            words=None,
            provider="stub"
        )


# Global client instance
asr_client = ASRClient()


if __name__ == "__main__":
    print("ASR Client Test")
    print("=" * 60)

    print(f"\n🔧 Configuration:")
    print(f"  Provider: {config.asr.provider}")
    print(f"  Model: {config.asr.model}")
    print(f"  API Key: {'✓ Set' if config.asr.api_key else '✗ Not set'}")
    print(f"  Language: {config.asr.language}")
    print(f"  ASR Enabled: {config.enable_asr}")

    print(f"\n📝 Testing stub mode...")
    client = ASRClient()

    # Test file transcription
    test_files = ["test_audio", "cafe_order", "introduction"]

    for test_file in test_files:
        fake_path = f"/tmp/{test_file}.mp3"
        print(f"\nTest: {fake_path}")
        result = client.transcribe_file(fake_path)
        print(f"  Text: {result.text}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Provider: {result.provider}")

    # Test bytes transcription
    print(f"\nTest: transcribe_bytes")
    result = client.transcribe_bytes(b"fake audio bytes", "test.mp3")
    print(f"  Text: {result.text}")
    print(f"  Provider: {result.provider}")

    print("\n" + "=" * 60)
    print("✅ ASR Client initialized successfully!")

    if not config.asr.api_key and config.enable_asr:
        print("\n⚠️  Note: Running in stub mode. Set OPENAI_API_KEY to test real ASR.")
