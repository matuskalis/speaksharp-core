-- Migration 001: Comprehensive User Data Collection
-- Run this AFTER the base schema.sql

-- ============================================
-- PART 1: Enhance User Profiles
-- ============================================

ALTER TABLE user_profiles
  ADD COLUMN IF NOT EXISTS full_name VARCHAR(255),
  ADD COLUMN IF NOT EXISTS profile_picture_url TEXT,
  ADD COLUMN IF NOT EXISTS date_of_birth DATE,
  ADD COLUMN IF NOT EXISTS age INTEGER,
  ADD COLUMN IF NOT EXISTS country VARCHAR(100),
  ADD COLUMN IF NOT EXISTS timezone VARCHAR(50),
  ADD COLUMN IF NOT EXISTS occupation VARCHAR(255),
  ADD COLUMN IF NOT EXISTS learning_purpose TEXT, -- "work", "travel", "education", "personal", etc.
  ADD COLUMN IF NOT EXISTS target_completion_date DATE,
  ADD COLUMN IF NOT EXISTS hours_per_week INTEGER DEFAULT 5,
  ADD COLUMN IF NOT EXISTS preferred_study_time VARCHAR(50), -- "morning", "afternoon", "evening", "night"
  ADD COLUMN IF NOT EXISTS english_use_context TEXT[], -- ["work", "social", "academic", etc.]
  ADD COLUMN IF NOT EXISTS weakest_skills TEXT[], -- ["grammar", "pronunciation", "vocabulary", etc.]
  ADD COLUMN IF NOT EXISTS bio TEXT,
  ADD COLUMN IF NOT EXISTS referral_source VARCHAR(100), -- "google", "friend", "ad", "social_media", etc.
  ADD COLUMN IF NOT EXISTS referral_code VARCHAR(50), -- if referred by another user
  ADD COLUMN IF NOT EXISTS marketing_emails_opt_in BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS total_study_time_minutes INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS account_status VARCHAR(50) DEFAULT 'active', -- "active", "paused", "cancelled"
  ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50) DEFAULT 'free', -- "free", "premium", "enterprise"
  ADD COLUMN IF NOT EXISTS trial_end_date DATE,
  ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS onboarding_step INTEGER DEFAULT 0;

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON user_profiles(country);
CREATE INDEX IF NOT EXISTS idx_user_profiles_subscription_tier ON user_profiles(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_active ON user_profiles(last_active_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_profiles_account_status ON user_profiles(account_status);

-- ============================================
-- PART 2: Session Tracking & Analytics
-- ============================================

CREATE TABLE IF NOT EXISTS session_analytics (
  session_analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  session_id UUID REFERENCES sessions(session_id),

  -- Device & Browser Info
  device_type VARCHAR(50), -- "desktop", "mobile", "tablet"
  os VARCHAR(100), -- "Windows 11", "macOS 14.0", "iOS 17", etc.
  browser VARCHAR(100), -- "Chrome 120", "Safari 17", "Firefox 121", etc.
  screen_resolution VARCHAR(50), -- "1920x1080", "1366x768", etc.
  user_agent TEXT,

  -- Network Info
  ip_address VARCHAR(45), -- supports IPv6
  country_code VARCHAR(10),
  city VARCHAR(100),

  -- Session Metrics
  page_views INTEGER DEFAULT 0,
  actions_taken INTEGER DEFAULT 0,
  errors_encountered INTEGER DEFAULT 0,

  -- Performance
  avg_response_time_ms INTEGER,
  total_api_calls INTEGER DEFAULT 0,

  -- Timestamps
  first_seen_at TIMESTAMP DEFAULT NOW(),
  last_seen_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_analytics_user ON session_analytics(user_id, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_analytics_device ON session_analytics(device_type);

-- ============================================
-- PART 3: User Engagement & Streaks
-- ============================================

CREATE TABLE IF NOT EXISTS user_streaks (
  streak_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) UNIQUE,

  -- Current Streak
  current_streak_days INTEGER DEFAULT 0,
  longest_streak_days INTEGER DEFAULT 0,
  current_streak_start_date DATE,
  last_activity_date DATE,

  -- Weekly Goals
  weekly_goal_minutes INTEGER DEFAULT 180, -- 3 hours per week default
  current_week_minutes INTEGER DEFAULT 0,
  week_start_date DATE,

  -- Lifetime Stats
  total_days_active INTEGER DEFAULT 0,
  total_sessions_completed INTEGER DEFAULT 0,

  -- Freeze Days (for maintaining streaks)
  freeze_days_available INTEGER DEFAULT 2,
  freeze_days_used INTEGER DEFAULT 0,

  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_streaks_current ON user_streaks(current_streak_days DESC);

-- ============================================
-- PART 4: Achievements & Gamification
-- ============================================

CREATE TABLE IF NOT EXISTS achievements (
  achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  achievement_key VARCHAR(100) UNIQUE NOT NULL, -- "first_lesson", "10_day_streak", "100_errors_fixed", etc.
  title VARCHAR(255) NOT NULL,
  description TEXT,
  icon_url TEXT,
  category VARCHAR(50), -- "milestone", "streak", "mastery", "social"
  points INTEGER DEFAULT 0,
  tier VARCHAR(20) DEFAULT 'bronze', -- "bronze", "silver", "gold", "platinum"
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_achievements (
  user_achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  achievement_id UUID REFERENCES achievements(achievement_id),
  unlocked_at TIMESTAMP DEFAULT NOW(),
  progress FLOAT DEFAULT 100.0, -- percentage towards completion
  UNIQUE(user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id, unlocked_at DESC);

-- ============================================
-- PART 5: Daily Goals & Tasks
-- ============================================

CREATE TABLE IF NOT EXISTS daily_goals (
  goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  goal_date DATE NOT NULL,

  -- Goal Targets
  target_study_minutes INTEGER DEFAULT 30,
  target_lessons INTEGER DEFAULT 1,
  target_reviews INTEGER DEFAULT 10,
  target_drills INTEGER DEFAULT 2,

  -- Actual Progress
  actual_study_minutes INTEGER DEFAULT 0,
  actual_lessons INTEGER DEFAULT 0,
  actual_reviews INTEGER DEFAULT 0,
  actual_drills INTEGER DEFAULT 0,

  -- Status
  completed BOOLEAN DEFAULT FALSE,
  completion_percentage FLOAT DEFAULT 0.0,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, goal_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_goals_user_date ON daily_goals(user_id, goal_date DESC);

-- ============================================
-- PART 6: Referral Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS referral_codes (
  code_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  code VARCHAR(50) UNIQUE NOT NULL,

  -- Stats
  total_signups INTEGER DEFAULT 0,
  total_conversions INTEGER DEFAULT 0, -- signups that became paying users

  -- Rewards
  reward_type VARCHAR(50), -- "free_month", "discount", "points", etc.
  reward_value INTEGER,

  is_active BOOLEAN DEFAULT TRUE,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS referral_conversions (
  conversion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  referrer_user_id UUID REFERENCES user_profiles(user_id),
  referred_user_id UUID REFERENCES user_profiles(user_id),
  referral_code VARCHAR(50),

  converted BOOLEAN DEFAULT FALSE, -- did they become a paying customer?
  converted_at TIMESTAMP,

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referral_conversions(referrer_user_id);

-- ============================================
-- PART 7: Subscriptions & Payments
-- ============================================

CREATE TABLE IF NOT EXISTS user_subscriptions (
  subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),

  -- Subscription Info
  tier VARCHAR(50) NOT NULL, -- "free", "premium", "enterprise"
  status VARCHAR(50) NOT NULL, -- "active", "past_due", "cancelled", "trialing"

  -- Billing
  billing_cycle VARCHAR(50), -- "monthly", "yearly", "lifetime"
  price_paid_cents INTEGER, -- store in cents to avoid float precision issues
  currency VARCHAR(10) DEFAULT 'USD',

  -- Payment Provider Info (DON'T store card details - use Stripe)
  stripe_customer_id VARCHAR(255),
  stripe_subscription_id VARCHAR(255),
  payment_method_last4 VARCHAR(4), -- last 4 digits only
  payment_method_type VARCHAR(50), -- "card", "paypal", etc.

  -- Dates
  started_at TIMESTAMP DEFAULT NOW(),
  current_period_start TIMESTAMP,
  current_period_end TIMESTAMP,
  cancelled_at TIMESTAMP,
  trial_start TIMESTAMP,
  trial_end TIMESTAMP,

  -- Cancellation Info
  cancellation_reason TEXT,
  will_renew BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe ON user_subscriptions(stripe_customer_id);

-- ============================================
-- PART 8: Feature Usage Tracking
-- ============================================

CREATE TABLE IF NOT EXISTS feature_usage (
  usage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),

  -- Feature Info
  feature_name VARCHAR(100) NOT NULL, -- "text_tutor", "voice_tutor", "srs_review", "lesson", etc.
  action VARCHAR(100), -- "started", "completed", "skipped", "failed", etc.

  -- Context
  session_id UUID REFERENCES sessions(session_id),
  metadata JSONB, -- flexible storage for feature-specific data

  -- Performance
  duration_seconds INTEGER,
  success BOOLEAN,

  occurred_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feature_usage_user ON feature_usage(user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_feature_usage_feature ON feature_usage(feature_name, occurred_at DESC);

-- ============================================
-- PART 9: User Feedback & Support
-- ============================================

CREATE TABLE IF NOT EXISTS user_feedback (
  feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),

  -- Feedback Type
  feedback_type VARCHAR(50) NOT NULL, -- "bug", "feature_request", "complaint", "praise", "other"
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),

  -- Content
  title VARCHAR(255),
  description TEXT NOT NULL,
  screenshot_urls TEXT[],

  -- Context
  page_url TEXT,
  browser_info TEXT,

  -- Status
  status VARCHAR(50) DEFAULT 'new', -- "new", "in_progress", "resolved", "closed"
  admin_response TEXT,
  responded_at TIMESTAMP,

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON user_feedback(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON user_feedback(status);

-- ============================================
-- PART 10: A/B Testing & Experiments
-- ============================================

CREATE TABLE IF NOT EXISTS ab_test_assignments (
  assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),

  -- Experiment Info
  experiment_key VARCHAR(100) NOT NULL, -- "onboarding_v2", "pricing_page_test", etc.
  variant VARCHAR(50) NOT NULL, -- "control", "variant_a", "variant_b", etc.

  -- Outcome Tracking
  converted BOOLEAN DEFAULT FALSE,
  conversion_value FLOAT,
  conversion_at TIMESTAMP,

  assigned_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, experiment_key)
);

CREATE INDEX IF NOT EXISTS idx_ab_tests_experiment ON ab_test_assignments(experiment_key, variant);

-- ============================================
-- PART 11: Notification Preferences
-- ============================================

CREATE TABLE IF NOT EXISTS notification_preferences (
  preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) UNIQUE,

  -- Email Notifications
  email_daily_reminder BOOLEAN DEFAULT TRUE,
  email_weekly_progress BOOLEAN DEFAULT TRUE,
  email_achievements BOOLEAN DEFAULT TRUE,
  email_tips BOOLEAN DEFAULT TRUE,
  email_product_updates BOOLEAN DEFAULT TRUE,
  email_marketing BOOLEAN DEFAULT TRUE,

  -- In-App Notifications
  inapp_streak_reminder BOOLEAN DEFAULT TRUE,
  inapp_goal_completion BOOLEAN DEFAULT TRUE,
  inapp_new_lessons BOOLEAN DEFAULT TRUE,

  -- Push Notifications (for future mobile app)
  push_enabled BOOLEAN DEFAULT FALSE,
  push_daily_reminder BOOLEAN DEFAULT FALSE,
  push_streak_risk BOOLEAN DEFAULT FALSE,

  -- Preferred Times
  reminder_time TIME DEFAULT '09:00:00',
  reminder_timezone VARCHAR(50),

  updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- PART 12: Support Functions
-- ============================================

-- Function to update user's last active time
CREATE OR REPLACE FUNCTION update_last_active()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE user_profiles
  SET last_active_at = NOW()
  WHERE user_id = NEW.user_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on sessions to update last_active_at
CREATE TRIGGER trigger_update_last_active
AFTER INSERT ON sessions
FOR EACH ROW
EXECUTE FUNCTION update_last_active();

-- Function to update streak
CREATE OR REPLACE FUNCTION update_user_streak(p_user_id UUID)
RETURNS VOID AS $$
DECLARE
  v_last_activity DATE;
  v_current_streak INTEGER;
BEGIN
  SELECT last_activity_date, current_streak_days
  INTO v_last_activity, v_current_streak
  FROM user_streaks
  WHERE user_id = p_user_id;

  IF v_last_activity IS NULL THEN
    -- First time activity
    INSERT INTO user_streaks (user_id, current_streak_days, longest_streak_days, current_streak_start_date, last_activity_date, total_days_active)
    VALUES (p_user_id, 1, 1, CURRENT_DATE, CURRENT_DATE, 1);
  ELSIF v_last_activity = CURRENT_DATE THEN
    -- Already logged activity today, do nothing
    RETURN;
  ELSIF v_last_activity = CURRENT_DATE - INTERVAL '1 day' THEN
    -- Continuing streak
    UPDATE user_streaks
    SET current_streak_days = current_streak_days + 1,
        longest_streak_days = GREATEST(longest_streak_days, current_streak_days + 1),
        last_activity_date = CURRENT_DATE,
        total_days_active = total_days_active + 1
    WHERE user_id = p_user_id;
  ELSE
    -- Streak broken
    UPDATE user_streaks
    SET current_streak_days = 1,
        current_streak_start_date = CURRENT_DATE,
        last_activity_date = CURRENT_DATE,
        total_days_active = total_days_active + 1
    WHERE user_id = p_user_id;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update streaks
CREATE OR REPLACE FUNCTION auto_update_streak()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM update_user_streak(NEW.user_id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_update_streak
AFTER INSERT ON sessions
FOR EACH ROW
EXECUTE FUNCTION auto_update_streak();

-- ============================================
-- PART 13: Analytics Views (for easy querying)
-- ============================================

-- User engagement summary view
CREATE OR REPLACE VIEW user_engagement_summary AS
SELECT
  up.user_id,
  up.full_name,
  up.level,
  up.subscription_tier,
  up.created_at AS signup_date,
  up.last_active_at,
  up.total_study_time_minutes,
  us.current_streak_days,
  us.longest_streak_days,
  COUNT(DISTINCT s.session_id) AS total_sessions,
  COUNT(DISTINCT e.error_id) AS total_errors_made,
  COUNT(DISTINCT sr.review_id) AS total_reviews_done,
  COUNT(DISTINCT ua.achievement_id) AS achievements_unlocked
FROM user_profiles up
LEFT JOIN user_streaks us ON up.user_id = us.user_id
LEFT JOIN sessions s ON up.user_id = s.user_id
LEFT JOIN error_log e ON up.user_id = e.user_id
LEFT JOIN srs_reviews sr ON up.user_id = sr.user_id
LEFT JOIN user_achievements ua ON up.user_id = ua.user_id
GROUP BY up.user_id, us.current_streak_days, us.longest_streak_days;

-- Daily active users view
CREATE OR REPLACE VIEW daily_active_users AS
SELECT
  DATE(last_active_at) AS date,
  COUNT(DISTINCT user_id) AS active_users
FROM user_profiles
WHERE last_active_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(last_active_at)
ORDER BY date DESC;

-- Feature popularity view
CREATE OR REPLACE VIEW feature_popularity AS
SELECT
  feature_name,
  COUNT(*) AS total_uses,
  COUNT(DISTINCT user_id) AS unique_users,
  AVG(duration_seconds) AS avg_duration_seconds,
  SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS success_rate
FROM feature_usage
WHERE occurred_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY feature_name
ORDER BY total_uses DESC;

-- ============================================
-- Done!
-- ============================================

SELECT 'Migration 001 completed successfully!' AS status;
