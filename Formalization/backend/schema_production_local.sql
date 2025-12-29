-- ==========================================================================
-- RESUME SCREENING APP - PRODUCTION POSTGRESQL SCHEMA
-- ==========================================================================
-- This script creates a robust database schema for the resume screening
-- application adapted from Supabase schema for standard PostgreSQL.
-- ==========================================================================

-- Clean slate: Drop existing objects if they exist (for re-runs)
DO $$
BEGIN
    -- Drop triggers and policies if table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'resumes') THEN
        DROP TRIGGER IF EXISTS update_resumes_updated_at ON resumes;
    END IF;
    
    -- Drop view if exists
    DROP VIEW IF EXISTS resume_stats;
    
    -- Drop function if exists
    DROP FUNCTION IF EXISTS update_updated_at_column();
    
    -- Drop table if exists
    DROP TABLE IF EXISTS resumes CASCADE;
END $$;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==========================================================================
-- 1. CREATE MAIN RESUMES TABLE
-- ==========================================================================
CREATE TABLE resumes (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- File metadata
    filename TEXT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,
    file_size INTEGER DEFAULT 0 CHECK (file_size >= 0),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- User and processing information
    user_type TEXT DEFAULT 'free' CHECK (user_type IN ('free', 'paid', 'enterprise')),
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    
    -- Raw extracted text
    raw_text TEXT,
    
    -- Structured extracted information
    personal_info JSONB DEFAULT '{}'::jsonb,
    contact_info JSONB DEFAULT '{}'::jsonb,
    professional_summary TEXT,
    
    -- Skills and competencies
    skills JSONB DEFAULT '[]'::jsonb,
    technical_skills JSONB DEFAULT '[]'::jsonb,
    soft_skills JSONB DEFAULT '[]'::jsonb,
    certifications JSONB DEFAULT '[]'::jsonb,
    languages JSONB DEFAULT '[]'::jsonb,
    
    -- Work experience
    experience JSONB DEFAULT '[]'::jsonb,
    total_experience_years DECIMAL(4,2),
    current_position TEXT,
    current_company TEXT,
    
    -- Education
    education JSONB DEFAULT '[]'::jsonb,
    highest_education_level TEXT,
    field_of_study TEXT,
    graduation_year INTEGER,
    
    -- Additional sections
    projects JSONB DEFAULT '[]'::jsonb,
    achievements JSONB DEFAULT '[]'::jsonb,
    publications JSONB DEFAULT '[]'::jsonb,
    contact_references JSONB DEFAULT '[]'::jsonb,
    
    -- AI Analysis and Scoring
    ai_analysis JSONB DEFAULT '{}'::jsonb,
    overall_score DECIMAL(5,2) CHECK (overall_score >= 0 AND overall_score <= 100),
    technical_score DECIMAL(5,2) CHECK (technical_score >= 0 AND technical_score <= 100),
    experience_score DECIMAL(5,2) CHECK (experience_score >= 0 AND experience_score <= 100),
    education_score DECIMAL(5,2) CHECK (education_score >= 0 AND education_score <= 100),
    skills_score DECIMAL(5,2) CHECK (skills_score >= 0 AND skills_score <= 100),
    cultural_fit_score DECIMAL(5,2) CHECK (cultural_fit_score >= 0 AND cultural_fit_score <= 100),
    
    -- Role matching
    role_matches JSONB DEFAULT '[]'::jsonb,
    recommended_positions JSONB DEFAULT '[]'::jsonb,
    
    -- AI insights
    strengths JSONB DEFAULT '[]'::jsonb,
    weaknesses JSONB DEFAULT '[]'::jsonb,
    improvement_suggestions JSONB DEFAULT '[]'::jsonb,
    career_recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Keywords and tags for search
    keywords JSONB DEFAULT '[]'::jsonb,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Quality metrics
    completeness_score DECIMAL(5,2) CHECK (completeness_score >= 0 AND completeness_score <= 100),
    quality_indicators JSONB DEFAULT '{}'::jsonb,
    
    -- Processing metadata
    processing_time_ms INTEGER DEFAULT 0,
    model_version TEXT,
    ai_confidence_score DECIMAL(5,2) CHECK (ai_confidence_score >= 0 AND ai_confidence_score <= 100),
    
    -- Review and annotation
    human_reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT,
    review_date TIMESTAMP WITH TIME ZONE,
    
    -- Status and lifecycle
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    priority_level INTEGER DEFAULT 0 CHECK (priority_level >= 0 AND priority_level <= 5),
    
    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    
    -- Notes and comments
    internal_notes TEXT,
    candidate_feedback TEXT,
    
    -- Privacy and compliance
    consent_given BOOLEAN DEFAULT FALSE,
    data_retention_date TIMESTAMP WITH TIME ZONE,
    
    -- Search optimization (computed column)
    search_vector TEXT GENERATED ALWAYS AS (
        COALESCE(filename, '') || ' ' ||
        COALESCE(raw_text, '') || ' ' ||
        COALESCE(professional_summary, '') || ' ' ||
        COALESCE(current_position, '') || ' ' ||
        COALESCE(current_company, '') || ' ' ||
        COALESCE(field_of_study, '')
    ) STORED
);

-- ==========================================================================
-- 2. CREATE INDEXES FOR OPTIMAL PERFORMANCE
-- ==========================================================================

-- Primary search and filtering indexes
CREATE INDEX idx_resumes_upload_date ON resumes(upload_date DESC);
CREATE INDEX idx_resumes_processing_status ON resumes(processing_status);
CREATE INDEX idx_resumes_user_type ON resumes(user_type);
CREATE INDEX idx_resumes_status ON resumes(status);

-- Scoring indexes
CREATE INDEX idx_resumes_overall_score ON resumes(overall_score DESC) WHERE overall_score IS NOT NULL;
CREATE INDEX idx_resumes_technical_score ON resumes(technical_score DESC) WHERE technical_score IS NOT NULL;
CREATE INDEX idx_resumes_experience_score ON resumes(experience_score DESC) WHERE experience_score IS NOT NULL;

-- Professional information indexes
CREATE INDEX idx_resumes_total_experience ON resumes(total_experience_years DESC) WHERE total_experience_years IS NOT NULL;
CREATE INDEX idx_resumes_current_company ON resumes(current_company) WHERE current_company IS NOT NULL;
CREATE INDEX idx_resumes_graduation_year ON resumes(graduation_year DESC) WHERE graduation_year IS NOT NULL;

-- Review and quality indexes
CREATE INDEX idx_resumes_human_reviewed ON resumes(human_reviewed);
CREATE INDEX idx_resumes_priority_level ON resumes(priority_level DESC);
CREATE INDEX idx_resumes_completeness_score ON resumes(completeness_score DESC) WHERE completeness_score IS NOT NULL;

-- Full-text search indexes
CREATE INDEX idx_resumes_search_gin ON resumes USING gin(search_vector gin_trgm_ops);

-- JSONB indexes for structured data
CREATE INDEX idx_resumes_skills_gin ON resumes USING gin(skills);
CREATE INDEX idx_resumes_experience_gin ON resumes USING gin(experience);
CREATE INDEX idx_resumes_education_gin ON resumes USING gin(education);
CREATE INDEX idx_resumes_keywords_gin ON resumes USING gin(keywords);
CREATE INDEX idx_resumes_role_matches_gin ON resumes USING gin(role_matches);

-- Compound indexes for common queries
CREATE INDEX idx_resumes_status_score ON resumes(status, overall_score DESC) WHERE status = 'active' AND overall_score IS NOT NULL;
CREATE INDEX idx_resumes_processing_upload ON resumes(processing_status, upload_date DESC);

-- ==========================================================================
-- 3. CREATE TRIGGER FUNCTION FOR AUTOMATIC TIMESTAMP UPDATES
-- ==========================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to resumes table
CREATE TRIGGER update_resumes_updated_at 
    BEFORE UPDATE ON resumes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================================================
-- 4. CREATE STATISTICS AND DASHBOARD VIEWS
-- ==========================================================================

-- Main statistics view for dashboard
CREATE OR REPLACE VIEW resume_stats AS
SELECT
    -- Basic counts
    COUNT(*) as total_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'completed') as processed_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_resumes,
    COUNT(*) FILTER (WHERE human_reviewed = true) as reviewed_resumes,
    
    -- Average scores
    ROUND(AVG(overall_score) FILTER (WHERE overall_score IS NOT NULL), 2) as avg_overall_score,
    ROUND(AVG(technical_score) FILTER (WHERE technical_score IS NOT NULL), 2) as avg_technical_score,
    ROUND(AVG(experience_score) FILTER (WHERE experience_score IS NOT NULL), 2) as avg_experience_score,
    ROUND(AVG(education_score) FILTER (WHERE education_score IS NOT NULL), 2) as avg_education_score,
    
    -- Experience metrics
    ROUND(AVG(total_experience_years) FILTER (WHERE total_experience_years IS NOT NULL), 1) as avg_experience_years,
    
    -- Time-based metrics
    COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '24 hours') as resumes_last_24h,
    COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '7 days') as resumes_last_week,
    COUNT(*) FILTER (WHERE upload_date >= NOW() - INTERVAL '30 days') as resumes_last_month,
    
    -- Quality metrics
    ROUND(AVG(completeness_score) FILTER (WHERE completeness_score IS NOT NULL), 2) as avg_completeness,
    ROUND(AVG(ai_confidence_score) FILTER (WHERE ai_confidence_score IS NOT NULL), 2) as avg_ai_confidence,
    
    -- User type distribution
    COUNT(*) FILTER (WHERE user_type = 'free') as free_users,
    COUNT(*) FILTER (WHERE user_type = 'paid') as paid_users,
    COUNT(*) FILTER (WHERE user_type = 'enterprise') as enterprise_users
FROM resumes 
WHERE status = 'active';

-- ==========================================================================
-- 5. SUCCESS VERIFICATION
-- ==========================================================================

-- Verify table was created successfully
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'resumes') THEN
        RAISE NOTICE '✅ SUCCESS: Table "resumes" created successfully with % columns', 
            (SELECT count(*) FROM information_schema.columns WHERE table_name = 'resumes' AND table_schema = 'public');
    ELSE
        RAISE EXCEPTION '❌ ERROR: Table "resumes" was not created';
    END IF;
    
    -- Check indexes
    IF (SELECT count(*) FROM pg_indexes WHERE tablename = 'resumes') > 0 THEN
        RAISE NOTICE '✅ SUCCESS: % indexes created successfully', 
            (SELECT count(*) FROM pg_indexes WHERE tablename = 'resumes');
    ELSE
        RAISE WARNING '⚠️  WARNING: No indexes found for resumes table';
    END IF;
    
    -- Check view
    IF EXISTS (SELECT FROM information_schema.views WHERE table_name = 'resume_stats') THEN
        RAISE NOTICE '✅ SUCCESS: View "resume_stats" created successfully';
    ELSE
        RAISE WARNING '⚠️  WARNING: View "resume_stats" was not created';
    END IF;
    
    -- Check trigger
    IF EXISTS (SELECT FROM information_schema.triggers WHERE trigger_name = 'update_resumes_updated_at') THEN
        RAISE NOTICE '✅ SUCCESS: Trigger "update_resumes_updated_at" created successfully';
    ELSE
        RAISE WARNING '⚠️  WARNING: Trigger was not created';
    END IF;
    
    RAISE NOTICE '🎉 SCHEMA DEPLOYMENT COMPLETE! Resume Screening Database is ready for use.';
END $$;
