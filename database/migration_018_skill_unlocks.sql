-- Migration 018: Skill-Based Unlocks System
-- Gamified progression with skill tracking, unlocks, and achievements

-- Skill profiles table
CREATE TABLE IF NOT EXISTS skill_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    total_xp INT NOT NULL DEFAULT 0,
    overall_level INT NOT NULL DEFAULT 1,
    skills JSONB NOT NULL DEFAULT '{}',           -- Skill progress by skill_id
    unlocked_content JSONB NOT NULL DEFAULT '[]', -- Array of unlocked content IDs
    earned_achievements JSONB NOT NULL DEFAULT '[]', -- Array of earned achievement IDs
    daily_xp INT NOT NULL DEFAULT 0,
    daily_xp_cap INT NOT NULL DEFAULT 500,
    last_daily_reset TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for skill profiles
CREATE INDEX IF NOT EXISTS idx_skill_profiles_level ON skill_profiles(overall_level DESC);
CREATE INDEX IF NOT EXISTS idx_skill_profiles_xp ON skill_profiles(total_xp DESC);
CREATE INDEX IF NOT EXISTS idx_skill_profiles_skills ON skill_profiles USING GIN (skills);

-- Achievement history table (for tracking when achievements were earned)
CREATE TABLE IF NOT EXISTS achievement_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    achievement_id TEXT NOT NULL,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    xp_awarded INT NOT NULL DEFAULT 0,
    context JSONB DEFAULT '{}'  -- Additional context about how it was earned
);

CREATE INDEX IF NOT EXISTS idx_achievement_history_user ON achievement_history(user_id);
CREATE INDEX IF NOT EXISTS idx_achievement_history_achievement ON achievement_history(achievement_id);

-- Unlock history table (for tracking when content was unlocked)
CREATE TABLE IF NOT EXISTS unlock_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content_id TEXT NOT NULL,
    unlock_type TEXT NOT NULL,
    unlocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    xp_awarded INT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_unlock_history_user ON unlock_history(user_id);
CREATE INDEX IF NOT EXISTS idx_unlock_history_content ON unlock_history(content_id);

-- XP transactions table (for tracking XP gains)
CREATE TABLE IF NOT EXISTS xp_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_id TEXT NOT NULL,
    xp_amount INT NOT NULL,
    source TEXT NOT NULL,  -- conversation, achievement, unlock, bonus
    session_id UUID,       -- Reference to conversation session if applicable
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_xp_transactions_user ON xp_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_created ON xp_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_skill ON xp_transactions(skill_id);

-- Function to get user's skill summary
CREATE OR REPLACE FUNCTION get_skill_summary(p_user_id UUID)
RETURNS TABLE (
    total_xp INT,
    overall_level INT,
    top_skills JSONB,
    recent_achievements JSONB,
    daily_xp INT,
    daily_xp_remaining INT
) AS $$
DECLARE
    v_profile skill_profiles%ROWTYPE;
BEGIN
    SELECT * INTO v_profile FROM skill_profiles WHERE user_id = p_user_id;

    IF v_profile IS NULL THEN
        RETURN QUERY SELECT
            0::INT as total_xp,
            1::INT as overall_level,
            '[]'::JSONB as top_skills,
            '[]'::JSONB as recent_achievements,
            0::INT as daily_xp,
            500::INT as daily_xp_remaining;
        RETURN;
    END IF;

    RETURN QUERY SELECT
        v_profile.total_xp,
        v_profile.overall_level,
        (
            SELECT jsonb_agg(skill_data ORDER BY (skill_data->>'level')::INT DESC)
            FROM (
                SELECT jsonb_build_object(
                    'skill_id', key,
                    'level', value->>'level',
                    'category', value->>'category'
                ) as skill_data
                FROM jsonb_each(v_profile.skills)
                LIMIT 5
            ) top
        ) as top_skills,
        (
            SELECT jsonb_agg(jsonb_build_object(
                'achievement_id', achievement_id,
                'earned_at', earned_at
            ) ORDER BY earned_at DESC)
            FROM achievement_history
            WHERE user_id = p_user_id
            LIMIT 5
        ) as recent_achievements,
        v_profile.daily_xp,
        (v_profile.daily_xp_cap - v_profile.daily_xp)::INT as daily_xp_remaining;
END;
$$ LANGUAGE plpgsql;

-- Function to get leaderboard
CREATE OR REPLACE FUNCTION get_leaderboard(
    p_limit INT DEFAULT 10,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    rank BIGINT,
    user_id UUID,
    total_xp INT,
    overall_level INT,
    achievement_count INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ROW_NUMBER() OVER (ORDER BY sp.total_xp DESC) as rank,
        sp.user_id,
        sp.total_xp,
        sp.overall_level,
        jsonb_array_length(sp.earned_achievements)::INT as achievement_count
    FROM skill_profiles sp
    ORDER BY sp.total_xp DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Function to get skill progress over time
CREATE OR REPLACE FUNCTION get_skill_progress_history(
    p_user_id UUID,
    p_skill_id TEXT,
    p_days INT DEFAULT 30
)
RETURNS TABLE (
    date DATE,
    xp_gained INT,
    cumulative_xp BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        DATE(xt.created_at) as date,
        SUM(xt.xp_amount)::INT as xp_gained,
        SUM(SUM(xt.xp_amount)) OVER (ORDER BY DATE(xt.created_at))::BIGINT as cumulative_xp
    FROM xp_transactions xt
    WHERE xt.user_id = p_user_id
      AND xt.skill_id = p_skill_id
      AND xt.created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY DATE(xt.created_at)
    ORDER BY DATE(xt.created_at);
END;
$$ LANGUAGE plpgsql;

-- Function to check and reset daily XP
CREATE OR REPLACE FUNCTION reset_daily_xp_if_needed(p_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_last_reset TIMESTAMP WITH TIME ZONE;
    v_was_reset BOOLEAN := FALSE;
BEGIN
    SELECT last_daily_reset INTO v_last_reset
    FROM skill_profiles
    WHERE user_id = p_user_id;

    IF v_last_reset IS NULL OR DATE(v_last_reset) < CURRENT_DATE THEN
        UPDATE skill_profiles
        SET daily_xp = 0,
            last_daily_reset = NOW()
        WHERE user_id = p_user_id;
        v_was_reset := TRUE;
    END IF;

    RETURN v_was_reset;
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON TABLE skill_profiles IS 'User skill progression and unlock status';
COMMENT ON TABLE achievement_history IS 'Record of when users earned achievements';
COMMENT ON TABLE unlock_history IS 'Record of when users unlocked content';
COMMENT ON TABLE xp_transactions IS 'Log of all XP gains for analytics';
