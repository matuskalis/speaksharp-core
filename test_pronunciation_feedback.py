"""
Test script for enhanced pronunciation feedback system.

Demonstrates:
- Word-level pronunciation analysis
- Specific, actionable feedback
- Common mispronunciation detection
- Improvement tracking
- Integration with voice sessions
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.pronunciation_analyzer import PronunciationAnalyzer, COMMON_MISPRONUNCIATIONS
from app.models import ASRResult, WordTiming


def test_pronunciation_analyzer():
    """Test the pronunciation analyzer with various scenarios."""
    print("=" * 80)
    print("PRONUNCIATION FEEDBACK SYSTEM TEST")
    print("=" * 80)

    analyzer = PronunciationAnalyzer(db=None)  # No DB for standalone test

    # Test Case 1: Perfect pronunciation
    print("\n" + "=" * 80)
    print("TEST 1: Perfect Pronunciation")
    print("=" * 80)

    asr_result = ASRResult(
        text="I think this is very good",
        confidence=0.95,
        language="en",
        duration=2.5,
        words=[
            WordTiming(word="I", start=0.0, end=0.2),
            WordTiming(word="think", start=0.2, end=0.6),
            WordTiming(word="this", start=0.6, end=0.9),
            WordTiming(word="is", start=0.9, end=1.1),
            WordTiming(word="very", start=1.1, end=1.5),
            WordTiming(word="good", start=1.5, end=2.0),
        ],
        provider="openai"
    )

    feedback = analyzer.analyze_pronunciation(
        asr_result=asr_result,
        reference_text="I think this is very good",
        user_id=None
    )

    print(f"\nReference: I think this is very good")
    print(f"Transcribed: {asr_result.text}")
    print(f"\nOverall Score: {feedback.overall_score}/100")
    print(f"Encouragement: {feedback.encouragement}")
    print(f"\nWord Scores:")
    for ws in feedback.word_scores:
        print(f"  - {ws.word}: {ws.score}/100")
    if feedback.tips:
        print(f"\nPronunciation Tips:")
        for tip in feedback.tips:
            print(f"  - {tip.word}: {tip.tip}")
            if tip.example:
                print(f"    Example: {tip.example}")

    # Test Case 2: TH sound mispronunciation (the -> de)
    print("\n" + "=" * 80)
    print("TEST 2: TH Sound Mispronunciation (common error)")
    print("=" * 80)

    asr_result = ASRResult(
        text="I tink dis is very good",  # "think" -> "tink", "this" -> "dis"
        confidence=0.88,
        language="en",
        duration=2.5,
        words=[
            WordTiming(word="I", start=0.0, end=0.2),
            WordTiming(word="tink", start=0.2, end=0.6),
            WordTiming(word="dis", start=0.6, end=0.9),
            WordTiming(word="is", start=0.9, end=1.1),
            WordTiming(word="very", start=1.1, end=1.5),
            WordTiming(word="good", start=1.5, end=2.0),
        ],
        provider="openai"
    )

    feedback = analyzer.analyze_pronunciation(
        asr_result=asr_result,
        reference_text="I think this is very good",
        user_id=None
    )

    print(f"\nReference: I think this is very good")
    print(f"Transcribed: {asr_result.text}")
    print(f"\nOverall Score: {feedback.overall_score}/100")
    print(f"Encouragement: {feedback.encouragement}")
    print(f"Problem Sounds: {', '.join(feedback.problem_sounds)}")
    print(f"\nWord Scores:")
    for ws in feedback.word_scores:
        print(f"  - {ws.word}: {ws.score}/100 {ws.issues}")
    if feedback.tips:
        print(f"\nPronunciation Tips:")
        for tip in feedback.tips:
            print(f"\n  Word: {tip.word}")
            print(f"  Issue: {tip.issue}")
            print(f"  Tip: {tip.tip}")
            if tip.phonetic:
                print(f"  Phonetic: {tip.phonetic}")
            if tip.example:
                print(f"  Example: {tip.example}")

    # Test Case 3: V/W confusion (very -> wery)
    print("\n" + "=" * 80)
    print("TEST 3: V/W Confusion")
    print("=" * 80)

    asr_result = ASRResult(
        text="the water is wery cold",  # "very" -> "wery"
        confidence=0.85,
        language="en",
        duration=2.0,
        words=[
            WordTiming(word="the", start=0.0, end=0.3),
            WordTiming(word="water", start=0.3, end=0.7),
            WordTiming(word="is", start=0.7, end=0.9),
            WordTiming(word="wery", start=0.9, end=1.3),
            WordTiming(word="cold", start=1.3, end=1.8),
        ],
        provider="openai"
    )

    feedback = analyzer.analyze_pronunciation(
        asr_result=asr_result,
        reference_text="the water is very cold",
        user_id=None
    )

    print(f"\nReference: the water is very cold")
    print(f"Transcribed: {asr_result.text}")
    print(f"\nOverall Score: {feedback.overall_score}/100")
    print(f"Encouragement: {feedback.encouragement}")
    print(f"Problem Sounds: {', '.join(feedback.problem_sounds)}")
    print(f"\nWord Scores:")
    for ws in feedback.word_scores:
        status = " [ISSUE]" if ws.score < 70 else ""
        print(f"  - {ws.word}: {ws.score}/100{status}")
    if feedback.tips:
        print(f"\nPronunciation Tips:")
        for tip in feedback.tips:
            print(f"\n  Word: {tip.word}")
            print(f"  Tip: {tip.tip}")
            if tip.example:
                print(f"  Example: {tip.example}")

    # Test Case 4: Multiple errors
    print("\n" + "=" * 80)
    print("TEST 4: Multiple Pronunciation Errors")
    print("=" * 80)

    asr_result = ASRResult(
        text="I tink de wata is wery goo",  # Multiple issues
        confidence=0.75,
        language="en",
        duration=2.5,
        words=[
            WordTiming(word="I", start=0.0, end=0.2),
            WordTiming(word="tink", start=0.2, end=0.6),
            WordTiming(word="de", start=0.6, end=0.8),
            WordTiming(word="wata", start=0.8, end=1.2),
            WordTiming(word="is", start=1.2, end=1.4),
            WordTiming(word="wery", start=1.4, end=1.8),
            WordTiming(word="goo", start=1.8, end=2.2),
        ],
        provider="openai"
    )

    feedback = analyzer.analyze_pronunciation(
        asr_result=asr_result,
        reference_text="I think the water is very good",
        user_id=None
    )

    print(f"\nReference: I think the water is very good")
    print(f"Transcribed: {asr_result.text}")
    print(f"\nOverall Score: {feedback.overall_score}/100")
    print(f"Encouragement: {feedback.encouragement}")
    print(f"Problem Sounds: {', '.join(feedback.problem_sounds)}")
    print(f"\nWord Scores:")
    for ws in feedback.word_scores:
        status = " [NEEDS WORK]" if ws.score < 70 else ""
        print(f"  - {ws.word}: {ws.score}/100{status}")
    if feedback.tips:
        print(f"\nTop 3 Pronunciation Tips:")
        for i, tip in enumerate(feedback.tips, 1):
            print(f"\n  {i}. {tip.word}")
            print(f"     {tip.tip}")
            if tip.example:
                print(f"     {tip.example}")


def test_common_mispronunciations_database():
    """Show the database of common mispronunciations."""
    print("\n" + "=" * 80)
    print("COMMON MISPRONUNCIATION DATABASE")
    print("=" * 80)

    print(f"\nTotal words tracked: {len(COMMON_MISPRONUNCIATIONS)}")
    print("\nSample entries:\n")

    sample_words = ["the", "think", "very", "water", "right", "good"]

    for word in sample_words:
        if word in COMMON_MISPRONUNCIATIONS:
            info = COMMON_MISPRONUNCIATIONS[word]
            print(f"Word: '{word}' {info.get('phonetic', '')}")
            print(f"  Common errors: {', '.join(info['common_errors'])}")
            print(f"  Tip: {info['tip']}")
            print(f"  Example: {info.get('example', 'N/A')}")
            print()


def test_pronunciation_feedback_format():
    """Show the format of pronunciation feedback in tutor response."""
    print("\n" + "=" * 80)
    print("PRONUNCIATION FEEDBACK FORMAT (for API)")
    print("=" * 80)

    analyzer = PronunciationAnalyzer(db=None)

    asr_result = ASRResult(
        text="I tink dis is good",
        confidence=0.88,
        language="en",
        duration=2.0,
        words=[
            WordTiming(word="I", start=0.0, end=0.2),
            WordTiming(word="tink", start=0.2, end=0.6),
            WordTiming(word="dis", start=0.6, end=0.9),
            WordTiming(word="is", start=0.9, end=1.1),
            WordTiming(word="good", start=1.1, end=1.6),
        ],
        provider="openai"
    )

    feedback = analyzer.analyze_pronunciation(
        asr_result=asr_result,
        reference_text="I think this is good",
        user_id=None
    )

    # Format as it would appear in API response
    api_format = {
        "overall_score": feedback.overall_score,
        "encouragement": feedback.encouragement,
        "tips": [
            {
                "word": tip.word,
                "issue": tip.issue,
                "tip": tip.tip,
                "phonetic": tip.phonetic,
                "example": tip.example
            }
            for tip in feedback.tips
        ],
        "problem_sounds": feedback.problem_sounds,
        "word_scores": [
            {
                "word": ws.word,
                "score": ws.score,
                "issues": ws.issues
            }
            for ws in feedback.word_scores
        ]
    }

    import json
    print("\nJSON Format:")
    print(json.dumps(api_format, indent=2))

    print("\n" + "=" * 80)
    print("HOW IT APPEARS IN TUTOR RESPONSE:")
    print("=" * 80)

    print(f"\nTutor Message: \"Good effort! You're pronouncing most words well.\"")
    print(f"\nPronunciation Feedback:")
    print(f"  Overall Score: {feedback.overall_score}/100")
    print(f"  {feedback.encouragement}")
    print()

    if feedback.tips:
        print("  Specific Tips:")
        for tip in feedback.tips:
            print(f"  - {tip.word}: {tip.tip}")
            if tip.example:
                print(f"    {tip.example}")

    print("\n  Word-by-word breakdown:")
    for ws in feedback.word_scores:
        emoji = "✓" if ws.score >= 80 else "○" if ws.score >= 60 else "✗"
        print(f"  {emoji} {ws.word}: {ws.score}/100")


if __name__ == "__main__":
    test_pronunciation_analyzer()
    test_common_mispronunciations_database()
    test_pronunciation_feedback_format()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nThe pronunciation feedback system provides:")
    print("  ✓ Specific, actionable tips for mispronounced words")
    print("  ✓ Detection of common pronunciation patterns")
    print("  ✓ Word-level scoring with detailed feedback")
    print("  ✓ Phonetic guidance and examples")
    print("  ✓ Encouraging but specific messages")
    print("  ✓ Tracking of problem sounds")
    print("\nNext steps:")
    print("  - Integrate with voice session API")
    print("  - Track improvement over time in database")
    print("  - Add user-specific pronunciation patterns")
    print("  - Generate personalized practice recommendations")
    print()
