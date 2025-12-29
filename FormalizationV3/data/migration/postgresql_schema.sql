-- PostgreSQL Schema Migration
-- Generated from SQLite schema
-- Generated on: 2025-07-29 12:31:26.235639

-- Table: admin_users
CREATE TABLE IF NOT EXISTS admin_users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    permissions TEXT DEFAULT '["all"]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Table: users
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

-- Table: user_sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table: admin_sessions
CREATE TABLE IF NOT EXISTS admin_sessions (
    id BIGINT PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table: system_analytics
CREATE TABLE IF NOT EXISTS system_analytics (
    id BIGINT PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- Table: api_usage
CREATE TABLE IF NOT EXISTS api_usage (
    id BIGINT PRIMARY KEY,
    user_id BIGINT,
    admin_id BIGINT,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code BIGINT,
    response_time_ms BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Table: user_credits
CREATE TABLE IF NOT EXISTS user_credits (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    trial_credits BIGINT DEFAULT 100,
    premium_credits BIGINT DEFAULT 0,
    total_used BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_trial_exhausted BOOLEAN DEFAULT FALSE,
    sales_contacted BOOLEAN DEFAULT FALSE
);

-- Table: credit_transactions
CREATE TABLE IF NOT EXISTS credit_transactions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    credit_type VARCHAR(20) NOT NULL,
    amount BIGINT NOT NULL,
    balance_after BIGINT NOT NULL,
    description TEXT,
    metadata TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: usage_analytics
CREATE TABLE IF NOT EXISTS usage_analytics (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    feature_used VARCHAR(50) NOT NULL,
    credits_consumed BIGINT DEFAULT 1,
    processing_tier VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_data TEXT
);

-- Table: sales_intelligence
CREATE TABLE IF NOT EXISTS sales_intelligence (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    lead_score BIGINT DEFAULT 0,
    qualification_status VARCHAR(20) DEFAULT 'new',
    usage_pattern TEXT,
    last_activity TIMESTAMP,
    sales_notes TEXT,
    follow_up_scheduled TIMESTAMP,
    contacted_at TIMESTAMP
);

-- Table: payment_transactions
CREATE TABLE IF NOT EXISTS payment_transactions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    payment_provider VARCHAR(20) DEFAULT 'razorpay',
    payment_id VARCHAR(100),
    order_id VARCHAR(100),
    amount_inr BIGINT NOT NULL,
    credits_purchased BIGINT NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_supabase_id ON users(supabase_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_token ON admin_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_expires ON admin_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_analytics_metric ON system_analytics(metric_name);
CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON system_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_timestamp ON credit_transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_timestamp ON usage_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_user_id ON sales_intelligence(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_score ON sales_intelligence(lead_score);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_admin_users_id ON admin_users(id);
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_status ON admin_users(status);
CREATE INDEX IF NOT EXISTS idx_users_id ON users(id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_id ON user_sessions(id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_agent ON user_sessions(user_agent);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_id ON admin_sessions(id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_admin_id ON admin_sessions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_sessions_user_agent ON admin_sessions(user_agent);
CREATE INDEX IF NOT EXISTS idx_system_analytics_id ON system_analytics(id);
CREATE INDEX IF NOT EXISTS idx_api_usage_id ON api_usage(id);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_admin_id ON api_usage(admin_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_status_code ON api_usage(status_code);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_agent ON api_usage(user_agent);
CREATE INDEX IF NOT EXISTS idx_user_credits_id ON user_credits(id);
CREATE INDEX IF NOT EXISTS idx_user_credits_updated_at ON user_credits(updated_at);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_id ON credit_transactions(id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_id ON usage_analytics(id);
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_id ON sales_intelligence(id);
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_qualification_status ON sales_intelligence(qualification_status);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_id ON payment_transactions(id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_payment_provider ON payment_transactions(payment_provider);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_payment_id ON payment_transactions(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_order_id ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_payment_status ON payment_transactions(payment_status);