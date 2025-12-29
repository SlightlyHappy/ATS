-- Fix Missing Tables for Railway Database
-- This addresses the missing user_ai_settings table and other schema issues

-- Create user_ai_settings table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_ai_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

-- Insert default AI settings for admin users
INSERT INTO user_ai_settings (user_id, ai_provider, ai_model, enabled, priority, config)
VALUES 
    ('admin', 'openai', 'gpt-4', true, 1, '{"temperature": 0.7, "max_tokens": 2000}'),
    ('admin', 'anthropic', 'claude-3-sonnet-20240229', true, 2, '{"temperature": 0.7, "max_tokens": 2000}'),
    ('admin', 'ollama', 'qwen2.5:14b', true, 3, '{"temperature": 0.7, "num_predict": 2000}')
ON CONFLICT (user_id, ai_provider, ai_model) DO NOTHING;

-- Add missing columns to resumes table if they don't exist
DO $$ 
BEGIN
    -- Add analysis_results column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'analysis_results') THEN
        ALTER TABLE resumes ADD COLUMN analysis_results JSONB DEFAULT NULL;
    END IF;
    
    -- Add extracted_text column  
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'extracted_text') THEN
        ALTER TABLE resumes ADD COLUMN extracted_text TEXT DEFAULT NULL;
    END IF;
    
    -- Add processing_started_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'processing_started_at') THEN
        ALTER TABLE resumes ADD COLUMN processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
    END IF;
    
    -- Add processing_completed_at column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'processing_completed_at') THEN
        ALTER TABLE resumes ADD COLUMN processing_completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
    END IF;
    
    -- Add ai_processing_time column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'resumes' AND column_name = 'ai_processing_time') THEN
        ALTER TABLE resumes ADD COLUMN ai_processing_time INTEGER DEFAULT 0;
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_user_id ON user_ai_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_enabled ON user_ai_settings(enabled);
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_priority ON user_ai_settings(priority);
CREATE INDEX IF NOT EXISTS idx_resumes_analysis_results ON resumes USING GIN(analysis_results);
CREATE INDEX IF NOT EXISTS idx_resumes_processing_status ON resumes(processing_status);

-- Fix skills column safely
DO $$ 
DECLARE
    current_type TEXT;
BEGIN
    -- Get current data type of skills column
    SELECT data_type INTO current_type 
    FROM information_schema.columns 
    WHERE table_name = 'resumes' AND column_name = 'skills';
    
    -- Only proceed if skills column exists
    IF current_type IS NOT NULL THEN
        -- If it's not already JSONB, convert it
        IF current_type != 'jsonb' THEN
            -- First, safely convert existing data
            UPDATE resumes 
            SET skills = CASE 
                WHEN skills IS NULL THEN '[]'::text
                WHEN skills::text = '' THEN '[]'::text
                WHEN skills::text LIKE '[%]' OR skills::text LIKE '{%}' THEN skills::text
                ELSE ('["' || replace(trim(skills::text), ',', '","') || '"]')::text
            END;
            
            -- Then alter the column type
            ALTER TABLE resumes ALTER COLUMN skills TYPE JSONB USING skills::jsonb;
            RAISE NOTICE 'Converted skills column to JSONB';
        ELSE
            -- Column is already JSONB, just update NULL values
            UPDATE resumes 
            SET skills = '[]'::jsonb 
            WHERE skills IS NULL;
            RAISE NOTICE 'Updated NULL skills values to empty arrays';
        END IF;
    ELSE
        RAISE NOTICE 'Skills column does not exist, skipping update';
    END IF;
END $$;
