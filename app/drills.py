from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID, uuid4


class MonologuePrompt(BaseModel):
    prompt_id: str
    text: str
    level: str
    category: str  # "daily_life", "opinion", "story", "description"
    time_limit_seconds: int = 180  # 3 minutes default


MONOLOGUE_PROMPTS: Dict[str, MonologuePrompt] = {
    "daily_routine": MonologuePrompt(
        prompt_id="daily_routine",
        text="Describe your typical morning routine from when you wake up until you leave home.",
        level="A1",
        category="daily_life",
        time_limit_seconds=120
    ),
    "favorite_place": MonologuePrompt(
        prompt_id="favorite_place",
        text="Tell me about your favorite place. Where is it? What does it look like? Why do you like it?",
        level="A2",
        category="description",
        time_limit_seconds=150
    ),
    "last_weekend": MonologuePrompt(
        prompt_id="last_weekend",
        text="What did you do last weekend? Tell me about the most interesting thing that happened.",
        level="A2",
        category="story",
        time_limit_seconds=180
    ),
    "future_plans": MonologuePrompt(
        prompt_id="future_plans",
        text="What are your plans for the next year? What do you want to achieve or do?",
        level="A2",
        category="opinion",
        time_limit_seconds=180
    ),
    "hobby_description": MonologuePrompt(
        prompt_id="hobby_description",
        text="Tell me about one of your hobbies. How did you start? What do you enjoy about it?",
        level="B1",
        category="daily_life",
        time_limit_seconds=180
    ),
    "memorable_meal": MonologuePrompt(
        prompt_id="memorable_meal",
        text="Describe the best meal you've ever had. Where were you? What did you eat? Who were you with?",
        level="A2",
        category="story",
        time_limit_seconds=150
    ),
    "learning_english": MonologuePrompt(
        prompt_id="learning_english",
        text="Why are you learning English? What do you find easy or difficult about it?",
        level="B1",
        category="opinion",
        time_limit_seconds=180
    ),
    "hometown": MonologuePrompt(
        prompt_id="hometown",
        text="Describe your hometown or the place where you grew up. What was it like?",
        level="A2",
        category="description",
        time_limit_seconds=180
    )
}


class MonologueSession(BaseModel):
    session_id: UUID = None
    user_id: UUID
    prompt: MonologuePrompt
    started_at: datetime = None
    user_response: str = ""
    word_count: int = 0
    duration_seconds: int = 0
    errors_found: List = []
    completed: bool = False


class JournalPrompt(BaseModel):
    prompt_id: str
    text: str
    level: str
    min_words: int = 50
    category: str  # "reflection", "description", "opinion", "narrative"


JOURNAL_PROMPTS: Dict[str, JournalPrompt] = {
    "today_feeling": JournalPrompt(
        prompt_id="today_feeling",
        text="How are you feeling today? What happened to make you feel this way?",
        level="A1",
        min_words=30,
        category="reflection"
    ),
    "weekend_plan": JournalPrompt(
        prompt_id="weekend_plan",
        text="What are you planning to do this weekend? Who will you see or what will you do?",
        level="A2",
        min_words=50,
        category="narrative"
    ),
    "best_memory": JournalPrompt(
        prompt_id="best_memory",
        text="Write about one of your favorite memories. What happened and why do you remember it?",
        level="A2",
        min_words=80,
        category="narrative"
    ),
    "daily_challenge": JournalPrompt(
        prompt_id="daily_challenge",
        text="What was challenging about today? How did you handle it?",
        level="B1",
        min_words=60,
        category="reflection"
    ),
    "person_admire": JournalPrompt(
        prompt_id="person_admire",
        text="Describe a person you admire. What qualities do they have? Why do you respect them?",
        level="B1",
        min_words=80,
        category="description"
    ),
    "current_goal": JournalPrompt(
        prompt_id="current_goal",
        text="What is one goal you're working towards right now? What steps are you taking to achieve it?",
        level="B1",
        min_words=70,
        category="reflection"
    ),
    "advice_self": JournalPrompt(
        prompt_id="advice_self",
        text="If you could give advice to yourself from 5 years ago, what would you say?",
        level="B1",
        min_words=60,
        category="opinion"
    ),
    "perfect_day": JournalPrompt(
        prompt_id="perfect_day",
        text="Describe your perfect day. What would you do from morning to evening?",
        level="A2",
        min_words=70,
        category="description"
    )
}


class JournalEntry(BaseModel):
    entry_id: UUID = None
    user_id: UUID
    prompt: JournalPrompt
    written_at: datetime = None
    content: str = ""
    word_count: int = 0
    errors_found: List = []
    completed: bool = False


class MonologueRunner:
    def __init__(self, prompt: MonologuePrompt, user_id: UUID):
        self.prompt = prompt
        self.user_id = user_id
        self.session = MonologueSession(
            session_id=uuid4(),
            user_id=user_id,
            prompt=prompt,
            started_at=datetime.now()
        )

    def start(self) -> str:
        print(f"\n{'='*60}")
        print(f"SPEAKING PRACTICE: Daily Monologue")
        print(f"{'='*60}")
        print(f"\n📝 Prompt: {self.prompt.text}")
        print(f"\n⏱ Time limit: {self.prompt.time_limit_seconds // 60} minute(s)")
        print(f"Level: {self.prompt.level}")
        print(f"\n💡 Tip: Speak naturally. Don't worry about making mistakes.")
        print(f"The tutor will help you improve after you finish.")
        print(f"\n{'='*60}\n")
        return "Ready to speak!"

    def submit_response(self, response_text: str, duration_seconds: int = 0) -> Dict:
        """Submit the user's monologue response."""
        self.session.user_response = response_text
        self.session.word_count = len(response_text.split())
        self.session.duration_seconds = duration_seconds
        self.session.completed = True

        return {
            "session_id": self.session.session_id,
            "word_count": self.session.word_count,
            "duration_seconds": duration_seconds,
            "response": response_text
        }

    def get_stats(self) -> Dict:
        """Get session statistics."""
        wpm = 0
        if self.session.duration_seconds > 0:
            wpm = (self.session.word_count / self.session.duration_seconds) * 60

        return {
            "word_count": self.session.word_count,
            "duration_seconds": self.session.duration_seconds,
            "words_per_minute": round(wpm, 1),
            "prompt_category": self.prompt.category,
            "level": self.prompt.level
        }


class JournalRunner:
    def __init__(self, prompt: JournalPrompt, user_id: UUID):
        self.prompt = prompt
        self.user_id = user_id
        self.entry = JournalEntry(
            entry_id=uuid4(),
            user_id=user_id,
            prompt=prompt,
            written_at=datetime.now()
        )

    def start(self) -> str:
        print(f"\n{'='*60}")
        print(f"WRITING PRACTICE: Daily Journal")
        print(f"{'='*60}")
        print(f"\n📝 Prompt: {self.prompt.text}")
        print(f"\n📏 Target: At least {self.prompt.min_words} words")
        print(f"Level: {self.prompt.level}")
        print(f"\n💡 Tip: Write naturally. Focus on expressing your ideas.")
        print(f"The tutor will provide corrections after you submit.")
        print(f"\n{'='*60}\n")
        return "Ready to write!"

    def submit_entry(self, content: str) -> Dict:
        """Submit the journal entry."""
        self.entry.content = content
        self.entry.word_count = len(content.split())
        self.entry.completed = True

        meets_minimum = self.entry.word_count >= self.prompt.min_words

        return {
            "entry_id": self.entry.entry_id,
            "word_count": self.entry.word_count,
            "min_words": self.prompt.min_words,
            "meets_minimum": meets_minimum,
            "content": content
        }

    def get_stats(self) -> Dict:
        """Get entry statistics."""
        return {
            "word_count": self.entry.word_count,
            "min_words": self.prompt.min_words,
            "prompt_category": self.prompt.category,
            "level": self.prompt.level,
            "completion_percentage": round((self.entry.word_count / self.prompt.min_words) * 100, 1)
        }


def get_monologue_prompt(prompt_id: str) -> Optional[MonologuePrompt]:
    return MONOLOGUE_PROMPTS.get(prompt_id)


def get_journal_prompt(prompt_id: str) -> Optional[JournalPrompt]:
    return JOURNAL_PROMPTS.get(prompt_id)


def list_monologue_prompts() -> List[str]:
    return list(MONOLOGUE_PROMPTS.keys())


def list_journal_prompts() -> List[str]:
    return list(JOURNAL_PROMPTS.keys())


if __name__ == "__main__":
    print("Testing Drill System")
    print("=" * 60)

    # Test Monologue
    print("\n1. MONOLOGUE DRILL")
    print("-" * 60)

    user_id = uuid4()
    prompt = get_monologue_prompt("last_weekend")
    runner = MonologueRunner(prompt, user_id)

    print(runner.start())

    # Simulate response
    test_response = """Last weekend was really nice. On Saturday morning, I went to the park with my friends.
    We played football for about two hours. The weather was perfect - sunny but not too hot.
    After that, we had lunch at a café near the park. I ordered a sandwich and iced coffee.
    In the evening, I stayed home and watched a movie with my family.
    On Sunday, I studied English and did some homework. It was a relaxing weekend."""

    result = runner.submit_response(test_response, duration_seconds=90)
    print(f"Submitted response:")
    print(f"  Words: {result['word_count']}")
    print(f"  Duration: {result['duration_seconds']}s")

    stats = runner.get_stats()
    print(f"\nStats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test Journal
    print("\n2. JOURNAL DRILL")
    print("-" * 60)

    j_prompt = get_journal_prompt("today_feeling")
    j_runner = JournalRunner(j_prompt, user_id)

    print(j_runner.start())

    # Simulate entry
    test_entry = """I'm feeling good today. I had a productive morning and finished all my work early.
    The weather is nice, which always makes me feel better. I'm looking forward to meeting my friend later."""

    j_result = j_runner.submit_entry(test_entry)
    print(f"Submitted entry:")
    print(f"  Words: {j_result['word_count']}/{j_result['min_words']}")
    print(f"  Meets minimum: {j_result['meets_minimum']}")

    j_stats = j_runner.get_stats()
    print(f"\nStats:")
    for key, value in j_stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Available monologue prompts:", len(list_monologue_prompts()))
    print("Available journal prompts:", len(list_journal_prompts()))
    print("\nDrill system test complete!")
