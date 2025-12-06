-- Migration 010: Diagnostic Test Tables
-- Creates tables for adaptive placement test sessions and answers

-- Diagnostic sessions table
CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',  -- 'in_progress' | 'completed'
    current_level VARCHAR(10) NOT NULL DEFAULT 'A2',    -- 'A1' | 'A2' | 'B1'
    questions_answered INTEGER NOT NULL DEFAULT 0,
    max_questions INTEGER NOT NULL DEFAULT 18,
    stats JSONB NOT NULL DEFAULT '{"A1": {"correct": 0, "total": 0}, "A2": {"correct": 0, "total": 0}, "B1": {"correct": 0, "total": 0}}'::jsonb,
    user_level VARCHAR(10),  -- Final determined level after completion
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_diagnostic_sessions_user ON diagnostic_sessions(user_id);
CREATE INDEX idx_diagnostic_sessions_status ON diagnostic_sessions(status);

-- Diagnostic answers table
CREATE TABLE IF NOT EXISTS diagnostic_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES diagnostic_sessions(session_id) ON DELETE CASCADE,
    question_index INTEGER NOT NULL,
    exercise_id VARCHAR(100) NOT NULL,  -- References exercises by exercise_id string
    skill_key VARCHAR(100) NOT NULL,
    level VARCHAR(10) NOT NULL,         -- 'A1' | 'A2' | 'B1'
    user_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_diagnostic_answers_session ON diagnostic_answers(session_id);
