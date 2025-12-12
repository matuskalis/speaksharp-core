-- Migration 012: Friends System
-- Username search, shareable invite links, async friend challenges

-- Friendships table (bidirectional - store both directions for easier queries)
CREATE TABLE IF NOT EXISTS friendships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  friend_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, blocked
  created_at TIMESTAMP DEFAULT NOW(),
  accepted_at TIMESTAMP,

  UNIQUE(user_id, friend_id),
  CHECK (user_id != friend_id)
);

CREATE INDEX idx_friendships_user ON friendships(user_id, status);
CREATE INDEX idx_friendships_friend ON friendships(friend_id, status);

-- Friend invite links (shareable codes)
CREATE TABLE IF NOT EXISTS friend_invite_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  invite_code VARCHAR(12) UNIQUE NOT NULL,
  uses_count INTEGER DEFAULT 0,
  max_uses INTEGER DEFAULT 10, -- null for unlimited
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_friend_invite_code ON friend_invite_links(invite_code) WHERE is_active = TRUE;

-- Friend challenges (async challenges between friends)
CREATE TABLE IF NOT EXISTS friend_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  challenger_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  challenged_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  challenge_type VARCHAR(30) NOT NULL, -- 'beat_xp_today', 'more_lessons_today'
  challenge_date DATE NOT NULL,

  -- Scores
  challenger_score INTEGER DEFAULT 0,
  challenged_score INTEGER DEFAULT 0,

  -- Status
  status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, declined, completed, expired
  winner_id UUID REFERENCES user_profiles(user_id),

  -- XP rewards
  xp_reward INTEGER DEFAULT 30,
  winner_claimed_xp BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMP DEFAULT NOW(),
  accepted_at TIMESTAMP,
  completed_at TIMESTAMP,

  UNIQUE(challenger_id, challenged_id, challenge_type, challenge_date)
);

CREATE INDEX idx_friend_challenges_challenger ON friend_challenges(challenger_id, status);
CREATE INDEX idx_friend_challenges_challenged ON friend_challenges(challenged_id, status);
CREATE INDEX idx_friend_challenges_date ON friend_challenges(challenge_date, status);

-- Add username to user_profiles if not exists (for search functionality)
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS username VARCHAR(30);
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS friend_code VARCHAR(8);

-- Create unique index on username (case-insensitive)
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(LOWER(username)) WHERE username IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_profiles_friend_code ON user_profiles(friend_code) WHERE friend_code IS NOT NULL;

-- Function to generate unique friend code
CREATE OR REPLACE FUNCTION generate_friend_code()
RETURNS VARCHAR(8)
AS $$
DECLARE
  chars TEXT := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  result VARCHAR(8) := '';
  i INTEGER;
BEGIN
  FOR i IN 1..8 LOOP
    result := result || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
  END LOOP;
  RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to ensure user has friend code
CREATE OR REPLACE FUNCTION ensure_friend_code(p_user_id UUID)
RETURNS VARCHAR(8)
AS $$
DECLARE
  v_code VARCHAR(8);
BEGIN
  -- Check if user already has a friend code
  SELECT friend_code INTO v_code FROM user_profiles WHERE user_id = p_user_id;

  IF v_code IS NOT NULL THEN
    RETURN v_code;
  END IF;

  -- Generate unique code
  LOOP
    v_code := generate_friend_code();
    BEGIN
      UPDATE user_profiles SET friend_code = v_code WHERE user_id = p_user_id;
      RETURN v_code;
    EXCEPTION WHEN unique_violation THEN
      -- Try again with different code
    END;
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to search users by username or friend code
CREATE OR REPLACE FUNCTION search_users(
  p_searcher_id UUID,
  p_query TEXT,
  p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  user_id UUID,
  username VARCHAR,
  display_name TEXT,
  friend_code VARCHAR,
  level INTEGER,
  total_xp INTEGER,
  streak_days INTEGER,
  is_friend BOOLEAN,
  friendship_status VARCHAR
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    up.user_id,
    up.username,
    up.display_name,
    up.friend_code,
    up.level,
    up.total_xp,
    COALESCE(us.streak_days, 0)::INTEGER as streak_days,
    EXISTS(
      SELECT 1 FROM friendships f
      WHERE ((f.user_id = p_searcher_id AND f.friend_id = up.user_id)
         OR (f.friend_id = p_searcher_id AND f.user_id = up.user_id))
        AND f.status = 'accepted'
    ) as is_friend,
    (
      SELECT f.status FROM friendships f
      WHERE (f.user_id = p_searcher_id AND f.friend_id = up.user_id)
         OR (f.friend_id = p_searcher_id AND f.user_id = up.user_id)
      LIMIT 1
    ) as friendship_status
  FROM user_profiles up
  LEFT JOIN user_streaks us ON us.user_id = up.user_id
  WHERE up.user_id != p_searcher_id
    AND (
      LOWER(up.username) LIKE LOWER(p_query || '%')
      OR LOWER(up.display_name) LIKE LOWER('%' || p_query || '%')
      OR UPPER(up.friend_code) = UPPER(p_query)
    )
  ORDER BY
    CASE WHEN UPPER(up.friend_code) = UPPER(p_query) THEN 0 ELSE 1 END,
    CASE WHEN LOWER(up.username) = LOWER(p_query) THEN 0 ELSE 1 END,
    up.total_xp DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get friend's public profile with activity
CREATE OR REPLACE FUNCTION get_friend_profile(
  p_user_id UUID,
  p_friend_id UUID
)
RETURNS TABLE (
  user_id UUID,
  username VARCHAR,
  display_name TEXT,
  friend_code VARCHAR,
  level INTEGER,
  total_xp INTEGER,
  streak_days INTEGER,
  longest_streak INTEGER,
  xp_today INTEGER,
  lessons_today INTEGER,
  is_friend BOOLEAN,
  last_7_days_activity JSONB
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    up.user_id,
    up.username,
    up.display_name,
    up.friend_code,
    up.level,
    up.total_xp,
    COALESCE(us.streak_days, 0)::INTEGER,
    COALESCE(us.longest_streak, 0)::INTEGER,
    COALESCE(
      (SELECT SUM(xp_earned)::INTEGER FROM xp_transactions
       WHERE xp_transactions.user_id = up.user_id AND DATE(created_at) = CURRENT_DATE),
      0
    )::INTEGER as xp_today,
    COALESCE(
      (SELECT COUNT(*)::INTEGER FROM learning_path_progress
       WHERE learning_path_progress.user_id = up.user_id AND DATE(completed_at) = CURRENT_DATE AND completed = TRUE),
      0
    )::INTEGER as lessons_today,
    EXISTS(
      SELECT 1 FROM friendships f
      WHERE ((f.user_id = p_user_id AND f.friend_id = up.user_id)
         OR (f.friend_id = p_user_id AND f.user_id = up.user_id))
        AND f.status = 'accepted'
    ) as is_friend,
    (
      SELECT jsonb_agg(jsonb_build_object(
        'date', d.day::DATE,
        'xp', COALESCE(xp.total, 0),
        'lessons', COALESCE(lp.count, 0)
      ) ORDER BY d.day)
      FROM generate_series(CURRENT_DATE - INTERVAL '6 days', CURRENT_DATE, '1 day') as d(day)
      LEFT JOIN (
        SELECT DATE(created_at) as day, SUM(xp_earned)::INTEGER as total
        FROM xp_transactions
        WHERE xp_transactions.user_id = up.user_id AND DATE(created_at) >= CURRENT_DATE - INTERVAL '6 days'
        GROUP BY DATE(created_at)
      ) xp ON xp.day = d.day::DATE
      LEFT JOIN (
        SELECT DATE(completed_at) as day, COUNT(*)::INTEGER as count
        FROM learning_path_progress
        WHERE learning_path_progress.user_id = up.user_id AND DATE(completed_at) >= CURRENT_DATE - INTERVAL '6 days' AND completed = TRUE
        GROUP BY DATE(completed_at)
      ) lp ON lp.day = d.day::DATE
    ) as last_7_days_activity
  FROM user_profiles up
  LEFT JOIN user_streaks us ON us.user_id = up.user_id
  WHERE up.user_id = p_friend_id;
END;
$$ LANGUAGE plpgsql;

-- Function to send friend request
CREATE OR REPLACE FUNCTION send_friend_request(p_user_id UUID, p_friend_id UUID)
RETURNS BOOLEAN
AS $$
DECLARE
  v_existing_status VARCHAR;
BEGIN
  -- Check for existing friendship
  SELECT status INTO v_existing_status
  FROM friendships
  WHERE (user_id = p_user_id AND friend_id = p_friend_id)
     OR (user_id = p_friend_id AND friend_id = p_user_id);

  IF v_existing_status = 'accepted' THEN
    RETURN FALSE; -- Already friends
  ELSIF v_existing_status = 'pending' THEN
    -- Accept existing request if it was from the other person
    UPDATE friendships
    SET status = 'accepted', accepted_at = NOW()
    WHERE user_id = p_friend_id AND friend_id = p_user_id AND status = 'pending';

    IF FOUND THEN
      RETURN TRUE;
    END IF;

    RETURN FALSE; -- Already sent request
  ELSIF v_existing_status = 'blocked' THEN
    RETURN FALSE;
  END IF;

  -- Create new request
  INSERT INTO friendships (user_id, friend_id, status)
  VALUES (p_user_id, p_friend_id, 'pending');

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to accept friend request
CREATE OR REPLACE FUNCTION accept_friend_request(p_user_id UUID, p_requester_id UUID)
RETURNS BOOLEAN
AS $$
BEGIN
  UPDATE friendships
  SET status = 'accepted', accepted_at = NOW()
  WHERE user_id = p_requester_id AND friend_id = p_user_id AND status = 'pending';

  RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to get friends list with today's stats
CREATE OR REPLACE FUNCTION get_friends_list(p_user_id UUID)
RETURNS TABLE (
  user_id UUID,
  username VARCHAR,
  display_name TEXT,
  level INTEGER,
  total_xp INTEGER,
  streak_days INTEGER,
  xp_today INTEGER,
  lessons_today INTEGER,
  friend_since TIMESTAMP
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    up.user_id,
    up.username,
    up.display_name,
    up.level,
    up.total_xp,
    COALESCE(us.streak_days, 0)::INTEGER,
    COALESCE(
      (SELECT SUM(xp_earned)::INTEGER FROM xp_transactions
       WHERE xp_transactions.user_id = up.user_id AND DATE(created_at) = CURRENT_DATE),
      0
    )::INTEGER as xp_today,
    COALESCE(
      (SELECT COUNT(*)::INTEGER FROM learning_path_progress
       WHERE learning_path_progress.user_id = up.user_id AND DATE(completed_at) = CURRENT_DATE AND completed = TRUE),
      0
    )::INTEGER as lessons_today,
    f.accepted_at as friend_since
  FROM friendships f
  JOIN user_profiles up ON (
    CASE WHEN f.user_id = p_user_id THEN f.friend_id ELSE f.user_id END = up.user_id
  )
  LEFT JOIN user_streaks us ON us.user_id = up.user_id
  WHERE (f.user_id = p_user_id OR f.friend_id = p_user_id)
    AND f.status = 'accepted'
  ORDER BY xp_today DESC, up.total_xp DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending friend requests
CREATE OR REPLACE FUNCTION get_pending_requests(p_user_id UUID)
RETURNS TABLE (
  request_id UUID,
  user_id UUID,
  username VARCHAR,
  display_name TEXT,
  level INTEGER,
  total_xp INTEGER,
  requested_at TIMESTAMP
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    f.id as request_id,
    up.user_id,
    up.username,
    up.display_name,
    up.level,
    up.total_xp,
    f.created_at as requested_at
  FROM friendships f
  JOIN user_profiles up ON f.user_id = up.user_id
  WHERE f.friend_id = p_user_id AND f.status = 'pending'
  ORDER BY f.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to create friend challenge
CREATE OR REPLACE FUNCTION create_friend_challenge(
  p_challenger_id UUID,
  p_challenged_id UUID,
  p_challenge_type VARCHAR
)
RETURNS UUID
AS $$
DECLARE
  v_challenge_id UUID;
BEGIN
  -- Verify they are friends
  IF NOT EXISTS(
    SELECT 1 FROM friendships
    WHERE ((user_id = p_challenger_id AND friend_id = p_challenged_id)
       OR (user_id = p_challenged_id AND friend_id = p_challenger_id))
      AND status = 'accepted'
  ) THEN
    RAISE EXCEPTION 'Users are not friends';
  END IF;

  -- Check for existing challenge today
  IF EXISTS(
    SELECT 1 FROM friend_challenges
    WHERE challenger_id = p_challenger_id
      AND challenged_id = p_challenged_id
      AND challenge_type = p_challenge_type
      AND challenge_date = CURRENT_DATE
      AND status IN ('pending', 'accepted')
  ) THEN
    RAISE EXCEPTION 'Challenge already exists for today';
  END IF;

  -- Create challenge
  INSERT INTO friend_challenges (challenger_id, challenged_id, challenge_type, challenge_date)
  VALUES (p_challenger_id, p_challenged_id, p_challenge_type, CURRENT_DATE)
  RETURNING id INTO v_challenge_id;

  RETURN v_challenge_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update friend challenge scores (called at end of day or when checking)
CREATE OR REPLACE FUNCTION update_friend_challenge_scores(p_challenge_id UUID)
RETURNS TABLE (
  challenger_score INTEGER,
  challenged_score INTEGER,
  winner_id UUID,
  status VARCHAR
)
AS $$
DECLARE
  v_challenge RECORD;
  v_challenger_xp INTEGER;
  v_challenged_xp INTEGER;
  v_challenger_lessons INTEGER;
  v_challenged_lessons INTEGER;
  v_winner UUID;
BEGIN
  SELECT * INTO v_challenge FROM friend_challenges WHERE id = p_challenge_id;

  IF v_challenge.status NOT IN ('pending', 'accepted') THEN
    RETURN QUERY SELECT v_challenge.challenger_score, v_challenge.challenged_score,
                        v_challenge.winner_id, v_challenge.status;
    RETURN;
  END IF;

  -- Get today's XP for both users
  SELECT COALESCE(SUM(xp_earned), 0)::INTEGER INTO v_challenger_xp
  FROM xp_transactions WHERE user_id = v_challenge.challenger_id AND DATE(created_at) = v_challenge.challenge_date;

  SELECT COALESCE(SUM(xp_earned), 0)::INTEGER INTO v_challenged_xp
  FROM xp_transactions WHERE user_id = v_challenge.challenged_id AND DATE(created_at) = v_challenge.challenge_date;

  -- Get today's lessons for both users
  SELECT COALESCE(COUNT(*), 0)::INTEGER INTO v_challenger_lessons
  FROM learning_path_progress WHERE user_id = v_challenge.challenger_id AND DATE(completed_at) = v_challenge.challenge_date AND completed = TRUE;

  SELECT COALESCE(COUNT(*), 0)::INTEGER INTO v_challenged_lessons
  FROM learning_path_progress WHERE user_id = v_challenge.challenged_id AND DATE(completed_at) = v_challenge.challenge_date AND completed = TRUE;

  -- Determine scores based on challenge type
  IF v_challenge.challenge_type = 'beat_xp_today' THEN
    v_challenge.challenger_score := v_challenger_xp;
    v_challenge.challenged_score := v_challenged_xp;
  ELSIF v_challenge.challenge_type = 'more_lessons_today' THEN
    v_challenge.challenger_score := v_challenger_lessons;
    v_challenge.challenged_score := v_challenged_lessons;
  END IF;

  -- Determine winner if challenge day is over
  IF v_challenge.challenge_date < CURRENT_DATE AND v_challenge.status = 'accepted' THEN
    IF v_challenge.challenger_score > v_challenge.challenged_score THEN
      v_winner := v_challenge.challenger_id;
    ELSIF v_challenge.challenged_score > v_challenge.challenger_score THEN
      v_winner := v_challenge.challenged_id;
    ELSE
      v_winner := NULL; -- Tie
    END IF;

    UPDATE friend_challenges
    SET challenger_score = v_challenge.challenger_score,
        challenged_score = v_challenge.challenged_score,
        winner_id = v_winner,
        status = 'completed',
        completed_at = NOW()
    WHERE id = p_challenge_id;

    v_challenge.status := 'completed';
  ELSE
    -- Just update scores
    UPDATE friend_challenges
    SET challenger_score = v_challenge.challenger_score,
        challenged_score = v_challenge.challenged_score
    WHERE id = p_challenge_id;
  END IF;

  RETURN QUERY SELECT v_challenge.challenger_score, v_challenge.challenged_score,
                      v_winner, v_challenge.status;
END;
$$ LANGUAGE plpgsql;
