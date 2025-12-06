-- Migration 009: Skill Definitions for Mastery Engine
-- Creates master skill definitions table and adds BKT columns to skill_graph_nodes

-- Master skill definitions (static, ~120 skills for MVP)
CREATE TABLE IF NOT EXISTS skill_definitions (
  skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_key VARCHAR(100) UNIQUE NOT NULL,
  domain VARCHAR(50) NOT NULL,
  category VARCHAR(100) NOT NULL,
  name_en VARCHAR(255) NOT NULL,
  description_en TEXT,
  cefr_level VARCHAR(10) NOT NULL,
  difficulty FLOAT DEFAULT 0.5,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_skill_definitions_domain ON skill_definitions(domain);
CREATE INDEX idx_skill_definitions_level ON skill_definitions(cefr_level);
CREATE INDEX idx_skill_definitions_key ON skill_definitions(skill_key);

-- Add BKT columns to existing skill_graph_nodes
ALTER TABLE skill_graph_nodes
ADD COLUMN IF NOT EXISTS p_learned FLOAT DEFAULT 0.1,
ADD COLUMN IF NOT EXISTS p_transit FLOAT DEFAULT 0.15;

-- Function to update skill mastery using BKT
CREATE OR REPLACE FUNCTION update_skill_bkt(
  p_user_id UUID,
  p_skill_key VARCHAR,
  p_correct BOOLEAN
)
RETURNS FLOAT
AS $$
DECLARE
  v_p_learned FLOAT;
  v_p_transit FLOAT;
  v_p_guess FLOAT := 0.2;
  v_p_slip FLOAT := 0.1;
  v_posterior FLOAT;
  v_new_p_learned FLOAT;
BEGIN
  -- Get current mastery or create new node
  SELECT p_learned, p_transit INTO v_p_learned, v_p_transit
  FROM skill_graph_nodes
  WHERE user_id = p_user_id AND skill_key = p_skill_key;

  IF NOT FOUND THEN
    v_p_learned := 0.1;
    v_p_transit := 0.15;
  END IF;

  -- BKT update
  IF p_correct THEN
    v_posterior := (v_p_learned * (1 - v_p_slip)) /
                   (v_p_learned * (1 - v_p_slip) + (1 - v_p_learned) * v_p_guess);
  ELSE
    v_posterior := (v_p_learned * v_p_slip) /
                   (v_p_learned * v_p_slip + (1 - v_p_learned) * (1 - v_p_guess));
  END IF;

  v_new_p_learned := v_posterior + (1 - v_posterior) * v_p_transit;

  -- Upsert skill node
  INSERT INTO skill_graph_nodes (
    node_id, user_id, skill_category, skill_key,
    mastery_score, p_learned, p_transit,
    practice_count, success_count, error_count, last_practiced
  )
  VALUES (
    gen_random_uuid(), p_user_id, 'mastery', p_skill_key,
    v_new_p_learned * 100, v_new_p_learned, v_p_transit,
    1, CASE WHEN p_correct THEN 1 ELSE 0 END, CASE WHEN NOT p_correct THEN 1 ELSE 0 END, NOW()
  )
  ON CONFLICT (user_id, skill_key) DO UPDATE SET
    p_learned = v_new_p_learned,
    mastery_score = v_new_p_learned * 100,
    practice_count = skill_graph_nodes.practice_count + 1,
    success_count = skill_graph_nodes.success_count + CASE WHEN p_correct THEN 1 ELSE 0 END,
    error_count = skill_graph_nodes.error_count + CASE WHEN NOT p_correct THEN 1 ELSE 0 END,
    last_practiced = NOW();

  RETURN v_new_p_learned;
END;
$$ LANGUAGE plpgsql;

-- Function to get recommended skills (lowest mastery first)
CREATE OR REPLACE FUNCTION get_recommended_skills(
  p_user_id UUID,
  p_limit INTEGER DEFAULT 3
)
RETURNS TABLE (
  skill_key VARCHAR,
  name_en VARCHAR,
  domain VARCHAR,
  cefr_level VARCHAR,
  p_learned FLOAT,
  practice_count INTEGER
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    sd.skill_key,
    sd.name_en,
    sd.domain,
    sd.cefr_level,
    COALESCE(sgn.p_learned, 0.1) as p_learned,
    COALESCE(sgn.practice_count, 0) as practice_count
  FROM skill_definitions sd
  LEFT JOIN skill_graph_nodes sgn
    ON sd.skill_key = sgn.skill_key AND sgn.user_id = p_user_id
  WHERE sd.is_active = TRUE
  ORDER BY COALESCE(sgn.p_learned, 0.1) ASC, sd.difficulty ASC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's skill mastery overview
CREATE OR REPLACE FUNCTION get_skill_mastery_overview(p_user_id UUID)
RETURNS TABLE (
  total_skills INTEGER,
  skills_practiced INTEGER,
  mastered_count INTEGER,
  in_progress_count INTEGER,
  struggling_count INTEGER,
  avg_mastery FLOAT
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    (SELECT COUNT(*)::INTEGER FROM skill_definitions WHERE is_active = TRUE),
    COUNT(sgn.skill_key)::INTEGER,
    COUNT(CASE WHEN sgn.p_learned >= 0.85 THEN 1 END)::INTEGER,
    COUNT(CASE WHEN sgn.p_learned >= 0.3 AND sgn.p_learned < 0.85 THEN 1 END)::INTEGER,
    COUNT(CASE WHEN sgn.p_learned < 0.3 THEN 1 END)::INTEGER,
    COALESCE(AVG(sgn.p_learned), 0.1)
  FROM skill_graph_nodes sgn
  WHERE sgn.user_id = p_user_id
    AND sgn.skill_key IN (SELECT skill_key FROM skill_definitions WHERE is_active = TRUE);
END;
$$ LANGUAGE plpgsql;
