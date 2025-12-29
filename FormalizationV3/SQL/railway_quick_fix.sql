-- RAILWAY QUICK SCHEMA FIX - Run this in Railway PostgreSQL console
-- Fixes all missing columns and schema issues

-- Add missing columns to user_profiles
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS company VARCHAR(255);
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS access_type VARCHAR(20) DEFAULT 'trial';
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Add missing columns to user_credits  
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS trial_credits INTEGER DEFAULT 100 CHECK (trial_credits >= 0);
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS premium_credits INTEGER DEFAULT 0 CHECK (premium_credits >= 0);
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS total_used INTEGER DEFAULT 0 CHECK (total_used >= 0);
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS is_trial_exhausted BOOLEAN DEFAULT FALSE;
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS sales_contacted BOOLEAN DEFAULT FALSE;
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS last_used TIMESTAMP WITH TIME ZONE;

-- Add missing columns to resumes
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS analysis_results JSONB DEFAULT NULL;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS extracted_text TEXT DEFAULT NULL;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS ai_processing_time INTEGER DEFAULT 0;

-- Add missing columns to usage_analytics
ALTER TABLE usage_analytics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create missing indexes
CREATE INDEX IF NOT EXISTS idx_resumes_analysis_results ON resumes USING GIN(analysis_results);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_created_at ON usage_analytics(created_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_name ON user_profiles(name);
CREATE INDEX IF NOT EXISTS idx_user_credits_trial_exhausted ON user_credits(is_trial_exhausted);

-- Insert default admin user
INSERT INTO user_profiles (id, email, name, company, access_type, is_active)
VALUES (
    'b8f7c9e6-1234-5678-9abc-def012345678'::uuid,
    'admin@bearsystems.co.in',
    'System Administrator', 
    'Bear Systems',
    'enterprise',
    true
) ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    company = EXCLUDED.company,
    access_type = EXCLUDED.access_type,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Insert default admin credits
INSERT INTO user_credits (user_id, trial_credits, premium_credits, total_used)
VALUES (
    'b8f7c9e6-1234-5678-9abc-def012345678'::uuid,
    1000,
    5000, 
    0
) ON CONFLICT (user_id) DO UPDATE SET
    trial_credits = GREATEST(user_credits.trial_credits, 1000),
    premium_credits = GREATEST(user_credits.premium_credits, 5000),
    updated_at = NOW();

-- Update NULL values
UPDATE resumes SET skills = '[]'::jsonb WHERE skills IS NULL;
UPDATE user_profiles SET access_type = 'trial' WHERE access_type IS NULL;
UPDATE user_profiles SET is_active = TRUE WHERE is_active IS NULL;
