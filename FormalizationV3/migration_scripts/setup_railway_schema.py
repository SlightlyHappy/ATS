"""
Railway PostgreSQL Schema Setup
Creates all tables needed for HR ATS System with UUID compatibility
"""

import os
import sys
import psycopg2
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

# Railway PostgreSQL Schema - Keeps UUID compatibility for easy migration
RAILWAY_SCHEMA_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core Tables (Phase 1)

-- User profiles (extends Supabase auth but no dependency)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name TEXT,
    access_type TEXT DEFAULT 'trial',
    trial_usage INTEGER DEFAULT 0,
    trial_limit INTEGER DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resumes with AI analysis results (Enhanced with all backend expected fields)
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- File metadata
    filename TEXT NOT NULL,
    file_hash TEXT,
    file_size INTEGER DEFAULT 0,
    file_type TEXT DEFAULT 'pdf',
    compressed_content TEXT,
    raw_text TEXT,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    
    -- Candidate information
    candidate_name TEXT DEFAULT '',
    candidate_email TEXT DEFAULT '',
    candidate_phone TEXT DEFAULT '',
    
    -- Skills and experience
    skills TEXT[] DEFAULT '{}',
    experience_years INTEGER DEFAULT 0,
    education_level TEXT DEFAULT '',
    
    -- AI Analysis scores (0-100 range)
    overall_score INTEGER DEFAULT 0 CHECK (overall_score >= 0 AND overall_score <= 100),
    technical_score INTEGER DEFAULT 0 CHECK (technical_score >= 0 AND technical_score <= 100),
    experience_score INTEGER DEFAULT 0 CHECK (experience_score >= 0 AND experience_score <= 100),
    education_score INTEGER DEFAULT 0 CHECK (education_score >= 0 AND education_score <= 100),
    role_fit_score INTEGER DEFAULT 0 CHECK (role_fit_score >= 0 AND role_fit_score <= 100),
    
    -- AI processing details
    ai_feedback TEXT,
    ai_model_used TEXT,
    ai_processing_time INTEGER DEFAULT 0,
    
    -- Additional metadata arrays
    job_titles TEXT[] DEFAULT '{}',
    companies TEXT[] DEFAULT '{}',
    programming_languages TEXT[] DEFAULT '{}',
    certifications TEXT[] DEFAULT '{}',
    
    -- Categorization and tagging
    tags TEXT[] DEFAULT '{}',
    category TEXT DEFAULT 'general',
    priority INTEGER DEFAULT 0,
    
    -- Status tracking
    is_shortlisted BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    notes TEXT,
    
    -- Legacy fields (for compatibility)
    analysis_result JSONB,
    similarity_score DECIMAL(5,4),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User activity tracking
CREATE TABLE IF NOT EXISTS user_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HR legal queries and responses
CREATE TABLE IF NOT EXISTS hr_legal_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    response_text TEXT,
    category VARCHAR(100),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System configuration
CREATE TABLE IF NOT EXISTS system_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payment Tables (Phase 2)

-- User credits and trial management
CREATE TABLE IF NOT EXISTS user_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    credit_type VARCHAR(50) NOT NULL, -- 'trial', 'premium', 'bonus'
    credits_available INTEGER DEFAULT 0,
    credits_used INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, credit_type)
);

-- Credit transaction history
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL, -- 'used', 'added', 'expired'
    credits_changed INTEGER NOT NULL,
    credits_remaining INTEGER NOT NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payment orders (RazorPay integration)
CREATE TABLE IF NOT EXISTS payment_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    razorpay_order_id VARCHAR(255) UNIQUE NOT NULL,
    amount INTEGER NOT NULL, -- Amount in paise
    currency VARCHAR(10) DEFAULT 'INR',
    status VARCHAR(50) DEFAULT 'created', -- 'created', 'paid', 'failed'
    plan_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Completed payment transactions
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES payment_orders(id) ON DELETE CASCADE,
    razorpay_payment_id VARCHAR(255) UNIQUE NOT NULL,
    razorpay_signature VARCHAR(500),
    amount INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'captured', 'failed', 'refunded'
    method VARCHAR(50), -- 'card', 'netbanking', 'wallet', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User privileges and queue management
CREATE TABLE IF NOT EXISTS user_privileges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    privilege_type VARCHAR(50) NOT NULL, -- 'queue_skip', 'priority_support'
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by UUID, -- Admin who granted the privilege
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage analytics for sales intelligence
CREATE TABLE IF NOT EXISTS usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    feature VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, feature)
);

-- Sales intelligence and lead scoring
CREATE TABLE IF NOT EXISTS sales_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    lead_score INTEGER DEFAULT 0,
    conversion_probability DECIMAL(3,2),
    engagement_level VARCHAR(50), -- 'low', 'medium', 'high'
    last_activity TIMESTAMP WITH TIME ZONE,
    qualification_status VARCHAR(50), -- 'cold', 'warm', 'hot', 'converted'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Advanced Analytics Tables (Phase 3)

-- Email campaigns tracking
CREATE TABLE IF NOT EXISTS email_campaigns_sent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    campaign_type VARCHAR(100) NOT NULL,
    subject TEXT,
    content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent', -- 'sent', 'delivered', 'opened', 'clicked'
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email automation triggers
CREATE TABLE IF NOT EXISTS email_automation_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trigger_name VARCHAR(255) NOT NULL,
    trigger_condition JSONB NOT NULL,
    email_template_id VARCHAR(255),
    delay_hours INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email performance metrics
CREATE TABLE IF NOT EXISTS email_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES email_campaigns_sent(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'delivered', 'opened', 'clicked', 'bounced'
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales team actions
CREATE TABLE IF NOT EXISTS sales_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL, -- 'call', 'email', 'demo', 'follow_up'
    action_details JSONB,
    performed_by VARCHAR(255), -- Sales rep name/id
    scheduled_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    outcome VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales status change history
CREATE TABLE IF NOT EXISTS sales_status_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    previous_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by VARCHAR(255),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ML-based user segmentation
CREATE TABLE IF NOT EXISTS user_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    segment_name VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3,2),
    segment_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, segment_name)
);

-- ML conversion predictions
CREATE TABLE IF NOT EXISTS conversion_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    prediction_model VARCHAR(100) NOT NULL,
    conversion_probability DECIMAL(5,4),
    predicted_value DECIMAL(10,2),
    features_used JSONB,
    prediction_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, prediction_model, prediction_date)
);

-- Precomputed cohort analysis
CREATE TABLE IF NOT EXISTS cohort_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_month DATE NOT NULL,
    period_number INTEGER NOT NULL, -- 0 for first month, 1 for second, etc.
    users_count INTEGER NOT NULL,
    retained_users INTEGER NOT NULL,
    retention_rate DECIMAL(5,4),
    revenue DECIMAL(12,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(cohort_month, period_number)
);

-- Detailed feature usage analytics
CREATE TABLE IF NOT EXISTS feature_usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    sub_feature VARCHAR(255),
    usage_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(255),
    duration_seconds INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance

-- User profiles indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_access_type ON user_profiles(access_type);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- Resumes indexes
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_upload_date ON resumes(upload_date);
CREATE INDEX IF NOT EXISTS idx_resumes_similarity_score ON resumes(similarity_score);

-- User activity indexes
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_type ON user_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);

-- HR legal queries indexes
CREATE INDEX IF NOT EXISTS idx_hr_legal_queries_user_id ON hr_legal_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_hr_legal_queries_category ON hr_legal_queries(category);
CREATE INDEX IF NOT EXISTS idx_hr_legal_queries_created_at ON hr_legal_queries(created_at);

-- Credit transactions indexes
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at);

-- Payment orders indexes
CREATE INDEX IF NOT EXISTS idx_payment_orders_user_id ON payment_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status);
CREATE INDEX IF NOT EXISTS idx_payment_orders_created_at ON payment_orders(created_at);

-- Usage analytics indexes
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_feature ON usage_analytics(feature);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_last_used ON usage_analytics(last_used);

-- Email campaigns indexes
CREATE INDEX IF NOT EXISTS idx_email_campaigns_user_id ON email_campaigns_sent(user_id);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_type ON email_campaigns_sent(campaign_type);
CREATE INDEX IF NOT EXISTS idx_email_campaigns_sent_at ON email_campaigns_sent(sent_at);

-- Feature usage analytics indexes
CREATE INDEX IF NOT EXISTS idx_feature_usage_user_id ON feature_usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_feature ON feature_usage_analytics(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_usage_timestamp ON feature_usage_analytics(usage_timestamp);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to relevant tables
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_resumes_updated_at BEFORE UPDATE ON resumes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_hr_legal_queries_updated_at BEFORE UPDATE ON hr_legal_queries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_credits_updated_at BEFORE UPDATE ON user_credits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payment_orders_updated_at BEFORE UPDATE ON payment_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_usage_analytics_updated_at BEFORE UPDATE ON usage_analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sales_intelligence_updated_at BEFORE UPDATE ON sales_intelligence FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_email_automation_triggers_updated_at BEFORE UPDATE ON email_automation_triggers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_segments_updated_at BEFORE UPDATE ON user_segments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""

def setup_railway_schema(database_url: str = None):
    """Set up Railway PostgreSQL schema"""
    
    database_url = database_url or os.getenv('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    try:
        # Connect to Railway PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        logger.info("Connected to Railway PostgreSQL")
        
        # Execute schema creation
        cursor.execute(RAILWAY_SCHEMA_SQL)
        conn.commit()
        
        logger.info("✅ Railway schema created successfully")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logger.info(f"✅ Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'message': f'Successfully created {len(tables)} tables',
            'tables': [table[0] for table in tables]
        }
        
    except Exception as e:
        logger.error(f"Failed to set up Railway schema: {e}")
        raise

def verify_schema():
    """Verify Railway schema is properly set up"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if all expected tables exist
        expected_tables = [
            'user_profiles', 'resumes', 'user_activity', 'hr_legal_queries', 'system_config',
            'user_credits', 'credit_transactions', 'payment_orders', 'payment_transactions',
            'user_privileges', 'usage_analytics', 'sales_intelligence', 'email_campaigns_sent',
            'email_automation_triggers', 'email_performance', 'sales_actions', 
            'sales_status_changes', 'user_segments', 'conversion_predictions', 
            'cohort_analysis', 'feature_usage_analytics'
        ]
        
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = ANY(%s)
        """, (expected_tables,))
        
        existing_tables = [table[0] for table in cursor.fetchall()]
        missing_tables = set(expected_tables) - set(existing_tables)
        
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            return {
                'status': 'error',
                'missing_tables': list(missing_tables),
                'existing_tables': existing_tables
            }
        
        logger.info("✅ All expected tables exist")
        
        # Test basic functionality
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            'status': 'success',
            'message': 'Schema verification successful',
            'postgresql_version': version,
            'tables_count': len(existing_tables)
        }
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Setting up Railway PostgreSQL schema...")
    
    try:
        result = setup_railway_schema()
        print(f"✅ {result['message']}")
        
        print("\n🔍 Verifying schema...")
        verification = verify_schema()
        
        if verification['status'] == 'success':
            print(f"✅ {verification['message']}")
            print(f"📊 PostgreSQL Version: {verification['postgresql_version']}")
            print(f"📋 Tables Created: {verification['tables_count']}")
        else:
            print(f"❌ Verification failed: {verification['message']}")
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)
