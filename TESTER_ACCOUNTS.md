# Vorex Tester Accounts

These 25 accounts have full access and bypass all trial/payment restrictions.

**Password for all accounts:** `VorexTest2024!`

## Account List

1. tester1@vorex.app
2. tester2@vorex.app
3. tester3@vorex.app
4. tester4@vorex.app
5. tester5@vorex.app
6. tester6@vorex.app
7. tester7@vorex.app
8. tester8@vorex.app
9. tester9@vorex.app
10. tester10@vorex.app
11. tester11@vorex.app
12. tester12@vorex.app
13. tester13@vorex.app
14. tester14@vorex.app
15. tester15@vorex.app
16. tester16@vorex.app
17. tester17@vorex.app
18. tester18@vorex.app
19. tester19@vorex.app
20. tester20@vorex.app
21. tester21@vorex.app
22. tester22@vorex.app
23. tester23@vorex.app
24. tester24@vorex.app
25. tester25@vorex.app

## Setup Instructions

### Option 1: Manual Creation (Supabase Dashboard)
1. Go to your Supabase project dashboard
2. Navigate to Authentication → Users
3. Click "Invite" or "Add user"
4. Create each account with the email and password above
5. After creation, mark them as testers with SQL:

```sql
UPDATE user_profiles
SET is_tester = TRUE
WHERE user_id IN (
  SELECT id FROM auth.users
  WHERE email LIKE 'tester%@vorex.app'
);
```

### Option 2: Supabase Auth API (Automated)
Use the Supabase Admin API to create accounts programmatically.

## How Tester Accounts Work

- `is_tester` flag set to `TRUE` in user_profiles table
- Frontend `useTrialStatus` hook returns `hasAccess: true` for testers
- No trial expiration checks
- No payment required
- Full feature access
