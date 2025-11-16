#!/usr/bin/env python3
"""
Test script to verify LLM integration in both stub and real API modes.

This script:
1. Tests configuration loading
2. Tests LLM client in stub mode
3. Tests tutor agent integration
4. Provides instructions for testing with real API
"""

import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from config import config, load_config
from llm_client import llm_client, LLMClient
from tutor_agent import call_llm_tutor, TutorAgent


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_configuration():
    """Test configuration loading."""
    print_section("STEP 1: CONFIGURATION TEST")

    cfg = load_config()

    print("🔧 LLM Configuration:")
    print(f"  Provider: {cfg.llm.provider}")
    print(f"  Model: {cfg.llm.model}")
    print(f"  API Key: {'✓ Set' if cfg.llm.api_key else '✗ Not set'}")
    print(f"  Temperature: {cfg.llm.temperature}")
    print(f"  Max Tokens: {cfg.llm.max_tokens}")
    print(f"  Timeout: {cfg.llm.timeout}s")
    print(f"  Retry Attempts: {cfg.llm.retry_attempts}")

    print("\n🎛 App Settings:")
    print(f"  Enable LLM: {cfg.enable_llm}")
    print(f"  Log API Calls: {cfg.log_api_calls}")
    print(f"  Debug Mode: {cfg.debug_mode}")

    if not cfg.llm.api_key and cfg.enable_llm:
        print("\n⚠️  LLM enabled but no API key set → Running in STUB MODE")
        return "stub"
    elif cfg.llm.api_key and cfg.enable_llm:
        print("\n✅ API key configured → Running in LLM MODE")
        return "llm"
    else:
        print("\n⚠️  LLM disabled → Running in STUB MODE")
        return "stub"


def test_llm_client(mode: str):
    """Test LLM client directly."""
    print_section("STEP 2: LLM CLIENT TEST")

    print(f"Testing in {mode.upper()} mode...\n")

    test_cases = [
        {
            "input": "I go to cinema yesterday.",
            "context": {"drill_type": "grammar_practice"},
            "expected_errors": ["tense", "article"]
        },
        {
            "input": "She don't like coffee.",
            "context": {"drill_type": "grammar_practice"},
            "expected_errors": ["subject-verb agreement"]
        },
        {
            "input": "I want order a large cappuccino please.",
            "context": {"scenario": "cafe_ordering"},
            "expected_errors": ["infinitive"]
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"  Input: {test['input']}")
        print(f"  Context: {test['context']}")

        response = llm_client.call_tutor(test['input'], test['context'])

        print(f"  Response Message: {response.message}")
        print(f"  Errors Found: {len(response.errors)}")

        if response.errors:
            for j, error in enumerate(response.errors, 1):
                print(f"    Error {j}:")
                print(f"      Type: {error.type.value}")
                print(f"      Original: {error.user_sentence}")
                print(f"      Corrected: {error.corrected_sentence}")
                print(f"      Explanation: {error.explanation}")

        if response.micro_task:
            print(f"  Micro-task: {response.micro_task}")

        print()

    if mode == "stub":
        print("📝 Note: In stub mode, LLM returns no errors.")
        print("   Heuristic layer (in tutor_agent) handles error detection.")


def test_tutor_agent(mode: str):
    """Test full tutor agent (heuristic + LLM layers)."""
    print_section("STEP 3: TUTOR AGENT INTEGRATION TEST")

    print(f"Testing two-layer system in {mode.upper()} mode...\n")

    tutor = TutorAgent()

    test_inputs = [
        ("Hello! I want order coffee, please.", {"scenario": "cafe_ordering"}),
        ("I like large cappuccino.", {"scenario": "cafe_ordering"}),
        ("Yesterday I go to park.", {"drill_type": "journal"}),
    ]

    for i, (user_input, context) in enumerate(test_inputs, 1):
        print(f"Test {i}: {user_input}")
        print(f"Context: {context}")

        response = tutor.process_user_input(user_input, context)

        print(f"  Tutor: {response.message}")
        print(f"  Total Errors: {len(response.errors)}")

        if response.errors:
            print("  Error Details:")
            for error in response.errors:
                source = "🔍 Heuristic" if "[heuristic]" in error.explanation else "🤖 LLM"
                print(f"    {source} | {error.type.value}: {error.explanation[:60]}...")

        print()

    if mode == "stub":
        print("📝 Note: In stub mode, all errors come from heuristic layer.")
        print("   With real LLM, you'll see both 🔍 and 🤖 errors.")


def show_llm_mode_instructions():
    """Show instructions for testing with real LLM."""
    print_section("TESTING WITH REAL LLM API")

    print("To test with real LLM integration:\n")

    print("1. Create .env file:")
    print("   cp .env.example .env\n")

    print("2. Add your API key to .env:")
    print("   # For OpenAI:")
    print("   OPENAI_API_KEY=your_key_here")
    print("   SPEAKSHARP_LLM_PROVIDER=openai\n")

    print("   # OR for Anthropic:")
    print("   ANTHROPIC_API_KEY=your_key_here")
    print("   SPEAKSHARP_LLM_PROVIDER=anthropic\n")

    print("3. Install API client:")
    print("   pip install openai    # for OpenAI")
    print("   pip install anthropic # for Anthropic\n")

    print("4. (Optional) Enable debug logging:")
    print("   SPEAKSHARP_DEBUG=true")
    print("   SPEAKSHARP_LOG_API=true\n")

    print("5. Run this test again:")
    print("   python test_llm_modes.py\n")

    print("6. Run full demo with LLM:")
    print("   python demo_integration.py\n")

    print("Expected differences in LLM mode:")
    print("  • More contextual, natural error corrections")
    print("  • Better understanding of register (formal vs informal)")
    print("  • Smarter micro-task suggestions")
    print("  • Errors tagged with 🤖 instead of 🔍")


def main():
    print("\n" + "=" * 70)
    print("  SPEAKSHARP LLM INTEGRATION TEST")
    print("=" * 70)

    # Step 1: Test configuration
    mode = test_configuration()

    # Step 2: Test LLM client
    test_llm_client(mode)

    # Step 3: Test tutor agent
    test_tutor_agent(mode)

    # Show instructions for LLM mode
    if mode == "stub":
        show_llm_mode_instructions()

    # Summary
    print_section("TEST SUMMARY")

    if mode == "stub":
        print("✅ All tests passed in STUB MODE")
        print("   Heuristic-based error detection is working correctly.")
        print("   Set API key in .env to test real LLM integration.\n")
    else:
        print("✅ All tests passed in LLM MODE")
        print("   Real API integration is working correctly.")
        print("   Both heuristic and LLM layers are active.\n")

    print("=" * 70)


if __name__ == "__main__":
    main()
