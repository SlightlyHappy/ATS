-- ==========================================================================
-- PHASE 3 TABLES FOR SALES INTELLIGENCE & ADVANCED ANALYTICS
-- Sales Intelligence, Email Automation, and Advanced Analytics Tables
-- ==========================================================================
-- This script adds Phase 3 tables to the existing database schema
-- Run this after the main database setup and Phase 2 payment tables
--
-- INSTRUCTIONS:
-- 1. Ensure Phase 1 and Phase 2 tables exist
-- 2. Copy this entire script
-- 3. Go to your Supabase Dashboard → SQL Editor
-- 4. Paste and run this script
-- ==========================================================================

-- ==========================================================================
-- 1. EMAIL AUTOMATION TABLES
-- ==========================================================================

-- Email Campaigns Sent - Track all sent email campaigns
CREATE TABLE IF NOT EXISTS email_campaigns_sent (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    template_name VARCHAR(50) NOT NULL,
    trigger_type VARCHAR(30) NOT NULL,
    trigger_data JSONB DEFAULT '{}',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    subject TEXT,
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'delivered', 'opened', 'clicked', 'bounced', 'failed')),
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes for performance
    UNIQUE(user_id, template_name)  -- Prevent duplicate campaigns per user
);

-- Email Automation Triggers - Scheduled email campaigns
CREATE TABLE IF NOT EXISTS email_automation_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    trigger_type VARCHAR(30) NOT NULL,
    trigger_condition TEXT,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    scheduled_send_at TIMESTAMP WITH TIME ZONE,
    campaign_data JSONB DEFAULT '{}'
);

-- Email Performance Tracking - Campaign performance metrics
CREATE TABLE IF NOT EXISTS email_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(50) NOT NULL UNIQUE,
    sent_count INTEGER DEFAULT 0 CHECK (sent_count >= 0),
    opened_count INTEGER DEFAULT 0 CHECK (opened_count >= 0),
    clicked_count INTEGER DEFAULT 0 CHECK (clicked_count >= 0),
    responded_count INTEGER DEFAULT 0 CHECK (responded_count >= 0),
    conversion_count INTEGER DEFAULT 0 CHECK (conversion_count >= 0),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================================================
-- 2. SALES INTELLIGENCE ENHANCEMENT TABLES
-- ==========================================================================

-- Sales Actions - Track sales team actions
CREATE TABLE IF NOT EXISTS sales_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    sales_rep VARCHAR(100) NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled')),
    notes TEXT,
    result JSONB DEFAULT '{}'
);

-- Sales Status Changes - Audit trail for lead status changes
CREATE TABLE IF NOT EXISTS sales_status_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    notes TEXT,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Privileges - Queue skip and premium privileges
CREATE TABLE IF NOT EXISTS user_privileges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    privilege_type VARCHAR(20) NOT NULL CHECK (privilege_type IN ('queue_skip', 'premium_processing', 'enterprise_access')),
    is_active BOOLEAN DEFAULT TRUE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    payment_reference TEXT,
    metadata JSONB DEFAULT '{}'
);

-- ==========================================================================
-- 3. ADVANCED ANALYTICS TABLES
-- ==========================================================================

-- User Segments - ML-based user segmentation
CREATE TABLE IF NOT EXISTS user_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    segment_type VARCHAR(30) NOT NULL,
    confidence_score DECIMAL(5,3) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    segment_data JSONB DEFAULT '{}',
    
    UNIQUE(user_id, segment_type)
);

-- Conversion Predictions - ML-based conversion predictions
CREATE TABLE IF NOT EXISTS conversion_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    prediction_type VARCHAR(30) NOT NULL,
    probability_score DECIMAL(5,3) CHECK (probability_score >= 0 AND probability_score <= 1),
    confidence_interval DECIMAL(5,3),
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(20),
    features_used JSONB DEFAULT '{}',
    
    UNIQUE(user_id, prediction_type)
);

-- Cohort Analysis Results - Precomputed cohort data
CREATE TABLE IF NOT EXISTS cohort_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_period VARCHAR(20) NOT NULL,
    cohort_type VARCHAR(20) NOT NULL DEFAULT 'weekly',
    user_count INTEGER NOT NULL CHECK (user_count >= 0),
    conversion_rate DECIMAL(5,3) CHECK (conversion_rate >= 0 AND conversion_rate <= 1),
    average_credits_used DECIMAL(8,2),
    average_days_to_conversion DECIMAL(6,2),
    top_features JSONB DEFAULT '[]',
    retention_rates JSONB DEFAULT '{}',
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(cohort_period, cohort_type)
);

-- Feature Usage Analytics - Detailed feature usage tracking
CREATE TABLE IF NOT EXISTS feature_usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    feature_name VARCHAR(50) NOT NULL,
    usage_count INTEGER DEFAULT 1 CHECK (usage_count >= 0),
    first_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_data JSONB DEFAULT '{}',
    conversion_impact DECIMAL(5,3),  -- Impact on conversion probability
    
    UNIQUE(user_id, feature_name)
);

-- ==========================================================================
-- 4. BUSINESS INTELLIGENCE VIEWS
-- ==========================================================================

-- Hot Leads View - Real-time hot leads identification
CREATE OR REPLACE VIEW hot_leads_view AS
SELECT 
    u.id as user_id,
    u.email,
    u.name,
    u.company,
    uc.total_used as credits_used,
    (uc.trial_credits + uc.premium_credits) as credits_remaining,
    si.lead_score,
    si.qualification_status,
    si.last_activity,
    EXTRACT(DAYS FROM (NOW() - u.created_at)) as days_since_signup,
    CASE 
        WHEN si.lead_score >= 80 THEN 'urgent'
        WHEN si.lead_score >= 60 THEN 'high'
        WHEN si.lead_score >= 40 THEN 'medium'
        ELSE 'low'
    END as priority,
    CASE
        WHEN si.lead_score >= 80 OR uc.total_used >= 95 THEN 'call_immediately'
        WHEN si.lead_score >= 60 OR (uc.trial_credits + uc.premium_credits) <= 10 THEN 'schedule_demo'
        WHEN si.lead_score >= 40 OR uc.total_used >= 50 THEN 'send_proposal'
        ELSE 'nurture_email'
    END as recommended_action
FROM user_profiles u
JOIN user_credits uc ON u.id = uc.user_id
LEFT JOIN sales_intelligence si ON u.id = si.user_id
WHERE (
    si.lead_score >= 70 OR
    uc.total_used >= 90 OR
    (uc.total_used >= 75 AND (uc.trial_credits + uc.premium_credits) <= 10)
)
AND u.created_at >= NOW() - INTERVAL '30 days'
ORDER BY si.lead_score DESC, uc.total_used DESC;

-- Conversion Funnel View - Real-time funnel analysis
CREATE OR REPLACE VIEW conversion_funnel_view AS
WITH funnel_data AS (
    SELECT 
        COUNT(*) as total_signups,
        COUNT(CASE WHEN uc.total_used > 0 THEN 1 END) as activated_users,
        COUNT(CASE WHEN uc.total_used >= 25 THEN 1 END) as engaged_users,
        COUNT(CASE WHEN uc.total_used >= 75 THEN 1 END) as power_users,
        COUNT(CASE WHEN pt.status = 'completed' THEN 1 END) as paying_customers
    FROM user_profiles u
    LEFT JOIN user_credits uc ON u.id = uc.user_id
    LEFT JOIN payment_transactions pt ON u.id = pt.user_id AND pt.status = 'completed'
    WHERE u.created_at >= NOW() - INTERVAL '30 days'
)
SELECT 
    total_signups,
    activated_users,
    engaged_users,
    power_users,
    paying_customers,
    ROUND(
        CASE WHEN total_signups > 0 THEN 
            (activated_users::decimal / total_signups) * 100 
        ELSE 0 END, 2
    ) as signup_to_activation_rate,
    ROUND(
        CASE WHEN activated_users > 0 THEN 
            (engaged_users::decimal / activated_users) * 100 
        ELSE 0 END, 2
    ) as activation_to_engagement_rate,
    ROUND(
        CASE WHEN engaged_users > 0 THEN 
            (power_users::decimal / engaged_users) * 100 
        ELSE 0 END, 2
    ) as engagement_to_power_rate,
    ROUND(
        CASE WHEN power_users > 0 THEN 
            (paying_customers::decimal / power_users) * 100 
        ELSE 0 END, 2
    ) as power_to_payment_rate,
    ROUND(
        CASE WHEN total_signups > 0 THEN 
            (paying_customers::decimal / total_signups) * 100 
        ELSE 0 END, 2
    ) as overall_conversion_rate
FROM funnel_data;

-- Revenue Analytics View - Real-time revenue metrics
CREATE OR REPLACE VIEW revenue_analytics_view AS
WITH revenue_data AS (
    SELECT 
        COUNT(*) as total_transactions,
        SUM(amount) as total_revenue,
        payment_type,
        COUNT(*) as type_count
    FROM payment_transactions 
    WHERE status = 'completed'
        AND processed_at >= NOW() - INTERVAL '30 days'
    GROUP BY payment_type
)
SELECT 
    payment_type,
    type_count as transactions,
    total_revenue as revenue,
    ROUND(total_revenue / type_count, 2) as avg_transaction_value
FROM revenue_data
UNION ALL
SELECT 
    'TOTAL' as payment_type,
    SUM(type_count) as transactions,
    SUM(total_revenue) as revenue,
    ROUND(SUM(total_revenue) / SUM(type_count), 2) as avg_transaction_value
FROM revenue_data;

-- ==========================================================================
-- 5. INDEXES FOR PERFORMANCE
-- ==========================================================================

-- Email automation indexes
CREATE INDEX IF NOT EXISTS idx_email_campaigns_user_template ON email_campaigns_sent(user_id, template_name);
CREATE INDEX IF NOT EXISTS idx_email_triggers_scheduled ON email_automation_triggers(scheduled_send_at) WHERE processed = FALSE;
CREATE INDEX IF NOT EXISTS idx_email_performance_template ON email_performance(template_name);

-- Sales intelligence indexes
CREATE INDEX IF NOT EXISTS idx_sales_actions_user ON sales_actions(user_id, triggered_at);
CREATE INDEX IF NOT EXISTS idx_sales_status_changes_user ON sales_status_changes(user_id, changed_at);
CREATE INDEX IF NOT EXISTS idx_user_privileges_active ON user_privileges(user_id, privilege_type) WHERE is_active = TRUE;

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_user_segments_type ON user_segments(segment_type, confidence_score);
CREATE INDEX IF NOT EXISTS idx_conversion_predictions_score ON conversion_predictions(probability_score DESC);
CREATE INDEX IF NOT EXISTS idx_feature_usage_analytics_user ON feature_usage_analytics(user_id, feature_name);

-- ==========================================================================
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- ==========================================================================

-- Enable RLS on new tables
ALTER TABLE email_campaigns_sent ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_automation_triggers ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_status_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_privileges ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversion_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE cohort_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_usage_analytics ENABLE ROW LEVEL SECURITY;

-- Admin access policies (full access)
CREATE POLICY "Admin full access email_campaigns_sent" ON email_campaigns_sent FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access email_automation_triggers" ON email_automation_triggers FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access email_performance" ON email_performance FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access sales_actions" ON sales_actions FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access sales_status_changes" ON sales_status_changes FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access user_privileges" ON user_privileges FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access user_segments" ON user_segments FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access conversion_predictions" ON conversion_predictions FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access cohort_analysis" ON cohort_analysis FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
CREATE POLICY "Admin full access feature_usage_analytics" ON feature_usage_analytics FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

-- User access policies (own data only)
CREATE POLICY "Users view own email campaigns" ON email_campaigns_sent FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users view own privileges" ON user_privileges FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users view own segments" ON user_segments FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users view own predictions" ON conversion_predictions FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users view own feature analytics" ON feature_usage_analytics FOR SELECT USING (user_id = auth.uid());

-- ==========================================================================
-- 7. INITIAL DATA SETUP
-- ==========================================================================

-- Insert default email performance records for tracking
INSERT INTO email_performance (template_name, sent_count, opened_count, clicked_count, responded_count, conversion_count)
VALUES 
    ('welcome_25', 0, 0, 0, 0, 0),
    ('milestone_50', 0, 0, 0, 0, 0),
    ('running_low_75', 0, 0, 0, 0, 0),
    ('almost_out_90', 0, 0, 0, 0, 0),
    ('trial_complete_100', 0, 0, 0, 0, 0),
    ('power_user', 0, 0, 0, 0, 0),
    ('feature_explorer', 0, 0, 0, 0, 0),
    ('batch_processor', 0, 0, 0, 0, 0),
    ('compliance_focused', 0, 0, 0, 0, 0),
    ('hot_lead', 0, 0, 0, 0, 0),
    ('enterprise_ready', 0, 0, 0, 0, 0)
ON CONFLICT (template_name) DO NOTHING;

-- ==========================================================================
-- PHASE 3 IMPLEMENTATION COMPLETE
-- ==========================================================================

-- Success message
DO $$
BEGIN
    RAISE NOTICE '🚀 Phase 3 Sales Intelligence & Advanced Analytics tables created successfully!';
    RAISE NOTICE '📊 Email automation, sales intelligence, and analytics systems ready';
    RAISE NOTICE '💡 Views created for real-time business intelligence';
    RAISE NOTICE '🔒 Row Level Security policies configured';
    RAISE NOTICE '⚡ Performance indexes added for optimal query speed';
END $$;
