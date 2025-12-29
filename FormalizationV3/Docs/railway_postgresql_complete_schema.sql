-- ==========================================================================
-- RAILWAY POSTGRESQL COMPLETE SCHEMA FOR RESUME ANALYSIS SYSTEM
-- Production-Ready Resume Upload and AI Analysis Storage
-- ==========================================================================
-- This script creates the complete database schema for Railway PostgreSQL
-- including the resumes table with AI analysis fields
--
-- FEATURES:
-- - Resume storage with comprehensive AI analysis fields
-- - User management and activity tracking
-- - Performance indexes for production queries
-- - Proper data types and constraints
-- - AI analysis result storage (JSON fields)
-- ==========================================================================

-- ==========================================================================
-- 1. CORE TABLES
-- ==========================================================================

-- Extended Users Table (compatible with existing schema)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    supabase_id VARCHAR(255),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    access_type VARCHAR(50) DEFAULT 'trial',
    trial_resumes_analyzed BIGINT DEFAULT 0,
    trial_legal_queries BIGINT DEFAULT 0,
    trial_resume_limit BIGINT DEFAULT 100,
    trial_legal_limit BIGINT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_admin VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    last_login TIMESTAMP,
    metadata TEXT
);

-- ==========================================================================
-- 2. RESUMES TABLE - MAIN FEATURE TABLE
-- ==========================================================================

-- Comprehensive Resumes Table for AI Analysis Storage
CREATE TABLE IF NOT EXISTS resumes (
    -- Primary identifier (UUID as string for compatibility)
    id VARCHAR(255) PRIMARY KEY,
    
    -- User association (compatible with Railway's BIGINT user IDs and UUID admin IDs)
    user_id VARCHAR(255) NOT NULL, -- Can handle both BIGINT and UUID
    
    -- File metadata
    filename VARCHAR(500) NOT NULL,
    file_hash VARCHAR(255) NOT NULL,
    file_size BIGINT DEFAULT 0 CHECK (file_size >= 0),
    file_type VARCHAR(20) DEFAULT 'pdf',
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Processing information
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    processing_error TEXT,
    
    -- Resume content storage
    compressed_content TEXT NOT NULL, -- Compressed full resume data
    raw_text TEXT, -- Extracted text for search
    processed_content TEXT, -- Processed/cleaned content
    
    -- Extracted candidate information
    candidate_name VARCHAR(255) DEFAULT '',
    candidate_email VARCHAR(255) DEFAULT '',
    candidate_phone VARCHAR(50) DEFAULT '',
    skills TEXT[], -- PostgreSQL array for skills
    experience_years INTEGER DEFAULT 0 CHECK (experience_years >= 0 AND experience_years <= 100),
    education_level VARCHAR(100) DEFAULT '',
    
    -- AI Analysis Scores (0-100 range)
    overall_score INTEGER DEFAULT 0 CHECK (overall_score >= 0 AND overall_score <= 100),
    technical_score INTEGER DEFAULT 0 CHECK (technical_score >= 0 AND technical_score <= 100),
    experience_score INTEGER DEFAULT 0 CHECK (experience_score >= 0 AND experience_score <= 100),
    education_score INTEGER DEFAULT 0 CHECK (education_score >= 0 AND education_score <= 100),
    role_fit_score INTEGER DEFAULT 0 CHECK (role_fit_score >= 0 AND role_fit_score <= 100),
    
    -- AI Analysis Details
    ai_feedback TEXT,
    ai_model_used VARCHAR(100),
    ai_processing_time INTEGER, -- milliseconds
    
    -- Additional extracted information arrays
    job_titles TEXT[], -- Previous job titles
    companies TEXT[], -- Previous companies
    programming_languages TEXT[], -- Programming skills
    certifications TEXT[], -- Certifications
    
    -- Resume categorization and tagging
    tags TEXT[],
    category VARCHAR(50) DEFAULT 'general',
    priority INTEGER DEFAULT 0,
    
    -- Status flags
    is_shortlisted BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    notes TEXT,
    
    -- AI Analysis Result Storage (COMPREHENSIVE)
    analysis_result JSONB, -- Complete AI analysis result as JSON
    agent_insights JSONB, -- Multi-agent insights
    consensus_score DECIMAL(5,2), -- AI consensus score
    legal_compliance JSONB, -- Legal compliance analysis
    similarity_score DECIMAL(5,2), -- Resume similarity score
    
    -- Location and contact information
    location_info JSONB DEFAULT '{}',
    
    -- Audit timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================================
-- 3. USER ACTIVITY TRACKING
-- ==========================================================================

-- User Activity Table for comprehensive tracking
CREATE TABLE IF NOT EXISTS user_activity (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    
    -- Activity details
    activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN (
        'login', 'logout', 'upload_resume', 'analyze_resume', 'export_data',
        'trial_upgrade', 'subscription_change', 'error_occurred'
    )),
    activity_description TEXT,
    
    -- Context and metadata
    resource_type VARCHAR(50), -- 'resume', 'user', 'system', etc.
    resource_id VARCHAR(255), -- ID of the resource being acted upon
    metadata JSONB DEFAULT '{}',
    
    -- Technical details
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Result and performance
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    processing_time INTEGER, -- milliseconds
    
    -- Details (for backward compatibility)
    details JSONB DEFAULT '{}',
    
    -- Timestamps
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================================
-- 4. HR LEGAL QUERIES TABLE
-- ==========================================================================

-- HR Legal Queries for legal compliance analysis
CREATE TABLE IF NOT EXISTS hr_legal_queries (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    
    -- Query details
    query_text TEXT NOT NULL,
    response_text TEXT,
    category VARCHAR(50) DEFAULT 'general' CHECK (category IN (
        'general', 'compliance', 'hiring_law', 'discrimination', 'privacy',
        'labor_rights', 'termination', 'workplace_safety', 'benefits'
    )),
    confidence_score DECIMAL(5,2),
    
    -- AI processing information
    ai_model_used VARCHAR(100),
    processing_time INTEGER, -- milliseconds
    processing_status VARCHAR(20) DEFAULT 'completed' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- Sources and metadata
    sources JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================================
-- 5. PERFORMANCE INDEXES
-- ==========================================================================

-- Resume table indexes for production performance
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_upload_date ON resumes(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_resumes_processing_status ON resumes(processing_status);
CREATE INDEX IF NOT EXISTS idx_resumes_overall_score ON resumes(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_resumes_candidate_name ON resumes(candidate_name);
CREATE INDEX IF NOT EXISTS idx_resumes_candidate_email ON resumes(candidate_email);
CREATE INDEX IF NOT EXISTS idx_resumes_file_hash ON resumes(file_hash);
CREATE INDEX IF NOT EXISTS idx_resumes_is_shortlisted ON resumes(is_shortlisted);
CREATE INDEX IF NOT EXISTS idx_resumes_category ON resumes(category);

-- Full-text search index for resume content
CREATE INDEX IF NOT EXISTS idx_resumes_raw_text_search ON resumes USING gin(to_tsvector('english', raw_text));
CREATE INDEX IF NOT EXISTS idx_resumes_processed_content_search ON resumes USING gin(to_tsvector('english', processed_content));

-- Array indexes for skills and tags search
CREATE INDEX IF NOT EXISTS idx_resumes_skills ON resumes USING GIN(skills);
CREATE INDEX IF NOT EXISTS idx_resumes_job_titles ON resumes USING GIN(job_titles);
CREATE INDEX IF NOT EXISTS idx_resumes_companies ON resumes USING GIN(companies);
CREATE INDEX IF NOT EXISTS idx_resumes_programming_languages ON resumes USING GIN(programming_languages);
CREATE INDEX IF NOT EXISTS idx_resumes_tags ON resumes USING GIN(tags);

-- JSON indexes for AI analysis results
CREATE INDEX IF NOT EXISTS idx_resumes_analysis_result ON resumes USING GIN(analysis_result);
CREATE INDEX IF NOT EXISTS idx_resumes_agent_insights ON resumes USING GIN(agent_insights);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_resumes_user_status_score ON resumes(user_id, processing_status, overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_resumes_user_date ON resumes(user_id, upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_resumes_status_date ON resumes(processing_status, upload_date DESC);

-- User activity indexes
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_activity_resource ON user_activity(resource_type, resource_id);

-- HR legal queries indexes
CREATE INDEX IF NOT EXISTS idx_hr_legal_user_id ON hr_legal_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_hr_legal_category ON hr_legal_queries(category);
CREATE INDEX IF NOT EXISTS idx_hr_legal_created_at ON hr_legal_queries(created_at DESC);

-- ==========================================================================
-- 6. FUNCTIONS AND TRIGGERS
-- ==========================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
DROP TRIGGER IF EXISTS update_resumes_updated_at ON resumes;
CREATE TRIGGER update_resumes_updated_at
    BEFORE UPDATE ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_activity_updated_at ON user_activity;
CREATE TRIGGER update_user_activity_updated_at
    BEFORE UPDATE ON user_activity
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_hr_legal_updated_at ON hr_legal_queries;
CREATE TRIGGER update_hr_legal_updated_at
    BEFORE UPDATE ON hr_legal_queries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================================================
-- 7. ANALYTICS VIEWS
-- ==========================================================================

-- Resume Analytics View
CREATE OR REPLACE VIEW resume_analytics AS
SELECT 
    COUNT(*) as total_resumes,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(*) FILTER (WHERE processing_status = 'completed') as completed_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'processing') as processing_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_resumes,
    ROUND(AVG(overall_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_overall_score,
    ROUND(AVG(technical_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_technical_score,
    ROUND(AVG(experience_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_experience_score,
    ROUND(AVG(ai_processing_time) FILTER (WHERE ai_processing_time > 0), 2) as avg_processing_time_ms,
    SUM(file_size) as total_storage_bytes,
    COUNT(*) FILTER (WHERE upload_date >= CURRENT_TIMESTAMP - INTERVAL '24 hours') as uploads_last_24h,
    COUNT(*) FILTER (WHERE upload_date >= CURRENT_TIMESTAMP - INTERVAL '7 days') as uploads_last_7d,
    COUNT(*) FILTER (WHERE upload_date >= CURRENT_TIMESTAMP - INTERVAL '30 days') as uploads_last_30d
FROM resumes;

-- System Health View
CREATE OR REPLACE VIEW system_health AS
SELECT 
    'resumes' as table_name,
    COUNT(*) as record_count,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_records
FROM resumes
UNION ALL
SELECT 
    'user_activity' as table_name,
    COUNT(*) as record_count,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_records
FROM user_activity
UNION ALL
SELECT 
    'hr_legal_queries' as table_name,
    COUNT(*) as record_count,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour') as recent_records
FROM hr_legal_queries;

-- ==========================================================================
-- 8. SAMPLE DATA FOR TESTING (Optional)
-- ==========================================================================

-- Sample resume record structure (commented out for production)
/*
INSERT INTO resumes (
    id, user_id, filename, file_hash, compressed_content, raw_text,
    processing_status, candidate_name, overall_score, 
    analysis_result, created_at
) VALUES (
    'sample-resume-001',
    'admin-user-001',
    'john_doe_resume.pdf',
    'sample-hash-123',
    'Sample compressed resume content...',
    'John Doe Software Engineer Experience: 5 years Skills: Python, JavaScript...',
    'completed',
    'John Doe',
    85,
    '{"overall_assessment": "Strong candidate", "technical_skills": ["Python", "JavaScript"], "experience_level": "Senior"}',
    CURRENT_TIMESTAMP
);
*/

-- ==========================================================================
-- 9. VERIFICATION QUERIES
-- ==========================================================================

-- Success message and verification
DO $$
BEGIN
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'RAILWAY POSTGRESQL RESUME ANALYSIS SCHEMA DEPLOYED SUCCESSFULLY!';
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'Tables created:';
    RAISE NOTICE '  - resumes (with comprehensive AI analysis fields)';
    RAISE NOTICE '  - user_activity (activity tracking)';
    RAISE NOTICE '  - hr_legal_queries (legal compliance)';
    RAISE NOTICE '  - users (extended with trial management)';
    RAISE NOTICE '';
    RAISE NOTICE 'Features enabled:';
    RAISE NOTICE '  ✅ Resume upload and storage';
    RAISE NOTICE '  ✅ AI analysis result storage (JSON fields)';
    RAISE NOTICE '  ✅ Full-text search capabilities';
    RAISE NOTICE '  ✅ Performance indexes for production';
    RAISE NOTICE '  ✅ Activity tracking and analytics';
    RAISE NOTICE '  ✅ Legal compliance queries';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Test resume upload functionality';
    RAISE NOTICE '  2. Verify AI analysis storage';
    RAISE NOTICE '  3. Check admin dashboard access';
    RAISE NOTICE '==========================================================================';
END $$;

-- Final verification
SELECT 'SUCCESS: Resumes table ready' as status, 
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'resumes') 
            THEN 'Created' ELSE 'Missing' END as resumes_table;

SELECT 'SUCCESS: Indexes ready' as status,
       COUNT(*) as index_count
FROM pg_indexes 
WHERE tablename IN ('resumes', 'user_activity', 'hr_legal_queries');
