-- ==========================================================================
-- RESUME SCREENING APP - BULLETPROOF SUPABASE DATABASE SCHEMA
-- ==========================================================================
-- This script creates a robust database schema for the resume screening
-- application with proper error handling and Supabase best practices.
--
-- INSTRUCTIONS:
-- 1. Copy this entire script
-- 2. Go to your Supabase Dashboard → SQL Editor
-- 3. Paste and run this script
-- 4. Verify the success messages at the end
-- ==========================================================================

-- Clean slate: Drop existing objects if they exist (for re-runs)
-- Note: Order matters - policies and triggers depend on table existing
DO $$
BEGIN
    -- Drop policies if table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'resumes') THEN
        DROP POLICY IF EXISTS "allow_all_operations" ON resumes;
        DROP TRIGGER IF EXISTS update_resumes_updated_at ON resumes;
    END IF;
    
    -- Drop view if exists
    DROP VIEW IF EXISTS resume_stats;
    
    -- Drop function if exists
    DROP FUNCTION IF EXISTS update_updated_at_column();
    
    -- Drop table if exists
    DROP TABLE IF EXISTS resumes CASCADE;
END $$;

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
    
    -- Compressed resume data (full resume info stored as compressed JSON)
    compressed_content TEXT NOT NULL,
    
    -- Extracted fields for easy querying and filtering
    candidate_name TEXT DEFAULT '',
    candidate_email TEXT DEFAULT '',
    skills TEXT[] DEFAULT '{}',
    experience_years INTEGER DEFAULT 0 CHECK (experience_years >= 0 AND experience_years <= 100),
    education_level TEXT DEFAULT '',
    
    -- AI Analysis scores (0-100 range)
    overall_score INTEGER DEFAULT 0 CHECK (overall_score >= 0 AND overall_score <= 100),
    technical_score INTEGER DEFAULT 0 CHECK (technical_score >= 0 AND technical_score <= 100),
    experience_score INTEGER DEFAULT 0 CHECK (experience_score >= 0 AND experience_score <= 100),
    education_score INTEGER DEFAULT 0 CHECK (education_score >= 0 AND education_score <= 100),
    role_fit_score INTEGER DEFAULT 0 CHECK (role_fit_score >= 0 AND role_fit_score <= 100),
    
    -- Additional metadata for search and analytics
    job_titles TEXT[] DEFAULT '{}',
    companies TEXT[] DEFAULT '{}',
    programming_languages TEXT[] DEFAULT '{}',
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================================================
-- 2. CREATE PERFORMANCE INDEXES
-- ==========================================================================
-- Primary query indexes
CREATE INDEX idx_resumes_upload_date ON resumes(upload_date DESC);
CREATE INDEX idx_resumes_user_type ON resumes(user_type);
CREATE INDEX idx_resumes_processing_status ON resumes(processing_status);
CREATE INDEX idx_resumes_overall_score ON resumes(overall_score DESC);

-- Search indexes
CREATE INDEX idx_resumes_candidate_name ON resumes(candidate_name);
CREATE INDEX idx_resumes_candidate_email ON resumes(candidate_email);

-- Array indexes for advanced search (GIN indexes for array operations)
CREATE INDEX idx_resumes_skills ON resumes USING GIN(skills);
CREATE INDEX idx_resumes_job_titles ON resumes USING GIN(job_titles);
CREATE INDEX idx_resumes_companies ON resumes USING GIN(companies);
CREATE INDEX idx_resumes_programming_languages ON resumes USING GIN(programming_languages);

-- Composite indexes for common query patterns
CREATE INDEX idx_resumes_status_score ON resumes(processing_status, overall_score DESC);
CREATE INDEX idx_resumes_user_type_date ON resumes(user_type, upload_date DESC);

-- ==========================================================================
-- 3. CREATE UPDATED_AT TRIGGER FUNCTION
-- ==========================================================================
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

-- Create the trigger
CREATE TRIGGER update_resumes_updated_at
    BEFORE UPDATE ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================================================
-- 4. SETUP ROW LEVEL SECURITY (RLS)
-- ==========================================================================
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

-- Allow all operations for now (we'll add proper user-based policies later)
CREATE POLICY "allow_all_operations" ON resumes
    FOR ALL 
    TO public
    USING (true)
    WITH CHECK (true);

-- ==========================================================================
-- 5. CREATE ANALYTICS VIEW
-- ==========================================================================
CREATE VIEW resume_stats AS
SELECT 
    -- Counts
    COUNT(*) as total_resumes,
    COUNT(*) FILTER (WHERE user_type = 'free') as free_user_resumes,
    COUNT(*) FILTER (WHERE user_type = 'paid') as paid_user_resumes,
    COUNT(*) FILTER (WHERE user_type = 'enterprise') as enterprise_user_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'completed') as completed_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'failed') as failed_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'processing') as processing_resumes,
    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending_resumes,
    
    -- Score averages (only for completed resumes)
    ROUND(AVG(overall_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_overall_score,
    ROUND(AVG(technical_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_technical_score,
    ROUND(AVG(experience_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_experience_score,
    ROUND(AVG(education_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_education_score,
    ROUND(AVG(role_fit_score) FILTER (WHERE processing_status = 'completed'), 2) as avg_role_fit_score,
    
    -- Score ranges
    MAX(overall_score) as max_overall_score,
    MIN(overall_score) FILTER (WHERE overall_score > 0) as min_overall_score,
    
    -- Date ranges
    MAX(upload_date) as latest_upload,
    MIN(upload_date) as first_upload,
    
    -- Storage stats
    SUM(file_size) as total_storage_bytes,
    ROUND(AVG(file_size), 0) as avg_file_size_bytes
FROM resumes;

-- ==========================================================================
-- 6. GRANT PERMISSIONS
-- ==========================================================================
-- Grant table permissions
GRANT ALL ON resumes TO anon, authenticated;
GRANT SELECT ON resume_stats TO anon, authenticated;

-- Grant sequence permissions (for UUID generation)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- ==========================================================================
-- 7. INSERT TEST DATA (SAFE)
-- ==========================================================================
-- Insert a simple test record to verify everything works
INSERT INTO resumes (
    filename, 
    compressed_content, 
    file_hash,
    candidate_name,
    candidate_email,
    processing_status,
    overall_score,
    technical_score,
    experience_score,
    education_score,
    role_fit_score,
    skills,
    job_titles,
    programming_languages,
    experience_years
) VALUES (
    'test_resume_sample.txt',
    'eJyrVkosLcmIz8nPS1WyUsrIyFGyMjAyNDMxNTUwNzEyMDIxNzI1NTEzMzQ1NzI2NDYxNjQ0NjQ1Mjc3NDY=',  -- Simple compressed test data
    'test_hash_' || extract(epoch from now())::text,  -- Unique hash
    'John Doe (Test User)',
    'john.doe.test@example.com',
    'completed',
    85,
    80,
    90,
    85,
    88,
    ARRAY['JavaScript', 'Python', 'React', 'Node.js'],
    ARRAY['Software Engineer', 'Full Stack Developer'],
    ARRAY['JavaScript', 'Python'],
    5
) ON CONFLICT (file_hash) DO NOTHING;

-- ==========================================================================
-- 8. VERIFICATION AND SUCCESS REPORTING
-- ==========================================================================
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    policy_count INTEGER;
    test_data_count INTEGER;
BEGIN
    -- Check table creation
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_name = 'resumes';
    
    -- Check index creation
    SELECT COUNT(*) INTO index_count 
    FROM pg_indexes 
    WHERE tablename = 'resumes';
    
    -- Check policy creation
    SELECT COUNT(*) INTO policy_count 
    FROM pg_policies 
    WHERE tablename = 'resumes';
    
    -- Check test data
    SELECT COUNT(*) INTO test_data_count 
    FROM resumes;
    
    -- Report results
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'SUPABASE SCHEMA SETUP COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'Tables created: %', table_count;
    RAISE NOTICE 'Indexes created: %', index_count;
    RAISE NOTICE 'Security policies: %', policy_count;
    RAISE NOTICE 'Test records inserted: %', test_data_count;
    RAISE NOTICE '==========================================================================';
    
    IF table_count = 0 THEN
        RAISE EXCEPTION 'ERROR: Table creation failed!';
    END IF;
    
    IF index_count < 5 THEN
        RAISE EXCEPTION 'ERROR: Index creation incomplete!';
    END IF;
    
    RAISE NOTICE 'Your Supabase database is ready for the Resume Screening App!';
    RAISE NOTICE 'You can now test the connection with your Python backend.';
    RAISE NOTICE '==========================================================================';
END $$;

-- Final verification queries
SELECT 'SUCCESS: resume_stats view' as status, COUNT(*) as record_count FROM resume_stats;
SELECT 'SUCCESS: resumes table' as status, COUNT(*) as record_count FROM resumes;
