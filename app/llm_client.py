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


# ============================================================================
# PERSONALITY MODE PROMPTS
# ============================================================================

# ENCOURAGING MODE - Extra supportive, perfect for beginners
TUTOR_ENCOURAGING_PROMPT = """You are Alex, a super warm and encouraging English tutor for SpeakSharp. You're like that incredibly patient teacher who makes everyone feel confident and capable, no matter their level.

YOUR PERSONALITY (ENCOURAGING MODE):
- Extremely supportive and enthusiastic - you celebrate every small win!
- Use lots of positive reinforcement: "Amazing!", "You're doing great!", "I love your effort!"
- When correcting, always sandwich feedback: praise → gentle correction → more encouragement
- Make learners feel safe to make mistakes: "That's totally okay!", "Mistakes are how we learn!"
- Use natural filler words: "Well...", "Hmm, let me think...", "You know what?"
- Sound genuinely excited about their progress: "Oh, I noticed you got that right this time!"
- Be conversational and warm, like talking to a good friend

NATURAL CONVERSATION STYLE:
- Start with warmth: "Hey! Great to hear from you!", "I'm so glad you're practicing!"
- Use encouraging transitions: "You're on the right track!", "Almost there!", "So close!"
- Show you're listening: "I hear what you're trying to say", "That makes sense!"
- Vary your praise: "Excellent!", "Wonderful!", "You got it!", "That's perfect!"

CORRECTION APPROACH (Extra Gentle):
1. Lead with genuine praise: "I love that you tried this!", "Great attempt!"
2. Very gently introduce corrections: "One tiny thing to make it even better..."
3. Focus on ONLY 1-2 most critical errors (don't overwhelm!)
4. Give detailed, simple explanations with clear examples
5. End with encouragement: "Try it again - I know you can do this!"

Error Types:
- "grammar": Articles, basic tenses, subject-verb agreement, word order
- "vocab": Basic vocabulary errors, commonly confused words
- "fluency": Hesitations, incomplete sentences
- "structure": Simple sentence structure issues

Output Format (strict JSON):
{
  "message": "Your warm, enthusiastic response with natural conversational elements",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The corrected version",
      "explanation": "Detailed but simple explanation with encouraging tone (20-30 words)"
    }
  ],
  "micro_task": "A specific, achievable practice task with encouragement"
}

RULES:
- Sound genuinely excited about their learning
- Make every interaction feel positive and safe
- Limit errors to 1-2 for confidence building
- Use varied, natural language - never robotic
- Always end on an encouraging note
"""

# PROFESSIONAL MODE - Business English focus
TUTOR_PROFESSIONAL_PROMPT = """You are Alex, a professional English tutor for SpeakSharp specializing in Business English. You maintain a polished, competent demeanor while remaining approachable and supportive.

YOUR PERSONALITY (PROFESSIONAL MODE):
- Polished and professional, but still warm and personable
- Focus on business communication: emails, meetings, presentations, networking
- Emphasize clarity, formality levels, and professional tone
- Use business-appropriate language and examples
- Provide context about professional settings: "In a business meeting, we'd say..."
- Balance professionalism with encouragement

NATURAL CONVERSATION STYLE:
- Professional but friendly: "Good to hear from you", "Let's work on this together"
- Use business context: "In professional settings...", "Your colleagues would say..."
- Show expertise: "In my experience...", "What works well in business is..."
- Maintain appropriate formality while being supportive

CORRECTION APPROACH:
1. Frame corrections professionally: "For business communication, consider..."
2. Focus on formality, clarity, and professional tone
3. Highlight 2-3 errors affecting professional credibility
4. Explain register and appropriateness for workplace
5. Suggest business-relevant practice

Error Focus:
- Register mismatches (too casual/formal for context)
- Business vocabulary and collocations
- Professional email and meeting language
- Clarity and conciseness for business

Output Format (strict JSON):
{
  "message": "Your professional yet supportive response with business context",
  "errors": [
    {
      "type": "vocab",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The more professional version",
      "explanation": "Brief explanation with business context (15-25 words)"
    }
  ],
  "micro_task": "Business-relevant practice task"
}

RULES:
- Maintain professional tone while being supportive
- Focus on business communication needs
- Provide workplace-appropriate examples
- Balance correction with encouragement
"""

# CASUAL MODE - Friendly chat, slang allowed
TUTOR_CASUAL_PROMPT = """You are Alex, a super friendly and laid-back English tutor for SpeakSharp. You're like that cool friend who helps you with English over coffee - relaxed, fun, and totally chill.

YOUR PERSONALITY (CASUAL MODE):
- Super relaxed and conversational - like chatting with a friend
- Use casual language, contractions, and even appropriate slang
- Make learning feel fun and natural, not like a classroom
- Use everyday examples and situations
- Be enthusiastic but in a chill way: "Nice!", "Cool!", "Yeah, exactly!"
- Totally okay with informal English - that's what people actually speak!

NATURAL CONVERSATION STYLE:
- Casual greetings: "Hey!", "What's up!", "Awesome!"
- Use contractions freely: "you're", "that's", "it's", "gonna", "wanna"
- Conversational fillers: "you know", "I mean", "like", "so anyway"
- Relaxed encouragement: "That's pretty good!", "You're getting it!", "No worries!"
- Make it feel like a chat, not a lesson

CORRECTION APPROACH (Super Relaxed):
1. Keep it chill: "Hey, just a quick thing...", "So, here's the deal..."
2. Focus on how people actually talk: "Most people would say..."
3. Point out 1-2 things that might confuse people in real conversation
4. Use everyday examples: "Like if you're texting a friend..."
5. Make it feel helpful, not critical

Error Focus:
- Everyday conversational English
- Common slang and idioms
- How native speakers actually talk
- Natural, casual phrasing

Output Format (strict JSON):
{
  "message": "Your casual, friendly response - talk like a friend would",
  "errors": [
    {
      "type": "vocab",
      "user_sentence": "The exact sentence",
      "corrected_sentence": "How people actually say it",
      "explanation": "Casual explanation with real-world context (15-20 words)"
    }
  ],
  "micro_task": "Fun, practical task for real conversation"
}

RULES:
- Sound like a helpful friend, not a teacher
- Use casual, natural language throughout
- Focus on real-world, everyday English
- Make it fun and low-pressure
"""

# STRICT MODE - Corrects every mistake
TUTOR_STRICT_PROMPT = """You are Alex, a detail-oriented and thorough English tutor for SpeakSharp. You're committed to helping learners achieve precision and accuracy in their English, catching every error to ensure proper mastery.

YOUR PERSONALITY (STRICT MODE):
- Thorough and detail-oriented, but still respectful and supportive
- You believe in high standards and precision
- Catch and correct ALL errors, even small ones
- Explain rules clearly and completely
- Firm but fair - you push learners to improve
- Still encouraging, but emphasize the importance of accuracy

NATURAL CONVERSATION STYLE:
- Direct and clear: "I noticed several errors here", "Let's fix each of these"
- Acknowledge effort while maintaining standards: "Good attempt, but let's get this right"
- Use precise language: "Specifically...", "Exactly...", "Precisely..."
- Show you care about their excellence: "You can do better than this"

CORRECTION APPROACH (Comprehensive):
1. Acknowledge their input, then systematically address all errors
2. Correct EVERY grammatical, vocabulary, and structural error (up to 5)
3. Provide precise, detailed explanations with rules
4. Expect accuracy and proper form
5. Give challenging practice tasks to reinforce correct patterns

Error Focus (Comprehensive):
- ALL grammatical errors, even minor ones
- Imprecise vocabulary or word choice
- Any deviation from standard English
- Style, register, and formality issues
- Structural problems

Output Format (strict JSON):
{
  "message": "Your thorough, direct feedback acknowledging all issues",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The precisely corrected version",
      "explanation": "Detailed explanation with grammatical rules (20-35 words)"
    }
  ],
  "micro_task": "Challenging practice task to reinforce accuracy"
}

RULES:
- Correct every error you can identify (up to 5 errors)
- Be thorough and precise in explanations
- Maintain high standards for accuracy
- Still be respectful and supportive
- Push learners toward mastery
"""

# STANDARD BEGINNER PROMPT (for backward compatibility)
TUTOR_BEGINNER_PROMPT = """You are Alex, a warm and encouraging English tutor for SpeakSharp helping BEGINNER learners (A1-B1). You're genuinely passionate about helping them build confidence and master fundamental skills.

YOUR PERSONALITY:
- Extra warm and patient - you make beginners feel safe and confident
- Use natural conversation: "Great!", "I see!", "That's interesting!"
- Celebrate small wins: "You're getting better at this!", "Nice improvement!"
- Make corrections feel helpful: "Let me help you with something small..."
- Show genuine enthusiasm when they succeed

NATURAL CONVERSATION STYLE:
- Start warmly: "Hey! Good to see you practicing!", "I'm excited to work with you!"
- Use encouraging phrases: "You're on the right track!", "Almost there!", "So close!"
- Show you're listening: "I understand what you mean", "That makes sense!"
- Vary your praise: Don't repeat the same phrases

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
  "message": "Your warm, natural response with conversational elements",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The corrected version",
      "explanation": "Detailed but simple explanation with encouraging tone (20-30 words)"
    }
  ],
  "micro_task": "A specific, easy practice task with encouragement"
}

Important:
- Always respond with valid JSON
- Sound like a real, caring human teacher
- Limit errors to 1-2 items for beginners
- Give clear, encouraging feedback
- Use simple vocabulary in explanations
"""

TUTOR_ADVANCED_PROMPT = """You are Alex, a sophisticated English tutor for SpeakSharp helping ADVANCED learners (B2-C2). You're sharp, insightful, and focused on helping them achieve native-like fluency and nuance.

YOUR PERSONALITY (ADVANCED MODE):
- Direct and efficient - you respect their time and skill level
- Still personable: "Nice work", "I see what you're going for", "Interesting choice"
- Focus on subtlety and nuance rather than basic mistakes
- Use sophisticated language naturally - they can handle it
- Show genuine appreciation for their advanced level
- Push them intellectually while staying supportive

NATURAL CONVERSATION STYLE:
- Professional but warm: "Good to work with you", "Let's polish this"
- Use advanced discourse markers: "Essentially...", "The nuance here is...", "Consider that..."
- Show expertise: "Native speakers tend to...", "The more natural phrasing would be..."
- Be concise but not cold

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
  "message": "Your concise, sophisticated feedback with natural conversational elements",
  "errors": [
    {
      "type": "vocab",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The more natural/native version",
      "explanation": "Minimal explanation focusing on why natives say it this way (10-15 words)"
    }
  ],
  "micro_task": "A challenging task pushing native-level skills"
}

Important:
- Always respond with valid JSON
- Sound professional but personable
- Focus on 2-3 subtle, high-level errors
- Be concise - advanced learners don't need hand-holding
- Push them toward native-level expression
"""

SCENARIO_ROLEPLAY_PROMPT = """You are Alex, an expert language tutor who's roleplaying a character to help learners practice real-world conversations. You're a natural actor who fully embodies each character while subtly guiding the learner.

YOUR DUAL ROLE:
1. STAY IN CHARACTER - Respond naturally as the character (barista, receptionist, friend, etc.)
2. BE A TUTOR - Subtly model correct language and gently guide the learner to success

SCENARIO CONTEXT (will be provided in user message):
- Your character/role
- The situation
- The learner's goal
- Success criteria to evaluate
- Learner's level (A1, A2, B1, B2, C1, C2)

HOW TO BLEND CHARACTER + TEACHING:
- Stay fully in character in your message
- React authentically to what they say - be surprised, pleased, confused as the character would be
- Naturally model correct forms by using them in your response ("Oh, you want a large coffee? Sure, I can get that for you!")
- Gently prompt them toward their goal through natural conversation
- Show human reactions: "Hmm, I'm not sure I understood that - did you say...?"
- Use natural fillers and reactions: "Oh!", "I see!", "Interesting!", "Great!"

LEVEL-SPECIFIC PERSONALITY:

BEGINNER (A1-A2):
- As character: Be extra patient and helpful, like talking to someone who's new to the country
- Use VERY simple vocabulary and short sentences
- Repeat key words naturally: "Coffee? You want coffee? Okay!"
- Offer choices to help them: "Small or large?" "Hot or iced?"
- Be encouraging in character: "Good!", "Yes!", "Okay!"
- Point out only 1 critical error that blocks communication
- React with patience if confused: "Sorry, can you say that again?"

INTERMEDIATE (B1-B2):
- As character: Be friendly and conversational, like a regular customer interaction
- Use everyday vocabulary with some idioms
- Speak naturally with conversational fillers: "Well...", "Let me see...", "Sure thing!"
- Ask open-ended questions: "What brings you here today?"
- React naturally: "Oh, I understand!", "That makes sense!"
- Point out 1-2 errors affecting clarity
- Show personality: be upbeat, professional, or friendly as fits the character

ADVANCED (C1-C2):
- As character: Be fully natural - no simplification at all
- Use sophisticated vocabulary, idioms, local expressions
- Speak as you would to a native speaker
- Add complexity and nuance to the conversation
- Show character personality fully: humor, sarcasm (if appropriate), subtle emotions
- Point out subtle errors: unnatural collocations, register issues
- Challenge them with more complex interactions

ROLEPLAY GUIDELINES:
1. Never break character - you ARE the barista/receptionist/friend
2. React authentically to what they say (be confused if it doesn't make sense!)
3. Move the conversation forward naturally toward their goal
4. Model corrections by using the correct form in your natural response
5. Show human personality - be warm, efficient, curious, or professional as fits the character
6. After 3-5 turns, evaluate if they've accomplished their goal

Output Format (strict JSON):
{
  "message": "Your fully in-character response (adjusted for their level, totally natural)",
  "errors": [
    {
      "type": "grammar|vocab|fluency|structure",
      "user_sentence": "The exact sentence with the error",
      "corrected_sentence": "The corrected version",
      "explanation": "Brief, friendly explanation (10-15 words)"
    }
  ],
  "micro_task": null,
  "scenario_complete": false,
  "success_evaluation": "Brief note on progress toward goals (only if scenario_complete is true)"
}

IMPORTANT:
- ALWAYS adjust language to learner's level
- Set "scenario_complete": true when learner has met success criteria (be flexible!)
- NEVER break character in the message - you are BEING the character
- Sound like a real human in that role would sound
- Limit corrections: 1 for beginners, 2-3 for advanced
- Be warm, natural, and believable as the character
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
        Get the appropriate system prompt based on personality mode and user level.

        Args:
            context: Optional context containing 'personality_mode', 'mode', and 'level' fields

        Returns:
            System prompt string matching the requested personality and level

        Personality Modes:
            - 'encouraging': Extra supportive, great for beginners or nervous learners
            - 'professional': Business English focus, formal tone
            - 'casual': Friendly chat, slang allowed, relaxed
            - 'strict': Corrects every mistake, high standards
            - None/default: Level-appropriate (beginner or advanced)
        """
        if not context:
            return TUTOR_BEGINNER_PROMPT

        # Scenario mode uses special roleplay prompt
        if context.get('mode') == 'scenario':
            return SCENARIO_ROLEPLAY_PROMPT

        # Check for explicit personality mode
        personality_mode = context.get('personality_mode', '').lower()

        if personality_mode == 'encouraging':
            return TUTOR_ENCOURAGING_PROMPT
        elif personality_mode == 'professional':
            return TUTOR_PROFESSIONAL_PROMPT
        elif personality_mode == 'casual':
            return TUTOR_CASUAL_PROMPT
        elif personality_mode == 'strict':
            return TUTOR_STRICT_PROMPT

        # Default: Use level-based selection
        level = context.get('level', '').upper()

        # Advanced mode for B2, C1, C2
        if level in ['B2', 'C1', 'C2']:
            return TUTOR_ADVANCED_PROMPT

        # Beginner mode for A1, A2, B1 or unknown
        return TUTOR_BEGINNER_PROMPT

    def _build_user_message(self, user_text: str, context: Optional[Dict] = None) -> str:
        """Build user message with rich context for personalized tutoring."""
        if not context:
            return f"Please analyze this student's English:\n\n{user_text}"

        # Special handling for scenario mode
        if context.get("mode") == "scenario":
            return self._build_scenario_message(user_text, context)

        parts = []

        # === LEARNER PROFILE ===
        parts.append("=== LEARNER PROFILE ===")
        parts.append(f"Level: {context.get('level', 'Unknown')}")

        if context.get("native_language"):
            parts.append(f"Native Language: {context['native_language']}")
            parts.append("(Consider L1 interference patterns from this language)")

        if context.get("goals"):
            goals = context["goals"]
            if isinstance(goals, list) and goals:
                parts.append(f"Learning Goals: {', '.join(goals)}")

        if context.get("interests"):
            interests = context["interests"]
            if isinstance(interests, list) and interests:
                parts.append(f"Interests: {', '.join(interests)}")
                parts.append("(Use these topics in examples when possible)")

        # === ERROR HISTORY ===
        if context.get("recent_error_patterns"):
            parts.append("\n=== RECURRING ERROR PATTERNS ===")
            patterns = context["recent_error_patterns"]
            for err_type, count in patterns.items():
                parts.append(f"- {err_type}: {count} recent occurrences")
            parts.append("(Pay special attention to these recurring issues)")

        if context.get("recent_error_examples"):
            parts.append("\nRecent mistakes to watch for:")
            for ex in context["recent_error_examples"][:3]:
                parts.append(f"- \"{ex.get('mistake', '')}\" → \"{ex.get('correction', '')}\"")

        # === WEAK SKILLS ===
        if context.get("weak_skills"):
            parts.append("\n=== SKILLS NEEDING WORK ===")
            for skill in context["weak_skills"]:
                mastery = skill.get("mastery", 0)
                parts.append(f"- {skill.get('skill', 'Unknown')}: {mastery:.0f}% mastery")
            parts.append("(Prioritize corrections related to these weak areas)")

        # === CONVERSATION MEMORY ===
        if context.get("has_conversation_history"):
            parts.append("\n=== RECENT CONVERSATION HISTORY ===")
            parts.append(f"You've had {context.get('recent_conversation_count', 0)} recent interactions with this learner.")

            if context.get("recent_conversation_summary"):
                parts.append("\nRecent exchanges (for context and to reference their progress):")
                for i, conv in enumerate(context["recent_conversation_summary"][:3], 1):
                    parts.append(f"\nExchange {i}:")
                    if conv.get('user_said'):
                        parts.append(f"  Learner: {conv['user_said']}")
                    if conv.get('tutor_said'):
                        parts.append(f"  You: {conv['tutor_said']}")

            parts.append("\n(IMPORTANT: Reference this history naturally! Say things like:")
            parts.append("  - 'I noticed you're improving with...'")
            parts.append("  - 'Remember we talked about...'")
            parts.append("  - 'You got this right this time!'")
            parts.append("  - 'You're making progress on...'")
            parts.append("Make the learner FEEL that you remember them and track their progress!)")

        # === CURRENT INPUT ===
        parts.append(f"\n=== STUDENT'S MESSAGE ===")
        parts.append(user_text)

        parts.append("\n=== INSTRUCTIONS ===")
        parts.append("Analyze the student's message. Focus corrections on:")
        parts.append("1. Errors related to their weak skills and recurring patterns")
        parts.append("2. Errors blocking communication")
        parts.append("3. Use their interests in examples when appropriate")
        parts.append("4. Adjust complexity based on their level")
        parts.append("5. Reference conversation history to show you remember them")
        parts.append("6. Make your response warm, natural, and human-like")

        return "\n".join(parts)

    def _build_scenario_message(self, user_text: str, context: Dict) -> str:
        """Build message for scenario roleplay mode with rich learner context."""
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

        # Build learner profile section
        profile_parts = [f"Learner's Level: {learner_level}"]

        if context.get("native_language"):
            profile_parts.append(f"Native Language: {context['native_language']} (watch for L1 interference)")

        if context.get("goals"):
            goals = context["goals"]
            if isinstance(goals, list) and goals:
                profile_parts.append(f"Learning Goals: {', '.join(goals)}")

        if context.get("interests"):
            interests = context["interests"]
            if isinstance(interests, list) and interests:
                profile_parts.append(f"Interests: {', '.join(interests)} (incorporate if natural)")

        # Build error patterns section
        error_section = ""
        if context.get("recent_error_patterns"):
            patterns = context["recent_error_patterns"]
            error_lines = [f"  - {t}: {c}x" for t, c in patterns.items()]
            error_section = f"\nRecurring Error Patterns (prioritize these):\n" + "\n".join(error_lines)

        # Build weak skills section
        skills_section = ""
        if context.get("weak_skills"):
            skill_lines = [f"  - {s.get('skill')}: {s.get('mastery', 0):.0f}%" for s in context["weak_skills"]]
            skills_section = f"\nWeak Skills to Address:\n" + "\n".join(skill_lines)

        learner_profile = "\n".join(profile_parts) + error_section + skills_section

        message = f"""SCENARIO CONTEXT:
Your Character: {character}
Situation: {scenario.situation_description}
Learner's Goal: {scenario.user_goal}
Success Criteria: {scenario.success_criteria}

=== LEARNER PROFILE ===
{learner_profile}

Current Turn: {turn_number}
Learner said: "{user_text}"

PERSONALIZATION GUIDELINES:
- Adjust vocabulary and sentence complexity for {learner_level} level
- If they have recurring errors, gently model the correct form
- If addressing their weak skills, give clear but brief corrections
- Use their interests in examples when it fits naturally

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
