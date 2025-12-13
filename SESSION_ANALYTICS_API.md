# Session Analytics API

This document describes the session analytics endpoints for the Vorex language learning app. These endpoints enable comprehensive tracking and analysis of user practice sessions.

## Overview

The session analytics system tracks detailed information about conversation, pronunciation, and roleplay sessions, providing:

- Session history and performance tracking
- Aggregated statistics and improvement trends
- Personalized warmup content based on weak areas
- Vocabulary retention analysis

## Database Schema

### session_results Table

```sql
CREATE TABLE session_results (
    session_result_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    session_type VARCHAR(50) NOT NULL,  -- 'conversation', 'pronunciation', 'roleplay'
    duration_seconds INTEGER NOT NULL,
    words_spoken INTEGER DEFAULT 0,
    pronunciation_score FLOAT DEFAULT 0.0,  -- 0-100
    fluency_score FLOAT DEFAULT 0.0,        -- 0-100
    grammar_score FLOAT DEFAULT 0.0,        -- 0-100
    topics TEXT[] DEFAULT '{}',
    vocabulary_learned TEXT[] DEFAULT '{}',
    areas_to_improve TEXT[] DEFAULT '{}',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

All endpoints require JWT authentication via the `Authorization: Bearer <token>` header.

### 1. Save Session Result

**Endpoint:** `POST /api/sessions/save`

**Description:** Save a completed session with detailed analytics data.

**Request Body:**

```json
{
  "session_type": "conversation",
  "duration_seconds": 300,
  "words_spoken": 120,
  "pronunciation_score": 85.5,
  "fluency_score": 78.0,
  "grammar_score": 82.5,
  "topics": ["travel", "booking hotels", "asking for directions"],
  "vocabulary_learned": ["reservation", "available", "amenities"],
  "areas_to_improve": ["past tense usage", "prepositions"],
  "metadata": {
    "scenario_id": "hotel-booking-123",
    "difficulty": "intermediate"
  }
}
```

**Response:**

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
  "topics": ["travel", "booking hotels", "asking for directions"],
  "vocabulary_learned": ["reservation", "available", "amenities"],
  "areas_to_improve": ["past tense usage", "prepositions"],
  "metadata": {
    "scenario_id": "hotel-booking-123",
    "difficulty": "intermediate"
  },
  "created_at": "2025-12-12T20:30:00Z",
  "updated_at": "2025-12-12T20:30:00Z"
}
```

**Validation:**
- `session_type` must be one of: `conversation`, `pronunciation`, `roleplay`
- `duration_seconds` must be >= 0
- `words_spoken` must be >= 0
- All scores must be between 0 and 100

---

### 2. Get Session History

**Endpoint:** `GET /api/sessions/history`

**Description:** Retrieve paginated session history with optional filtering.

**Query Parameters:**
- `session_type` (optional): Filter by session type (`conversation`, `pronunciation`, `roleplay`)
- `limit` (optional, default: 20, max: 100): Number of results per page
- `offset` (optional, default: 0): Pagination offset

**Example Request:**

```
GET /api/sessions/history?session_type=conversation&limit=10&offset=0
```

**Response:**

```json
{
  "sessions": [
    {
      "session_result_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "session_type": "conversation",
      "duration_seconds": 300,
      "words_spoken": 120,
      "pronunciation_score": 85.5,
      "fluency_score": 78.0,
      "grammar_score": 82.5,
      "topics": ["travel", "booking hotels"],
      "vocabulary_learned": ["reservation", "available"],
      "areas_to_improve": ["past tense usage"],
      "metadata": {},
      "created_at": "2025-12-12T20:30:00Z",
      "updated_at": "2025-12-12T20:30:00Z"
    }
    // ... more sessions
  ],
  "total": 10,
  "limit": 10,
  "offset": 0
}
```

---

### 3. Get Session Statistics

**Endpoint:** `GET /api/sessions/stats`

**Description:** Get aggregated statistics for a time period.

**Query Parameters:**
- `period` (optional, default: 'week'): Time period for stats (`week` or `month`)

**Example Request:**

```
GET /api/sessions/stats?period=week
```

**Response:**

```json
{
  "total_sessions": 15,
  "total_duration": 4500,
  "total_words_spoken": 1800,
  "avg_pronunciation": 84.2,
  "avg_fluency": 79.5,
  "avg_grammar": 81.8,
  "sessions_by_type": {
    "conversation": {
      "count": 8,
      "avg_duration": 320
    },
    "pronunciation": {
      "count": 4,
      "avg_duration": 180
    },
    "roleplay": {
      "count": 3,
      "avg_duration": 400
    }
  },
  "improvement_trends": [
    {
      "date": "2025-12-06",
      "pronunciation": 82.0,
      "fluency": 76.5,
      "grammar": 80.0
    },
    {
      "date": "2025-12-07",
      "pronunciation": 83.5,
      "fluency": 78.0,
      "grammar": 81.0
    }
    // ... more daily averages
  ],
  "common_topics": [
    {
      "topic": "travel",
      "count": 12
    },
    {
      "topic": "business",
      "count": 8
    }
    // ... more topics
  ],
  "areas_to_improve": [
    {
      "area": "past tense usage",
      "count": 6
    },
    {
      "area": "prepositions",
      "count": 4
    }
    // ... more areas
  ]
}
```

**Statistics Included:**
- **Total Sessions**: Number of sessions in the period
- **Total Duration**: Sum of all session durations (seconds)
- **Total Words Spoken**: Sum of words spoken across all sessions
- **Average Scores**: Mean pronunciation, fluency, and grammar scores
- **Sessions by Type**: Breakdown of session counts and average duration by type
- **Improvement Trends**: Daily average scores showing progress over time
- **Common Topics**: Most frequently covered topics
- **Areas to Improve**: Most common weak areas across sessions

---

### 4. Get Warmup Content

**Endpoint:** `GET /api/sessions/warmup`

**Description:** Get personalized warmup content based on recent performance.

**Example Request:**

```
GET /api/sessions/warmup
```

**Response:**

```json
{
  "focus_areas": [
    "past tense usage",
    "prepositions",
    "pronunciation of 'th' sounds"
  ],
  "vocabulary_review": [
    "reservation",
    "available",
    "amenities",
    "confirm",
    "deposit"
  ],
  "last_session_summary": {
    "session_type": "conversation",
    "duration_seconds": 300,
    "pronunciation_score": 85.5,
    "fluency_score": 78.0,
    "grammar_score": 82.5,
    "areas_to_improve": ["past tense usage", "prepositions"],
    "created_at": "2025-12-12T20:30:00Z"
  }
}
```

**Purpose:**
This endpoint analyzes:
- The user's last session performance
- Weak areas from the past 7 days
- Vocabulary that appears infrequently (needs reinforcement)

The frontend can use this data to:
- Generate targeted practice exercises
- Create quick quiz questions on weak areas
- Review vocabulary that needs reinforcement
- Show progress from the last session

---

## Usage Examples

### Example 1: Save a Conversation Session

```javascript
// After completing a conversation session
const sessionData = {
  session_type: 'conversation',
  duration_seconds: 420,
  words_spoken: 180,
  pronunciation_score: 88.0,
  fluency_score: 82.5,
  grammar_score: 85.0,
  topics: ['restaurant', 'ordering food', 'dietary restrictions'],
  vocabulary_learned: ['allergic', 'vegetarian', 'spicy', 'recommend'],
  areas_to_improve: ['articles (a/an/the)', 'polite requests'],
  metadata: {
    scenario_id: 'restaurant-ordering',
    ai_tutor_mode: 'patient',
    user_level: 'B1'
  }
};

const response = await fetch('/api/sessions/save', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(sessionData)
});

const result = await response.json();
console.log('Session saved:', result.session_result_id);
```

### Example 2: Display Weekly Progress

```javascript
// Fetch weekly stats for progress dashboard
const response = await fetch('/api/sessions/stats?period=week', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const stats = await response.json();

// Display improvement chart
const improvementChart = stats.improvement_trends.map(day => ({
  date: day.date,
  avgScore: (day.pronunciation + day.fluency + day.grammar) / 3
}));

console.log(`Total practice time: ${stats.total_duration / 60} minutes`);
console.log(`Average pronunciation: ${stats.avg_pronunciation}%`);
console.log(`Top weak area: ${stats.areas_to_improve[0]?.area}`);
```

### Example 3: Generate Warmup Exercise

```javascript
// Before starting a new session, get warmup content
const response = await fetch('/api/sessions/warmup', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const warmup = await response.json();

// Show user their focus areas
console.log('Today\'s focus areas:', warmup.focus_areas);

// Create vocabulary quiz from review list
const quiz = warmup.vocabulary_review.map(word => ({
  question: `Use "${word}" in a sentence`,
  word: word
}));

// Show last session summary
if (warmup.last_session_summary) {
  console.log('Last session type:', warmup.last_session_summary.session_type);
  console.log('Score:', {
    pronunciation: warmup.last_session_summary.pronunciation_score,
    fluency: warmup.last_session_summary.fluency_score,
    grammar: warmup.last_session_summary.grammar_score
  });
}
```

---

## Installation

### 1. Apply the Database Migration

```bash
cd /Users/matuskalis/vorex-backend
python3 database/apply_migration_015.py
```

Or run the migration manually:

```bash
psql $DATABASE_URL -f database/migration_015_session_analytics.sql
```

### 2. Restart the Backend

The new endpoints are automatically available in the FastAPI application.

```bash
# If using Railway, push the changes
git add .
git commit -m "Add session analytics endpoints"
git push

# If running locally
uvicorn app.api2:app --reload
```

---

## API Documentation

After starting the backend, visit the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Look for the "Sessions" tag to see all session analytics endpoints with interactive testing.

---

## Implementation Notes

### Database Methods

All database operations are handled in `/Users/matuskalis/vorex-backend/app/db.py`:

- `save_session_result()` - Insert new session result
- `get_session_history()` - Query session history with filtering/pagination
- `get_session_stats()` - Aggregate statistics with time period
- `get_warmup_content()` - Analyze recent performance for warmup suggestions

### Authentication

All endpoints use JWT token authentication via `verify_token()` dependency. The user ID is extracted from the token's `sub` claim and used for all database queries.

### Performance Considerations

- Indexes are created on `user_id`, `created_at`, and `session_type` for efficient querying
- Array operations (UNNEST) are used for analyzing topics and vocabulary
- Stats queries use COALESCE to handle NULL values gracefully
- Pagination is enforced with max limit of 100 results

---

## Future Enhancements

Potential improvements for the session analytics system:

1. **Skill-Based Analysis**: Link sessions to specific skill nodes for targeted improvement tracking
2. **Comparative Analytics**: Compare user performance to cohort averages
3. **Streak Tracking**: Track consecutive days with sessions
4. **Achievement Integration**: Award achievements based on session milestones
5. **Export Functionality**: Allow users to export their session data
6. **Real-Time Analytics**: WebSocket support for live session tracking
7. **AI-Generated Insights**: Use LLM to generate personalized learning insights

---

## Support

For questions or issues with the session analytics API:

1. Check the API documentation at `/docs`
2. Review the database schema in `database/migration_015_session_analytics.sql`
3. Examine the implementation in `app/db.py` and `app/api2.py`
