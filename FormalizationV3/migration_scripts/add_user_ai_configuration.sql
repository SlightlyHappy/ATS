-- Migration: Add User AI Configuration Tables
-- Created: 2025-08-03
-- Purpose: Admin-configurable AI models per user

-- User AI Settings table
CREATE TABLE IF NOT EXISTS user_ai_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    ai_provider VARCHAR(50) NOT NULL DEFAULT 'ollama',
    ai_model VARCHAR(100) NOT NULL DEFAULT 'llama3.1:8b',
    set_by_admin BOOLEAN DEFAULT false,
    admin_user_id UUID REFERENCES user_profiles(id),
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_ai_provider CHECK (ai_provider IN ('ollama', 'openai', 'anthropic')),
    UNIQUE(user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_user_id ON user_ai_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_provider ON user_ai_settings(ai_provider);
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_enabled ON user_ai_settings(enabled);
CREATE INDEX IF NOT EXISTS idx_user_ai_settings_admin ON user_ai_settings(admin_user_id) WHERE admin_user_id IS NOT NULL;

-- AI Processing Logs table for monitoring
CREATE TABLE IF NOT EXISTS ai_processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
    ai_provider VARCHAR(50) NOT NULL,
    ai_model VARCHAR(100) NOT NULL,
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    cost_estimate DECIMAL(10,6),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    analysis_type VARCHAR(50) DEFAULT 'comprehensive',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_processing_provider CHECK (ai_provider IN ('ollama', 'openai', 'anthropic'))
);

-- Indexes for AI processing logs
CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_user_id ON ai_processing_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_created_at ON ai_processing_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_provider ON ai_processing_logs(ai_provider);
CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_success ON ai_processing_logs(success);
CREATE INDEX IF NOT EXISTS idx_ai_processing_logs_resume_id ON ai_processing_logs(resume_id) WHERE resume_id IS NOT NULL;

-- Default AI settings for existing users (Ollama for everyone initially)
INSERT INTO user_ai_settings (user_id, ai_provider, ai_model, set_by_admin, enabled)
SELECT 
    id as user_id,
    'ollama' as ai_provider,
    'llama3.1:8b' as ai_model,
    false as set_by_admin,
    true as enabled
FROM user_profiles 
WHERE id NOT IN (SELECT user_id FROM user_ai_settings)
ON CONFLICT (user_id) DO NOTHING;

-- Add comment for documentation
COMMENT ON TABLE user_ai_settings IS 'Stores AI provider and model configuration per user, configurable by admin';
COMMENT ON TABLE ai_processing_logs IS 'Logs all AI processing requests for monitoring and cost tracking';

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_ai_settings_updated_at 
    BEFORE UPDATE ON user_ai_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
