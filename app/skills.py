"""
Skill Definitions for Vorex Mastery Engine
~120 micro-skills covering A1-B1 levels
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SkillDefinition:
    skill_key: str
    domain: str
    category: str
    name_en: str
    description_en: str
    cefr_level: str
    difficulty: float = 0.5

# Grammar Skills (~60)
GRAMMAR_SKILLS: List[SkillDefinition] = [
    # Present Simple (6)
    SkillDefinition("grammar_present_simple_affirmative", "grammar", "present_simple", "Present Simple - Affirmative", "Form positive statements: I work, She works", "A1", 0.3),
    SkillDefinition("grammar_present_simple_negative", "grammar", "present_simple", "Present Simple - Negative", "Form negative statements: I don't work, She doesn't work", "A1", 0.35),
    SkillDefinition("grammar_present_simple_question", "grammar", "present_simple", "Present Simple - Questions", "Form questions: Do you work? Does she work?", "A1", 0.4),
    SkillDefinition("grammar_present_simple_third_person", "grammar", "present_simple", "Present Simple - Third Person -s", "Add -s/-es for he/she/it: works, goes, watches", "A1", 0.35),
    SkillDefinition("grammar_present_simple_time_expressions", "grammar", "present_simple", "Present Simple - Time Expressions", "Use with: always, usually, sometimes, never", "A2", 0.4),
    SkillDefinition("grammar_present_simple_frequency", "grammar", "present_simple", "Present Simple - Frequency Adverbs", "Position of frequency adverbs in sentences", "A2", 0.45),

    # Present Continuous (4)
    SkillDefinition("grammar_present_cont_affirmative", "grammar", "present_continuous", "Present Continuous - Affirmative", "I am working, She is working", "A1", 0.35),
    SkillDefinition("grammar_present_cont_negative", "grammar", "present_continuous", "Present Continuous - Negative", "I'm not working, She isn't working", "A1", 0.4),
    SkillDefinition("grammar_present_cont_question", "grammar", "present_continuous", "Present Continuous - Questions", "Are you working? Is she working?", "A2", 0.45),
    SkillDefinition("grammar_present_simple_vs_cont", "grammar", "present_continuous", "Present Simple vs Continuous", "Habits vs current actions", "A2", 0.55),

    # Past Simple (6)
    SkillDefinition("grammar_past_simple_regular", "grammar", "past_simple", "Past Simple - Regular Verbs", "Add -ed: worked, played, watched", "A1", 0.4),
    SkillDefinition("grammar_past_simple_irregular", "grammar", "past_simple", "Past Simple - Irregular Verbs", "went, had, saw, came, took", "A2", 0.5),
    SkillDefinition("grammar_past_simple_negative", "grammar", "past_simple", "Past Simple - Negative", "I didn't work, She didn't go", "A2", 0.45),
    SkillDefinition("grammar_past_simple_question", "grammar", "past_simple", "Past Simple - Questions", "Did you work? Where did she go?", "A2", 0.5),
    SkillDefinition("grammar_past_simple_time_expressions", "grammar", "past_simple", "Past Simple - Time Expressions", "yesterday, last week, two days ago", "A2", 0.45),
    SkillDefinition("grammar_past_simple_ago", "grammar", "past_simple", "Past Simple - Ago", "Using 'ago' with time expressions", "A2", 0.45),

    # Future (4)
    SkillDefinition("grammar_future_will", "grammar", "future", "Future - Will", "I will help, She will come", "A2", 0.5),
    SkillDefinition("grammar_future_going_to", "grammar", "future", "Future - Going To", "I'm going to study, She's going to travel", "A2", 0.5),
    SkillDefinition("grammar_future_present_cont", "grammar", "future", "Future - Present Continuous", "Using present continuous for planned future", "B1", 0.6),
    SkillDefinition("grammar_future_time_expressions", "grammar", "future", "Future - Time Expressions", "tomorrow, next week, in two days", "A2", 0.45),

    # Articles (4)
    SkillDefinition("grammar_article_a_an", "grammar", "articles", "Articles - A/An", "Using a/an with consonants/vowels", "A1", 0.3),
    SkillDefinition("grammar_article_the", "grammar", "articles", "Articles - The", "Using 'the' for specific things", "A2", 0.5),
    SkillDefinition("grammar_article_zero", "grammar", "articles", "Articles - Zero Article", "When not to use articles", "B1", 0.6),
    SkillDefinition("grammar_article_countable", "grammar", "articles", "Articles - Countable/Uncountable", "a chair, some water, much/many", "A2", 0.55),

    # Pronouns (6)
    SkillDefinition("grammar_pronoun_subject", "grammar", "pronouns", "Pronouns - Subject", "I, you, he, she, it, we, they", "A1", 0.25),
    SkillDefinition("grammar_pronoun_object", "grammar", "pronouns", "Pronouns - Object", "me, you, him, her, it, us, them", "A1", 0.35),
    SkillDefinition("grammar_pronoun_possessive_adj", "grammar", "pronouns", "Possessive Adjectives", "my, your, his, her, its, our, their", "A1", 0.35),
    SkillDefinition("grammar_pronoun_possessive_pron", "grammar", "pronouns", "Possessive Pronouns", "mine, yours, his, hers, ours, theirs", "A2", 0.5),
    SkillDefinition("grammar_pronoun_reflexive", "grammar", "pronouns", "Reflexive Pronouns", "myself, yourself, himself, herself", "A2", 0.55),
    SkillDefinition("grammar_pronoun_demonstrative", "grammar", "pronouns", "Demonstrative Pronouns", "this, that, these, those", "A1", 0.35),

    # Prepositions (6)
    SkillDefinition("grammar_prep_time", "grammar", "prepositions", "Prepositions - Time", "at 5pm, on Monday, in January", "A1", 0.4),
    SkillDefinition("grammar_prep_place", "grammar", "prepositions", "Prepositions - Place", "at home, in the room, on the table", "A1", 0.4),
    SkillDefinition("grammar_prep_movement", "grammar", "prepositions", "Prepositions - Movement", "to, from, into, out of, through", "A2", 0.5),
    SkillDefinition("grammar_prep_common", "grammar", "prepositions", "Common Preposition Phrases", "at work, in time, on time, by car", "A2", 0.5),
    SkillDefinition("grammar_prep_in_on_at", "grammar", "prepositions", "In/On/At Usage", "Distinguishing in, on, at", "A2", 0.55),
    SkillDefinition("grammar_prep_to_for", "grammar", "prepositions", "To/For Usage", "give to him, a gift for you", "A2", 0.5),

    # Modals (6)
    SkillDefinition("grammar_modal_can", "grammar", "modals", "Modal - Can/Could", "ability and possibility", "A1", 0.4),
    SkillDefinition("grammar_modal_must", "grammar", "modals", "Modal - Must/Have To", "obligation and necessity", "A2", 0.5),
    SkillDefinition("grammar_modal_should", "grammar", "modals", "Modal - Should", "advice and recommendations", "A2", 0.5),
    SkillDefinition("grammar_modal_may_might", "grammar", "modals", "Modal - May/Might", "possibility and permission", "B1", 0.6),
    SkillDefinition("grammar_modal_would", "grammar", "modals", "Modal - Would", "requests and conditionals", "B1", 0.6),
    SkillDefinition("grammar_modal_negatives", "grammar", "modals", "Modal Negatives", "can't, mustn't, shouldn't", "A2", 0.5),

    # Comparatives (4)
    SkillDefinition("grammar_comp_er_est", "grammar", "comparatives", "Comparatives - -er/-est", "bigger, biggest, faster, fastest", "A2", 0.5),
    SkillDefinition("grammar_comp_more_most", "grammar", "comparatives", "Comparatives - More/Most", "more beautiful, most interesting", "A2", 0.5),
    SkillDefinition("grammar_comp_irregular", "grammar", "comparatives", "Comparatives - Irregular", "better/best, worse/worst, farther/farthest", "A2", 0.55),
    SkillDefinition("grammar_comp_as_as", "grammar", "comparatives", "Comparatives - As...As", "as tall as, not as big as", "B1", 0.6),

    # Conjunctions (4)
    SkillDefinition("grammar_conj_and_but_or", "grammar", "conjunctions", "Conjunctions - And/But/Or", "basic coordination", "A1", 0.3),
    SkillDefinition("grammar_conj_because_so", "grammar", "conjunctions", "Conjunctions - Because/So", "cause and result", "A2", 0.45),
    SkillDefinition("grammar_conj_when_while", "grammar", "conjunctions", "Conjunctions - When/While", "time clauses", "A2", 0.5),
    SkillDefinition("grammar_conj_if", "grammar", "conjunctions", "Conjunctions - If", "first conditional basics", "B1", 0.6),

    # Word Order (4)
    SkillDefinition("grammar_word_order_statement", "grammar", "word_order", "Word Order - Statements", "Subject + Verb + Object", "A1", 0.35),
    SkillDefinition("grammar_word_order_question", "grammar", "word_order", "Word Order - Questions", "Question word + aux + subject + verb", "A2", 0.5),
    SkillDefinition("grammar_word_order_negative", "grammar", "word_order", "Word Order - Negatives", "subject + aux + not + verb", "A2", 0.45),
    SkillDefinition("grammar_word_order_adverb", "grammar", "word_order", "Word Order - Adverbs", "position of adverbs in sentences", "B1", 0.55),

    # Other Grammar (6)
    SkillDefinition("grammar_there_is_are", "grammar", "existence", "There Is/There Are", "existence statements", "A1", 0.35),
    SkillDefinition("grammar_there_was_were", "grammar", "existence", "There Was/There Were", "past existence", "A2", 0.45),
    SkillDefinition("grammar_possessive_s", "grammar", "possession", "Possessive 's", "John's book, my mother's car", "A1", 0.35),
    SkillDefinition("grammar_possessive_of", "grammar", "possession", "Possessive 'of'", "the color of the car", "A2", 0.45),
    SkillDefinition("grammar_imperative", "grammar", "imperatives", "Imperatives", "commands: Open the door, Don't touch", "A1", 0.35),
    SkillDefinition("grammar_imperative_lets", "grammar", "imperatives", "Let's", "suggestions: Let's go, Let's eat", "A2", 0.4),
]

# Vocabulary Skills (~40)
VOCABULARY_SKILLS: List[SkillDefinition] = [
    # Everyday (8)
    SkillDefinition("vocab_everyday_greetings", "vocabulary", "everyday", "Greetings & Introductions", "Hello, How are you, Nice to meet you", "A1", 0.25),
    SkillDefinition("vocab_everyday_numbers", "vocabulary", "everyday", "Numbers & Counting", "1-100, ordinals, dates", "A1", 0.3),
    SkillDefinition("vocab_everyday_colors", "vocabulary", "everyday", "Colors", "red, blue, green, dark/light", "A1", 0.25),
    SkillDefinition("vocab_everyday_family", "vocabulary", "everyday", "Family Members", "mother, father, sister, uncle, cousin", "A1", 0.3),
    SkillDefinition("vocab_everyday_food", "vocabulary", "everyday", "Food & Drink", "bread, water, vegetables, meals", "A1", 0.35),
    SkillDefinition("vocab_everyday_clothes", "vocabulary", "everyday", "Clothing", "shirt, pants, shoes, jacket", "A1", 0.35),
    SkillDefinition("vocab_everyday_home", "vocabulary", "everyday", "Home & Furniture", "room, bed, table, kitchen", "A1", 0.35),
    SkillDefinition("vocab_everyday_body", "vocabulary", "everyday", "Body Parts", "head, hand, eye, stomach", "A1", 0.3),

    # Actions (8)
    SkillDefinition("vocab_action_daily_routine", "vocabulary", "actions", "Daily Routine Verbs", "wake up, get dressed, have breakfast", "A1", 0.35),
    SkillDefinition("vocab_action_work", "vocabulary", "actions", "Work Activities", "work, write, call, email, meet", "A2", 0.45),
    SkillDefinition("vocab_action_leisure", "vocabulary", "actions", "Leisure Activities", "play, watch, read, listen, go out", "A1", 0.35),
    SkillDefinition("vocab_action_travel", "vocabulary", "actions", "Travel Verbs", "go, arrive, leave, stay, visit", "A2", 0.45),
    SkillDefinition("vocab_action_shopping", "vocabulary", "actions", "Shopping Actions", "buy, pay, try on, return, exchange", "A2", 0.45),
    SkillDefinition("vocab_action_eating", "vocabulary", "actions", "Eating & Drinking", "eat, drink, order, taste, cook", "A1", 0.35),
    SkillDefinition("vocab_action_communication", "vocabulary", "actions", "Communication Verbs", "say, tell, ask, answer, explain", "A2", 0.5),
    SkillDefinition("vocab_action_movement", "vocabulary", "actions", "Movement Verbs", "walk, run, sit, stand, lie", "A1", 0.35),

    # Descriptive (8)
    SkillDefinition("vocab_describe_feelings", "vocabulary", "descriptive", "Feelings & Emotions", "happy, sad, angry, excited, tired", "A1", 0.35),
    SkillDefinition("vocab_describe_appearance", "vocabulary", "descriptive", "Physical Appearance", "tall, short, young, old, beautiful", "A2", 0.4),
    SkillDefinition("vocab_describe_weather", "vocabulary", "descriptive", "Weather", "sunny, rainy, cold, hot, windy", "A1", 0.3),
    SkillDefinition("vocab_describe_size", "vocabulary", "descriptive", "Size & Quantity", "big, small, heavy, light, long", "A1", 0.35),
    SkillDefinition("vocab_describe_opinion", "vocabulary", "descriptive", "Opinion Adjectives", "good, bad, nice, interesting, boring", "A2", 0.4),
    SkillDefinition("vocab_describe_frequency", "vocabulary", "descriptive", "Frequency Words", "always, usually, often, sometimes, never", "A1", 0.35),
    SkillDefinition("vocab_describe_time", "vocabulary", "descriptive", "Time Expressions", "today, yesterday, tomorrow, now, later", "A1", 0.3),
    SkillDefinition("vocab_describe_quantity", "vocabulary", "descriptive", "Quantity Words", "some, any, many, much, a lot of", "A2", 0.45),

    # Situational (8)
    SkillDefinition("vocab_situation_restaurant", "vocabulary", "situational", "Restaurant Vocabulary", "menu, waiter, bill, tip, reservation", "A2", 0.45),
    SkillDefinition("vocab_situation_airport", "vocabulary", "situational", "Airport & Travel", "flight, boarding pass, gate, luggage", "A2", 0.5),
    SkillDefinition("vocab_situation_hotel", "vocabulary", "situational", "Hotel Vocabulary", "room, reception, check-in, key, service", "A2", 0.45),
    SkillDefinition("vocab_situation_directions", "vocabulary", "situational", "Directions", "left, right, straight, corner, opposite", "A1", 0.4),
    SkillDefinition("vocab_situation_phone", "vocabulary", "situational", "Phone Conversations", "call, answer, leave a message, hang up", "A2", 0.5),
    SkillDefinition("vocab_situation_doctor", "vocabulary", "situational", "Health & Doctor", "sick, medicine, appointment, symptoms", "A2", 0.5),
    SkillDefinition("vocab_situation_shopping", "vocabulary", "situational", "Shopping Vocabulary", "price, size, sale, discount, receipt", "A2", 0.45),
    SkillDefinition("vocab_situation_work", "vocabulary", "situational", "Workplace Vocabulary", "office, meeting, boss, colleague, deadline", "B1", 0.55),

    # Collocations (8)
    SkillDefinition("vocab_colloc_make_do", "vocabulary", "collocations", "Make vs Do", "make a decision, do homework", "A2", 0.55),
    SkillDefinition("vocab_colloc_get", "vocabulary", "collocations", "Get Collocations", "get up, get married, get tired", "A2", 0.5),
    SkillDefinition("vocab_colloc_take", "vocabulary", "collocations", "Take Collocations", "take a photo, take a break, take time", "A2", 0.5),
    SkillDefinition("vocab_colloc_have", "vocabulary", "collocations", "Have Collocations", "have breakfast, have fun, have a shower", "A2", 0.45),
    SkillDefinition("vocab_colloc_verb_noun", "vocabulary", "collocations", "Common Verb+Noun", "catch a bus, miss a flight, tell a story", "B1", 0.55),
    SkillDefinition("vocab_colloc_adj_noun", "vocabulary", "collocations", "Common Adj+Noun", "heavy rain, strong coffee, fast food", "B1", 0.55),
    SkillDefinition("vocab_phrasal_basic", "vocabulary", "phrasal_verbs", "Basic Phrasal Verbs", "turn on/off, get up, look for", "A2", 0.5),
    SkillDefinition("vocab_phrasal_common", "vocabulary", "phrasal_verbs", "Common Phrasal Verbs", "find out, give up, put off, take off", "B1", 0.6),
]

# Listening Skills (~10)
LISTENING_SKILLS: List[SkillDefinition] = [
    # Word Recognition (3)
    SkillDefinition("listening_word_numbers", "listening", "word_recognition", "Hearing Numbers", "dates, times, prices, phone numbers", "A1", 0.4),
    SkillDefinition("listening_word_names", "listening", "word_recognition", "Hearing Names", "names of people and places", "A1", 0.35),
    SkillDefinition("listening_word_key_nouns", "listening", "word_recognition", "Key Nouns", "main subjects in conversation", "A2", 0.45),

    # Gist (3)
    SkillDefinition("listening_gist_topic", "listening", "gist", "Topic Identification", "what is the conversation about", "A2", 0.5),
    SkillDefinition("listening_gist_emotion", "listening", "gist", "Speaker Emotion", "happy, angry, worried, excited", "A2", 0.5),
    SkillDefinition("listening_gist_main_idea", "listening", "gist", "Main Idea", "central point of the message", "B1", 0.55),

    # Detail (4)
    SkillDefinition("listening_detail_specific", "listening", "detail", "Specific Information", "exact facts and details", "A2", 0.5),
    SkillDefinition("listening_detail_sequence", "listening", "detail", "Sequence of Events", "order of actions", "B1", 0.55),
    SkillDefinition("listening_detail_time_place", "listening", "detail", "Time & Place Details", "when and where", "A2", 0.45),
    SkillDefinition("listening_detail_instructions", "listening", "detail", "Following Instructions", "steps and directions", "B1", 0.6),
]

# Pronunciation Skills (~10)
PRONUNCIATION_SKILLS: List[SkillDefinition] = [
    # Sounds (4)
    SkillDefinition("pronunciation_th_sound", "pronunciation", "sounds", "TH Sound", "/th/ as in 'think' and 'this'", "A1", 0.5),
    SkillDefinition("pronunciation_r_l", "pronunciation", "sounds", "R/L Distinction", "right vs light, road vs load", "A2", 0.55),
    SkillDefinition("pronunciation_vowel_pairs", "pronunciation", "sounds", "Vowel Pairs", "ship/sheep, bed/bad", "A2", 0.55),
    SkillDefinition("pronunciation_word_stress", "pronunciation", "sounds", "Word Stress", "PHOto, poTAto, comPUter", "A2", 0.5),

    # Connected Speech (3)
    SkillDefinition("pronunciation_linking", "pronunciation", "connected", "Word Linking", "an apple, turn it on", "B1", 0.6),
    SkillDefinition("pronunciation_weak_forms", "pronunciation", "connected", "Weak Forms", "to, for, and in fast speech", "B1", 0.65),
    SkillDefinition("pronunciation_contractions", "pronunciation", "connected", "Contractions", "I'm, don't, shouldn't", "A2", 0.45),

    # Intonation (3)
    SkillDefinition("pronunciation_intonation_question", "pronunciation", "intonation", "Question Intonation", "rising vs falling", "A2", 0.5),
    SkillDefinition("pronunciation_intonation_statement", "pronunciation", "intonation", "Statement Intonation", "falling patterns", "A2", 0.5),
    SkillDefinition("pronunciation_intonation_list", "pronunciation", "intonation", "List Intonation", "rising, rising, falling", "B1", 0.55),
]

# All skills combined
ALL_SKILLS: List[SkillDefinition] = GRAMMAR_SKILLS + VOCABULARY_SKILLS + LISTENING_SKILLS + PRONUNCIATION_SKILLS

def get_skills_by_domain(domain: str) -> List[SkillDefinition]:
    """Get all skills for a specific domain"""
    return [s for s in ALL_SKILLS if s.domain == domain]

def get_skills_by_level(level: str) -> List[SkillDefinition]:
    """Get all skills for a specific CEFR level"""
    return [s for s in ALL_SKILLS if s.cefr_level == level]

def get_skill_by_key(skill_key: str) -> Optional[SkillDefinition]:
    """Get a skill by its key"""
    for skill in ALL_SKILLS:
        if skill.skill_key == skill_key:
            return skill
    return None

# Export count for verification
SKILL_COUNT = len(ALL_SKILLS)
