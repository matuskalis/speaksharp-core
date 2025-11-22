-- SpeakSharp Database Schema (Supabase-ready PostgreSQL)

-- Users table (managed by Supabase Auth)
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id UUID PRIMARY KEY,
  level VARCHAR(10) DEFAULT 'A1',
  goals JSONB DEFAULT '{}',
  interests JSONB DEFAULT '[]',
  native_language VARCHAR(50),
  pronunciation_baseline JSONB,
  fluency_baseline FLOAT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- SRS Cards
CREATE TABLE IF NOT EXISTS srs_cards (
  card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  card_type VARCHAR(50) NOT NULL,
  front TEXT NOT NULL,
  back TEXT NOT NULL,
  level VARCHAR(10) DEFAULT 'A1',
  source VARCHAR(50),
  source_id UUID,
  difficulty FLOAT DEFAULT 0.5,
  next_review_date TIMESTAMP NOT NULL,
  interval_days INTEGER DEFAULT 1,
  ease_factor FLOAT DEFAULT 2.5,
  review_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);

CREATE INDEX idx_srs_cards_user_next_review ON srs_cards(user_id, next_review_date);

-- SRS Reviews
CREATE TABLE IF NOT EXISTS srs_reviews (
  review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  card_id UUID REFERENCES srs_cards(card_id),
  user_id UUID REFERENCES user_profiles(user_id),
  reviewed_at TIMESTAMP DEFAULT NOW(),
  quality INTEGER NOT NULL CHECK (quality >= 0 AND quality <= 5),
  response_time_ms INTEGER,
  user_response TEXT,
  correct BOOLEAN,
  new_interval_days INTEGER,
  new_ease_factor FLOAT
);

CREATE INDEX idx_srs_reviews_card ON srs_reviews(card_id);

-- Skill Graph Nodes
CREATE TABLE IF NOT EXISTS skill_graph_nodes (
  node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  skill_category VARCHAR(50) NOT NULL,
  skill_key VARCHAR(100) NOT NULL,
  mastery_score FLOAT DEFAULT 0.0 CHECK (mastery_score >= 0 AND mastery_score <= 100),
  confidence FLOAT DEFAULT 0.0 CHECK (confidence >= 0 AND confidence <= 1),
  last_practiced TIMESTAMP,
  practice_count INTEGER DEFAULT 0,
  error_count INTEGER DEFAULT 0,
  success_count INTEGER DEFAULT 0,
  decay_rate FLOAT DEFAULT 0.05,
  metadata JSONB,
  UNIQUE(user_id, skill_key)
);

CREATE INDEX idx_skill_nodes_user ON skill_graph_nodes(user_id);

-- Error Log
CREATE TABLE IF NOT EXISTS error_log (
  error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  session_id UUID,
  error_type VARCHAR(100) NOT NULL,
  source_type VARCHAR(50),
  user_sentence TEXT NOT NULL,
  corrected_sentence TEXT NOT NULL,
  explanation TEXT,
  occurred_at TIMESTAMP DEFAULT NOW(),
  recycled BOOLEAN DEFAULT FALSE,
  recycled_count INTEGER DEFAULT 0
);

CREATE INDEX idx_error_log_user ON error_log(user_id, occurred_at DESC);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
  session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id),
  session_type VARCHAR(50) NOT NULL,
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  duration_seconds INTEGER,
  state VARCHAR(50) DEFAULT 'in_progress',
  metadata JSONB
);

CREATE INDEX idx_sessions_user ON sessions(user_id, started_at DESC);

-- Evaluations
CREATE TABLE IF NOT EXISTS evaluations (
  evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(session_id),
  user_id UUID REFERENCES user_profiles(user_id),
  input_type VARCHAR(50),
  transcript TEXT,
  audio_url TEXT,
  scores JSONB,
  subscores JSONB,
  errors JSONB,
  timing_data JSONB,
  suggested_drills JSONB,
  evaluated_at TIMESTAMP DEFAULT NOW()
);

-- Content Library
CREATE TABLE IF NOT EXISTS content_library (
  content_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_type VARCHAR(50) NOT NULL,
  title TEXT NOT NULL,
  level_min VARCHAR(10),
  level_max VARCHAR(10),
  skill_targets JSONB,
  content_data JSONB,
  audio_url TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);

-- SRS Functions

-- Get due cards for review
CREATE OR REPLACE FUNCTION get_due_cards(p_user_id UUID, p_limit INTEGER DEFAULT 20)
RETURNS TABLE (card_id UUID, front TEXT, back TEXT, card_type VARCHAR)
AS $$
BEGIN
  RETURN QUERY
  SELECT c.card_id, c.front, c.back, c.card_type
  FROM srs_cards c
  WHERE c.user_id = p_user_id
    AND c.next_review_date <= NOW()
  ORDER BY c.next_review_date ASC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Update card after review (SM-2 Algorithm)
CREATE OR REPLACE FUNCTION update_card_after_review(
  p_card_id UUID,
  p_quality INTEGER,
  p_response_time_ms INTEGER,
  p_user_response TEXT,
  p_correct BOOLEAN
)
RETURNS VOID
AS $$
DECLARE
  v_current_ease FLOAT;
  v_current_interval INTEGER;
  v_new_ease FLOAT;
  v_new_interval INTEGER;
  v_user_id UUID;
BEGIN
  SELECT ease_factor, interval_days, user_id INTO v_current_ease, v_current_interval, v_user_id
  FROM srs_cards WHERE card_id = p_card_id;

  -- SM-2 Algorithm
  IF p_quality >= 3 THEN
    v_new_ease := v_current_ease + (0.1 - (5 - p_quality) * (0.08 + (5 - p_quality) * 0.02));
    IF v_new_ease < 1.3 THEN
      v_new_ease := 1.3;
    END IF;
    v_new_interval := CEIL(v_current_interval * v_new_ease);
  ELSE
    v_new_ease := GREATEST(1.3, v_current_ease - 0.2);
    v_new_interval := 1;
  END IF;

  UPDATE srs_cards
  SET next_review_date = NOW() + (v_new_interval || ' days')::INTERVAL,
      interval_days = v_new_interval,
      ease_factor = v_new_ease,
      review_count = review_count + 1
  WHERE card_id = p_card_id;

  INSERT INTO srs_reviews (card_id, user_id, quality, response_time_ms, user_response, correct, new_interval_days, new_ease_factor)
  VALUES (p_card_id, v_user_id, p_quality, p_response_time_ms, p_user_response, p_correct, v_new_interval, v_new_ease);
END;
$$ LANGUAGE plpgsql;

-- Create card from error
CREATE OR REPLACE FUNCTION create_card_from_error(p_error_id UUID)
RETURNS UUID
AS $$
DECLARE
  v_card_id UUID;
  v_error RECORD;
BEGIN
  SELECT * INTO v_error FROM error_log WHERE error_id = p_error_id;

  v_card_id := gen_random_uuid();

  INSERT INTO srs_cards (card_id, user_id, card_type, front, back, source, source_id, difficulty, next_review_date)
  VALUES (
    v_card_id,
    v_error.user_id,
    'error_repair',
    'Fix this sentence: ' || v_error.user_sentence,
    v_error.corrected_sentence || E'\n\nExplanation: ' || v_error.explanation,
    'error',
    p_error_id,
    0.7,
    NOW()
  );

  UPDATE error_log SET recycled = TRUE, recycled_count = recycled_count + 1
  WHERE error_id = p_error_id;

  RETURN v_card_id;
END;
$$ LANGUAGE plpgsql;

-- Update skill node
CREATE OR REPLACE FUNCTION update_skill_node(
  p_user_id UUID,
  p_skill_key VARCHAR,
  p_success BOOLEAN,
  p_score_delta FLOAT
)
RETURNS VOID
AS $$
BEGIN
  INSERT INTO skill_graph_nodes (node_id, user_id, skill_key, mastery_score, practice_count, error_count, success_count, last_practiced)
  VALUES (
    gen_random_uuid(),
    p_user_id,
    p_skill_key,
    GREATEST(0, LEAST(100, p_score_delta)),
    1,
    CASE WHEN NOT p_success THEN 1 ELSE 0 END,
    CASE WHEN p_success THEN 1 ELSE 0 END,
    NOW()
  )
  ON CONFLICT (user_id, skill_key) DO UPDATE SET
    mastery_score = GREATEST(0, LEAST(100, skill_graph_nodes.mastery_score + p_score_delta)),
    practice_count = skill_graph_nodes.practice_count + 1,
    error_count = skill_graph_nodes.error_count + CASE WHEN NOT p_success THEN 1 ELSE 0 END,
    success_count = skill_graph_nodes.success_count + CASE WHEN p_success THEN 1 ELSE 0 END,
    last_practiced = NOW(),
    confidence = LEAST(1.0, skill_graph_nodes.confidence + 0.05);
END;
$$ LANGUAGE plpgsql;

-- Get weakest skills
CREATE OR REPLACE FUNCTION get_weakest_skills(p_user_id UUID, p_limit INTEGER DEFAULT 5)
RETURNS TABLE (skill_key VARCHAR, mastery_score FLOAT, error_count INTEGER)
AS $$
BEGIN
  RETURN QUERY
  SELECT s.skill_key, s.mastery_score, s.error_count
  FROM skill_graph_nodes s
  WHERE s.user_id = p_user_id
  ORDER BY s.mastery_score ASC, s.error_count DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
