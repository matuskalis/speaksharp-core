# SpeakSharp / Vorex - Comprehensive Project Overview

## Table of Contents
1. [Project Vision](#project-vision)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [Current Features](#current-features)
5. [Recent Major Work](#recent-major-work)
6. [Project Structure](#project-structure)
7. [Key Systems](#key-systems)
8. [Database Schema](#database-schema)
9. [API Endpoints](#api-endpoints)
10. [Frontend Pages](#frontend-pages)
11. [Current State](#current-state)
12. [Future Vision](#future-vision)
13. [Setup & Development](#setup--development)
14. [Deployment](#deployment)
15. [Known Issues](#known-issues)

---

## Project Vision

**SpeakSharp** (also called Vorex in some parts) is an **AI-powered English learning platform** that focuses on **adaptive, personalized language learning** through:

- **Real-time conversation practice** with AI tutors
- **Voice-based learning** with pronunciation feedback
- **Intelligent skill tracking** that identifies weak areas
- **Adaptive lesson planning** based on user progress
- **Spaced Repetition System (SRS)** for vocabulary retention
- **CEFR-aligned progression** (A1 → C2)

### Core Philosophy
- **Show, don't tell** - Make AI intelligence visible through data-driven dashboards
- **No passive learning** - Every interaction should provide immediate, actionable feedback
- **Personalization at scale** - Use AI to create unique learning paths for each user
- **Momentum-driven** - Create urgency and progress visibility to drive engagement

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js)                     │
│  - App Router (Next.js 14.2.0)                              │
│  - React 18 + TypeScript                                     │
│  - Tailwind CSS + Framer Motion                             │
│  - Supabase Auth                                             │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/REST
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  - Python 3.14 + FastAPI                                    │
│  - JWT Authentication                                        │
│  - PostgreSQL (Supabase)                                     │
│  - AsyncPG for DB                                            │
│  - OpenAI GPT-4 integration                                  │
│  - Deepgram for ASR                                          │
│  - ElevenLabs for TTS                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│                  Database (PostgreSQL/Supabase)              │
│  - User profiles & auth (Supabase Auth)                     │
│  - Learning data (sessions, progress, SRS cards)            │
│  - Error tracking & analytics                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend (`/vorex-frontend`)
- **Framework**: Next.js 14.2.0 (App Router)
- **Language**: TypeScript 5.x
- **UI Library**: React 18
- **Styling**: Tailwind CSS 3.x
- **Animation**: Framer Motion
- **Auth**: Supabase Client (@supabase/supabase-js)
- **HTTP Client**: Fetch API (wrapped in `apiClient`)
- **State Management**: React Context API
- **Form Handling**: React Hook Form (in some components)

### Backend (`/vorex-backend`)
- **Framework**: FastAPI
- **Language**: Python 3.14
- **Database**: PostgreSQL (via Supabase)
- **ORM**: Raw SQL with AsyncPG
- **Auth**: JWT tokens (Supabase)
- **AI/ML**:
  - OpenAI GPT-4 (tutoring, content generation)
  - Deepgram (ASR - Automatic Speech Recognition)
  - ElevenLabs (TTS - Text to Speech)
  - Phonemizer (pronunciation scoring)
- **HTTP Server**: Uvicorn
- **Environment**: python-dotenv

### Infrastructure
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Railway
- **Database**: Supabase (Managed PostgreSQL)
- **Auth Provider**: Supabase Auth
- **Version Control**: Git

---

## Current Features

### ✅ Implemented Features

#### 1. **User Authentication & Onboarding**
- Email/password signup via Supabase
- Placement test with 10 questions
- Goal setting and interest selection
- Daily time commitment tracking
- 14-day free trial system

#### 2. **Adaptive Learning Dashboard** (NEW - Just Implemented)
- **Today's Focus**: 3 AI-prioritized tasks based on weak skills
- **Quick Actions**: One-click access to learning modes
- **Skill Breakdown**: Visual bars for Grammar/Vocabulary/Fluency/Pronunciation (0-100)
- **Progress Path**: CEFR level visualization (A1→C2) with ETA
- **Recent Growth**: 7-day activity heatmap
- Real-time metrics: minutes studied today, streak, daily goal

#### 3. **AI Text Tutor** (`/tutor`)
- GPT-4 powered conversational tutoring
- Context-aware error correction
- Micro-tasks and exercises
- Session persistence

#### 4. **Voice Tutor** (`/voice-tutor`)
- Real-time speech recognition (Deepgram)
- AI voice responses (ElevenLabs TTS)
- Pronunciation feedback
- Conversational practice

#### 5. **Journal Writing** (`/journal`)
- Guided writing prompts
- AI-powered grammar correction
- Error analysis and feedback

#### 6. **Monologue Practice** (`/monologue`)
- Voice recording practice
- Topic-based speaking exercises
- Pronunciation scoring

#### 7. **Spaced Repetition System (SRS)**
- Vocabulary card system
- SM-2 algorithm implementation
- Due card scheduling
- Mastery tracking

#### 8. **Error Tracking & Analytics**
- Skill categorization (grammar, vocabulary, fluency, pronunciation)
- Error frequency tracking
- Weak skill identification
- Mastery score calculation

#### 9. **Scenario-Based Learning**
- Contextual conversation practice
- Real-world situation simulations

#### 10. **Lessons & Drills**
- Structured lesson plans
- Practice drills
- Progress tracking

---

## Recent Major Work

### Dashboard Refactor (November 2024)

**Context**: The original `/learn` page was a static list of buttons with hardcoded lesson data. Based on user feedback (via ChatGPT critique), it was identified as "surface-level and generic" with no visible AI intelligence.

**Implementation**: Complete transformation into a **data-driven adaptive dashboard**

#### What Was Built:

**Backend (`/api/learning/dashboard`)**:
- Intelligent task prioritization based on user's 3 weakest skills
- Skill scoring calculation (0-100 scale) derived from mastery data
- CEFR progress tracking with estimated days to next level
- 7-day activity aggregation
- Real-time metrics (study time, streaks, goals)

**Frontend Components** (all new):
1. `TodayFocus.tsx` - 3 prioritized tasks with type badges (lesson/drill/scenario)
2. `SkillBreakdown.tsx` - Visual skill bars with weak-skill highlighting
3. `ProgressPath.tsx` - Interactive CEFR level track (A1→C2)
4. `RecentGrowth.tsx` - 7-day heatmap with intensity colors
5. `QuickActions.tsx` - Quick-access buttons for learning modes

**Key Features**:
- All data from single `getLearningDashboard()` API call
- Framer Motion animations for smooth UX
- Electric blue design theme (`electric-500`, `electric-600`)
- Responsive layout (mobile-first)
- Real-time weak skill detection

**Files Changed**:
- `/vorex-frontend/app/learn/page.tsx` (492 → 204 lines, complete rewrite)
- `/vorex-frontend/lib/types.ts` (added dashboard types)
- `/vorex-frontend/lib/api-client.ts` (added `getLearningDashboard()`)
- `/vorex-backend/app/api.py` (added `/api/learning/dashboard` endpoint, lines 1956-2129)
- Created 5 new dashboard components in `/vorex-frontend/app/components/dashboard/`

**Current Status**:
- ✅ Backend API implemented and deployed to Railway
- ✅ Frontend components built and deployed to Vercel
- ⚠️ Testing blocked by onboarding flow issues (temporarily disabled for dev)
- ⏳ Needs production testing with real user data

---

## Project Structure

### Frontend (`/vorex-frontend`)
```
vorex-frontend/
├── app/
│   ├── components/
│   │   ├── dashboard/           # NEW - Dashboard components
│   │   │   ├── TodayFocus.tsx
│   │   │   ├── QuickActions.tsx
│   │   │   ├── SkillBreakdown.tsx
│   │   │   ├── ProgressPath.tsx
│   │   │   └── RecentGrowth.tsx
│   │   ├── AuthForm.tsx
│   │   ├── GoalSelector.tsx
│   │   ├── InterestsSelector.tsx
│   │   ├── OnboardingWizard.tsx
│   │   ├── PlacementTest.tsx
│   │   ├── PricingSection.tsx
│   │   └── TimeCommitment.tsx
│   ├── auth/page.tsx             # Authentication page
│   ├── get-started/page.tsx      # Onboarding flow
│   ├── journal/page.tsx          # Writing practice
│   ├── learn/page.tsx            # MAIN DASHBOARD (new)
│   ├── monologue/page.tsx        # Speaking practice
│   ├── pricing/page.tsx          # Pricing page
│   ├── subscribe/page.tsx        # Subscription page
│   ├── test-dashboard/page.tsx   # Testing utility
│   ├── tutor/page.tsx            # Text AI tutor
│   └── voice-tutor/page.tsx      # Voice AI tutor
├── components/
│   ├── ui/                       # Shadcn UI components
│   ├── app-shell.tsx             # Layout wrapper
│   ├── loading-skeleton.tsx      # Loading states
│   └── paywall.tsx               # Paywall component
├── contexts/
│   └── AuthContext.tsx           # Auth state management
├── hooks/
│   ├── useTrialStatus.ts         # Trial access logic
│   └── useUserProfile.ts         # User profile hook
├── lib/
│   ├── api-client.ts             # HTTP client
│   ├── types.ts                  # TypeScript types
│   └── utils.ts                  # Utilities
└── .env.local                    # Environment variables
```

### Backend (`/vorex-backend`)
```
vorex-backend/
├── app/
│   ├── api.py                    # MAIN API FILE (2144 lines)
│   ├── auth.py                   # JWT auth logic
│   ├── config.py                 # Configuration
│   ├── db.py                     # Database wrapper
│   ├── drills.py                 # Drill exercises
│   ├── lessons.py                # Lesson content
│   ├── llm_client.py             # OpenAI integration
│   ├── asr_client.py             # Deepgram ASR
│   ├── tts_client.py             # ElevenLabs TTS
│   ├── models.py                 # Pydantic models
│   ├── placement_test.py         # Placement test logic
│   ├── pronunciation.py          # Pronunciation scoring
│   ├── pronunciation_scorer.py   # Phoneme analysis
│   ├── scenarios.py              # Scenario definitions
│   ├── srs_system.py             # Spaced repetition
│   ├── state_machine.py          # Session state
│   ├── tutor_agent.py            # AI tutor logic
│   └── voice_session.py          # Voice session handling
├── migrations/                   # Database migrations
│   ├── migration_001.sql         # Initial schema
│   ├── migration_002.sql         # Add columns
│   ├── migration_003.sql         # Onboarding fields
│   ├── migration_004.sql         # Trial dates
│   └── migration_005.sql         # Onboarding completed
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── mark_complete.py              # Utility script
```

---

## Key Systems

### 1. Authentication Flow
```
User signup → Supabase Auth → JWT token → Backend verification
                                ↓
                        User profile creation
                                ↓
                        Onboarding wizard
```

### 2. Adaptive Dashboard System
```
User visits /learn → Fetch getLearningDashboard()
                            ↓
                    Backend analyzes:
                    - Weak skills from error_log
                    - Mastery scores from srs_cards
                    - Session history
                    - CEFR level progress
                            ↓
                    Returns personalized data:
                    - 3 prioritized tasks
                    - Skill scores
                    - Progress metrics
                    - Activity history
                            ↓
                    Frontend renders dashboard
```

### 3. Error Tracking & Skill Analysis
```
User makes error → Categorized by skill type
                         ↓
                   Stored in error_log table
                         ↓
                   Aggregated for weak skill detection
                         ↓
                   Influences task prioritization
```

### 4. SRS (Spaced Repetition)
```
Card presented → User response → SM-2 algorithm calculates:
                                  - New interval
                                  - Easiness factor
                                  - Next review date
                                  - Mastery score
```

### 5. Trial System
```
User signs up → 14-day trial starts
                    ↓
              Trial tracked via:
              - trial_start_date
              - trial_end_date
                    ↓
              Paywall shown if expired
```

---

## Database Schema

### Core Tables

#### `auth.users` (Supabase managed)
- `id` (UUID, PK)
- `email`
- `created_at`
- Managed by Supabase Auth

#### `public.user_profile`
```sql
- user_id (UUID, FK → auth.users, PK)
- level (TEXT) - CEFR level (A1, A2, B1, B2, C1, C2)
- daily_goal (INTEGER) - Minutes per day
- created_at (TIMESTAMP)
- goals (TEXT[]) - Learning goals
- interests (TEXT[]) - User interests
- onboarding_completed (BOOLEAN) - NEW
- trial_start_date (TIMESTAMP) - NEW
- trial_end_date (TIMESTAMP) - NEW
- is_tester (BOOLEAN) - Bypass paywall
```

#### `public.sessions`
```sql
- id (UUID, PK)
- user_id (UUID, FK → auth.users)
- session_type (TEXT) - 'lesson', 'drill', 'scenario', 'tutor'
- created_at (TIMESTAMP)
- completed_at (TIMESTAMP)
- metadata (JSONB) - Session details
```

#### `public.srs_cards`
```sql
- id (UUID, PK)
- user_id (UUID, FK → auth.users)
- word (TEXT)
- translation (TEXT)
- context_sentence (TEXT)
- interval (INTEGER) - Days until next review
- repetitions (INTEGER)
- easiness_factor (FLOAT)
- next_review_date (TIMESTAMP)
- mastery_score (FLOAT) - 0.0 to 1.0
- created_at (TIMESTAMP)
- last_reviewed_at (TIMESTAMP)
```

#### `public.error_log`
```sql
- id (UUID, PK)
- user_id (UUID, FK → auth.users)
- error_type (TEXT)
- error_description (TEXT)
- correction (TEXT)
- skill_category (TEXT) - 'grammar', 'vocabulary', 'fluency', 'pronunciation'
- created_at (TIMESTAMP)
- session_id (UUID, FK → sessions)
```

---

## API Endpoints

### Authentication
- `POST /api/auth/token` - Get JWT token (Supabase)

### User Management
- `GET /api/users/me` - Get current user profile
- `GET /api/users/{user_id}` - Get user profile by ID
- `PUT /api/users/profile` - Update user profile
- `POST /api/users/profile` - Create user profile

### Learning Dashboard (NEW)
- `GET /api/learning/dashboard` - Get personalized dashboard data
  - Returns: todayFocus, skillScores, progressPath, recentGrowth, metrics

### Placement Test
- `POST /api/placement/test` - Submit placement test
- `GET /api/placement/questions` - Get test questions

### Tutoring
- `POST /api/tutor/chat` - Text-based tutoring
- `POST /api/tutor/voice` - Voice-based tutoring
- `POST /api/voice/session/start` - Start voice session
- `POST /api/voice/session/process` - Process voice input

### SRS System
- `GET /api/srs/due` - Get due cards for review
- `POST /api/srs/review` - Submit card review
- `POST /api/srs/card` - Create new card

### Error Tracking
- `POST /api/errors` - Log error
- `GET /api/errors` - Get user errors
- `GET /api/errors/weak-skills` - Get weak skill analysis

### Sessions
- `POST /api/sessions` - Create session
- `PUT /api/sessions/{session_id}` - Update session
- `GET /api/sessions` - Get user sessions

### Lessons & Drills
- `GET /api/lessons` - Get lessons
- `GET /api/drills` - Get drills

### Admin (Temporary)
- `POST /api/admin/complete-onboarding` - Mark onboarding complete (for testing)

---

## Frontend Pages

### Public Pages
- `/` - Landing page
- `/pricing` - Pricing page
- `/auth` - Login/signup page

### Onboarding Flow
- `/get-started` - Multi-step onboarding wizard
  1. Goal selection
  2. Time commitment
  3. Interests
  4. Authentication (if not logged in)
  5. Placement test

### Protected Pages (require auth)
- `/learn` - **Main dashboard** (NEW - adaptive, data-driven)
- `/tutor` - Text AI tutor chat
- `/voice-tutor` - Voice AI conversation
- `/journal` - Writing practice with feedback
- `/monologue` - Speaking practice
- `/subscribe` - Trial/subscription management

### Utility Pages
- `/test-dashboard` - Testing bypass (dev only)

---

## Current State

### ✅ What's Working
- Full authentication flow via Supabase
- Onboarding wizard with placement test
- All learning modes (tutor, voice, journal, monologue)
- SRS vocabulary system
- Error tracking and skill analysis
- Trial system (14 days)
- **NEW**: Adaptive dashboard with intelligent task prioritization
- Deployment: Frontend on Vercel, Backend on Railway

### ⚠️ What Needs Work
- **Onboarding flow** has UI issues (buttons not clickable in some cases)
- **Dashboard testing** blocked by onboarding - temporarily disabled check
- **Database schema** inconsistencies between local and production
- **Paywall integration** needs refinement
- **Real user data** needed to validate dashboard algorithms

### 🐛 Known Bugs
- Onboarding page buttons sometimes unresponsive (CSS/React issue)
- Local database missing `user_profile` table (env mismatch)
- Frontend loading states sometimes infinite loop
- Database connection pooling needs optimization

### 📊 Performance
- Frontend: Fast (Next.js SSR + RSC)
- Backend: ~200-500ms API response times
- Database: Needs query optimization for dashboard endpoint

---

## Future Vision

### Phase 1: Core Improvements (Next 1-2 months)
1. **Fix onboarding flow** - Resolve button click issues
2. **Dashboard polish** - Real user testing and iteration
3. **Payment integration** - Stripe for subscriptions
4. **Mobile responsiveness** - Ensure all pages work on mobile
5. **Performance optimization** - Database indexing, caching

### Phase 2: AI Power Surfacing (2-3 months)
1. **Achievement system** - Badges, milestones, level-ups
2. **Smart notifications** - "You're close to your daily goal!"
3. **Weekly insights** - AI-generated progress reports
4. **Lesson recommendations** - Personalized lesson suggestions
5. **Real-time progress graphs** - Skill improvement over time

### Phase 3: Social & Engagement (3-6 months)
1. **Leaderboards** - Weekly/monthly rankings
2. **Study groups** - Peer learning
3. **Challenges** - Daily/weekly challenges
4. **Streaks & rewards** - Duolingo-style engagement
5. **Share progress** - Social media integration

### Phase 4: Content Expansion (6-12 months)
1. **More languages** - Spanish, French, German, etc.
2. **Specialized tracks** - Business English, IELTS prep, etc.
3. **Video lessons** - Integrated video content
4. **Live tutoring** - Connect with human tutors
5. **Writing correction** - Advanced essay feedback

### Phase 5: Platform (12+ months)
1. **Mobile apps** - iOS and Android native apps
2. **Offline mode** - Download lessons for offline use
3. **API for partners** - White-label solutions
4. **Teacher dashboard** - For schools and institutions
5. **Analytics platform** - Deep learning insights

### Moonshot Ideas
- **AR/VR integration** - Immersive conversation practice
- **AI-generated content** - Infinite personalized lessons
- **Speech synthesis cloning** - Practice with famous voices
- **Gamification** - Full RPG-style learning experience
- **Peer matching** - AI-powered study buddy matching

---

## Setup & Development

### Prerequisites
- Node.js 18+ (for frontend)
- Python 3.14 (for backend)
- PostgreSQL (via Supabase)
- Supabase account
- OpenAI API key
- Deepgram API key (for ASR)
- ElevenLabs API key (for TTS)

### Frontend Setup
```bash
cd vorex-frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with your Supabase credentials
npm run dev
# Visit http://localhost:3000
```

### Backend Setup
```bash
cd vorex-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python -m app.api
# API runs on http://localhost:8000
```

### Environment Variables

**Frontend** (`.env.local`):
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend** (`.env`):
```
DATABASE_URL=postgresql://...
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key
JWT_SECRET=your_jwt_secret
```

---

## Deployment

### Current Setup
- **Frontend**: Vercel (auto-deploy from main branch)
- **Backend**: Railway (connected to GitHub)
- **Database**: Supabase (hosted PostgreSQL)

### Deployment Process
```bash
# Frontend
git push origin main
# Vercel auto-deploys

# Backend
git push origin main
# Railway auto-deploys

# Manual Railway deployment
railway up
```

### Migrations
```bash
# Run migrations on Railway
railway run python -m migrations.run_migration_005
```

---

## Known Issues

### Critical
1. ⛔ **Onboarding UI blocking** - Buttons unresponsive, prevents user signup
2. ⛔ **Database schema mismatch** - Local DB missing tables from production

### High Priority
3. 🔴 **Dashboard untested** - New dashboard needs real user validation
4. 🔴 **Payment flow incomplete** - Stripe integration needed
5. 🔴 **Mobile responsiveness** - Some pages break on mobile

### Medium Priority
6. 🟡 **Performance** - Dashboard endpoint could be faster
7. 🟡 **Error handling** - Frontend needs better error states
8. 🟡 **Loading states** - Infinite loading in some scenarios

### Low Priority
9. 🔵 **Code cleanup** - Remove dead code and temp files
10. 🔵 **Documentation** - API docs need updating
11. 🔵 **Testing** - Add unit/integration tests

---

## Key Metrics to Track

### User Engagement
- Daily Active Users (DAU)
- Weekly Active Users (WAU)
- Session length
- Completion rate (lessons finished vs. started)
- Streak length

### Learning Outcomes
- Words mastered (SRS)
- Skill improvements over time
- CEFR level progression
- Error reduction rate

### Business Metrics
- Trial-to-paid conversion
- Churn rate
- LTV (Lifetime Value)
- NPS (Net Promoter Score)

---

## Architecture Decisions

### Why Next.js App Router?
- Server components for better performance
- File-based routing
- Built-in API routes (not used, but available)
- Excellent DX and TypeScript support

### Why FastAPI?
- Async support for real-time features
- Auto-generated OpenAPI docs
- Fast performance
- Python ecosystem (AI/ML libraries)

### Why Supabase?
- Managed PostgreSQL
- Built-in auth (saves time)
- Real-time subscriptions (future use)
- Good free tier for development

### Why Not...?
- **Not Next.js API routes**: Wanted separate backend for flexibility
- **Not Django**: FastAPI is faster and more modern for async work
- **Not MongoDB**: Relational data (user → sessions → errors) fits SQL better
- **Not Firebase**: More control with PostgreSQL + Supabase

---

## Contact & Contribution

This is currently a solo project. For questions or collaboration:
- Check the code comments
- Review API docs at `http://localhost:8000/docs`
- Read this document

---

## Recent Changelog

### 2024-11-30 - Dashboard Refactor
- ✅ Built adaptive dashboard system
- ✅ Created 5 new dashboard components
- ✅ Implemented intelligent task prioritization
- ✅ Added skill scoring algorithm
- ✅ CEFR progress visualization
- ✅ 7-day activity heatmap
- ✅ Deployed to production

### 2024-11 - Trial System
- ✅ Added 14-day free trial
- ✅ Trial date tracking in database
- ✅ Paywall component
- ✅ Tester bypass system

### 2024-10 - Onboarding Redesign
- ✅ Electric blue theme
- ✅ Placement test with new UI
- ✅ Goal/interest selection
- ✅ Time commitment picker

---

**Last Updated**: November 30, 2024
**Version**: 2.0 (Dashboard Update)
**Status**: 🚧 Active Development
