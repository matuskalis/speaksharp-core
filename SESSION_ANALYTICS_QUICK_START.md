# Session Analytics - Quick Start Guide

## Installation (One-Time Setup)

```bash
cd /Users/matuskalis/vorex-backend
python3 database/apply_migration_015.py
```

## API Endpoints Summary

Base URL: `https://your-app.railway.app` or `http://localhost:8000`

All endpoints require: `Authorization: Bearer YOUR_JWT_TOKEN`

### 1. Save Session Result

```http
POST /api/sessions/save
```

**Minimal Request:**
```json
{
  "session_type": "conversation",
  "duration_seconds": 300
}
```

**Full Request:**
```json
{
  "session_type": "conversation",
  "duration_seconds": 300,
  "words_spoken": 120,
  "pronunciation_score": 85.5,
  "fluency_score": 78.0,
  "grammar_score": 82.5,
  "topics": ["travel", "hotels"],
  "vocabulary_learned": ["reservation", "available"],
  "areas_to_improve": ["past tense", "prepositions"],
  "metadata": {"scenario_id": "hotel-booking"}
}
```

### 2. Get Session History

```http
GET /api/sessions/history?session_type=conversation&limit=20&offset=0
```

**Parameters:**
- `session_type` (optional): `conversation`, `pronunciation`, or `roleplay`
- `limit` (optional, default: 20, max: 100)
- `offset` (optional, default: 0)

### 3. Get Session Stats

```http
GET /api/sessions/stats?period=week
```

**Parameters:**
- `period` (optional, default: `week`): `week` or `month`

### 4. Get Warmup Content

```http
GET /api/sessions/warmup
```

No parameters required.

## Quick Integration Examples

### React Native / TypeScript

```typescript
// Save session after completion
async function saveSession(sessionData: SessionData) {
  const response = await fetch('/api/sessions/save', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(sessionData)
  });
  return await response.json();
}

// Get weekly stats for dashboard
async function getWeeklyStats() {
  const response = await fetch('/api/sessions/stats?period=week', {
    headers: {
      'Authorization': `Bearer ${authToken}`
    }
  });
  return await response.json();
}

// Get warmup content before session
async function getWarmup() {
  const response = await fetch('/api/sessions/warmup', {
    headers: {
      'Authorization': `Bearer ${authToken}`
    }
  });
  return await response.json();
}
```

### Python

```python
import requests

headers = {'Authorization': f'Bearer {token}'}
base_url = 'https://your-app.railway.app'

# Save session
session_data = {
    'session_type': 'conversation',
    'duration_seconds': 300,
    'pronunciation_score': 85.5,
    'fluency_score': 78.0,
    'grammar_score': 82.5
}
response = requests.post(f'{base_url}/api/sessions/save',
                        json=session_data, headers=headers)

# Get stats
stats = requests.get(f'{base_url}/api/sessions/stats?period=week',
                     headers=headers).json()
```

### cURL

```bash
# Save session
curl -X POST http://localhost:8000/api/sessions/save \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_type": "conversation", "duration_seconds": 300}'

# Get history
curl -X GET "http://localhost:8000/api/sessions/history?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get stats
curl -X GET "http://localhost:8000/api/sessions/stats?period=week" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get warmup
curl -X GET "http://localhost:8000/api/sessions/warmup" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Response Examples

### Save Session Response

```json
{
  "session_result_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "session_type": "conversation",
  "duration_seconds": 300,
  "words_spoken": 120,
  "pronunciation_score": 85.5,
  "fluency_score": 78.0,
  "grammar_score": 82.5,
  "topics": ["travel", "hotels"],
  "vocabulary_learned": ["reservation"],
  "areas_to_improve": ["past tense"],
  "metadata": {},
  "created_at": "2025-12-12T20:30:00Z",
  "updated_at": "2025-12-12T20:30:00Z"
}
```

### Stats Response

```json
{
  "total_sessions": 15,
  "total_duration": 4500,
  "total_words_spoken": 1800,
  "avg_pronunciation": 84.2,
  "avg_fluency": 79.5,
  "avg_grammar": 81.8,
  "sessions_by_type": {
    "conversation": {"count": 8, "avg_duration": 320}
  },
  "improvement_trends": [
    {
      "date": "2025-12-06",
      "pronunciation": 82.0,
      "fluency": 76.5,
      "grammar": 80.0
    }
  ],
  "common_topics": [
    {"topic": "travel", "count": 12}
  ],
  "areas_to_improve": [
    {"area": "past tense usage", "count": 6}
  ]
}
```

### Warmup Response

```json
{
  "focus_areas": ["past tense usage", "prepositions"],
  "vocabulary_review": ["reservation", "available"],
  "last_session_summary": {
    "session_type": "conversation",
    "duration_seconds": 300,
    "pronunciation_score": 85.5,
    "fluency_score": 78.0,
    "grammar_score": 82.5,
    "areas_to_improve": ["past tense"],
    "created_at": "2025-12-12T20:30:00Z"
  }
}
```

## Session Types

Valid `session_type` values:
- `conversation` - General conversation practice
- `pronunciation` - Focused pronunciation drills
- `roleplay` - Scenario-based roleplay sessions

## Common Use Cases

### 1. Complete Session Flow

```typescript
// 1. Get warmup before session starts
const warmup = await getWarmup();
showWarmupExercises(warmup.focus_areas);

// 2. Run the session
const sessionData = await runConversationSession();

// 3. Save session results
await saveSession({
  session_type: 'conversation',
  duration_seconds: sessionData.duration,
  pronunciation_score: sessionData.scores.pronunciation,
  fluency_score: sessionData.scores.fluency,
  grammar_score: sessionData.scores.grammar,
  topics: sessionData.topics,
  vocabulary_learned: sessionData.newWords,
  areas_to_improve: sessionData.weaknesses
});

// 4. Show progress
const stats = await getWeeklyStats();
showProgressDashboard(stats);
```

### 2. Progress Dashboard

```typescript
// Fetch weekly stats
const weeklyStats = await fetch('/api/sessions/stats?period=week', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Display metrics
console.log(`Sessions this week: ${weeklyStats.total_sessions}`);
console.log(`Practice time: ${weeklyStats.total_duration / 60} minutes`);
console.log(`Average score: ${(weeklyStats.avg_pronunciation +
              weeklyStats.avg_fluency + weeklyStats.avg_grammar) / 3}`);

// Show improvement chart
weeklyStats.improvement_trends.forEach(day => {
  console.log(`${day.date}: ${day.pronunciation}% pronunciation`);
});
```

### 3. Session History View

```typescript
// Fetch recent sessions
const history = await fetch('/api/sessions/history?limit=10', {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

// Display list
history.sessions.forEach(session => {
  console.log(`${session.created_at}: ${session.session_type}`);
  console.log(`Duration: ${session.duration_seconds}s`);
  console.log(`Score: ${session.pronunciation_score}%`);
});
```

## Testing

Visit the interactive API docs:

```
http://localhost:8000/docs
```

Or run the test script:

```bash
python3 test_session_analytics.py
```

## Troubleshooting

**401 Unauthorized:**
- Check JWT token is valid
- Ensure header format: `Authorization: Bearer <token>`

**400 Bad Request:**
- Validate session_type is: conversation, pronunciation, or roleplay
- Check scores are between 0-100
- Ensure duration_seconds is positive

**500 Server Error:**
- Check database migration was applied
- Verify DATABASE_URL environment variable
- Check server logs for details

## Documentation

Full documentation: `/Users/matuskalis/vorex-backend/SESSION_ANALYTICS_API.md`

Implementation details: `/Users/matuskalis/vorex-backend/SESSION_ANALYTICS_IMPLEMENTATION.md`
