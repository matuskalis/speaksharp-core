# Dashboard Testing Guide

## Current Status (December 1, 2025)

### ✅ Infrastructure Ready
- **Backend**: Running on `localhost:8000`
- **Frontend**: Running on `localhost:3001`
- **Database**: Connected and healthy
- **Dashboard Endpoint**: `/api/learning/dashboard` is active
- **Onboarding Check**: Temporarily disabled for testing

### 🎯 What Was Built

We completely refactored the `/learn` page from a static list of lessons into an adaptive, data-driven dashboard with 5 modular components:

1. **TodayFocus**: Shows 3 AI-prioritized tasks based on your weakest skills
2. **QuickActions**: 4 quick-access buttons (Writing, Speaking, AI Tutor, Voice Tutor)
3. **SkillBreakdown**: Visual progress bars for Grammar, Vocabulary, Fluency, Pronunciation
4. **ProgressPath**: Interactive CEFR level tracker (A1 → C2) with ETA to next level
5. **RecentGrowth**: 7-day activity heatmap showing study patterns

### 🧪 How to Test

#### Step 1: Ensure You're Logged In
1. Navigate to `http://localhost:3001`
2. If not logged in, sign in with your Supabase account
3. Your test account: `user_id: 2d284815-2b8b-4a6a-8859-1de162e23a04`

#### Step 2: Access the Dashboard
1. Navigate to `http://localhost:3001/learn`
2. The page should load immediately (onboarding check is disabled)

#### Step 3: Expected Behavior

**You should see:**
- Header: "Your Learning Dashboard"
- Top stats showing:
  - Minutes studied today
  - Current streak (days)
  - Daily goal (minutes)
  - Progress bar indicating goal completion

**Dashboard Sections (in order):**

1. **Today's Focus**
   - 3 cards with prioritized tasks
   - Each card shows: emoji icon, task type (lesson/drill/scenario), title, duration, target skill
   - Cards have colored borders (blue for lessons, green for drills, purple for scenarios)

2. **Quick Actions**
   - 4 colorful action buttons
   - "Start Writing" (blue), "Start Speaking" (green), "AI Tutor" (purple), "Voice Tutor" (orange)
   - Each with emoji icon and description

3. **Skill Breakdown**
   - 4 skills displayed with horizontal progress bars
   - Grammar, Vocabulary, Fluency, Pronunciation
   - Scores shown as percentages (0-100)
   - Weakest skill highlighted with amber background

4. **Progress Path**
   - Visual CEFR level timeline: A1 → A2 → B1 → B2 → C1 → C2
   - Current level highlighted with electric blue ring
   - Shows progress % to next level
   - Displays estimated days to reach next level

5. **Recent Growth**
   - 7-day calendar heatmap
   - Each day shows minutes studied
   - Color intensity indicates activity level (darker = more minutes)
   - Weekly total displayed

### 🐛 What to Check For

#### Visual Issues
- [ ] All components render without layout breaks
- [ ] Animations are smooth (fade-in, slide-up effects)
- [ ] Colors match the electric blue theme
- [ ] Responsive design works on different screen sizes
- [ ] Icons and emojis display correctly

#### Data Issues
- [ ] Stats show real numbers (not 0/null/undefined)
- [ ] Task recommendations are relevant
- [ ] Skill scores are realistic (0-100 range)
- [ ] CEFR progress matches your actual level (B2)
- [ ] Activity heatmap shows correct data

#### Functional Issues
- [ ] Quick action buttons are clickable
- [ ] Task cards link to correct pages
- [ ] No console errors (open DevTools → Console tab)
- [ ] Loading states display properly
- [ ] Error states handle gracefully

### 📊 Backend API Details

**Endpoint**: `GET /api/learning/dashboard`
**Authentication**: Required (Bearer token)

**Response Structure**:
```json
{
  "todayFocus": [
    {
      "id": "string",
      "type": "lesson|drill|scenario",
      "title": "string",
      "duration": number,
      "skill": "string",
      "href": "string"
    }
  ],
  "skillScores": {
    "grammar": 75,
    "vocabulary": 68,
    "fluency": 82,
    "pronunciation": 71
  },
  "progressPath": {
    "current": "B2",
    "next": "C1",
    "progress": 45,
    "daysToNext": 67
  },
  "recentGrowth": [
    {
      "date": "2025-11-24",
      "minutes": 25
    }
  ],
  "minutesStudiedToday": 0,
  "currentStreak": 0,
  "dailyGoal": 30
}
```

### 🔍 Debugging

#### If you see a loading spinner forever:
1. Open DevTools → Network tab
2. Look for requests to `/api/learning/dashboard`
3. Check if the request succeeded (200 OK) or failed (4xx/5xx)
4. If failed, check the error message

#### If you see an error screen:
1. Note the exact error message
2. Open DevTools → Console tab
3. Look for red error messages
4. Share the error with me for debugging

#### If the page is blank:
1. Check DevTools → Console for JavaScript errors
2. Verify you're logged in (check Network tab for auth tokens)
3. Try refreshing the page
4. Check if backend is running: `curl http://localhost:8000/health`

### 🎨 Known Issues

1. **Onboarding Check Disabled**: The check in `/app/learn/page.tsx` (lines 36-41) is commented out. This needs to be re-enabled after testing.

2. **Empty Data**: If you haven't completed any lessons yet, some sections may show zeros or empty states. This is expected for a new account.

3. **Railway Deployment**: The production Railway deployment is currently showing 404. Needs investigation.

### 📝 Next Steps After Testing

Once you've verified the dashboard works:

1. **Re-enable Onboarding Check**
   - Uncomment lines 36-41 in `/Users/matuskalis/vorex-frontend/app/learn/page.tsx`

2. **Fix Railway Deployment**
   - Investigate why Railway is returning 404
   - Ensure environment variables are set correctly
   - Verify the deployment succeeded

3. **Polish UI/UX**
   - Address any visual inconsistencies found
   - Improve animations or transitions as needed
   - Add loading skeletons if data fetching is slow

4. **Add Real Data**
   - Complete some lessons to populate the dashboard
   - Test with realistic user activity
   - Verify recommendations adapt based on weak skills

### 📞 Report Issues

If you encounter any problems:
1. Take a screenshot
2. Copy any console errors
3. Note what you were doing when it happened
4. Share all the above with me

---

**Last Updated**: December 1, 2025
**Test Environment**: Local development (localhost)
**Status**: Ready for testing
