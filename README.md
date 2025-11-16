# SpeakSharp Core MVP

AI-powered English learning tutor core system with state machine, scenario-based learning, error tagging, and spaced repetition.

## Project Structure

```
speaksharp-core/
├── app/
│   ├── models.py           # Pydantic data models
│   ├── state_machine.py    # App state machine with 5 states
│   ├── tutor_agent.py      # AI tutor with error tagging
│   ├── scenarios.py        # 5 conversation scenarios
│   ├── lessons.py          # 11 structured lessons (A1-A2)
│   └── srs_system.py       # Spaced repetition system (SM-2)
├── database/
│   └── schema.sql          # Supabase-ready PostgreSQL schemas
├── demo_integration.py     # End-to-end runnable demo
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Components

### 1. State Machine (`state_machine.py`)

Five states with transitions:
- `onboarding` - Initial setup and level assessment
- `daily_review` - SRS-based review session
- `scenario_session` - Conversation practice
- `free_chat` - Open conversation mode
- `feedback_report` - Session summary

Router prioritizes: onboarding → daily_review → scenario → free_chat

### 2. Tutor Agent (`tutor_agent.py`)

AI tutor with:
- System prompt enforcing correction strategy
- Error detection and tagging (grammar, vocab, fluency, structure, pronunciation)
- Micro-task generation
- Strict JSON output format

Error types:
- `grammar` - Articles, tenses, agreement, word order
- `vocab` - Wrong word, collocation, register
- `fluency` - Hesitations, restarts
- `structure` - Sentence structure issues
- `pronunciation_placeholder` - Pronunciation errors (placeholder)

### 3. Scenario Templates (`scenarios.py`)

Five executable scenarios:
- **Café Ordering** (A1-B1) - Transactional conversation
- **Self Introduction** (A1-B2) - Social meeting
- **Asking for Directions** (A2-B1) - Navigation and spatial language
- **Making a Doctor's Appointment** (A2-B2) - Phone conversation, health vocabulary
- **Talk About Your Day** (A2-B2) - Narrative practice

Each with:
- Situation description
- User goal and task
- Success criteria
- Difficulty tags
- User variables

### 4. Lesson System (`lessons.py`)

11 structured lessons covering A1-A2 grammar and communication:
- **Present Simple Basics** - Daily routines
- **Articles (A, An, The)** - Article usage
- **Past Simple Regular** - Regular past tense
- **Making Requests** - Polite requests with modals
- **Question Formation** - Wh- and Yes/No questions
- **Prepositions of Time** - At, In, On
- **Present Continuous** - Actions happening now
- **Comparatives & Superlatives** - Comparing things
- **Future Going To** - Plans and intentions
- **Past Simple Irregular** - Irregular verbs
- **Can (Ability/Permission)** - Modal can usage

Each lesson includes:
- Context and explanation
- Target language structure
- Examples
- Controlled practice tasks (3-4)
- Freer production task
- Summary

### 5. SRS System (`srs_system.py`)

Spaced repetition with SM-2 algorithm:
- `add_item()` - Create new card
- `get_due_items()` - Fetch cards for review
- `update_item()` - Update after review with SM-2 calculation
- `schedule_next_review()` - Calculate next review date
- `create_card_from_error()` - Auto-create cards from errors

Card types: definition, cloze, production, pronunciation, error_repair

### 6. Database Schema (`database/schema.sql`)

Supabase-ready PostgreSQL with tables:
- `user_profiles` - User data and level
- `srs_cards` - SRS cards with SM-2 data
- `srs_reviews` - Review history
- `skill_graph_nodes` - Skill tracking
- `error_log` - Error history
- `sessions` - Session tracking
- `evaluations` - Assessment results
- `content_library` - Lessons and scenarios

Functions: `get_due_cards()`, `update_card_after_review()`, `create_card_from_error()`, `update_skill_node()`, `get_weakest_skills()`

## Installation

```bash
cd speaksharp-core
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## LLM Configuration (Optional)

The tutor agent can run in two modes:
- **Stub mode** (default): Uses heuristic error detection only, no API calls needed
- **LLM mode**: Connects to OpenAI or Anthropic for enhanced contextual feedback

### Quick Start (Stub Mode)
No configuration needed. The system works out of the box with heuristic-based corrections.

### Enable LLM Mode

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API key:
```bash
# For OpenAI
OPENAI_API_KEY=your_api_key_here
SPEAKSHARP_LLM_PROVIDER=openai

# OR for Anthropic
ANTHROPIC_API_KEY=your_api_key_here
SPEAKSHARP_LLM_PROVIDER=anthropic
```

3. (Optional) Customize model and parameters:
```bash
SPEAKSHARP_LLM_MODEL=gpt-4o-mini  # or claude-3-5-haiku-20241022
SPEAKSHARP_LLM_TEMP=0.7
SPEAKSHARP_ENABLE_LLM=true
```

4. Install LLM client libraries (if not already installed):
```bash
pip install openai anthropic
```

The system will automatically use the LLM when an API key is configured.

### Test Configuration
```bash
cd app
python config.py
```

## Database Configuration

The system includes full PostgreSQL/Supabase integration for persistence.

### Database Setup

1. **Create a PostgreSQL database** (local or Supabase):
   ```bash
   # Local PostgreSQL
   createdb speaksharp

   # OR use Supabase (recommended for production)
   # Create a new project at https://supabase.com
   ```

2. **Run the schema**:
   ```bash
   psql speaksharp < database/schema.sql

   # OR for Supabase, run the SQL in the SQL Editor
   ```

3. **Set database environment variables**:
   ```bash
   # Option 1: Connection string (recommended)
   export DATABASE_URL="postgresql://user:password@localhost:5432/speaksharp"

   # OR for Supabase
   export SUPABASE_DB_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"

   # Option 2: Individual components
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=speaksharp
   export DB_USER=postgres
   export DB_PASSWORD=yourpassword
   ```

4. **Test database connection**:
   ```bash
   python test_db_integration.py
   ```

### Database Module Usage

The `app/db.py` module provides a clean interface for database operations:

```python
from app.db import get_db
import uuid

db = get_db()

# Create user
user = db.create_user(
    user_id=uuid.uuid4(),
    level="A1",
    native_language="Spanish"
)

# Get due SRS cards
cards = db.get_due_cards(user_id, limit=20)

# Log errors
error = db.log_error(
    user_id=user_id,
    error_type="grammar",
    user_sentence="I go yesterday",
    corrected_sentence="I went yesterday",
    explanation="Use past tense"
)
```

## API Server

The system includes a FastAPI-based REST API for integration with frontends.

### Starting the API Server

```bash
# Make sure database is configured first
source venv/bin/activate
python -m app.api

# OR with uvicorn directly
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Create User
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "level": "A1",
    "native_language": "Spanish",
    "interests": ["travel", "food"]
  }'
```

#### Text Tutoring
```bash
curl -X POST http://localhost:8000/api/tutor/text \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-uuid",
    "text": "I go to school yesterday",
    "context": "Talking about past activities"
  }'
```

#### Get Due SRS Cards
```bash
curl http://localhost:8000/api/srs/due/{user_id}?limit=20
```

#### Submit SRS Review
```bash
curl -X POST http://localhost:8000/api/srs/review \
  -H "Content-Type: application/json" \
  -d '{
    "card_id": "card-uuid",
    "quality": 4,
    "response_time_ms": 3500,
    "correct": true
  }'
```

#### Get User Errors
```bash
curl http://localhost:8000/api/errors/{user_id}?limit=50&unrecycled_only=true
```

#### Voice Tutoring
```bash
curl -X POST http://localhost:8000/api/tutor/voice \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-uuid",
    "audio_path": "/path/to/audio.wav"
  }'
```

See full API documentation at `http://localhost:8000/docs` when the server is running.

## Run End-to-End Demo

```bash
python demo_integration.py
```

The demo executes the complete flow:
1. Onboarding → set user level and goals
2. Daily SRS review → review 3 cards with SM-2
3. Lesson → Articles (A, An, The) with controlled practice
4. Scenario session → café ordering with tutor corrections
5. Error tagging → detect and tag errors in real-time
6. SRS creation → auto-create cards from errors
7. Feedback report → performance summary

## Run Individual Components

Test state machine:
```bash
cd app
python state_machine.py
```

Test tutor agent:
```bash
cd app
python tutor_agent.py
```

Test scenarios:
```bash
cd app
python scenarios.py
```

Test SRS system:
```bash
cd app
python srs_system.py
```

Test lesson system:
```bash
cd app
python lessons.py
```

## Integration Status

The system includes both stub implementations (for testing) and production-ready components:

### ✅ Production-Ready
1. **Database Layer**: Full PostgreSQL/Supabase integration via `app/db.py`
2. **REST API**: FastAPI server with comprehensive endpoints (`app/api.py`)
3. **Schema**: Complete database schema with functions (`database/schema.sql`)
4. **LLM Integration**: Real OpenAI/Anthropic API calls (optional, toggleable)
5. **Voice Integration**: Real ASR/TTS via OpenAI Whisper and TTS-1

### 🔄 Hybrid (Stub + Real)
1. **Tutor Agent**: Works with both stub (heuristic) and real LLM modes
2. **Voice Session**: Works with both stub and real ASR/TTS modes
3. **SRS System**: In-memory for demos, database-backed via API

### 📋 Next Steps for Production
1. **Authentication**: Integrate Supabase Auth for user management
2. **File Storage**: Add audio file storage (Supabase Storage or S3)
3. **Frontend**: Build web/mobile UI consuming the REST API
4. **Deployment**: Deploy API to production (Fly.io, Railway, etc.)
5. **Monitoring**: Add logging, error tracking, and analytics

## Output Format

Tutor responses are strict JSON:
```json
{
  "message": "Tutor's response text",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "Original sentence",
      "corrected_sentence": "Corrected version",
      "explanation": "Brief explanation"
    }
  ],
  "micro_task": "Practice task"
}
```

## Next Steps

- Integrate with real LLM API (OpenAI, Anthropic, etc.)
- Add ASR for speech input
- Connect Supabase database
- Build client UI (web/mobile)
- Add more scenarios beyond MVP (currently 5/5 for MVP, target 30-50 for V1)
- Expand lessons beyond A2 level (currently 11 A1-A2 lessons)
- Implement pronunciation scoring
- Add analytics and progress tracking
- Integrate lesson delivery into state machine daily loop
