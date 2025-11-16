"""
SpeakSharp Tutor Agent

This module implements a two-layer error detection and correction system:
1. Heuristic layer: Fast, regex-based error detection for common patterns
2. LLM layer: AI-powered contextual analysis and natural language feedback

LLM INTEGRATION POINTS:
======================

1. WHERE TO PLUG IN REAL LLM API:
   - Function: call_llm_tutor() around line 100
   - Replace the simulation logic with actual API calls to OpenAI/Anthropic/etc.
   - Send: user_text, context, system_prompt, conversation_history
   - Receive: JSON response matching the expected format below

2. EXPECTED LLM JSON RESPONSE FORMAT:
   {
     "message": "Natural language response to the learner",
     "errors": [
       {
         "type": "grammar|vocab|fluency|pronunciation_placeholder|structure",
         "user_sentence": "The exact sentence from user input",
         "corrected_sentence": "The corrected version",
         "explanation": "Brief, learner-friendly explanation"
       }
     ],
     "micro_task": "Optional practice suggestion"
   }

3. ERROR HANDLING STRATEGY:
   - If LLM returns malformed JSON: Parse what you can, use empty lists for missing fields
   - If LLM response is completely invalid: Fall back to heuristic-only mode
   - If individual errors are malformed: Skip them, keep valid ones
   - Always return a valid TutorResponse object
   - Log errors for debugging but never crash the session

4. QUALITY SAFEGUARDS:
   - Validate error types against ErrorType enum
   - Ensure all required fields are present in each error
   - Limit total errors to 5 per response (avoid overwhelming learner)
   - Prefer LLM message over generated one, but have fallback
"""

import json
import re
from typing import List, Dict, Optional
from app.models import Error, TutorResponse, ErrorType


TUTOR_SYSTEM_PROMPT = """You are an English tutor AI for SpeakSharp. Your role is to help learners improve their English.

PERSONA:
- Supportive but direct
- Corrective but not nitpicky
- Task-oriented, not chatty
- Friendly but firm expert
- Always goal-oriented

CORRECTION STRATEGY:
1. Selectively correct errors blocking clarity or fossilized patterns
2. Reformulate user sentences naturally
3. Offer short, simple explanations with examples
4. Don't interrupt every sentence
5. Avoid metalinguistic jargon

ERROR TYPES TO TAG:
- grammar: article errors, tense errors, agreement, word order, etc.
- vocab: wrong word, collocation mismatch, register error
- fluency: hesitations, restarts, low fluency
- pronunciation_placeholder: mispronunciations (placeholder for now)
- structure: sentence structure, clause issues, discourse problems

TURN MANAGEMENT:
- Keep learner speaking 60-70% of time
- Use short, clear turns
- Avoid monologues

OUTPUT FORMAT (strict JSON):
{
  "message": "your response to the learner",
  "errors": [
    {
      "type": "grammar|vocab|fluency|pronunciation_placeholder|structure",
      "user_sentence": "what they said",
      "corrected_sentence": "corrected version",
      "explanation": "brief explanation"
    }
  ],
  "micro_task": "optional micro-task for practice"
}

RULES:
- Always output valid JSON
- Tag 1-3 most important errors per turn
- Generate 1 micro-task when appropriate
- Be concise and clear
- Focus on high-impact corrections
"""


def call_llm_tutor(user_text: str, context: dict | None = None) -> TutorResponse:
    """
    Call LLM-based tutor for contextual error analysis.

    This function delegates to the LLM client which handles:
    - API selection (OpenAI/Anthropic)
    - Retry logic and error handling
    - Response parsing and validation
    - Fallback to stub mode if API unavailable

    Args:
        user_text: The learner's input text
        context: Optional context dict (scenario_id, user_level, drill_type, etc.)

    Returns:
        TutorResponse with message, errors, and micro_task
    """
    from app.llm_client import llm_client
    return llm_client.call_tutor(user_text, context)


class TutorAgent:
    def __init__(self, system_prompt: str = TUTOR_SYSTEM_PROMPT):
        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, str]] = []

    def process_user_input(self, user_text: str, context: Dict = None) -> TutorResponse:
        """
        Process user input through two-layer analysis: heuristic + LLM.

        Pipeline:
        1. Heuristic layer: Fast regex-based error detection
        2. LLM layer: Contextual AI analysis
        3. Merge results: Combine errors from both layers
        4. Generate response: Use LLM message with merged errors

        Args:
            user_text: The learner's input text
            context: Optional context dict (scenario_id, user_level, etc.)

        Returns:
            TutorResponse with merged corrections and feedback
        """
        if context is None:
            context = {}

        self.conversation_history.append({
            "role": "user",
            "content": user_text
        })

        # Layer 1: Heuristic error detection (fast, rule-based)
        heuristic_errors = self._detect_errors(user_text)

        # Tag heuristic errors so they're distinguishable in output
        for err in heuristic_errors:
            err.explanation = "[heuristic] " + err.explanation

        # Layer 2: LLM-based analysis (contextual, intelligent)
        llm_response = call_llm_tutor(user_text, context)

        # Merge results: Combine errors from both layers
        all_errors = heuristic_errors + llm_response.errors

        # Deduplicate similar errors (prefer LLM version)
        # Simple deduplication: if same corrected_sentence, keep LLM version
        seen_corrections = set()
        unique_errors = []
        for err in all_errors:
            if err.corrected_sentence not in seen_corrections:
                unique_errors.append(err)
                seen_corrections.add(err.corrected_sentence)

        # Limit to top 5 errors to avoid overwhelming the learner
        final_errors = unique_errors[:5]

        # Use LLM message as primary (it's more natural and contextual)
        # Fall back to generated message if LLM didn't provide one
        if llm_response.message:
            message = llm_response.message
        elif final_errors:
            message = self._generate_correction_message(user_text, final_errors)
        else:
            message = self._generate_positive_response(user_text)

        # Use LLM micro-task, or generate from errors, or use context-based
        micro_task = (
            llm_response.micro_task or
            self._generate_micro_task(final_errors) or
            self._generate_continuation_task(context)
        )

        tutor_response = TutorResponse(
            message=message,
            errors=final_errors,
            micro_task=micro_task
        )

        self.conversation_history.append({
            "role": "assistant",
            "content": tutor_response.message
        })

        return tutor_response

    def _detect_errors(self, text: str) -> List[Error]:
        """Detect common errors in user text (simplified for demo)."""
        errors = []

        # Check for missing "to" in "want to"
        if re.search(r'\bwant\s+\w+\b', text, re.IGNORECASE) and not re.search(r'\bwant to\b', text, re.IGNORECASE):
            errors.append(Error(
                type=ErrorType.GRAMMAR,
                user_sentence=text,
                corrected_sentence=re.sub(r'\bwant\s+(\w+)', r'want to \1', text, flags=re.IGNORECASE),
                explanation="Use 'want to' before a verb. Example: 'I want to order coffee.'"
            ))

        # Check for missing articles with countable nouns
        if re.search(r'\b(I like|I want|I take|order)\s+(large|small|big)?\s*(coffee|cappuccino|croissant|muffin|sandwich)\b', text, re.IGNORECASE):
            if not re.search(r'\b(a|an|the)\s+(large|small|big)?\s*(coffee|cappuccino|croissant|muffin|sandwich)\b', text, re.IGNORECASE):
                errors.append(Error(
                    type=ErrorType.GRAMMAR,
                    user_sentence=text,
                    corrected_sentence=re.sub(
                        r'\b(I like|I want|I take|order)\s+((large|small|big)\s+)?(coffee|cappuccino|croissant|muffin|sandwich)\b',
                        r'\1 a \2\4',
                        text,
                        flags=re.IGNORECASE
                    ),
                    explanation="Missing article. Use 'a' before singular countable nouns like coffee, croissant."
                ))

        # Check for missing auxiliary in questions
        if re.search(r'\bHow much it (cost|is)\b', text, re.IGNORECASE):
            errors.append(Error(
                type=ErrorType.GRAMMAR,
                user_sentence=text,
                corrected_sentence=text.replace("How much it cost", "How much does it cost")
                                       .replace("How much it is", "How much is it"),
                explanation="In questions, use auxiliary 'does' before the subject. Example: 'How much does it cost?'"
            ))

        # Check for present simple instead of future in immediate intentions
        if re.search(r'\bI (pay|go|take|order)\b(?!.*\b(yesterday|last|ago)\b)', text, re.IGNORECASE):
            if not re.search(r'\b(will|\'ll)\b', text, re.IGNORECASE):
                errors.append(Error(
                    type=ErrorType.GRAMMAR,
                    user_sentence=text,
                    corrected_sentence=re.sub(r'\bI (pay|go|take|order)\b', r"I'll \1", text, flags=re.IGNORECASE),
                    explanation="For immediate intentions, use 'I'll' (I will). Example: 'I'll pay with card.'"
                ))

        # Check for common article errors
        if re.search(r'\b(I am student|She is teacher)\b', text, re.IGNORECASE):
            errors.append(Error(
                type=ErrorType.GRAMMAR,
                user_sentence=text,
                corrected_sentence=text.replace("I am student", "I am a student")
                                       .replace("She is teacher", "She is a teacher"),
                explanation="Missing article. Use 'a/an' before singular countable nouns."
            ))

        # Check for tense errors
        if re.search(r'\byesterday.*\b(go|eat|see)\b', text, re.IGNORECASE):
            errors.append(Error(
                type=ErrorType.GRAMMAR,
                user_sentence=text,
                corrected_sentence=text.replace(" go ", " went ")
                                       .replace(" eat ", " ate ")
                                       .replace(" see ", " saw "),
                explanation="Use past tense with 'yesterday'."
            ))

        # Check for subject-verb agreement
        if re.search(r'\b(he go|she have|it are)\b', text, re.IGNORECASE):
            errors.append(Error(
                type=ErrorType.GRAMMAR,
                user_sentence=text,
                corrected_sentence=text.replace("he go", "he goes")
                                       .replace("she have", "she has")
                                       .replace("it are", "it is"),
                explanation="Subject and verb must agree. Use 's' with he/she/it in present tense."
            ))

        return errors

    def _generate_correction_message(self, user_text: str, errors: List[Error]) -> str:
        """Generate a correction message."""
        if len(errors) == 1:
            return f"Good attempt! Let me help with one thing: {errors[0].corrected_sentence}. {errors[0].explanation} Try again?"
        else:
            return f"I understood you! A couple of corrections: {errors[0].corrected_sentence}. Can you try saying that again?"

    def _generate_positive_response(self, user_text: str) -> str:
        """Generate positive response for error-free input."""
        responses = [
            "Perfect! That was well said.",
            "Excellent! Your grammar is correct.",
            "Great job! Very natural.",
            "Nice work! Clear and correct."
        ]
        import random
        return random.choice(responses)

    def _generate_micro_task(self, errors: List[Error]) -> Optional[str]:
        """Generate micro-task based on errors."""
        if not errors:
            return None

        error_type = errors[0].type

        tasks = {
            ErrorType.GRAMMAR: "Make 3 sentences using the correct form.",
            ErrorType.VOCAB: "Use this word in a different sentence.",
            ErrorType.STRUCTURE: "Try rephrasing with a different structure.",
            ErrorType.FLUENCY: "Repeat the sentence smoothly without pauses."
        }

        return tasks.get(error_type, "Practice this pattern in a new context.")

    def _generate_continuation_task(self, context: Dict) -> Optional[str]:
        """Generate continuation task based on context."""
        scenario = context.get('scenario_id')

        if scenario == 'cafe_ordering':
            return "Now ask about the price."
        elif scenario == 'self_introduction':
            return "Tell me about your hobbies."
        elif scenario == 'talk_about_your_day':
            return "What happened next?"

        return "Can you tell me more about that?"

    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []


if __name__ == "__main__":
    # Test the tutor agent
    print("Testing Tutor Agent")
    print("=" * 60)

    tutor = TutorAgent()

    # Test cases
    test_inputs = [
        "I am student at university.",
        "Yesterday I go to the park.",
        "She have three cats.",
        "I like playing football and reading books."
    ]

    for i, user_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}:")
        print(f"User: {user_input}")

        response = tutor.process_user_input(user_input, {'scenario_id': 'self_introduction'})

        print(f"Tutor: {response.message}")
        if response.errors:
            print(f"Errors detected: {len(response.errors)}")
            for err in response.errors:
                print(f"  - {err.type.value}: {err.explanation}")
        if response.micro_task:
            print(f"Micro-task: {response.micro_task}")
        print("-" * 60)

    print("\nTutor agent test complete!")
