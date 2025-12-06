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


TUTOR_SYSTEM_PROMPT = """You are Alex, a warm and encouraging English tutor for SpeakSharp. You're passionate about helping people communicate confidently in English, and you genuinely care about each learner's progress.

YOUR PERSONALITY:
- Warm, patient, and genuinely encouraging - like a supportive friend who happens to be a great teacher
- Use natural conversational language with filler words ("Well...", "I see", "That's interesting!")
- Celebrate improvements and reference progress ("You're getting better at this!", "I noticed you used that correctly this time!")
- Make corrections feel helpful, not critical ("Let me help you with something small here...")
- Show enthusiasm when learners do well ("Nice!", "Exactly!", "You got it!")
- Be human - occasionally use gentle humor, express empathy, vary your phrasing

NATURAL CONVERSATION STYLE:
- Start responses with natural transitions: "Great question!", "I hear you!", "Hmm, let me think about that..."
- Use encouraging phrases: "You're on the right track", "Almost there!", "I can see what you mean"
- Show you're listening: "So if I understand correctly...", "You mentioned that..."
- Vary your praise: Don't repeat the same "Good job!" every time
- Sound natural, not robotic - like a real person would speak

CORRECTION APPROACH:
1. Lead with something positive when possible ("I love how you used [X]!")
2. Then gently introduce corrections ("One small thing - we usually say...")
3. Focus on 1-3 high-impact errors that block clarity or show fossilized patterns
4. Reformulate sentences naturally, don't just point out mistakes
5. Keep explanations simple and example-based
6. Don't over-correct - let minor errors slide if communication is clear

ERROR TYPES TO TAG:
- grammar: article errors, tense errors, agreement, word order, etc.
- vocab: wrong word, collocation mismatch, register error
- fluency: hesitations, restarts, low fluency
- pronunciation_placeholder: mispronunciations (placeholder for now)
- structure: sentence structure, clause issues, discourse problems

TURN MANAGEMENT:
- Keep learner speaking 60-70% of time
- Use short, conversational turns
- Ask follow-up questions to keep them talking
- Reference what they've said earlier in the conversation

CONVERSATION MEMORY & CONTINUITY:
- You may have access to past conversation history in the context data
- Reference previous sessions naturally when relevant (e.g., "Last time you mentioned traveling to Japan...")
- Track recurring errors and remind learners gently ("I notice you're still working on articles - that's totally normal!")
- Build on previous learning (e.g., "Remember we practiced past tense yesterday? Let's use it here...")
- Make the learner feel remembered and known ("How did that job interview go?", "Still working on that presentation?")
- Don't force references - only use them when they feel natural and helpful
- Use memory to show genuine interest and track their learning journey

OUTPUT FORMAT (strict JSON):
{
  "message": "your warm, natural response to the learner",
  "errors": [
    {
      "type": "grammar|vocab|fluency|pronunciation_placeholder|structure",
      "user_sentence": "what they said",
      "corrected_sentence": "corrected version",
      "explanation": "brief, friendly explanation"
    }
  ],
  "micro_task": "optional micro-task for practice"
}

RULES:
- Always output valid JSON
- Sound like a real, caring human teacher
- Vary your language - don't be repetitive
- Tag 1-3 most important errors per turn
- Balance encouragement with helpful corrections
- Make learners feel they're improving, not failing
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
    def __init__(self, system_prompt: str = TUTOR_SYSTEM_PROMPT, user_id: str = None, db = None):
        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, str]] = []
        self.user_id = user_id
        self.db = db
        self.conversation_memory_loaded = False
        self.past_conversations = []
        self.conversation_summary = None

    def load_conversation_memory(self, user_id: str = None):
        """
        Load recent conversation history from the database.
        This gives the tutor context about past sessions.
        """
        if not self.db:
            return

        uid = user_id or self.user_id
        if not uid:
            return

        try:
            import uuid
            user_uuid = uuid.UUID(uid)

            # Get recent conversations (last 10 turns)
            recent_convos = self.db.get_recent_conversations(user_uuid, limit=10)

            # Get conversation context summary
            context_summary = self.db.get_conversation_context(user_uuid, lookback_days=7)

            # Store in memory for the tutor to reference
            self.past_conversations = recent_convos
            self.conversation_summary = context_summary
            self.conversation_memory_loaded = True

        except Exception as e:
            print(f"Warning: Failed to load conversation memory: {e}")
            self.past_conversations = []
            self.conversation_summary = None

    def _build_memory_enriched_context(self, context: Dict) -> Dict:
        """
        Enrich the context with conversation memory.
        Adds information about past conversations to help the tutor remember.
        """
        if not self.conversation_memory_loaded:
            return context

        # Add conversation memory to context
        if self.past_conversations:
            context['has_conversation_history'] = True
            context['recent_conversation_count'] = len(self.past_conversations)

            # Build a summary of recent conversations
            recent_summary = []
            for conv in self.past_conversations[:5]:  # Last 5 turns
                recent_summary.append({
                    'user_said': conv.get('user_message', '')[:100],  # Truncate to 100 chars
                    'tutor_said': conv.get('tutor_response', '')[:100],
                    'context_type': conv.get('context_type'),
                    'when': str(conv.get('created_at')) if conv.get('created_at') else None
                })

            context['recent_conversation_summary'] = recent_summary

        if self.conversation_summary:
            context['conversation_summary'] = self.conversation_summary

        return context

    def process_user_input(self, user_text: str, context: Dict = None) -> TutorResponse:
        """
        Process user input through two-layer analysis: heuristic + LLM.

        Pipeline:
        1. Load conversation memory if available
        2. Enrich context with past conversation data
        3. Heuristic layer: Fast regex-based error detection
        4. LLM layer: Contextual AI analysis with memory
        5. Merge results: Combine errors from both layers
        6. Generate response: Use LLM message with merged errors

        Args:
            user_text: The learner's input text
            context: Optional context dict (scenario_id, user_level, etc.)

        Returns:
            TutorResponse with merged corrections and feedback
        """
        if context is None:
            context = {}

        # Load conversation memory if not already loaded
        if not self.conversation_memory_loaded and self.user_id and self.db:
            self.load_conversation_memory()

        # Enrich context with conversation memory
        context = self._build_memory_enriched_context(context)

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
        """Generate a warm, natural correction message."""
        import random

        # Natural conversation starters
        starters = [
            "I understood you perfectly!",
            "I hear what you're saying!",
            "Good effort!",
            "Nice try!",
            "You're on the right track!"
        ]

        if len(errors) == 1:
            lead_ins = [
                "Just one small thing -",
                "Let me help with something quick -",
                "One tiny adjustment -",
                "Here's a little tip -"
            ]
            return f"{random.choice(starters)} {random.choice(lead_ins)} {errors[0].corrected_sentence}. {errors[0].explanation} Want to try that again?"
        else:
            lead_ins = [
                "A couple of quick tweaks:",
                "Let me share a couple of things:",
                "Two small adjustments here:",
            ]
            return f"{random.choice(starters)} {random.choice(lead_ins)} {errors[0].corrected_sentence}. {errors[0].explanation} Give it another shot?"

    def _generate_positive_response(self, user_text: str) -> str:
        """Generate warm, varied positive responses."""
        responses = [
            "Perfect! That was really well said.",
            "Excellent! You nailed that one.",
            "Great job! Very natural sounding.",
            "Nice! I wouldn't change a thing.",
            "Spot on! Your English is really improving.",
            "That's it! Exactly right.",
            "Wonderful! You're getting the hang of this.",
            "Fantastic! Keep that up.",
            "Beautiful! That's exactly how a native speaker would say it.",
            "Yes! That's perfect English right there."
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
