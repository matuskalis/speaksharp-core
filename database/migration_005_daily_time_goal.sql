-- Migration 005: Add daily_time_goal column
-- Date: 2024-11-30

ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS daily_time_goal INTEGER;

COMMENT ON COLUMN user_profiles.daily_time_goal IS 'User daily study time goal in minutes';
