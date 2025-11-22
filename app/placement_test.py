"""
Placement Test for SpeakSharp

Determines user's English level (A1-C2) through adaptive testing.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class PlacementQuestion(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    correct_answer: int  # Index of correct option (0-3)
    level: str  # A1, A2, B1, B2, C1, C2
    skill_type: str  # grammar, vocabulary, comprehension
    explanation: Optional[str] = None


class PlacementTestResult(BaseModel):
    level: str
    score: int  # Out of 10
    strengths: List[str]
    weaknesses: List[str]
    recommendation: str


# Placement Test Questions Database
# Questions progress from A1 (easiest) to C2 (hardest)
PLACEMENT_QUESTIONS: List[PlacementQuestion] = [
    # A1 Level Questions
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
        question_id="a1_vocab_1",
        question_text="I have two ___.",
        options=["childs", "child", "children", "childrens"],
        correct_answer=2,
        level="A1",
        skill_type="vocabulary",
        explanation="'Children' is the plural of 'child'."
    ),

    # A2 Level Questions
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
        question_id="a2_vocab_1",
        question_text="I'm looking ___ my keys. Have you seen them?",
        options=["at", "for", "on", "to"],
        correct_answer=1,
        level="A2",
        skill_type="vocabulary",
        explanation="'Looking for' means searching for something."
    ),

    # B1 Level Questions
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
        question_id="b1_comprehension_1",
        question_text="The meeting has been ___ until next week due to scheduling conflicts.",
        options=["put off", "put on", "put up", "put away"],
        correct_answer=0,
        level="B1",
        skill_type="vocabulary",
        explanation="'Put off' means to postpone or delay."
    ),

    # B2 Level Questions
    PlacementQuestion(
        question_id="b2_grammar_1",
        question_text="By this time next year, I ___ living in Paris for five years.",
        options=["will be", "will have been", "am", "have been"],
        correct_answer=1,
        level="B2",
        skill_type="grammar",
        explanation="Future perfect continuous describes duration up to a future point."
    ),

    PlacementQuestion(
        question_id="b2_vocab_1",
        question_text="The company's profits have ___ significantly this quarter.",
        options=["raised", "risen", "rose", "arise"],
        correct_answer=1,
        level="B2",
        skill_type="vocabulary",
        explanation="'Risen' (intransitive) is correct; 'raised' requires an object."
    ),

    # C1 Level Questions
    PlacementQuestion(
        question_id="c1_grammar_1",
        question_text="___ have I encountered such blatant disregard for professional standards.",
        options=["Rarely", "Seldom", "Hardly ever", "Seldom if ever"],
        correct_answer=0,
        level="C1",
        skill_type="grammar",
        explanation="Negative inversion with 'rarely' creates formal emphasis."
    ),

    PlacementQuestion(
        question_id="c1_vocab_1",
        question_text="The politician's speech was so ___ that even her opponents were convinced.",
        options=["convincing", "compelling", "persuasive", "eloquent"],
        correct_answer=3,
        level="C1",
        skill_type="vocabulary",
        explanation="'Eloquent' best captures fluent, persuasive, and moving speech."
    ),

    # C2 Level Questions
    PlacementQuestion(
        question_id="c2_grammar_1",
        question_text="Little ___ that this decision would have such far-reaching consequences.",
        options=["they knew", "did they know", "they did know", "knew they"],
        correct_answer=1,
        level="C2",
        skill_type="grammar",
        explanation="Negative inversion with 'little' requires auxiliary 'did'."
    ),

    PlacementQuestion(
        question_id="c2_vocab_1",
        question_text="The author's use of ___ language created a dreamlike quality in the narrative.",
        options=["ethereal", "delicate", "subtle", "refined"],
        correct_answer=0,
        level="C2",
        skill_type="vocabulary",
        explanation="'Ethereal' best conveys otherworldly, dreamlike qualities."
    ),
]


class PlacementTestEvaluator:
    """Evaluates placement test and determines user's level."""

    LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

    def __init__(self):
        self.questions = PLACEMENT_QUESTIONS

    def get_questions(self, num_questions: int = 10) -> List[PlacementQuestion]:
        """
        Get placement test questions.
        For adaptive testing, we start with mid-level questions.
        """
        # For now, return all questions in order
        # In future, can implement adaptive selection
        return self.questions[:num_questions]

    def evaluate_test(self, answers: List[int]) -> PlacementTestResult:
        """
        Evaluate user's answers and determine their level.

        Args:
            answers: List of selected option indices (0-3)

        Returns:
            PlacementTestResult with level and feedback
        """
        questions = self.get_questions(len(answers))

        # Calculate score by level
        level_scores = {level: {"correct": 0, "total": 0} for level in self.LEVEL_ORDER}

        for i, (question, answer) in enumerate(zip(questions, answers)):
            level = question.level
            level_scores[level]["total"] += 1

            if answer == question.correct_answer:
                level_scores[level]["correct"] += 1

        # Determine user's level
        determined_level = self._determine_level(level_scores)

        # Calculate overall score
        total_correct = sum(answer == question.correct_answer
                           for answer, question in zip(answers, questions))
        score = total_correct

        # Generate feedback
        strengths, weaknesses = self._analyze_performance(questions, answers)
        recommendation = self._generate_recommendation(determined_level, score)

        return PlacementTestResult(
            level=determined_level,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation
        )

    def _determine_level(self, level_scores: Dict[str, Dict[str, int]]) -> str:
        """
        Determine user's level based on their performance at each level.

        Logic:
        - If user gets 100% at a level, they're at least that level
        - Find the highest level where they get 50%+ correct
        - If they struggle at a level, that's their ceiling
        """
        user_level = "A1"  # Default

        for level in self.LEVEL_ORDER:
            total = level_scores[level]["total"]
            if total == 0:
                continue

            correct = level_scores[level]["correct"]
            percentage = (correct / total) * 100

            # If they get 50% or more at this level, they're at least this level
            if percentage >= 50:
                user_level = level
            else:
                # They struggled at this level, so they're likely the previous level
                break

        return user_level

    def _analyze_performance(
        self,
        questions: List[PlacementQuestion],
        answers: List[int]
    ) -> tuple[List[str], List[str]]:
        """Analyze strengths and weaknesses."""
        grammar_correct = 0
        grammar_total = 0
        vocab_correct = 0
        vocab_total = 0

        for question, answer in zip(questions, answers):
            is_correct = (answer == question.correct_answer)

            if question.skill_type == "grammar":
                grammar_total += 1
                if is_correct:
                    grammar_correct += 1
            elif question.skill_type in ["vocabulary", "comprehension"]:
                vocab_total += 1
                if is_correct:
                    vocab_correct += 1

        strengths = []
        weaknesses = []

        # Analyze grammar
        if grammar_total > 0:
            grammar_pct = (grammar_correct / grammar_total) * 100
            if grammar_pct >= 70:
                strengths.append("grammar")
            elif grammar_pct < 50:
                weaknesses.append("grammar")

        # Analyze vocabulary
        if vocab_total > 0:
            vocab_pct = (vocab_correct / vocab_total) * 100
            if vocab_pct >= 70:
                strengths.append("vocabulary")
            elif vocab_pct < 50:
                weaknesses.append("vocabulary")

        # Default messages
        if not strengths:
            strengths = ["You're building a solid foundation"]
        if not weaknesses:
            weaknesses = ["Keep practicing to maintain your skills"]

        return strengths, weaknesses

    def _generate_recommendation(self, level: str, score: int) -> str:
        """Generate personalized recommendation."""
        level_recommendations = {
            "A1": "Start with basic vocabulary and simple sentence structures. Focus on everyday conversations.",
            "A2": "Practice simple past and future tenses. Build vocabulary for common situations.",
            "B1": "Work on complex sentences, conditionals, and expressing opinions. Expand your vocabulary.",
            "B2": "Focus on advanced grammar structures, idiomatic expressions, and fluency in discussions.",
            "C1": "Refine your style, work on nuanced expressions, and practice formal/informal register.",
            "C2": "Polish your near-native skills. Focus on subtle expressions and advanced vocabulary.",
        }

        base_rec = level_recommendations.get(level, "Keep practicing regularly!")

        if score >= 9:
            return f"Excellent work! {base_rec}"
        elif score >= 7:
            return f"Great job! {base_rec}"
        elif score >= 5:
            return f"Good effort! {base_rec}"
        else:
            return f"You're on your way! {base_rec}"


# Singleton instance
placement_evaluator = PlacementTestEvaluator()


if __name__ == "__main__":
    # Test the placement test
    evaluator = PlacementTestEvaluator()

    # Test scenario 1: A1 learner (gets first 2 right, rest wrong)
    print("Test 1: A1 Learner")
    answers_a1 = [0, 2, 0, 0, 0, 0, 0, 0, 0, 0]  # Only first 2 correct
    result = evaluator.evaluate_test(answers_a1)
    print(f"Level: {result.level}")
    print(f"Score: {result.score}/10")
    print(f"Strengths: {result.strengths}")
    print(f"Weaknesses: {result.weaknesses}")
    print(f"Recommendation: {result.recommendation}")
    print()

    # Test scenario 2: B2 learner (gets up to B2 mostly right)
    print("Test 2: B2 Learner")
    answers_b2 = [0, 2, 2, 1, 1, 0, 1, 1, 0, 0]  # Gets A1-B2 right, C1-C2 wrong
    result = evaluator.evaluate_test(answers_b2)
    print(f"Level: {result.level}")
    print(f"Score: {result.score}/10")
    print(f"Strengths: {result.strengths}")
    print(f"Weaknesses: {result.weaknesses}")
    print(f"Recommendation: {result.recommendation}")
    print()

    # Test scenario 3: C2 learner (gets everything right)
    print("Test 3: C2 Learner")
    answers_c2 = [0, 2, 2, 1, 1, 0, 1, 1, 0, 0]  # All correct
    correct_answers = [q.correct_answer for q in evaluator.get_questions(10)]
    result = evaluator.evaluate_test(correct_answers)
    print(f"Level: {result.level}")
    print(f"Score: {result.score}/10")
    print(f"Strengths: {result.strengths}")
    print(f"Weaknesses: {result.weaknesses}")
    print(f"Recommendation: {result.recommendation}")
