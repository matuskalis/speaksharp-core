# SpeakSharp API - Quick Start Guide

## Prerequisites

1. **Database Setup**
   ```bash
   # Create database
   createdb speaksharp

   # Apply schema
   psql speaksharp < database/schema.sql

   # Set environment variable
   export DATABASE_URL="postgresql://user:password@localhost:5432/speaksharp"
   ```

2. **Install Dependencies**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Start the API Server

```bash
# Method 1: Direct Python
python -m app.api

# Method 2: Using uvicorn
uvicorn app.api:app --reload --port 8000
```

The server will start at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## Common API Workflows

### 1. Create a User

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "level": "A1",
    "native_language": "Spanish",
    "goals": {"improve_speaking": true},
    "interests": ["travel", "food", "technology"]
  }'
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "level": "A1",
  "native_language": "Spanish",
  "goals": {"improve_speaking": true},
  "interests": ["travel", "food", "technology"],
  "created_at": "2025-11-15T21:00:00",
  "updated_at": "2025-11-15T21:00:00"
}
```

Save the `user_id` for subsequent requests.

### 2. Text Tutoring Session

```bash
USER_ID="your-user-id-from-step-1"

curl -X POST http://localhost:8000/api/tutor/text \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"text\": \"I go to cinema yesterday\",
    \"context\": \"Talking about weekend activities\"
  }"
```

**Response:**
```json
{
  "message": "Good effort! I can help you improve that.",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "I go to cinema yesterday",
      "corrected_sentence": "I went to the cinema yesterday",
      "explanation": "Use past tense 'went' with 'yesterday'. Also add 'the' before 'cinema'."
    }
  ],
  "micro_task": "Try making another sentence about what you did last week.",
  "session_id": "650e8400-e29b-41d4-a716-446655440000"
}
```

The errors are automatically logged to the database.

### 3. Get Due SRS Cards

```bash
USER_ID="your-user-id"

curl http://localhost:8000/api/srs/due/$USER_ID?limit=20
```

**Response:**
```json
{
  "cards": [
    {
      "card_id": "750e8400-e29b-41d4-a716-446655440000",
      "front": "What is the past tense of 'go'?",
      "back": "went",
      "card_type": "definition"
    }
  ],
  "count": 1
}
```

### 4. Submit SRS Review

```bash
curl -X POST http://localhost:8000/api/srs/review \
  -H "Content-Type: application/json" \
  -d '{
    "card_id": "750e8400-e29b-41d4-a716-446655440000",
    "quality": 4,
    "response_time_ms": 3500,
    "user_response": "went",
    "correct": true
  }'
```

**Quality Scale:**
- 0: Complete blackout
- 1: Incorrect response, correct answer felt unfamiliar
- 2: Incorrect response, correct answer felt familiar
- 3: Correct with difficulty
- 4: Correct with hesitation
- 5: Perfect recall

**Response:**
```json
{
  "status": "success",
  "message": "Review recorded successfully",
  "card_id": "750e8400-e29b-41d4-a716-446655440000"
}
```

The card's next review date is automatically calculated using the SM-2 algorithm.

### 5. Get User Errors

```bash
USER_ID="your-user-id"

# Get all errors
curl http://localhost:8000/api/errors/$USER_ID?limit=50

# Get only unrecycled errors (not yet converted to SRS cards)
curl http://localhost:8000/api/errors/$USER_ID?limit=50&unrecycled_only=true
```

**Response:**
```json
{
  "errors": [
    {
      "error_id": "850e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "error_type": "grammar",
      "user_sentence": "I go to cinema yesterday",
      "corrected_sentence": "I went to the cinema yesterday",
      "explanation": "Use past tense 'went' with 'yesterday'",
      "occurred_at": "2025-11-15T21:05:00",
      "recycled": false,
      "recycled_count": 0
    }
  ],
  "count": 1
}
```

### 6. Create SRS Card from Error

```bash
ERROR_ID="your-error-id"

curl -X POST http://localhost:8000/api/srs/from-error/$ERROR_ID
```

**Response:**
```json
{
  "status": "success",
  "message": "Card created from error",
  "card_id": "950e8400-e29b-41d4-a716-446655440000",
  "error_id": "850e8400-e29b-41d4-a716-446655440000"
}
```

The error is now marked as `recycled: true`.

### 7. Get Weakest Skills

```bash
USER_ID="your-user-id"

curl http://localhost:8000/api/skills/weakest/$USER_ID?limit=5
```

**Response:**
```json
{
  "skills": [
    {
      "skill_key": "grammar.articles",
      "mastery_score": 25.5,
      "error_count": 8
    },
    {
      "skill_key": "grammar.past_simple",
      "mastery_score": 42.0,
      "error_count": 5
    }
  ],
  "count": 2
}
```

### 8. Voice Tutoring (Requires Audio File)

```bash
USER_ID="your-user-id"

curl -X POST http://localhost:8000/api/tutor/voice \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"audio_path\": \"/path/to/audio.wav\"
  }"
```

**Response:**
```json
{
  "transcript": "I want order a coffee",
  "message": "Good try! Let me help you with that.",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "I want order a coffee",
      "corrected_sentence": "I want to order a coffee",
      "explanation": "Use 'want to' before a verb"
    }
  ],
  "audio_url": "/tmp/response_audio.mp3",
  "session_id": "a50e8400-e29b-41d4-a716-446655440000"
}
```

## Complete User Journey Example

```bash
# 1. Create user
USER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"level": "A1", "native_language": "Spanish"}')

USER_ID=$(echo $USER_RESPONSE | jq -r '.user_id')
echo "Created user: $USER_ID"

# 2. Practice with tutor
curl -s -X POST http://localhost:8000/api/tutor/text \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"text\": \"I go to school yesterday\"
  }" | jq

# 3. Get errors
ERRORS=$(curl -s http://localhost:8000/api/errors/$USER_ID?unrecycled_only=true)
echo "$ERRORS" | jq

# 4. Create SRS card from first error
ERROR_ID=$(echo "$ERRORS" | jq -r '.errors[0].error_id')
curl -s -X POST http://localhost:8000/api/srs/from-error/$ERROR_ID | jq

# 5. Get due cards
curl -s http://localhost:8000/api/srs/due/$USER_ID | jq

# 6. Practice more
curl -s -X POST http://localhost:8000/api/tutor/text \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"text\": \"She don't like coffee\"
  }" | jq

# 7. Check weakest skills
curl -s http://localhost:8000/api/skills/weakest/$USER_ID | jq
```

## Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2025-11-15T21:10:00"
}
```

## Interactive API Documentation

Visit `http://localhost:8000/docs` in your browser for:
- Complete API reference
- Interactive request builder
- Schema documentation
- Try-it-out functionality

## Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Create user
response = requests.post(f"{BASE_URL}/api/users", json={
    "level": "A1",
    "native_language": "Spanish",
    "interests": ["travel", "food"]
})
user = response.json()
user_id = user["user_id"]
print(f"Created user: {user_id}")

# Text tutoring
response = requests.post(f"{BASE_URL}/api/tutor/text", json={
    "user_id": user_id,
    "text": "I go to cinema yesterday",
    "context": "Weekend activities"
})
result = response.json()
print(f"Tutor response: {result['message']}")
print(f"Errors found: {len(result['errors'])}")

# Get due cards
response = requests.get(f"{BASE_URL}/api/srs/due/{user_id}?limit=20")
cards = response.json()
print(f"Due cards: {cards['count']}")

# Get errors
response = requests.get(f"{BASE_URL}/api/errors/{user_id}?unrecycled_only=true")
errors = response.json()
print(f"Unrecycled errors: {errors['count']}")
```

## Configuration

### Stub Mode (No External APIs)
```bash
# Just database - LLM/ASR/TTS will use stubs
export DATABASE_URL="postgresql://..."
python -m app.api
```

### Full Mode (Real APIs)
```bash
# Database + OpenAI for everything
export DATABASE_URL="postgresql://..."
export OPENAI_API_KEY="sk-..."
export SPEAKSHARP_ENABLE_LLM=true
export SPEAKSHARP_ENABLE_ASR=true
export SPEAKSHARP_ENABLE_TTS=true
python -m app.api
```

## Troubleshooting

### Database Connection Failed
```bash
# Check environment variable
echo $DATABASE_URL

# Test connection manually
psql $DATABASE_URL -c "SELECT 1"

# Verify schema is loaded
psql $DATABASE_URL -c "\dt"
```

### Import Errors
```bash
# Ensure all dependencies installed
pip install -r requirements.txt

# Verify psycopg
python -c "import psycopg; print(psycopg.__version__)"

# Verify FastAPI
python -c "import fastapi; print(fastapi.__version__)"
```

### Port Already in Use
```bash
# Use different port
uvicorn app.api:app --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill
```

## Next Steps

1. **Frontend Integration**: Build React/Next.js app consuming this API
2. **Authentication**: Add Supabase Auth middleware
3. **File Upload**: Implement multipart/form-data for audio files
4. **WebSocket**: Add real-time features for live tutoring
5. **Deployment**: Deploy to production (Fly.io, Railway, etc.)

## Support

- API Docs: `http://localhost:8000/docs`
- Full Documentation: See `README.md`
- Database Schema: See `database/schema.sql`
- Implementation Status: See `DATABASE_API_COMPLETE.md`
