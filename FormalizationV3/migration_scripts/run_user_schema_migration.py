#!/usr/bin/env python3
"""
COMPREHENSIVE Railway PostgreSQL User Schema Migration
Sets up ALL database tables and extensions required for the complete HR ATS user endpoints implementation
Based on comprehensive analysis of frontend request documents and backend requirements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from railway_database import RailwayPostgreSQL
from dotenv import load_dotenv
import json

def main():
    # Load environment variables
    load_dotenv()
    
    print('🚀 Starting COMPREHENSIVE Railway PostgreSQL User Schema Migration...')
    print('📋 Based on Frontend Request Plan & Implementation Requirements')
    print(f'DATABASE_URL: {"✅ Found" if os.getenv("DATABASE_URL") else "❌ Not found"}')
    print(f'DATABASE_PUBLIC_URL: {"✅ Found" if os.getenv("DATABASE_PUBLIC_URL") else "❌ Not found"}')
    
    try:
        # Initialize Railway PostgreSQL connection
        print('🔗 Connecting to Railway PostgreSQL...')
        railway_db = RailwayPostgreSQL()
        
        # Test connection
        print('✅ Railway PostgreSQL connection established')
        
        # Run comprehensive schema setup
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                
                # Enable UUID extension
                print('🔧 Enabling UUID extension...')
                cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
                
                # ==================================================
                # PHASE 1: CORE USER PROFILE EXTENSIONS
                # ==================================================
                print('📊 Phase 1: User Profile Extensions...')
                
                # Check if user_profiles table exists and add missing columns
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'user_profiles' AND table_schema = 'public'
                """)
                existing_columns = [row[0] for row in cursor.fetchall()]
                
                # Extended user profile columns for complete user management
                new_columns = [
                    ('phone', 'VARCHAR(20)'),
                    ('avatar_url', 'TEXT'),
                    ('location_data', 'JSONB'),
                    ('professional_info', 'JSONB'),  # Job title, company, salary expectations
                    ('preferences', 'JSONB'),        # Notification preferences, privacy settings
                    ('security_settings', 'JSONB'), # 2FA, session preferences
                    ('timezone', 'VARCHAR(50) DEFAULT \'UTC\''),
                    ('last_active', 'TIMESTAMP WITH TIME ZONE'),
                    ('account_status', 'VARCHAR(20) DEFAULT \'active\''),  # active, suspended, deleted
                    ('email_verified', 'BOOLEAN DEFAULT false'),
                    ('phone_verified', 'BOOLEAN DEFAULT false'),
                    ('onboarding_completed', 'BOOLEAN DEFAULT false'),
                    ('marketing_consent', 'BOOLEAN DEFAULT false'),
                    ('data_retention_consent', 'BOOLEAN DEFAULT false'),
                    ('last_login_ip', 'INET'),
                    ('failed_login_attempts', 'INTEGER DEFAULT 0'),
                    ('account_locked_until', 'TIMESTAMP WITH TIME ZONE'),
                    ('password_changed_at', 'TIMESTAMP WITH TIME ZONE'),
                    ('profile_completion_score', 'INTEGER DEFAULT 0') # 0-100
                ]
                
                for column_name, column_type in new_columns:
                    if column_name not in existing_columns:
                        cursor.execute(f"ALTER TABLE user_profiles ADD COLUMN {column_name} {column_type}")
                        print(f'  ✅ Added column: {column_name}')
                    else:
                        print(f'  ⏭️  Column exists: {column_name}')
                
                # ==================================================
                # PHASE 2: ENHANCED ACTIVITY LOGGING SYSTEM
                # ==================================================
                print('📊 Phase 2: Enhanced Activity Logging System...')
                
                # Comprehensive activity tracking (replaces basic user_activity)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_activity_detailed (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        action VARCHAR(100) NOT NULL,
                        category VARCHAR(50) NOT NULL, -- 'content', 'account', 'billing', 'security', 'system'
                        sub_action VARCHAR(100),        -- More specific action type
                        details JSONB NOT NULL,         -- Action-specific details
                        metadata JSONB,                 -- IP, device, location, user_agent, session_id
                        status VARCHAR(20) DEFAULT 'success', -- 'success', 'failed', 'warning', 'info'
                        severity VARCHAR(20) DEFAULT 'low',   -- 'low', 'medium', 'high', 'critical'
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE  -- For GDPR compliance (auto-delete old logs)
                    )
                ''')
                
                # Activity tracking indexes for performance
                activity_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_activity_detailed_user_id ON user_activity_detailed(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_activity_detailed_category ON user_activity_detailed(category)',
                    'CREATE INDEX IF NOT EXISTS idx_user_activity_detailed_created_at ON user_activity_detailed(created_at)',
                    'CREATE INDEX IF NOT EXISTS idx_user_activity_detailed_action ON user_activity_detailed(action)',
                    'CREATE INDEX IF NOT EXISTS idx_user_activity_detailed_status ON user_activity_detailed(status)',
                    'CREATE INDEX IF NOT EXISTS idx_user_activity_detailed_severity ON user_activity_detailed(severity)',
                    'CREATE INDEX IF NOT EXISTS idx_user_activity_detailed_expires_at ON user_activity_detailed(expires_at)'
                ]
                
                for index in activity_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 3: USER ANALYTICS & USAGE STATISTICS
                # ==================================================
                print('📊 Phase 3: User Analytics & Usage Statistics...')
                
                # Daily user usage statistics for analytics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_usage_stats (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        period_start DATE NOT NULL,
                        period_end DATE NOT NULL,
                        period_type VARCHAR(20) DEFAULT 'daily', -- 'daily', 'weekly', 'monthly'
                        
                        -- Resume statistics
                        resumes_uploaded INTEGER DEFAULT 0,
                        resumes_analyzed INTEGER DEFAULT 0,
                        avg_analysis_score DECIMAL(5,2),
                        total_processing_time_seconds INTEGER DEFAULT 0,
                        
                        -- Feature usage
                        dashboard_views INTEGER DEFAULT 0,
                        profile_updates INTEGER DEFAULT 0,
                        searches_performed INTEGER DEFAULT 0,
                        exports_generated INTEGER DEFAULT 0,
                        
                        -- Engagement metrics
                        session_count INTEGER DEFAULT 0,
                        total_session_duration_seconds INTEGER DEFAULT 0,
                        unique_features_used INTEGER DEFAULT 0,
                        
                        -- Business metrics
                        time_saved_hours DECIMAL(10,2) DEFAULT 0,
                        cost_per_analysis DECIMAL(10,2) DEFAULT 0,
                        roi_score DECIMAL(5,2) DEFAULT 0,
                        
                        -- Metadata
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        UNIQUE(user_id, period_start, period_end, period_type)
                    )
                ''')
                
                # Usage stats indexes
                usage_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_usage_stats_user_id ON user_usage_stats(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_usage_stats_period ON user_usage_stats(period_start, period_end)',
                    'CREATE INDEX IF NOT EXISTS idx_user_usage_stats_type ON user_usage_stats(period_type)'
                ]
                
                for index in usage_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 4: ENHANCED SESSION MANAGEMENT
                # ==================================================
                print('📊 Phase 4: Enhanced Session Management...')
                
                # User sessions with device tracking and security features
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        session_token VARCHAR(500) UNIQUE NOT NULL,
                        refresh_token VARCHAR(500) UNIQUE,
                        
                        -- Session timing
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        -- Device and security tracking
                        ip_address INET,
                        user_agent TEXT,
                        device_fingerprint VARCHAR(255),
                        device_type VARCHAR(50),          -- 'desktop', 'mobile', 'tablet'
                        browser_name VARCHAR(100),
                        browser_version VARCHAR(50),
                        os_name VARCHAR(100),
                        os_version VARCHAR(50),
                        
                        -- Geolocation
                        country_code VARCHAR(5),
                        city VARCHAR(100),
                        timezone_offset INTEGER,
                        
                        -- Security flags
                        is_active BOOLEAN DEFAULT true,
                        is_suspicious BOOLEAN DEFAULT false,
                        risk_score INTEGER DEFAULT 0,    -- 0-100
                        security_flags JSONB,            -- Array of security concerns
                        
                        -- Session metadata
                        session_data JSONB,              -- Additional session data
                        revoked_at TIMESTAMP WITH TIME ZONE,
                        revoked_by VARCHAR(50),          -- 'user', 'admin', 'system', 'security'
                        revoke_reason VARCHAR(200)
                    )
                ''')
                
                # Session management indexes
                session_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_refresh_token ON user_sessions(refresh_token)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_device_fingerprint ON user_sessions(device_fingerprint)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_is_suspicious ON user_sessions(is_suspicious)',
                    'CREATE INDEX IF NOT EXISTS idx_user_sessions_last_used ON user_sessions(last_used)'
                ]
                
                for index in session_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 5: PASSWORD RESET & SECURITY TOKENS
                # ==================================================
                print('📊 Phase 5: Password Reset & Security Token System...')
                
                # Password reset tokens for forgot password functionality
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS password_reset_tokens (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        token VARCHAR(255) UNIQUE NOT NULL,
                        token_hash VARCHAR(255) NOT NULL,    -- Hashed version for security
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        used_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        -- Security tracking
                        ip_address INET,
                        user_agent TEXT,
                        attempts_count INTEGER DEFAULT 0,
                        is_valid BOOLEAN DEFAULT true,
                        
                        -- Metadata
                        metadata JSONB
                    )
                ''')
                
                # Email verification tokens
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS email_verification_tokens (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        email VARCHAR(255) NOT NULL,        -- Email being verified
                        token VARCHAR(255) UNIQUE NOT NULL,
                        token_hash VARCHAR(255) NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        verified_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        -- Security
                        ip_address INET,
                        attempts_count INTEGER DEFAULT 0,
                        is_valid BOOLEAN DEFAULT true
                    )
                ''')
                
                # Security token indexes
                security_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token)',
                    'CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at)',
                    'CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token ON email_verification_tokens(token)',
                    'CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_email ON email_verification_tokens(email)'
                ]
                
                for index in security_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 6: SUBSCRIPTION & PAYMENT SYSTEM
                # ==================================================
                print('📊 Phase 6: Comprehensive Subscription & Payment System...')
                
                # User subscriptions with full lifecycle management
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_subscriptions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Subscription details
                        plan_id VARCHAR(100) NOT NULL,              -- 'trial', 'basic', 'professional', 'enterprise'
                        plan_name VARCHAR(255) NOT NULL,
                        billing_cycle VARCHAR(20) NOT NULL,         -- 'monthly', 'yearly', 'lifetime'
                        status VARCHAR(50) DEFAULT 'active',        -- 'active', 'cancelled', 'expired', 'suspended'
                        
                        -- Pricing
                        amount DECIMAL(10,2) NOT NULL,              -- Subscription amount
                        currency VARCHAR(10) DEFAULT 'INR',
                        
                        -- Billing dates
                        started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                        current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                        trial_start TIMESTAMP WITH TIME ZONE,
                        trial_end TIMESTAMP WITH TIME ZONE,
                        cancelled_at TIMESTAMP WITH TIME ZONE,
                        ends_at TIMESTAMP WITH TIME ZONE,           -- Final end date (after cancellation)
                        
                        -- Limits and quotas
                        monthly_resume_limit INTEGER,
                        monthly_legal_query_limit INTEGER,
                        storage_limit_gb INTEGER,
                        api_rate_limit INTEGER,
                        
                        -- Usage tracking
                        current_usage JSONB,                        -- Current period usage
                        
                        -- Payment details
                        razorpay_subscription_id VARCHAR(255),
                        payment_method JSONB,                       -- Payment method details
                        
                        -- Metadata
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        UNIQUE(user_id, plan_id, current_period_start)
                    )
                ''')
                
                # Enhanced payment orders with subscription context
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS payment_orders (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        subscription_id UUID REFERENCES user_subscriptions(id) ON DELETE SET NULL,
                        
                        -- RazorPay integration
                        razorpay_order_id VARCHAR(255) UNIQUE NOT NULL,
                        razorpay_payment_id VARCHAR(255),
                        razorpay_signature VARCHAR(500),
                        
                        -- Order details
                        order_type VARCHAR(50) NOT NULL,            -- 'subscription', 'upgrade', 'credit_purchase', 'one_time'
                        package_type VARCHAR(100) NOT NULL,
                        amount INTEGER NOT NULL,                    -- Amount in paise
                        currency VARCHAR(10) DEFAULT 'INR',
                        status VARCHAR(50) DEFAULT 'created',       -- 'created', 'pending', 'paid', 'failed', 'refunded'
                        
                        -- Timing
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        paid_at TIMESTAMP WITH TIME ZONE,
                        failed_at TIMESTAMP WITH TIME ZONE,
                        refunded_at TIMESTAMP WITH TIME ZONE,
                        
                        -- Additional details
                        description TEXT,
                        failure_reason TEXT,
                        refund_reason TEXT,
                        metadata JSONB
                    )
                ''')
                
                # Payment transactions with detailed tracking
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS payment_transactions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        order_id UUID NOT NULL REFERENCES payment_orders(id) ON DELETE CASCADE,
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Transaction details
                        transaction_id VARCHAR(255) UNIQUE NOT NULL,
                        transaction_type VARCHAR(50) NOT NULL,      -- 'charge', 'refund', 'partial_refund'
                        amount INTEGER NOT NULL,
                        currency VARCHAR(10) DEFAULT 'INR',
                        status VARCHAR(50) NOT NULL,
                        
                        -- Payment method
                        payment_method VARCHAR(50),                 -- 'card', 'netbanking', 'wallet', 'upi'
                        card_type VARCHAR(50),                      -- 'visa', 'mastercard', 'amex', etc.
                        bank VARCHAR(100),
                        
                        -- Timestamps
                        processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        -- Additional data
                        gateway_response JSONB,
                        fees_charged DECIMAL(10,2),
                        tax_amount DECIMAL(10,2),
                        net_amount DECIMAL(10,2),
                        
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                ''')
                
                # Payment system indexes
                payment_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status)',
                    'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_plan_id ON user_subscriptions(plan_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_subscriptions_current_period ON user_subscriptions(current_period_start, current_period_end)',
                    'CREATE INDEX IF NOT EXISTS idx_payment_orders_user_id ON payment_orders(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_payment_orders_razorpay_order_id ON payment_orders(razorpay_order_id)',
                    'CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status)',
                    'CREATE INDEX IF NOT EXISTS idx_payment_orders_created_at ON payment_orders(created_at)',
                    'CREATE INDEX IF NOT EXISTS idx_payment_transactions_order_id ON payment_transactions(order_id)',
                    'CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_payment_transactions_transaction_id ON payment_transactions(transaction_id)'
                ]
                
                for index in payment_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 7: ENHANCED RESUME MANAGEMENT
                # ==================================================
                print('📊 Phase 7: Enhanced Resume Management System...')
                
                # Enhanced resumes table with all required fields
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resumes (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- File information
                        filename VARCHAR(255) NOT NULL,
                        original_filename VARCHAR(255),
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        file_hash VARCHAR(255),
                        file_type VARCHAR(20) DEFAULT 'pdf',
                        
                        -- Upload details
                        upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        uploaded_from_ip INET,
                        
                        -- Processing information
                        processing_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
                        processing_started_at TIMESTAMP WITH TIME ZONE,
                        processing_completed_at TIMESTAMP WITH TIME ZONE,
                        processing_duration_seconds INTEGER,
                        processing_error TEXT,
                        processing_tier VARCHAR(50),                     -- 'free_trial', 'premium', 'enterprise'
                        
                        -- Candidate information
                        candidate_name VARCHAR(255),
                        candidate_email VARCHAR(255),
                        candidate_phone VARCHAR(50),
                        candidate_location VARCHAR(255),
                        
                        -- Analysis scores (0-100)
                        overall_score DECIMAL(5,2),
                        technical_score DECIMAL(5,2),
                        experience_score DECIMAL(5,2),
                        education_score DECIMAL(5,2),
                        skills_score DECIMAL(5,2),
                        communication_score DECIMAL(5,2),
                        
                        -- Extracted information
                        skills TEXT[],
                        experience_years INTEGER,
                        education_level VARCHAR(100),
                        job_titles TEXT[],
                        companies TEXT[],
                        certifications TEXT[],
                        languages TEXT[],
                        
                        -- AI analysis results
                        analysis_data JSONB,                            -- Complete AI analysis
                        analysis_summary TEXT,
                        ai_feedback TEXT,
                        ai_model_used VARCHAR(100),
                        
                        -- User organization
                        tags TEXT[],
                        category VARCHAR(100) DEFAULT 'general',
                        is_favorite BOOLEAN DEFAULT false,
                        is_archived BOOLEAN DEFAULT false,
                        notes TEXT,
                        custom_fields JSONB,
                        
                        -- Sharing and privacy
                        visibility VARCHAR(20) DEFAULT 'private',       -- 'private', 'shared', 'public'
                        shared_with JSONB,                              -- Array of user IDs or teams
                        
                        -- Search optimization
                        search_vector tsvector,                         -- Full-text search
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_viewed_at TIMESTAMP WITH TIME ZONE,
                        archived_at TIMESTAMP WITH TIME ZONE
                    )
                ''')
                
                # Resume analysis indexes for performance
                resume_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_upload_date ON resumes(upload_date)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_processing_status ON resumes(processing_status)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_overall_score ON resumes(overall_score)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_candidate_name ON resumes(candidate_name)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_candidate_email ON resumes(candidate_email)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_skills ON resumes USING GIN(skills)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_tags ON resumes USING GIN(tags)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_category ON resumes(category)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_visibility ON resumes(visibility)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_search_vector ON resumes USING GIN(search_vector)',
                    'CREATE INDEX IF NOT EXISTS idx_resumes_file_hash ON resumes(file_hash)'
                ]
                
                for index in resume_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 8: ENTERPRISE & COMPLIANCE FEATURES
                # ==================================================
                print('📊 Phase 8: Enterprise & Compliance Features...')
                
                # Data export requests for GDPR compliance
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_export_requests (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Request details
                        export_type VARCHAR(50) NOT NULL,           -- 'full', 'partial', 'specific'
                        data_types TEXT[],                          -- ['profile', 'resumes', 'activity', 'payments']
                        format VARCHAR(20) DEFAULT 'json',          -- 'json', 'csv', 'pdf'
                        
                        -- Status tracking
                        status VARCHAR(50) DEFAULT 'requested',     -- 'requested', 'processing', 'ready', 'downloaded', 'expired'
                        requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        processed_at TIMESTAMP WITH TIME ZONE,
                        downloaded_at TIMESTAMP WITH TIME ZONE,
                        expires_at TIMESTAMP WITH TIME ZONE,
                        
                        -- File details
                        file_path TEXT,
                        file_size INTEGER,
                        download_count INTEGER DEFAULT 0,
                        
                        -- Security
                        download_token VARCHAR(255) UNIQUE,
                        ip_address INET,
                        
                        -- Metadata
                        metadata JSONB,
                        processing_log TEXT
                    )
                ''')
                
                # Account deletion requests and audit trail
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS account_deletion_requests (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Request details
                        deletion_type VARCHAR(50) NOT NULL,         -- 'immediate', 'scheduled', 'soft'
                        reason VARCHAR(500),
                        confirmation_token VARCHAR(255),
                        
                        -- Status tracking
                        status VARCHAR(50) DEFAULT 'requested',     -- 'requested', 'confirmed', 'processing', 'completed', 'cancelled'
                        requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        confirmed_at TIMESTAMP WITH TIME ZONE,
                        scheduled_for TIMESTAMP WITH TIME ZONE,
                        completed_at TIMESTAMP WITH TIME ZONE,
                        
                        -- Data retention
                        data_backup_path TEXT,
                        retention_period_days INTEGER DEFAULT 30,
                        
                        -- Security
                        ip_address INET,
                        user_agent TEXT,
                        
                        -- Audit
                        processed_by UUID,                          -- Admin user ID
                        processing_notes TEXT,
                        metadata JSONB
                    )
                ''')
                
                # API access tokens for enterprise integrations
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS api_access_tokens (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Token details
                        token_name VARCHAR(255) NOT NULL,
                        token_value VARCHAR(500) UNIQUE NOT NULL,
                        token_hash VARCHAR(255) NOT NULL,
                        
                        -- Permissions and scope
                        scopes TEXT[],                              -- ['read:resumes', 'write:resumes', 'read:analytics']
                        permissions JSONB,
                        rate_limit INTEGER DEFAULT 1000,           -- Requests per hour
                        
                        -- Status and timing
                        is_active BOOLEAN DEFAULT true,
                        expires_at TIMESTAMP WITH TIME ZONE,
                        last_used_at TIMESTAMP WITH TIME ZONE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        -- Usage tracking
                        total_requests INTEGER DEFAULT 0,
                        last_request_ip INET,
                        
                        -- Security
                        allowed_ips INET[],
                        security_policy JSONB
                    )
                ''')
                
                # Enterprise compliance indexes
                compliance_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_data_export_requests_user_id ON data_export_requests(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_data_export_requests_status ON data_export_requests(status)',
                    'CREATE INDEX IF NOT EXISTS idx_account_deletion_requests_user_id ON account_deletion_requests(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_account_deletion_requests_status ON account_deletion_requests(status)',
                    'CREATE INDEX IF NOT EXISTS idx_api_access_tokens_user_id ON api_access_tokens(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_api_access_tokens_token_value ON api_access_tokens(token_value)',
                    'CREATE INDEX IF NOT EXISTS idx_api_access_tokens_is_active ON api_access_tokens(is_active)'
                ]
                
                for index in compliance_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 9: NOTIFICATION & COMMUNICATION SYSTEM
                # ==================================================
                print('📊 Phase 9: Notification & Communication System...')
                
                # User notification preferences
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_notification_preferences (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Email notifications
                        email_resume_completed BOOLEAN DEFAULT true,
                        email_payment_success BOOLEAN DEFAULT true,
                        email_payment_failed BOOLEAN DEFAULT true,
                        email_subscription_changes BOOLEAN DEFAULT true,
                        email_security_alerts BOOLEAN DEFAULT true,
                        email_marketing BOOLEAN DEFAULT false,
                        email_weekly_summary BOOLEAN DEFAULT true,
                        
                        -- Push notifications
                        push_resume_completed BOOLEAN DEFAULT true,
                        push_payment_updates BOOLEAN DEFAULT true,
                        push_security_alerts BOOLEAN DEFAULT true,
                        
                        -- SMS notifications
                        sms_security_alerts BOOLEAN DEFAULT false,
                        sms_payment_updates BOOLEAN DEFAULT false,
                        
                        -- Frequency settings
                        digest_frequency VARCHAR(20) DEFAULT 'weekly', -- 'daily', 'weekly', 'monthly', 'never'
                        quiet_hours_start TIME,
                        quiet_hours_end TIME,
                        timezone VARCHAR(50) DEFAULT 'UTC',
                        
                        -- Communication preferences
                        preferred_language VARCHAR(10) DEFAULT 'en',
                        communication_channel VARCHAR(20) DEFAULT 'email', -- 'email', 'sms', 'push'
                        
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        UNIQUE(user_id)
                    )
                ''')
                
                # Notification queue for reliable delivery
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notification_queue (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Notification details
                        notification_type VARCHAR(100) NOT NULL,    -- 'resume_completed', 'payment_success', etc.
                        channel VARCHAR(20) NOT NULL,              -- 'email', 'sms', 'push', 'in_app'
                        priority INTEGER DEFAULT 5,                -- 1-10 (1 = highest priority)
                        
                        -- Content
                        subject VARCHAR(500),
                        content TEXT NOT NULL,
                        content_html TEXT,
                        
                        -- Delivery tracking
                        status VARCHAR(50) DEFAULT 'pending',       -- 'pending', 'sent', 'delivered', 'failed', 'cancelled'
                        scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        sent_at TIMESTAMP WITH TIME ZONE,
                        delivered_at TIMESTAMP WITH TIME ZONE,
                        
                        -- Retry logic
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        next_retry_at TIMESTAMP WITH TIME ZONE,
                        
                        -- Tracking
                        external_id VARCHAR(255),                  -- Provider-specific tracking ID
                        delivery_status JSONB,                     -- Provider response details
                        
                        -- Metadata
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                ''')
                
                # Notification indexes
                notification_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_notification_preferences_user_id ON user_notification_preferences(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_notification_queue_user_id ON notification_queue(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_notification_queue_status ON notification_queue(status)',
                    'CREATE INDEX IF NOT EXISTS idx_notification_queue_scheduled_for ON notification_queue(scheduled_for)',
                    'CREATE INDEX IF NOT EXISTS idx_notification_queue_priority ON notification_queue(priority)',
                    'CREATE INDEX IF NOT EXISTS idx_notification_queue_retry ON notification_queue(next_retry_at, retry_count)'
                ]
                
                for index in notification_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 10: SEARCH & CACHING OPTIMIZATION
                # ==================================================
                print('📊 Phase 10: Search & Caching Optimization...')
                
                # User search history for improved experience
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_search_history (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Search details
                        search_query TEXT NOT NULL,
                        search_type VARCHAR(50) NOT NULL,          -- 'resume', 'candidate', 'skill', 'general'
                        search_filters JSONB,                     -- Applied filters
                        
                        -- Results
                        results_count INTEGER DEFAULT 0,
                        results_preview JSONB,                    -- Top 3 results for quick access
                        
                        -- Performance
                        execution_time_ms INTEGER,
                        search_index_used VARCHAR(100),
                        
                        -- User interaction
                        clicked_results INTEGER[] DEFAULT '{}',   -- Array of result IDs that were clicked
                        bookmarked BOOLEAN DEFAULT false,
                        
                        -- Timing
                        searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                ''')
                
                # Cache invalidation tracking
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache_invalidation_log (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        
                        -- Cache details
                        cache_key VARCHAR(500) NOT NULL,
                        cache_type VARCHAR(100) NOT NULL,          -- 'user_dashboard', 'resume_list', 'analytics'
                        user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
                        
                        -- Invalidation reason
                        reason VARCHAR(200) NOT NULL,              -- 'data_updated', 'user_action', 'scheduled_refresh'
                        triggered_by VARCHAR(100),                 -- 'user', 'system', 'admin'
                        
                        -- Timing
                        invalidated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        
                        -- Metadata
                        metadata JSONB
                    )
                ''')
                
                # Search and cache indexes
                search_indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_user_search_history_user_id ON user_search_history(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_user_search_history_search_type ON user_search_history(search_type)',
                    'CREATE INDEX IF NOT EXISTS idx_user_search_history_searched_at ON user_search_history(searched_at)',
                    'CREATE INDEX IF NOT EXISTS idx_cache_invalidation_log_cache_type ON cache_invalidation_log(cache_type)',
                    'CREATE INDEX IF NOT EXISTS idx_cache_invalidation_log_user_id ON cache_invalidation_log(user_id)',
                    'CREATE INDEX IF NOT EXISTS idx_cache_invalidation_log_invalidated_at ON cache_invalidation_log(invalidated_at)'
                ]
                
                for index in search_indexes:
                    cursor.execute(index)
                
                # ==================================================
                # PHASE 11: TRIGGERS & AUTOMATION
                # ==================================================
                print('📊 Phase 11: Database Triggers & Automation...')
                
                # Update triggers for updated_at columns
                cursor.execute('''
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = NOW();
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                ''')
                
                # Apply update triggers to relevant tables
                update_trigger_tables = [
                    'user_profiles',
                    'user_subscriptions', 
                    'payment_orders',
                    'resumes',
                    'user_notification_preferences'
                ]
                
                for table in update_trigger_tables:
                    trigger_sql = f'''
                        DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                        CREATE TRIGGER update_{table}_updated_at 
                        BEFORE UPDATE ON {table} 
                        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                    '''
                    cursor.execute(trigger_sql)
                    print(f'  ✅ Created update trigger for {table}')
                
                # Search vector update trigger for resumes
                cursor.execute('''
                    CREATE OR REPLACE FUNCTION update_resume_search_vector()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.search_vector := to_tsvector('english', 
                            COALESCE(NEW.filename, '') || ' ' ||
                            COALESCE(NEW.candidate_name, '') || ' ' ||
                            COALESCE(NEW.candidate_email, '') || ' ' ||
                            COALESCE(array_to_string(NEW.skills, ' '), '') || ' ' ||
                            COALESCE(array_to_string(NEW.job_titles, ' '), '') || ' ' ||
                            COALESCE(array_to_string(NEW.companies, ' '), '') || ' ' ||
                            COALESCE(NEW.analysis_summary, '') || ' ' ||
                            COALESCE(array_to_string(NEW.tags, ' '), '')
                        );
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                ''')
                
                cursor.execute('''
                    DROP TRIGGER IF EXISTS update_resume_search_vector_trigger ON resumes;
                    CREATE TRIGGER update_resume_search_vector_trigger
                    BEFORE INSERT OR UPDATE ON resumes
                    FOR EACH ROW EXECUTE FUNCTION update_resume_search_vector();
                ''')
                
                # Activity logging trigger for security events
                cursor.execute('''
                    CREATE OR REPLACE FUNCTION log_security_events()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        -- Log password changes
                        IF TG_OP = 'UPDATE' AND OLD.password_changed_at IS DISTINCT FROM NEW.password_changed_at THEN
                            INSERT INTO user_activity_detailed (user_id, action, category, details, metadata, severity)
                            VALUES (
                                NEW.id,
                                'password_changed',
                                'security',
                                '{"event": "password_updated", "timestamp": "' || NOW() || '"}',
                                '{"ip_address": null, "trigger": "database_trigger"}',
                                'high'
                            );
                        END IF;
                        
                        -- Log account status changes
                        IF TG_OP = 'UPDATE' AND OLD.account_status IS DISTINCT FROM NEW.account_status THEN
                            INSERT INTO user_activity_detailed (user_id, action, category, details, metadata, severity)
                            VALUES (
                                NEW.id,
                                'account_status_changed',
                                'security',
                                '{"event": "account_status_change", "old_status": "' || OLD.account_status || '", "new_status": "' || NEW.account_status || '"}',
                                '{"ip_address": null, "trigger": "database_trigger"}',
                                'high'
                            );
                        END IF;
                        
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                ''')
                
                cursor.execute('''
                    DROP TRIGGER IF EXISTS log_security_events_trigger ON user_profiles;
                    CREATE TRIGGER log_security_events_trigger
                    AFTER UPDATE ON user_profiles
                    FOR EACH ROW EXECUTE FUNCTION log_security_events();
                ''')
                
                # ==================================================
                # PHASE 12: DATA VALIDATION & CONSTRAINTS
                # ==================================================
                print('📊 Phase 12: Data Validation & Constraints...')
                
                # Add check constraints for data integrity
                validation_constraints = [
                    # User profile constraints
                    "ALTER TABLE user_profiles ADD CONSTRAINT chk_profile_completion_score CHECK (profile_completion_score >= 0 AND profile_completion_score <= 100)",
                    "ALTER TABLE user_profiles ADD CONSTRAINT chk_failed_login_attempts CHECK (failed_login_attempts >= 0)",
                    "ALTER TABLE user_profiles ADD CONSTRAINT chk_account_status CHECK (account_status IN ('active', 'suspended', 'deleted', 'pending'))",
                    
                    # Resume constraints
                    "ALTER TABLE resumes ADD CONSTRAINT chk_overall_score CHECK (overall_score >= 0 AND overall_score <= 100)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_technical_score CHECK (technical_score >= 0 AND technical_score <= 100)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_experience_score CHECK (experience_score >= 0 AND experience_score <= 100)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_education_score CHECK (education_score >= 0 AND education_score <= 100)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_skills_score CHECK (skills_score >= 0 AND skills_score <= 100)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_communication_score CHECK (communication_score >= 0 AND communication_score <= 100)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_experience_years CHECK (experience_years >= 0 AND experience_years <= 70)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_file_size CHECK (file_size > 0)",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_processing_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))",
                    "ALTER TABLE resumes ADD CONSTRAINT chk_visibility CHECK (visibility IN ('private', 'shared', 'public'))",
                    
                    # Session constraints
                    "ALTER TABLE user_sessions ADD CONSTRAINT chk_risk_score CHECK (risk_score >= 0 AND risk_score <= 100)",
                    "ALTER TABLE user_sessions ADD CONSTRAINT chk_session_timing CHECK (expires_at > created_at)",
                    
                    # Payment constraints
                    "ALTER TABLE payment_orders ADD CONSTRAINT chk_payment_amount CHECK (amount > 0)",
                    "ALTER TABLE payment_transactions ADD CONSTRAINT chk_transaction_amount CHECK (amount > 0)",
                    
                    # Subscription constraints
                    "ALTER TABLE user_subscriptions ADD CONSTRAINT chk_subscription_amount CHECK (amount >= 0)",
                    "ALTER TABLE user_subscriptions ADD CONSTRAINT chk_subscription_period CHECK (current_period_end > current_period_start)",
                    "ALTER TABLE user_subscriptions ADD CONSTRAINT chk_subscription_status CHECK (status IN ('active', 'cancelled', 'expired', 'suspended'))",
                    "ALTER TABLE user_subscriptions ADD CONSTRAINT chk_billing_cycle CHECK (billing_cycle IN ('monthly', 'yearly', 'lifetime'))"
                ]
                
                for constraint in validation_constraints:
                    try:
                        cursor.execute(constraint)
                        print(f'  ✅ Added constraint: {constraint.split()[3]}')
                    except Exception as e:
                        if 'already exists' in str(e).lower():
                            print(f'  ⏭️  Constraint exists: {constraint.split()[3]}')
                        else:
                            print(f'  ⚠️  Failed to add constraint: {e}')
            
            conn.commit()
        
        print('\n🎉 COMPREHENSIVE DATABASE SCHEMA MIGRATION COMPLETED! 🎉')
        print('=' * 80)
        print('✅ All required tables created with proper indexing')
        print('✅ User profile extensions added (phone, avatar, professional info)')
        print('✅ Enhanced activity logging system ready')
        print('✅ Comprehensive usage statistics tracking ready')
        print('✅ Advanced session management with security features')
        print('✅ Password reset and email verification systems ready')
        print('✅ Full subscription and payment management system')
        print('✅ Enhanced resume management with search capabilities')
        print('✅ Enterprise compliance features (GDPR, data export)')
        print('✅ API access token management')
        print('✅ Notification and communication preferences')
        print('✅ Search optimization and caching systems')
        print('✅ Database triggers and automation')
        print('✅ Data validation constraints')
        print('=' * 80)
        print('🚀 Ready for complete user endpoint implementation!')
        
        # Verify tables were created
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                print(f'\n📊 Database tables verified ({len(tables)} total):')
                
                # Group tables by category for better readability
                table_categories = {
                    'Core': ['user_profiles', 'resumes'],
                    'Activity & Analytics': ['user_activity_detailed', 'user_usage_stats', 'user_search_history'],
                    'Authentication & Security': ['user_sessions', 'password_reset_tokens', 'email_verification_tokens'],
                    'Payment & Subscription': ['user_subscriptions', 'payment_orders', 'payment_transactions'],
                    'Communication': ['user_notification_preferences', 'notification_queue'],
                    'Enterprise': ['data_export_requests', 'account_deletion_requests', 'api_access_tokens'],
                    'System': ['cache_invalidation_log']
                }
                
                for category, expected_tables in table_categories.items():
                    print(f'  {category}:')
                    for table in expected_tables:
                        status = '✅' if table in tables else '❌'
                        print(f'    {status} {table}')
                
                # Check for any additional tables not in our categories
                categorized_tables = []
                for cat_tables in table_categories.values():
                    categorized_tables.extend(cat_tables)
                
                additional_tables = [t for t in tables if t not in categorized_tables]
                if additional_tables:
                    print(f'  Additional tables: {", ".join(additional_tables)}')
        
        return True
        
    except Exception as e:
        print(f'❌ Migration failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
