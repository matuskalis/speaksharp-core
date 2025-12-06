-- Migration 004: Add tester account flag
-- Date: 2024-11-30
-- Description: Adds is_tester flag for accounts with unlimited access

-- Add is_tester column to user_profiles
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS is_tester BOOLEAN DEFAULT FALSE;

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.is_tester IS 'Tester accounts bypass trial/payment restrictions and have unlimited access';

-- Create index for efficient tester queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_tester ON user_profiles(is_tester)
WHERE is_tester = TRUE;
