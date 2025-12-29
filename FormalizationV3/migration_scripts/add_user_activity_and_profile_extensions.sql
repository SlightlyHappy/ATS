-- User Activity Detailed Table Migration
-- Adds comprehensive activity logging for user actions, security, and analytics

-- Create user_activity_detailed table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_activity_detailed (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'content', 'account', 'billing', 'security', 'api_access'
    details JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}', -- IP, device, location, user_agent
    status VARCHAR(20) DEFAULT 'success', -- 'success', 'failed', 'warning'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Add foreign key constraint if user_profiles table exists
    CONSTRAINT fk_user_activity_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES user_profiles(id) 
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity_detailed(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_category ON user_activity_detailed(category);
CREATE INDEX IF NOT EXISTS idx_user_activity_created_at ON user_activity_detailed(created_at);
CREATE INDEX IF NOT EXISTS idx_user_activity_action ON user_activity_detailed(action);
CREATE INDEX IF NOT EXISTS idx_user_activity_status ON user_activity_detailed(status);

-- Add composite index for common queries
CREATE INDEX IF NOT EXISTS idx_user_activity_user_date ON user_activity_detailed(user_id, created_at DESC);

-- Add user profile extensions if they don't exist
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS location_data JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS professional_info JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS security_settings JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN IF NOT EXISTS last_active TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop trigger if it exists and recreate
DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create user usage statistics table for analytics
CREATE TABLE IF NOT EXISTS user_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    resumes_uploaded INTEGER DEFAULT 0,
    resumes_analyzed INTEGER DEFAULT 0,
    avg_analysis_score DECIMAL(5,2),
    time_saved_hours DECIMAL(10,2),
    api_calls_count INTEGER DEFAULT 0,
    feature_usage JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, period_start, period_end)
);

-- Create indexes for usage stats
CREATE INDEX IF NOT EXISTS idx_user_usage_stats_user_id ON user_usage_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_stats_period ON user_usage_stats(period_start, period_end);

-- Insert sample activity for testing (if user exists)
-- This helps validate the schema works correctly
DO $$
DECLARE
    sample_user_id UUID;
BEGIN
    -- Get a sample user ID (first user in the system)
    SELECT id INTO sample_user_id FROM user_profiles LIMIT 1;
    
    IF sample_user_id IS NOT NULL THEN
        -- Insert sample activity record
        INSERT INTO user_activity_detailed (
            user_id, action, category, details, metadata, status
        ) VALUES (
            sample_user_id,
            'schema_migration_test',
            'system',
            '{"message": "User activity table created successfully", "migration_version": "1.0"}',
            '{"migration_date": "' || NOW()::text || '", "automated": true}',
            'success'
        ) ON CONFLICT DO NOTHING;
        
        RAISE NOTICE 'Sample activity record inserted for user: %', sample_user_id;
    ELSE
        RAISE NOTICE 'No users found - sample activity record not inserted';
    END IF;
END
$$;

-- Verify the migration worked
DO $$
DECLARE
    activity_count INTEGER;
    profile_columns INTEGER;
BEGIN
    -- Check activity table
    SELECT COUNT(*) INTO activity_count FROM user_activity_detailed;
    RAISE NOTICE 'User activity table has % records', activity_count;
    
    -- Check profile table columns
    SELECT COUNT(*) INTO profile_columns 
    FROM information_schema.columns 
    WHERE table_name = 'user_profiles' 
    AND column_name IN ('phone', 'avatar_url', 'location_data', 'professional_info', 'preferences');
    
    RAISE NOTICE 'User profiles table has % additional columns', profile_columns;
    
    IF profile_columns >= 5 THEN
        RAISE NOTICE 'User profile extensions migration completed successfully';
    ELSE
        RAISE WARNING 'User profile extensions may not have been fully applied';
    END IF;
END
$$;
