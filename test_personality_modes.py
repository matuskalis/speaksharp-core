#!/usr/bin/env python3
"""
Test script for AI Tutor Personality Modes

This script demonstrates the different personality modes of Alex, the AI tutor.
Run this to see how the tutor's personality adapts to different modes.

Usage:
    python test_personality_modes.py
"""

from app.tutor_agent import TutorAgent


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_personality_mode(mode_name, user_input, level, context=None):
    """Test a specific personality mode."""
    print(f"\n📚 Personality Mode: {mode_name.upper()}")
    print(f"📊 Learner Level: {level}")
    print(f"💬 User Input: \"{user_input}\"")
    print("-" * 70)

    tutor = TutorAgent()

    # Build context
    if context is None:
        context = {}
    context['level'] = level
    if mode_name != "default":
        context['personality_mode'] = mode_name

    # Get response
    response = tutor.process_user_input(user_input, context)

    # Display response
    print(f"\n🤖 Alex: {response.message}")

    if response.errors:
        print(f"\n📝 Errors detected: {len(response.errors)}")
        for i, error in enumerate(response.errors, 1):
            print(f"\n   Error {i} ({error.type.value}):")
            print(f"   ❌ Your sentence: {error.user_sentence}")
            print(f"   ✅ Corrected: {error.corrected_sentence}")
            print(f"   💡 Explanation: {error.explanation}")

    if response.micro_task:
        print(f"\n✏️  Practice Task: {response.micro_task}")

    print()


def main():
    """Run personality mode tests."""
    print_section("AI Tutor Personality Enhancement Demo")
    print("\nThis demo shows how Alex adapts to different personality modes.")
    print("Each mode provides a unique teaching style for different learner needs.")

    # Test 1: Encouraging Mode (Beginner)
    print_section("Test 1: ENCOURAGING Mode - Perfect for Nervous Beginners")
    test_personality_mode(
        mode_name="encouraging",
        user_input="I go to cinema yesterday",
        level="A1"
    )

    # Test 2: Professional Mode (Business English)
    print_section("Test 2: PROFESSIONAL Mode - Business English Focus")
    test_personality_mode(
        mode_name="professional",
        user_input="I wanna talk about the quarterly meeting",
        level="B2"
    )

    # Test 3: Casual Mode (Everyday Conversation)
    print_section("Test 3: CASUAL Mode - Relaxed, Everyday English")
    test_personality_mode(
        mode_name="casual",
        user_input="I will take a coffee please",
        level="B1"
    )

    # Test 4: Strict Mode (Advanced Learners)
    print_section("Test 4: STRICT Mode - High Standards & Accuracy")
    test_personality_mode(
        mode_name="strict",
        user_input="I go to cinema for buy ticket and she don't want come",
        level="C1"
    )

    # Test 5: Default Mode (Auto-adapts to level)
    print_section("Test 5: DEFAULT Mode - Auto-adapts to Beginner Level")
    test_personality_mode(
        mode_name="default",
        user_input="She have three cats",
        level="A2"
    )

    # Test 6: Default Mode (Auto-adapts to advanced level)
    print_section("Test 6: DEFAULT Mode - Auto-adapts to Advanced Level")
    test_personality_mode(
        mode_name="default",
        user_input="I'm not use to working in such environment",
        level="C1"
    )

    # Test 7: Perfect input with Encouraging Mode
    print_section("Test 7: Perfect Input - Celebrating Success!")
    test_personality_mode(
        mode_name="encouraging",
        user_input="I went to the cinema yesterday and watched a great movie",
        level="B1"
    )

    # Summary
    print_section("Personality Modes Summary")
    print("""
The AI tutor 'Alex' now supports 4 distinct personality modes:

1. ENCOURAGING MODE - Extra supportive, great for beginners
   • Super warm and enthusiastic
   • Celebrates every small win
   • Very gentle corrections
   • Best for: Nervous learners, beginners, confidence building

2. PROFESSIONAL MODE - Business English focus
   • Polished and professional tone
   • Focus on workplace communication
   • Teaches business vocabulary and formality
   • Best for: Business English learners, professionals

3. CASUAL MODE - Friendly chat, slang allowed
   • Super relaxed and conversational
   • Teaches everyday spoken English
   • Includes slang and informal language
   • Best for: Casual conversation practice, real-world English

4. STRICT MODE - Corrects every mistake
   • Detail-oriented and thorough
   • Catches ALL errors (up to 5)
   • High standards for accuracy
   • Best for: Advanced learners, exam prep, perfectionists

5. DEFAULT MODE - Auto-adapts to learner level
   • Automatically chooses beginner or advanced approach
   • Based on CEFR level (A1-C2)
   • No personality_mode specified

All modes feature:
✅ Natural, human-like conversation
✅ Varied responses (not robotic)
✅ Level-adaptive language
✅ Warm, encouraging tone
✅ Progress tracking and memory

See TUTOR_PERSONALITY_GUIDE.md for more details!
    """)

    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
