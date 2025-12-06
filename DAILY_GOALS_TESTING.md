# Daily Goals Feature - Testing Guide

This guide explains how to test the newly implemented Daily Goals feature.

## Backend Endpoints

### 1. GET /api/goals/today
Gets today's daily goal for the authenticated user. Creates a goal with default targets if it doesn't exist.

**Test with cURL:**
```bash
curl -X GET "http://localhost:8000/api/goals/today" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "goal_id": "uuid",
  "user_id": "uuid",
  "goal_date": "2025-12-04",
  "target_study_minutes": 30,
  "target_lessons": 1,
  "target_reviews": 10,
  "target_drills": 2,
  "actual_study_minutes": 0,
  "actual_lessons": 0,
  "actual_reviews": 0,
  "actual_drills": 0,
  "completed": false,
  "completion_percentage": 0.0,
  "created_at": "2025-12-04T10:00:00",
  "updated_at": "2025-12-04T10:00:00"
}
```

### 2. POST /api/goals/today
Updates today's goal targets for the authenticated user.

**Test with cURL:**
```bash
curl -X POST "http://localhost:8000/api/goals/today" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_study_minutes": 45,
    "target_lessons": 2,
    "target_reviews": 15,
    "target_drills": 3
  }'
```

### 3. POST /api/goals/today/progress
Increments today's goal progress counters.

**Test with cURL:**
```bash
curl -X POST "http://localhost:8000/api/goals/today/progress" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "study_minutes": 15,
    "lessons": 1,
    "reviews": 5,
    "drills": 1
  }'
```

## Frontend Component

The `DailyGoalCard` component is already integrated in the dashboard at `/Users/matuskalis/vorex-frontend/components/daily-goal-card.tsx`

### Features:
1. **Circular Progress Ring** - Shows overall completion percentage visually
2. **Individual Progress Bars** - For each goal metric (study minutes, lessons, reviews, drills)
3. **Edit Mode** - Allows customizing daily targets
4. **Celebration Animation** - Triggers when all goals are completed (trophy with sparkles)
5. **Motivational Messages** - Encourages user at 75% and celebrates at 100%

### Component Usage:
The component is already used in the dashboard:
```tsx
import DailyGoalCard from "@/components/daily-goal-card";

// In your dashboard component:
<DailyGoalCard />
```

## Database Schema

The `daily_goals` table structure (already exists):
```sql
CREATE TABLE daily_goals (
  goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES user_profiles(user_id),
  goal_date DATE NOT NULL DEFAULT CURRENT_DATE,
  target_study_minutes INT DEFAULT 30,
  target_lessons INT DEFAULT 1,
  target_reviews INT DEFAULT 10,
  target_drills INT DEFAULT 2,
  actual_study_minutes INT DEFAULT 0,
  actual_lessons INT DEFAULT 0,
  actual_reviews INT DEFAULT 0,
  actual_drills INT DEFAULT 0,
  completed BOOLEAN DEFAULT FALSE,
  completion_percentage DECIMAL(5,2) DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, goal_date)
);
```

## Integration Points

To automatically update progress when users complete activities:

### After Completing a Lesson:
```typescript
await apiClient.updateGoalProgress({ lessons: 1 });
```

### After Completing Reviews:
```typescript
await apiClient.updateGoalProgress({ reviews: 5 }); // Number of reviews completed
```

### After Completing a Drill:
```typescript
await apiClient.updateGoalProgress({ drills: 1 });
```

### After Study Session:
```typescript
await apiClient.updateGoalProgress({ study_minutes: 15 }); // Duration in minutes
```

## Testing Checklist

- [ ] Backend server starts without errors
- [ ] GET /api/goals/today creates a goal with defaults
- [ ] POST /api/goals/today updates targets correctly
- [ ] POST /api/goals/today/progress increments counters
- [ ] Completion percentage calculates correctly
- [ ] `completed` flag turns true when all goals reached
- [ ] Frontend component loads without errors
- [ ] Circular progress ring animates correctly
- [ ] Edit mode saves changes
- [ ] Celebration animation shows at 100%
- [ ] Component matches app's visual theme
- [ ] API calls include proper JWT authentication

## Next Steps

1. **Integrate Progress Updates**: Add calls to `/api/goals/today/progress` in lesson, review, drill, and tutor completion handlers
2. **Add to Learn Page**: Consider adding a simplified version to the learn page
3. **Track Study Time**: Implement a timer or tracking mechanism for study minutes
4. **Analytics**: Add goal completion tracking to analytics dashboard
