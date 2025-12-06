"""
Thinking in English Engine

A conversational practice mode where users express thoughts in English.
Focus on expression, not knowledge testing. Easy questions about the user's life,
with gentle inline corrections.

Hard constraints enforced:
- Max 2 sentences per AI response
- Always ends with a question
- Level-appropriate vocabulary
- Topic guardrails
- Edge case handlers (idk, native language, short answers)
"""

import json
import re
import unicodedata
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

MAX_TURNS_HARD_CAP = 20  # Absolute maximum regardless of settings
DEFAULT_MAX_TURNS = 10
MIN_TURNS_FOR_XP = 6  # Minimum turns to earn XP on early end
XP_FULL_SESSION = 50
XP_PARTIAL_SESSION = 25
FREE_DAILY_SESSIONS = 3  # Cap for free users
MAX_AI_TOKENS = 150  # Hard cap on AI response length

# Topics the AI must deflect away from
FORBIDDEN_TOPICS = [
    "politics", "politician", "election", "government", "democrat", "republican",
    "religion", "god", "church", "mosque", "temple", "pray", "faith", "atheist",
    "death", "dying", "suicide", "kill", "murder",
    "violence", "abuse", "assault", "rape",
    "sex", "sexual", "porn",
    "drugs", "cocaine", "heroin", "meth",
    "illness", "cancer", "disease", "mental health", "depression", "anxiety",
    "money problems", "debt", "bankrupt", "poor",
    "war", "terrorism", "bomb",
]

# Patterns that suggest user needs help
HELP_PATTERNS = [
    r"^i don'?t know\.?$",
    r"^idk\.?$",
    r"^i'?m not sure\.?$",
    r"^help\.?$",
    r"^what\.?\??$",
    r"^huh\.?\??$",
    r"^\?+$",
    r"^i can'?t\.?$",
]

# ============================================================================
# SYSTEM PROMPTS - STRICT FORMAT
# ============================================================================

THINKING_SYSTEM_PROMPT_A1 = """You are Alex, a friendly person having a casual chat with someone learning English. You're genuinely interested in them.

HOW TO TALK:
- Chat like a real friend, not a teacher
- React naturally to what they say - share your own thoughts, relate to their experience
- Ask follow-up questions that show you're actually listening
- Keep your language simple (they're a beginner) but don't be robotic
- If they share something ("I drank coffee"), respond like a human would ("Oh nice! I love coffee in the morning too. Do you put milk in yours?")

WHAT NOT TO DO:
- Don't just say "Good job!" or "Nice!" and stop - that's weird
- Don't correct every small mistake - focus on communication
- Don't act like a teacher giving praise
- Don't ask questions that feel like a test

CORRECTION STYLE:
- Only correct if you genuinely don't understand
- Weave corrections naturally: "So you WENT to the store? What did you buy?"
- Never explain grammar rules

SENSITIVE TOPICS:
If they mention politics, religion, health problems, or money issues, gently redirect: "That sounds tough. Hey, I was wondering - [new topic]?"

RESPOND IN JSON:
{"message": "your natural response", "correction": {"original": null, "corrected": null, "note": null}, "question_asked": "the question you asked, if any"}"""

THINKING_SYSTEM_PROMPT_A2 = """You are Alex, a friendly person chatting with someone who's learning English. You're curious about their life.

HOW TO TALK:
- Have a real conversation - react to what they say, share related thoughts
- Ask follow-up questions based on what they actually told you
- If they say "I went to the park", don't just say "Nice!" - ask what they did there, who they went with, etc.
- Be interested in details - that's what friends do
- Use everyday language, past and present tense are fine

WHAT NOT TO DO:
- Don't give generic praise ("Good job!", "Well done!")
- Don't end conversations with just acknowledgment
- Don't act like you're evaluating them
- Don't rapid-fire questions like it's an interview

CORRECTION STYLE:
- Correct things that sound confusing or very unnatural
- Do it naturally: "Oh so you WENT there? That sounds fun!"
- Don't explain grammar - just model the correct form
- Most turns don't need corrections

SENSITIVE TOPICS:
Gently change subject if they bring up politics, religion, health issues, or money problems.

RESPOND IN JSON:
{"message": "your natural response", "correction": {"original": null, "corrected": null, "note": null}, "question_asked": "your follow-up question, if any"}"""

THINKING_SYSTEM_PROMPT_B1 = """You are Alex, having a genuine conversation with someone who speaks decent English. You're interested in their thoughts and experiences.

HOW TO TALK:
- Talk like you would with any friend - share opinions, ask about theirs
- Dig deeper into topics - ask "why", explore their reasoning
- You can discuss hypotheticals, comparisons, future plans
- React authentically - agree, disagree gently, share your perspective
- Build on what they say rather than jumping to new topics

WHAT NOT TO DO:
- Don't give teacher-like feedback ("Good job!", "Nice sentence!")
- Don't just acknowledge and move on
- Don't interrogate with rapid questions
- Don't be artificially positive about everything they say

CORRECTION STYLE:
- Only correct things that would genuinely confuse a native speaker
- Recast naturally: "Oh so you'd RATHER stay home? Yeah I get that"
- Don't point out corrections explicitly
- Most of the time, just keep the conversation flowing

SENSITIVE TOPICS:
Redirect smoothly if they bring up politics, religion, health, or money: "That's a lot to deal with. Speaking of which - [natural transition]"

RESPOND IN JSON:
{"message": "your natural response", "correction": {"original": null, "corrected": null, "note": null}, "question_asked": "your question, if you asked one"}"""


# Per-turn reminder injected into context
TURN_REMINDER = """
REMEMBER:
- Be a friend having a real conversation, not a teacher giving feedback
- React naturally to what they said - don't just acknowledge and ask a new question
- No grammar lectures - if you correct, weave it in naturally
- Output valid JSON only
"""


# ============================================================================
# STARTER QUESTIONS BY LEVEL
# ============================================================================

STARTER_QUESTIONS = {
    "A1": [
        "Hi! Let's chat. Do you like mornings or evenings?",
        "Hello! Do you drink coffee or tea?",
        "Hi there! What is your favorite day?",
        "Hey! Do you like cooking?",
        "Hello! What is your favorite food?",
        "Hi! Do you have any pets?",
    ],
    "A2": [
        "Hi! What do you usually do after work or school?",
        "Hello! Tell me about your morning routine - what do you do first?",
        "Hey! What kind of music do you listen to?",
        "Hi! How do you spend your free time?",
        "Hello! Do you like where you live? Why?",
        "Hi! What did you do last weekend?",
    ],
    "B1": [
        "Hi! If you could learn any new skill, what would you choose and why?",
        "Hello! What's something you've been thinking about lately?",
        "Hey! Tell me about a hobby you enjoy - what do you like about it?",
        "Hi! Would you say you're more of an introvert or extrovert?",
        "Hello! If you could change one thing about your routine, what would it be?",
        "Hi! What's a goal you're working towards right now?",
    ],
}

# Help responses when user says "idk" etc
HELP_RESPONSES = {
    "A1": [
        ("It's okay! Let me ask something easier. Do you like pizza?", "Do you like pizza?"),
        ("No problem! Here's a simple one. What color do you like?", "What color do you like?"),
        ("That's fine! Easy question: Do you like music?", "Do you like music?"),
    ],
    "A2": [
        ("That's okay! Let me try another question. What did you eat for breakfast today?", "What did you eat for breakfast today?"),
        ("No worries! Here's an easier one: What do you usually do in the evening?", "What do you usually do in the evening?"),
        ("It's fine! Tell me: Do you prefer staying home or going out?", "Do you prefer staying home or going out?"),
    ],
    "B1": [
        ("That's totally fine! Let me ask something different. What kind of movies do you enjoy watching?", "What kind of movies do you enjoy watching?"),
        ("No problem! Here's another one: If you had a free day tomorrow, what would you do?", "If you had a free day tomorrow, what would you do?"),
        ("It's okay! Tell me about the last book or show you enjoyed.", "What was the last book or show you enjoyed?"),
    ],
}

# Short answer prompts
SHORT_ANSWER_PROMPTS = [
    "Can you tell me a bit more about that?",
    "Interesting! Why is that?",
    "Oh! Can you explain a little more?",
]

# Native language detection - simple heuristic
def contains_non_latin(text: str) -> bool:
    """Check if text contains significant non-Latin characters."""
    non_latin_count = 0
    total_alpha = 0
    for char in text:
        if char.isalpha():
            total_alpha += 1
            # Check if character is outside basic Latin
            if unicodedata.category(char) == 'Lo':  # Other Letter
                non_latin_count += 1
            elif ord(char) > 127 and not unicodedata.category(char).startswith('L'):
                pass  # Accented Latin is OK
            elif ord(char) > 255:  # Non-ASCII, non-Latin-Extended
                non_latin_count += 1

    if total_alpha == 0:
        return False
    return (non_latin_count / total_alpha) > 0.3


def contains_forbidden_topic(text: str) -> bool:
    """Check if text contains forbidden topics."""
    text_lower = text.lower()
    for topic in FORBIDDEN_TOPICS:
        if topic in text_lower:
            return True
    return False


def is_help_request(text: str) -> bool:
    """Check if user is asking for help or saying idk."""
    text_clean = text.strip().lower()
    for pattern in HELP_PATTERNS:
        if re.match(pattern, text_clean, re.IGNORECASE):
            return True
    return False


def is_short_answer(text: str) -> bool:
    """Check if answer is too short to be meaningful."""
    words = text.strip().split()
    return len(words) <= 2


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ThinkingTurn:
    """A single turn in a thinking session."""
    turn_number: int
    user_message: str
    ai_response: str
    question_asked: str
    correction: Optional[Dict[str, str]] = None
    user_word_count: int = 0
    had_correction: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        self.user_word_count = len(self.user_message.split())
        self.had_correction = bool(self.correction and self.correction.get("original"))


@dataclass
class ThinkingSession:
    """A Thinking in English session."""
    session_id: str
    user_id: str
    level: str
    turns: List[ThinkingTurn] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: Optional[str] = None
    max_turns: int = DEFAULT_MAX_TURNS
    short_answer_count: int = 0  # Track consecutive short answers
    help_request_count: int = 0  # Track help requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "level": self.level,
            "turns": [asdict(t) for t in self.turns],
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "max_turns": self.max_turns,
            "current_turn": len(self.turns),
            "is_complete": len(self.turns) >= self.max_turns or self.ended_at is not None,
        }

    def get_duration_seconds(self) -> int:
        """Get session duration in seconds."""
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.ended_at) if self.ended_at else datetime.utcnow()
        return int((end - start).total_seconds())


# ============================================================================
# ANALYTICS EVENTS
# ============================================================================

@dataclass
class ThinkEvent:
    """Base class for think analytics events."""
    user_id: str
    event_type: str = ""  # Set by subclass __post_init__
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionStartedEvent(ThinkEvent):
    """Fired when a think session starts."""
    session_id: str = ""
    level: str = ""
    source: str = "learn"  # where user came from

    def __post_init__(self):
        self.event_type = "think_session_started"


@dataclass
class TurnCompletedEvent(ThinkEvent):
    """Fired when a turn is completed."""
    session_id: str = ""
    turn_index: int = 0
    user_word_count: int = 0
    had_correction: bool = False

    def __post_init__(self):
        self.event_type = "think_turn_completed"


@dataclass
class SessionCompletedEvent(ThinkEvent):
    """Fired when a session completes (10 turns)."""
    session_id: str = ""
    turns: int = 0
    duration_sec: int = 0
    total_words: int = 0
    corrections_count: int = 0

    def __post_init__(self):
        self.event_type = "think_session_completed"


@dataclass
class SessionAbandonedEvent(ThinkEvent):
    """Fired when user ends session early."""
    session_id: str = ""
    turns_done: int = 0
    duration_sec: int = 0

    def __post_init__(self):
        self.event_type = "think_session_abandoned"


# ============================================================================
# THINKING ENGINE
# ============================================================================

class ThinkingEngine:
    """Engine for Thinking in English conversations."""

    def __init__(self):
        self.sessions: Dict[str, ThinkingSession] = {}
        self.user_active_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.user_daily_sessions: Dict[str, Dict[str, int]] = {}  # user_id -> {date: count}
        self.events: List[ThinkEvent] = []  # In-memory event log (should be sent to analytics)

    def log_event(self, event: ThinkEvent):
        """Log an analytics event."""
        self.events.append(event)
        # In production, send to analytics service
        print(f"[THINK_EVENT] {event.event_type}: {event.to_dict()}")

    def get_system_prompt(self, level: str) -> str:
        """Get the appropriate system prompt for user level."""
        if level == "A1":
            return THINKING_SYSTEM_PROMPT_A1
        elif level == "A2":
            return THINKING_SYSTEM_PROMPT_A2
        else:
            return THINKING_SYSTEM_PROMPT_B1

    def get_starter_question(self, level: str) -> str:
        """Get a random starter question for the level."""
        import random
        questions = STARTER_QUESTIONS.get(level, STARTER_QUESTIONS["A2"])
        return random.choice(questions)

    def get_help_response(self, level: str) -> Tuple[str, str]:
        """Get a help response for user who says idk."""
        import random
        responses = HELP_RESPONSES.get(level, HELP_RESPONSES["A2"])
        return random.choice(responses)

    def check_session_limit(self, user_id: str, is_paid: bool) -> bool:
        """Check if user can start a new session (free user limit)."""
        if is_paid:
            return True

        today = datetime.utcnow().date().isoformat()
        user_sessions = self.user_daily_sessions.get(user_id, {})
        today_count = user_sessions.get(today, 0)
        return today_count < FREE_DAILY_SESSIONS

    def increment_session_count(self, user_id: str):
        """Increment daily session count for user."""
        today = datetime.utcnow().date().isoformat()
        if user_id not in self.user_daily_sessions:
            self.user_daily_sessions[user_id] = {}
        self.user_daily_sessions[user_id][today] = self.user_daily_sessions[user_id].get(today, 0) + 1

    def get_active_session(self, user_id: str) -> Optional[ThinkingSession]:
        """Get user's active session if one exists."""
        session_id = self.user_active_sessions.get(user_id)
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if not session.ended_at:
                return session
        return None

    def create_session(self, user_id: str, level: str, source: str = "learn") -> ThinkingSession:
        """Create a new session for user."""
        import uuid

        # End any existing session
        existing = self.get_active_session(user_id)
        if existing:
            self.end_session(existing.session_id, force=True)

        session_id = str(uuid.uuid4())
        session = ThinkingSession(
            session_id=session_id,
            user_id=user_id,
            level=level,
            max_turns=DEFAULT_MAX_TURNS,
        )

        self.sessions[session_id] = session
        self.user_active_sessions[user_id] = session_id
        self.increment_session_count(user_id)

        # Log event
        self.log_event(SessionStartedEvent(
            user_id=user_id,
            session_id=session_id,
            level=level,
            source=source,
        ))

        return session

    def end_session(self, session_id: str, force: bool = False) -> Optional[Dict[str, Any]]:
        """End a session and return summary."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        session.ended_at = datetime.utcnow().isoformat()
        summary = self.generate_session_summary(session)

        # Log event
        turns_done = len(session.turns)
        if turns_done >= session.max_turns:
            self.log_event(SessionCompletedEvent(
                user_id=session.user_id,
                session_id=session_id,
                turns=turns_done,
                duration_sec=session.get_duration_seconds(),
                total_words=summary["total_words"],
                corrections_count=summary["corrections_count"],
            ))
        else:
            self.log_event(SessionAbandonedEvent(
                user_id=session.user_id,
                session_id=session_id,
                turns_done=turns_done,
                duration_sec=session.get_duration_seconds(),
            ))

        # Clean up
        if session.user_id in self.user_active_sessions:
            if self.user_active_sessions[session.user_id] == session_id:
                del self.user_active_sessions[session.user_id]

        if not force:
            del self.sessions[session_id]

        return summary

    def build_conversation_context(self, session: ThinkingSession) -> str:
        """Build conversation context from previous turns."""
        if not session.turns:
            return ""

        context_parts = ["CONVERSATION SO FAR:"]
        # Keep last 4 turns for context (not too long)
        recent_turns = session.turns[-4:]
        for turn in recent_turns:
            context_parts.append(f"User: {turn.user_message}")
            context_parts.append(f"You: {turn.ai_response}")

        context_parts.append(TURN_REMINDER)
        return "\n".join(context_parts)

    def preprocess_user_message(self, message: str, session: ThinkingSession) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Preprocess user message and handle edge cases.
        Returns (processed_message, special_response_or_none)
        """
        message = message.strip()

        # Check for native language (non-Latin characters)
        if contains_non_latin(message):
            return message, {
                "message": "I'd love to hear that in English! Try your best - I'll help if you need it. " +
                          self.get_help_response(session.level)[1],
                "correction": None,
                "question_asked": self.get_help_response(session.level)[1],
                "special": "native_language"
            }

        # Check for help request
        if is_help_request(message):
            session.help_request_count += 1
            response, question = self.get_help_response(session.level)
            return message, {
                "message": response,
                "correction": None,
                "question_asked": question,
                "special": "help_request"
            }

        # Check for forbidden topics
        if contains_forbidden_topic(message):
            redirect_questions = {
                "A1": "Let's talk about something fun! Do you like movies?",
                "A2": "That's a big topic! Tell me, what's your favorite way to relax?",
                "B1": "That's quite complex! Let's keep it light - what have you been enjoying lately?",
            }
            q = redirect_questions.get(session.level, redirect_questions["A2"])
            return message, {
                "message": "Interesting thought! " + q,
                "correction": None,
                "question_asked": q,
                "special": "topic_redirect"
            }

        # Check for very short answer
        if is_short_answer(message):
            session.short_answer_count += 1
            if session.short_answer_count == 1:
                # First time: ask for more
                return message, {
                    "message": "Got it! " + SHORT_ANSWER_PROMPTS[0],
                    "correction": None,
                    "question_asked": SHORT_ANSWER_PROMPTS[0],
                    "special": "short_answer_prompt"
                }
            # Second time: just accept and move on
            session.short_answer_count = 0
            return message, None

        # Reset short answer counter on normal message
        session.short_answer_count = 0
        return message, None

    def parse_llm_response(self, response_text: str, level: str) -> Dict[str, Any]:
        """Parse the LLM JSON response with validation."""
        try:
            text = response_text.strip()
            # Handle markdown code blocks
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            parsed = json.loads(text.strip())

            # Validate required fields
            message = parsed.get("message", "")
            if not message:
                raise ValueError("Empty message")

            # Enforce max length (rough check: ~15 words per sentence, max 2 sentences)
            words = message.split()
            if len(words) > 40:
                # Truncate to first 2 sentences
                sentences = re.split(r'[.!?]+', message)
                message = '. '.join(sentences[:2]).strip()
                if not message.endswith(('?', '.', '!')):
                    message += '?'
                parsed["message"] = message

            # Validate correction format
            correction = parsed.get("correction")
            if correction:
                if not isinstance(correction, dict):
                    parsed["correction"] = None
                elif not correction.get("original") or correction.get("original") == "null":
                    parsed["correction"] = None

            # Ensure question_asked exists
            if not parsed.get("question_asked"):
                # Extract question from message
                if "?" in message:
                    q_parts = message.split("?")
                    for part in reversed(q_parts[:-1]):
                        q = part.strip().split(".")[-1].strip() + "?"
                        if len(q) > 5:
                            parsed["question_asked"] = q
                            break
                if not parsed.get("question_asked"):
                    parsed["question_asked"] = "What do you think?"

            return parsed

        except (json.JSONDecodeError, ValueError) as e:
            # Fallback response
            fallback_questions = {
                "A1": "That's nice! Do you like it?",
                "A2": "Interesting! Can you tell me more?",
                "B1": "I see! What do you think about that?",
            }
            q = fallback_questions.get(level, fallback_questions["A2"])
            return {
                "message": q,
                "correction": None,
                "question_asked": q,
            }

    def add_turn(self, session: ThinkingSession, user_message: str, ai_response: Dict[str, Any]) -> ThinkingTurn:
        """Add a turn to the session."""
        correction = ai_response.get("correction")
        if correction and (not correction.get("original") or correction.get("original") == "null"):
            correction = None

        turn = ThinkingTurn(
            turn_number=len(session.turns) + 1,
            user_message=user_message,
            ai_response=ai_response.get("message", ""),
            question_asked=ai_response.get("question_asked", ""),
            correction=correction,
        )
        session.turns.append(turn)

        # Log event
        self.log_event(TurnCompletedEvent(
            user_id=session.user_id,
            session_id=session.session_id,
            turn_index=turn.turn_number,
            user_word_count=turn.user_word_count,
            had_correction=turn.had_correction,
        ))

        return turn

    def generate_session_summary(self, session: ThinkingSession) -> Dict[str, Any]:
        """Generate end-of-session summary."""
        total_turns = len(session.turns)
        corrections = []
        user_word_count = 0

        for turn in session.turns:
            user_word_count += turn.user_word_count
            if turn.correction and turn.correction.get("original"):
                corrections.append({
                    "original": turn.correction["original"],
                    "corrected": turn.correction.get("corrected", ""),
                    "note": turn.correction.get("note", "")
                })

        # Calculate XP
        xp_earned = 0
        if total_turns >= session.max_turns:
            xp_earned = XP_FULL_SESSION
        elif total_turns >= MIN_TURNS_FOR_XP:
            xp_earned = XP_PARTIAL_SESSION

        # Generate strengths
        strengths = []
        if total_turns >= session.max_turns:
            strengths.append("Great job completing a full conversation!")
        elif total_turns >= MIN_TURNS_FOR_XP:
            strengths.append("Good practice session!")

        if user_word_count > 80:
            strengths.append("You expressed yourself with lots of detail!")
        elif user_word_count > 40:
            strengths.append("You shared your thoughts clearly!")

        if len(corrections) == 0:
            strengths.append("Your English was natural and clear!")
        elif len(corrections) < total_turns / 3:
            strengths.append("Very few corrections needed - well done!")

        if not strengths:
            strengths.append("You practiced thinking in English - that's what matters!")

        return {
            "total_turns": total_turns,
            "total_words": user_word_count,
            "corrections_count": len(corrections),
            "corrections": corrections[:5],
            "strengths": strengths,
            "xp_earned": xp_earned,
            "duration_seconds": session.get_duration_seconds(),
        }


# Global engine instance
thinking_engine = ThinkingEngine()
