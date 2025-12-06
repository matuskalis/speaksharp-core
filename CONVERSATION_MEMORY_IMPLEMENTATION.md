# Conversation Memory Implementation

## Overview

The Voice Tutor now has conversation memory! The tutor can remember past sessions and reference previous conversations, making interactions feel more personal and continuous.

## What Was Implemented

### 1. Database Schema (Migration 008)

**File:** `/Users/matuskalis/vorex-backend/database/migration_008_conversation_memory.sql`

Created `conversation_history` table:
```sql
CREATE TABLE conversation_history (
  conversation_id UUID PRIMARY KEY,
  user_id UUID REFERENCES user_profiles(user_id),
  session_id UUID REFERENCES sessions(session_id),
  turn_number INTEGER NOT NULL,
  user_message TEXT NOT NULL,
  tutor_response TEXT NOT NULL,
  context_type VARCHAR(50),  -- 'scenario', 'lesson', 'free_chat', 'voice_tutor'
  context_id VARCHAR(100),    -- scenario_id, lesson_id, etc.
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'
);
```

**Indexes:**
- `idx_conversation_user_created` - Fast lookup by user and date
- `idx_conversation_session` - Group by session
- `idx_conversation_context` - Filter by context type/ID

**Database Functions:**
- `save_conversation_turn()` - Save a conversation turn
- `get_recent_conversations()` - Fetch recent turns for context
- `get_conversation_context()` - Get summary and statistics
- `get_conversation_by_context()` - Filter by scenario/lesson/etc.
- `clear_conversation_history()` - Clear history (all or before date)

### 2. Database Methods (db.py)

**File:** `/Users/matuskalis/vorex-backend/app/db.py`

Added methods to the `Database` class:

```python
# Save conversation
db.save_conversation_turn(
    user_id=user_id,
    session_id=session_id,
    turn_number=1,
    user_message="I want to learn English",
    tutor_response="Great! Let's start with...",
    context_type="free_chat",
    context_id=None,
    metadata={"error_count": 2}
)

# Get recent conversations
conversations = db.get_recent_conversations(user_id, limit=10)

# Get conversation summary
summary = db.get_conversation_context(user_id, lookback_days=7)

# Filter by context
scenario_convos = db.get_conversation_by_context(
    user_id,
    context_type="scenario",
    context_id="cafe_ordering"
)

# Clear history
deleted = db.clear_conversation_history(user_id)
```

### 3. Tutor Agent with Memory (tutor_agent.py)

**File:** `/Users/matuskalis/vorex-backend/app/tutor_agent.py`

Modified `TutorAgent` class:

**New initialization:**
```python
tutor = TutorAgent(user_id=str(user_id), db=db)
```

**Memory loading:**
```python
tutor.load_conversation_memory()
# Loads last 10 conversation turns
# Loads 7-day conversation summary
```

**Context enrichment:**
The tutor automatically enriches context with:
- `has_conversation_history` - Flag indicating memory exists
- `recent_conversation_count` - Number of recent turns
- `recent_conversation_summary` - Last 5 conversation summaries
- `conversation_summary` - Statistics and patterns

**Updated system prompt:**
Added instructions for the AI tutor to:
- Reference previous sessions naturally
- Track recurring errors
- Build on previous learning
- Make learners feel remembered
- Use phrases like "Last time you mentioned..." and "Remember we practiced..."

### 4. API Endpoints (api2.py)

**File:** `/Users/matuskalis/vorex-backend/app/api2.py`

#### New Endpoints:

**1. GET `/api/tutor/history`**
Get conversation history for authenticated user

Query params:
- `limit` (int, default 20) - Max conversations to return
- `context_type` (str, optional) - Filter by context
- `context_id` (str, optional) - Filter by specific context ID

Response:
```json
{
  "conversations": [
    {
      "conversation_id": "uuid",
      "turn_number": 1,
      "user_message": "I want coffee",
      "tutor_response": "Great! Say 'I'd like a coffee, please'",
      "context_type": "scenario",
      "context_id": "cafe_ordering",
      "created_at": "2025-12-04T10:30:00Z",
      "metadata": {"error_count": 1}
    }
  ],
  "count": 20,
  "summary": {
    "total_conversations": 45,
    "recent_topics": ["scenario", "lesson", "free_chat"],
    "context_summary": {...}
  }
}
```

**2. DELETE `/api/tutor/history`**
Clear conversation history

Query params:
- `before_date` (ISO string, optional) - Only clear before this date

Response:
```json
{
  "status": "success",
  "message": "Cleared 45 conversation turn(s)",
  "deleted_count": 45
}
```

**3. GET `/api/tutor/memory-summary`**
Get summary of what tutor remembers

Query params:
- `lookback_days` (int, default 30) - Days to look back

Response:
```json
{
  "total_conversations": 45,
  "recent_topics": ["scenario", "lesson", "free_chat"],
  "most_active_context": "scenario",
  "last_conversation_date": "2025-12-04T10:30:00Z"
}
```

#### Modified Endpoints:

**POST `/api/tutor/text`**
Now automatically saves conversation turns after processing:
```python
# Initialize tutor with memory
tutor = TutorAgent(user_id=str(user_id), db=db)

# Process user input (automatically loads memory)
response = tutor.process_user_input(text, context=rich_context)

# Save conversation turn
db.save_conversation_turn(
    user_id=user_id,
    session_id=session_id,
    turn_number=turn_number,
    user_message=text,
    tutor_response=response.message,
    context_type=scenario_id or "free_chat",
    context_id=scenario_id
)
```

**POST `/api/tutor/voice`**
Voice tutor also saves conversation turns with audio metadata

## How It Works

### Flow for a Conversation with Memory:

1. **User sends message** → `POST /api/tutor/text`

2. **Tutor initializes with memory:**
   ```python
   tutor = TutorAgent(user_id=user_id, db=db)
   # Automatically loads last 10 conversations
   # Loads 7-day summary statistics
   ```

3. **Context is enriched with memory:**
   ```python
   context = {
       # ... existing context ...
       'has_conversation_history': True,
       'recent_conversation_count': 10,
       'recent_conversation_summary': [
           {'user_said': 'I want coffee', 'tutor_said': '...'},
           # ... last 5 turns
       ],
       'conversation_summary': {
           'total_conversations': 45,
           'most_active_context': 'scenario'
       }
   }
   ```

4. **LLM receives enriched context:**
   The AI tutor now has access to:
   - What the user talked about recently
   - What contexts they've been practicing
   - How many conversations they've had
   - Patterns in their learning

5. **Tutor can reference past:**
   - "Last time you mentioned wanting to order at a cafe..."
   - "Remember we practiced past tense yesterday?"
   - "I notice you're still working on articles - that's totally normal!"
   - "How did that job interview go?"

6. **Conversation is saved:**
   ```python
   db.save_conversation_turn(
       user_id=user_id,
       session_id=session_id,
       turn_number=1,
       user_message="I went to the store yesterday",
       tutor_response="Great use of past tense! Last time...",
       context_type="free_chat",
       metadata={'error_count': 0}
   )
   ```

## Example Usage

### Python Client Example:
```python
import requests

# Get conversation history
response = requests.get(
    "http://localhost:8000/api/tutor/history",
    headers={"Authorization": f"Bearer {token}"},
    params={"limit": 20}
)
history = response.json()

# Get what tutor remembers
response = requests.get(
    "http://localhost:8000/api/tutor/memory-summary",
    headers={"Authorization": f"Bearer {token}"},
    params={"lookback_days": 30}
)
memory = response.json()
print(f"Tutor has {memory['total_conversations']} conversations in memory")

# Clear old conversations (older than 30 days)
from datetime import datetime, timedelta
cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
response = requests.delete(
    "http://localhost:8000/api/tutor/history",
    headers={"Authorization": f"Bearer {token}"},
    params={"before_date": cutoff_date}
)
```

### JavaScript/Frontend Example:
```javascript
// Get conversation history
const history = await fetch('/api/tutor/history?limit=20', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Display what tutor remembers
const memory = await fetch('/api/tutor/memory-summary?lookback_days=30', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

console.log(`Tutor remembers ${memory.total_conversations} conversations`);
console.log(`Most active context: ${memory.most_active_context}`);

// Clear all history
await fetch('/api/tutor/history', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## Database Migration

To apply the migration:

```bash
cd /Users/matuskalis/vorex-backend
source venv/bin/activate
python3 database/apply_migration_008.py
```

Or apply manually:
```bash
psql $DATABASE_URL -f database/migration_008_conversation_memory.sql
```

## Benefits

1. **Personalized Learning:**
   - Tutor remembers what you've practiced
   - References your past topics naturally
   - Tracks your progress over time

2. **Continuity:**
   - Conversations feel connected
   - No repetition of introductions
   - Learning journey tracking

3. **Better Error Correction:**
   - Tutor notices recurring errors
   - Can reference past corrections
   - Builds on previous learning

4. **User Engagement:**
   - "Last time you mentioned..." feels personal
   - Shows genuine interest in learner's life
   - Makes learning feel like a relationship

## Technical Notes

### Performance:
- Indexed queries for fast lookups
- Limited to recent conversations (configurable)
- Metadata stored as JSONB for flexibility

### Privacy:
- Conversations linked to user_id
- Users can clear their own history
- Optional date-based cleanup

### Scalability:
- Efficient indexes on user_id and created_at
- Configurable conversation limits
- Automatic cleanup possible via cron

### Error Handling:
- Graceful degradation if DB unavailable
- Memory loading failures don't crash sessions
- Warnings logged, not errors thrown

## Files Modified/Created

### Created:
1. `/Users/matuskalis/vorex-backend/database/migration_008_conversation_memory.sql` - Database schema
2. `/Users/matuskalis/vorex-backend/database/apply_migration_008.py` - Migration script
3. This documentation file

### Modified:
1. `/Users/matuskalis/vorex-backend/app/db.py` - Added conversation memory methods
2. `/Users/matuskalis/vorex-backend/app/tutor_agent.py` - Added memory loading and context enrichment
3. `/Users/matuskalis/vorex-backend/app/api2.py` - Added endpoints and conversation saving

## Next Steps

To fully utilize conversation memory:

1. **Apply the migration** - Run `apply_migration_008.py`
2. **Test the endpoints** - Use the API to verify functionality
3. **Update frontend** - Add UI to show conversation history
4. **Configure retention** - Set up automatic cleanup if desired
5. **Monitor usage** - Track conversation storage growth

## Testing

Manual testing checklist:

- [ ] Apply migration successfully
- [ ] Create a conversation turn
- [ ] Retrieve conversation history
- [ ] Verify tutor loads memory
- [ ] Test context enrichment
- [ ] Clear conversation history
- [ ] Test filtering by context
- [ ] Verify voice tutor saves conversations
- [ ] Check memory summary endpoint
- [ ] Test with multiple users (isolation)

## Future Enhancements

Possible improvements:

1. **Semantic Search:**
   - Search conversations by topic/keyword
   - Find relevant past discussions

2. **Conversation Summaries:**
   - AI-generated summaries of past sessions
   - "What did we talk about last week?"

3. **Learning Progress Tracking:**
   - Track improvement over time
   - Show before/after comparisons

4. **Smart Context Loading:**
   - Load only relevant past conversations
   - Context-aware memory retrieval

5. **Conversation Insights:**
   - Most discussed topics
   - Common error patterns
   - Learning velocity metrics
