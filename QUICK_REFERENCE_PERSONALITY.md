# Quick Reference - AI Tutor Personality Modes

## How to Use in Your Code

### Basic Usage

```python
from app.tutor_agent import TutorAgent

tutor = TutorAgent()

response = tutor.process_user_input(
    user_text="I go to cinema yesterday",
    context={
        "level": "A2",                    # Required: A1, A2, B1, B2, C1, C2
        "personality_mode": "encouraging" # Optional: See modes below
    }
)

print(response.message)      # Alex's warm, natural response
print(response.errors)       # List of Error objects
print(response.micro_task)   # Practice suggestion
```

### With Conversation Memory

```python
from app.tutor_agent import TutorAgent
from app.db import DatabaseClient

db = DatabaseClient()
tutor = TutorAgent(user_id="user-123", db=db)

# Tutor automatically loads and references past conversations
response = tutor.process_user_input(
    "I went to the park",
    context={"level": "A2"}
)

# Alex will say things like:
# "Great job! I noticed you used the past tense correctly this time -
#  remember last session we worked on that? You're really improving!"
```

## Personality Modes

### 1. Encouraging (Super Supportive)
```python
context = {
    "level": "A1",
    "personality_mode": "encouraging"
}
```
**Best for:** Nervous beginners, confidence building
**Tone:** Extremely warm and enthusiastic
**Corrections:** Only 1-2 most critical errors, very gentle

### 2. Professional (Business English)
```python
context = {
    "level": "B2",
    "personality_mode": "professional"
}
```
**Best for:** Business English, workplace communication
**Tone:** Polished but approachable
**Corrections:** Focus on formality, register, business vocabulary

### 3. Casual (Everyday Conversation)
```python
context = {
    "level": "B1",
    "personality_mode": "casual"
}
```
**Best for:** Conversational practice, learning slang
**Tone:** Super relaxed and friendly
**Corrections:** Focus on how people actually talk

### 4. Strict (High Accuracy)
```python
context = {
    "level": "C1",
    "personality_mode": "strict"
}
```
**Best for:** Advanced learners, exam prep
**Tone:** Detail-oriented and thorough
**Corrections:** ALL errors (up to 5), comprehensive explanations

### 5. Default (Auto-Adapt)
```python
context = {
    "level": "B1"
    # No personality_mode specified
}
```
**Behavior:** Automatically selects:
- Beginner-friendly for A1, A2, B1
- Advanced mode for B2, C1, C2

## Context Parameters

```python
context = {
    # Required
    "level": "A2",                    # A1, A2, B1, B2, C1, C2

    # Personality (optional)
    "personality_mode": "encouraging", # encouraging, professional, casual, strict

    # Learner profile (optional, enriches responses)
    "native_language": "Spanish",
    "goals": ["travel", "work"],
    "interests": ["sports", "music"],

    # Error tracking (optional, auto-populated if using DB)
    "recent_error_patterns": {
        "grammar": 5,
        "vocab": 2
    },
    "weak_skills": [
        {"skill": "articles", "mastery": 45},
        {"skill": "past_tense", "mastery": 60}
    ],

    # Scenario mode (special)
    "mode": "scenario",
    "scenario_id": "cafe_ordering",
    "turn_number": 1
}
```

## Response Object

```python
response = TutorResponse(
    message="Alex's warm, natural response",
    errors=[
        Error(
            type=ErrorType.GRAMMAR,
            user_sentence="I go to cinema",
            corrected_sentence="I went to the cinema",
            explanation="Use past tense 'went' with 'yesterday'"
        )
    ],
    micro_task="Make 3 sentences using past tense verbs",
    scenario_complete=False,           # Only for scenario mode
    success_evaluation="Good progress" # Only when scenario_complete=True
)
```

## Tutor Characteristics by Mode

| Feature | Encouraging | Professional | Casual | Strict | Default |
|---------|------------|--------------|---------|--------|---------|
| **Warmth** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Formality** | Low | High | Very Low | Medium | Varies |
| **Error Count** | 1-2 | 2-3 | 1-2 | 3-5 | 1-3 |
| **Explanation Detail** | High | Medium | Low | Very High | Medium |
| **Encouragement** | Very High | Medium | High | Low | Medium |
| **Best For** | Beginners | Business | Casual chat | Advanced | General |

## Example Responses by Mode

**Input:** "I want go to coffee shop"

### Encouraging
```
"Hey! Great effort! I can see what you're trying to say. Just one tiny thing -
we need 'to' between 'want' and 'go'. So it's 'I want to go to the coffee shop.'
Try saying it again - I know you've got this!"
```

### Professional
```
"In professional settings, we'd say 'I would like to go to the coffee shop.'
Note the infinitive 'to go' after 'want.' This construction is essential for
clear business communication."
```

### Casual
```
"Hey! So close! You just need 'to' in there - 'I want TO go to the coffee shop.'
Most people actually say 'I wanna go' in casual conversation. Give it another shot!"
```

### Strict
```
"I noticed an error. The sentence should be 'I want to go to the coffee shop.'
Specifically: 1) After 'want,' use infinitive 'to go'. 2) Add article 'the'
before 'coffee shop'. Review infinitive constructions and practice three sentences."
```

## Special Features

### Conversation Memory
When initialized with `user_id` and `db`:
- Remembers past conversations
- References improvements: "You're getting better at this!"
- Tracks recurring errors
- Makes learner feel remembered

### Level Adaptation
Automatically adjusts:
- **A1-A2**: Simple vocabulary, short sentences, very patient
- **B1-B2**: Everyday language, normal pace, natural conversation
- **C1-C2**: Sophisticated vocabulary, idioms, native-like speech

### Natural Variation
Never repeats the same phrase:
- 10+ different praise responses
- Multiple correction lead-ins
- Varied conversation starters
- Human-like filler words

## Files Modified

1. **`/Users/matuskalis/vorex-backend/app/tutor_agent.py`**
   - Enhanced personality in system prompt
   - Natural conversation helpers
   - Varied response generation

2. **`/Users/matuskalis/vorex-backend/app/llm_client.py`**
   - 4 new personality mode prompts
   - Mode selection logic
   - Conversation memory integration
   - Enhanced scenario roleplay

## Tips

1. **Match mode to learner needs:**
   - Nervous? → Encouraging
   - Business? → Professional
   - Casual practice? → Casual
   - Perfectionist? → Strict

2. **Always provide level:**
   - Tutor adapts vocabulary and complexity
   - Critical for appropriate responses

3. **Enable memory when possible:**
   - Initialize with `user_id` and `db`
   - Creates personalized experience
   - Tracks real progress

4. **Trust the personality:**
   - Responses will vary naturally
   - No robotic repetition
   - Feels like a real teacher

## See Also

- **`TUTOR_PERSONALITY_GUIDE.md`** - Complete guide with examples
- **`PERSONALITY_EXAMPLES.md`** - Detailed prompt examples
- **`test_personality_modes.py`** - Test script for all modes

---

**Quick Start:**
```python
from app.tutor_agent import TutorAgent

tutor = TutorAgent()
response = tutor.process_user_input(
    "I go to cinema yesterday",
    context={"level": "A2", "personality_mode": "encouraging"}
)
print(response.message)
```

Done! Alex will respond warmly and naturally.
