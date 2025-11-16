# LLM Integration - Complete Implementation Guide

## Overview

The SpeakSharp tutor agent now has full LLM integration with two operational modes:
- **Stub Mode** (default): Heuristic-only error detection, no API calls required
- **LLM Mode**: Real API integration with OpenAI or Anthropic for enhanced feedback

## Architecture

### Two-Layer Error Detection System

```
User Input
    ↓
┌─────────────────────────────────────────────────────────┐
│  TutorAgent.process_user_input()                        │
│                                                          │
│  ┌────────────────────────────────┐                     │
│  │  Layer 1: Heuristic            │                     │
│  │  - Regex-based rules           │                     │
│  │  - Fast, offline               │                     │
│  │  - Tagged with "[heuristic]"   │                     │
│  └────────────────────────────────┘                     │
│               ↓                                          │
│  ┌────────────────────────────────┐                     │
│  │  Layer 2: LLM (via llm_client) │                     │
│  │  - Context-aware               │                     │
│  │  - Natural language feedback   │                     │
│  │  - Retry logic + fallback      │                     │
│  └────────────────────────────────┘                     │
│               ↓                                          │
│  ┌────────────────────────────────┐                     │
│  │  Merge & Deduplicate           │                     │
│  │  - Combine both layers         │                     │
│  │  - Prioritize LLM message      │                     │
│  │  - Limit to top 5 errors       │                     │
│  └────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
    ↓
TutorResponse (message, errors[], micro_task)
```

## Implementation Files

### 1. `app/config.py`
**Purpose**: Configuration management for API keys and settings

**Key Features**:
- Loads from environment variables
- Supports both OpenAI and Anthropic
- Feature flags (enable_llm, debug_mode, log_api_calls)
- Default models: gpt-4o-mini (OpenAI), claude-3-5-haiku-20241022 (Anthropic)

**Environment Variables**:
```bash
SPEAKSHARP_LLM_PROVIDER=openai|anthropic
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
SPEAKSHARP_LLM_MODEL=model_name
SPEAKSHARP_ENABLE_LLM=true|false
SPEAKSHARP_DEBUG=true|false
SPEAKSHARP_LOG_API=true|false
```

### 2. `app/llm_client.py`
**Purpose**: Unified LLM API wrapper with retry logic and error handling

**Key Components**:
- `LLMClient` class: Main wrapper
- `call_tutor()`: Primary entry point
- `_call_openai()`: OpenAI API integration
- `_call_anthropic()`: Anthropic API integration
- `_parse_response()`: JSON validation and parsing
- `_stub_response()`: Fallback when API unavailable

**Features**:
- Automatic retry with exponential backoff
- Graceful fallback to stub mode on failure
- Response validation and error handling
- Context-aware prompt construction
- Debug logging

**System Prompt**:
Enforces strict JSON output format:
```json
{
  "message": "Encouraging response",
  "errors": [
    {
      "type": "grammar|vocab|fluency|structure",
      "user_sentence": "Original text",
      "corrected_sentence": "Corrected text",
      "explanation": "Brief explanation"
    }
  ],
  "micro_task": "Optional practice task"
}
```

### 3. `app/tutor_agent.py`
**Purpose**: Integration point between heuristics and LLM

**Key Changes**:
- `call_llm_tutor()` delegates to `llm_client.call_tutor()`
- `process_user_input()` merges heuristic + LLM errors
- Heuristic errors tagged with "[heuristic] " prefix
- LLM errors used as-is
- Deduplication logic for similar corrections

### 4. `.env.example`
Template for environment configuration with all available options.

### 5. `test_llm_modes.py`
Comprehensive test script that:
- Tests configuration loading
- Tests LLM client in isolation
- Tests full tutor agent integration
- Shows clear output for both modes
- Provides instructions for LLM mode setup

## Operational Modes

### Stub Mode (Default)

**When Active**:
- No API key configured
- `SPEAKSHARP_ENABLE_LLM=false`
- API call fails after retries
- LLM library not installed

**Behavior**:
- LLM layer returns empty errors
- Heuristic layer handles all error detection
- All errors tagged with 🔍 (heuristic)
- No API costs
- Works offline

**Example Output**:
```
Tutor: Perfect, I understood you clearly.
Total Errors: 2
  🔍 Heuristic | grammar: Use 'want to' before a verb
  🔍 Heuristic | grammar: Missing article 'a'
```

### LLM Mode

**When Active**:
- API key configured in .env
- `SPEAKSHARP_ENABLE_LLM=true` (default)
- API client library installed

**Behavior**:
- Both heuristic and LLM layers active
- LLM provides contextual corrections
- Errors from both sources merged
- LLM message preferred over generic ones
- Errors tagged with 🔍 (heuristic) or 🤖 (LLM)

**Example Output**:
```
Tutor: I understand! Try: "I'd like a large cappuccino."
Total Errors: 3
  🔍 Heuristic | grammar: Missing article 'a'
  🤖 LLM | vocab: Use 'I'd like' instead of 'I like' when ordering
  🔍 Heuristic | grammar: Use 'want to' before a verb
```

## Setup Instructions

### Quick Start (Stub Mode)
No setup needed. System works out of the box.

```bash
python demo_integration.py  # Runs with heuristic-only
```

### Enable LLM Mode

**Step 1**: Copy environment template
```bash
cp .env.example .env
```

**Step 2**: Edit `.env` and add your API key

For OpenAI:
```bash
OPENAI_API_KEY=sk-...
SPEAKSHARP_LLM_PROVIDER=openai
SPEAKSHARP_LLM_MODEL=gpt-4o-mini  # or gpt-4o, gpt-4-turbo
```

For Anthropic:
```bash
ANTHROPIC_API_KEY=sk-ant-...
SPEAKSHARP_LLM_PROVIDER=anthropic
SPEAKSHARP_LLM_MODEL=claude-3-5-haiku-20241022  # or sonnet
```

**Step 3**: Install API client library
```bash
pip install openai      # for OpenAI
# OR
pip install anthropic   # for Anthropic
```

**Step 4**: Run demo with LLM
```bash
python demo_integration.py
```

## Testing

### Test Configuration
```bash
cd app
python config.py
```

Expected output shows provider, model, API key status.

### Test LLM Client
```bash
cd app
python llm_client.py
```

Runs 3 test cases and shows responses.

### Test Full Integration
```bash
python test_llm_modes.py
```

Comprehensive test showing:
1. Configuration status
2. LLM client behavior
3. Tutor agent two-layer system
4. Instructions for enabling LLM mode

### Run Full Demo
```bash
python demo_integration.py
```

Complete daily loop with all components.

## Error Handling

### Graceful Degradation
1. **No API key**: Falls back to stub mode
2. **Library not installed**: Falls back to stub mode
3. **API call fails**: Retries 3x with backoff
4. **All retries fail**: Falls back to stub mode
5. **Malformed JSON response**: Returns basic response
6. **Invalid error types**: Skips invalid errors

### Debug Mode
Enable verbose logging:
```bash
SPEAKSHARP_DEBUG=true
```

Shows:
- API call attempts and failures
- JSON parsing errors
- Retry attempts
- Fallback triggers

### API Call Logging
Track all API calls:
```bash
SPEAKSHARP_LOG_API=true
```

Logs timestamp, provider, and model for each call.

## Cost Management

### Recommended Models

**Development/Testing**:
- OpenAI: `gpt-4o-mini` (~$0.15/1M input tokens)
- Anthropic: `claude-3-5-haiku-20241022` (~$0.80/1M input tokens)

**Production (higher quality)**:
- OpenAI: `gpt-4o` (~$2.50/1M input tokens)
- Anthropic: `claude-3-5-sonnet-20241022` (~$3.00/1M input tokens)

### Token Usage
Typical per-correction API call:
- System prompt: ~200 tokens
- User message: ~50-100 tokens
- Response: ~100-200 tokens
- **Total**: ~400 tokens per correction

Daily user session (~10 corrections):
- ~4,000 tokens
- Cost with gpt-4o-mini: ~$0.0006
- Cost per 1,000 users/day: ~$0.60

### Cost Control Features
- Max tokens capped at 500
- Errors limited to 3 per response
- Heuristic layer reduces API calls
- Timeout prevents runaway costs
- Retry limit prevents infinite loops

## Integration Checklist

- [x] Configuration system (`app/config.py`)
- [x] LLM client wrapper (`app/llm_client.py`)
- [x] Tutor agent integration (`app/tutor_agent.py`)
- [x] OpenAI API support
- [x] Anthropic API support
- [x] Retry logic with exponential backoff
- [x] Graceful fallback to stub mode
- [x] JSON response validation
- [x] Error deduplication
- [x] Context-aware prompts
- [x] Debug logging
- [x] API call logging
- [x] Environment configuration (`.env.example`)
- [x] Comprehensive test script (`test_llm_modes.py`)
- [x] Documentation (this file)
- [x] Updated README.md
- [x] Demo runs in both modes

## Next Steps

### Short-term Enhancements
- [ ] Add conversation history to LLM context
- [ ] Implement caching for repeated corrections
- [ ] Add cost tracking and usage metrics
- [ ] A/B test heuristic-only vs combined pipeline

### Medium-term
- [ ] Fine-tune LLM on SpeakSharp correction patterns
- [ ] Add streaming responses for real-time feedback
- [ ] Implement rate limiting per user
- [ ] Add support for other LLM providers (local models, etc.)

### Long-term
- [ ] Multi-agent evaluation pipeline
- [ ] Specialized models for different error types
- [ ] Advanced prompt engineering based on user data
- [ ] Reinforcement learning from user feedback

## Troubleshooting

### "No API key configured" warning
- Check `.env` file exists in project root
- Verify key name matches provider (OPENAI_API_KEY or ANTHROPIC_API_KEY)
- Restart application after adding key

### "openai/anthropic package not installed"
- Install with: `pip install openai` or `pip install anthropic`
- Check virtual environment is activated

### API calls failing
- Enable debug mode: `SPEAKSHARP_DEBUG=true`
- Check API key is valid
- Verify network connectivity
- Check provider API status page

### Unexpected errors in output
- Review system prompt in `llm_client.py`
- Check error type enum in `models.py`
- Enable debug mode to see raw LLM responses

### High costs
- Use cheaper models (gpt-4o-mini, haiku)
- Reduce max_tokens limit
- Add caching layer
- Implement request throttling

## Files Modified/Created

**Created**:
- `app/config.py` (118 lines)
- `app/llm_client.py` (293 lines)
- `.env.example` (48 lines)
- `test_llm_modes.py` (239 lines)
- `LLM_INTEGRATION_COMPLETE.md` (this file)

**Modified**:
- `app/tutor_agent.py` (replaced call_llm_tutor implementation)
- `requirements.txt` (added openai, anthropic)
- `README.md` (added LLM configuration section)

**No changes**:
- `app/models.py` ✓
- `app/state_machine.py` ✓
- `app/scenarios.py` ✓
- `app/lessons.py` ✓
- `app/drills.py` ✓
- `app/srs_system.py` ✓
- `demo_integration.py` ✓
- `database/schema.sql` ✓

## Conclusion

LLM integration is **complete and production-ready**. The system:
- ✅ Works out of the box (stub mode)
- ✅ Supports real API integration (OpenAI, Anthropic)
- ✅ Handles errors gracefully
- ✅ Falls back automatically
- ✅ Fully tested
- ✅ Well documented
- ✅ Cost-conscious defaults

The two-layer architecture ensures reliability while maximizing quality when LLM is available.
