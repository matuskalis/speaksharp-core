"""
LLM client wrapper for SpeakSharp.

Supports OpenAI and Anthropic APIs with retry logic, error handling, and logging.
"""

import json
import time
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import config
from app.models import TutorResponse, Error, ErrorType


# System prompts for different tutor modes
TUTOR_BEGINNER_PROMPT = """You are an AI English tutor for SpeakSharp helping BEGINNER learners (A1-B1). Your role is to help them build confidence and correct fundamental mistakes.

BEGINNER MODE GUIDELINES:
1. Be extra warm and encouraging. Build confidence with every interaction.
2. Focus on ONLY 1-2 most critical errors that block communication.
3. Provide DETAILED, simple explanations using basic vocabulary.
4. Always give clear examples showing the pattern.
5. Suggest concrete, easy micro-tasks for immediate practice.
6. Prioritize: subject-verb agreement, basic tenses, articles, word order.

Error Types:
- "grammar": Articles, basic tenses, subject-verb agreement, word order
- "vocab": Basic vocabulary errors, commonly confused words
- "fluency": Hesitations, incomplete sentences
- "structure": Simple sentence structure issues

Output Format (strict JSON):
{
  "message": "Your warm, encouraging response (1-2 sentences)",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The corrected version",
      "explanation": "Detailed but simple explanation with an example (20-30 words)"
    }
  ],
  "micro_task": "A specific, easy practice task (e.g., 'Make 2 more sentences using this pattern: I am/He is/She is')"
}

Important:
- Always respond with valid JSON
- Limit errors to 1-2 items for beginners
- Give clear, encouraging feedback
- Use simple vocabulary in explanations
"""

TUTOR_ADVANCED_PROMPT = """You are an AI English tutor for SpeakSharp helping ADVANCED learners (B2-C2). Your role is to help them achieve native-like fluency and nuance.

ADVANCED MODE GUIDELINES:
1. Be direct and concise. Advanced learners want efficiency.
2. Focus on 2-3 subtle errors: collocations, register, idioms, style, discourse.
3. Provide MINIMAL explanations - just the key insight.
4. Challenge them with sophisticated vocabulary and structures.
5. Suggest tasks that push them to native-level expression.
6. Prioritize: collocation, register, idioms, discourse markers, style.

Error Types:
- "grammar": Subtle tense/aspect issues, conditionals, subjunctive
- "vocab": Unnatural collocations, register mismatches, imprecise word choice
- "fluency": Overly formal/informal register, unnatural phrasing
- "structure": Discourse issues, information structure, emphasis

Output Format (strict JSON):
{
  "message": "Your concise, direct feedback (1 sentence)",
  "errors": [
    {
      "type": "vocab",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The more natural/native version",
      "explanation": "Minimal explanation focusing on why natives say it this way (10-15 words)"
    }
  ],
  "micro_task": "A challenging task pushing native-level skills (e.g., 'Rephrase this using a conditional perfect')"
}

Important:
- Always respond with valid JSON
- Focus on 2-3 subtle, high-level errors
- Be concise - advanced learners don't need hand-holding
- Push them toward native-level expression
"""

SCENARIO_ROLEPLAY_PROMPT = """You are roleplaying a character in an English learning scenario. Your job is to:
1. STAY IN CHARACTER - Respond as the character would in the situation
2. Move the conversation forward naturally
3. Correct errors by modeling correct language in your response, not by explicitly teaching
4. Track whether the learner is meeting their goals
5. ADJUST YOUR LANGUAGE based on the learner's level (details below)

SCENARIO CONTEXT (will be provided in user message):
- Your character/role
- The situation
- The learner's goal
- Success criteria to evaluate
- Learner's level (A1, A2, B1, B2, C1, C2)

LEVEL-SPECIFIC BEHAVIOR:

BEGINNER (A1-A2):
- Use VERY simple vocabulary and short sentences
- Speak slowly and clearly (imagine pauses between words)
- Repeat key words if they seem confused
- Ask simple yes/no questions or offer choices ("Coffee or tea?")
- Be VERY patient and encouraging
- Point out only 1 critical error that blocks communication
- Give simple, clear explanations

INTERMEDIATE (B1-B2):
- Use everyday vocabulary, some idioms are OK
- Speak at normal pace with natural sentence structure
- Ask open-ended questions
- Point out 1-2 errors (grammar, vocabulary, or natural phrasing)
- Encourage more complex responses
- Use more natural conversational fillers ("Well...", "I see", "That makes sense")

ADVANCED (C1-C2):
- Use sophisticated vocabulary, idioms, and nuanced expressions
- Speak naturally as a native would
- Challenge them with complex topics or subtle questions
- Point out subtle errors: unnatural collocations, register issues, style
- Expect near-native fluency
- Focus on polish and naturalness, not basic correctness

ROLEPLAY GUIDELINES:
1. Respond AS THE CHARACTER (e.g., barista, doctor receptionist, new friend)
2. Keep responses short and natural (1-2 sentences for beginners, can be longer for advanced)
3. React authentically to what the learner says
4. Guide them toward completing the task naturally
5. If they make errors, model the correct form in your response
6. After 3-5 turns, evaluate if they've met success criteria

Output Format (strict JSON):
{
  "message": "Your in-character response to the learner (adjusted for their level)",
  "errors": [
    {
      "type": "grammar|vocab|fluency|structure",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The corrected version",
      "explanation": "Brief explanation (10-15 words)"
    }
  ],
  "micro_task": null,
  "scenario_complete": false,
  "success_evaluation": "Brief note on progress toward goals (only if scenario_complete is true)"
}

IMPORTANT:
- ALWAYS adjust your vocabulary and complexity to the learner's level
- Set "scenario_complete": true when learner has met success criteria
- Always respond as the character, never break character
- Keep your message natural and conversational
- Limit corrections based on level (1 for beginners, 2-3 for advanced)
- Return valid JSON
"""


class LLMClient:
    """Wrapper for LLM API calls with retry logic and error handling."""

    def __init__(self):
        self.config = config.llm
        self.provider = self.config.provider
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate API client."""
        if not self.config.api_key:
            if config.enable_llm and config.debug_mode:
                print("⚠️  Warning: No API key configured, using stub mode")
            return

        if self.provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.config.api_key)
            except ImportError:
                print("⚠️  openai package not installed. Install with: pip install openai")
                self.client = None
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError:
                print("⚠️  anthropic package not installed. Install with: pip install anthropic")
                self.client = None

    def call_tutor(
        self,
        user_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TutorResponse:
        """
        Call LLM API to get tutor feedback on user input.

        Args:
            user_text: The user's input text
            context: Optional context dict (drill_type, scenario, level, etc.)

        Returns:
            TutorResponse with message, errors, and optional micro_task
        """
        # If LLM is disabled or client not initialized, use stub
        if not config.enable_llm or not self.client:
            return self._stub_response(user_text, context)

        # Determine tutor mode based on user level
        system_prompt = self._get_system_prompt(context)

        # Build user message with context
        user_message = self._build_user_message(user_text, context)

        # Try API call with retries
        for attempt in range(self.config.retry_attempts):
            try:
                if self.provider == "openai":
                    response = self._call_openai(user_message, system_prompt)
                elif self.provider == "anthropic":
                    response = self._call_anthropic(user_message, system_prompt)
                else:
                    return self._stub_response(user_text, context)

                # Parse and validate response
                return self._parse_response(response, user_text)

            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    if config.debug_mode:
                        print(f"⚠️  API call failed (attempt {attempt + 1}), retrying: {e}")
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    if config.debug_mode:
                        print(f"❌ API call failed after {self.config.retry_attempts} attempts: {e}")
                    # Fall back to stub
                    return self._stub_response(user_text, context)

        return self._stub_response(user_text, context)

    def _get_system_prompt(self, context: Optional[Dict] = None) -> str:
        """
        Get the appropriate system prompt based on mode and user level.

        Args:
            context: Optional context containing 'mode' and 'level' fields

        Returns:
            System prompt string (scenario, beginner, or advanced mode)
        """
        if not context:
            return TUTOR_BEGINNER_PROMPT

        # Scenario mode uses special roleplay prompt
        if context.get('mode') == 'scenario':
            return SCENARIO_ROLEPLAY_PROMPT

        level = context.get('level', '').upper()

        # Advanced mode for B2, C1, C2
        if level in ['B2', 'C1', 'C2']:
            return TUTOR_ADVANCED_PROMPT

        # Beginner mode for A1, A2, B1 or unknown
        return TUTOR_BEGINNER_PROMPT

    def _build_user_message(self, user_text: str, context: Optional[Dict] = None) -> str:
        """Build user message with optional context."""
        if not context:
            return f"Please analyze this student's English:\n\n{user_text}"

        # Special handling for scenario mode
        if context.get("mode") == "scenario":
            return self._build_scenario_message(user_text, context)

        parts = []

        # Add context information
        if context.get("drill_type"):
            parts.append(f"Context: {context['drill_type']} practice")
        if context.get("scenario"):
            parts.append(f"Scenario: {context['scenario']}")
        if context.get("level"):
            parts.append(f"Student level: {context['level']}")

        # Add the user's text
        parts.append(f"\nStudent's response:\n{user_text}")

        return "\n".join(parts)

    def _build_scenario_message(self, user_text: str, context: Dict) -> str:
        """Build message for scenario roleplay mode."""
        from app.scenarios import SCENARIO_TEMPLATES

        scenario_id = context.get("scenario_id", "")
        turn_number = context.get("turn_number", 1)

        scenario = SCENARIO_TEMPLATES.get(scenario_id)
        if not scenario:
            return f"User said: {user_text}"

        # Character name mapping
        character_names = {
            "cafe_ordering": "Barista at Sunrise Café",
            "self_introduction": "Alex, a friendly person at a social event",
            "talk_about_your_day": "A close friend",
            "asking_directions": "A helpful local resident",
            "doctor_appointment": "Medical receptionist at City Medical Center",
            "shopping_clothes": "Sales assistant at a clothing store",
            "job_interview": "HR interviewer at the company",
            "hotel_checkin": "Hotel receptionist at the front desk",
            "restaurant_complaint": "Waiter/Server at the restaurant",
            "bank_inquiry": "Bank representative",
            "making_work_friends": "Friendly coworker in the break room",
            "apartment_viewing": "Landlord or rental agent",
            "flight_delay": "Airline customer service representative",
        }

        character = character_names.get(scenario_id, "Conversation partner")

        # Get learner's level from context or use scenario's level range
        learner_level = context.get("level", scenario.level_min).upper()

        message = f"""SCENARIO CONTEXT:
Your Character: {character}
Situation: {scenario.situation_description}
Learner's Goal: {scenario.user_goal}
Success Criteria: {scenario.success_criteria}
Learner's Level: {learner_level}

Current Turn: {turn_number}
Learner said: "{user_text}"

IMPORTANT: Adjust your vocabulary, sentence complexity, and error corrections based on the learner's level ({learner_level}). Review the LEVEL-SPECIFIC BEHAVIOR section above.

COMPLETION EVALUATION:
- Minimum turns: 3 (don't end too early)
- Maximum turns: 8 (end gracefully even if not perfect)
- Evaluate on Turn 3+: Check if the learner has accomplished their goal
- Set "scenario_complete": true when:
  1. The learner has met the success criteria (even partially)
  2. The conversation has reached a natural conclusion
  3. You've given them enough practice opportunities
- Be flexible: Don't wait for perfection. If they've demonstrated the key skills, complete it.

Respond in character. Guide the conversation naturally toward their goal."""

        return message

    def _call_openai(self, user_message: str, system_prompt: str) -> str:
        """Call OpenAI API."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] OpenAI API call: {self.config.model}")

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )

        return response.choices[0].message.content

    def _call_anthropic(self, user_message: str, system_prompt: str) -> str:
        """Call Anthropic API."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] Anthropic API call: {self.config.model}")

        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ],
            timeout=self.config.timeout
        )

        return response.content[0].text

    def _parse_response(self, response_text: str, user_text: str) -> TutorResponse:
        """Parse LLM response into TutorResponse object."""
        try:
            data = json.loads(response_text)

            # Validate required fields
            message = data.get("message", "I understood you!")
            errors_data = data.get("errors", [])
            micro_task = data.get("micro_task")
            scenario_complete = data.get("scenario_complete")
            success_evaluation = data.get("success_evaluation")

            # Parse errors
            errors = []
            for err_data in errors_data[:5]:  # Limit to 5 errors
                try:
                    error = Error(
                        type=ErrorType(err_data["type"]),
                        user_sentence=err_data["user_sentence"],
                        corrected_sentence=err_data["corrected_sentence"],
                        explanation=err_data["explanation"]
                    )
                    errors.append(error)
                except (KeyError, ValueError) as e:
                    if config.debug_mode:
                        print(f"⚠️  Skipping malformed error: {e}")
                    continue

            return TutorResponse(
                message=message,
                errors=errors,
                micro_task=micro_task,
                scenario_complete=scenario_complete,
                success_evaluation=success_evaluation
            )

        except json.JSONDecodeError as e:
            if config.debug_mode:
                print(f"⚠️  Failed to parse LLM response as JSON: {e}")
                print(f"Response: {response_text[:200]}")

            # Fallback: return basic response
            return TutorResponse(
                message="I understood you!",
                errors=[],
                micro_task=None
            )

    def _stub_response(self, user_text: str, context: Optional[Dict] = None) -> TutorResponse:
        """
        Stub response for when LLM is disabled or unavailable.
        Returns basic encouragement with no errors (heuristic layer will handle errors).
        """
        messages = [
            "I understood you!",
            "Nice! Very natural.",
            "Good job!",
            "Perfect, I understood you clearly.",
        ]

        import random
        message = random.choice(messages)

        return TutorResponse(
            message=message,
            errors=[],
            micro_task=None
        )


# Global client instance
llm_client = LLMClient()


if __name__ == "__main__":
    print("LLM Client Test")
    print("=" * 60)

    # Test configuration
    print(f"\n🔧 Configuration:")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Model: {config.llm.model}")
    print(f"  API Key: {'✓ Set' if config.llm.api_key else '✗ Not set'}")
    print(f"  LLM Enabled: {config.enable_llm}")

    # Test stub mode
    print(f"\n📝 Testing stub mode...")
    client = LLMClient()

    test_inputs = [
        "I go to cinema yesterday.",
        "She don't like coffee.",
        "I want order a coffee please.",
    ]

    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: {test_input}")
        response = client.call_tutor(test_input, context={"drill_type": "practice"})
        print(f"  Message: {response.message}")
        print(f"  Errors: {len(response.errors)}")
        if response.micro_task:
            print(f"  Task: {response.micro_task}")

    print("\n" + "=" * 60)
    print("✅ LLM Client initialized successfully!")

    if not config.llm.api_key and config.enable_llm:
        print("\n⚠️  Note: Running in stub mode. Set API key to test real LLM calls.")
