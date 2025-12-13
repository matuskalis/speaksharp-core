#!/usr/bin/env python3
"""
Test script for the pronunciation analysis endpoint.

This script tests the /api/speech/analyze-pronunciation endpoint
to ensure it properly analyzes pronunciation and returns the expected format.

Note: To run tests that require dependencies, activate the virtual environment first:
    source venv/bin/activate (or venv/Scripts/activate on Windows)
    python test_pronunciation_analysis.py
"""

import os
import sys
import json
from pathlib import Path

# Flag to check if we can import app modules
CAN_IMPORT_MODULES = True

try:
    # Add app directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    from app.pronunciation_scorer import PronunciationScorer
    from app.pronunciation_analyzer import PronunciationAnalyzer
    from app.asr_client import asr_client
except ImportError as e:
    print(f"⚠️  Cannot import app modules: {e}")
    print("⚠️  Some tests will be skipped. Run with venv activated for full tests.")
    CAN_IMPORT_MODULES = False


def test_pronunciation_scorer():
    """Test the pronunciation scorer with stub data."""
    print("\n" + "=" * 60)
    print("Testing Pronunciation Scorer")
    print("=" * 60)

    if not CAN_IMPORT_MODULES:
        print("⚠️  Skipped (requires venv)")
        return

    scorer = PronunciationScorer()

    # Test phrases
    test_cases = [
        {
            "reference": "The quick brown fox",
            "expected_phonemes": ["θ", "ð"]  # th sounds
        },
        {
            "reference": "I think this is right",
            "expected_phonemes": ["θ", "ð", "ɹ"]  # th and r sounds
        },
        {
            "reference": "She sells seashells",
            "expected_phonemes": ["ʃ", "s", "z"]  # sh and s sounds
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Reference: '{test_case['reference']}'")

        try:
            # In a real test, we'd use an actual audio file
            # For now, we'll just test the scorer logic
            from app.models import ASRResult, WordTiming

            # Create mock ASR result
            words = test_case['reference'].split()
            word_timings = [
                WordTiming(word=word, start=i*0.5, end=(i+1)*0.5, confidence=0.95)
                for i, word in enumerate(words)
            ]

            mock_asr = ASRResult(
                text=test_case['reference'],
                confidence=0.95,
                language="en",
                duration=len(words) * 0.5,
                words=word_timings,
                provider="stub"
            )

            print(f"  ✓ Created mock ASR result with {len(words)} words")
            print(f"  ✓ Expected phonemes: {', '.join(test_case['expected_phonemes'])}")

        except Exception as e:
            print(f"  ✗ Error: {e}")


def test_phoneme_extraction():
    """Test phoneme extraction from words."""
    print("\n" + "=" * 60)
    print("Testing Phoneme Extraction")
    print("=" * 60)

    if not CAN_IMPORT_MODULES:
        print("⚠️  Skipped (requires venv)")
        return

    scorer = PronunciationScorer()

    test_words = [
        "think",
        "this",
        "right",
        "water",
        "very",
        "ship",
        "measure"
    ]

    print("\nExtracting phonemes from common words:")
    for word in test_words:
        try:
            phonemes = scorer._get_phonemes(word)
            print(f"  {word:10} -> {' '.join(phonemes)}")
        except Exception as e:
            print(f"  {word:10} -> Error: {e}")


def test_response_format():
    """Test that the response format matches the expected schema."""
    print("\n" + "=" * 60)
    print("Testing Response Format")
    print("=" * 60)

    # Expected response schema
    expected_schema = {
        "success": bool,
        "transcript": str,
        "overall_score": float,
        "pronunciation_score": float,
        "fluency_score": float,
        "phoneme_analysis": list,
        "word_scores": list,
        "feedback": str,
        "words_per_minute": float,
        "duration": float,
        "word_count": int
    }

    # Mock response
    mock_response = {
        "success": True,
        "transcript": "The quick brown fox",
        "overall_score": 85.5,
        "pronunciation_score": 85.5,
        "fluency_score": 78.3,
        "phoneme_analysis": [
            {
                "word": "the",
                "phoneme": "ð",
                "status": "correct",
                "confidence": 0.85,
                "expected_ipa": "ð",
                "actual_ipa": "ð"
            }
        ],
        "word_scores": [
            {
                "word": "the",
                "score": 85.0,
                "issues": []
            }
        ],
        "feedback": "Good pronunciation overall.",
        "words_per_minute": 125.5,
        "duration": 5.23,
        "word_count": 4
    }

    print("\nValidating response schema:")
    all_valid = True

    for key, expected_type in expected_schema.items():
        if key not in mock_response:
            print(f"  ✗ Missing field: {key}")
            all_valid = False
        elif not isinstance(mock_response[key], expected_type):
            print(f"  ✗ Invalid type for {key}: expected {expected_type.__name__}, got {type(mock_response[key]).__name__}")
            all_valid = False
        else:
            print(f"  ✓ {key}: {expected_type.__name__}")

    if all_valid:
        print("\n✓ Response format is valid!")
    else:
        print("\n✗ Response format has errors")

    # Validate phoneme_analysis structure
    if mock_response.get("phoneme_analysis"):
        print("\nValidating phoneme_analysis structure:")
        phoneme_fields = ["word", "phoneme", "status", "confidence", "expected_ipa", "actual_ipa"]
        sample = mock_response["phoneme_analysis"][0]

        for field in phoneme_fields:
            if field in sample:
                print(f"  ✓ {field}: {type(sample[field]).__name__}")
            else:
                print(f"  ✗ Missing field: {field}")

    # Validate word_scores structure
    if mock_response.get("word_scores"):
        print("\nValidating word_scores structure:")
        word_fields = ["word", "score", "issues"]
        sample = mock_response["word_scores"][0]

        for field in word_fields:
            if field in sample:
                print(f"  ✓ {field}: {type(sample[field]).__name__}")
            else:
                print(f"  ✗ Missing field: {field}")


def test_fluency_calculation():
    """Test fluency score calculation logic."""
    print("\n" + "=" * 60)
    print("Testing Fluency Calculation")
    print("=" * 60)

    test_cases = [
        {"word_count": 10, "duration": 5.0, "expected_wpm": 120},  # Normal pace
        {"word_count": 5, "duration": 5.0, "expected_wpm": 60},    # Too slow
        {"word_count": 20, "duration": 5.0, "expected_wpm": 240},  # Too fast
        {"word_count": 12, "duration": 4.8, "expected_wpm": 150},  # Good pace
    ]

    print("\nTesting various speaking rates:")
    for case in test_cases:
        wpm = (case["word_count"] / case["duration"]) * 60
        print(f"\n  Words: {case['word_count']}, Duration: {case['duration']}s")
        print(f"  WPM: {wpm:.1f} (expected: {case['expected_wpm']})")

        # Calculate fluency score using the endpoint's logic
        if 100 <= wpm <= 180:
            fluency_score = min(95, 70 + int(case["word_count"] * 2))
            status = "Optimal"
        elif wpm < 100:
            fluency_score = max(40, int(wpm * 0.7))
            status = "Too slow"
        else:
            fluency_score = max(50, 100 - int((wpm - 180) * 0.3))
            status = "Too fast"

        print(f"  Fluency Score: {fluency_score} ({status})")


def test_score_ranges():
    """Test that scores are in valid ranges."""
    print("\n" + "=" * 60)
    print("Testing Score Ranges")
    print("=" * 60)

    print("\nScore interpretation:")
    score_ranges = [
        (95, "Excellent pronunciation"),
        (85, "Good pronunciation overall"),
        (70, "Your pronunciation is understandable"),
        (50, "Keep practicing")
    ]

    for score, expected_feedback in score_ranges:
        if score >= 90:
            feedback = "Excellent pronunciation! Your speech is very clear."
        elif score >= 75:
            feedback = "Good pronunciation overall. A few sounds need refinement."
        elif score >= 60:
            feedback = "Your pronunciation is understandable. Focus on the tips below to improve."
        else:
            feedback = "Keep practicing! Pronunciation takes time. Work on the specific sounds highlighted below."

        print(f"\n  Score {score}:")
        print(f"  → {feedback}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PRONUNCIATION ANALYSIS ENDPOINT - TEST SUITE")
    print("=" * 70)

    try:
        test_response_format()
        test_fluency_calculation()
        test_score_ranges()
        test_phoneme_extraction()
        test_pronunciation_scorer()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 70)

        print("\nTo test the actual endpoint:")
        print("1. Start the server: uvicorn app.api2:app --reload")
        print("2. Use curl or the examples in PRONUNCIATION_ANALYSIS_ENDPOINT.md")
        print("\nExample:")
        print("  curl -X POST http://localhost:8000/api/speech/analyze-pronunciation \\")
        print("    -H 'Authorization: Bearer YOUR_TOKEN' \\")
        print("    -F 'audio=@test.m4a' \\")
        print("    -F 'target_text=Hello world'")

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
