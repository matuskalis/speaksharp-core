# LLM Integration Preparation

## Overview
The tutor agent has been refactored to support real LLM integration while maintaining backward compatibility with the demo.

## Architecture

### Two-Layer Error Detection System

```
User Input
    ↓
┌─────────────────────────────────────────┐
│  process_user_input()                   │
│                                         │
│  ┌──────────────────────────────┐      │
│  │  Layer 1: Heuristic          │      │
│  │  - Fast regex-based rules    │      │
│  │  - Common error patterns     │      │
│  │  - Tagged with "[heuristic]" │      │
│  └──────────────────────────────┘      │
│             ↓                           │
│  ┌──────────────────────────────┐      │
│  │  Layer 2: LLM Analysis       │      │
│  │  - Contextual understanding  │      │
│  │  - Natural language feedback │      │
│  │  - Nuanced corrections       │      │
│  └──────────────────────────────┘      │
│             ↓                           │
│  ┌──────────────────────────────┐      │
│  │  Merge & Deduplicate         │      │
│  │  - Combine both layers       │      │
│  │  - Remove duplicates         │      │
│  │  - Limit to top 5 errors     │      │
│  └──────────────────────────────┘      │
└─────────────────────────────────────────┘
    ↓
TutorResponse
```

## Key Components

### 1. `call_llm_tutor(user_text, context)` - NEW
**Location**: `app/tutor_agent.py:102`

Standalone function that simulates (and will replace with) real LLM API calls.

**Current Behavior**:
- Simulates intelligent error detection
- Returns TutorResponse with contextual feedback
- Detects patterns like "I like" vs "I'd like" for ordering contexts

**Production Integration**:
```python
def call_llm_tutor(user_text: str, context: dict | None = None) -> TutorResponse:
    # 1. Construct API request
    messages = [
        {"role": "system", "content": TUTOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_text}
    ]

    # 2. Call LLM API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )

    # 3. Parse JSON response
    data = json.loads(response.choices[0].message.content)

    # 4. Validate and return
    return TutorResponse(
        message=data['message'],
        errors=[Error(**err) for err in data['errors']],
        micro_task=data.get('micro_task')
    )
```

### 2. `process_user_input(user_text, context)` - REFACTORED
**Location**: `app/tutor_agent.py:190`

Main entry point for processing user input.

**New Pipeline**:
1. Calls `_detect_errors()` for heuristic layer
2. Tags heuristic errors with "[heuristic] " prefix
3. Calls `call_llm_tutor()` for LLM layer
4. Merges and deduplicates errors
5. Prefers LLM message over generated ones
6. Returns unified TutorResponse

**Signature unchanged**: Maintains backward compatibility.

### 3. Expected LLM Response Format

```json
{
  "message": "I understand! Just a small tip: I'd like a large cappuccino.",
  "errors": [
    {
      "type": "vocab",
      "user_sentence": "I like large cappuccino.",
      "corrected_sentence": "I'd like a large cappuccino.",
      "explanation": "When ordering, use 'I'd like' instead of 'I like' to sound more natural."
    },
    {
      "type": "grammar",
      "user_sentence": "I like large cappuccino.",
      "corrected_sentence": "I like a large cappuccino.",
      "explanation": "Missing article 'a' before singular countable noun."
    }
  ],
  "micro_task": "Try saying that again with both corrections."
}
```

### 4. Error Types (enum)
- `grammar` - Articles, tenses, agreement, word order
- `vocab` - Wrong word, collocation, register
- `fluency` - Hesitations, restarts, low fluency
- `pronunciation_placeholder` - Pronunciation issues (future)
- `structure` - Sentence structure, discourse problems

## Demo Integration

### Enhanced Output
The demo (`demo_integration.py`) now shows:
- **Turn 1**: Full breakdown of heuristic vs LLM errors
- **Other turns**: Icons to distinguish error sources
  - 🔍 = Heuristic layer
  - 🤖 = LLM layer

Example output:
```
⚠ Errors detected (2):

  📋 DETAILED ERROR ANALYSIS (Two-Layer System):

  🔍 Heuristic Layer (2 errors):
    • grammar: [heuristic] Use 'want to' before a verb.
      Corrected: Hello! I want to order coffee, please.

  🤖 LLM Layer (0 errors):
```

## Error Handling Strategy

### Malformed LLM Responses
1. **Invalid JSON**: Parse what you can, use empty arrays for missing fields
2. **Missing required fields**: Skip that error, keep valid ones
3. **Invalid error types**: Validate against ErrorType enum, skip invalids
4. **Complete failure**: Fall back to heuristic-only mode
5. **Never crash**: Always return valid TutorResponse

### Quality Safeguards
- Limit total errors to 5 per response
- Deduplicate similar corrections
- Prefer LLM message over generated fallbacks
- Tag heuristic errors for transparency

## Files Modified

### 1. `app/tutor_agent.py`
- **Added**: Module docstring with integration instructions
- **Added**: `call_llm_tutor()` function
- **Refactored**: `process_user_input()` to use two-layer pipeline
- **Removed**: `_simulate_llm_response()` (obsolete)
- **Removed**: `_parse_response()` (obsolete)
- **Unchanged**: `_detect_errors()`, `_generate_*()` helper methods

### 2. `demo_integration.py`
- **Enhanced**: Error display to show heuristic vs LLM breakdown
- **Added**: Detailed analysis view for Turn 1
- **Added**: Icons (🔍/🤖) to distinguish error sources
- **Unchanged**: Overall flow and structure

### 3. No changes to:
- `app/models.py` ✓
- `app/srs_system.py` ✓
- `app/state_machine.py` ✓
- `app/scenarios.py` ✓
- `database/schema.sql` ✓

## Integration Checklist

When replacing with real LLM API:

- [ ] Install LLM client library (`openai`, `anthropic`, etc.)
- [ ] Add API key to environment variables
- [ ] Replace `call_llm_tutor()` function body with API call
- [ ] Add retry logic for API failures
- [ ] Add rate limiting
- [ ] Add request/response logging
- [ ] Add cost tracking
- [ ] Test error handling with malformed responses
- [ ] Monitor latency and adjust timeout
- [ ] A/B test heuristic-only vs combined pipeline

## Testing

### Run Demo
```bash
source venv/bin/activate
python demo_integration.py
```

### Run Tutor Agent Tests
```bash
cd app
source ../venv/bin/activate
python tutor_agent.py
```

### Expected Results
- ✓ Demo completes without errors
- ✓ Shows 8 total errors detected (heuristic + LLM)
- ✓ Turn 1 displays detailed breakdown
- ✓ Both layers contributing to error detection
- ✓ Natural LLM-style messages displayed
- ✓ SRS cards created from errors

## Next Steps

1. **Immediate**: Add API key management and environment config
2. **Short-term**: Implement real OpenAI/Anthropic API integration
3. **Medium-term**: Add conversation history to LLM context
4. **Long-term**: Fine-tune LLM on SpeakSharp correction patterns
