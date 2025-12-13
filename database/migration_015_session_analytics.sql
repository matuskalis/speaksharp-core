-- Migration 015: Session Analytics
-- Adds comprehensive session tracking for conversation, pronunciation, and roleplay sessions

-- Session Results table for detailed analytics
CREATE TABLE IF NOT EXISTS session_results (
    session_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    session_type VARCHAR(50) NOT NULL,  -- 'conversation', 'pronunciation', 'roleplay'
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds >= 0),
    words_spoken INTEGER DEFAULT 0 CHECK (words_spoken >= 0),
    pronunciation_score FLOAT DEFAULT 0.0 CHECK (pronunciation_score >= 0 AND pronunciation_score <= 100),
    fluency_score FLOAT DEFAULT 0.0 CHECK (fluency_score >= 0 AND fluency_score <= 100),
    grammar_score FLOAT DEFAULT 0.0 CHECK (grammar_score >= 0 AND grammar_score <= 100),
    topics TEXT[] DEFAULT '{}',  -- Array of topics covered
    vocabulary_learned TEXT[] DEFAULT '{}',  -- Array of vocabulary items learned
    areas_to_improve TEXT[] DEFAULT '{}',  -- Array of areas needing improvement
    metadata JSONB,  -- Additional session-specific data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_session_results_user_created
    ON session_results(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_results_type_user
    ON session_results(session_type, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_results_scores
    ON session_results(user_id, pronunciation_score, fluency_score, grammar_score);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_session_results_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_session_results_timestamp
    BEFORE UPDATE ON session_results
    FOR EACH ROW
    EXECUTE FUNCTION update_session_results_timestamp();
