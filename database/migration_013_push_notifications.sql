-- Migration 013: Push Notifications System
-- Web Push API subscriptions and preferences

-- Push subscriptions table
CREATE TABLE IF NOT EXISTS push_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL UNIQUE,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  last_used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_push_subscriptions_user ON push_subscriptions(user_id);
CREATE INDEX idx_push_subscriptions_endpoint ON push_subscriptions(endpoint);

-- Push notification preferences table
CREATE TABLE IF NOT EXISTS push_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE UNIQUE,
  enabled BOOLEAN DEFAULT FALSE,
  streak_reminders BOOLEAN DEFAULT TRUE,
  friend_challenges BOOLEAN DEFAULT TRUE,
  achievements BOOLEAN DEFAULT TRUE,
  daily_goals BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_push_preferences_user ON push_preferences(user_id);

-- Function to get or create push preferences for a user
CREATE OR REPLACE FUNCTION get_or_create_push_preferences(p_user_id UUID)
RETURNS TABLE (
  enabled BOOLEAN,
  streak_reminders BOOLEAN,
  friend_challenges BOOLEAN,
  achievements BOOLEAN,
  daily_goals BOOLEAN
)
AS $$
BEGIN
  -- Insert default preferences if not exists
  INSERT INTO push_preferences (user_id)
  VALUES (p_user_id)
  ON CONFLICT (user_id) DO NOTHING;

  -- Return preferences
  RETURN QUERY
  SELECT
    pp.enabled,
    pp.streak_reminders,
    pp.friend_challenges,
    pp.achievements,
    pp.daily_goals
  FROM push_preferences pp
  WHERE pp.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update push preferences
CREATE OR REPLACE FUNCTION update_push_preferences(
  p_user_id UUID,
  p_enabled BOOLEAN DEFAULT NULL,
  p_streak_reminders BOOLEAN DEFAULT NULL,
  p_friend_challenges BOOLEAN DEFAULT NULL,
  p_achievements BOOLEAN DEFAULT NULL,
  p_daily_goals BOOLEAN DEFAULT NULL
)
RETURNS TABLE (
  enabled BOOLEAN,
  streak_reminders BOOLEAN,
  friend_challenges BOOLEAN,
  achievements BOOLEAN,
  daily_goals BOOLEAN
)
AS $$
BEGIN
  -- Ensure preferences exist
  INSERT INTO push_preferences (user_id)
  VALUES (p_user_id)
  ON CONFLICT (user_id) DO NOTHING;

  -- Update preferences (only non-null values)
  UPDATE push_preferences SET
    enabled = COALESCE(p_enabled, push_preferences.enabled),
    streak_reminders = COALESCE(p_streak_reminders, push_preferences.streak_reminders),
    friend_challenges = COALESCE(p_friend_challenges, push_preferences.friend_challenges),
    achievements = COALESCE(p_achievements, push_preferences.achievements),
    daily_goals = COALESCE(p_daily_goals, push_preferences.daily_goals),
    updated_at = NOW()
  WHERE user_id = p_user_id;

  -- Return updated preferences
  RETURN QUERY
  SELECT
    pp.enabled,
    pp.streak_reminders,
    pp.friend_challenges,
    pp.achievements,
    pp.daily_goals
  FROM push_preferences pp
  WHERE pp.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get users to notify for a specific event type
CREATE OR REPLACE FUNCTION get_users_for_push_notification(
  p_user_ids UUID[],
  p_notification_type VARCHAR
)
RETURNS TABLE (
  user_id UUID,
  endpoint TEXT,
  p256dh TEXT,
  auth TEXT
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    ps.user_id,
    ps.endpoint,
    ps.p256dh,
    ps.auth
  FROM push_subscriptions ps
  JOIN push_preferences pp ON pp.user_id = ps.user_id
  WHERE ps.user_id = ANY(p_user_ids)
    AND pp.enabled = TRUE
    AND (
      (p_notification_type = 'streak_reminder' AND pp.streak_reminders = TRUE) OR
      (p_notification_type = 'friend_challenge' AND pp.friend_challenges = TRUE) OR
      (p_notification_type = 'achievement' AND pp.achievements = TRUE) OR
      (p_notification_type = 'daily_goal' AND pp.daily_goals = TRUE) OR
      (p_notification_type = 'test') -- Always allow test notifications
    );
END;
$$ LANGUAGE plpgsql;

-- Add trigger to create friend challenge notification
CREATE OR REPLACE FUNCTION notify_friend_challenge_received()
RETURNS TRIGGER
AS $$
DECLARE
  v_challenger_name TEXT;
  v_challenge_label TEXT;
BEGIN
  -- Get challenger's name
  SELECT COALESCE(display_name, username, 'Someone')
  INTO v_challenger_name
  FROM user_profiles
  WHERE user_id = NEW.challenger_id;

  -- Get challenge type label
  IF NEW.challenge_type = 'beat_xp_today' THEN
    v_challenge_label := 'XP challenge';
  ELSE
    v_challenge_label := 'lessons challenge';
  END IF;

  -- Create in-app notification
  PERFORM create_notification(
    NEW.challenged_id,
    'friend_challenge',
    'Challenge Received!',
    v_challenger_name || ' has challenged you to a ' || v_challenge_label || '!',
    '/friends',
    jsonb_build_object(
      'challenge_id', NEW.id,
      'challenger_id', NEW.challenger_id,
      'challenger_name', v_challenger_name,
      'challenge_type', NEW.challenge_type,
      'xp_reward', NEW.xp_reward
    )
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for friend challenge notifications
DROP TRIGGER IF EXISTS trigger_notify_friend_challenge ON friend_challenges;
CREATE TRIGGER trigger_notify_friend_challenge
  AFTER INSERT ON friend_challenges
  FOR EACH ROW
  EXECUTE FUNCTION notify_friend_challenge_received();

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'Migration 013: Push notifications system created successfully!';
  RAISE NOTICE 'Created: push_subscriptions table';
  RAISE NOTICE 'Created: push_preferences table';
  RAISE NOTICE 'Created: Helper functions for push notification management';
  RAISE NOTICE 'Created: Trigger for friend challenge push notifications';
END $$;
