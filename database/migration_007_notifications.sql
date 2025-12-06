-- Migration 007: User Notifications System
-- Creates table and functions for in-app notifications

-- ============================================
-- PART 1: Create notifications table
-- ============================================

CREATE TABLE IF NOT EXISTS user_notifications (
  notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL, -- 'streak_risk', 'achievement', 'goal_complete', 'weekly_summary', 'reminder', 'level_up'
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  read BOOLEAN DEFAULT FALSE,
  action_url TEXT, -- Optional link to relevant page (e.g., "/achievements", "/review")
  metadata JSONB, -- Additional data (achievement details, goal stats, etc.)
  created_at TIMESTAMP DEFAULT NOW(),
  read_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON user_notifications(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON user_notifications(user_id, read, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON user_notifications(type);

-- ============================================
-- PART 2: Functions for notification management
-- ============================================

-- Function to get unread count for a user
CREATE OR REPLACE FUNCTION get_unread_notification_count(p_user_id UUID)
RETURNS INTEGER
AS $$
BEGIN
  RETURN (
    SELECT COUNT(*)
    FROM user_notifications
    WHERE user_id = p_user_id AND read = FALSE
  );
END;
$$ LANGUAGE plpgsql;

-- Function to mark notification as read
CREATE OR REPLACE FUNCTION mark_notification_read(p_notification_id UUID)
RETURNS VOID
AS $$
BEGIN
  UPDATE user_notifications
  SET read = TRUE, read_at = NOW()
  WHERE notification_id = p_notification_id AND read = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to mark all notifications as read for a user
CREATE OR REPLACE FUNCTION mark_all_notifications_read(p_user_id UUID)
RETURNS INTEGER
AS $$
DECLARE
  v_updated_count INTEGER;
BEGIN
  UPDATE user_notifications
  SET read = TRUE, read_at = NOW()
  WHERE user_id = p_user_id AND read = FALSE;

  GET DIAGNOSTICS v_updated_count = ROW_COUNT;
  RETURN v_updated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to create a notification
CREATE OR REPLACE FUNCTION create_notification(
  p_user_id UUID,
  p_type VARCHAR,
  p_title VARCHAR,
  p_message TEXT,
  p_action_url TEXT DEFAULT NULL,
  p_metadata JSONB DEFAULT NULL
)
RETURNS UUID
AS $$
DECLARE
  v_notification_id UUID;
BEGIN
  INSERT INTO user_notifications (user_id, type, title, message, action_url, metadata)
  VALUES (p_user_id, p_type, p_title, p_message, p_action_url, p_metadata)
  RETURNING notification_id INTO v_notification_id;

  RETURN v_notification_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old read notifications (optional - for maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_notifications(p_days_old INTEGER DEFAULT 30)
RETURNS INTEGER
AS $$
DECLARE
  v_deleted_count INTEGER;
BEGIN
  DELETE FROM user_notifications
  WHERE read = TRUE
    AND read_at < NOW() - (p_days_old || ' days')::INTERVAL;

  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
  RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- PART 3: Trigger functions for auto-notifications
-- ============================================

-- Trigger function: Notify on achievement unlock
CREATE OR REPLACE FUNCTION notify_achievement_unlocked()
RETURNS TRIGGER
AS $$
DECLARE
  v_achievement RECORD;
BEGIN
  -- Get achievement details
  SELECT title, description, points, icon
  INTO v_achievement
  FROM achievements
  WHERE achievement_id = NEW.achievement_id;

  -- Create notification
  PERFORM create_notification(
    NEW.user_id,
    'achievement',
    'Achievement Unlocked!',
    'You earned "' || v_achievement.title || '" (+' || v_achievement.points || ' XP)',
    '/achievements',
    jsonb_build_object(
      'achievement_id', NEW.achievement_id,
      'title', v_achievement.title,
      'points', v_achievement.points,
      'icon', v_achievement.icon
    )
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for achievement unlocks
DROP TRIGGER IF EXISTS trigger_notify_achievement ON user_achievements;
CREATE TRIGGER trigger_notify_achievement
  AFTER INSERT ON user_achievements
  FOR EACH ROW
  EXECUTE FUNCTION notify_achievement_unlocked();

-- Trigger function: Notify on daily goal completion
CREATE OR REPLACE FUNCTION notify_daily_goal_complete()
RETURNS TRIGGER
AS $$
BEGIN
  -- Only notify when goal becomes completed (wasn't completed before)
  IF NEW.completed = TRUE AND (OLD.completed IS NULL OR OLD.completed = FALSE) THEN
    PERFORM create_notification(
      NEW.user_id,
      'goal_complete',
      'Daily Goal Completed!',
      'Great job! You completed all your daily goals for ' || TO_CHAR(NEW.goal_date, 'Month DD') || '!',
      '/dashboard',
      jsonb_build_object(
        'goal_date', NEW.goal_date,
        'study_minutes', NEW.actual_study_minutes,
        'lessons', NEW.actual_lessons,
        'reviews', NEW.actual_reviews,
        'drills', NEW.actual_drills
      )
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for daily goal completion
DROP TRIGGER IF EXISTS trigger_notify_goal_complete ON daily_goals;
CREATE TRIGGER trigger_notify_goal_complete
  AFTER UPDATE ON daily_goals
  FOR EACH ROW
  EXECUTE FUNCTION notify_daily_goal_complete();

-- Trigger function: Notify on streak milestone
CREATE OR REPLACE FUNCTION notify_streak_milestone()
RETURNS TRIGGER
AS $$
BEGIN
  -- Notify on streak milestones: 7, 14, 30, 50, 100 days
  IF NEW.current_streak_days IN (7, 14, 30, 50, 100) AND
     (OLD.current_streak_days IS NULL OR OLD.current_streak_days != NEW.current_streak_days) THEN
    PERFORM create_notification(
      NEW.user_id,
      'streak_milestone',
      NEW.current_streak_days || '-Day Streak!',
      'Amazing! You are on fire with a ' || NEW.current_streak_days || '-day learning streak!',
      '/dashboard',
      jsonb_build_object(
        'streak_days', NEW.current_streak_days,
        'longest_streak', NEW.longest_streak_days
      )
    );
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for streak milestones
DROP TRIGGER IF EXISTS trigger_notify_streak_milestone ON user_streaks;
CREATE TRIGGER trigger_notify_streak_milestone
  AFTER UPDATE ON user_streaks
  FOR EACH ROW
  EXECUTE FUNCTION notify_streak_milestone();

-- ============================================
-- PART 4: Level up notification function
-- ============================================

-- This will be called manually from application code when user levels up
CREATE OR REPLACE FUNCTION notify_level_up(
  p_user_id UUID,
  p_old_level VARCHAR,
  p_new_level VARCHAR
)
RETURNS VOID
AS $$
BEGIN
  PERFORM create_notification(
    p_user_id,
    'level_up',
    'Level Up!',
    'Congratulations! You advanced from ' || p_old_level || ' to ' || p_new_level || '!',
    '/dashboard',
    jsonb_build_object(
      'old_level', p_old_level,
      'new_level', p_new_level
    )
  );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- PART 5: Streak risk notification
-- ============================================

-- Function to check and notify users at risk of losing streak
-- This should be called daily via cron job or scheduled task
CREATE OR REPLACE FUNCTION check_and_notify_streak_risk()
RETURNS INTEGER
AS $$
DECLARE
  v_user RECORD;
  v_notification_count INTEGER := 0;
  v_hours_since_activity INTEGER;
BEGIN
  -- Find users who haven't been active today and have a streak
  FOR v_user IN
    SELECT
      us.user_id,
      us.current_streak_days,
      us.last_activity_date,
      EXTRACT(EPOCH FROM (NOW() - COALESCE(us.last_activity_date, NOW())))::INTEGER / 3600 AS hours_since_activity
    FROM user_streaks us
    WHERE us.current_streak_days > 0
      AND us.last_activity_date < CURRENT_DATE
      -- Don't spam: only notify if no recent streak_risk notification
      AND NOT EXISTS (
        SELECT 1 FROM user_notifications
        WHERE user_id = us.user_id
          AND type = 'streak_risk'
          AND created_at > NOW() - INTERVAL '12 hours'
      )
  LOOP
    -- Only notify if it's been 20+ hours since last activity
    IF v_user.hours_since_activity >= 20 THEN
      PERFORM create_notification(
        v_user.user_id,
        'streak_risk',
        'Don''t Break Your Streak!',
        'Your ' || v_user.current_streak_days || '-day streak is at risk! Complete a quick activity today to keep it going.',
        '/',
        jsonb_build_object(
          'streak_days', v_user.current_streak_days,
          'hours_remaining', 24 - v_user.hours_since_activity
        )
      );
      v_notification_count := v_notification_count + 1;
    END IF;
  END LOOP;

  RETURN v_notification_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- SUCCESS MESSAGE
-- ============================================

DO $$
BEGIN
  RAISE NOTICE 'Migration 007: Notifications system created successfully!';
  RAISE NOTICE 'Created: user_notifications table';
  RAISE NOTICE 'Created: Helper functions for notification management';
  RAISE NOTICE 'Created: Triggers for auto-notifications (achievements, goals, streaks)';
  RAISE NOTICE 'Note: Run check_and_notify_streak_risk() daily via cron for streak reminders';
END $$;
