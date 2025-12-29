"""
Database migration script for Sales Intelligence features.
Creates all necessary tables for lead scoring, ROI calculations, and sales metrics.
"""

# Sales Intelligence Database Schema
sales_intelligence_schema = """
-- ============================================================================
-- LEADS TABLE - Lead profiles and scoring
-- ============================================================================
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    
    -- Lead classification
    status VARCHAR(20) NOT NULL DEFAULT 'cold' CHECK (status IN ('cold', 'warm', 'hot', 'qualified', 'converted', 'lost')),
    source VARCHAR(20) NOT NULL DEFAULT 'organic' CHECK (source IN ('organic', 'referral', 'demo', 'marketing', 'api', 'direct')),
    
    -- Scoring
    overall_score INTEGER DEFAULT 0 CHECK (overall_score >= 0 AND overall_score <= 100),
    engagement_score INTEGER DEFAULT 0 CHECK (engagement_score >= 0 AND engagement_score <= 40),
    usage_score INTEGER DEFAULT 0 CHECK (usage_score >= 0 AND usage_score <= 30),
    potential_score INTEGER DEFAULT 0 CHECK (potential_score >= 0 AND potential_score <= 30),
    
    -- Lead details
    company_name VARCHAR(200),
    industry VARCHAR(100),
    company_size VARCHAR(50) CHECK (company_size IN ('startup', 'small', 'medium', 'large', 'enterprise')),
    estimated_monthly_analyses INTEGER DEFAULT 0,
    budget_range VARCHAR(50) CHECK (budget_range IN ('low', 'medium', 'high', 'enterprise')),
    
    -- Activity tracking
    first_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_score_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Qualification data
    qualification_notes TEXT,
    qualification_metadata JSONB DEFAULT '{}',
    
    -- Conversion tracking
    converted_at TIMESTAMP,
    conversion_value FLOAT,
    conversion_source VARCHAR(100),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for leads table
CREATE INDEX idx_leads_user_id ON leads(user_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_score ON leads(overall_score);
CREATE INDEX idx_leads_source ON leads(source);
CREATE INDEX idx_leads_last_activity ON leads(last_activity);
CREATE INDEX idx_leads_created ON leads(created_at);

-- ============================================================================
-- LEAD_SCORE_HISTORY TABLE - Track score changes over time
-- ============================================================================
CREATE TABLE lead_score_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    old_score INTEGER NOT NULL,
    new_score INTEGER NOT NULL,
    change_reason VARCHAR(100),
    
    score_breakdown JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for lead_score_history table
CREATE INDEX idx_score_history_lead_id ON lead_score_history(lead_id);
CREATE INDEX idx_score_history_created ON lead_score_history(created_at);

-- ============================================================================
-- LEAD_ACTIVITIES TABLE - Track lead activities and touchpoints
-- ============================================================================
CREATE TABLE lead_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    
    activity_type VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for lead_activities table
CREATE INDEX idx_activities_lead_id ON lead_activities(lead_id);
CREATE INDEX idx_activities_type ON lead_activities(activity_type);
CREATE INDEX idx_activities_created ON lead_activities(created_at);

-- ============================================================================
-- SALES_METRICS TABLE - Aggregated sales metrics for reporting
-- ============================================================================
CREATE TABLE sales_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    metric_date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL CHECK (metric_type IN ('daily', 'weekly', 'monthly')),
    
    -- Lead metrics
    total_leads INTEGER DEFAULT 0,
    new_leads INTEGER DEFAULT 0,
    hot_leads INTEGER DEFAULT 0,
    qualified_leads INTEGER DEFAULT 0,
    converted_leads INTEGER DEFAULT 0,
    
    -- Conversion metrics
    conversion_rate FLOAT DEFAULT 0.0,
    average_score FLOAT DEFAULT 0.0,
    average_time_to_conversion FLOAT,
    
    -- Revenue metrics
    total_conversion_value FLOAT DEFAULT 0.0,
    average_deal_size FLOAT DEFAULT 0.0,
    
    -- Additional metrics
    metrics_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sales_metrics table
CREATE INDEX idx_metrics_date ON sales_metrics(metric_date);
CREATE INDEX idx_metrics_type ON sales_metrics(metric_type);
CREATE INDEX idx_metrics_date_type ON sales_metrics(metric_date, metric_type);

-- ============================================================================
-- ROI_CALCULATIONS TABLE - Store ROI calculations for prospects
-- ============================================================================
CREATE TABLE roi_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Input parameters
    monthly_analyses INTEGER NOT NULL,
    time_saved_per_analysis FLOAT DEFAULT 2.0,
    hourly_rate FLOAT NOT NULL,
    current_process_cost FLOAT,
    
    -- Calculated results
    monthly_time_savings FLOAT,
    monthly_cost_savings FLOAT,
    platform_cost FLOAT,
    net_savings FLOAT,
    roi_percentage FLOAT,
    payback_period_days FLOAT,
    
    -- Additional calculations
    annual_savings FLOAT,
    three_year_savings FLOAT,
    
    calculation_metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for roi_calculations table
CREATE INDEX idx_roi_lead_id ON roi_calculations(lead_id);
CREATE INDEX idx_roi_created ON roi_calculations(created_at);
CREATE INDEX idx_roi_monthly_analyses ON roi_calculations(monthly_analyses);

-- ============================================================================
-- TRIGGERS for automatic timestamp updates
-- ============================================================================

-- Update trigger for leads table
CREATE OR REPLACE FUNCTION update_leads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_leads_updated_at();

-- ============================================================================
-- INITIAL DATA AND CONSTRAINTS
-- ============================================================================

-- Add foreign key constraint to ensure leads reference valid users
ALTER TABLE leads 
ADD CONSTRAINT fk_leads_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Ensure unique constraint on user_id (one lead profile per user)
ALTER TABLE leads 
ADD CONSTRAINT unique_lead_user_id UNIQUE (user_id);

-- Add check constraints for score ranges
ALTER TABLE leads 
ADD CONSTRAINT check_overall_score_range 
CHECK (overall_score >= 0 AND overall_score <= 100);

ALTER TABLE leads 
ADD CONSTRAINT check_engagement_score_range 
CHECK (engagement_score >= 0 AND engagement_score <= 40);

ALTER TABLE leads 
ADD CONSTRAINT check_usage_score_range 
CHECK (usage_score >= 0 AND usage_score <= 30);

ALTER TABLE leads 
ADD CONSTRAINT check_potential_score_range 
CHECK (potential_score >= 0 AND potential_score <= 30);

-- ============================================================================
-- VIEWS for common queries
-- ============================================================================

-- Hot leads view
CREATE VIEW hot_leads_view AS
SELECT 
    l.*,
    u.email,
    u.first_name,
    u.last_name,
    u.created_at as user_created_at,
    u.total_credits_used,
    u.credits_balance
FROM leads l
JOIN users u ON l.user_id = u.id
WHERE l.overall_score >= 70
ORDER BY l.overall_score DESC;

-- Lead activity summary view
CREATE VIEW lead_activity_summary AS
SELECT 
    l.id as lead_id,
    l.overall_score,
    l.status,
    u.email,
    COUNT(la.id) as total_activities,
    MAX(la.created_at) as last_activity_date,
    COUNT(CASE WHEN la.activity_type = 'hot_lead_alert' THEN 1 END) as alert_count
FROM leads l
JOIN users u ON l.user_id = u.id
LEFT JOIN lead_activities la ON l.id = la.lead_id
GROUP BY l.id, l.overall_score, l.status, u.email;

-- Sales performance view
CREATE VIEW sales_performance_view AS
SELECT 
    DATE_TRUNC('week', created_at) as week_start,
    COUNT(*) as new_leads,
    COUNT(CASE WHEN overall_score >= 70 THEN 1 END) as hot_leads,
    COUNT(CASE WHEN status = 'qualified' THEN 1 END) as qualified_leads,
    COUNT(CASE WHEN status = 'converted' THEN 1 END) as converted_leads,
    AVG(overall_score) as average_score
FROM leads
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week_start;

"""

def print_migration_sql():
    """Print the SQL migration script."""
    print("-- Sales Intelligence Database Migration")
    print("-- Run this SQL script in your PostgreSQL database")
    print("-- to create all necessary tables for lead scoring")
    print("")
    print(sales_intelligence_schema)

if __name__ == "__main__":
    print_migration_sql()
