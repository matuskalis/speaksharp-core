# Vorex Development Roadmap

## High Priority (Ready to implement)

| # | Task | Effort | Description |
|---|------|--------|-------------|
| 1 | **Modularize api2.py** | Medium | Split 6500+ line file into sub-routers (auth, tutor, skills, social, etc.) |
| 2 | **Add Redis caching** | Medium | Cache hot SRS cards, skill profiles, session data |
| 3 | **WebSocket live tutoring** | High | Real-time conversation with streaming responses |
| 4 | **Expand content** | High | Add 20+ scenarios, 50+ lessons (currently 5/11) |
| 5 | **Pronunciation scoring unification** | Medium | Merge phoneme analysis into single 0-100 score |

## Medium Priority (Enhancement)

| # | Task | Effort | Description |
|---|------|--------|-------------|
| 6 | **Mobile app** | High | React Native/Expo app consuming REST API |
| 7 | **Analytics dashboard** | Medium | Visualize learning curves, retention, weak skills |
| 8 | **Adaptive difficulty** | Medium | Dynamic lesson/scenario difficulty per user |
| 9 | **Connection pooling** | Low | Configure SQLAlchemy/psycopg2 connection pool |
| 10 | **Structured logging** | Low | JSON logs, Sentry integration, APM |

## Low Priority (Nice-to-have)

| # | Task | Effort | Description |
|---|------|--------|-------------|
| 11 | **Offline mode** | High | Service worker, local DB sync for mobile |
| 12 | **Community features** | High | Forums, peer review, writing challenges |
| 13 | **Multi-language UI** | Medium | i18n for non-English speakers |
| 14 | **Digital certificates** | Low | Issue completion badges |

## Technical Debt

| # | Task | Description |
|---|------|-------------|
| TD1 | **Type hints** | Add consistent typing across all modules |
| TD2 | **Test coverage** | Expand pytest to >80% coverage |
| TD3 | **Error handling** | Replace generic exceptions with specific handlers |
| TD4 | **Documentation** | Add docstrings to all public functions |
| TD5 | **Clean up docs** | Remove/consolidate ~30 orphaned .md files |

---

## Content Expansion Details

### Current State
- **Scenarios**: 5 (Café Ordering, Self Introduction, Asking Directions, Doctor's Appointment, Talk About Your Day)
- **Lessons**: 11 (A1-A2 grammar and communication)

### Target State
- **Scenarios**: 30+ covering:
  - Everyday situations (shopping, restaurants, transportation)
  - Professional contexts (job interviews, meetings, presentations)
  - Social situations (parties, making friends, phone calls)
  - Travel scenarios (hotel, airport, sightseeing)
  - Emergency situations (pharmacy, police, lost items)

- **Lessons**: 50+ covering:
  - A1: Basics (present simple, articles, pronouns)
  - A2: Elementary (past tenses, modals, comparatives)
  - B1: Intermediate (conditionals, passive voice, reported speech)
  - B2: Upper-intermediate (perfect tenses, subjunctive, advanced modals)

---

## API Modularization Plan

Current `api2.py` (6500+ lines) should be split into:

```
app/
├── api/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, middleware, CORS
│   ├── routers/
│   │   ├── auth.py      # /api/auth/* endpoints
│   │   ├── users.py     # /api/users/* endpoints
│   │   ├── tutor.py     # /api/tutor/* endpoints
│   │   ├── srs.py       # /api/srs/* endpoints
│   │   ├── skills.py    # /api/skills/* endpoints
│   │   ├── replays.py   # /api/replays/* endpoints
│   │   ├── lessons.py   # /api/lessons/* endpoints
│   │   └── scenarios.py # /api/scenarios/* endpoints
│   └── dependencies.py  # Shared deps (auth, db)
```

---

## Recently Completed

- [x] Pronunciation phoneme analysis with IPA confusion tracking
- [x] Conversation replay with coaching annotations
- [x] Skill-based XP/unlock progression system
- [x] Multi-AI orchestrator with parallel processing
- [x] User Language Profile with adaptive tutoring
- [x] Audio quality detection for pronunciation accuracy
- [x] L1 interference patterns for 8 major languages

---

**Last Updated**: December 14, 2025
