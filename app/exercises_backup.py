"""
Exercise library for grammar and vocabulary practice.

Contains multiple choice, fill-in-blank, and sentence correction exercises
organized by level (A1-C2) and skill type (grammar, vocabulary).
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
import random


class ExerciseType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SENTENCE_CORRECTION = "sentence_correction"


class SkillType(str, Enum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"


@dataclass
class Exercise:
    """Represents a single exercise."""
    exercise_id: str
    exercise_type: ExerciseType
    level: str  # A1, A2, B1, B2, C1, C2
    skill: SkillType
    question: str
    correct_answer: str
    explanation: str
    hint: Optional[str] = None
    options: Optional[List[str]] = None  # For multiple choice
    skill_keys: Optional[List[str]] = None  # Links to skill_definitions for mastery tracking


# Exercise library organized by type and level
EXERCISES: Dict[str, Exercise] = {}


def _add_exercise(exercise: Exercise):
    """Helper to add exercise to library."""
    EXERCISES[exercise.exercise_id] = exercise


# ============================================================================
# MULTIPLE CHOICE - GRAMMAR
# ============================================================================

# A1 Level
_add_exercise(Exercise(
    exercise_id="mc-gram-a1-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="I ___ a student.",
    options=["am", "is", "are", "be"],
    correct_answer="am",
    explanation="With 'I', we always use 'am'. Example: I am happy, I am here.",
    hint="Think about the verb 'to be' with 'I'.",
    skill_keys=["grammar_present_simple_affirmative"]
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="She ___ breakfast every morning.",
    options=["eat", "eats", "eating", "ate"],
    correct_answer="eats",
    explanation="For he/she/it in present simple, we add -s to the verb.",
    hint="Third person singular needs -s."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="___ you like coffee?",
    options=["Do", "Does", "Are", "Is"],
    correct_answer="Do",
    explanation="Questions with 'you' use 'do' as the auxiliary verb.",
    hint="What auxiliary verb do we use with 'you'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="There ___ two books on the table.",
    options=["is", "are", "be", "been"],
    correct_answer="are",
    explanation="'There are' is used with plural nouns (two books).",
    hint="Is the noun singular or plural?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="My sister ___ a doctor.",
    options=["is", "are", "am", "be"],
    correct_answer="is",
    explanation="For he/she/it, we use 'is' with the verb 'to be'.",
    hint="What form of 'be' goes with 'she'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="They ___ from Spain.",
    options=["is", "am", "are", "be"],
    correct_answer="are",
    explanation="For 'they' (plural), we use 'are'.",
    hint="What form of 'be' goes with 'they'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="I ___ not hungry.",
    options=["am", "is", "are", "do"],
    correct_answer="am",
    explanation="With 'I', we always use 'am' (even in negatives).",
    hint="First person singular of 'be'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="He ___ to work by bus.",
    options=["go", "goes", "going", "goed"],
    correct_answer="goes",
    explanation="Third person singular (he/she/it) adds -s or -es to the verb.",
    hint="Present simple with he/she/it."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="We ___ football on Sundays.",
    options=["plays", "play", "playing", "played"],
    correct_answer="play",
    explanation="With 'we', the verb stays in base form (no -s).",
    hint="Base form for we/they/I/you."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="___ she live in London?",
    options=["Do", "Does", "Is", "Are"],
    correct_answer="Does",
    explanation="Questions with he/she/it use 'does' as the auxiliary verb.",
    hint="Auxiliary verb for third person questions."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="This is ___ umbrella.",
    options=["a", "an", "the", "some"],
    correct_answer="an",
    explanation="We use 'an' before words that start with a vowel sound (umbrella starts with 'u').",
    hint="A or an before vowel sounds?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="I have ___ apple.",
    options=["a", "an", "some", "any"],
    correct_answer="an",
    explanation="We use 'an' before words that start with a vowel sound.",
    hint="Which article before 'apple'?"
))

# A2 Level
_add_exercise(Exercise(
    exercise_id="mc-gram-a2-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="I ___ TV when the phone rang.",
    options=["watched", "was watching", "watch", "have watched"],
    correct_answer="was watching",
    explanation="Past continuous (was watching) is used for an action in progress when another action interrupted it.",
    hint="What tense describes an ongoing past action?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="She has ___ to Paris three times.",
    options=["go", "went", "been", "going"],
    correct_answer="been",
    explanation="Present perfect uses 'have/has + past participle'. 'Been' is the past participle of 'go' when talking about visiting places.",
    hint="What's the past participle form used with 'have'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="This is ___ interesting book I've ever read.",
    options=["more", "most", "the most", "the more"],
    correct_answer="the most",
    explanation="Superlatives require 'the' + most/est. 'The most interesting' compares to all others.",
    hint="What form do we use for superlatives?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="I ___ my homework when my friend called.",
    options=["did", "was doing", "have done", "do"],
    correct_answer="was doing",
    explanation="Past continuous describes an action in progress when interrupted by another past action.",
    hint="Ongoing action in the past."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="We ___ never seen a whale before.",
    options=["have", "has", "had", "are"],
    correct_answer="have",
    explanation="Present perfect with 'we' uses 'have' + past participle.",
    hint="Present perfect with plural subject."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="She is ___ than her brother.",
    options=["tall", "taller", "tallest", "more tall"],
    correct_answer="taller",
    explanation="Comparatives for short adjectives add -er. 'Taller' compares two people.",
    hint="Comparing two people."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="I'm going ___ buy some groceries.",
    options=["for", "to", "at", "in"],
    correct_answer="to",
    explanation="'Going to + verb' expresses future plans or intentions.",
    hint="Future intention structure."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="There isn't ___ milk in the fridge.",
    options=["some", "any", "a", "many"],
    correct_answer="any",
    explanation="In negatives and questions, we use 'any' instead of 'some'.",
    hint="Negative sentences use...?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="She ___ a new car last month.",
    options=["buys", "bought", "has bought", "buying"],
    correct_answer="bought",
    explanation="'Last month' indicates past simple tense. 'Bought' is past of 'buy'.",
    hint="Past time marker = past simple."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="You ___ wear a seatbelt. It's the law.",
    options=["can", "must", "might", "could"],
    correct_answer="must",
    explanation="'Must' expresses obligation or necessity (it's required by law).",
    hint="Strong obligation."
))

# B1 Level
_add_exercise(Exercise(
    exercise_id="mc-gram-b1-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="If I ___ you, I would apply for that job.",
    options=["am", "was", "were", "be"],
    correct_answer="were",
    explanation="In second conditional (hypothetical situations), we use 'were' for all subjects, including I/he/she.",
    hint="What form of 'be' is used in hypothetical conditions?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="She asked me if I ___ help her.",
    options=["can", "could", "will", "would"],
    correct_answer="could",
    explanation="In reported speech, 'can' changes to 'could' when the reporting verb is past tense.",
    hint="How does 'can' change in reported speech?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="I've been studying English ___ three years.",
    options=["since", "for", "during", "while"],
    correct_answer="for",
    explanation="'For' is used with periods of time (three years), while 'since' is used with points in time (2020).",
    hint="'For' or 'since' with duration?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="I wish I ___ more time to finish the project.",
    options=["have", "had", "would have", "having"],
    correct_answer="had",
    explanation="After 'wish', we use past tense to express something we want but don't have.",
    hint="Wish + past tense for unreal situations."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="The book ___ by millions of people worldwide.",
    options=["has read", "has been read", "have read", "have been read"],
    correct_answer="has been read",
    explanation="Passive voice: has + been + past participle. The book doesn't read, it is read.",
    hint="Passive voice with present perfect."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="You ___ told me about the meeting earlier!",
    options=["should", "should have", "must", "must have"],
    correct_answer="should have",
    explanation="'Should have + past participle' expresses regret or criticism about the past.",
    hint="Criticism about something in the past."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="I'd rather ___ at home tonight.",
    options=["to stay", "staying", "stay", "stayed"],
    correct_answer="stay",
    explanation="'Would rather' is followed by the base form of the verb.",
    hint="Structure: would rather + base verb."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="Despite ___ tired, she finished the marathon.",
    options=["be", "being", "was", "to be"],
    correct_answer="being",
    explanation="'Despite' is followed by a noun or gerund (-ing form).",
    hint="Despite + gerund."
))

# B2 Level
_add_exercise(Exercise(
    exercise_id="mc-gram-b2-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="If I had known about the problem, I ___ you sooner.",
    options=["would help", "would have helped", "will help", "helped"],
    correct_answer="would have helped",
    explanation="Third conditional uses 'would have + past participle' for hypothetical past situations.",
    hint="What structure follows 'If I had known'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Neither the manager ___ the employees were informed about the changes.",
    options=["nor", "or", "and", "but"],
    correct_answer="nor",
    explanation="'Neither...nor' is a correlative conjunction used to join two negative alternatives.",
    hint="What word pairs with 'neither'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="By the time she arrives, we ___ already finished dinner.",
    options=["will", "will have", "would", "have"],
    correct_answer="will have",
    explanation="Future perfect ('will have + past participle') describes an action completed before a future time.",
    hint="What tense expresses completion before a future event?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Not only ___ the exam, but she also got the highest score.",
    options=["she passed", "did she pass", "she did pass", "passed she"],
    correct_answer="did she pass",
    explanation="'Not only' at the start of a sentence requires inversion (auxiliary + subject + verb).",
    hint="Inversion after 'Not only' at sentence start."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="I'd sooner ___ than ask him for help.",
    options=["to die", "dying", "die", "died"],
    correct_answer="die",
    explanation="'Would sooner' (like 'would rather') is followed by the base form of the verb.",
    hint="Same structure as 'would rather'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="The proposal, ___ was submitted last week, has been approved.",
    options=["that", "which", "what", "who"],
    correct_answer="which",
    explanation="In non-defining relative clauses (with commas), we use 'which' for things, not 'that'.",
    hint="Non-defining relative clause for things."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="She ___ have left already; her car is gone.",
    options=["can", "must", "should", "would"],
    correct_answer="must",
    explanation="'Must have + past participle' expresses a logical deduction about the past.",
    hint="Logical conclusion based on evidence."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Were I ___ the decision, I would choose differently.",
    options=["make", "making", "to make", "made"],
    correct_answer="to make",
    explanation="Formal conditional inversion: 'Were I to...' replaces 'If I were to...'",
    hint="Formal inverted conditional structure."
))

# C1 Level
_add_exercise(Exercise(
    exercise_id="mc-gram-c1-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="___ had I sat down than the phone rang.",
    options=["No sooner", "Hardly", "Scarcely", "Barely"],
    correct_answer="No sooner",
    explanation="'No sooner...than' is an inverted structure for emphasizing sequence. Note: Hardly/Scarcely use 'when', not 'than'.",
    hint="Which phrase pairs correctly with 'than'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="It's high time you ___ looking for a new job.",
    options=["start", "started", "starting", "have started"],
    correct_answer="started",
    explanation="'It's high time' is followed by past tense to express that something should have happened already.",
    hint="What tense follows 'It's high time'?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Little ___ he know what challenges lay ahead.",
    options=["does", "did", "had", "would"],
    correct_answer="did",
    explanation="'Little' at the start of a sentence requires inversion with past simple.",
    hint="Inversion with negative adverb."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="I object ___ being treated like a child.",
    options=["for", "to", "at", "against"],
    correct_answer="to",
    explanation="'Object to' is followed by a gerund (-ing). Note: 'to' here is a preposition, not infinitive marker.",
    hint="'Object' takes which preposition?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="She couldn't help but ___ at his joke.",
    options=["laugh", "laughing", "to laugh", "laughed"],
    correct_answer="laugh",
    explanation="'Can't help but + base verb' is a formal construction meaning 'cannot avoid doing'.",
    hint="'Cannot help but' + base form."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Under no circumstances ___ leave the building during the drill.",
    options=["you should", "should you", "you must", "must you"],
    correct_answer="should you",
    explanation="Negative adverbial phrases at the start require inversion: auxiliary + subject.",
    hint="Inversion after 'Under no circumstances'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="The painting is thought ___ over 500 years old.",
    options=["being", "to be", "it is", "that is"],
    correct_answer="to be",
    explanation="Passive reporting structure: subject + is thought/believed/said + to be.",
    hint="Passive reporting structure."
))

# C2 Level
_add_exercise(Exercise(
    exercise_id="mc-gram-c2-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="___ be it from me to criticize, but I think there's a better approach.",
    options=["Far", "So", "As", "Let"],
    correct_answer="Far",
    explanation="'Far be it from me to...' is a formal expression meaning 'I don't want to (but I will).'",
    hint="This is a fixed expression meaning 'I don't want to...'"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="Try ___ he might, he couldn't solve the puzzle.",
    options=["as", "however", "though", "while"],
    correct_answer="as",
    explanation="'Try as he might' is an inverted concessive structure using 'as'.",
    hint="Inverted concessive clause."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="So ___ was the damage that the building had to be demolished.",
    options=["extensive", "extend", "extensively", "extension"],
    correct_answer="extensive",
    explanation="'So + adjective + was/were' is an inverted structure for emphasis.",
    hint="Inverted structure for emphasis."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="___ it not been for your help, I would have failed.",
    options=["Had", "Were", "Should", "If"],
    correct_answer="Had",
    explanation="'Had it not been for' is formal inverted third conditional (= If it hadn't been for).",
    hint="Formal inverted third conditional."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="He's not so much lazy ___ unmotivated.",
    options=["as", "but", "than", "and"],
    correct_answer="as",
    explanation="'Not so much X as Y' means 'Y rather than X' - comparison structure.",
    hint="'Not so much... as...' structure."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="Suffice ___ to say, the meeting didn't go well.",
    options=["it", "this", "that", "so"],
    correct_answer="it",
    explanation="'Suffice it to say' is a fixed expression meaning 'it's enough to say'.",
    hint="Fixed expression: 'Suffice __ to say'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="What with one thing and ___, I never finished the report.",
    options=["another", "other", "others", "the other"],
    correct_answer="another",
    explanation="'What with one thing and another' is an idiom meaning 'because of many circumstances'.",
    hint="Fixed idiomatic expression."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="The company's ___ financial practices led to its downfall.",
    options=["nefarious", "notorious", "infamous", "dubious"],
    correct_answer="nefarious",
    explanation="'Nefarious' means wicked or criminal, typically used for deliberate wrongdoing.",
    hint="Meaning 'wicked or criminal'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="Be that ___ it may, we must proceed with caution.",
    options=["as", "what", "which", "how"],
    correct_answer="as",
    explanation="'Be that as it may' is a formal expression meaning 'nevertheless' or 'even so'.",
    hint="Fixed formal expression."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="His ___ personality made him unsuitable for customer-facing roles.",
    options=["taciturn", "loquacious", "garrulous", "verbose"],
    correct_answer="taciturn",
    explanation="'Taciturn' means habitually reserved and uncommunicative.",
    hint="Word meaning 'not talkative'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="The harder you work, the ___ you'll achieve.",
    options=["more", "most", "much", "many"],
    correct_answer="more",
    explanation="'The + comparative, the + comparative' structure for proportional relationship.",
    hint="Proportional comparative structure."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="The article was filled with ___ language designed to inflame public opinion.",
    options=["incendiary", "inflammatory", "provocative", "contentious"],
    correct_answer="incendiary",
    explanation="'Incendiary' means designed to cause anger or violence, especially in speech.",
    hint="Meaning 'deliberately inflammatory'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="Come what ___, we will stand by our principles.",
    options=["may", "might", "will", "shall"],
    correct_answer="may",
    explanation="'Come what may' is a fixed expression meaning 'whatever happens'.",
    hint="Fixed expression with 'come'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="The professor's ___ knowledge of the subject was truly impressive.",
    options=["encyclopedic", "comprehensive", "extensive", "thorough"],
    correct_answer="encyclopedic",
    explanation="'Encyclopedic knowledge' means extremely comprehensive and detailed knowledge.",
    hint="Meaning 'extremely comprehensive'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="Lest we ___, let me remind you of our objectives.",
    options=["forget", "should forget", "will forget", "would forget"],
    correct_answer="forget",
    explanation="'Lest' (formal: for fear that) takes subjunctive or 'should', but bare infinitive is also used.",
    hint="Formal conjunction with subjunctive."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="The speaker's ___ wit kept the audience entertained throughout.",
    options=["scintillating", "sparkling", "brilliant", "sharp"],
    correct_answer="scintillating",
    explanation="'Scintillating' means brilliantly clever or entertaining, especially wit.",
    hint="Formal word for 'brilliantly clever'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="___ though the task was, she completed it successfully.",
    options=["Difficult", "Difficulty", "Difficultly", "Difficulties"],
    correct_answer="Difficult",
    explanation="Inverted concessive: adjective + though/as + subject + verb.",
    hint="Inverted concessive structure."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="The plan was criticized for being too ___ and impractical.",
    options=["quixotic", "pragmatic", "realistic", "feasible"],
    correct_answer="quixotic",
    explanation="'Quixotic' means exceedingly idealistic and unrealistic.",
    hint="Meaning 'unrealistically idealistic'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="The terms of the agreement are ___ negotiation.",
    options=["open to", "subject to", "liable to", "prone to"],
    correct_answer="subject to",
    explanation="'Subject to' means dependent on or conditional upon something.",
    hint="Meaning 'conditional upon'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="His ___ demeanor belied his inner turmoil.",
    options=["phlegmatic", "excitable", "nervous", "anxious"],
    correct_answer="phlegmatic",
    explanation="'Phlegmatic' means calm and unemotional in temperament.",
    hint="Meaning 'calm and unemotional'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="In no way ___ responsible for the accident.",
    options=["I am", "am I", "I was", "was I"],
    correct_answer="am I",
    explanation="Negative expressions at the start require inversion.",
    hint="Inversion after 'In no way'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="The detective's ___ investigation uncovered new evidence.",
    options=["assiduous", "casual", "cursory", "superficial"],
    correct_answer="assiduous",
    explanation="'Assiduous' means showing great care and perseverance.",
    hint="Meaning 'extremely diligent'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c2-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="The matter is one ___ requires immediate attention.",
    options=["that", "which", "what", "whom"],
    correct_answer="that",
    explanation="After 'one' (meaning 'thing'), we use 'that' not 'which'.",
    hint="Relative pronoun after 'one'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="The government's ___ approach to the crisis was widely criticized.",
    options=["dilatory", "prompt", "swift", "immediate"],
    correct_answer="dilatory",
    explanation="'Dilatory' means slow to act, causing delay.",
    hint="Formal word meaning 'delaying'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c2-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="Her ___ refusal to compromise made negotiations difficult.",
    options=["obdurate", "flexible", "amenable", "compliant"],
    correct_answer="obdurate",
    explanation="'Obdurate' means stubbornly refusing to change one's opinion.",
    hint="Meaning 'stubbornly inflexible'."
))

# ============================================================================
# MULTIPLE CHOICE - VOCABULARY
# ============================================================================

# A1 Level
_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="What's the opposite of 'hot'?",
    options=["warm", "cold", "cool", "wet"],
    correct_answer="cold",
    explanation="Hot and cold are opposites (antonyms).",
    hint="Think about temperature."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I need to buy some bread. I'm going to the ___.",
    options=["library", "hospital", "bakery", "school"],
    correct_answer="bakery",
    explanation="A bakery is a place where bread and pastries are sold.",
    hint="Where do you buy bread?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="The day after Monday is ___.",
    options=["Wednesday", "Tuesday", "Sunday", "Friday"],
    correct_answer="Tuesday",
    explanation="The days of the week in order: Monday, Tuesday, Wednesday...",
    hint="Days of the week."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I write with a ___.",
    options=["book", "pen", "chair", "door"],
    correct_answer="pen",
    explanation="A pen is a tool used for writing.",
    hint="What tool do you use to write?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="What color is the sky on a clear day?",
    options=["green", "red", "blue", "yellow"],
    correct_answer="blue",
    explanation="The sky appears blue on clear, sunny days.",
    hint="Look up on a sunny day!"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="My mother's mother is my ___.",
    options=["aunt", "sister", "grandmother", "cousin"],
    correct_answer="grandmother",
    explanation="Your grandmother is your parent's mother.",
    hint="Family relationships."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I'm very ___. I need to drink water.",
    options=["hungry", "tired", "thirsty", "happy"],
    correct_answer="thirsty",
    explanation="Thirsty means you need to drink something.",
    hint="What feeling makes you want to drink?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="Spring, summer, autumn, and ___ are the four seasons.",
    options=["winter", "rain", "snow", "cold"],
    correct_answer="winter",
    explanation="Winter is the fourth season, typically the coldest.",
    hint="The coldest season."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I use my ___ to call people.",
    options=["phone", "book", "shoe", "cup"],
    correct_answer="phone",
    explanation="A phone is a device used to make calls.",
    hint="Communication device."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="When you meet someone, you say '___'.",
    options=["Goodbye", "Hello", "Goodnight", "Sorry"],
    correct_answer="Hello",
    explanation="'Hello' is a greeting used when you meet someone.",
    hint="A greeting word."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="I ___ a cat and a dog.",
    options=["has", "have", "having", "had"],
    correct_answer="have",
    explanation="With 'I', we use 'have' in present simple.",
    hint="Present simple with 'I'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="The book is ___ the table.",
    options=["in", "on", "at", "of"],
    correct_answer="on",
    explanation="We use 'on' for things on flat surfaces.",
    hint="Preposition for surfaces."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="I live ___ New York.",
    options=["on", "at", "in", "to"],
    correct_answer="in",
    explanation="We use 'in' for cities and countries.",
    hint="Preposition for cities."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I ___ my teeth every morning.",
    options=["wash", "brush", "clean", "comb"],
    correct_answer="brush",
    explanation="'Brush teeth' is the correct collocation.",
    hint="What do you do with your teeth?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I wear ___ on my feet.",
    options=["gloves", "hat", "shoes", "shirt"],
    correct_answer="shoes",
    explanation="Shoes are worn on feet.",
    hint="Clothing for feet."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-016",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="She ___ a teacher.",
    options=["am", "is", "are", "be"],
    correct_answer="is",
    explanation="With 'she', we use 'is'.",
    hint="Third person singular of 'be'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="There are twelve ___ in a year.",
    options=["weeks", "days", "months", "hours"],
    correct_answer="months",
    explanation="A year has twelve months (January to December).",
    hint="January, February, March..."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-017",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="It ___ very hot today.",
    options=["am", "is", "are", "be"],
    correct_answer="is",
    explanation="With 'it', we use 'is'.",
    hint="The verb 'be' with 'it'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I sleep in my ___.",
    options=["kitchen", "bathroom", "bedroom", "garage"],
    correct_answer="bedroom",
    explanation="A bedroom is the room where you sleep.",
    hint="Room for sleeping."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a1-018",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="They ___ students.",
    options=["am", "is", "are", "be"],
    correct_answer="are",
    explanation="With 'they', we use 'are'.",
    hint="Plural form of 'be'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a1-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A1",
    skill=SkillType.VOCABULARY,
    question="I use a ___ to cut paper.",
    options=["knife", "scissors", "spoon", "fork"],
    correct_answer="scissors",
    explanation="Scissors are used to cut paper.",
    hint="Tool for cutting paper."
))

# A2 Level
_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="She was very ___ when she heard the good news.",
    options=["angry", "sad", "excited", "tired"],
    correct_answer="excited",
    explanation="'Excited' describes a positive emotional response to good news.",
    hint="What feeling do you have with good news?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="I need to ___ a taxi to get to the airport.",
    options=["catch", "take", "get", "have"],
    correct_answer="catch",
    explanation="'Catch a taxi' is a common collocation meaning to get/take a taxi.",
    hint="Common phrase with taxi."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="The ___ of the movie was very interesting.",
    options=["plot", "plate", "plant", "plane"],
    correct_answer="plot",
    explanation="The plot is the story or sequence of events in a movie or book.",
    hint="The story of a movie."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="Can you ___ me the salt, please?",
    options=["give", "pass", "take", "bring"],
    correct_answer="pass",
    explanation="'Pass' is used when asking someone to hand you something nearby.",
    hint="At the dinner table..."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="He's very ___. He always helps others.",
    options=["selfish", "lazy", "generous", "mean"],
    correct_answer="generous",
    explanation="Generous means willing to give and help others.",
    hint="A positive trait about helping others."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="I have a ___ - my head really hurts.",
    options=["stomachache", "headache", "toothache", "backache"],
    correct_answer="headache",
    explanation="A headache is pain in the head.",
    hint="Pain in your head."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="The opposite of 'cheap' is ___.",
    options=["free", "expensive", "poor", "rich"],
    correct_answer="expensive",
    explanation="Expensive means costing a lot of money, opposite of cheap.",
    hint="Costs a lot of money."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="I need to ___ my car at the gas station.",
    options=["fill up", "fill in", "fill out", "fill down"],
    correct_answer="fill up",
    explanation="'Fill up' means to add fuel to a car.",
    hint="Phrasal verb for adding gas."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="I ___ coffee. I prefer tea.",
    options=["don't like", "doesn't like", "am not liking", "not like"],
    correct_answer="don't like",
    explanation="Present simple negative with 'I' uses 'don't + base verb'.",
    hint="Present simple negative."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="How ___ books do you have?",
    options=["much", "many", "often", "long"],
    correct_answer="many",
    explanation="'Many' is used with countable nouns (books).",
    hint="Countable vs uncountable."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="Please ___ off your phone in the cinema.",
    options=["turn", "make", "take", "put"],
    correct_answer="turn",
    explanation="'Turn off' means to stop a device from operating.",
    hint="Phrasal verb for stopping a device."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="He ___ to school yesterday.",
    options=["go", "goes", "went", "going"],
    correct_answer="went",
    explanation="'Yesterday' indicates past simple. 'Went' is the past of 'go'.",
    hint="Past tense of 'go'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="I need to ___ a decision soon.",
    options=["do", "make", "take", "have"],
    correct_answer="make",
    explanation="'Make a decision' is the correct collocation.",
    hint="Common collocation with 'decision'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="She ___ at the moment.",
    options=["is studying", "studies", "studied", "study"],
    correct_answer="is studying",
    explanation="'At the moment' indicates present continuous (is/are + -ing).",
    hint="Present continuous for now."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="I have to ___ my homework before dinner.",
    options=["make", "do", "write", "work"],
    correct_answer="do",
    explanation="'Do homework' is the correct collocation.",
    hint="Common verb with 'homework'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="I have lived here ___ 2015.",
    options=["for", "since", "from", "at"],
    correct_answer="since",
    explanation="'Since' is used with a point in time (2015).",
    hint="Point in time vs duration."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="Can you ___ up the volume? I can't hear.",
    options=["turn", "put", "make", "set"],
    correct_answer="turn",
    explanation="'Turn up' means to increase volume.",
    hint="Phrasal verb for increasing volume."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-016",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="This exercise is ___ difficult than the last one.",
    options=["more", "much", "most", "many"],
    correct_answer="more",
    explanation="'More' is used for comparative with longer adjectives.",
    hint="Comparative form."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="I ___ into an old friend at the mall yesterday.",
    options=["ran", "walked", "met", "saw"],
    correct_answer="ran",
    explanation="'Run into' means to meet someone by chance.",
    hint="Phrasal verb for meeting by chance."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-017",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="Would you like ___ tea?",
    options=["some", "any", "a", "an"],
    correct_answer="some",
    explanation="In offers and requests, we use 'some' instead of 'any'.",
    hint="Offers use 'some'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="I need to ___ a shower before work.",
    options=["make", "do", "take", "have"],
    correct_answer="take",
    explanation="'Take a shower' is the common collocation (though 'have a shower' is also correct).",
    hint="Common verb with 'shower'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-a2-018",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="I ___ to London last year.",
    options=["go", "went", "have been", "have gone"],
    correct_answer="went",
    explanation="'Last year' is a finished time, so we use past simple.",
    hint="Finished time = past simple."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-a2-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="The plane will ___ off in ten minutes.",
    options=["take", "get", "go", "fly"],
    correct_answer="take",
    explanation="'Take off' means when a plane leaves the ground.",
    hint="Phrasal verb for planes departing."
))

# B1 Level
_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="The company decided to ___ 50 new employees.",
    options=["fire", "hire", "retire", "resign"],
    correct_answer="hire",
    explanation="'Hire' means to employ someone. 'Fire' means to dismiss. 'Retire' and 'resign' are about leaving a job.",
    hint="What verb means 'to give someone a job'?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="I couldn't ___ the temptation to eat another piece of cake.",
    options=["resist", "insist", "persist", "consist"],
    correct_answer="resist",
    explanation="'Resist' means to stop yourself from doing something. 'Resist temptation' is a common collocation.",
    hint="What verb means 'to fight against' an urge?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="The house ___ by my grandfather in 1950.",
    options=["built", "was built", "has built", "is building"],
    correct_answer="was built",
    explanation="Passive voice in past simple: was/were + past participle.",
    hint="Passive voice in the past."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="We need to ___ up with a solution quickly.",
    options=["come", "get", "make", "take"],
    correct_answer="come",
    explanation="'Come up with' means to think of or produce an idea or solution.",
    hint="Phrasal verb meaning 'to think of'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="He told me ___ so much noise.",
    options=["don't make", "not to make", "to not make", "not making"],
    correct_answer="not to make",
    explanation="Reported commands use: tell someone (not) to + infinitive.",
    hint="Structure after 'tell someone'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="The meeting has been ___ off until next week.",
    options=["put", "taken", "called", "set"],
    correct_answer="put",
    explanation="'Put off' means to postpone or delay something.",
    hint="Phrasal verb meaning 'postpone'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="I'm looking forward ___ you soon.",
    options=["to see", "to seeing", "seeing", "see"],
    correct_answer="to seeing",
    explanation="'Look forward to' is followed by a gerund (-ing), not an infinitive.",
    hint="'To' here is a preposition."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="I can't ___ out what he's saying.",
    options=["make", "take", "find", "get"],
    correct_answer="make",
    explanation="'Make out' means to understand or discern something with difficulty.",
    hint="Phrasal verb meaning 'understand'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="We ___ go to the beach if the weather is nice.",
    options=["will", "would", "will be", "going to"],
    correct_answer="will",
    explanation="First conditional uses 'will' in the main clause for future possibility.",
    hint="First conditional structure."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="Can you ___ after my cat while I'm on vacation?",
    options=["see", "look", "watch", "take"],
    correct_answer="look",
    explanation="'Look after' means to take care of someone or something.",
    hint="Phrasal verb meaning 'take care of'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="She suggested ___ to the new restaurant.",
    options=["to go", "going", "go", "gone"],
    correct_answer="going",
    explanation="'Suggest' is followed by a gerund (-ing), not an infinitive.",
    hint="Structure after 'suggest'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="I need to ___ over my notes before the exam.",
    options=["go", "look", "read", "study"],
    correct_answer="go",
    explanation="'Go over' means to review or examine something carefully.",
    hint="Phrasal verb meaning 'review'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="He's worked here ___ ten years.",
    options=["since", "for", "during", "from"],
    correct_answer="for",
    explanation="'For' is used with a period of time (ten years).",
    hint="Duration of time."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="The company had to ___ off 50 employees.",
    options=["lay", "put", "take", "set"],
    correct_answer="lay",
    explanation="'Lay off' means to dismiss employees, typically due to economic reasons.",
    hint="Phrasal verb meaning 'dismiss from work'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="Unless you ___ harder, you won't pass the exam.",
    options=["study", "will study", "studied", "would study"],
    correct_answer="study",
    explanation="After 'unless' (like 'if'), we use present simple, not 'will'.",
    hint="No 'will' after 'unless'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="She ___ down my invitation to the party.",
    options=["turned", "put", "took", "gave"],
    correct_answer="turned",
    explanation="'Turn down' means to reject or refuse an offer or invitation.",
    hint="Phrasal verb meaning 'reject'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-016",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="I'm not used ___ up so early.",
    options=["to get", "to getting", "getting", "get"],
    correct_answer="to getting",
    explanation="'Be used to' is followed by a gerund (-ing). Note: different from 'used to + infinitive'.",
    hint="'Be used to' + gerund."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="The project ___ off well with great team collaboration.",
    options=["got", "took", "went", "came"],
    correct_answer="got",
    explanation="'Get off to a good/bad start' means to begin in a particular way.",
    hint="Phrasal verb meaning 'to start'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-017",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="The book, ___ I bought yesterday, is very interesting.",
    options=["that", "which", "what", "who"],
    correct_answer="which",
    explanation="In non-defining relative clauses (with commas), we use 'which' for things.",
    hint="Non-defining relative clause."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b1-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="I need to ___ up on my Spanish before the trip.",
    options=["brush", "clean", "wash", "polish"],
    correct_answer="brush",
    explanation="'Brush up on' means to improve or refresh your knowledge of something.",
    hint="Idiom meaning 'improve your knowledge'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b1-018",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="I'd prefer ___ a movie rather than go out.",
    options=["watch", "watching", "to watch", "watched"],
    correct_answer="to watch",
    explanation="'Prefer to do' (infinitive) or 'prefer doing' (gerund) are both correct, but 'prefer to do' is more common.",
    hint="'Prefer to' + infinitive."
))

# B2 Level
_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="The new policy will ___ significant changes to the organization.",
    options=["bring about", "bring up", "bring out", "bring down"],
    correct_answer="bring about",
    explanation="'Bring about' means to cause something to happen.",
    hint="Which phrasal verb means 'to cause'?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="Despite the ___ weather, we decided to go hiking.",
    options=["inclement", "clement", "magnificent", "ordinary"],
    correct_answer="inclement",
    explanation="'Inclement' means unpleasantly cold or wet, typically used to describe bad weather.",
    hint="A formal word for 'bad' weather."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Scarcely ___ arrived when the fire alarm went off.",
    options=["we had", "had we", "we have", "have we"],
    correct_answer="had we",
    explanation="'Scarcely' at the start requires inversion: auxiliary + subject.",
    hint="Inversion with negative adverb."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="The company needs to ___ out the competition to survive.",
    options=["see", "look", "watch", "find"],
    correct_answer="see",
    explanation="'See out' means to outlast or survive longer than someone.",
    hint="Phrasal verb meaning 'outlast'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="He acts as if he ___ the boss.",
    options=["is", "was", "were", "be"],
    correct_answer="were",
    explanation="After 'as if/as though', we use 'were' for all persons when expressing unreality.",
    hint="Subjunctive after 'as if'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="The new evidence ___ into question the validity of the research.",
    options=["calls", "puts", "takes", "brings"],
    correct_answer="calls",
    explanation="'Call into question' means to raise doubts about something.",
    hint="Phrase meaning 'to doubt'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="I'd rather you ___ tell anyone about this.",
    options=["don't", "didn't", "not", "wouldn't"],
    correct_answer="didn't",
    explanation="'Would rather + subject + past tense' for preferences about others' actions.",
    hint="'Would rather' + subject + past."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="Her explanation didn't ___ up to scrutiny.",
    options=["stand", "hold", "keep", "stay"],
    correct_answer="stand",
    explanation="'Stand up to scrutiny' means to remain valid when examined closely.",
    hint="Idiom meaning 'withstand examination'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="We ___ about the problem for hours when the solution suddenly came to us.",
    options=["have been thinking", "had been thinking", "are thinking", "were thinking"],
    correct_answer="had been thinking",
    explanation="Past perfect continuous shows an action that had been in progress before another past action.",
    hint="Action in progress before past moment."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="The manager decided to ___ a blind eye to the minor infractions.",
    options=["turn", "close", "shut", "make"],
    correct_answer="turn",
    explanation="'Turn a blind eye' means to deliberately ignore something wrong.",
    hint="Idiom meaning 'to ignore'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="No matter ___ hard I try, I can't solve this problem.",
    options=["how", "what", "which", "that"],
    correct_answer="how",
    explanation="'No matter how + adjective/adverb' expresses that something makes no difference.",
    hint="'No matter' + question word."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="The deadline is fast ___, and we're not ready.",
    options=["approaching", "coming", "nearing", "advancing"],
    correct_answer="approaching",
    explanation="'Fast approaching' is a strong collocation meaning getting very close in time.",
    hint="Collocation with 'fast' and 'deadline'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="The building is reported ___ in the fire.",
    options=["to damage", "to be damaged", "to have damaged", "to have been damaged"],
    correct_answer="to have been damaged",
    explanation="Passive perfect infinitive: 'to have been + past participle' for completed past actions.",
    hint="Passive + perfect infinitive."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="She has a ___ for languages and speaks five fluently.",
    options=["talent", "gift", "flair", "ability"],
    correct_answer="flair",
    explanation="'A flair for' is a strong collocation meaning natural ability or talent.",
    hint="Common collocation meaning 'natural talent'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Provided that you ___ the instructions, everything will be fine.",
    options=["follow", "will follow", "would follow", "followed"],
    correct_answer="follow",
    explanation="'Provided that' (like 'if') takes present tense for future conditions.",
    hint="Conditional conjunction."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="His new business venture is really taking ___.",
    options=["off", "up", "on", "over"],
    correct_answer="off",
    explanation="'Take off' means to suddenly become successful or popular.",
    hint="Phrasal verb meaning 'become successful'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-b2-016",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Such ___ the force of the explosion that windows shattered for miles.",
    options=["is", "was", "were", "be"],
    correct_answer="was",
    explanation="Inverted structure: 'Such + be + noun' for emphasis.",
    hint="Inversion with 'such'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-b2-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="The proposal was met with ___ criticism from the board.",
    options=["strong", "heavy", "hard", "fierce"],
    correct_answer="fierce",
    explanation="'Fierce criticism' is a strong collocation meaning intense or harsh criticism.",
    hint="Strong collocation with 'criticism'."
))

# C1 Level
_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-001",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The professor's ___ explanation made the complex topic easy to understand.",
    options=["lucid", "obscure", "cryptic", "vague"],
    correct_answer="lucid",
    explanation="'Lucid' means clear and easy to understand, especially of writing or speech.",
    hint="Which word means 'clear and understandable'?"
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-002",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="Her ___ comments during the meeting offended several colleagues.",
    options=["tactful", "caustic", "diplomatic", "measured"],
    correct_answer="caustic",
    explanation="'Caustic' means severely critical or sarcastic in a hurtful way.",
    hint="Which word describes harsh, biting criticism?"
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Rarely ___ such an impressive performance.",
    options=["I have seen", "have I seen", "I saw", "did I see"],
    correct_answer="have I seen",
    explanation="Negative adverbs at the start require inversion with present perfect.",
    hint="Inversion with 'rarely'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-003",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The politician's ___ speech failed to convince the skeptical audience.",
    options=["eloquent", "verbose", "concise", "articulate"],
    correct_answer="verbose",
    explanation="'Verbose' means using more words than needed, often ineffectively.",
    hint="Word meaning 'wordy but not effective'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Not until the last minute ___ that the event was cancelled.",
    options=["we found out", "did we find out", "we did find out", "found we out"],
    correct_answer="did we find out",
    explanation="'Not until' at the start requires inversion in the main clause.",
    hint="Inversion after 'Not until'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-004",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The company's financial problems are ___ of poor management.",
    options=["symptomatic", "symbolic", "systematic", "synthetic"],
    correct_answer="symptomatic",
    explanation="'Symptomatic of' means being a sign or indication of something.",
    hint="Meaning 'a sign of something'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="What annoys me is ___ she never apologizes.",
    options=["that", "what", "which", "how"],
    correct_answer="that",
    explanation="'What' introduces a nominal clause, followed by 'that' introducing the complement clause.",
    hint="Complement clause after 'is'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-005",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The evidence was considered ___ and therefore inadmissible in court.",
    options=["dubious", "spurious", "ambiguous", "questionable"],
    correct_answer="spurious",
    explanation="'Spurious' means false or fake, especially evidence or reasoning.",
    hint="Meaning 'false or fake'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-011",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="The committee is said ___ the proposal next week.",
    options=["to consider", "to be considering", "considering", "consider"],
    correct_answer="to be considering",
    explanation="Passive reporting with continuous infinitive for ongoing future action.",
    hint="Continuous infinitive in passive report."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-006",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="His ___ attitude toward work has hindered his career advancement.",
    options=["lackadaisical", "meticulous", "diligent", "conscientious"],
    correct_answer="lackadaisical",
    explanation="'Lackadaisical' means lacking enthusiasm and determination; carelessly lazy.",
    hint="Word meaning 'carelessly lazy'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-012",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="So badly ___ in the accident that he spent months in hospital.",
    options=["he was injured", "was he injured", "he injured", "injured he"],
    correct_answer="was he injured",
    explanation="'So + adverb' at the start requires inversion.",
    hint="Inversion after 'So badly'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-007",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The report contains several ___ errors that undermine its credibility.",
    options=["flagrant", "blatant", "egregious", "obvious"],
    correct_answer="egregious",
    explanation="'Egregious' means outstandingly bad or shocking, often used for errors.",
    hint="Formal word for 'shockingly bad'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-013",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Only by working together ___ solve this crisis.",
    options=["we can", "can we", "we could", "could we"],
    correct_answer="can we",
    explanation="'Only by' at the start requires inversion.",
    hint="Inversion after 'Only by'."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-008",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The manager's ___ behavior created a hostile work environment.",
    options=["abrasive", "smooth", "polished", "refined"],
    correct_answer="abrasive",
    explanation="'Abrasive' describes someone who is harsh or unpleasant in manner.",
    hint="Word describing harsh, unpleasant manner."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-014",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="But for your intervention, the situation ___ much worse.",
    options=["would be", "would have been", "will be", "had been"],
    correct_answer="would have been",
    explanation="'But for' (= if it weren't for) with past reference takes third conditional.",
    hint="'But for' = third conditional."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-009",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The new regulations are designed to ___ fraud and corruption.",
    options=["curb", "curve", "kerb", "disturb"],
    correct_answer="curb",
    explanation="'Curb' means to restrain or keep in check.",
    hint="Word meaning 'to restrain or control'."
))

_add_exercise(Exercise(
    exercise_id="mc-gram-c1-015",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Were it ___ for the delay, we would be finished by now.",
    options=["not", "no", "none", "never"],
    correct_answer="not",
    explanation="Inverted conditional: 'Were it not for' = 'If it weren't for'.",
    hint="Formal inverted conditional."
))

_add_exercise(Exercise(
    exercise_id="mc-vocab-c1-010",
    exercise_type=ExerciseType.MULTIPLE_CHOICE,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The author's ___ use of metaphor enhances the narrative.",
    options=["judicious", "judicial", "prejudicial", "judgemental"],
    correct_answer="judicious",
    explanation="'Judicious' means having or showing good judgment.",
    hint="Word meaning 'showing good judgment'."
))

# ============================================================================
# FILL IN THE BLANK
# ============================================================================

_add_exercise(Exercise(
    exercise_id="fib-gram-a2-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="She ___ (go) to the gym every Monday.",
    correct_answer="goes",
    explanation="Third person singular (she) in present simple adds -s: goes.",
    hint="Present simple, third person singular."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-b1-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="If I ___ (know) the answer, I would tell you.",
    correct_answer="knew",
    explanation="Second conditional uses past simple in the if-clause.",
    hint="Second conditional structure."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-b1-002",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="By 5 PM tomorrow, I ___ (finish) all my work.",
    correct_answer="will have finished",
    explanation="Future perfect tense: will have + past participle.",
    hint="What tense for completion before a future time?"
))

_add_exercise(Exercise(
    exercise_id="fib-vocab-b1-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="The movie was so ___ that I fell asleep. (boring/bored)",
    correct_answer="boring",
    explanation="'Boring' describes things. 'Bored' describes feelings. The movie causes boredom, so it's boring.",
    hint="-ing for things, -ed for feelings."
))

_add_exercise(Exercise(
    exercise_id="fib-vocab-b2-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="She made a strong ___ for increasing the budget. (argument supporting something)",
    correct_answer="case",
    explanation="'Make a case for' means to present arguments supporting something.",
    hint="A word meaning 'argument' or 'reasoning'."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-a1-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="My name ___ John.",
    correct_answer="is",
    explanation="With 'my name' (third person singular), we use 'is'.",
    hint="Verb 'to be' with singular subject."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-a1-002",
    exercise_type=ExerciseType.FILL_BLANK,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="They ___ students.",
    correct_answer="are",
    explanation="With 'they' (plural), we use 'are'.",
    hint="Verb 'to be' with plural subject."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-a2-002",
    exercise_type=ExerciseType.FILL_BLANK,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="I ___ (live) in this city for five years.",
    correct_answer="have lived",
    explanation="Present perfect: have/has + past participle for experiences up to now.",
    hint="Present perfect tense."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-a2-003",
    exercise_type=ExerciseType.FILL_BLANK,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="She is ___ (tall) than her sister.",
    correct_answer="taller",
    explanation="Comparative form: add -er for short adjectives.",
    hint="Comparative form of 'tall'."
))

_add_exercise(Exercise(
    exercise_id="fib-vocab-a2-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="A2",
    skill=SkillType.VOCABULARY,
    question="Can you ___ the salt, please? (hand me something)",
    correct_answer="pass",
    explanation="'Pass' is used for handing something to someone nearby.",
    hint="Verb for giving something to someone."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-b1-003",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="The letter ___ (write) yesterday.",
    correct_answer="was written",
    explanation="Passive voice past simple: was/were + past participle.",
    hint="Passive voice in past."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-b1-004",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="I'm used to ___ (work) late hours.",
    correct_answer="working",
    explanation="'Be used to' is followed by a gerund (-ing form).",
    hint="Gerund after 'be used to'."
))

_add_exercise(Exercise(
    exercise_id="fib-vocab-b1-002",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B1",
    skill=SkillType.VOCABULARY,
    question="We need to ___ up with a better plan. (think of)",
    correct_answer="come",
    explanation="'Come up with' means to think of or produce an idea.",
    hint="Phrasal verb meaning 'think of'."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-b2-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="If I ___ (know) about the problem earlier, I would have helped.",
    correct_answer="had known",
    explanation="Third conditional: if + past perfect in the condition clause.",
    hint="Past perfect in third conditional."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-b2-002",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="By this time next year, I ___ (graduate) from university.",
    correct_answer="will have graduated",
    explanation="Future perfect: will have + past participle for completion before future time.",
    hint="Future perfect tense."
))

_add_exercise(Exercise(
    exercise_id="fib-vocab-b2-002",
    exercise_type=ExerciseType.FILL_BLANK,
    level="B2",
    skill=SkillType.VOCABULARY,
    question="The new policy will ___ about significant changes. (cause)",
    correct_answer="bring",
    explanation="'Bring about' means to cause something to happen.",
    hint="Phrasal verb meaning 'cause'."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-c1-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Little ___ (he/know) that his life was about to change.",
    correct_answer="did he know",
    explanation="Negative adverb 'little' at the start requires inversion.",
    hint="Inversion with 'little'."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-c1-002",
    exercise_type=ExerciseType.FILL_BLANK,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Not only ___ (she/pass) the exam, but she got the highest score.",
    correct_answer="did she pass",
    explanation="'Not only' requires inversion: auxiliary + subject + verb.",
    hint="Inversion after 'not only'."
))

_add_exercise(Exercise(
    exercise_id="fib-vocab-c1-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="C1",
    skill=SkillType.VOCABULARY,
    question="The new regulations aim to ___ corruption. (restrain)",
    correct_answer="curb",
    explanation="'Curb' means to restrain or keep in check.",
    hint="Formal verb meaning 'restrain'."
))

_add_exercise(Exercise(
    exercise_id="fib-gram-c2-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="___ (be) that as it may, we must proceed.",
    correct_answer="Be",
    explanation="'Be that as it may' is a fixed formal expression.",
    hint="Fixed expression starting with 'be'."
))

_add_exercise(Exercise(
    exercise_id="fib-vocab-c2-001",
    exercise_type=ExerciseType.FILL_BLANK,
    level="C2",
    skill=SkillType.VOCABULARY,
    question="Her ___ refusal to cooperate hindered the investigation. (stubborn)",
    correct_answer="obdurate",
    explanation="'Obdurate' means stubbornly refusing to change.",
    hint="Formal word meaning 'stubbornly inflexible'."
))

# ============================================================================
# SENTENCE CORRECTION
# ============================================================================

_add_exercise(Exercise(
    exercise_id="sc-gram-a2-001",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'Me and him went to the store.'",
    correct_answer="He and I went to the store.",
    explanation="Subject pronouns (I, he) are used as subjects. Also, it's polite to put others first.",
    hint="What pronouns should be used as subjects?"
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b1-001",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'I have went to Paris twice.'",
    correct_answer="I have gone to Paris twice.",
    explanation="Present perfect uses have + past participle. The past participle of 'go' is 'gone', not 'went'.",
    hint="What's the past participle of 'go'?"
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b1-002",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'Between you and I, this is a secret.'",
    correct_answer="Between you and me, this is a secret.",
    explanation="'Between' is a preposition and requires object pronouns. 'Me' is correct, not 'I'.",
    hint="What pronoun follows a preposition?"
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b2-001",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'The team are playing good today.'",
    correct_answer="The team is playing well today.",
    explanation="In American English, collective nouns take singular verbs. Also, 'well' (adverb) modifies the verb, not 'good' (adjective).",
    hint="Collective nouns + adverb vs adjective."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b2-002",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'If I would have known, I would have called.'",
    correct_answer="If I had known, I would have called.",
    explanation="Third conditional: If + past perfect, would have + past participle. Never 'would have' in the if-clause.",
    hint="What's the correct third conditional structure?"
))

_add_exercise(Exercise(
    exercise_id="sc-gram-a1-001",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'She go to school every day.'",
    correct_answer="She goes to school every day.",
    explanation="Third person singular (she/he/it) requires -s or -es in present simple.",
    hint="Third person singular needs -s."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-a1-002",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="A1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'I am have a car.'",
    correct_answer="I have a car.",
    explanation="We don't use 'am' with 'have' in present simple. Just 'I have'.",
    hint="No 'am' needed with 'have'."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-a2-002",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'I am knowing the answer.'",
    correct_answer="I know the answer.",
    explanation="Stative verbs like 'know' are not normally used in continuous tenses.",
    hint="'Know' is a stative verb."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-a2-003",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="A2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'She is more tall than me.'",
    correct_answer="She is taller than me.",
    explanation="For short adjectives (one syllable), use -er, not 'more'.",
    hint="Short adjectives add -er."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b1-003",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'I am living here since 2010.'",
    correct_answer="I have lived here since 2010. / I have been living here since 2010.",
    explanation="With 'since', use present perfect (simple or continuous), not present simple/continuous.",
    hint="Use present perfect with 'since'."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b1-004",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'He suggested me to go home.'",
    correct_answer="He suggested that I go home. / He suggested going home.",
    explanation="'Suggest' is followed by a that-clause or gerund, not 'someone to do'.",
    hint="'Suggest' + that or gerund."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b2-003",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'Despite of the rain, we went out.'",
    correct_answer="Despite the rain, we went out.",
    explanation="'Despite' is not followed by 'of'. Use 'despite' or 'in spite of'.",
    hint="'Despite' vs 'in spite of'."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-b2-004",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="B2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'I wish I was taller.'",
    correct_answer="I wish I were taller.",
    explanation="After 'wish', formal English uses 'were' for all persons (subjunctive).",
    hint="Subjunctive after 'wish'."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-c1-001",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'Rarely I have seen such dedication.'",
    correct_answer="Rarely have I seen such dedication.",
    explanation="Negative adverbs at the start require inversion: auxiliary + subject.",
    hint="Inversion with negative adverbs."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-c1-002",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="C1",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'I object of the new policy.'",
    correct_answer="I object to the new policy.",
    explanation="'Object' is followed by the preposition 'to', not 'of'.",
    hint="Correct preposition with 'object'."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-c2-001",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'Far is it from me to criticize.'",
    correct_answer="Far be it from me to criticize.",
    explanation="'Far be it from me' is a fixed expression using subjunctive 'be'.",
    hint="Fixed expression with subjunctive."
))

_add_exercise(Exercise(
    exercise_id="sc-gram-c2-002",
    exercise_type=ExerciseType.SENTENCE_CORRECTION,
    level="C2",
    skill=SkillType.GRAMMAR,
    question="Correct the error: 'Lest he will forget, send him a reminder.'",
    correct_answer="Lest he forget, send him a reminder.",
    explanation="'Lest' is followed by subjunctive (base form) or 'should', not 'will'.",
    hint="Subjunctive after 'lest'."
))


class ExerciseManager:
    """Manages exercise selection and evaluation."""

    def get_practice_session(
        self,
        count: int = 5,
        level: Optional[str] = None,
        skill: Optional[SkillType] = None,
        exercise_type: Optional[ExerciseType] = None,
    ) -> List[Exercise]:
        """
        Get a practice session with mixed exercises.

        Args:
            count: Number of exercises to return
            level: Filter by level (A1, A2, B1, B2, C1, C2)
            skill: Filter by skill type
            exercise_type: Filter by exercise type

        Returns:
            List of exercises for the session
        """
        # Filter exercises
        filtered = list(EXERCISES.values())

        if level:
            # Strictly filter to user's level only
            # No adjacent levels - users should master their level first
            filtered = [e for e in filtered if e.level == level.upper()]

        if skill:
            filtered = [e for e in filtered if e.skill == skill]

        if exercise_type:
            filtered = [e for e in filtered if e.exercise_type == exercise_type]

        # Ensure variety of types
        if not exercise_type and len(filtered) >= count:
            # Try to get a mix of types
            by_type: Dict[ExerciseType, List[Exercise]] = {}
            for ex in filtered:
                if ex.exercise_type not in by_type:
                    by_type[ex.exercise_type] = []
                by_type[ex.exercise_type].append(ex)

            selected = []
            types = list(by_type.keys())
            random.shuffle(types)
            type_idx = 0

            while len(selected) < count and any(by_type.values()):
                current_type = types[type_idx % len(types)]
                if by_type[current_type]:
                    ex = random.choice(by_type[current_type])
                    by_type[current_type].remove(ex)
                    selected.append(ex)
                type_idx += 1

            random.shuffle(selected)
            return selected

        # Random selection
        random.shuffle(filtered)
        return filtered[:count]

    def check_answer(
        self,
        exercise_id: str,
        user_answer: str,
    ) -> Dict:
        """
        Check if user's answer is correct.

        Args:
            exercise_id: ID of the exercise
            user_answer: User's submitted answer

        Returns:
            Dict with is_correct, correct_answer, and explanation
        """
        if exercise_id not in EXERCISES:
            raise ValueError(f"Exercise {exercise_id} not found")

        exercise = EXERCISES[exercise_id]

        # Normalize answers for comparison
        user_normalized = user_answer.strip().lower()
        correct_normalized = exercise.correct_answer.strip().lower()

        # For multiple choice, also check by option text
        is_correct = user_normalized == correct_normalized

        if not is_correct and exercise.options:
            # Check if user provided option index
            try:
                idx = int(user_answer)
                if 0 <= idx < len(exercise.options):
                    is_correct = exercise.options[idx].lower() == correct_normalized
            except ValueError:
                pass

        return {
            "is_correct": is_correct,
            "correct_answer": exercise.correct_answer,
            "explanation": exercise.explanation,
            "user_answer": user_answer,
        }

    def get_exercise(self, exercise_id: str) -> Optional[Exercise]:
        """Get a specific exercise by ID."""
        return EXERCISES.get(exercise_id)

    def get_all_exercises(self) -> List[Exercise]:
        """Get all exercises."""
        return list(EXERCISES.values())


# Singleton instance
exercise_manager = ExerciseManager()
