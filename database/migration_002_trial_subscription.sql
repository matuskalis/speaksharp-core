-- Migration 002: Add Trial and Subscription fields to user_profiles
-- Date: 2024-11-27
-- Description: Adds trial tracking and subscription management fields

-- Add trial and subscription columns to user_profiles
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS trial_start_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50),
ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(50);

-- Add comment for documentation
COMMENT ON COLUMN user_profiles.trial_start_date IS 'Date when user trial started (14-day free trial)';
COMMENT ON COLUMN user_profiles.trial_end_date IS 'Date when user trial ends';
COMMENT ON COLUMN user_profiles.subscription_status IS 'Subscription status: active, cancelled, expired, null';
COMMENT ON COLUMN user_profiles.subscription_tier IS 'Subscription tier: starter, pro, premium, enterprise, null';

-- Create index for efficient trial expiration queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_trial_end ON user_profiles(trial_end_date)
WHERE trial_end_date IS NOT NULL;

-- Create index for subscription queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_subscription ON user_profiles(subscription_status, subscription_tier)
WHERE subscription_status IS NOT NULL;
