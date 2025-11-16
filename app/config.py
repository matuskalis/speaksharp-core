"""
Configuration management for SpeakSharp Core.

Handles API keys, environment variables, and system settings.
"""

import os
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM API configuration."""
    provider: str = "openai"  # "openai" or "anthropic"
    api_key: Optional[str] = None
    model: str = "gpt-4o-mini"  # Default to cost-effective model
    temperature: float = 0.7
    max_tokens: int = 500
    timeout: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds


class ASRConfig(BaseModel):
    """ASR (Automatic Speech Recognition) configuration."""
    provider: str = "openai"  # "openai" (Whisper)
    api_key: Optional[str] = None
    model: str = "whisper-1"
    language: str = "en"  # ISO 639-1 language code
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class TTSConfig(BaseModel):
    """TTS (Text-to-Speech) configuration."""
    provider: str = "openai"  # "openai"
    api_key: Optional[str] = None
    model: str = "tts-1"  # or "tts-1-hd"
    voice: str = "alloy"  # alloy, echo, fable, onyx, nova, shimmer
    speed: float = 1.0  # 0.25 to 4.0
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class AppConfig(BaseModel):
    """Application configuration."""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    asr: ASRConfig = Field(default_factory=ASRConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    enable_llm: bool = True  # Toggle for stub vs real LLM
    enable_asr: bool = True  # Toggle for stub vs real ASR
    enable_tts: bool = True  # Toggle for stub vs real TTS
    log_api_calls: bool = False
    debug_mode: bool = False


def load_config() -> AppConfig:
    """
    Load configuration from environment variables.

    Environment variables:
    - SPEAKSHARP_LLM_PROVIDER: "openai" or "anthropic"
    - OPENAI_API_KEY: OpenAI API key
    - ANTHROPIC_API_KEY: Anthropic API key
    - SPEAKSHARP_LLM_MODEL: Model name override
    - SPEAKSHARP_ENABLE_LLM: "true" or "false"
    - SPEAKSHARP_ASR_PROVIDER: "openai"
    - SPEAKSHARP_ASR_MODEL: Model name override
    - SPEAKSHARP_ASR_LANGUAGE: Language code (default: en)
    - SPEAKSHARP_ENABLE_ASR: "true" or "false"
    - SPEAKSHARP_TTS_PROVIDER: "openai"
    - SPEAKSHARP_TTS_MODEL: Model name override
    - SPEAKSHARP_TTS_VOICE: Voice name
    - SPEAKSHARP_TTS_SPEED: Speed (0.25-4.0)
    - SPEAKSHARP_ENABLE_TTS: "true" or "false"
    - SPEAKSHARP_DEBUG: "true" or "false"
    """
    # LLM configuration
    llm_provider = os.getenv("SPEAKSHARP_LLM_PROVIDER", "openai")

    if llm_provider == "openai":
        llm_api_key = os.getenv("OPENAI_API_KEY")
    elif llm_provider == "anthropic":
        llm_api_key = os.getenv("ANTHROPIC_API_KEY")
    else:
        llm_api_key = None

    llm_model = os.getenv("SPEAKSHARP_LLM_MODEL")
    if not llm_model:
        if llm_provider == "openai":
            llm_model = "gpt-4o-mini"
        elif llm_provider == "anthropic":
            llm_model = "claude-3-5-haiku-20241022"
        else:
            llm_model = "gpt-4o-mini"

    # ASR configuration
    asr_provider = os.getenv("SPEAKSHARP_ASR_PROVIDER", "openai")

    if asr_provider == "openai":
        asr_api_key = os.getenv("OPENAI_API_KEY")
    else:
        asr_api_key = None

    asr_model = os.getenv("SPEAKSHARP_ASR_MODEL", "whisper-1")
    asr_language = os.getenv("SPEAKSHARP_ASR_LANGUAGE", "en")

    # TTS configuration
    tts_provider = os.getenv("SPEAKSHARP_TTS_PROVIDER", "openai")

    if tts_provider == "openai":
        tts_api_key = os.getenv("OPENAI_API_KEY")
    else:
        tts_api_key = None

    tts_model = os.getenv("SPEAKSHARP_TTS_MODEL", "tts-1")
    tts_voice = os.getenv("SPEAKSHARP_TTS_VOICE", "alloy")
    tts_speed = float(os.getenv("SPEAKSHARP_TTS_SPEED", "1.0"))

    # Feature flags
    enable_llm = os.getenv("SPEAKSHARP_ENABLE_LLM", "true").lower() == "true"
    enable_asr = os.getenv("SPEAKSHARP_ENABLE_ASR", "true").lower() == "true"
    enable_tts = os.getenv("SPEAKSHARP_ENABLE_TTS", "true").lower() == "true"
    debug_mode = os.getenv("SPEAKSHARP_DEBUG", "false").lower() == "true"
    log_api_calls = os.getenv("SPEAKSHARP_LOG_API", "false").lower() == "true"

    llm_config = LLMConfig(
        provider=llm_provider,
        api_key=llm_api_key,
        model=llm_model,
        temperature=float(os.getenv("SPEAKSHARP_LLM_TEMP", "0.7")),
        max_tokens=int(os.getenv("SPEAKSHARP_LLM_MAX_TOKENS", "500")),
        timeout=int(os.getenv("SPEAKSHARP_LLM_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("SPEAKSHARP_LLM_RETRY", "3")),
    )

    asr_config = ASRConfig(
        provider=asr_provider,
        api_key=asr_api_key,
        model=asr_model,
        language=asr_language,
        timeout=int(os.getenv("SPEAKSHARP_ASR_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("SPEAKSHARP_ASR_RETRY", "3")),
    )

    tts_config = TTSConfig(
        provider=tts_provider,
        api_key=tts_api_key,
        model=tts_model,
        voice=tts_voice,
        speed=tts_speed,
        timeout=int(os.getenv("SPEAKSHARP_TTS_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("SPEAKSHARP_TTS_RETRY", "3")),
    )

    return AppConfig(
        llm=llm_config,
        asr=asr_config,
        tts=tts_config,
        enable_llm=enable_llm,
        enable_asr=enable_asr,
        enable_tts=enable_tts,
        log_api_calls=log_api_calls,
        debug_mode=debug_mode
    )


# Global config instance
config = load_config()


if __name__ == "__main__":
    print("SpeakSharp Configuration Test")
    print("=" * 60)

    cfg = load_config()

    print("\n🔧 LLM Configuration:")
    print(f"  Provider: {cfg.llm.provider}")
    print(f"  Model: {cfg.llm.model}")
    print(f"  API Key: {'✓ Set' if cfg.llm.api_key else '✗ Not set'}")
    print(f"  Temperature: {cfg.llm.temperature}")
    print(f"  Max Tokens: {cfg.llm.max_tokens}")
    print(f"  Timeout: {cfg.llm.timeout}s")

    print("\n🎤 ASR Configuration:")
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

    print("\n🎛 App Settings:")
    print(f"  Enable LLM: {cfg.enable_llm}")
    print(f"  Enable ASR: {cfg.enable_asr}")
    print(f"  Enable TTS: {cfg.enable_tts}")
    print(f"  Log API Calls: {cfg.log_api_calls}")
    print(f"  Debug Mode: {cfg.debug_mode}")

    print("\n" + "=" * 60)

    warnings = []
    if not cfg.llm.api_key and cfg.enable_llm:
        warnings.append(f"LLM enabled but no API key set (need {cfg.llm.provider.upper()}_API_KEY)")
    if not cfg.asr.api_key and cfg.enable_asr:
        warnings.append(f"ASR enabled but no API key set (need OPENAI_API_KEY)")
    if not cfg.tts.api_key and cfg.enable_tts:
        warnings.append(f"TTS enabled but no API key set (need OPENAI_API_KEY)")

    if warnings:
        print("\n⚠️  Warnings:")
        for w in warnings:
            print(f"   • {w}")
        print("\n   Running in STUB mode for missing keys.")
    else:
        print("\n✅ Configuration loaded successfully!")
