-- Migration 011: Daily Challenges System
-- 3 fixed slots: Core (volume), Accuracy (quality), Stretch (bonus)

-- Daily Challenges for each user per day
CREATE TABLE IF NOT EXISTS daily_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  challenge_date DATE NOT NULL,

  -- Core Challenge: Complete 2 lessons
  core_target INTEGER DEFAULT 2,
  core_progress INTEGER DEFAULT 0,
  core_completed BOOLEAN DEFAULT FALSE,
  core_completed_at TIMESTAMP,
  core_xp_reward INTEGER DEFAULT 15,

  -- Accuracy Challenge: Score 80%+ on any lesson
  accuracy_target INTEGER DEFAULT 80,  -- percentage
  accuracy_progress INTEGER DEFAULT 0,  -- best score today
  accuracy_completed BOOLEAN DEFAULT FALSE,
  accuracy_completed_at TIMESTAMP,
  accuracy_xp_reward INTEGER DEFAULT 25,

  -- Stretch Challenge: Earn 60+ XP OR Complete 1 speaking session
  stretch_xp_target INTEGER DEFAULT 60,
  stretch_xp_progress INTEGER DEFAULT 0,
  stretch_speaking_target INTEGER DEFAULT 1,
  stretch_speaking_progress INTEGER DEFAULT 0,
  stretch_completed BOOLEAN DEFAULT FALSE,
  stretch_completed_at TIMESTAMP,
  stretch_xp_reward INTEGER DEFAULT 50,
  stretch_gives_freeze_token BOOLEAN DEFAULT TRUE,

  -- Overall status
  all_completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, challenge_date)
);

CREATE INDEX idx_daily_challenges_user_date ON daily_challenges(user_id, challenge_date DESC);

-- Streak Freeze Tokens (earned from completing stretch challenges)
CREATE TABLE IF NOT EXISTS streak_freeze_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  earned_at TIMESTAMP DEFAULT NOW(),
  used_at TIMESTAMP,
  used BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_streak_freeze_tokens_user ON streak_freeze_tokens(user_id, used);

-- Function to get or create today's challenges
CREATE OR REPLACE FUNCTION get_or_create_daily_challenges(p_user_id UUID)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  challenge_date DATE,
  core_target INTEGER,
  core_progress INTEGER,
  core_completed BOOLEAN,
  core_xp_reward INTEGER,
  accuracy_target INTEGER,
  accuracy_progress INTEGER,
  accuracy_completed BOOLEAN,
  accuracy_xp_reward INTEGER,
  stretch_xp_target INTEGER,
  stretch_xp_progress INTEGER,
  stretch_speaking_target INTEGER,
  stretch_speaking_progress INTEGER,
  stretch_completed BOOLEAN,
  stretch_xp_reward INTEGER,
  all_completed BOOLEAN
)
AS $$
DECLARE
  v_today DATE := CURRENT_DATE;
BEGIN
  -- Insert if not exists
  INSERT INTO daily_challenges (user_id, challenge_date)
  VALUES (p_user_id, v_today)
  ON CONFLICT (user_id, challenge_date) DO NOTHING;

  -- Return the challenges
  RETURN QUERY
  SELECT
    dc.id, dc.user_id, dc.challenge_date,
    dc.core_target, dc.core_progress, dc.core_completed, dc.core_xp_reward,
    dc.accuracy_target, dc.accuracy_progress, dc.accuracy_completed, dc.accuracy_xp_reward,
    dc.stretch_xp_target, dc.stretch_xp_progress, dc.stretch_speaking_target,
    dc.stretch_speaking_progress, dc.stretch_completed, dc.stretch_xp_reward,
    dc.all_completed
  FROM daily_challenges dc
  WHERE dc.user_id = p_user_id AND dc.challenge_date = v_today;
END;
$$ LANGUAGE plpgsql;

-- Function to update challenge progress
CREATE OR REPLACE FUNCTION update_challenge_progress(
  p_user_id UUID,
  p_lessons_completed INTEGER DEFAULT 0,
  p_best_score INTEGER DEFAULT 0,
  p_xp_earned INTEGER DEFAULT 0,
  p_speaking_sessions INTEGER DEFAULT 0
)
RETURNS TABLE (
  core_just_completed BOOLEAN,
  accuracy_just_completed BOOLEAN,
  stretch_just_completed BOOLEAN,
  total_xp_earned INTEGER,
  earned_freeze_token BOOLEAN
)
AS $$
DECLARE
  v_today DATE := CURRENT_DATE;
  v_challenge RECORD;
  v_core_just_completed BOOLEAN := FALSE;
  v_accuracy_just_completed BOOLEAN := FALSE;
  v_stretch_just_completed BOOLEAN := FALSE;
  v_total_xp INTEGER := 0;
  v_earned_freeze BOOLEAN := FALSE;
BEGIN
  -- Ensure today's challenges exist
  INSERT INTO daily_challenges (user_id, challenge_date)
  VALUES (p_user_id, v_today)
  ON CONFLICT (user_id, challenge_date) DO NOTHING;

  -- Get current state
  SELECT * INTO v_challenge
  FROM daily_challenges
  WHERE user_id = p_user_id AND challenge_date = v_today;

  -- Update Core Challenge (lessons completed)
  IF NOT v_challenge.core_completed AND p_lessons_completed > 0 THEN
    UPDATE daily_challenges
    SET core_progress = core_progress + p_lessons_completed,
        updated_at = NOW()
    WHERE id = v_challenge.id;

    -- Check if just completed
    IF v_challenge.core_progress + p_lessons_completed >= v_challenge.core_target THEN
      UPDATE daily_challenges
      SET core_completed = TRUE, core_completed_at = NOW()
      WHERE id = v_challenge.id;
      v_core_just_completed := TRUE;
      v_total_xp := v_total_xp + v_challenge.core_xp_reward;
    END IF;
  END IF;

  -- Update Accuracy Challenge (best score)
  IF NOT v_challenge.accuracy_completed AND p_best_score > 0 THEN
    UPDATE daily_challenges
    SET accuracy_progress = GREATEST(accuracy_progress, p_best_score),
        updated_at = NOW()
    WHERE id = v_challenge.id;

    -- Check if just completed (score >= 80%)
    IF p_best_score >= v_challenge.accuracy_target THEN
      UPDATE daily_challenges
      SET accuracy_completed = TRUE, accuracy_completed_at = NOW()
      WHERE id = v_challenge.id;
      v_accuracy_just_completed := TRUE;
      v_total_xp := v_total_xp + v_challenge.accuracy_xp_reward;
    END IF;
  END IF;

  -- Update Stretch Challenge (XP or speaking)
  IF NOT v_challenge.stretch_completed THEN
    UPDATE daily_challenges
    SET stretch_xp_progress = stretch_xp_progress + p_xp_earned,
        stretch_speaking_progress = stretch_speaking_progress + p_speaking_sessions,
        updated_at = NOW()
    WHERE id = v_challenge.id;

    -- Check if just completed (XP target OR speaking target)
    IF v_challenge.stretch_xp_progress + p_xp_earned >= v_challenge.stretch_xp_target
       OR v_challenge.stretch_speaking_progress + p_speaking_sessions >= v_challenge.stretch_speaking_target THEN
      UPDATE daily_challenges
      SET stretch_completed = TRUE, stretch_completed_at = NOW()
      WHERE id = v_challenge.id;
      v_stretch_just_completed := TRUE;
      v_total_xp := v_total_xp + v_challenge.stretch_xp_reward;

      -- Grant streak freeze token
      IF v_challenge.stretch_gives_freeze_token THEN
        INSERT INTO streak_freeze_tokens (user_id) VALUES (p_user_id);
        v_earned_freeze := TRUE;
      END IF;
    END IF;
  END IF;

  -- Check if all completed
  UPDATE daily_challenges
  SET all_completed = (core_completed AND accuracy_completed AND stretch_completed)
  WHERE id = v_challenge.id;

  RETURN QUERY SELECT v_core_just_completed, v_accuracy_just_completed, v_stretch_just_completed, v_total_xp, v_earned_freeze;
END;
$$ LANGUAGE plpgsql;

-- Function to get available streak freeze tokens
CREATE OR REPLACE FUNCTION get_streak_freeze_count(p_user_id UUID)
RETURNS INTEGER
AS $$
BEGIN
  RETURN (SELECT COUNT(*) FROM streak_freeze_tokens WHERE user_id = p_user_id AND used = FALSE);
END;
$$ LANGUAGE plpgsql;

-- Function to use a streak freeze token
CREATE OR REPLACE FUNCTION use_streak_freeze_token(p_user_id UUID)
RETURNS BOOLEAN
AS $$
DECLARE
  v_token_id UUID;
BEGIN
  SELECT id INTO v_token_id
  FROM streak_freeze_tokens
  WHERE user_id = p_user_id AND used = FALSE
  ORDER BY earned_at ASC
  LIMIT 1;

  IF v_token_id IS NULL THEN
    RETURN FALSE;
  END IF;

  UPDATE streak_freeze_tokens
  SET used = TRUE, used_at = NOW()
  WHERE id = v_token_id;

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
