"""
Audio Quality Detection for Vorex.

Analyzes audio quality to detect poor microphone conditions
that could affect pronunciation scoring accuracy.
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass


@dataclass
class AudioQualityResult:
    """Result of audio quality analysis."""
    snr_db: float  # Signal-to-noise ratio in decibels
    clipping_detected: bool  # Whether audio clipping was detected
    quality: str  # "good", "fair", or "poor"
    recommendation: Optional[str]  # Suggestion for user if quality is poor

    def to_dict(self) -> dict:
        return {
            "snr_db": round(self.snr_db, 1),
            "clipping_detected": self.clipping_detected,
            "quality": self.quality,
            "recommendation": self.recommendation
        }


def analyze_audio_quality_from_bytes(audio_bytes: bytes) -> AudioQualityResult:
    """
    Analyze audio quality from raw bytes.

    Args:
        audio_bytes: Raw audio data as bytes

    Returns:
        AudioQualityResult with quality metrics
    """
    try:
        import io
        import soundfile as sf

        # Read audio from bytes
        audio_buffer = io.BytesIO(audio_bytes)
        y, sr = sf.read(audio_buffer)

        # Convert to mono if stereo
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)

        return _analyze_signal(y)

    except ImportError:
        # soundfile not installed, return default good quality
        return AudioQualityResult(
            snr_db=20.0,
            clipping_detected=False,
            quality="good",
            recommendation=None
        )
    except Exception as e:
        # On any error, assume good quality to not block the user
        print(f"[AudioQuality] Error analyzing audio: {e}")
        return AudioQualityResult(
            snr_db=20.0,
            clipping_detected=False,
            quality="good",
            recommendation=None
        )


def analyze_audio_quality_from_file(file_path: str) -> AudioQualityResult:
    """
    Analyze audio quality from a file.

    Args:
        file_path: Path to audio file

    Returns:
        AudioQualityResult with quality metrics
    """
    try:
        import soundfile as sf

        # Read audio file
        y, sr = sf.read(file_path)

        # Convert to mono if stereo
        if len(y.shape) > 1:
            y = np.mean(y, axis=1)

        return _analyze_signal(y)

    except ImportError:
        return AudioQualityResult(
            snr_db=20.0,
            clipping_detected=False,
            quality="good",
            recommendation=None
        )
    except Exception as e:
        print(f"[AudioQuality] Error analyzing audio file: {e}")
        return AudioQualityResult(
            snr_db=20.0,
            clipping_detected=False,
            quality="good",
            recommendation=None
        )


def _analyze_signal(y: np.ndarray) -> AudioQualityResult:
    """
    Analyze audio signal for quality metrics.

    Args:
        y: Audio signal as numpy array (normalized to -1 to 1)

    Returns:
        AudioQualityResult with quality metrics
    """
    # Handle empty or very short audio
    if len(y) < 100:
        return AudioQualityResult(
            snr_db=0.0,
            clipping_detected=False,
            quality="poor",
            recommendation="Recording too short. Please try again."
        )

    # Calculate signal-to-noise ratio
    # Signal power: RMS of entire signal
    signal_power = np.mean(y ** 2)

    # Noise estimate: RMS of quietest 10% of samples (assumed to be noise floor)
    sorted_abs = np.sort(np.abs(y))
    noise_samples = sorted_abs[:int(len(sorted_abs) * 0.1)]
    noise_power = np.mean(noise_samples ** 2) if len(noise_samples) > 0 else 1e-10

    # SNR in decibels
    snr = 10 * np.log10(signal_power / (noise_power + 1e-10))

    # Clipping detection: samples very close to max amplitude
    clipping_ratio = np.sum(np.abs(y) > 0.99) / len(y)
    clipping_detected = clipping_ratio > 0.01  # More than 1% clipped

    # Determine overall quality
    if snr > 20 and not clipping_detected:
        quality = "good"
        recommendation = None
    elif snr > 10 and not clipping_detected:
        quality = "fair"
        recommendation = "Try moving to a quieter location for better results."
    else:
        quality = "poor"
        if clipping_detected:
            recommendation = "Audio is too loud. Please speak a bit softer or move away from the microphone."
        else:
            recommendation = "Audio quality is low. Try moving to a quieter location or check your microphone."

    return AudioQualityResult(
        snr_db=snr,
        clipping_detected=clipping_detected,
        quality=quality,
        recommendation=recommendation
    )


def should_penalize_pronunciation(audio_quality: AudioQualityResult) -> bool:
    """
    Determine if pronunciation scoring should be adjusted due to poor audio quality.

    Args:
        audio_quality: Result from audio quality analysis

    Returns:
        True if pronunciation scores should include a confidence penalty
    """
    return audio_quality.quality == "poor" or audio_quality.snr_db < 10
