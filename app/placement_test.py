"""
Placement Test for Vorex - Redesigned with Adaptive Testing

Determines user's English level (A1-C2) through adaptive testing algorithm.
- 36 questions total (6 per level)
- Adaptive algorithm starts at B1 and adjusts based on performance
- More accurate level determination with fewer questions
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import random


class PlacementQuestion(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    correct_answer: int  # Index of correct option (0-3)
    level: str  # A1, A2, B1, B2, C1, C2
    skill_type: str  # grammar, vocabulary, reading, collocations
    explanation: Optional[str] = None


class PlacementTestResult(BaseModel):
    level: str
    score: int
    total_questions: int
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str


class AdaptiveTestState(BaseModel):
    """State for adaptive testing session"""
    session_id: str
    current_level: str
    questions_asked: List[str]  # question_ids already asked
    answers: List[Dict[str, Any]]  # [{question_id, answer, correct, level}]
    consecutive_correct: int
    consecutive_wrong: int
    level_history: List[str]  # track level changes
    is_complete: bool
    final_level: Optional[str] = None


# Expanded Question Bank - 36 Questions (6 per level)
PLACEMENT_QUESTIONS: List[PlacementQuestion] = [
    # ============= A1 Level (6 questions) =============
    PlacementQuestion(
        question_id="a1_grammar_1",
        question_text="I ___ a student.",
        options=["am", "is", "are", "be"],
        correct_answer=0,
        level="A1",
        skill_type="grammar",
        explanation="Use 'am' with 'I' in present simple."
    ),
    PlacementQuestion(
        question_id="a1_grammar_2",
        question_text="She ___ a teacher.",
        options=["am", "is", "are", "be"],
        correct_answer=1,
        level="A1",
        skill_type="grammar",
        explanation="Use 'is' with he/she/it."
    ),
    PlacementQuestion(
        question_id="a1_grammar_3",
        question_text="They ___ from Spain.",
        options=["am", "is", "are", "be"],
        correct_answer=2,
        level="A1",
        skill_type="grammar",
        explanation="Use 'are' with they/we/you."
    ),
    PlacementQuestion(
        question_id="a1_vocab_1",
        question_text="I have two ___.",
        options=["childs", "child", "children", "childrens"],
        correct_answer=2,
        level="A1",
        skill_type="vocabulary",
        explanation="'Children' is the irregular plural of 'child'."
    ),
    PlacementQuestion(
        question_id="a1_vocab_2",
        question_text="The opposite of 'hot' is ___.",
        options=["warm", "cold", "cool", "heat"],
        correct_answer=1,
        level="A1",
        skill_type="vocabulary",
        explanation="'Cold' is the direct opposite of 'hot'."
    ),
    PlacementQuestion(
        question_id="a1_vocab_3",
        question_text="What color is the sky?",
        options=["green", "blue", "red", "yellow"],
        correct_answer=1,
        level="A1",
        skill_type="vocabulary",
        explanation="The sky is typically blue."
    ),

    # ============= A2 Level (6 questions) =============
    PlacementQuestion(
        question_id="a2_grammar_1",
        question_text="She ___ to the cinema yesterday.",
        options=["go", "goes", "went", "going"],
        correct_answer=2,
        level="A2",
        skill_type="grammar",
        explanation="Use simple past 'went' for completed past actions."
    ),
    PlacementQuestion(
        question_id="a2_grammar_2",
        question_text="I ___ dinner when you called.",
        options=["cook", "cooked", "was cooking", "am cooking"],
        correct_answer=2,
        level="A2",
        skill_type="grammar",
        explanation="Past continuous for an action in progress when interrupted."
    ),
    PlacementQuestion(
        question_id="a2_grammar_3",
        question_text="He ___ play tennis every Sunday.",
        options=["don't", "doesn't", "isn't", "aren't"],
        correct_answer=1,
        level="A2",
        skill_type="grammar",
        explanation="Use 'doesn't' with he/she/it in negative present simple."
    ),
    PlacementQuestion(
        question_id="a2_vocab_1",
        question_text="I'm looking ___ my keys. Have you seen them?",
        options=["at", "for", "on", "to"],
        correct_answer=1,
        level="A2",
        skill_type="vocabulary",
        explanation="'Looking for' means searching for something."
    ),
    PlacementQuestion(
        question_id="a2_vocab_2",
        question_text="Can you ___ me a favor?",
        options=["make", "do", "give", "take"],
        correct_answer=1,
        level="A2",
        skill_type="collocations",
        explanation="The collocation is 'do a favor'."
    ),
    PlacementQuestion(
        question_id="a2_vocab_3",
        question_text="I need to ___ an appointment with the doctor.",
        options=["do", "make", "have", "take"],
        correct_answer=1,
        level="A2",
        skill_type="collocations",
        explanation="The collocation is 'make an appointment'."
    ),

    # ============= B1 Level (6 questions) =============
    PlacementQuestion(
        question_id="b1_grammar_1",
        question_text="If I ___ more time, I would learn Spanish.",
        options=["have", "had", "will have", "would have"],
        correct_answer=1,
        level="B1",
        skill_type="grammar",
        explanation="Second conditional uses 'if + past simple' for hypothetical situations."
    ),
    PlacementQuestion(
        question_id="b1_grammar_2",
        question_text="I wish I ___ speak French.",
        options=["can", "could", "will", "would"],
        correct_answer=1,
        level="B1",
        skill_type="grammar",
        explanation="'Wish + could' expresses a desire for an ability you don't have."
    ),
    PlacementQuestion(
        question_id="b1_grammar_3",
        question_text="The book ___ by millions of people.",
        options=["has read", "has been read", "have read", "have been read"],
        correct_answer=1,
        level="B1",
        skill_type="grammar",
        explanation="Present perfect passive: has/have + been + past participle."
    ),
    PlacementQuestion(
        question_id="b1_vocab_1",
        question_text="The meeting has been ___ until next week.",
        options=["put off", "put on", "put up", "put away"],
        correct_answer=0,
        level="B1",
        skill_type="vocabulary",
        explanation="'Put off' means to postpone or delay."
    ),
    PlacementQuestion(
        question_id="b1_vocab_2",
        question_text="I can't ___ up with his behavior anymore.",
        options=["put", "give", "take", "get"],
        correct_answer=0,
        level="B1",
        skill_type="vocabulary",
        explanation="'Put up with' means to tolerate."
    ),
    PlacementQuestion(
        question_id="b1_reading_1",
        question_text="'She was over the moon about the news.' This means she was ___.",
        options=["confused", "extremely happy", "worried", "tired"],
        correct_answer=1,
        level="B1",
        skill_type="reading",
        explanation="'Over the moon' is an idiom meaning extremely happy."
    ),

    # ============= B2 Level (6 questions) =============
    PlacementQuestion(
        question_id="b2_grammar_1",
        question_text="By this time next year, I ___ in Paris for five years.",
        options=["will be living", "will have been living", "am living", "have been living"],
        correct_answer=1,
        level="B2",
        skill_type="grammar",
        explanation="Future perfect continuous for duration up to a future point."
    ),
    PlacementQuestion(
        question_id="b2_grammar_2",
        question_text="I'd rather you ___ smoking.",
        options=["stop", "stopped", "to stop", "stopping"],
        correct_answer=1,
        level="B2",
        skill_type="grammar",
        explanation="'Would rather + past simple' for preferences about others' actions."
    ),
    PlacementQuestion(
        question_id="b2_grammar_3",
        question_text="Not until I got home ___ I had left my wallet.",
        options=["I realized", "did I realize", "I did realize", "realized I"],
        correct_answer=1,
        level="B2",
        skill_type="grammar",
        explanation="Negative inversion: 'Not until...' requires inverted word order."
    ),
    PlacementQuestion(
        question_id="b2_vocab_1",
        question_text="The company's profits have ___ significantly this quarter.",
        options=["raised", "risen", "rose", "arisen"],
        correct_answer=1,
        level="B2",
        skill_type="vocabulary",
        explanation="'Risen' (intransitive) for something that goes up on its own."
    ),
    PlacementQuestion(
        question_id="b2_vocab_2",
        question_text="The project was a complete ___. We achieved all our goals.",
        options=["succeed", "success", "successful", "successfully"],
        correct_answer=1,
        level="B2",
        skill_type="vocabulary",
        explanation="'Success' is the noun form needed after 'a complete'."
    ),
    PlacementQuestion(
        question_id="b2_reading_1",
        question_text="'The proposal was met with fierce opposition.' This means people ___.",
        options=["strongly supported it", "strongly disagreed", "were confused", "ignored it"],
        correct_answer=1,
        level="B2",
        skill_type="reading",
        explanation="'Fierce opposition' indicates strong disagreement."
    ),

    # ============= C1 Level (6 questions) =============
    PlacementQuestion(
        question_id="c1_grammar_1",
        question_text="___ have I seen such a remarkable performance.",
        options=["Rarely", "Never", "Seldom", "All are correct"],
        correct_answer=3,
        level="C1",
        skill_type="grammar",
        explanation="All negative adverbs can start sentences with inversion."
    ),
    PlacementQuestion(
        question_id="c1_grammar_2",
        question_text="Were it not for his help, we ___ the project on time.",
        options=["wouldn't finish", "wouldn't have finished", "didn't finish", "won't finish"],
        correct_answer=1,
        level="C1",
        skill_type="grammar",
        explanation="Inverted third conditional: 'Were it not for' + would have + past participle."
    ),
    PlacementQuestion(
        question_id="c1_grammar_3",
        question_text="No sooner ___ than the phone rang.",
        options=["I had arrived", "had I arrived", "I arrived", "did I arrive"],
        correct_answer=1,
        level="C1",
        skill_type="grammar",
        explanation="'No sooner...than' requires inversion with past perfect."
    ),
    PlacementQuestion(
        question_id="c1_vocab_1",
        question_text="The politician's speech was so ___ that even opponents were convinced.",
        options=["convincing", "compelling", "persuasive", "eloquent"],
        correct_answer=3,
        level="C1",
        skill_type="vocabulary",
        explanation="'Eloquent' best captures fluent, persuasive, and moving speech."
    ),
    PlacementQuestion(
        question_id="c1_vocab_2",
        question_text="Her ___ attention to detail made her an excellent editor.",
        options=["meticulous", "careful", "thorough", "precise"],
        correct_answer=0,
        level="C1",
        skill_type="vocabulary",
        explanation="'Meticulous' conveys extreme care and precision."
    ),
    PlacementQuestion(
        question_id="c1_reading_1",
        question_text="'The findings corroborate previous research.' This means the findings ___.",
        options=["contradict", "support", "question", "extend"],
        correct_answer=1,
        level="C1",
        skill_type="reading",
        explanation="'Corroborate' means to confirm or support with evidence."
    ),

    # ============= C2 Level (6 questions) =============
    PlacementQuestion(
        question_id="c2_grammar_1",
        question_text="Little ___ that this decision would have such consequences.",
        options=["they knew", "did they know", "they did know", "knew they"],
        correct_answer=1,
        level="C2",
        skill_type="grammar",
        explanation="'Little' as negative adverb requires inversion: 'did they know'."
    ),
    PlacementQuestion(
        question_id="c2_grammar_2",
        question_text="So profound ___ the impact that society was forever changed.",
        options=["is", "was", "being", "been"],
        correct_answer=1,
        level="C2",
        skill_type="grammar",
        explanation="'So + adjective + be' inversion in formal writing."
    ),
    PlacementQuestion(
        question_id="c2_grammar_3",
        question_text="___ as it may seem, the evidence is irrefutable.",
        options=["Strange", "Strangely", "Stranger", "Strangest"],
        correct_answer=0,
        level="C2",
        skill_type="grammar",
        explanation="'Adjective + as it may seem' is a concessive structure."
    ),
    PlacementQuestion(
        question_id="c2_vocab_1",
        question_text="The author's use of ___ language created a dreamlike quality.",
        options=["ethereal", "delicate", "subtle", "refined"],
        correct_answer=0,
        level="C2",
        skill_type="vocabulary",
        explanation="'Ethereal' conveys otherworldly, dreamlike qualities."
    ),
    PlacementQuestion(
        question_id="c2_vocab_2",
        question_text="His ___ remarks alienated many supporters.",
        options=["contentious", "controversial", "incendiary", "provocative"],
        correct_answer=2,
        level="C2",
        skill_type="vocabulary",
        explanation="'Incendiary' suggests inflammatory language designed to provoke."
    ),
    PlacementQuestion(
        question_id="c2_reading_1",
        question_text="'The theory has been subjected to rigorous scrutiny.' This means it has been ___.",
        options=["criticized unfairly", "examined thoroughly", "widely accepted", "recently revised"],
        correct_answer=1,
        level="C2",
        skill_type="reading",
        explanation="'Rigorous scrutiny' means thorough, careful examination."
    ),
]


class AdaptivePlacementTest:
    """
    Adaptive placement test that adjusts difficulty based on performance.

    Algorithm:
    1. Start at B1 level
    2. 2 correct in a row → move up a level
    3. 2 wrong in a row → move down a level
    4. Test ends when:
       - Level stabilizes (2+ questions at same level with mixed results), OR
       - Maximum 12 questions reached, OR
       - User reaches ceiling (C2) or floor (A1) and stabilizes
    """

    LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
    MAX_QUESTIONS = 12
    MIN_QUESTIONS = 6

    def __init__(self):
        self.questions_by_level: Dict[str, List[PlacementQuestion]] = {}
        for q in PLACEMENT_QUESTIONS:
            if q.level not in self.questions_by_level:
                self.questions_by_level[q.level] = []
            self.questions_by_level[q.level].append(q)

    def start_test(self, session_id: str) -> AdaptiveTestState:
        """Initialize a new adaptive test session."""
        return AdaptiveTestState(
            session_id=session_id,
            current_level="B1",  # Start at B1
            questions_asked=[],
            answers=[],
            consecutive_correct=0,
            consecutive_wrong=0,
            level_history=["B1"],
            is_complete=False
        )

    def get_next_question(self, state: AdaptiveTestState) -> Optional[PlacementQuestion]:
        """Get the next question based on current state."""
        if state.is_complete:
            return None

        # Get available questions at current level
        available = [
            q for q in self.questions_by_level.get(state.current_level, [])
            if q.question_id not in state.questions_asked
        ]

        # If no questions available at this level, try adjacent levels
        if not available:
            level_idx = self.LEVEL_ORDER.index(state.current_level)
            # Try one level down, then one level up
            for offset in [-1, 1]:
                adj_idx = level_idx + offset
                if 0 <= adj_idx < len(self.LEVEL_ORDER):
                    adj_level = self.LEVEL_ORDER[adj_idx]
                    available = [
                        q for q in self.questions_by_level.get(adj_level, [])
                        if q.question_id not in state.questions_asked
                    ]
                    if available:
                        break

        if not available:
            # No more questions available
            state.is_complete = True
            state.final_level = self._determine_final_level(state)
            return None

        # Return a random question from available ones
        return random.choice(available)

    def process_answer(
        self,
        state: AdaptiveTestState,
        question: PlacementQuestion,
        answer: int
    ) -> AdaptiveTestState:
        """Process an answer and update the test state."""
        is_correct = answer == question.correct_answer

        # Record the answer
        state.questions_asked.append(question.question_id)
        state.answers.append({
            "question_id": question.question_id,
            "answer": answer,
            "correct": is_correct,
            "level": question.level
        })

        # Update consecutive counters
        if is_correct:
            state.consecutive_correct += 1
            state.consecutive_wrong = 0
        else:
            state.consecutive_wrong += 1
            state.consecutive_correct = 0

        # Determine if we should change levels
        level_idx = self.LEVEL_ORDER.index(state.current_level)

        if state.consecutive_correct >= 2 and level_idx < len(self.LEVEL_ORDER) - 1:
            # Move up a level
            state.current_level = self.LEVEL_ORDER[level_idx + 1]
            state.consecutive_correct = 0
            state.level_history.append(state.current_level)
        elif state.consecutive_wrong >= 2 and level_idx > 0:
            # Move down a level
            state.current_level = self.LEVEL_ORDER[level_idx - 1]
            state.consecutive_wrong = 0
            state.level_history.append(state.current_level)

        # Check if test should end
        if self._should_end_test(state):
            state.is_complete = True
            state.final_level = self._determine_final_level(state)

        return state

    def _should_end_test(self, state: AdaptiveTestState) -> bool:
        """Determine if the test should end."""
        num_questions = len(state.answers)

        # Maximum questions reached
        if num_questions >= self.MAX_QUESTIONS:
            return True

        # Minimum questions not yet reached
        if num_questions < self.MIN_QUESTIONS:
            return False

        # Check for level stability (same level appears 3+ times in last 4 entries)
        if len(state.level_history) >= 4:
            recent_levels = state.level_history[-4:]
            for level in self.LEVEL_ORDER:
                if recent_levels.count(level) >= 3:
                    return True

        # Check if user is at ceiling/floor and consistent
        if state.current_level in ["A1", "C2"] and num_questions >= 8:
            # Count answers at this level
            level_answers = [a for a in state.answers if a["level"] == state.current_level]
            if len(level_answers) >= 3:
                return True

        return False

    def _determine_final_level(self, state: AdaptiveTestState) -> str:
        """Determine the final level based on performance."""
        if not state.answers:
            return "B1"

        # Calculate performance at each level
        level_performance: Dict[str, Dict[str, int]] = {
            level: {"correct": 0, "total": 0} for level in self.LEVEL_ORDER
        }

        for answer in state.answers:
            level = answer["level"]
            level_performance[level]["total"] += 1
            if answer["correct"]:
                level_performance[level]["correct"] += 1

        # Find the highest level where user scores >= 50%
        final_level = "A1"
        for level in self.LEVEL_ORDER:
            perf = level_performance[level]
            if perf["total"] == 0:
                continue
            accuracy = perf["correct"] / perf["total"]
            if accuracy >= 0.5:
                final_level = level
            elif accuracy < 0.5 and perf["total"] >= 2:
                # User struggled at this level, stop here
                break

        return final_level

    def evaluate_test(self, state: AdaptiveTestState) -> PlacementTestResult:
        """Generate the final test result."""
        final_level = state.final_level or self._determine_final_level(state)

        # Calculate score
        total_correct = sum(1 for a in state.answers if a["correct"])
        total_questions = len(state.answers)

        # Analyze strengths and weaknesses
        strengths, weaknesses = self._analyze_performance(state)

        # Generate recommendation
        recommendation = self._generate_recommendation(final_level, total_correct, total_questions)

        return PlacementTestResult(
            level=final_level,
            score=total_correct,
            total_questions=total_questions,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation
        )

    def _analyze_performance(self, state: AdaptiveTestState) -> tuple[List[str], List[str]]:
        """Analyze performance by skill type."""
        skill_performance: Dict[str, Dict[str, int]] = {}

        for answer in state.answers:
            q = next((q for q in PLACEMENT_QUESTIONS if q.question_id == answer["question_id"]), None)
            if not q:
                continue

            skill = q.skill_type
            if skill not in skill_performance:
                skill_performance[skill] = {"correct": 0, "total": 0}

            skill_performance[skill]["total"] += 1
            if answer["correct"]:
                skill_performance[skill]["correct"] += 1

        strengths = []
        weaknesses = []

        for skill, perf in skill_performance.items():
            if perf["total"] == 0:
                continue
            accuracy = perf["correct"] / perf["total"]
            skill_name = skill.replace("_", " ").title()
            if accuracy >= 0.7:
                strengths.append(skill_name)
            elif accuracy < 0.4:
                weaknesses.append(skill_name)

        if not strengths:
            strengths = ["Building a solid foundation"]
        if not weaknesses:
            weaknesses = ["Continue practicing to maintain skills"]

        return strengths, weaknesses

    def _generate_recommendation(self, level: str, score: int, total: int) -> str:
        """Generate personalized recommendation."""
        recommendations = {
            "A1": "Start with basic vocabulary and simple sentence structures. Practice everyday conversations and common phrases.",
            "A2": "Focus on past and future tenses. Build vocabulary for common situations like shopping, travel, and work.",
            "B1": "Work on complex sentences, conditionals, and expressing opinions. Expand your vocabulary with phrasal verbs and idioms.",
            "B2": "Focus on advanced grammar like perfect tenses and passive voice. Practice idiomatic expressions and formal/informal register.",
            "C1": "Refine your style with nuanced expressions. Practice advanced writing and formal academic language.",
            "C2": "Polish your near-native skills. Focus on subtle distinctions, literary expressions, and professional communication.",
        }

        base_rec = recommendations.get(level, "Keep practicing regularly!")

        if total > 0:
            accuracy = score / total
            if accuracy >= 0.8:
                prefix = "Excellent performance! "
            elif accuracy >= 0.6:
                prefix = "Great job! "
            else:
                prefix = "Good effort! "
        else:
            prefix = ""

        return f"{prefix}{base_rec}"


# Legacy support - maintain backward compatibility with old linear test
class PlacementTestEvaluator:
    """Legacy evaluator for backward compatibility."""

    LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

    def __init__(self):
        self.questions = PLACEMENT_QUESTIONS
        self.adaptive_test = AdaptivePlacementTest()

    def get_questions(self, num_questions: int = 12) -> List[PlacementQuestion]:
        """Get placement test questions (legacy linear mode)."""
        # Return questions evenly distributed across levels
        questions = []
        per_level = max(1, num_questions // 6)

        for level in self.LEVEL_ORDER:
            level_qs = [q for q in self.questions if q.level == level]
            questions.extend(level_qs[:per_level])

        return questions[:num_questions]

    def evaluate_test(self, answers: List[int]) -> PlacementTestResult:
        """Evaluate legacy linear test."""
        questions = self.get_questions(len(answers))

        # Create a mock adaptive state for evaluation
        state = AdaptiveTestState(
            session_id="legacy",
            current_level="B1",
            questions_asked=[q.question_id for q in questions],
            answers=[
                {
                    "question_id": q.question_id,
                    "answer": a,
                    "correct": a == q.correct_answer,
                    "level": q.level
                }
                for q, a in zip(questions, answers)
            ],
            consecutive_correct=0,
            consecutive_wrong=0,
            level_history=["B1"],
            is_complete=True,
            final_level=None
        )

        return self.adaptive_test.evaluate_test(state)


# Singleton instances
adaptive_placement_test = AdaptivePlacementTest()
placement_evaluator = PlacementTestEvaluator()


if __name__ == "__main__":
    # Test the adaptive placement test
    test = AdaptivePlacementTest()

    print("=== Adaptive Placement Test Demo ===\n")

    # Simulate a B2 level learner
    print("Simulating B2-level learner...")
    state = test.start_test("test_session_1")

    # Answer pattern: correct at A1-B1, mixed at B2, wrong at C1+
    question_count = 0
    while not state.is_complete and question_count < 15:
        question = test.get_next_question(state)
        if not question:
            break

        question_count += 1

        # Simulate answers based on level
        level_idx = AdaptivePlacementTest.LEVEL_ORDER.index(question.level)
        if level_idx <= 2:  # A1, A2, B1 - correct
            answer = question.correct_answer
        elif level_idx == 3:  # B2 - mostly correct
            answer = question.correct_answer if random.random() < 0.7 else (question.correct_answer + 1) % 4
        else:  # C1, C2 - mostly wrong
            answer = (question.correct_answer + 1) % 4 if random.random() < 0.7 else question.correct_answer

        print(f"Q{question_count}: [{question.level}] {question.question_text[:40]}... Answer: {'✓' if answer == question.correct_answer else '✗'}")
        state = test.process_answer(state, question, answer)

    result = test.evaluate_test(state)
    print(f"\n=== Results ===")
    print(f"Level: {result.level}")
    print(f"Score: {result.score}/{result.total_questions}")
    print(f"Strengths: {result.strengths}")
    print(f"Weaknesses: {result.weaknesses}")
    print(f"Recommendation: {result.recommendation}")
