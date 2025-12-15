-- Migration 017: Conversation Replays with Coaching
-- Stores timestamped conversation sessions with coaching annotations

-- Conversation replays table
CREATE TABLE IF NOT EXISTS conversation_replays (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scenario_name TEXT,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    segments JSONB NOT NULL DEFAULT '[]',  -- Array of transcript segments with annotations
    summary JSONB NOT NULL DEFAULT '{}',   -- Overall session statistics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_replays_user_id ON conversation_replays(user_id);
CREATE INDEX IF NOT EXISTS idx_replays_started_at ON conversation_replays(started_at DESC);

-- Index for searching within segments
CREATE INDEX IF NOT EXISTS idx_replays_segments ON conversation_replays USING GIN (segments);

-- Function to get user's recent replays
CREATE OR REPLACE FUNCTION get_user_replays(
    p_user_id UUID,
    p_limit INT DEFAULT 10
)
RETURNS TABLE (
    session_id UUID,
    scenario_name TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    summary JSONB,
    duration_seconds NUMERIC,
    total_annotations INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        r.session_id,
        r.scenario_name,
        r.started_at,
        r.ended_at,
        r.summary,
        EXTRACT(EPOCH FROM (r.ended_at - r.started_at)) as duration_seconds,
        (SELECT COUNT(*)::INT
         FROM jsonb_array_elements(r.segments) seg,
              jsonb_array_elements(seg->'annotations') ann
        ) as total_annotations
    FROM conversation_replays r
    WHERE r.user_id = p_user_id
    ORDER BY r.started_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get annotation statistics for a user
CREATE OR REPLACE FUNCTION get_annotation_stats(
    p_user_id UUID,
    p_days INT DEFAULT 30
)
RETURNS TABLE (
    category TEXT,
    total_count BIGINT,
    error_count BIGINT,
    improvement_count BIGINT,
    praise_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ann->>'category' as category,
        COUNT(*) as total_count,
        COUNT(*) FILTER (WHERE ann->>'type' = 'error') as error_count,
        COUNT(*) FILTER (WHERE ann->>'type' = 'improvement') as improvement_count,
        COUNT(*) FILTER (WHERE ann->>'type' = 'praise') as praise_count
    FROM conversation_replays r,
         jsonb_array_elements(r.segments) seg,
         jsonb_array_elements(seg->'annotations') ann
    WHERE r.user_id = p_user_id
      AND r.started_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY ann->>'category';
END;
$$ LANGUAGE plpgsql;

-- Add comment
COMMENT ON TABLE conversation_replays IS 'Stores conversation sessions with timestamped coaching annotations for replay';
