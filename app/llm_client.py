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


# System prompt for the tutor
TUTOR_SYSTEM_PROMPT = """You are an AI English tutor for SpeakSharp. Your role is to help learners improve their English through natural, encouraging correction.

Guidelines:
1. Be warm and encouraging. Never be harsh or discouraging.
2. Focus on 1-3 most important errors per response, not every tiny mistake.
3. Provide brief, clear explanations.
4. Suggest a micro-task for immediate practice when appropriate.
5. Respond in natural, conversational language.

Error Types:
- "grammar": Articles, tenses, subject-verb agreement, word order
- "vocab": Wrong word choice, unnatural collocations, register issues
- "fluency": Hesitations, false starts, overly complicated phrasing
- "structure": Sentence structure problems, discourse issues

Output Format (strict JSON):
{
  "message": "Your encouraging response to the learner",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The corrected version",
      "explanation": "Brief explanation of the correction"
    }
  ],
  "micro_task": "Optional: A small practice task based on the error (e.g., 'Try saying that sentence again with the correction')"
}

Important:
- Always respond with valid JSON
- Limit errors array to 3 items maximum
- Be specific with user_sentence and corrected_sentence
- Keep explanations under 20 words
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
            context: Optional context dict (drill_type, scenario, etc.)

        Returns:
            TutorResponse with message, errors, and optional micro_task
        """
        # If LLM is disabled or client not initialized, use stub
        if not config.enable_llm or not self.client:
            return self._stub_response(user_text, context)

        # Build user message with context
        user_message = self._build_user_message(user_text, context)

        # Try API call with retries
        for attempt in range(self.config.retry_attempts):
            try:
                if self.provider == "openai":
                    response = self._call_openai(user_message)
                elif self.provider == "anthropic":
                    response = self._call_anthropic(user_message)
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

    def _build_user_message(self, user_text: str, context: Optional[Dict] = None) -> str:
        """Build user message with optional context."""
        if not context:
            return f"Please analyze this student's English:\n\n{user_text}"

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

    def _call_openai(self, user_message: str) -> str:
        """Call OpenAI API."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] OpenAI API call: {self.config.model}")

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": TUTOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )

        return response.choices[0].message.content

    def _call_anthropic(self, user_message: str) -> str:
        """Call Anthropic API."""
        if config.log_api_calls:
            print(f"[{datetime.now()}] Anthropic API call: {self.config.model}")

        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=TUTOR_SYSTEM_PROMPT,
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
                micro_task=micro_task
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
