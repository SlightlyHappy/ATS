-- ==========================================================================
-- COMPLETE RESUME SCREENING APP - SUPABASE DATABASE SCHEMA V3
-- ==========================================================================
-- This script creates a comprehensive database schema with:
-- - User authentication and management
-- - Resume storage and analysis
-- - Activity tracking and analytics
-- - Trial/subscription management
-- - HR Legal compliance tracking
-- - System configuration and settings
--
-- INSTRUCTIONS:
-- 1. Copy this entire script
-- 2. Go to your Supabase Dashboard → SQL Editor
-- 3. Paste and run this script
-- 4. Enable Authentication in Supabase Dashboard
-- 5. Configure your frontend with Supabase keys
-- ==========================================================================

-- Clean slate: Drop existing objects if they exist (for re-runs)
DO $$
BEGIN
    -- Drop all policies first (only if tables exist)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_profiles') THEN
        DROP POLICY IF EXISTS "users_own_data" ON user_profiles;
        DROP POLICY IF EXISTS "admins_can_view_all" ON user_profiles;
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'resumes') THEN
        DROP POLICY IF EXISTS "users_own_resumes" ON resumes;
        DROP POLICY IF EXISTS "admins_can_view_all_resumes" ON resumes;
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_activity') THEN
        DROP POLICY IF EXISTS "users_own_activity" ON user_activity;
        DROP POLICY IF EXISTS "admins_can_view_all_activity" ON user_activity;
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'hr_legal_queries') THEN
        DROP POLICY IF EXISTS "users_own_legal_queries" ON hr_legal_queries;
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'system_config') THEN
        DROP POLICY IF EXISTS "public_access_system_config" ON system_config;
        DROP POLICY IF EXISTS "authenticated_access_system_config" ON system_config;
        DROP POLICY IF EXISTS "admin_manage_system_config" ON system_config;
    END IF;
    
    -- Drop triggers (only if tables exist)
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_profiles') THEN
        DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'resumes') THEN
        DROP TRIGGER IF EXISTS update_resumes_updated_at ON resumes;
        DROP TRIGGER IF EXISTS log_resume_activity ON resumes;
        DROP TRIGGER IF EXISTS update_trial_usage ON resumes;
        DROP TRIGGER IF EXISTS check_trial_limits_trigger ON resumes;
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_activity') THEN
        DROP TRIGGER IF EXISTS update_user_activity_updated_at ON user_activity;
    END IF;
    
    -- Drop trigger on auth.users if it exists
    IF EXISTS (SELECT FROM information_schema.triggers WHERE trigger_schema = 'auth' AND trigger_name = 'on_auth_user_created') THEN
        DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
    END IF;
    
    DROP VIEW IF EXISTS user_analytics;
    DROP VIEW IF EXISTS resume_stats;
    DROP VIEW IF EXISTS system_analytics;
    
    DROP FUNCTION IF EXISTS update_updated_at_column();
    DROP FUNCTION IF EXISTS log_user_activity();
    DROP FUNCTION IF EXISTS increment_trial_usage();
    DROP FUNCTION IF EXISTS check_trial_limits();
    
    DROP TABLE IF EXISTS hr_legal_queries CASCADE;
    DROP TABLE IF EXISTS user_activity CASCADE;
    DROP TABLE IF EXISTS system_config CASCADE;
    DROP TABLE IF EXISTS resumes CASCADE;
    DROP TABLE IF EXISTS user_profiles CASCADE;
END $$;

-- ==========================================================================
-- 1. CREATE CORE TABLES
-- ==========================================================================

-- User Profiles Table (extends Supabase auth.users)
CREATE TABLE user_profiles (
    -- Link to Supabase auth.users
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Basic user information
    full_name TEXT,
    email TEXT UNIQUE NOT NULL,
    company_name TEXT,
    job_title TEXT,
    phone TEXT,
    
    -- Account type and permissions
    access_type TEXT DEFAULT 'trial' CHECK (access_type IN ('trial', 'full', 'enterprise')),
    is_admin BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Trial management
    trial_start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trial_end_date TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days'),
    trial_usage INTEGER DEFAULT 0,
    trial_limit INTEGER DEFAULT 100,
    
    -- Subscription information
    subscription_id TEXT,
    subscription_status TEXT DEFAULT 'trial' CHECK (subscription_status IN ('trial', 'active', 'cancelled', 'expired')),
    subscription_start_date TIMESTAMP WITH TIME ZONE,
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    
    -- User preferences
    preferences JSONB DEFAULT '{}',
    ai_settings JSONB DEFAULT '{}',
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced Resumes Table
CREATE TABLE resumes (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- User association
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- File metadata
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER DEFAULT 0 CHECK (file_size >= 0),
    file_type TEXT DEFAULT 'pdf',
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Processing information
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    
    -- Compressed resume data (full resume info stored as compressed JSON)
    compressed_content TEXT NOT NULL,
    raw_text TEXT, -- Extracted text for search
    
    -- Extracted fields for easy querying and filtering
    candidate_name TEXT DEFAULT '',
    candidate_email TEXT DEFAULT '',
    candidate_phone TEXT DEFAULT '',
    skills TEXT[] DEFAULT '{}',
    experience_years INTEGER DEFAULT 0 CHECK (experience_years >= 0 AND experience_years <= 100),
    education_level TEXT DEFAULT '',
    
    -- AI Analysis scores (0-100 range)
    overall_score INTEGER DEFAULT 0 CHECK (overall_score >= 0 AND overall_score <= 100),
    technical_score INTEGER DEFAULT 0 CHECK (technical_score >= 0 AND technical_score <= 100),
    experience_score INTEGER DEFAULT 0 CHECK (experience_score >= 0 AND experience_score <= 100),
    education_score INTEGER DEFAULT 0 CHECK (education_score >= 0 AND education_score <= 100),
    role_fit_score INTEGER DEFAULT 0 CHECK (role_fit_score >= 0 AND role_fit_score <= 100),
    
    -- AI Analysis details
    ai_feedback TEXT,
    ai_model_used TEXT,
    ai_processing_time INTEGER, -- milliseconds
    
    -- Additional metadata for search and analytics
    job_titles TEXT[] DEFAULT '{}',
    companies TEXT[] DEFAULT '{}',
    programming_languages TEXT[] DEFAULT '{}',
    certifications TEXT[] DEFAULT '{}',
    location_info JSONB DEFAULT '{}',
    
    -- Resume categorization and tagging
    tags TEXT[] DEFAULT '{}',
    category TEXT DEFAULT 'general',
    priority INTEGER DEFAULT 0,
    
    -- Status tracking
    is_shortlisted BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    notes TEXT,
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Activity Tracking Table
CREATE TABLE user_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Activity details
    activity_type TEXT NOT NULL CHECK (activity_type IN (
        'login', 'logout', 'upload_resume', 'analyze_resume', 'export_data',
        'update_settings', 'view_dashboard', 'hr_legal_query', 'admin_action',
        'trial_upgrade', 'subscription_change', 'error_occurred'
    )),
    activity_description TEXT,
    
    -- Context and metadata
    resource_type TEXT, -- 'resume', 'user', 'system', etc.
    resource_id UUID, -- ID of the resource being acted upon
    metadata JSONB DEFAULT '{}',
    
    -- Technical details
    ip_address INET,
    user_agent TEXT,
    session_id TEXT,
    
    -- Result and performance
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    processing_time INTEGER, -- milliseconds
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HR Legal Queries Table
CREATE TABLE hr_legal_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Query details
    query_text TEXT NOT NULL,
    query_category TEXT DEFAULT 'general' CHECK (query_category IN (
        'general', 'compliance', 'hiring_law', 'discrimination', 'privacy',
        'labor_rights', 'termination', 'workplace_safety', 'benefits'
    )),
    
    -- Response details
    response_text TEXT,
    confidence_score DECIMAL(5,2),
    sources JSONB DEFAULT '[]',
    
    -- AI processing information
    ai_model_used TEXT,
    processing_time INTEGER, -- milliseconds
    processing_status TEXT DEFAULT 'completed' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- User feedback
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System Configuration Table
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Configuration details
    config_key TEXT UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    config_type TEXT DEFAULT 'general' CHECK (config_type IN (
        'general', 'ai_models', 'trial_limits', 'subscription_plans',
        'email_templates', 'legal_sources', 'feature_flags'
    )),
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false, -- Can be accessed without authentication
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================================================
-- 2. CREATE PERFORMANCE INDEXES
-- ==========================================================================

-- User Profiles Indexes
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_access_type ON user_profiles(access_type);
CREATE INDEX idx_user_profiles_trial_usage ON user_profiles(trial_usage);
CREATE INDEX idx_user_profiles_subscription_status ON user_profiles(subscription_status);
CREATE INDEX idx_user_profiles_last_activity ON user_profiles(last_activity DESC);

-- Resumes Indexes
CREATE INDEX idx_resumes_user_id ON resumes(user_id);
CREATE INDEX idx_resumes_upload_date ON resumes(upload_date DESC);
CREATE INDEX idx_resumes_processing_status ON resumes(processing_status);
CREATE INDEX idx_resumes_overall_score ON resumes(overall_score DESC);
CREATE INDEX idx_resumes_candidate_name ON resumes(candidate_name);
CREATE INDEX idx_resumes_candidate_email ON resumes(candidate_email);
CREATE INDEX idx_resumes_is_shortlisted ON resumes(is_shortlisted);
CREATE INDEX idx_resumes_is_archived ON resumes(is_archived);

-- Full-text search index for resume content
CREATE INDEX idx_resumes_raw_text ON resumes USING gin(to_tsvector('english', raw_text));

-- Array indexes for advanced search
CREATE INDEX idx_resumes_skills ON resumes USING GIN(skills);
CREATE INDEX idx_resumes_job_titles ON resumes USING GIN(job_titles);
CREATE INDEX idx_resumes_companies ON resumes USING GIN(companies);
CREATE INDEX idx_resumes_programming_languages ON resumes USING GIN(programming_languages);
CREATE INDEX idx_resumes_tags ON resumes USING GIN(tags);

-- Composite indexes for common query patterns
CREATE INDEX idx_resumes_user_status_score ON resumes(user_id, processing_status, overall_score DESC);
CREATE INDEX idx_resumes_user_date ON resumes(user_id, upload_date DESC);

-- User Activity Indexes
CREATE INDEX idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX idx_user_activity_created_at ON user_activity(created_at DESC);
CREATE INDEX idx_user_activity_resource ON user_activity(resource_type, resource_id);
CREATE INDEX idx_user_activity_session ON user_activity(session_id);

-- HR Legal Queries Indexes
CREATE INDEX idx_hr_legal_user_id ON hr_legal_queries(user_id);
CREATE INDEX idx_hr_legal_category ON hr_legal_queries(query_category);
CREATE INDEX idx_hr_legal_created_at ON hr_legal_queries(created_at DESC);
CREATE INDEX idx_hr_legal_rating ON hr_legal_queries(user_rating);

-- System Config Indexes
CREATE INDEX idx_system_config_key ON system_config(config_key);
CREATE INDEX idx_system_config_type ON system_config(config_type);
CREATE INDEX idx_system_config_active ON system_config(is_active);

-- ==========================================================================
-- 3. CREATE HELPER FUNCTIONS
-- ==========================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Function to log user activity
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    -- Log resume upload activity
    IF TG_OP = 'INSERT' THEN
        INSERT INTO user_activity (
            user_id,
            activity_type,
            activity_description,
            resource_type,
            resource_id,
            metadata
        ) VALUES (
            NEW.user_id,
            'upload_resume',
            'Uploaded resume: ' || NEW.filename,
            'resume',
            NEW.id,
            jsonb_build_object(
                'filename', NEW.filename,
                'file_size', NEW.file_size,
                'file_type', NEW.file_type
            )
        );
    END IF;
    
    -- Log resume analysis completion
    IF TG_OP = 'UPDATE' AND OLD.processing_status != NEW.processing_status AND NEW.processing_status = 'completed' THEN
        INSERT INTO user_activity (
            user_id,
            activity_type,
            activity_description,
            resource_type,
            resource_id,
            metadata
        ) VALUES (
            NEW.user_id,
            'analyze_resume',
            'Completed analysis for: ' || NEW.filename,
            'resume',
            NEW.id,
            jsonb_build_object(
                'overall_score', NEW.overall_score,
                'processing_time', NEW.ai_processing_time
            )
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$;

-- Function to increment trial usage
CREATE OR REPLACE FUNCTION increment_trial_usage()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    -- Only increment for trial users on successful resume processing
    IF TG_OP = 'UPDATE' AND OLD.processing_status != NEW.processing_status AND NEW.processing_status = 'completed' THEN
        UPDATE user_profiles 
        SET 
            trial_usage = trial_usage + 1,
            last_activity = NOW()
        WHERE id = NEW.user_id AND access_type = 'trial';
    END IF;
    
    RETURN NEW;
END;
$$;

-- Function to check trial limits
CREATE OR REPLACE FUNCTION check_trial_limits()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    user_trial_usage INTEGER;
    user_trial_limit INTEGER;
    user_access_type TEXT;
BEGIN
    -- Get user trial information
    SELECT trial_usage, trial_limit, access_type
    INTO user_trial_usage, user_trial_limit, user_access_type
    FROM user_profiles
    WHERE id = NEW.user_id;
    
    -- Check trial limits for trial users
    IF user_access_type = 'trial' AND user_trial_usage >= user_trial_limit THEN
        RAISE EXCEPTION 'Trial limit reached. Upgrade to continue using the service.';
    END IF;
    
    RETURN NEW;
END;
$$;

-- ==========================================================================
-- 4. CREATE TRIGGERS
-- ==========================================================================

-- Updated_at triggers
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resumes_updated_at
    BEFORE UPDATE ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_activity_updated_at
    BEFORE UPDATE ON user_activity
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Activity logging triggers
CREATE TRIGGER log_resume_activity
    AFTER INSERT OR UPDATE ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION log_user_activity();

-- Trial usage triggers
CREATE TRIGGER update_trial_usage
    AFTER UPDATE ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION increment_trial_usage();

CREATE TRIGGER check_trial_limits_trigger
    BEFORE INSERT ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION check_trial_limits();

-- ==========================================================================
-- 5. SETUP ROW LEVEL SECURITY (RLS)
-- ==========================================================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr_legal_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;

-- User Profiles Policies
CREATE POLICY "users_own_data" ON user_profiles
    FOR ALL
    USING (auth.uid() = id);

CREATE POLICY "admins_can_view_all" ON user_profiles
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Resumes Policies
CREATE POLICY "users_own_resumes" ON resumes
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_can_view_all_resumes" ON resumes
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- User Activity Policies
CREATE POLICY "users_own_activity" ON user_activity
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_can_view_all_activity" ON user_activity
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- HR Legal Queries Policies
CREATE POLICY "users_own_legal_queries" ON hr_legal_queries
    FOR ALL
    USING (auth.uid() = user_id);

-- System Config Policies
CREATE POLICY "public_access_system_config" ON system_config
    FOR SELECT
    USING (is_public = true);

CREATE POLICY "authenticated_access_system_config" ON system_config
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "admin_manage_system_config" ON system_config
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ==========================================================================
-- 6. CREATE ANALYTICS VIEWS
-- ==========================================================================

-- User Analytics View
CREATE VIEW user_analytics AS
SELECT 
    -- User counts
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE access_type = 'trial') as trial_users,
    COUNT(*) FILTER (WHERE access_type = 'full') as full_users,
    COUNT(*) FILTER (WHERE access_type = 'enterprise') as enterprise_users,
    COUNT(*) FILTER (WHERE is_active = true) as active_users,
    COUNT(*) FILTER (WHERE is_admin = true) as admin_users,
    
    -- Trial analytics
    ROUND(AVG(trial_usage) FILTER (WHERE access_type = 'trial'), 2) as avg_trial_usage,
    MAX(trial_usage) FILTER (WHERE access_type = 'trial') as max_trial_usage,
    COUNT(*) FILTER (WHERE access_type = 'trial' AND trial_usage >= trial_limit) as trial_limit_reached,
    
    -- Activity analytics
    COUNT(*) FILTER (WHERE last_activity >= NOW() - INTERVAL '24 hours') as active_last_24h,
    COUNT(*) FILTER (WHERE last_activity >= NOW() - INTERVAL '7 days') as active_last_7d,
    COUNT(*) FILTER (WHERE last_activity >= NOW() - INTERVAL '30 days') as active_last_30d,
    
    -- Registration analytics
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as new_users_24h,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as new_users_7d,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as new_users_30d
FROM user_profiles;

-- Enhanced Resume Stats View
CREATE VIEW resume_stats AS
SELECT 
    -- Overall counts
    COUNT(*) as total_resumes,
    COUNT(DISTINCT user_id) as unique_users_with_resumes,
    
    -- Processing status counts
    COUNT(*) FILTER (WHERE processing_status = 'completed') as completed_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'processing') as processing_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_resumes,
    
    -- User type breakdown
    COUNT(*) FILTER (WHERE user_id IN (SELECT id FROM user_profiles WHERE access_type = 'trial')) as trial_user_resumes,
    COUNT(*) FILTER (WHERE user_id IN (SELECT id FROM user_profiles WHERE access_type = 'full')) as full_user_resumes,
    COUNT(*) FILTER (WHERE user_id IN (SELECT id FROM user_profiles WHERE access_type = 'enterprise')) as enterprise_user_resumes,
    
    -- Score analytics (only for completed resumes)
    ROUND(AVG(overall_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_overall_score,
    ROUND(AVG(technical_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_technical_score,
    ROUND(AVG(experience_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_experience_score,
    ROUND(AVG(education_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_education_score,
    ROUND(AVG(role_fit_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_role_fit_score,
    
    -- Score ranges
    MAX(overall_score) as max_overall_score,
    MIN(overall_score) FILTER (WHERE overall_score > 0) as min_overall_score,
    
    -- File analytics
    SUM(file_size) as total_storage_bytes,
    ROUND(AVG(file_size), 0) as avg_file_size_bytes,
    
    -- Performance analytics
    ROUND(AVG(ai_processing_time) FILTER (WHERE ai_processing_time > 0), 2) as avg_processing_time_ms,
    
    -- Date ranges
    MAX(upload_date) as latest_upload,
    MIN(upload_date) as first_upload,
    
    -- Activity counts
    COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '24 hours') as uploads_last_24h,
    COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '7 days') as uploads_last_7d,
    COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '30 days') as uploads_last_30d
FROM resumes;

-- System Analytics View
CREATE VIEW system_analytics AS
SELECT 
    -- Activity analytics
    COUNT(*) as total_activities,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) FILTER (WHERE activity_type = 'login') as total_logins,
    COUNT(*) FILTER (WHERE activity_type = 'upload_resume') as total_uploads,
    COUNT(*) FILTER (WHERE activity_type = 'analyze_resume') as total_analyses,
    COUNT(*) FILTER (WHERE activity_type = 'hr_legal_query') as total_legal_queries,
    COUNT(*) FILTER (WHERE success = false) as total_errors,
    
    -- Performance analytics
    ROUND(AVG(processing_time) FILTER (WHERE processing_time > 0), 2) as avg_processing_time_ms,
    
    -- Recent activity
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as activities_last_24h,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as activities_last_7d,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as activities_last_30d
FROM user_activity;

-- ==========================================================================
-- 7. INSERT INITIAL SYSTEM CONFIGURATION
-- ==========================================================================

-- Trial limits configuration
INSERT INTO system_config (config_key, config_value, config_type, description, is_public) VALUES
('trial_limits', '{"max_resumes": 100, "duration_days": 30, "features": ["upload", "analysis", "basic_export"]}', 'trial_limits', 'Default trial account limitations', true),
('subscription_plans', '{"full": {"price": 29.99, "features": ["unlimited_resumes", "advanced_analytics", "csv_export", "hr_legal"]}, "enterprise": {"price": 99.99, "features": ["everything", "priority_support", "custom_integrations"]}}', 'subscription_plans', 'Available subscription plans', true),
('ai_models', '{"default": "ollama:llama3", "available": ["ollama:llama3", "openai:gpt-4", "anthropic:claude"]}', 'ai_models', 'Available AI models for resume analysis', false),
('feature_flags', '{"hr_legal_enabled": true, "advanced_search": true, "bulk_upload": true}', 'feature_flags', 'System feature toggles', false),
('email_templates', '{"welcome": "Welcome to Resume Screening App!", "trial_expiring": "Your trial expires soon", "upgrade_prompt": "Upgrade to continue"}', 'email_templates', 'Email notification templates', false);

-- HR Legal sources configuration
INSERT INTO system_config (config_key, config_value, config_type, description, is_public) VALUES
('hr_legal_sources', '{"indian_laws": ["Industrial Relations Code 2020", "Wages Code 2019", "Social Security Code 2020"], "international": ["ILO Conventions", "GDPR Guidelines"]}', 'legal_sources', 'Legal knowledge base sources', false);

-- ==========================================================================
-- 8. CREATE ADMIN USER FUNCTION (Call this after first user signs up)
-- ==========================================================================

CREATE OR REPLACE FUNCTION setup_admin_user(user_email TEXT)
RETURNS VOID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE user_profiles 
    SET 
        is_admin = true,
        access_type = 'enterprise',
        trial_limit = 999999
    WHERE email = user_email;
    
    -- Log admin creation
    INSERT INTO user_activity (
        user_id,
        activity_type,
        activity_description
    ) 
    SELECT 
        id,
        'admin_action',
        'Admin privileges granted'
    FROM user_profiles 
    WHERE email = user_email;
END;
$$;

-- ==========================================================================
-- 9. CREATE USER PROFILE TRIGGER FOR NEW SIGNUPS
-- ==========================================================================

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO user_profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
    );
    
    -- Log signup activity
    INSERT INTO user_activity (
        user_id,
        activity_type,
        activity_description,
        metadata
    ) VALUES (
        NEW.id,
        'login',
        'New user signup',
        jsonb_build_object(
            'signup_method', COALESCE(NEW.raw_user_meta_data->>'provider', 'email'),
            'email', NEW.email
        )
    );
    
    RETURN NEW;
END;
$$;

-- Create trigger for new user signups
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ==========================================================================
-- 10. GRANT PERMISSIONS
-- ==========================================================================

-- Grant table permissions
GRANT ALL ON user_profiles TO anon, authenticated;
GRANT ALL ON resumes TO anon, authenticated;
GRANT ALL ON user_activity TO anon, authenticated;
GRANT ALL ON hr_legal_queries TO anon, authenticated;
GRANT SELECT ON system_config TO anon, authenticated;
GRANT INSERT, UPDATE, DELETE ON system_config TO authenticated;

-- Grant view permissions
GRANT SELECT ON user_analytics TO authenticated;
GRANT SELECT ON resume_stats TO authenticated;
GRANT SELECT ON system_analytics TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Grant function permissions
GRANT EXECUTE ON FUNCTION setup_admin_user(TEXT) TO authenticated;

-- ==========================================================================
-- 11. VERIFICATION AND SUCCESS REPORTING
-- ==========================================================================
DO $$
DECLARE
    tables_count INTEGER;
    indexes_count INTEGER;
    policies_count INTEGER;
    triggers_count INTEGER;
    functions_count INTEGER;
    config_count INTEGER;
BEGIN
    -- Count created objects
    SELECT COUNT(*) INTO tables_count FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('user_profiles', 'resumes', 'user_activity', 'hr_legal_queries', 'system_config');
    SELECT COUNT(*) INTO indexes_count FROM pg_indexes WHERE schemaname = 'public' AND tablename IN ('user_profiles', 'resumes', 'user_activity', 'hr_legal_queries', 'system_config');
    SELECT COUNT(*) INTO policies_count FROM pg_policies WHERE schemaname = 'public';
    SELECT COUNT(*) INTO triggers_count FROM information_schema.triggers WHERE trigger_schema = 'public';
    SELECT COUNT(*) INTO functions_count FROM information_schema.routines WHERE routine_schema = 'public' AND routine_type = 'FUNCTION';
    SELECT COUNT(*) INTO config_count FROM system_config;
    
    -- Report results
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'COMPLETE SUPABASE SCHEMA SETUP COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'Tables created: %', tables_count;
    RAISE NOTICE 'Indexes created: %', indexes_count;
    RAISE NOTICE 'Security policies: %', policies_count;
    RAISE NOTICE 'Triggers created: %', triggers_count;
    RAISE NOTICE 'Functions created: %', functions_count;
    RAISE NOTICE 'System configs: %', config_count;
    RAISE NOTICE '==========================================================================';
    
    IF tables_count < 5 THEN
        RAISE EXCEPTION 'ERROR: Table creation incomplete!';
    END IF;
    
    RAISE NOTICE 'NEXT STEPS:';
    RAISE NOTICE '1. Enable Authentication in Supabase Dashboard';
    RAISE NOTICE '2. Configure your environment variables with Supabase keys';
    RAISE NOTICE '3. Update your frontend to use Supabase auth';
    RAISE NOTICE '4. Test user signup and resume upload';
    RAISE NOTICE '5. Call setup_admin_user(''your-email@domain.com'') to create admin';
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'Your complete Resume Screening App database is ready!';
    RAISE NOTICE '==========================================================================';
END $$;

-- Final verification queries
SELECT 'SUCCESS: User profiles ready' as status, COUNT(*) as record_count FROM user_profiles;
SELECT 'SUCCESS: System config ready' as status, COUNT(*) as record_count FROM system_config;
SELECT 'SUCCESS: Views created' as status, 
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'user_analytics') THEN 'Yes' ELSE 'No' END as analytics_ready;
