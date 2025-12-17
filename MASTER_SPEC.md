# Vorex (SpeakSharp) - Master Specification Document
# AI-Powered Language Learning Platform

**Version:** 2.0.0
**Last Updated:** December 16, 2024
**Document Purpose:** Complete technical specification for LLM agents working on this codebase

---

# TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Repository Structure](#3-repository-structure)
4. [Backend Specification](#4-backend-specification)
5. [Mobile App Specification](#5-mobile-app-specification)
6. [API Reference](#6-api-reference)
7. [Database Schema](#7-database-schema)
8. [Authentication System](#8-authentication-system)
9. [AI/ML Systems](#9-aiml-systems)
10. [Gamification System](#10-gamification-system)
11. [Voice & Speech Systems](#11-voice--speech-systems)
12. [Design System](#12-design-system)
13. [State Management](#13-state-management)
14. [Deployment & Infrastructure](#14-deployment--infrastructure)
15. [Testing Strategy](#15-testing-strategy)
16. [Common Patterns](#16-common-patterns)
17. [Known Issues & TODOs](#17-known-issues--todos)
18. [Development Guidelines](#18-development-guidelines)

---

# 1. EXECUTIVE SUMMARY

## 1.1 Product Overview

Vorex (also branded as SpeakSharp) is an AI-powered mobile language learning application focused on **spoken English proficiency**. Unlike traditional language apps that focus on reading/writing, Vorex emphasizes:

- **Conversational practice** with AI tutors
- **Real-time pronunciation feedback**
- **Adaptive difficulty** based on CEFR levels (A1-C1)
- **Gamified progression** with XP, achievements, and streaks
- **Spaced Repetition System (SRS)** for vocabulary retention

## 1.2 Target Users

- Non-native English speakers (A1-B2 level)
- Professionals needing business English
- Students preparing for English proficiency tests
- Anyone wanting to improve spoken fluency

## 1.3 Technology Stack

| Layer | Technology |
|-------|------------|
| Mobile App | React Native + Expo (SDK 52) |
| Backend API | Python FastAPI |
| Database | PostgreSQL (via Supabase) |
| Authentication | Supabase Auth (JWT) |
| AI/LLM | OpenAI GPT-4 / Claude |
| Speech-to-Text | OpenAI Whisper |
| Text-to-Speech | OpenAI TTS |
| Hosting (Backend) | Railway |
| Hosting (Web) | Vercel |

## 1.4 Key URLs

- **Backend API:** `https://speaksharp-core-production.up.railway.app`
- **Supabase:** `https://tintxajnzqamsgjeplsk.supabase.co`
- **Mobile Repository:** `github.com/matuskalis/vorex-mobile`
- **Backend Repository:** `github.com/matuskalis/vorex-backend`

---

# 2. ARCHITECTURE OVERVIEW

## 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MOBILE APP (Expo/RN)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │   Home   │ │ Practice │ │ Progress │ │ Profile  │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                  │
│  ┌────┴────────────┴────────────┴────────────┴────┐            │
│  │              API Client (TypeScript)            │            │
│  └─────────────────────┬───────────────────────────┘            │
└────────────────────────┼────────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Tutor   │ │  Speech  │ │   SRS    │ │ Sessions │           │
│  │  Agent   │ │  Client  │ │  Engine  │ │ Manager  │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                  │
│  ┌────┴────────────┴────────────┴────────────┴────┐            │
│  │              Database Layer (PostgreSQL)        │            │
│  └─────────────────────┬───────────────────────────┘            │
└────────────────────────┼────────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Supabase │  │  OpenAI  │  │ External │
    │ (DB/Auth)│  │ (AI/TTS) │  │   APIs   │
    └──────────┘  └──────────┘  └──────────┘
```

## 2.2 Data Flow

### Conversation Flow
```
User speaks → Audio captured → Sent to backend → Whisper ASR →
Text transcript → Tutor Agent (LLM) → Response generated →
Pronunciation analysis → OpenAI TTS → Audio response →
Played to user
```

### Session Save Flow
```
Session ends → Stats calculated → POST /api/sessions/save →
XP awarded → Streak updated → Achievements checked →
Client notified → UI updated
```

---

# 3. REPOSITORY STRUCTURE

## 3.1 Backend Repository (`vorex-backend`)

```
vorex-backend/
├── app/
│   ├── api2.py              # Main FastAPI application (PRIMARY)
│   ├── api.py               # Legacy API (deprecated)
│   ├── auth.py              # JWT authentication & user management
│   ├── config.py            # Environment configuration
│   ├── db.py                # Database connection & utilities
│   ├── models.py            # Pydantic models & enums
│   ├── tutor_agent.py       # AI conversation agent
│   ├── voice_session.py     # Voice conversation handler
│   ├── asr_client.py        # Speech-to-text client
│   ├── tts_client.py        # Text-to-speech client
│   ├── pronunciation.py     # Pronunciation scoring
│   ├── pronunciation_analyzer.py  # Phoneme analysis
│   ├── phoneme_analyzer.py  # IPA phoneme detection
│   ├── skill_unlocks.py     # Gamification & progression
│   ├── exercises.py         # Exercise definitions
│   ├── diagnostic.py        # Placement test engine
│   ├── scenarios.py         # Role-play scenarios
│   ├── lessons.py           # Lesson content
│   ├── conversation_replay.py # Session replay system
│   ├── thinking_engine.py   # CoT reasoning for tutor
│   ├── state_machine.py     # Conversation state tracking
│   └── payments.py          # Subscription handling
├── database/
│   └── apply_migration_*.py # Database migrations
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway deployment config
└── railway.toml             # Railway settings
```

## 3.2 Mobile Repository (`vorex-mobile`)

```
vorex-mobile/
├── app/                     # Expo Router pages
│   ├── (tabs)/              # Tab-based navigation
│   │   ├── index.tsx        # Home screen (Practice tab)
│   │   ├── conversation.tsx # AI conversation screen
│   │   ├── progress.tsx     # Progress/stats screen
│   │   ├── review.tsx       # SRS review screen
│   │   └── profile.tsx      # User profile screen
│   ├── lesson/
│   │   └── [id].tsx         # Dynamic lesson screen
│   ├── role-play/
│   │   ├── index.tsx        # Role-play selection
│   │   └── [id].tsx         # Role-play session
│   ├── placement-test.tsx   # Initial assessment
│   ├── pronunciation-drill.tsx # Pronunciation practice
│   ├── session-summary.tsx  # Post-session summary
│   ├── vocabulary-review.tsx # Vocabulary SRS
│   ├── login.tsx            # Auth screen
│   ├── signup.tsx           # Registration
│   └── _layout.tsx          # Root layout
├── src/
│   ├── components/          # Reusable UI components
│   ├── context/             # React contexts
│   │   ├── AuthContext.tsx  # Authentication state
│   │   ├── LearningContext.tsx # Learning state
│   │   └── GamificationContext.tsx # XP/achievements
│   ├── contexts/            # Additional contexts
│   │   ├── SRSContext.tsx   # Spaced repetition
│   │   └── RecommendationContext.tsx
│   ├── lib/
│   │   ├── api-client.ts    # Backend API wrapper
│   │   └── supabase.ts      # Supabase client
│   ├── data/
│   │   └── achievements.ts  # Achievement definitions
│   ├── theme/               # Design system
│   │   ├── index.ts         # Main exports
│   │   ├── colors.ts        # Color palette
│   │   ├── typography.ts    # Font styles
│   │   ├── spacing.ts       # Layout tokens
│   │   ├── shadows.ts       # Elevation
│   │   └── themes.ts        # Light/dark themes
│   └── utils/
│       ├── animations.ts    # Animation configs
│       ├── gamification.ts  # XP calculations
│       └── spacedRepetition.ts # SM-2 algorithm
├── package.json
├── app.json                 # Expo config
└── tsconfig.json
```

---

# 4. BACKEND SPECIFICATION

## 4.1 Application Entry Point

**File:** `app/api2.py`

The main FastAPI application configures:
- CORS middleware (allows all origins for mobile)
- Database connection lifecycle
- Route registration
- Migrations on startup

```python
# Key configuration
app = FastAPI(title="SpeakSharp Core", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 4.2 Core Modules

### 4.2.1 Authentication (`auth.py`)

- Uses Supabase JWT tokens
- `verify_token()` - validates JWT, returns user_id
- `optional_verify_token()` - allows anonymous access
- `get_or_create_user()` - creates user profile if needed
- `add_user_xp()` - awards XP to user
- `get_user_xp()` - retrieves current XP

### 4.2.2 Tutor Agent (`tutor_agent.py`)

The AI conversation engine:
- Maintains conversation context
- Generates pedagogically-appropriate responses
- Detects grammar/vocabulary errors
- Provides corrections with explanations
- Adapts to user's CEFR level

```python
class TutorAgent:
    def __init__(self, user_level: str = "A1"):
        self.level = user_level
        self.conversation_history = []

    async def respond(self, user_text: str, scenario: Optional[str] = None) -> TutorResponse:
        # 1. Analyze user input for errors
        # 2. Generate contextual response
        # 3. Include micro-tasks when appropriate
        # 4. Track conversation state
```

### 4.2.3 Speech Processing

**ASR Client (`asr_client.py`):**
- Wrapper for OpenAI Whisper API
- Handles audio format conversion
- Returns transcript with word-level timing

**TTS Client (`tts_client.py`):**
- Wrapper for OpenAI TTS API
- Voice options: alloy, echo, fable, onyx, nova, shimmer
- Configurable speech speed

**Pronunciation Analysis (`pronunciation_analyzer.py`):**
- Compares spoken text to expected text
- Calculates word-level accuracy
- Identifies mispronounced phonemes
- Generates targeted feedback

### 4.2.4 Skill Unlocks System (`skill_unlocks.py`)

Gamification progression system:

```python
class SkillCategory(Enum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    PRONUNCIATION = "pronunciation"
    FLUENCY = "fluency"
    LISTENING = "listening"
    CONVERSATION = "conversation"

@dataclass
class SkillProgress:
    skill_id: str
    category: SkillCategory
    level: int
    xp: int
    accuracy: float
    streak_days: int
```

**Skill Definitions:**
- `grammar_tenses` - Verb tense mastery
- `grammar_articles` - Article usage (a/an/the)
- `grammar_prepositions` - Preposition mastery
- `vocabulary_basic` - Core 1000 words
- `vocabulary_professional` - Business vocabulary
- `pronunciation_vowels` - Vowel sounds
- `pronunciation_consonants` - Consonant sounds

---

# 5. MOBILE APP SPECIFICATION

## 5.1 Navigation Structure

Uses Expo Router with file-based routing:

```
(tabs)/           # Bottom tab navigator
  index.tsx       # Practice (default tab)
  conversation.tsx
  progress.tsx
  review.tsx
  profile.tsx

lesson/[id].tsx   # Lesson detail (dynamic route)
role-play/[id].tsx # Role-play session
```

## 5.2 Screen Specifications

### 5.2.1 Home/Practice Screen (`app/(tabs)/index.tsx`)

**Purpose:** Main entry point for practice activities

**Sections:**
1. **Hero Dashboard** - Daily progress ring, streak, XP
2. **Recommended** - AI-suggested activities (horizontal scroll)
3. **Quick Actions** - Conversation, Vocabulary, Pronunciation buttons
4. **Practice Categories** - Filtered lesson grid

**State:**
- `LearningContext` for progress data
- `GamificationContext` for XP/streak
- `apiClient.getRecommendations()` for suggestions

### 5.2.2 Conversation Screen (`app/(tabs)/conversation.tsx`)

**Purpose:** Free-form AI conversation practice

**Features:**
- Real-time voice recording
- Speech-to-text transcription
- AI tutor responses with TTS
- Grammar error highlighting
- Pronunciation feedback

**Flow:**
```
1. User presses microphone button
2. Audio recorded via expo-av
3. Audio sent to /api/speech/transcribe
4. Transcript sent to /api/tutor/text
5. Response received with errors[]
6. Response spoken via /api/speech/synthesize
7. Session saved on completion
```

### 5.2.3 Progress Screen (`app/(tabs)/progress.tsx`)

**Purpose:** Display learning statistics

**Sections:**
1. **Daily Goal Ring** - Minutes practiced today
2. **Weekly Activity** - 7-day breakdown with day indicators
3. **Streak Display** - Current streak from backend
4. **Performance Metrics** - Pronunciation/Fluency/Grammar scores
5. **Monthly Summary** - Total time, sessions, cards learned
6. **CEFR Progress** - Level visualization (A1→C1)

**Data Sources:**
- `apiClient.getSessionStats()`
- `apiClient.getDailyBreakdown(7)`
- `apiClient.getProgressSummary()` (for streak)

### 5.2.4 Profile Screen (`app/(tabs)/profile.tsx`)

**Purpose:** User settings and achievements

**Sections:**
1. **Profile Header** - Avatar, name, level, total XP
2. **Stats Grid** - Level, XP, Streak, Sessions
3. **Achievements Badge Grid** - 6 badges with progress bars
4. **Settings** - Notifications, Voice, Theme, Account

**Achievement Display:**
- Fetches `earned_achievements` from skill profile
- Shows progress bars for locked achievements
- Sorts by progress (closest to unlock first)

### 5.2.5 Review Screen (`app/(tabs)/review.tsx`)

**Purpose:** SRS vocabulary review

**Flow:**
1. Fetch due cards from `/api/srs/due`
2. Present flashcard interface
3. User rates recall quality (0-5)
4. Submit review to `/api/srs/review`
5. Update card interval via SM-2 algorithm

---

# 6. API REFERENCE

## 6.1 Authentication

All authenticated endpoints require:
```
Authorization: Bearer <supabase_jwt_token>
```

## 6.2 User Endpoints

### GET /api/users/me
Returns current user profile.

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "string",
  "display_name": "string | null",
  "current_level": "A1",
  "total_xp": 1250,
  "avatar_url": "string | null"
}
```

### GET /api/progress/summary
Returns progress overview.

**Response:**
```json
{
  "current_level": "A2",
  "total_xp": 2500,
  "streak_days": 7,
  "lessons_completed": 15,
  "weekly_progress": [10, 15, 20, 5, 0, 25, 30]
}
```

## 6.3 Tutor Endpoints

### POST /api/tutor/text
Send text message to AI tutor.

**Request:**
```json
{
  "text": "I go to store yesterday",
  "scenario_id": "coffee_shop",
  "session_id": "uuid (optional)",
  "turn_number": 3
}
```

**Response:**
```json
{
  "message": "I understand! By the way, for past actions we use 'went' instead of 'go'. Would you like me to explain past tense?",
  "errors": [
    {
      "type": "grammar",
      "user_sentence": "I go to store yesterday",
      "corrected_sentence": "I went to the store yesterday",
      "explanation": "Use 'went' (past tense of 'go') for actions in the past. Also, 'the store' needs the article 'the'."
    }
  ],
  "session_id": "uuid"
}
```

## 6.4 Speech Endpoints

### POST /api/speech/transcribe
Transcribe audio to text.

**Request:** `multipart/form-data` with `audio` file

**Response:**
```json
{
  "transcript": "Hello, how are you today?",
  "confidence": 0.95,
  "words": [
    {"word": "Hello", "start": 0.0, "end": 0.5},
    {"word": "how", "start": 0.6, "end": 0.8}
  ]
}
```

### POST /api/speech/synthesize
Convert text to speech audio.

**Request:**
```json
{
  "text": "Hello! Nice to meet you.",
  "voice": "alloy",
  "speed": 1.0
}
```

**Response:** Audio file (audio/mpeg)

### POST /api/speech/analyze
Analyze pronunciation of spoken audio.

**Request:** `multipart/form-data`
- `audio`: Audio file
- `expected_text`: Target sentence

**Response:**
```json
{
  "transcript": "I went to the store",
  "pronunciation_score": 85,
  "fluency_score": 78,
  "mispronounced_words": ["store"],
  "feedback": "Good job! Watch the 'or' sound in 'store'."
}
```

### POST /api/speech/analyze-pronunciation
Detailed phoneme-level analysis.

**Response:**
```json
{
  "transcript": "The weather is nice",
  "overall_score": 82,
  "pronunciation_score": 85,
  "fluency_score": 80,
  "phoneme_analysis": [
    {
      "phoneme": "th",
      "word": "The",
      "status": "close",
      "confidence": 0.75,
      "expected_ipa": "ð",
      "actual_ipa": "d"
    }
  ],
  "word_scores": [
    {"word": "weather", "score": 90, "issues": []},
    {"word": "nice", "score": 75, "issues": ["final_s"]}
  ],
  "feedback": "Work on the 'th' sound. Try placing your tongue between your teeth."
}
```

## 6.5 SRS Endpoints

### GET /api/srs/due?limit=20
Get cards due for review.

**Response:**
```json
{
  "cards": [
    {
      "card_id": "uuid",
      "front": "accomplish",
      "back": "to succeed in doing something",
      "card_type": "vocabulary",
      "ease_factor": 2.5,
      "interval_days": 3,
      "next_review": "2024-12-16T10:00:00Z"
    }
  ],
  "total_due": 15
}
```

### POST /api/srs/review
Submit a card review.

**Request:**
```json
{
  "card_id": "uuid",
  "quality": 4,
  "response_time_ms": 2500
}
```

**Response:**
```json
{
  "success": true,
  "card": {...},
  "next_review": "2024-12-23T10:00:00Z",
  "interval_days": 7
}
```

### GET /api/srs/stats
Get SRS statistics.

**Response:**
```json
{
  "total_cards": 150,
  "cards_due_today": 12,
  "cards_learned": 85,
  "cards_learning": 30,
  "average_retention": 87.5,
  "streak_days": 7
}
```

## 6.6 Session Endpoints

### POST /api/sessions/save
Save a practice session.

**Request:**
```json
{
  "scenario_id": "coffee_shop",
  "duration_seconds": 300,
  "turns_count": 10,
  "pronunciation_score": 85,
  "fluency_score": 78,
  "grammar_errors": [
    {
      "type": "tense",
      "user_sentence": "I go yesterday",
      "corrected_sentence": "I went yesterday",
      "explanation": "Past tense required"
    }
  ],
  "completed": true
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid",
  "xp_earned": 50,
  "streak_updated": true
}
```

### GET /api/sessions/stats?period=week
Get aggregated session statistics.

**Response:**
```json
{
  "total_sessions": 25,
  "total_minutes": 450,
  "total_xp": 1250,
  "average_pronunciation": 82,
  "average_fluency": 78,
  "most_practiced_scenario": "coffee_shop",
  "sessions_by_day": {
    "2024-12-10": 3,
    "2024-12-11": 2
  },
  "pronunciation_trend": [75, 78, 80, 82, 85],
  "grammar_improvement": 12
}
```

### GET /api/sessions/daily-breakdown?days=7
Get daily practice breakdown.

**Response:**
```json
{
  "days": [
    {"date": "2024-12-16", "sessions": 2, "minutes": 45, "xp": 120},
    {"date": "2024-12-15", "sessions": 1, "minutes": 20, "xp": 50}
  ],
  "totals": {
    "sessions": 12,
    "minutes": 240,
    "xp": 650
  }
}
```

## 6.7 Skill Endpoints

### GET /api/skills/profile
Get user's complete skill profile.

**Response:**
```json
{
  "total_xp": 2500,
  "overall_level": 5,
  "skills": {
    "grammar_tenses": {
      "level": 3,
      "xp": 280,
      "p_learned": 0.65
    },
    "pronunciation_vowels": {
      "level": 2,
      "xp": 150,
      "p_learned": 0.45
    }
  },
  "unlocked_content": ["scenario_restaurant", "lesson_conditionals"],
  "earned_achievements": ["first_conversation", "streak_3", "words_100"]
}
```

## 6.8 Bonus Endpoints

### GET /api/bonuses/summary
Get daily bonus status.

**Response:**
```json
{
  "total_bonus_xp_today": 75,
  "bonuses_claimed": [
    {"type": "login", "xp": 25, "multiplier": 1.0}
  ],
  "available_bonuses": {
    "login_bonus": {"available": false, "xp": 25},
    "streak_bonus": {"active": true, "multiplier": 1.5, "streak_days": 7},
    "weekend_bonus": {"active": true, "multiplier": 1.5},
    "event_bonus": {"active": false, "name": null, "multiplier": 1.0}
  },
  "current_multiplier": 2.25
}
```

### POST /api/bonuses/claim-login
Claim daily login bonus.

**Response:**
```json
{
  "success": true,
  "xp_earned": 25,
  "message": "Daily login bonus claimed!"
}
```

## 6.9 Learning Endpoints

### GET /api/learn/guided
Get guided learning path.

**Response:**
```json
{
  "units": [
    {
      "unit_id": "uuid",
      "unit_number": 1,
      "title": "Greetings & Introductions",
      "description": "Learn to introduce yourself",
      "level": "A1",
      "is_locked": false,
      "lessons": [
        {
          "lesson_id": "uuid",
          "lesson_number": 1,
          "title": "Hello & Goodbye",
          "is_locked": false,
          "completed": true
        }
      ]
    }
  ]
}
```

### GET /api/learn/lesson/{lesson_id}
Get lesson content.

**Response:**
```json
{
  "lesson_id": "uuid",
  "title": "Verb Tenses: Present Simple",
  "exercises": [
    {
      "id": "ex_001",
      "type": "fill_blank",
      "content": {
        "sentence": "She ___ to work every day.",
        "options": ["go", "goes", "going"],
        "correct": "goes"
      }
    }
  ]
}
```

### POST /api/learn/lesson/complete
Submit lesson completion.

**Request:**
```json
{
  "lesson_id": "uuid",
  "score": 85,
  "time_spent_seconds": 300,
  "mistakes_count": 3
}
```

## 6.10 Recommendation Endpoints

### GET /api/recommendations
Get AI-powered recommendations.

**Response:**
```json
{
  "recommendations": [
    {
      "lesson_id": "uuid",
      "type": "lesson",
      "title": "Past Tense Practice",
      "description": "Based on recent errors, practice past tense",
      "reason": "You made 3 past tense errors today",
      "difficulty": "medium",
      "estimated_minutes": 10,
      "priority": 1
    }
  ],
  "reasoning": "Focus on grammar patterns where errors occurred"
}
```

### GET /api/practice/scenarios
Get practice scenarios with progress.

**Response:**
```json
{
  "scenarios": [
    {
      "scenario_id": "coffee_shop",
      "title": "Ordering Coffee",
      "description": "Practice ordering at a cafe",
      "difficulty": "beginner",
      "category": "daily_life",
      "estimated_minutes": 5,
      "times_practiced": 3,
      "last_practiced": "2024-12-15T10:00:00Z",
      "best_pronunciation_score": 88,
      "completed": true
    }
  ]
}
```

---

# 7. DATABASE SCHEMA

## 7.1 Core Tables

### user_profiles
```sql
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY,
    level VARCHAR(10) DEFAULT 'A1',
    native_language VARCHAR(50),
    goals JSONB,
    interests TEXT[],
    daily_time_goal INTEGER DEFAULT 15,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    full_name VARCHAR(255),
    voice_preferences JSONB DEFAULT '{"voice": "alloy", "speech_speed": 1.0}',
    trial_start_date TIMESTAMP,
    trial_end_date TIMESTAMP,
    subscription_status VARCHAR(50),
    subscription_tier VARCHAR(50),
    is_tester BOOLEAN DEFAULT FALSE,
    total_xp INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### session_results
```sql
CREATE TABLE session_results (
    session_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(user_id),
    session_type VARCHAR(50) NOT NULL,
    duration_seconds INTEGER NOT NULL,
    words_spoken INTEGER DEFAULT 0,
    pronunciation_score FLOAT,
    fluency_score FLOAT,
    grammar_score FLOAT,
    topics TEXT[],
    vocabulary_learned TEXT[],
    areas_to_improve TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### srs_cards
```sql
CREATE TABLE srs_cards (
    card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(user_id),
    card_type VARCHAR(50) NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    level VARCHAR(10) DEFAULT 'A1',
    source VARCHAR(50) DEFAULT 'lesson',
    difficulty FLOAT DEFAULT 0.5,
    next_review_date TIMESTAMP,
    interval_days INTEGER DEFAULT 1,
    ease_factor FLOAT DEFAULT 2.5,
    review_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### srs_reviews
```sql
CREATE TABLE srs_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID REFERENCES srs_cards(card_id),
    user_id UUID REFERENCES user_profiles(user_id),
    quality INTEGER CHECK (quality >= 0 AND quality <= 5),
    response_time_ms INTEGER,
    correct BOOLEAN,
    new_interval_days INTEGER,
    new_ease_factor FLOAT,
    reviewed_at TIMESTAMP DEFAULT NOW()
);
```

### skill_nodes
```sql
CREATE TABLE skill_nodes (
    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(user_id),
    skill_category VARCHAR(50) NOT NULL,
    skill_key VARCHAR(100) NOT NULL,
    mastery_score FLOAT DEFAULT 0.0,
    confidence FLOAT DEFAULT 0.0,
    last_practiced TIMESTAMP,
    practice_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    UNIQUE(user_id, skill_key)
);
```

## 7.2 Learning Path Tables

### learning_units
```sql
CREATE TABLE learning_units (
    unit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_number INTEGER NOT NULL,
    level VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    color VARCHAR(20),
    order_index INTEGER NOT NULL,
    is_locked BOOLEAN DEFAULT TRUE,
    prerequisite_unit_id UUID REFERENCES learning_units(unit_id),
    estimated_time_minutes INTEGER,
    metadata JSONB,
    UNIQUE(level, unit_number)
);
```

### learning_lessons
```sql
CREATE TABLE learning_lessons (
    lesson_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID REFERENCES learning_units(unit_id),
    lesson_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    lesson_type VARCHAR(50) DEFAULT 'standard',
    order_index INTEGER NOT NULL,
    xp_reward INTEGER DEFAULT 10,
    is_locked BOOLEAN DEFAULT TRUE,
    prerequisite_lesson_id UUID REFERENCES learning_lessons(lesson_id),
    estimated_time_minutes INTEGER DEFAULT 5,
    content JSONB,
    metadata JSONB,
    UNIQUE(unit_id, lesson_number)
);
```

### user_lesson_progress
```sql
CREATE TABLE user_lesson_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(user_id),
    lesson_id UUID REFERENCES learning_lessons(lesson_id),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE,
    score INTEGER,
    mistakes_count INTEGER DEFAULT 0,
    time_spent_seconds INTEGER DEFAULT 0,
    exercises_completed INTEGER DEFAULT 0,
    total_exercises INTEGER,
    current_exercise_index INTEGER DEFAULT 0,
    metadata JSONB,
    UNIQUE(user_id, lesson_id)
);
```

## 7.3 Gamification Tables

### daily_challenge_progress
```sql
CREATE TABLE daily_challenge_progress (
    user_id UUID REFERENCES user_profiles(user_id),
    challenge_date DATE NOT NULL,
    challenge_type VARCHAR(50) NOT NULL,
    progress INTEGER DEFAULT 0,
    goal INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, challenge_date)
);
```

### daily_bonus_claims
```sql
CREATE TABLE daily_bonus_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(user_id),
    bonus_type VARCHAR(30) NOT NULL,
    bonus_xp INTEGER NOT NULL,
    multiplier DECIMAL(3,2) DEFAULT 1.0,
    claimed_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, bonus_type, claimed_date)
);
```

### xp_multiplier_events
```sql
CREATE TABLE xp_multiplier_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    multiplier DECIMAL(3,2) NOT NULL DEFAULT 2.0,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

# 8. AUTHENTICATION SYSTEM

## 8.1 Overview

Authentication uses **Supabase Auth** with JWT tokens:

1. User signs up/logs in via Supabase client
2. Supabase returns JWT access token
3. Mobile app includes token in `Authorization` header
4. Backend validates token via Supabase JWT verification

## 8.2 Mobile Auth Flow

**File:** `src/context/AuthContext.tsx`

```typescript
// Sign up
const { data, error } = await supabase.auth.signUp({
  email,
  password,
});

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
});

// Get current session
const { data: { session } } = await supabase.auth.getSession();

// Token for API calls
const token = session?.access_token;
```

## 8.3 Backend Token Verification

**File:** `app/auth.py`

```python
async def verify_token(
    authorization: str = Header(None)
) -> str:
    """Verify Supabase JWT and return user_id."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization token")

    token = authorization.replace("Bearer ", "")

    # Decode JWT (Supabase uses HS256)
    payload = jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated"
    )

    return payload["sub"]  # user_id
```

## 8.4 User Profile Creation

On first API call, user profile is automatically created:

```python
async def get_or_create_user(user_id: str, db: Database) -> dict:
    """Get existing user or create new profile."""
    profile = await db.get_user_profile(user_id)

    if not profile:
        profile = await db.create_user_profile(
            user_id=user_id,
            level="A1",
            native_language="unknown"
        )

    return profile
```

---

# 9. AI/ML SYSTEMS

## 9.1 Tutor Agent Architecture

The AI tutor uses a multi-stage pipeline:

```
User Input
    ↓
┌─────────────────┐
│ Error Detection │ ← Grammar/vocab/fluency analysis
└────────┬────────┘
         ↓
┌─────────────────┐
│ Context Builder │ ← User level, history, scenario
└────────┬────────┘
         ↓
┌─────────────────┐
│   LLM Prompt    │ ← GPT-4 / Claude
└────────┬────────┘
         ↓
┌─────────────────┐
│ Response Parser │ ← Extract message, errors, tasks
└────────┬────────┘
         ↓
Tutor Response
```

## 9.2 LLM Prompt Template

```python
TUTOR_SYSTEM_PROMPT = """
You are an English language tutor for a {level} level student.

Guidelines:
1. Respond naturally as if in conversation
2. Match your vocabulary to the student's level
3. When you notice errors, correct them gently
4. Provide brief explanations for corrections
5. Encourage the student with positive feedback
6. If in a scenario, stay in character

Current scenario: {scenario_description}
"""
```

## 9.3 Error Detection Categories

| Error Type | Examples | Detection Method |
|------------|----------|------------------|
| Grammar | Tense errors, subject-verb agreement | Rule-based + LLM |
| Vocabulary | Word choice, collocations | LLM semantic analysis |
| Fluency | Fragmented sentences, filler words | Pattern matching |
| Pronunciation | (From audio analysis) | Whisper + custom scoring |

## 9.4 Pronunciation Scoring Algorithm

```python
def calculate_pronunciation_score(
    expected_text: str,
    transcript: str,
    word_timings: List[WordTiming]
) -> PronunciationResult:
    """
    Calculate pronunciation score based on:
    1. Word accuracy (Levenshtein distance)
    2. Timing consistency
    3. Confidence scores from ASR
    """
    word_scores = []

    for expected, spoken in zip_words(expected_text, transcript):
        similarity = compute_similarity(expected, spoken)
        timing_score = evaluate_timing(word_timings, spoken)

        word_scores.append({
            "word": expected,
            "score": (similarity * 0.7 + timing_score * 0.3) * 100,
            "issues": identify_issues(expected, spoken)
        })

    return PronunciationResult(
        overall_score=mean([ws["score"] for ws in word_scores]),
        word_scores=word_scores,
        feedback=generate_feedback(word_scores)
    )
```

---

# 10. GAMIFICATION SYSTEM

## 10.1 XP System

### XP Rewards

| Action | XP Earned |
|--------|-----------|
| Complete lesson | 50 |
| Pronunciation drill | 10 |
| Start conversation | 25 |
| Complete conversation | 100 |
| Meet daily goal | 50 |
| Perfect answer | 5 |
| Per streak day | 10 |

### Level Calculation

```typescript
// XP needed for each level: level^2 * 100
// Level 1: 100 XP
// Level 2: 400 XP
// Level 5: 2,500 XP
// Level 10: 10,000 XP

function calculateLevel(xp: number): number {
  return Math.floor(Math.sqrt(xp / 100));
}

function xpForNextLevel(currentLevel: number): number {
  return (currentLevel + 1) ** 2 * 100;
}
```

## 10.2 Achievement System

### Achievement Categories

| Category | Examples |
|----------|----------|
| Milestone | First Conversation, First Lesson |
| Streak | 3-Day, 7-Day, 30-Day, 100-Day |
| Practice | Words spoken milestones |
| Time | Practice hours |
| Mastery | Perfect pronunciation, all role-plays |
| Level | Level 5, 10, 25, 50 |

### Achievement Definition (Mobile)

```typescript
interface Achievement {
  id: string;
  title: string;
  description: string;
  category: 'milestone' | 'streak' | 'practice' | 'mastery' | 'time';
  icon: string;
  xpReward: number;
  condition: {
    type: 'streak' | 'level' | 'words_spoken' | 'practice_time' | ...;
    value?: number;
  };
}
```

### Achievement Progress Calculation

```typescript
const getAchievementProgress = (achievement: Achievement): number => {
  const { type, value } = achievement.condition;

  switch (type) {
    case 'streak':
      return streakDays / (value ?? 1);
    case 'level':
      return currentLevel / (value ?? 1);
    case 'practice_time':
      return totalMinutes / (value ?? 1);
    case 'lessons_completed':
      return sessionsCompleted / (value ?? 1);
    case 'words_spoken':
      return wordsSpoken / (value ?? 1);
    default:
      return 0;
  }
};
```

## 10.3 Streak System

Streaks track consecutive days of practice:

```python
def update_streak(user_id: str, db: Database):
    """Update user's streak after a practice session."""
    last_session = db.get_last_session(user_id)
    today = date.today()

    if last_session is None:
        return set_streak(user_id, 1)

    last_date = last_session.created_at.date()

    if last_date == today:
        return  # Already practiced today
    elif last_date == today - timedelta(days=1):
        return increment_streak(user_id)  # Consecutive day
    else:
        return reset_streak(user_id)  # Streak broken
```

## 10.4 Daily Bonuses

| Bonus Type | XP Amount | Condition |
|------------|-----------|-----------|
| Login Bonus | 25 | First action of the day |
| Streak Bonus | 10 * streak_days | Maintain streak |
| Weekend Bonus | 1.5x multiplier | Saturday/Sunday |
| Event Bonus | Variable | Special events |

---

# 11. VOICE & SPEECH SYSTEMS

## 11.1 Audio Recording (Mobile)

Uses `expo-av` for audio capture:

```typescript
const [recording, setRecording] = useState<Audio.Recording>();

async function startRecording() {
  await Audio.requestPermissionsAsync();
  await Audio.setAudioModeAsync({
    allowsRecordingIOS: true,
    playsInSilentModeIOS: true,
  });

  const { recording } = await Audio.Recording.createAsync(
    Audio.RecordingOptionsPresets.HIGH_QUALITY
  );
  setRecording(recording);
}

async function stopRecording() {
  await recording.stopAndUnloadAsync();
  const uri = recording.getURI();
  // Send to backend for transcription
}
```

## 11.2 Speech-to-Text (Backend)

Uses OpenAI Whisper API:

```python
class ASRClient:
    async def transcribe(self, audio_bytes: bytes) -> ASRResult:
        response = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.m4a", audio_bytes),
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

        return ASRResult(
            text=response.text,
            words=[
                WordTiming(
                    word=w["word"],
                    start=w["start"],
                    end=w["end"]
                )
                for w in response.words
            ]
        )
```

## 11.3 Text-to-Speech (Backend)

Uses OpenAI TTS API:

```python
class TTSClient:
    async def synthesize(
        self,
        text: str,
        voice: str = "alloy",
        speed: float = 1.0
    ) -> bytes:
        response = await openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed
        )

        return response.content  # MP3 audio bytes
```

## 11.4 Audio Playback (Mobile)

```typescript
async function playAudio(audioUri: string) {
  const { sound } = await Audio.Sound.createAsync(
    { uri: audioUri },
    { shouldPlay: true }
  );

  sound.setOnPlaybackStatusUpdate((status) => {
    if (status.didJustFinish) {
      sound.unloadAsync();
    }
  });
}
```

---

# 12. DESIGN SYSTEM

## 12.1 Color Palette

```typescript
export const colors = {
  // Primary brand color (indigo)
  primary: {
    50: '#eef2ff',
    100: '#e0e7ff',
    200: '#c7d2fe',
    300: '#a5b4fc',
    400: '#818cf8',
    500: '#6366f1',  // Main
    600: '#4f46e5',
    700: '#4338ca',
    800: '#3730a3',
    900: '#312e81',
  },

  // Accent (amber/gold)
  accent: {
    500: '#fbbf24',
  },

  // Success (green)
  success: {
    500: '#22c55e',
  },

  // Error (red)
  error: {
    500: '#ef4444',
  },

  // Neutral (grays)
  neutral: {
    0: '#ffffff',
    50: '#fafafa',
    100: '#f4f4f5',
    500: '#71717a',
    700: '#3f3f46',
    800: '#27272a',
    900: '#18181b',
    950: '#09090b',
  },

  // Text colors
  text: {
    primary: '#ffffff',
    secondary: '#a3a3a3',
    muted: '#737373',
  },
};
```

## 12.2 Typography

```typescript
export const textStyles = {
  // Headings
  h1: { fontSize: 32, fontWeight: '700', lineHeight: 40 },
  h2: { fontSize: 24, fontWeight: '700', lineHeight: 32 },
  h3: { fontSize: 20, fontWeight: '600', lineHeight: 28 },

  // Body text
  bodyLarge: { fontSize: 18, fontWeight: '400', lineHeight: 28 },
  body: { fontSize: 16, fontWeight: '400', lineHeight: 24 },
  bodySmall: { fontSize: 14, fontWeight: '400', lineHeight: 20 },

  // Labels
  labelLarge: { fontSize: 14, fontWeight: '600', lineHeight: 20 },
  labelMedium: { fontSize: 12, fontWeight: '600', lineHeight: 16 },
  labelSmall: { fontSize: 11, fontWeight: '600', lineHeight: 16 },

  // Special
  caption: { fontSize: 12, fontWeight: '400', lineHeight: 16 },
  overline: { fontSize: 10, fontWeight: '600', lineHeight: 16, textTransform: 'uppercase' },
};
```

## 12.3 Spacing Scale

```typescript
export const spacing = {
  0.5: 2,
  1: 4,
  1.5: 6,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  8: 32,
  10: 40,
  12: 48,
  16: 64,
};

export const layout = {
  screenPadding: 16,
  cardPadding: 16,
  radius: {
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    full: 9999,
  },
};
```

## 12.4 Dark Theme

```typescript
export const darkTheme = {
  colors: {
    background: {
      primary: '#0a0a0a',   // Main background
      secondary: '#171717', // Slightly lighter
      card: '#1a1a1a',      // Card surfaces
      elevated: '#262626',  // Elevated surfaces
    },
    border: {
      default: '#262626',
      light: '#404040',
    },
    text: {
      primary: '#ffffff',
      secondary: '#a3a3a3',
      muted: '#737373',
    },
  },
};
```

## 12.5 Component Patterns

### Card Style
```typescript
const cardStyle = {
  backgroundColor: darkTheme.colors.background.card,
  borderRadius: layout.radius.xl,
  padding: spacing[5],
  borderWidth: 1,
  borderColor: darkTheme.colors.border.default,
};
```

### Button Variants
```typescript
// Primary button
const primaryButton = {
  backgroundColor: colors.primary[500],
  paddingVertical: spacing[3],
  paddingHorizontal: spacing[6],
  borderRadius: layout.radius.full,
};

// Secondary button
const secondaryButton = {
  backgroundColor: 'transparent',
  borderWidth: 1,
  borderColor: colors.primary[500],
  paddingVertical: spacing[3],
  paddingHorizontal: spacing[6],
  borderRadius: layout.radius.full,
};
```

---

# 13. STATE MANAGEMENT

## 13.1 Context Architecture

```
App
├── AuthProvider (authentication state)
│   ├── LearningProvider (learning progress)
│   │   ├── GamificationProvider (XP, achievements)
│   │   │   ├── SRSProvider (spaced repetition)
│   │   │   │   └── Screen Components
```

## 13.2 AuthContext

```typescript
interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
  error: string | null;
}

interface AuthContextValue extends AuthState {
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}
```

## 13.3 LearningContext

```typescript
interface LearningState {
  cefrLevel: string;
  dailyGoalMinutes: number;
  todayStats: {
    speakingMinutes: number;
    lessonsCompleted: number;
  };
  weeklyStats: {
    speakingMinutes: number;
    pronunciationScore: number;
    fluencyScore: number;
    grammarScore: number;
  };
}

interface LearningActions {
  updateLevel: (level: string) => void;
  recordPractice: (minutes: number) => void;
  completeLesson: (lessonId: string, score: number) => void;
}
```

## 13.4 GamificationContext

```typescript
interface GamificationState {
  totalXP: number;
  level: number;
  streakDays: number;
  longestStreak: number;
  achievements: string[];
  dailyGoalProgress: number;
}

interface GamificationActions {
  addXP: (amount: number, source: string) => void;
  checkAchievements: () => void;
  updateStreak: () => void;
}
```

## 13.5 SRSContext

```typescript
interface SRSState {
  dueCards: SRSCard[];
  totalCards: number;
  cardsLearned: number;
  cardsLearning: number;
  averageRetention: number;
  loading: boolean;
}

interface SRSActions {
  fetchDueCards: () => Promise<void>;
  submitReview: (cardId: string, quality: number) => Promise<void>;
  createCard: (front: string, back: string, type: string) => Promise<void>;
}
```

---

# 14. DEPLOYMENT & INFRASTRUCTURE

## 14.1 Backend (Railway)

**Configuration:** `railway.toml`
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.api2:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
```

**Environment Variables:**
```
DATABASE_URL=postgresql://...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=xxx
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 14.2 Database (Supabase)

- **Project:** tintxajnzqamsgjeplsk
- **Region:** us-east-1
- **PostgreSQL Version:** 15

**Connection:**
```
Host: db.tintxajnzqamsgjeplsk.supabase.co
Port: 5432
Database: postgres
```

## 14.3 Mobile App (Expo)

**Build Commands:**
```bash
# Development
npx expo start --clear

# iOS Simulator
npx expo start --ios --clear

# Production build
eas build --platform ios
eas build --platform android

# OTA update
eas update --branch production
```

**Environment:**
```typescript
// In app code, use Expo constants
const API_URL = 'https://speaksharp-core-production.up.railway.app';
const SUPABASE_URL = 'https://tintxajnzqamsgjeplsk.supabase.co';
```

---

# 15. TESTING STRATEGY

## 15.1 Backend Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific module
pytest tests/test_tutor.py -v
```

**Test Structure:**
```
tests/
├── test_api.py          # API endpoint tests
├── test_tutor.py        # Tutor agent tests
├── test_srs.py          # SRS algorithm tests
├── test_pronunciation.py # Pronunciation scoring
└── conftest.py          # Fixtures
```

## 15.2 Mobile Testing

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# E2E tests (Detox)
detox test --configuration ios.sim.debug
```

## 15.3 Test User Accounts

For development, use `is_tester: true` accounts:
- Skip trial limitations
- Bypass payment checks
- Enable debug logging

---

# 16. COMMON PATTERNS

## 16.1 API Error Handling (Mobile)

```typescript
try {
  const result = await apiClient.someEndpoint();
  // Handle success
} catch (error) {
  if (error.message.includes('401')) {
    // Auth error - redirect to login
  } else if (error.message.includes('404')) {
    // Not found - show appropriate message
  } else {
    // Generic error
    Alert.alert('Error', error.message);
  }
}
```

## 16.2 Loading States (Mobile)

```typescript
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

const fetchData = useCallback(async () => {
  try {
    setError(null);
    const data = await apiClient.getData();
    setData(data);
  } catch (err) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
}, []);

useEffect(() => {
  fetchData();
}, [fetchData]);
```

## 16.3 Pull-to-Refresh (Mobile)

```typescript
const [isRefreshing, setIsRefreshing] = useState(false);

const handleRefresh = useCallback(async () => {
  setIsRefreshing(true);
  await fetchData();
  setIsRefreshing(false);
}, [fetchData]);

<ScrollView
  refreshControl={
    <RefreshControl
      refreshing={isRefreshing}
      onRefresh={handleRefresh}
      tintColor={colors.primary[400]}
    />
  }
>
```

## 16.4 Null Safety Pattern

```typescript
// Use nullish coalescing for defaults
const streakDays = progressSummary?.streak_days ?? gamificationState.streakDays ?? 0;

// Use optional chaining for deep access
const lastSessionDate = sessionHistory?.[0]?.created_at;

// Guard against NaN
const displayScore = isNaN(score) ? 0 : Math.round(score);

// Clamp values to valid range
const progressPercent = Math.min(Math.max(progress, 0), 100);
```

## 16.5 Backend Route Pattern

```python
@app.post("/api/resource")
async def create_resource(
    request: CreateResourceRequest,
    user_id: str = Depends(verify_token),
    db: Database = Depends(get_db)
):
    try:
        result = await db.create_resource(user_id, request.dict())
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        raise HTTPException(500, "Internal server error")
```

---

# 17. KNOWN ISSUES & TODOS

## 17.1 Current Limitations

| Issue | Status | Priority |
|-------|--------|----------|
| SRS integration incomplete | In Progress | High |
| Phoneme-level analysis limited | Planned | Medium |
| Offline mode not implemented | Planned | Low |
| Push notifications partial | In Progress | Medium |

## 17.2 Technical Debt

1. **Legacy API (`api.py`)** - Should be fully migrated to `api2.py`
2. **Exercise XP cache** - In-memory, needs Redis for scale
3. **Audio format handling** - Needs standardization (m4a/mp3/wav)
4. **Error messages** - Not fully localized

## 17.3 Future Enhancements

- [ ] Real-time voice conversation (WebSocket)
- [ ] Social features (friends, challenges)
- [ ] Native speaker recordings
- [ ] Custom lesson builder
- [ ] Progress export/analytics

---

# 18. DEVELOPMENT GUIDELINES

## 18.1 Code Style

### TypeScript/React Native
- Use functional components with hooks
- Prefer `const` over `let`
- Use descriptive variable names
- Extract reusable logic to custom hooks
- Use TypeScript strict mode

### Python/FastAPI
- Follow PEP 8
- Use type hints everywhere
- Document public functions with docstrings
- Use Pydantic for request/response models
- Prefer async functions for I/O

## 18.2 Git Workflow

```bash
# Feature branch
git checkout -b feature/description

# Commit with descriptive message
git commit -m "feat: Add pronunciation feedback component

- Implement phoneme-level scoring display
- Add visual indicators for correct/incorrect sounds
- Integrate with existing feedback modal

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push and create PR
git push origin feature/description
```

## 18.3 PR Checklist

- [ ] Code follows project style guidelines
- [ ] No console.log/print statements in production code
- [ ] API changes are backward compatible
- [ ] New endpoints have authentication
- [ ] Error cases are handled
- [ ] Loading states are implemented
- [ ] Works on both iOS and Android

## 18.4 File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `ProgressRing.tsx` |
| Contexts | PascalCase + Context | `AuthContext.tsx` |
| Utilities | camelCase | `spacedRepetition.ts` |
| Python modules | snake_case | `skill_unlocks.py` |
| API routes | kebab-case | `/api/daily-breakdown` |

## 18.5 Important Reminders

1. **Always fetch backend data** - Don't rely solely on local state
2. **Handle loading states** - Show skeletons or spinners
3. **Validate inputs** - Both client and server side
4. **Test edge cases** - Empty states, errors, large data
5. **Consider offline** - Graceful degradation when possible
6. **Log errors** - With context for debugging
7. **Keep secrets secret** - Use environment variables

---

# APPENDIX A: QUICK REFERENCE

## API Base URL
```
https://speaksharp-core-production.up.railway.app
```

## Common Endpoints
```
GET  /api/users/me
GET  /api/progress/summary
POST /api/tutor/text
POST /api/speech/transcribe
POST /api/speech/synthesize
GET  /api/srs/due
POST /api/srs/review
POST /api/sessions/save
GET  /api/sessions/stats
GET  /api/skills/profile
GET  /api/recommendations
```

## CEFR Levels
```
A1 - Beginner
A2 - Elementary
B1 - Intermediate
B2 - Upper Intermediate
C1 - Advanced
```

## XP Formula
```
Level = floor(sqrt(XP / 100))
XP for Level N = N^2 * 100
```

---

*Document generated December 16, 2024*
*For the latest version, refer to the repository documentation.*
