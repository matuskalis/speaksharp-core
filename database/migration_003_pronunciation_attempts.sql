-- Migration 003: Pronunciation Attempts Table
-- Add table for storing pronunciation scoring data

CREATE TABLE IF NOT EXISTS pronunciation_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  phrase TEXT NOT NULL,
  phoneme_scores JSONB NOT NULL,
  overall_score REAL NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pronunciation_user_created
  ON pronunciation_attempts (user_id, created_at DESC);

-- Add comment for documentation
COMMENT ON TABLE pronunciation_attempts IS 'Stores pronunciation assessment results with phoneme-level scoring';
COMMENT ON COLUMN pronunciation_attempts.phoneme_scores IS 'JSONB array of {phoneme, score, position} objects';
COMMENT ON COLUMN pronunciation_attempts.overall_score IS 'Average score across all phonemes (0-100)';
