-- Resume Screening Database Schema (Local Development)
-- Simple version without Supabase-specific features

-- Drop tables if they exist
DROP TABLE IF EXISTS resumes CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP VIEW IF EXISTS resume_stats CASCADE;

-- ==========================================================================
-- 1. EXTENSIONS
-- ==========================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==========================================================================
-- 2. CUSTOM TYPES
-- ==========================================================================
DO $$ BEGIN
    CREATE TYPE analysis_status AS ENUM (
        'pending',
        'processing', 
        'completed',
        'failed',
        'error'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ==========================================================================
-- 3. MAIN TABLES
-- ==========================================================================

-- Resumes table with comprehensive schema
CREATE TABLE resumes (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- File information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT,
    file_size INTEGER,
    file_type VARCHAR(50),
    file_hash VARCHAR(64),
    
    -- Extracted content
    extracted_text TEXT,
    
    -- Personal information
    candidate_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    location VARCHAR(255),
    
    -- Professional summary
    summary TEXT,
    objective TEXT,
    
    -- Skills (stored as JSONB for flexibility)
    skills JSONB DEFAULT '[]'::jsonb,
    technical_skills JSONB DEFAULT '[]'::jsonb,
    soft_skills JSONB DEFAULT '[]'::jsonb,
    
    -- Experience information
    total_experience_years DECIMAL(4,2),
    experience_details JSONB DEFAULT '[]'::jsonb,
    current_position VARCHAR(255),
    current_company VARCHAR(255),
    
    -- Education information
    education JSONB DEFAULT '[]'::jsonb,
    highest_degree VARCHAR(255),
    field_of_study VARCHAR(255),
    university VARCHAR(255),
    graduation_year INTEGER,
    
    -- Additional sections
    certifications JSONB DEFAULT '[]'::jsonb,
    languages JSONB DEFAULT '[]'::jsonb,
    projects JSONB DEFAULT '[]'::jsonb,
    achievements JSONB DEFAULT '[]'::jsonb,
    
    -- AI Analysis
    ai_analysis JSONB,
    analysis_status analysis_status DEFAULT 'pending',
    analysis_error TEXT,
    
    -- Scoring
    overall_score DECIMAL(5,2),
    technical_score DECIMAL(5,2),
    experience_score DECIMAL(5,2),
    education_score DECIMAL(5,2),
    skills_score DECIMAL(5,2),
    
    -- Match scores for different roles
    role_matches JSONB DEFAULT '{}'::jsonb,
    
    -- AI-generated insights
    strengths JSONB DEFAULT '[]'::jsonb,
    weaknesses JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Keywords and tags
    keywords JSONB DEFAULT '[]'::jsonb,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Processing metadata
    processing_time_ms INTEGER,
    ai_model_used VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzed_at TIMESTAMP WITH TIME ZONE,
    
    -- Admin/review fields
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT,
    status VARCHAR(50) DEFAULT 'active',
    
    -- Search and filtering
    searchable_content TEXT GENERATED ALWAYS AS (
        COALESCE(candidate_name, '') || ' ' ||
        COALESCE(email, '') || ' ' ||
        COALESCE(current_position, '') || ' ' ||
        COALESCE(current_company, '') || ' ' ||
        COALESCE(summary, '') || ' ' ||
        COALESCE(extracted_text, '')
    ) STORED
);

-- ==========================================================================
-- 4. INDEXES FOR PERFORMANCE
-- ==========================================================================

-- Primary search indexes
CREATE INDEX idx_resumes_candidate_name ON resumes(candidate_name);
CREATE INDEX idx_resumes_email ON resumes(email);
CREATE INDEX idx_resumes_status ON resumes(status);
CREATE INDEX idx_resumes_analysis_status ON resumes(analysis_status);
CREATE INDEX idx_resumes_created_at ON resumes(created_at DESC);
CREATE INDEX idx_resumes_updated_at ON resumes(updated_at DESC);

-- Performance indexes
CREATE INDEX idx_resumes_overall_score ON resumes(overall_score DESC) WHERE overall_score IS NOT NULL;
CREATE INDEX idx_resumes_experience_years ON resumes(total_experience_years DESC) WHERE total_experience_years IS NOT NULL;

-- Text search indexes
CREATE INDEX idx_resumes_searchable_content ON resumes USING gin(to_tsvector('english', searchable_content));
CREATE INDEX idx_resumes_filename ON resumes(filename);
CREATE INDEX idx_resumes_file_hash ON resumes(file_hash);

-- JSONB indexes for efficient querying
CREATE INDEX idx_resumes_skills_gin ON resumes USING gin(skills);
CREATE INDEX idx_resumes_role_matches_gin ON resumes USING gin(role_matches);

-- ==========================================================================
-- 5. FUNCTIONS AND TRIGGERS
-- ==========================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_resumes_updated_at 
    BEFORE UPDATE ON resumes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================================================
-- 6. VIEWS FOR ANALYTICS
-- ==========================================================================

-- Resume statistics view
CREATE OR REPLACE VIEW resume_stats AS
SELECT 
    COUNT(*) as total_resumes,
    COUNT(*) FILTER (WHERE analysis_status = 'completed') as analyzed_resumes,
    COUNT(*) FILTER (WHERE analysis_status = 'pending') as pending_analysis,
    COUNT(*) FILTER (WHERE analysis_status = 'failed') as failed_analysis,
    COUNT(*) FILTER (WHERE reviewed = true) as reviewed_resumes,
    AVG(overall_score) FILTER (WHERE overall_score IS NOT NULL) as avg_overall_score,
    AVG(total_experience_years) FILTER (WHERE total_experience_years IS NOT NULL) as avg_experience_years,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as resumes_last_24h,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as resumes_last_week,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as resumes_last_month;
