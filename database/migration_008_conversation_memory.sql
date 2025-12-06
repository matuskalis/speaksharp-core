-- Migration 008: Conversation Memory System
-- Creates conversation_history table to store user-tutor conversations
-- Enables the tutor to remember past sessions and reference previous conversations

-- Conversation History Table
CREATE TABLE IF NOT EXISTS conversation_history (
  conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_profiles(user_id) ON DELETE CASCADE,
  session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,

  -- Conversation turn data
  turn_number INTEGER NOT NULL,
  user_message TEXT NOT NULL,
  tutor_response TEXT NOT NULL,

  -- Metadata
  context_type VARCHAR(50), -- 'scenario', 'lesson', 'free_chat', 'voice_tutor', etc.
  context_id VARCHAR(100), -- scenario_id, lesson_id, etc.

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),

  -- Additional metadata (errors detected, topics discussed, etc.)
  metadata JSONB DEFAULT '{}'::JSONB
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_conversation_user_created ON conversation_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_context ON conversation_history(user_id, context_type, context_id);

-- Function: Get recent conversations for context loading
CREATE OR REPLACE FUNCTION get_recent_conversations(
  p_user_id UUID,
  p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
  conversation_id UUID,
  turn_number INTEGER,
  user_message TEXT,
  tutor_response TEXT,
  context_type VARCHAR,
  context_id VARCHAR,
  created_at TIMESTAMP,
  metadata JSONB
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    ch.conversation_id,
    ch.turn_number,
    ch.user_message,
    ch.tutor_response,
    ch.context_type,
    ch.context_id,
    ch.created_at,
    ch.metadata
  FROM conversation_history ch
  WHERE ch.user_id = p_user_id
  ORDER BY ch.created_at DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function: Get conversation context (summaries and key topics)
CREATE OR REPLACE FUNCTION get_conversation_context(
  p_user_id UUID,
  p_lookback_days INTEGER DEFAULT 7,
  p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
  total_conversations BIGINT,
  recent_topics TEXT[],
  context_summary JSONB
)
AS $$
DECLARE
  v_total_conversations BIGINT;
  v_recent_topics TEXT[];
  v_context_summary JSONB;
BEGIN
  -- Count total conversations in lookback period
  SELECT COUNT(*) INTO v_total_conversations
  FROM conversation_history ch
  WHERE ch.user_id = p_user_id
    AND ch.created_at >= NOW() - (p_lookback_days || ' days')::INTERVAL;

  -- Extract topics/keywords from recent conversations
  -- This is a simplified version - could be enhanced with NLP
  SELECT ARRAY_AGG(DISTINCT ch.context_type)
  INTO v_recent_topics
  FROM conversation_history ch
  WHERE ch.user_id = p_user_id
    AND ch.created_at >= NOW() - (p_lookback_days || ' days')::INTERVAL;

  -- Build summary JSON
  SELECT jsonb_build_object(
    'total_conversations', v_total_conversations,
    'recent_topics', COALESCE(v_recent_topics, ARRAY[]::TEXT[]),
    'last_conversation_date', MAX(ch.created_at),
    'most_active_context', (
      SELECT ch2.context_type
      FROM conversation_history ch2
      WHERE ch2.user_id = p_user_id
        AND ch2.created_at >= NOW() - (p_lookback_days || ' days')::INTERVAL
      GROUP BY ch2.context_type
      ORDER BY COUNT(*) DESC
      LIMIT 1
    )
  )
  INTO v_context_summary
  FROM conversation_history ch
  WHERE ch.user_id = p_user_id
    AND ch.created_at >= NOW() - (p_lookback_days || ' days')::INTERVAL;

  RETURN QUERY SELECT v_total_conversations, v_recent_topics, v_context_summary;
END;
$$ LANGUAGE plpgsql;

-- Function: Save a conversation turn
CREATE OR REPLACE FUNCTION save_conversation_turn(
  p_user_id UUID,
  p_session_id UUID,
  p_turn_number INTEGER,
  p_user_message TEXT,
  p_tutor_response TEXT,
  p_context_type VARCHAR DEFAULT NULL,
  p_context_id VARCHAR DEFAULT NULL,
  p_metadata JSONB DEFAULT '{}'::JSONB
)
RETURNS UUID
AS $$
DECLARE
  v_conversation_id UUID;
BEGIN
  v_conversation_id := gen_random_uuid();

  INSERT INTO conversation_history (
    conversation_id,
    user_id,
    session_id,
    turn_number,
    user_message,
    tutor_response,
    context_type,
    context_id,
    metadata
  )
  VALUES (
    v_conversation_id,
    p_user_id,
    p_session_id,
    p_turn_number,
    p_user_message,
    p_tutor_response,
    p_context_type,
    p_context_id,
    p_metadata
  );

  RETURN v_conversation_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Clear conversation history for a user
CREATE OR REPLACE FUNCTION clear_conversation_history(
  p_user_id UUID,
  p_before_date TIMESTAMP DEFAULT NULL
)
RETURNS INTEGER
AS $$
DECLARE
  v_deleted_count INTEGER;
BEGIN
  IF p_before_date IS NULL THEN
    -- Delete all conversations
    DELETE FROM conversation_history
    WHERE user_id = p_user_id;
  ELSE
    -- Delete conversations before specified date
    DELETE FROM conversation_history
    WHERE user_id = p_user_id
      AND created_at < p_before_date;
  END IF;

  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
  RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Get conversation history by context
CREATE OR REPLACE FUNCTION get_conversation_by_context(
  p_user_id UUID,
  p_context_type VARCHAR,
  p_context_id VARCHAR DEFAULT NULL,
  p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
  conversation_id UUID,
  turn_number INTEGER,
  user_message TEXT,
  tutor_response TEXT,
  created_at TIMESTAMP
)
AS $$
BEGIN
  RETURN QUERY
  SELECT
    ch.conversation_id,
    ch.turn_number,
    ch.user_message,
    ch.tutor_response,
    ch.created_at
  FROM conversation_history ch
  WHERE ch.user_id = p_user_id
    AND ch.context_type = p_context_type
    AND (p_context_id IS NULL OR ch.context_id = p_context_id)
  ORDER BY ch.created_at DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE conversation_history IS 'Stores conversation turns between users and the AI tutor for continuity and context';
COMMENT ON COLUMN conversation_history.turn_number IS 'Sequential turn number within a session';
COMMENT ON COLUMN conversation_history.context_type IS 'Type of conversation context: scenario, lesson, free_chat, voice_tutor, etc.';
COMMENT ON COLUMN conversation_history.context_id IS 'ID of the specific scenario, lesson, or other context';
COMMENT ON COLUMN conversation_history.metadata IS 'Additional data like detected errors, topics discussed, sentiment, etc.';
