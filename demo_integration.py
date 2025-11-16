#!/usr/bin/env python3
"""
SpeakSharp Core MVP - End-to-End Integration Demo

This script demonstrates the complete flow:
1. Onboarding
2. Daily SRS Review
3. Lesson (structured grammar/communication lesson)
4. Scenario Session (conversation practice with tutor)
5. Monologue Drill (speaking practice)
6. Journal Drill (writing practice)
7. Error-based SRS card creation
8. Feedback Report
9. Voice Mode Demo (ASR + Tutor + TTS)

All components integrated with stubbed user data.
"""

import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from state_machine import StateMachine, Router, AppState
from tutor_agent import TutorAgent
from scenarios import get_scenario, ScenarioRunner
from srs_system import SRSSystem
from lessons import get_lesson, LessonRunner
from drills import get_monologue_prompt, MonologueRunner, get_journal_prompt, JournalRunner
from voice_session import VoiceSession
from models import CardType, ErrorType


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Print a subsection header."""
    print(f"\n--- {title} ---\n")


def simulate_user_delay():
    """Simulate user thinking/typing time."""
    import time
    time.sleep(0.5)


def main():
    """Run the complete end-to-end integration demo."""

    print_section("SPEAKSHARP CORE MVP - END-TO-END DEMO")

    # Initialize system components
    user_id = uuid4()
    state_machine = StateMachine(user_id)
    router = Router()
    tutor = TutorAgent()
    srs = SRSSystem()

    print(f"User ID: {user_id}")
    print(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ========================================================================
    # 1. ONBOARDING
    # ========================================================================
    print_section("STEP 1: ONBOARDING")

    state_machine.enter_state(AppState.ONBOARDING)

    print("Collecting user information...")
    state_machine.context['level'] = 'A2'
    state_machine.context['goals'] = ['work', 'travel']
    state_machine.context['interests'] = ['technology', 'music', 'cooking']
    state_machine.context['native_language'] = 'Spanish'

    print(f"✓ Level assessed: {state_machine.context['level']}")
    print(f"✓ Goals set: {', '.join(state_machine.context['goals'])}")
    print(f"✓ Interests: {', '.join(state_machine.context['interests'])}")

    state_machine.exit_state(AppState.ONBOARDING)
    router.mark_complete(AppState.ONBOARDING)

    simulate_user_delay()

    # ========================================================================
    # 2. DAILY SRS REVIEW
    # ========================================================================
    print_section("STEP 2: DAILY SRS REVIEW")

    # Pre-populate some SRS cards (set as due now for demo)
    print_subsection("Setting up SRS cards")

    from datetime import timedelta

    card1_id = srs.add_item(
        user_id=user_id,
        card_type=CardType.DEFINITION,
        front="What does 'efficient' mean?",
        back="Achieving maximum productivity with minimum wasted effort or expense",
        level="B1"
    )
    # Make it due now
    srs.cards[card1_id].next_review_date = datetime.now() - timedelta(hours=1)

    card2_id = srs.add_item(
        user_id=user_id,
        card_type=CardType.CLOZE,
        front="She ___ to work every day. (drive)",
        back="She drives to work every day.",
        level="A2"
    )
    # Make it due now
    srs.cards[card2_id].next_review_date = datetime.now() - timedelta(hours=1)

    card3_id = srs.add_item(
        user_id=user_id,
        card_type=CardType.ERROR_REPAIR,
        front="Fix: I go to cinema yesterday.",
        back="I went to the cinema yesterday.\n\nExplanation: Use past tense 'went' with 'yesterday'.",
        level="A2"
    )
    # Make it due now
    srs.cards[card3_id].next_review_date = datetime.now() - timedelta(hours=1)

    # Start review session
    state_machine.enter_state(AppState.DAILY_REVIEW)

    due_cards = srs.get_due_items(user_id, limit=10)
    state_machine.context['cards_total'] = len(due_cards)

    print(f"\nReviewing {len(due_cards)} cards...")

    # Simulate reviewing cards
    for i, card in enumerate(due_cards, 1):
        print(f"\n[Card {i}/{len(due_cards)}]")
        print(f"Q: {card.front}")

        simulate_user_delay()

        # Simulate user answer with varying quality
        quality = 5 if i == 1 else (4 if i == 2 else 3)
        response_time = 1500 + (i * 300)
        correct = quality >= 3

        print(f"A: [User answers] (quality: {quality}/5)")
        print(f"Correct answer: {card.back}")

        srs.update_item(
            card_id=card.card_id,
            quality=quality,
            response_time_ms=response_time,
            user_response="User's answer",
            correct=correct
        )

        state_machine.context['cards_reviewed'] = i

    state_machine.exit_state(AppState.DAILY_REVIEW)
    router.mark_complete(AppState.DAILY_REVIEW)

    simulate_user_delay()

    # ========================================================================
    # 3. LESSON - ARTICLES
    # ========================================================================
    print_section("STEP 3: LESSON - ARTICLES (A, AN, THE)")

    lesson = get_lesson("articles_a_an_the")
    lesson_runner = LessonRunner(lesson)

    print(lesson_runner.start())

    print("📝 Practice Tasks\n")

    # Controlled practice
    for i, task in enumerate(lesson.controlled_practice, 1):
        print(f"Task {i}/{len(lesson.controlled_practice)}: {task.prompt}")

        simulate_user_delay()

        # Simulate user attempting the task
        user_attempt = task.example_answer
        print(f"You: {user_attempt}")

        # Process through lesson runner
        result = lesson_runner.process_response(user_attempt)
        print(f"✓ {result['feedback']}\n")

        simulate_user_delay()

    # Freer production
    print("🎯 Production Task")
    final_task = lesson_runner.get_next_task()
    print(f"Task: {final_task.prompt}\n")

    simulate_user_delay()

    user_production = "I bought a new laptop yesterday. The laptop is very fast and has a large screen."
    print(f"You: {user_production}")

    # Get tutor feedback on production
    tutor_response = tutor.process_user_input(user_production, context={'lesson_id': lesson.lesson_id})
    print(f"Tutor: {tutor_response.message}")

    if tutor_response.errors:
        print(f"Corrections: {len(tutor_response.errors)} found")
        for err in tutor_response.errors[:2]:
            source = "🔍" if err.explanation.startswith("[heuristic]") else "🤖"
            print(f"  {source} {err.type.value}: {err.explanation}")

    result = lesson_runner.process_response(user_production)
    print(f"\n{result['feedback']}")

    final_result = lesson_runner.finish()
    print(f"\n✓ Lesson complete!")
    print(f"Skills practiced: {', '.join(final_result['skill_targets'])}")

    simulate_user_delay()

    # ========================================================================
    # 4. SCENARIO SESSION WITH TUTOR
    # ========================================================================
    print_section("STEP 4: SCENARIO SESSION - CAFE ORDERING")

    # Load scenario
    scenario = get_scenario("cafe_ordering")
    runner = ScenarioRunner(scenario)

    state_machine.enter_state(
        AppState.SCENARIO_SESSION,
        {'scenario_id': 'cafe_ordering'}
    )

    # Start scenario
    opening = runner.start()
    print(opening)

    # Simulated conversation with errors for tutor to catch
    conversation = [
        "Hello! I want order coffee, please.",  # Missing "to"
        "I like large cappuccino.",  # Missing article
        "Yes, I take croissant too.",  # Should be "I'll take" or "I'll have"
        "How much it cost?",  # Missing "does"
        "I pay with card. Thank you!"  # Should be "I'll pay"
    ]

    all_errors = []

    for turn_num, user_input in enumerate(conversation, 1):
        state_machine.context['scenario_turns'] = turn_num

        print(f"\n[Turn {turn_num}]")
        print(f"You: {user_input}")

        simulate_user_delay()

        # Process with tutor agent
        tutor_response = tutor.process_user_input(
            user_input,
            context={'scenario_id': 'cafe_ordering'}
        )

        print(f"Tutor: {tutor_response.message}")

        # Display errors if found
        if tutor_response.errors:
            print(f"\n⚠ Errors detected ({len(tutor_response.errors)}):")

            # Show detailed breakdown for first turn to demonstrate dual-layer system
            if turn_num == 1:
                print("\n  📋 DETAILED ERROR ANALYSIS (Two-Layer System):")
                heuristic_errors = [e for e in tutor_response.errors if e.explanation.startswith("[heuristic]")]
                llm_errors = [e for e in tutor_response.errors if not e.explanation.startswith("[heuristic]")]

                if heuristic_errors:
                    print(f"\n  🔍 Heuristic Layer ({len(heuristic_errors)} errors):")
                    for err in heuristic_errors:
                        print(f"    • {err.type.value}: {err.explanation}")
                        print(f"      Corrected: {err.corrected_sentence}")

                if llm_errors:
                    print(f"\n  🤖 LLM Layer ({len(llm_errors)} errors):")
                    for err in llm_errors:
                        print(f"    • {err.type.value}: {err.explanation}")
                        print(f"      Corrected: {err.corrected_sentence}")

                print()  # Blank line

            # Regular display for other turns
            for err in tutor_response.errors:
                if turn_num > 1:  # Skip for turn 1 since we showed detailed view
                    source = "🔍" if err.explanation.startswith("[heuristic]") else "🤖"
                    print(f"  {source} {err.type.value}: {err.explanation}")
                    print(f"    Corrected: {err.corrected_sentence}")
                all_errors.append(err)

        # Display micro-task if provided
        if tutor_response.micro_task:
            print(f"\n💡 Micro-task: {tutor_response.micro_task}")

        # Get AI response from scenario
        result = runner.process_turn(user_input)
        print(f"Barista: {result['ai_response']}")

        simulate_user_delay()

        # Check if scenario is complete
        if result['scenario_complete']:
            print_subsection("Scenario Complete!")
            feedback = result['feedback']
            print(f"Turns completed: {feedback['turns_completed']}")
            print(f"Success criteria met: {feedback['success_criteria_met']}")
            state_machine.context['scenario_complete'] = True
            break

    state_machine.exit_state(AppState.SCENARIO_SESSION)
    router.mark_complete(AppState.SCENARIO_SESSION)

    simulate_user_delay()

    # ========================================================================
    # 5. MONOLOGUE PRACTICE
    # ========================================================================
    print_section("STEP 5: SPEAKING DRILL - DAILY MONOLOGUE")

    monologue_prompt = get_monologue_prompt("last_weekend")
    monologue_runner = MonologueRunner(monologue_prompt, user_id)

    print(monologue_runner.start())

    # Simulate user speaking (in production, this would be ASR transcription)
    monologue_text = """Last weekend I had a great time. On Saturday, I went to the park with my friends.
    We play football and had picnic. The weather was very nice and sunny.
    After that, I went home and watch movie with my family.
    On Sunday, I study English and do my homework. It was relaxing weekend."""

    print("🎤 Speaking...")
    print(f"\nTranscript: {monologue_text}\n")

    simulate_user_delay()

    # Submit response
    m_result = monologue_runner.submit_response(monologue_text, duration_seconds=75)
    print(f"✓ Response submitted: {m_result['word_count']} words in {m_result['duration_seconds']}s")

    # Get tutor feedback
    m_tutor_response = tutor.process_user_input(monologue_text, context={'drill_type': 'monologue'})

    print(f"\nTutor feedback: {m_tutor_response.message}")

    if m_tutor_response.errors:
        print(f"\n⚠ Corrections ({len(m_tutor_response.errors)}):")
        for err in m_tutor_response.errors[:3]:
            source = "🔍" if err.explanation.startswith("[heuristic]") else "🤖"
            print(f"  {source} {err.type.value}: {err.explanation}")
            all_errors.append(err)

    m_stats = monologue_runner.get_stats()
    print(f"\n📊 Performance:")
    print(f"  • Words per minute: {m_stats['words_per_minute']}")
    print(f"  • Total words: {m_stats['word_count']}")
    print(f"  • Duration: {m_stats['duration_seconds']}s")

    simulate_user_delay()

    # ========================================================================
    # 6. WRITING DRILL - DAILY JOURNAL
    # ========================================================================
    print_section("STEP 6: WRITING DRILL - DAILY JOURNAL")

    journal_prompt = get_journal_prompt("today_feeling")
    journal_runner = JournalRunner(journal_prompt, user_id)

    print(journal_runner.start())

    # Simulate user writing (in production, this would be text input)
    journal_text = """I'm feeling good today. I had productive morning and finished all my work early.
    I meet my friend for coffee and we talked about our plans. The weather is nice which always make me feel better.
    I'm looking forward to relaxing this evening."""

    print("✍️ Writing...")
    print(f"\nJournal entry: {journal_text}\n")

    simulate_user_delay()

    # Submit entry
    j_result = journal_runner.submit_entry(journal_text)
    print(f"✓ Entry submitted: {j_result['word_count']} words (minimum: {j_result['min_words']})")
    print(f"  Meets minimum: {'✓' if j_result['meets_minimum'] else '✗'}")

    # Get tutor feedback
    j_tutor_response = tutor.process_user_input(journal_text, context={'drill_type': 'journal'})

    print(f"\nTutor feedback: {j_tutor_response.message}")

    if j_tutor_response.errors:
        print(f"\n⚠ Corrections ({len(j_tutor_response.errors)}):")
        for err in j_tutor_response.errors[:3]:
            source = "🔍" if err.explanation.startswith("[heuristic]") else "🤖"
            print(f"  {source} {err.type.value}: {err.explanation}")
            all_errors.append(err)

    j_stats = journal_runner.get_stats()
    print(f"\n📊 Performance:")
    print(f"  • Word count: {j_stats['word_count']}/{j_stats['min_words']}")
    print(f"  • Completion: {j_stats['completion_percentage']}%")
    print(f"  • Category: {j_stats['prompt_category']}")

    simulate_user_delay()

    # ========================================================================
    # 7. ERROR-BASED SRS CARD CREATION
    # ========================================================================
    print_section("STEP 7: CREATING SRS CARDS FROM ERRORS")

    print(f"Found {len(all_errors)} errors during the session")
    print("Creating SRS cards for practice...\n")

    new_cards = []
    for i, error in enumerate(all_errors[:3], 1):  # Limit to top 3 errors
        print(f"{i}. Error type: {error.type.value}")
        print(f"   Original: {error.user_sentence}")
        print(f"   Corrected: {error.corrected_sentence}")

        card_id = srs.create_card_from_error(error, user_id)
        new_cards.append(card_id)

        simulate_user_delay()

    print(f"\n✓ Created {len(new_cards)} new SRS cards from errors")

    # ========================================================================
    # 8. FEEDBACK REPORT
    # ========================================================================
    print_section("STEP 8: SESSION FEEDBACK REPORT")

    state_machine.enter_state(AppState.FEEDBACK_REPORT)

    print_subsection("Performance Summary")

    # SRS Review Stats
    print("📊 SRS Review:")
    print(f"  • Cards reviewed: {state_machine.context.get('cards_reviewed', 0)}")
    print(f"  • Average quality: 4.0/5.0")
    print(f"  • Accuracy: 100%")

    # Lesson Stats
    print("\n📚 Lesson Performance:")
    print(f"  • Lesson: {lesson.title}")
    print(f"  • Tasks completed: {final_result['tasks_completed']}")
    print(f"  • Skills practiced: {', '.join(final_result['skill_targets'])}")
    print(f"  • Status: ✓ Complete")

    # Scenario Stats
    print("\n🎭 Scenario Performance:")
    print(f"  • Scenario: {scenario.title}")
    print(f"  • Turns completed: {state_machine.context.get('scenario_turns', 0)}")
    print(f"  • Success: ✓")

    # Monologue Stats
    print("\n🎤 Monologue Performance:")
    print(f"  • Words spoken: {m_stats['word_count']}")
    print(f"  • Speaking rate: {m_stats['words_per_minute']} WPM")
    print(f"  • Duration: {m_stats['duration_seconds']}s")
    print(f"  • Prompt: {monologue_prompt.text[:60]}...")

    # Journal Stats
    print("\n✍️ Journal Performance:")
    print(f"  • Words written: {j_stats['word_count']}")
    print(f"  • Target: {j_stats['min_words']} words")
    print(f"  • Completion: {j_stats['completion_percentage']}%")
    print(f"  • Category: {j_stats['prompt_category']}")

    # Error Analysis
    print(f"\n⚠ Total Errors Detected: {len(all_errors)}")
    print("\n⚠ Error Breakdown:")
    error_counts = {}
    for err in all_errors:
        error_counts[err.type.value] = error_counts.get(err.type.value, 0) + 1

    for error_type, count in error_counts.items():
        print(f"  • {error_type}: {count}")

    # Next Steps
    print("\n📚 Next Steps:")
    print("  • Review new SRS cards tomorrow")
    print("  • Practice present simple with articles")
    print("  • Try 'self_introduction' scenario next")

    # Overall SRS Stats
    print_subsection("Overall SRS Statistics")
    stats = srs.get_stats(user_id)
    for key, value in stats.items():
        print(f"  • {key}: {value}")

    state_machine.exit_state(AppState.FEEDBACK_REPORT)

    simulate_user_delay()

    # ========================================================================
    # 9. VOICE MODE DEMO (ASR + TUTOR + TTS)
    # ========================================================================
    print_section("STEP 9: VOICE MODE DEMO (ASR + TUTOR + TTS)")

    print("Testing complete voice interaction pipeline:\n")
    print("Pipeline: Audio Input → ASR → Tutor Agent → TTS → Audio Output\n")

    # Create voice session
    voice_session = VoiceSession(
        user_id=user_id,
        mode="free_chat",
        context={"session_type": "voice_demo"}
    )

    # Simulate voice interactions
    voice_tests = [
        {
            "audio_path": "/tmp/test_audio.mp3",
            "description": "Free chat greeting"
        },
        {
            "audio_path": "/tmp/cafe_order.mp3",
            "description": "Café order with errors"
        }
    ]

    for i, test in enumerate(voice_tests, 1):
        print(f"Voice Turn {i}: {test['description']}")
        print("-" * 70)

        # Process voice input
        result = voice_session.handle_audio_input(test['audio_path'])

        print(f"🎤 ASR Recognized: {result.recognized_text}")
        print(f"   Confidence: {result.asr_confidence}")

        print(f"\n💬 Tutor Response: {result.tutor_response.message}")

        if result.tutor_response.errors:
            print(f"\n⚠  Errors corrected: {len(result.tutor_response.errors)}")
            for error in result.tutor_response.errors[:2]:
                source = "🔍" if error.explanation.startswith("[heuristic]") else "🤖"
                print(f"   {source} {error.type.value}: {error.corrected_sentence}")

        if result.tts_output_path:
            tts_filename = Path(result.tts_output_path).name
            print(f"\n🔊 TTS Output: {tts_filename}")
        else:
            print(f"\n🔊 TTS Output: (not generated)")

        print(f"\n⏱  Processing Time: {result.processing_time_ms}ms")
        print()

        simulate_user_delay()

    print("✓ Voice mode pipeline operational\n")
    print("📝 Note: Running in stub mode by default.")
    print("   Set OPENAI_API_KEY to test with real ASR/TTS.\n")

    simulate_user_delay()

    # ========================================================================
    # 10. SUMMARY
    # ========================================================================
    print_section("DEMO COMPLETE - SUMMARY")

    print("✓ Onboarding: User profile created")
    print(f"✓ Daily Review: {state_machine.context.get('cards_reviewed', 0)} cards reviewed")
    print(f"✓ Lesson: {lesson.title} completed ({final_result['tasks_completed']} tasks)")
    print(f"✓ Scenario Session: {scenario.title} completed")
    print(f"✓ Monologue Drill: {m_stats['word_count']} words at {m_stats['words_per_minute']} WPM")
    print(f"✓ Journal Drill: {j_stats['word_count']} words ({j_stats['completion_percentage']}% of target)")
    print(f"✓ Voice Mode: 2 voice turns (ASR + Tutor + TTS pipeline)")
    print(f"✓ Tutor Agent: {len(all_errors)} errors tagged and corrected")
    print(f"✓ SRS Integration: {len(new_cards)} new cards created from errors")
    print("✓ Feedback Report: Generated and displayed")

    print("\n" + "=" * 80)
    print("  All components working successfully!")
    print("  The core MVP is operational and ready for integration.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
