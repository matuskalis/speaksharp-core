-- Migration 014: Gamification Bonuses System
-- Daily login bonuses, streak multipliers, weekend bonuses, perfect score bonuses

-- Daily bonus claims tracking
CREATE TABLE IF NOT EXISTS daily_bonus_claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  bonus_type VARCHAR(30) NOT NULL, -- 'login', 'first_lesson', 'streak', 'weekend', 'perfect_score'
  bonus_xp INTEGER NOT NULL,
  multiplier DECIMAL(3,2) DEFAULT 1.0,
  claimed_date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(user_id, bonus_type, claimed_date)
);

CREATE INDEX idx_daily_bonus_user_date ON daily_bonus_claims(user_id, claimed_date);

-- XP multiplier events (for special events like double XP weekends)
CREATE TABLE IF NOT EXISTS xp_multiplier_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  description TEXT,
  multiplier DECIMAL(3,2) NOT NULL DEFAULT 2.0,
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_xp_events_active ON xp_multiplier_events(is_active, start_date, end_date);

-- Function to get active XP bonuses for a user
CREATE OR REPLACE FUNCTION get_active_bonuses(p_user_id UUID)
RETURNS TABLE (
  login_bonus_available BOOLEAN,
  login_bonus_xp INTEGER,
  streak_multiplier DECIMAL(3,2),
  streak_days INTEGER,
  weekend_bonus_active BOOLEAN,
  weekend_multiplier DECIMAL(3,2),
  event_bonus_active BOOLEAN,
  event_name VARCHAR,
  event_multiplier DECIMAL(3,2),
  total_multiplier DECIMAL(4,2)
)
AS $$
DECLARE
  v_streak_days INTEGER;
  v_streak_mult DECIMAL(3,2);
  v_weekend_mult DECIMAL(3,2);
  v_event_mult DECIMAL(3,2);
  v_event_name VARCHAR;
  v_login_claimed BOOLEAN;
  v_is_weekend BOOLEAN;
  v_has_event BOOLEAN;
BEGIN
  -- Get current streak
  SELECT COALESCE(us.current_streak_days, 0)
  INTO v_streak_days
  FROM user_streaks us
  WHERE us.user_id = p_user_id;

  -- Calculate streak multiplier (1.0 + 0.01 per streak day, max 1.5)
  v_streak_mult := LEAST(1.0 + (COALESCE(v_streak_days, 0) * 0.01), 1.5);

  -- Check if login bonus already claimed today
  SELECT EXISTS(
    SELECT 1 FROM daily_bonus_claims
    WHERE user_id = p_user_id
      AND bonus_type = 'login'
      AND claimed_date = CURRENT_DATE
  ) INTO v_login_claimed;

  -- Check if it's weekend (Saturday or Sunday)
  v_is_weekend := EXTRACT(DOW FROM CURRENT_DATE) IN (0, 6);
  v_weekend_mult := CASE WHEN v_is_weekend THEN 1.5 ELSE 1.0 END;

  -- Check for active XP events
  SELECT name, multiplier
  INTO v_event_name, v_event_mult
  FROM xp_multiplier_events
  WHERE is_active = TRUE
    AND NOW() BETWEEN start_date AND end_date
  ORDER BY multiplier DESC
  LIMIT 1;

  v_has_event := v_event_name IS NOT NULL;
  v_event_mult := COALESCE(v_event_mult, 1.0);

  RETURN QUERY SELECT
    NOT v_login_claimed AS login_bonus_available,
    25 AS login_bonus_xp, -- Base login bonus
    v_streak_mult AS streak_multiplier,
    COALESCE(v_streak_days, 0) AS streak_days,
    v_is_weekend AS weekend_bonus_active,
    v_weekend_mult AS weekend_multiplier,
    v_has_event AS event_bonus_active,
    v_event_name AS event_name,
    v_event_mult AS event_multiplier,
    -- Total multiplier: streak * weekend * event (multiplicative)
    ROUND((v_streak_mult * v_weekend_mult * v_event_mult)::NUMERIC, 2) AS total_multiplier;
END;
$$ LANGUAGE plpgsql;

-- Function to claim daily login bonus
CREATE OR REPLACE FUNCTION claim_login_bonus(p_user_id UUID)
RETURNS TABLE (
  success BOOLEAN,
  xp_earned INTEGER,
  message TEXT
)
AS $$
DECLARE
  v_already_claimed BOOLEAN;
  v_base_xp INTEGER := 25;
  v_streak_mult DECIMAL(3,2);
  v_total_xp INTEGER;
BEGIN
  -- Check if already claimed
  SELECT EXISTS(
    SELECT 1 FROM daily_bonus_claims
    WHERE user_id = p_user_id
      AND bonus_type = 'login'
      AND claimed_date = CURRENT_DATE
  ) INTO v_already_claimed;

  IF v_already_claimed THEN
    RETURN QUERY SELECT FALSE, 0, 'Login bonus already claimed today'::TEXT;
    RETURN;
  END IF;

  -- Get streak multiplier
  SELECT LEAST(1.0 + (COALESCE(us.current_streak_days, 0) * 0.01), 1.5)
  INTO v_streak_mult
  FROM user_streaks us
  WHERE us.user_id = p_user_id;

  v_streak_mult := COALESCE(v_streak_mult, 1.0);
  v_total_xp := FLOOR(v_base_xp * v_streak_mult);

  -- Record the claim
  INSERT INTO daily_bonus_claims (user_id, bonus_type, bonus_xp, multiplier)
  VALUES (p_user_id, 'login', v_total_xp, v_streak_mult);

  -- Add XP to user
  UPDATE user_profiles
  SET total_xp = total_xp + v_total_xp
  WHERE user_id = p_user_id;

  RETURN QUERY SELECT TRUE, v_total_xp, ('Daily login bonus: +' || v_total_xp || ' XP')::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate XP with all bonuses
CREATE OR REPLACE FUNCTION calculate_bonus_xp(
  p_user_id UUID,
  p_base_xp INTEGER,
  p_is_perfect_score BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
  final_xp INTEGER,
  bonus_breakdown JSONB
)
AS $$
DECLARE
  v_streak_mult DECIMAL(3,2);
  v_weekend_mult DECIMAL(3,2);
  v_event_mult DECIMAL(3,2);
  v_perfect_mult DECIMAL(3,2);
  v_final_xp INTEGER;
  v_breakdown JSONB;
BEGIN
  -- Get streak multiplier
  SELECT LEAST(1.0 + (COALESCE(us.current_streak_days, 0) * 0.01), 1.5)
  INTO v_streak_mult
  FROM user_streaks us
  WHERE us.user_id = p_user_id;
  v_streak_mult := COALESCE(v_streak_mult, 1.0);

  -- Weekend multiplier
  v_weekend_mult := CASE WHEN EXTRACT(DOW FROM CURRENT_DATE) IN (0, 6) THEN 1.5 ELSE 1.0 END;

  -- Event multiplier
  SELECT COALESCE(MAX(multiplier), 1.0)
  INTO v_event_mult
  FROM xp_multiplier_events
  WHERE is_active = TRUE AND NOW() BETWEEN start_date AND end_date;

  -- Perfect score multiplier
  v_perfect_mult := CASE WHEN p_is_perfect_score THEN 1.25 ELSE 1.0 END;

  -- Calculate final XP
  v_final_xp := FLOOR(p_base_xp * v_streak_mult * v_weekend_mult * v_event_mult * v_perfect_mult);

  -- Build breakdown
  v_breakdown := jsonb_build_object(
    'base_xp', p_base_xp,
    'streak_multiplier', v_streak_mult,
    'weekend_multiplier', v_weekend_mult,
    'event_multiplier', v_event_mult,
    'perfect_score_multiplier', v_perfect_mult,
    'final_xp', v_final_xp,
    'bonus_xp', v_final_xp - p_base_xp
  );

  RETURN QUERY SELECT v_final_xp, v_breakdown;
END;
$$ LANGUAGE plpgsql;

-- Function to get today's bonus summary for dashboard
CREATE OR REPLACE FUNCTION get_bonus_summary(p_user_id UUID)
RETURNS TABLE (
  total_bonus_xp_today INTEGER,
  bonuses_claimed JSONB,
  available_bonuses JSONB,
  current_multiplier DECIMAL(4,2)
)
AS $$
DECLARE
  v_claimed JSONB;
  v_available JSONB;
  v_total_bonus INTEGER;
  v_active_bonuses RECORD;
BEGIN
  -- Get claimed bonuses today
  SELECT jsonb_agg(jsonb_build_object(
    'type', bonus_type,
    'xp', bonus_xp,
    'multiplier', multiplier
  ))
  INTO v_claimed
  FROM daily_bonus_claims
  WHERE user_id = p_user_id AND claimed_date = CURRENT_DATE;

  -- Get total bonus XP today
  SELECT COALESCE(SUM(bonus_xp), 0)
  INTO v_total_bonus
  FROM daily_bonus_claims
  WHERE user_id = p_user_id AND claimed_date = CURRENT_DATE;

  -- Get active bonuses
  SELECT * INTO v_active_bonuses FROM get_active_bonuses(p_user_id);

  v_available := jsonb_build_object(
    'login_bonus', jsonb_build_object(
      'available', v_active_bonuses.login_bonus_available,
      'xp', v_active_bonuses.login_bonus_xp
    ),
    'streak_bonus', jsonb_build_object(
      'active', v_active_bonuses.streak_days > 0,
      'multiplier', v_active_bonuses.streak_multiplier,
      'streak_days', v_active_bonuses.streak_days
    ),
    'weekend_bonus', jsonb_build_object(
      'active', v_active_bonuses.weekend_bonus_active,
      'multiplier', v_active_bonuses.weekend_multiplier
    ),
    'event_bonus', jsonb_build_object(
      'active', v_active_bonuses.event_bonus_active,
      'name', v_active_bonuses.event_name,
      'multiplier', v_active_bonuses.event_multiplier
    )
  );

  RETURN QUERY SELECT
    v_total_bonus,
    COALESCE(v_claimed, '[]'::jsonb),
    v_available,
    v_active_bonuses.total_multiplier;
END;
$$ LANGUAGE plpgsql;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'Migration 014: Gamification bonuses system created successfully!';
  RAISE NOTICE 'Created: daily_bonus_claims table';
  RAISE NOTICE 'Created: xp_multiplier_events table';
  RAISE NOTICE 'Created: get_active_bonuses function';
  RAISE NOTICE 'Created: claim_login_bonus function';
  RAISE NOTICE 'Created: calculate_bonus_xp function';
  RAISE NOTICE 'Created: get_bonus_summary function';
END $$;
