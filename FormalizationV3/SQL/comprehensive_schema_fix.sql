-- Comprehensive Database Schema Fix for Railway PostgreSQL
-- This script fixes all the reported schema issues

-- =======================
-- 1. Fix user_profiles table
-- =======================
DO $$ 
BEGIN
    -- Ensure name column exists in user_profiles
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_profiles' AND column_name = 'name') THEN
        ALTER TABLE user_profiles ADD COLUMN name VARCHAR(255);
        RAISE NOTICE 'Added name column to user_profiles';
    END IF;
    
    -- Ensure company column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_profiles' AND column_name = 'company') THEN
        ALTER TABLE user_profiles ADD COLUMN company VARCHAR(255);
        RAISE NOTICE 'Added company column to user_profiles';
    END IF;
    
    -- Ensure access_type column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_profiles' AND column_name = 'access_type') THEN
        ALTER TABLE user_profiles ADD COLUMN access_type VARCHAR(20) DEFAULT 'trial';
        RAISE NOTICE 'Added access_type column to user_profiles';
    END IF;
    
    -- Ensure is_active column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_profiles' AND column_name = 'is_active') THEN
        ALTER TABLE user_profiles ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added is_active column to user_profiles';
    END IF;
END $$;

-- =======================
-- 2. Fix user_credits table
-- =======================
DO $$ 
BEGIN
    -- Ensure trial_credits column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_credits' AND column_name = 'trial_credits') THEN
        ALTER TABLE user_credits ADD COLUMN trial_credits INTEGER DEFAULT 100 CHECK (trial_credits >= 0);
        RAISE NOTICE 'Added trial_credits column to user_credits';
    END IF;
    
    -- Ensure premium_credits column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_credits' AND column_name = 'premium_credits') THEN
        ALTER TABLE user_credits ADD COLUMN premium_credits INTEGER DEFAULT 0 CHECK (premium_credits >= 0);
        RAISE NOTICE 'Added premium_credits column to user_credits';
    END IF;
    
    -- Ensure total_used column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_credits' AND column_name = 'total_used') THEN
        ALTER TABLE user_credits ADD COLUMN total_used INTEGER DEFAULT 0 CHECK (total_used >= 0);
        RAISE NOTICE 'Added total_used column to user_credits';
    END IF;
    
    -- Ensure is_trial_exhausted column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_credits' AND column_name = 'is_trial_exhausted') THEN
        ALTER TABLE user_credits ADD COLUMN is_trial_exhausted BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added is_trial_exhausted column to user_credits';
    END IF;
    
    -- Ensure sales_contacted column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_credits' AND column_name = 'sales_contacted') THEN
        ALTER TABLE user_credits ADD COLUMN sales_contacted BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added sales_contacted column to user_credits';
    END IF;
    
    -- Ensure last_used column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_credits' AND column_name = 'last_used') THEN
        ALTER TABLE user_credits ADD COLUMN last_used TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Added last_used column to user_credits';
    END IF;
END $$;

-- =======================
-- 3. Fix resumes table
-- =======================
DO $$ 
BEGIN
    -- Ensure analysis_results column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'analysis_results') THEN
        ALTER TABLE resumes ADD COLUMN analysis_results JSONB DEFAULT NULL;
        RAISE NOTICE 'Added analysis_results column to resumes';
    END IF;
    
    -- Ensure extracted_text column exists  
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'extracted_text') THEN
        ALTER TABLE resumes ADD COLUMN extracted_text TEXT DEFAULT NULL;
        RAISE NOTICE 'Added extracted_text column to resumes';
    END IF;
    
    -- Ensure processing_started_at column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'processing_started_at') THEN
        ALTER TABLE resumes ADD COLUMN processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
        RAISE NOTICE 'Added processing_started_at column to resumes';
    END IF;
    
    -- Ensure processing_completed_at column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'processing_completed_at') THEN
        ALTER TABLE resumes ADD COLUMN processing_completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
        RAISE NOTICE 'Added processing_completed_at column to resumes';
    END IF;
    
    -- Ensure ai_processing_time column exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'ai_processing_time') THEN
        ALTER TABLE resumes ADD COLUMN ai_processing_time INTEGER DEFAULT 0;
        RAISE NOTICE 'Added ai_processing_time column to resumes';
    END IF;
    
    -- Fix skills column type issue - handle PostgreSQL arrays properly
    DECLARE
        current_type TEXT;
        current_udt_name TEXT;
    BEGIN
        SELECT data_type, udt_name INTO current_type, current_udt_name
        FROM information_schema.columns 
        WHERE table_name = 'resumes' AND column_name = 'skills';
        
        IF current_type IS NOT NULL THEN
            RAISE NOTICE 'Found skills column with type: % (udt: %)', current_type, current_udt_name;
            
            IF current_type = 'ARRAY' OR current_udt_name = '_text' THEN
                -- Column is PostgreSQL array, convert to JSONB safely
                RAISE NOTICE 'Converting PostgreSQL array to JSONB';
                
                -- First add a temporary column to store JSONB data
                ALTER TABLE resumes ADD COLUMN skills_temp JSONB;
                
                -- Convert array data to JSONB in the temp column
                UPDATE resumes 
                SET skills_temp = CASE 
                    WHEN skills IS NULL THEN '[]'::jsonb
                    WHEN array_length(skills, 1) IS NULL THEN '[]'::jsonb
                    ELSE (
                        SELECT json_agg(elem)::jsonb 
                        FROM unnest(skills) AS elem
                    )
                END;
                
                -- Drop the old column and rename temp column
                ALTER TABLE resumes DROP COLUMN skills;
                ALTER TABLE resumes RENAME COLUMN skills_temp TO skills;
                
                RAISE NOTICE 'Successfully converted skills array to JSONB';
                
            ELSIF current_type != 'jsonb' THEN
                -- Column is text/varchar, convert to JSONB
                RAISE NOTICE 'Converting % to JSONB', current_type;
                
                -- Add temporary column
                ALTER TABLE resumes ADD COLUMN skills_temp JSONB;
                
                -- Convert text data to JSONB in the temp column
                UPDATE resumes 
                SET skills_temp = CASE 
                    WHEN skills IS NULL THEN '[]'::jsonb
                    WHEN skills::text = '' THEN '[]'::jsonb
                    WHEN skills::text LIKE '[%]' OR skills::text LIKE '{%}' THEN 
                        -- Try to parse as JSON, fallback to empty array
                        (CASE 
                            WHEN skills::text ~ '^[\[\{].*[\]\}]$' THEN 
                                (skills::text)::jsonb
                            ELSE '[]'::jsonb
                        END)
                    ELSE 
                        -- Convert comma-separated values to JSON array
                        (CASE 
                            WHEN trim(skills::text) = '' THEN '[]'::jsonb
                            ELSE ('["' || replace(replace(trim(skills::text), '"', '\"'), ',', '","') || '"]')::jsonb
                        END)
                END;
                
                -- Drop old column and rename temp column
                ALTER TABLE resumes DROP COLUMN skills;
                ALTER TABLE resumes RENAME COLUMN skills_temp TO skills;
                
                RAISE NOTICE 'Converted skills column to JSONB type';
                
            ELSE
                -- Column is already JSONB, just update NULL values
                UPDATE resumes SET skills = '[]'::jsonb WHERE skills IS NULL;
                RAISE NOTICE 'Skills column already JSONB, updated NULL values';
            END IF;
            
        ELSE
            -- Add skills column if it doesn't exist
            ALTER TABLE resumes ADD COLUMN skills JSONB DEFAULT '[]';
            RAISE NOTICE 'Added skills column as JSONB to resumes';
        END IF;
        
    EXCEPTION 
        WHEN OTHERS THEN
            RAISE NOTICE 'Error converting skills column: %. Adding new JSONB column.', SQLERRM;
            -- If conversion fails, ensure we have a working skills column
            BEGIN
                ALTER TABLE resumes DROP COLUMN IF EXISTS skills_temp;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name = 'resumes' AND column_name = 'skills') THEN
                    ALTER TABLE resumes ADD COLUMN skills JSONB DEFAULT '[]';
                    RAISE NOTICE 'Added new skills column as JSONB';
                END IF;
            EXCEPTION 
                WHEN OTHERS THEN
                    RAISE NOTICE 'Failed to create skills column: %', SQLERRM;
            END;
    END;
END $$;

-- =======================
-- 4. Fix usage_analytics table timestamp references
-- =======================
-- The usage_analytics table already has a 'timestamp' column, 
-- but some queries might be looking for 'created_at' instead
DO $$ 
BEGIN
    -- Ensure both timestamp and created_at exist for compatibility
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usage_analytics' AND column_name = 'created_at') THEN
        ALTER TABLE usage_analytics ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added created_at column to usage_analytics';
        
        -- Copy timestamp data to created_at for existing records
        UPDATE usage_analytics SET created_at = timestamp WHERE created_at IS NULL;
    END IF;
END $$;

-- =======================
-- 5. Create user_ai_settings and users tables if missing
-- =======================
-- Create user_ai_settings table
CREATE TABLE IF NOT EXISTS user_ai_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    ai_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    ai_model VARCHAR(100) NOT NULL DEFAULT 'gpt-3.5-turbo',
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Create unique constraint to prevent duplicates
    UNIQUE(user_id, ai_provider, ai_model)
);

-- Create users table for authentication (this is what the app actually uses)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    supabase_id TEXT UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash TEXT NOT NULL,
    access_type VARCHAR(20) DEFAULT 'trial',
    created_by_admin BOOLEAN DEFAULT FALSE,
    trial_resumes_analyzed INTEGER DEFAULT 0,
    trial_legal_queries INTEGER DEFAULT 0,
    trial_resume_limit INTEGER DEFAULT 100,
    trial_legal_limit INTEGER DEFAULT 50,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =======================
-- 6. Insert default admin user and AI settings
-- =======================
-- Ensure UUID extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insert default admin user profile in user_profiles table (for compatibility)
INSERT INTO user_profiles (id, email, name, company, access_type, is_active)
VALUES (
    uuid_generate_v4(),
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

-- Insert admin user in users table (for authentication) with bcrypt hash of "Benzie1!Benzie1!Benzie1!"
-- This is the bcrypt hash for the password "Benzie1!Benzie1!Benzie1!"
INSERT INTO users (email, name, password_hash, access_type, created_by_admin, trial_resume_limit, trial_legal_limit)
VALUES (
    'admin@bearsystems.co.in',
    'System Administrator', 
    '$2b$12$k.eL4qWYU2QiBRdZSx9PfOeyVEdu4ok8LfhZryv/TpDoCcSaHaDbG',  -- bcrypt hash of "Benzie1!Benzie1!Benzie1!"
    'enterprise',
    true,
    10000,
    5000
) ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    access_type = EXCLUDED.access_type,
    trial_resume_limit = EXCLUDED.trial_resume_limit,
    trial_legal_limit = EXCLUDED.trial_legal_limit,
    updated_at = NOW();

-- Alternative: Create admin user with username "admin" as well
INSERT INTO users (email, name, password_hash, access_type, created_by_admin, trial_resume_limit, trial_legal_limit)
VALUES (
    'admin',  -- This allows login with username "admin"
    'System Administrator', 
    '$2b$12$k.eL4qWYU2QiBRdZSx9PfOeyVEdu4ok8LfhZryv/TpDoCcSaHaDbG',  -- bcrypt hash of "Benzie1!Benzie1!Benzie1!"
    'enterprise',
    true,
    10000,
    5000
) ON CONFLICT (email) DO UPDATE SET
    name = EXCLUDED.name,
    access_type = EXCLUDED.access_type,
    trial_resume_limit = EXCLUDED.trial_resume_limit,
    trial_legal_limit = EXCLUDED.trial_legal_limit,
    updated_at = NOW();

-- Insert default AI settings for admin
INSERT INTO user_ai_settings (user_id, ai_provider, ai_model, enabled, priority, config)
VALUES 
    ('admin', 'openai', 'gpt-4', true, 1, '{"temperature": 0.7, "max_tokens": 2000}'),
    ('admin', 'anthropic', 'claude-3-sonnet-20240229', true, 2, '{"temperature": 0.7, "max_tokens": 2000}'),
    ('admin', 'ollama', 'qwen2.5:14b', true, 3, '{"temperature": 0.7, "num_predict": 2000}')
ON CONFLICT (user_id, ai_provider, ai_model) DO UPDATE SET
    enabled = EXCLUDED.enabled,
    priority = EXCLUDED.priority,
    config = EXCLUDED.config,
    updated_at = NOW();

-- Insert default admin credits
DO $$
DECLARE
    admin_user_id UUID;
    admin_users_id INTEGER;
BEGIN
    -- Get the admin user ID from user_profiles table
    SELECT id INTO admin_user_id 
    FROM user_profiles 
    WHERE email = 'admin@bearsystems.co.in';
    
    -- Get the admin user ID from users table  
    SELECT id INTO admin_users_id
    FROM users 
    WHERE email = 'admin@bearsystems.co.in' OR email = 'admin';
    
    -- Insert credits for user_profiles table admin user
    IF admin_user_id IS NOT NULL THEN
        INSERT INTO user_credits (user_id, trial_credits, premium_credits, total_used)
        VALUES (
            admin_user_id,
            10000,
            50000,
            0
        ) ON CONFLICT (user_id) DO UPDATE SET
            trial_credits = GREATEST(user_credits.trial_credits, 10000),
            premium_credits = GREATEST(user_credits.premium_credits, 50000),
            updated_at = NOW();
        
        RAISE NOTICE 'Admin credits configured for user_profiles ID: %', admin_user_id;
    ELSE
        RAISE NOTICE 'Admin user not found in user_profiles, skipping credits setup';
    END IF;
    
    RAISE NOTICE 'Admin user setup completed. Login credentials: admin / Benzie1!Benzie1!Benzie1!';
    RAISE NOTICE 'Users table admin ID: %', admin_users_id;
END $$;

-- =======================
-- 7. Create all necessary indexes safely
-- =======================
-- Core indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_access_type ON user_profiles(access_type);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);

-- Core indexes for users table (authentication)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_access_type ON users(access_type);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_supabase_id ON users(supabase_id);

CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_trial_exhausted ON user_credits(is_trial_exhausted);

CREATE INDEX IF NOT EXISTS idx_user_ai_settings_user_id ON user_ai_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_enabled ON user_ai_settings(enabled);
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_priority ON user_ai_settings(priority);

-- Resume indexes (only create if analysis_results column exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'resumes' AND column_name = 'analysis_results') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_resumes_analysis_results ON resumes USING GIN(analysis_results)';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_processing_status ON resumes(processing_status);
CREATE INDEX IF NOT EXISTS idx_resumes_upload_date ON resumes(upload_date);
CREATE INDEX IF NOT EXISTS idx_resumes_overall_score ON resumes(overall_score);
CREATE INDEX IF NOT EXISTS idx_resumes_skills ON resumes USING GIN(skills);

-- Usage analytics indexes (handle both timestamp and created_at)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'usage_analytics' AND column_name = 'timestamp') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_usage_analytics_timestamp ON usage_analytics(timestamp)';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'usage_analytics' AND column_name = 'created_at') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_usage_analytics_created_at ON usage_analytics(created_at)';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_feature_used ON usage_analytics(feature_used);

-- =======================
-- 8. Update any NULL values safely
-- =======================
-- Update resumes with NULL skills to empty JSONB array
UPDATE resumes 
SET skills = '[]'::jsonb 
WHERE skills IS NULL;

-- Update user_profiles with missing access_type
UPDATE user_profiles 
SET access_type = 'trial' 
WHERE access_type IS NULL;

-- Update user_profiles with missing is_active
UPDATE user_profiles 
SET is_active = TRUE 
WHERE is_active IS NULL;

-- =======================
-- SUCCESS MESSAGE & VALIDATION
-- =======================
DO $$
DECLARE
    missing_tables TEXT[] := '{}';
    missing_columns TEXT[] := '{}';
    table_name TEXT;
    column_name TEXT;
BEGIN
    -- Check for missing critical tables
    FOR table_name IN 
        SELECT unnest(ARRAY['user_profiles', 'users', 'user_credits', 'user_ai_settings', 'resumes', 'usage_analytics'])
    LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    -- Check for missing critical columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'name') THEN
        missing_columns := array_append(missing_columns, 'user_profiles.name');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_hash') THEN
        missing_columns := array_append(missing_columns, 'users.password_hash');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_credits' AND column_name = 'trial_credits') THEN
        missing_columns := array_append(missing_columns, 'user_credits.trial_credits');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'resumes' AND column_name = 'skills') THEN
        missing_columns := array_append(missing_columns, 'resumes.skills');
    END IF;
    
    -- Report results
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE WARNING '⚠️ Missing tables: %', array_to_string(missing_tables, ', ');
    END IF;
    
    IF array_length(missing_columns, 1) > 0 THEN
        RAISE WARNING '⚠️ Missing columns: %', array_to_string(missing_columns, ', ');
    END IF;
    
    IF array_length(missing_tables, 1) = 0 AND array_length(missing_columns, 1) = 0 THEN
        RAISE NOTICE '✅ Comprehensive database schema fix completed successfully!';
        RAISE NOTICE '🔧 All missing columns have been added';
        RAISE NOTICE '📊 All indexes have been created safely';
        RAISE NOTICE '👤 Default admin user and settings configured';
        RAISE NOTICE '🔑 Admin Login Credentials:';
        RAISE NOTICE '   Username: admin';
        RAISE NOTICE '   Password: Benzie1!Benzie1!Benzie1!';
        RAISE NOTICE '   Email: admin@bearsystems.co.in';
        RAISE NOTICE '✨ Database is now ready for Railway deployment';
    ELSE
        RAISE WARNING '⚠️ Schema fix completed with some issues - manual review required';
    END IF;
END $$;
