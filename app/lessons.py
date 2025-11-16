from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel


class LessonTask(BaseModel):
    task_type: str  # "transformation", "production", "comprehension", "gap_fill"
    prompt: str
    expected_pattern: Optional[str] = None
    example_answer: Optional[str] = None


class Lesson(BaseModel):
    lesson_id: str
    title: str
    level: str
    skill_targets: List[str]
    duration_minutes: int
    context: str
    target_language: str
    explanation: str
    examples: List[str]
    controlled_practice: List[LessonTask]
    freer_production: LessonTask
    summary: str


LESSON_LIBRARY: Dict[str, Lesson] = {
    "present_simple_basics": Lesson(
        lesson_id="present_simple_basics",
        title="Present Simple - Daily Routines",
        level="A1",
        skill_targets=["present_simple", "daily_routines", "time_expressions"],
        duration_minutes=7,
        context="We use the present simple to talk about habits, routines, and things that are generally true.",
        target_language="Subject + verb (add -s/-es for he/she/it)",
        explanation="When you talk about what you do every day, use the present simple. Remember: I/you/we/they → verb; he/she/it → verb + s",
        examples=[
            "I wake up at 7 AM every day.",
            "She drinks coffee in the morning.",
            "They go to school by bus.",
            "He works in an office."
        ],
        controlled_practice=[
            LessonTask(
                task_type="gap_fill",
                prompt="I ___ (eat) breakfast at 8 AM.",
                expected_pattern="eat",
                example_answer="I eat breakfast at 8 AM."
            ),
            LessonTask(
                task_type="gap_fill",
                prompt="She ___ (watch) TV in the evening.",
                expected_pattern="watches",
                example_answer="She watches TV in the evening."
            ),
            LessonTask(
                task_type="transformation",
                prompt="I / study / English / every day. (Make a sentence)",
                expected_pattern="I study English every day",
                example_answer="I study English every day."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Tell me about your typical morning routine. Use at least 3 sentences.",
            example_answer="I wake up at 7 AM. I eat breakfast and drink coffee. Then I go to work."
        ),
        summary="Great! You practiced the present simple for routines. Remember to add -s for he/she/it."
    ),

    "articles_a_an_the": Lesson(
        lesson_id="articles_a_an_the",
        title="Articles - A, An, The",
        level="A1",
        skill_targets=["articles", "countable_nouns"],
        duration_minutes=6,
        context="Articles (a, an, the) are small but important words that come before nouns.",
        target_language="a/an (first mention, singular), the (specific or already mentioned)",
        explanation="Use 'a' before consonant sounds, 'an' before vowel sounds. Use 'the' when talking about something specific or already mentioned.",
        examples=[
            "I saw a cat in the garden. The cat was black.",
            "She is an engineer.",
            "Can you pass me the salt?",
            "I need a pen and an eraser."
        ],
        controlled_practice=[
            LessonTask(
                task_type="gap_fill",
                prompt="I want ___ apple.",
                expected_pattern="an",
                example_answer="I want an apple."
            ),
            LessonTask(
                task_type="gap_fill",
                prompt="She is ___ teacher.",
                expected_pattern="a",
                example_answer="She is a teacher."
            ),
            LessonTask(
                task_type="gap_fill",
                prompt="I bought a book yesterday. ___ book is very interesting.",
                expected_pattern="The",
                example_answer="I bought a book yesterday. The book is very interesting."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Describe something you bought recently. Use a/an and the correctly.",
            example_answer="I bought a new phone last week. The phone has a great camera."
        ),
        summary="Well done! Remember: a/an for first mention, the for specific things."
    ),

    "past_simple_regular": Lesson(
        lesson_id="past_simple_regular",
        title="Past Simple - Regular Verbs",
        level="A2",
        skill_targets=["past_simple", "regular_verbs", "time_expressions_past"],
        duration_minutes=7,
        context="We use the past simple to talk about finished actions in the past.",
        target_language="verb + -ed (regular verbs)",
        explanation="For regular verbs in the past, add -ed. If the verb ends in -e, just add -d. If it ends in consonant+y, change y to i and add -ed.",
        examples=[
            "I walked to school yesterday.",
            "She studied English last night.",
            "They lived in London for 5 years.",
            "We watched a movie on Saturday."
        ],
        controlled_practice=[
            LessonTask(
                task_type="transformation",
                prompt="I (play) football yesterday.",
                expected_pattern="played",
                example_answer="I played football yesterday."
            ),
            LessonTask(
                task_type="transformation",
                prompt="She (cook) dinner last night.",
                expected_pattern="cooked",
                example_answer="She cooked dinner last night."
            ),
            LessonTask(
                task_type="production",
                prompt="Make a sentence about what you did last weekend. Use a regular verb.",
                example_answer="I visited my grandmother last weekend."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Tell me about your last vacation or trip. Use at least 3 past simple verbs.",
            example_answer="Last summer, I traveled to Spain. I stayed in Barcelona for a week. I visited many museums and walked around the city every day."
        ),
        summary="Excellent! You can now talk about past events using regular verbs + -ed."
    ),

    "making_requests": Lesson(
        lesson_id="making_requests",
        title="Polite Requests - Can/Could/Would",
        level="A2",
        skill_targets=["polite_requests", "modal_verbs", "service_language"],
        duration_minutes=6,
        context="When asking for things or favors, we use polite forms to sound friendly and respectful.",
        target_language="Can/Could/Would you + verb? / I'd like...",
        explanation="'Can you' is direct. 'Could you' and 'Would you' are more polite. 'I'd like' is polite for ordering or requesting.",
        examples=[
            "Can you help me?",
            "Could you pass the salt, please?",
            "Would you mind opening the window?",
            "I'd like a coffee, please."
        ],
        controlled_practice=[
            LessonTask(
                task_type="transformation",
                prompt="Ask someone politely to close the door. (Use 'could')",
                expected_pattern="Could you close the door",
                example_answer="Could you close the door, please?"
            ),
            LessonTask(
                task_type="transformation",
                prompt="Order a sandwich politely at a café. (Use 'I'd like')",
                expected_pattern="I'd like",
                example_answer="I'd like a sandwich, please."
            ),
            LessonTask(
                task_type="production",
                prompt="Ask a stranger for directions politely.",
                example_answer="Excuse me, could you tell me how to get to the train station?"
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Imagine you're in a restaurant. Order your meal and ask for something you need.",
            example_answer="I'd like the pasta, please. Could you also bring me some water? And would you mind bringing extra napkins?"
        ),
        summary="Great work! You can now make polite requests in different situations."
    ),

    "question_formation": Lesson(
        lesson_id="question_formation",
        title="Asking Questions - Wh- and Yes/No",
        level="A1",
        skill_targets=["question_formation", "wh_words", "auxiliary_verbs"],
        duration_minutes=7,
        context="To get information, we ask questions using question words or by inverting subject and verb.",
        target_language="Wh- word + auxiliary + subject + verb? / Auxiliary + subject + verb?",
        explanation="Yes/No questions: Do/Does/Is/Are + subject + verb. Wh- questions: What/Where/When/Why/How + auxiliary + subject + verb.",
        examples=[
            "Do you like coffee?",
            "Where do you live?",
            "What is your name?",
            "How are you?",
            "When does the class start?"
        ],
        controlled_practice=[
            LessonTask(
                task_type="transformation",
                prompt="You / like / pizza. (Make a yes/no question)",
                expected_pattern="Do you like pizza",
                example_answer="Do you like pizza?"
            ),
            LessonTask(
                task_type="transformation",
                prompt="She / live / ? (Add 'where')",
                expected_pattern="Where does she live",
                example_answer="Where does she live?"
            ),
            LessonTask(
                task_type="production",
                prompt="Ask about someone's job using 'what'.",
                example_answer="What do you do? / What is your job?"
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Ask me 3 questions to get to know me better.",
            example_answer="Where are you from? What do you like to do in your free time? Do you have any hobbies?"
        ),
        summary="Excellent! You can now ask both yes/no and information questions."
    ),

    "prepositions_of_time": Lesson(
        lesson_id="prepositions_of_time",
        title="Prepositions of Time - At, In, On",
        level="A2",
        skill_targets=["prepositions_time", "time_expressions"],
        duration_minutes=6,
        context="We use different prepositions with different time expressions.",
        target_language="at (specific times), on (days/dates), in (months/years/longer periods)",
        explanation="Use 'at' for clock times and specific moments. Use 'on' for days and dates. Use 'in' for months, years, seasons, and longer periods.",
        examples=[
            "I wake up at 7 AM.",
            "The meeting is on Monday.",
            "She was born in 1995.",
            "We'll see you in the morning.",
            "The party is on December 25th."
        ],
        controlled_practice=[
            LessonTask(
                task_type="gap_fill",
                prompt="I have class ___ 3 PM.",
                expected_pattern="at",
                example_answer="I have class at 3 PM."
            ),
            LessonTask(
                task_type="gap_fill",
                prompt="My birthday is ___ July.",
                expected_pattern="in",
                example_answer="My birthday is in July."
            ),
            LessonTask(
                task_type="gap_fill",
                prompt="Let's meet ___ Friday.",
                expected_pattern="on",
                example_answer="Let's meet on Friday."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Tell me about your schedule this week. Use at, in, and on.",
            example_answer="I have a meeting on Monday at 9 AM. In the afternoon, I'll work from home. On Wednesday, I have a doctor's appointment at 2 PM."
        ),
        summary="Great! You now know when to use at, in, and on with time expressions."
    ),

    "present_continuous": Lesson(
        lesson_id="present_continuous",
        title="Present Continuous - What's Happening Now",
        level="A2",
        skill_targets=["present_continuous", "action_verbs", "time_now"],
        duration_minutes=7,
        context="We use the present continuous to talk about actions happening right now or around now.",
        target_language="am/is/are + verb-ing",
        explanation="Use this form when something is happening at the moment of speaking, or for temporary situations.",
        examples=[
            "I am studying English right now.",
            "She is watching TV at the moment.",
            "They are playing football in the park.",
            "He is living in London this year."
        ],
        controlled_practice=[
            LessonTask(
                task_type="gap_fill",
                prompt="I ___ (read) a book right now.",
                expected_pattern="am reading",
                example_answer="I am reading a book right now."
            ),
            LessonTask(
                task_type="gap_fill",
                prompt="She ___ (talk) on the phone.",
                expected_pattern="is talking",
                example_answer="She is talking on the phone."
            ),
            LessonTask(
                task_type="transformation",
                prompt="They / study / for the exam. (Make present continuous)",
                expected_pattern="are studying",
                example_answer="They are studying for the exam."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Look around you. Describe what is happening right now. Use 3-4 sentences.",
            example_answer="I am sitting at my desk. I am learning English. The birds are singing outside my window. My coffee is getting cold."
        ),
        summary="Perfect! You can now describe actions happening right now using the present continuous."
    ),

    "comparatives_superlatives": Lesson(
        lesson_id="comparatives_superlatives",
        title="Comparatives and Superlatives",
        level="A2",
        skill_targets=["comparatives", "superlatives", "adjectives"],
        duration_minutes=8,
        context="We use comparatives to compare two things and superlatives to say something is the most/least.",
        target_language="-er/more (comparatives), -est/most (superlatives)",
        explanation="Short adjectives: add -er/-est (big → bigger → biggest). Long adjectives: use more/most (expensive → more expensive → most expensive).",
        examples=[
            "This book is cheaper than that one.",
            "She is taller than her brother.",
            "This is the most interesting movie I've seen.",
            "He is the fastest runner in the team.",
            "Chinese is more difficult than English."
        ],
        controlled_practice=[
            LessonTask(
                task_type="transformation",
                prompt="My car is ___ (fast) than yours.",
                expected_pattern="faster",
                example_answer="My car is faster than yours."
            ),
            LessonTask(
                task_type="transformation",
                prompt="This is the ___ (good) restaurant in town.",
                expected_pattern="best",
                example_answer="This is the best restaurant in town."
            ),
            LessonTask(
                task_type="production",
                prompt="Compare two cities you know.",
                example_answer="New York is bigger than Boston, but Boston is quieter and more relaxed."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Compare yourself now to yourself 5 years ago. What has changed?",
            example_answer="I am more confident than I was 5 years ago. I'm also busier and more independent. I think I'm happier now than before."
        ),
        summary="Excellent! You can now compare things and describe extremes."
    ),

    "future_going_to": Lesson(
        lesson_id="future_going_to",
        title="Future Plans - Going To",
        level="A2",
        skill_targets=["future_going_to", "plans_intentions", "time_future"],
        duration_minutes=6,
        context="We use 'going to' to talk about future plans and intentions.",
        target_language="am/is/are + going to + verb",
        explanation="Use 'going to' when you've already decided to do something in the future. It shows you have a plan or intention.",
        examples=[
            "I'm going to study medicine next year.",
            "She's going to visit her parents this weekend.",
            "They're going to move to a new apartment.",
            "What are you going to do tomorrow?",
            "We're not going to buy a new car this year."
        ],
        controlled_practice=[
            LessonTask(
                task_type="gap_fill",
                prompt="I ___ (go) to the gym tomorrow.",
                expected_pattern="am going to go / 'm going to go",
                example_answer="I'm going to go to the gym tomorrow."
            ),
            LessonTask(
                task_type="transformation",
                prompt="She / study / abroad / next year. (Make 'going to' sentence)",
                expected_pattern="is going to study",
                example_answer="She is going to study abroad next year."
            ),
            LessonTask(
                task_type="production",
                prompt="Tell me about your plans for this weekend.",
                example_answer="I'm going to meet my friends on Saturday. We're going to watch a movie and have dinner together."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="What are your goals for the next year? What are you going to do to achieve them?",
            example_answer="I'm going to improve my English. I'm going to practice every day and speak with native speakers. I'm also going to read more books in English."
        ),
        summary="Great! You can now talk about your future plans and intentions."
    ),

    "past_simple_irregular": Lesson(
        lesson_id="past_simple_irregular",
        title="Past Simple - Irregular Verbs",
        level="A2",
        skill_targets=["past_simple", "irregular_verbs", "storytelling"],
        duration_minutes=7,
        context="Many common verbs have irregular past forms that don't follow the -ed pattern.",
        target_language="Irregular past forms (go→went, eat→ate, see→saw, etc.)",
        explanation="You need to memorize irregular past forms. Common ones: go→went, see→saw, eat→ate, drink→drank, buy→bought, make→made, have→had, do→did.",
        examples=[
            "I went to Paris last summer.",
            "She saw a beautiful sunset yesterday.",
            "We ate dinner at a nice restaurant.",
            "He bought a new phone last week.",
            "They had a great time at the party."
        ],
        controlled_practice=[
            LessonTask(
                task_type="transformation",
                prompt="I (go) to the beach yesterday.",
                expected_pattern="went",
                example_answer="I went to the beach yesterday."
            ),
            LessonTask(
                task_type="transformation",
                prompt="She (see) her old friend at the mall.",
                expected_pattern="saw",
                example_answer="She saw her old friend at the mall."
            ),
            LessonTask(
                task_type="production",
                prompt="Make a sentence about something you ate or drank recently.",
                example_answer="I drank coffee this morning. / I ate pizza for lunch yesterday."
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Tell me about the best day you had last month. What did you do?",
            example_answer="Last month, I went to a concert with my friends. We saw our favorite band and had an amazing time. After the concert, we ate at a great restaurant and talked for hours."
        ),
        summary="Excellent! You can now use irregular verbs to talk about the past."
    ),

    "can_ability_permission": Lesson(
        lesson_id="can_ability_permission",
        title="Can - Ability and Permission",
        level="A1",
        skill_targets=["modal_can", "ability", "permission"],
        duration_minutes=6,
        context="We use 'can' to talk about ability (what we're able to do) and permission (what we're allowed to do).",
        target_language="can/can't + verb (no -s, no to)",
        explanation="Use 'can' for things you know how to do or are able to do. Also use it to ask for permission or give permission. Remember: can + base verb (no 'to').",
        examples=[
            "I can speak English and Spanish.",
            "She can swim very well.",
            "Can you help me with this?",
            "You can use my phone if you need to.",
            "He can't drive yet."
        ],
        controlled_practice=[
            LessonTask(
                task_type="gap_fill",
                prompt="I ___ (can) play the guitar.",
                expected_pattern="can",
                example_answer="I can play the guitar."
            ),
            LessonTask(
                task_type="transformation",
                prompt="She / not / speak / French. (Use can't)",
                expected_pattern="can't speak",
                example_answer="She can't speak French."
            ),
            LessonTask(
                task_type="production",
                prompt="Ask someone if they can do something.",
                example_answer="Can you speak Chinese? / Can you play any musical instruments?"
            )
        ],
        freer_production=LessonTask(
            task_type="production",
            prompt="Tell me 3 things you can do well and 1 thing you can't do (but want to learn).",
            example_answer="I can cook well, I can speak two languages, and I can play tennis. But I can't play the piano yet - I want to learn!"
        ),
        summary="Perfect! You can now talk about abilities and ask for permission."
    )
}


class LessonRunner:
    def __init__(self, lesson: Lesson):
        self.lesson = lesson
        self.current_step = 0
        self.completed_practice = []
        self.user_responses = []

    def start(self) -> str:
        print(f"\n{'='*60}")
        print(f"LESSON: {self.lesson.title}")
        print(f"{'='*60}")
        print(f"Level: {self.lesson.level} | Duration: ~{self.lesson.duration_minutes} minutes")
        print(f"\n📚 Context:")
        print(f"{self.lesson.context}")
        print(f"\n🎯 Target: {self.lesson.target_language}")
        print(f"\n💡 Explanation:")
        print(f"{self.lesson.explanation}")
        print(f"\n✨ Examples:")
        for i, ex in enumerate(self.lesson.examples, 1):
            print(f"  {i}. {ex}")
        print(f"\n{'='*60}\n")
        return "Now let's practice!"

    def get_next_task(self) -> Optional[LessonTask]:
        if self.current_step < len(self.lesson.controlled_practice):
            return self.lesson.controlled_practice[self.current_step]
        elif self.current_step == len(self.lesson.controlled_practice):
            return self.lesson.freer_production
        return None

    def process_response(self, user_response: str) -> Dict:
        self.user_responses.append(user_response)
        task = self.get_next_task()

        if task:
            self.completed_practice.append({
                'task': task,
                'response': user_response
            })
            self.current_step += 1

        is_complete = self.current_step > len(self.lesson.controlled_practice)

        return {
            'accepted': True,
            'feedback': "Good!" if not is_complete else self.lesson.summary,
            'complete': is_complete,
            'next_task': self.get_next_task()
        }

    def finish(self) -> Dict:
        return {
            'lesson_id': self.lesson.lesson_id,
            'completed': True,
            'tasks_completed': len(self.completed_practice),
            'summary': self.lesson.summary,
            'skill_targets': self.lesson.skill_targets
        }


def get_lesson(lesson_id: str) -> Optional[Lesson]:
    return LESSON_LIBRARY.get(lesson_id)


def get_lessons_by_level(level: str) -> List[Lesson]:
    return [l for l in LESSON_LIBRARY.values() if l.level == level]


def list_all_lessons() -> List[str]:
    return list(LESSON_LIBRARY.keys())


if __name__ == "__main__":
    print("Testing Lesson System")
    print("=" * 60)

    lesson = get_lesson("present_simple_basics")
    runner = LessonRunner(lesson)

    print(runner.start())

    print("\n🔹 Controlled Practice")
    for i, task in enumerate(lesson.controlled_practice, 1):
        print(f"\nTask {i}: {task.prompt}")
        print(f"Example answer: {task.example_answer}")

        result = runner.process_response(task.example_answer)
        print(f"Feedback: {result['feedback']}")

    print("\n🔹 Freer Production")
    task = runner.get_next_task()
    print(f"\nTask: {task.prompt}")
    print(f"Example: {task.example_answer}")

    result = runner.process_response(task.example_answer)
    print(f"\n{result['feedback']}")

    final = runner.finish()
    print(f"\n✓ Lesson complete! Skills practiced: {', '.join(final['skill_targets'])}")
    print("\nLesson system test complete!")
