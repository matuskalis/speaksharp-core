-- Migration 006: Add onboarding_completed and full_name columns
-- Date: 2024-12-04
-- Description: Adds fields needed for user onboarding flow

-- Add onboarding_completed column
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;

-- Add full_name column
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);

-- Add comments for documentation
COMMENT ON COLUMN user_profiles.onboarding_completed IS 'Whether user has completed the onboarding flow';
COMMENT ON COLUMN user_profiles.full_name IS 'User full name from profile';
