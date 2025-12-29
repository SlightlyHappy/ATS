-- ==========================================================================
-- PAYMENT SYSTEM TABLES FOR SUPABASE
-- Phase 2 Payment Integration - RazorPay & Credit Management
-- ==========================================================================
-- This script adds the missing payment tables to the existing Supabase schema
-- Run this after the main supabaseschema.sql has been executed
--
-- INSTRUCTIONS:
-- 1. Ensure the main supabaseschema.sql has been run first
-- 2. Copy this entire script
-- 3. Go to your Supabase Dashboard → SQL Editor
-- 4. Paste and run this script
-- ==========================================================================

-- ==========================================================================
-- 1. CREATE PAYMENT SYSTEM TABLES
-- ==========================================================================

-- User Credits Table - Tracks trial and premium credits
CREATE TABLE IF NOT EXISTS user_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Credit balances
    trial_credits INTEGER DEFAULT 100 CHECK (trial_credits >= 0),
    premium_credits INTEGER DEFAULT 0 CHECK (premium_credits >= 0),
    total_used INTEGER DEFAULT 0 CHECK (total_used >= 0),
    
    -- Status tracking
    is_trial_exhausted BOOLEAN DEFAULT FALSE,
    sales_contacted BOOLEAN DEFAULT FALSE,
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE,
    
    -- Ensure one record per user
    UNIQUE(user_id)
);

-- Credit Transactions Table - Tracks all credit movements
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Transaction details
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('deduct', 'add', 'purchase', 'refund')),
    credit_type VARCHAR(20) NOT NULL CHECK (credit_type IN ('trial', 'premium', 'enterprise')),
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL CHECK (balance_after >= 0),
    
    -- Context
    description TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payment Orders Table - RazorPay order tracking
CREATE TABLE IF NOT EXISTS payment_orders (
    order_id TEXT PRIMARY KEY,
    razorpay_order_id TEXT UNIQUE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Payment details
    payment_type TEXT NOT NULL CHECK (payment_type IN ('queue_skip', 'credit_package_10', 'credit_package_25', 'enterprise_upgrade')),
    amount INTEGER NOT NULL CHECK (amount > 0), -- Amount in paisa (INR * 100)
    currency TEXT DEFAULT 'INR',
    
    -- Status tracking
    status TEXT DEFAULT 'created' CHECK (status IN ('created', 'pending', 'paid', 'failed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE,
    razorpay_payment_id TEXT,
    
    -- Additional data
    metadata JSONB DEFAULT '{}'
);

-- Payment Transactions Table - Completed payment records
CREATE TABLE IF NOT EXISTS payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id TEXT NOT NULL REFERENCES payment_orders(order_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Payment provider details
    payment_provider VARCHAR(20) DEFAULT 'razorpay',
    razorpay_payment_id TEXT,
    amount INTEGER NOT NULL CHECK (amount > 0),
    
    -- Processing details
    status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    credits_added INTEGER DEFAULT 0 CHECK (credits_added >= 0),
    payment_status VARCHAR(20) DEFAULT 'pending',
    
    -- Verification and audit
    verified_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional data
    webhook_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- User Privileges Table - Special permissions and queue skip
CREATE TABLE IF NOT EXISTS user_privileges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Privilege details
    privilege_type TEXT NOT NULL CHECK (privilege_type IN ('queue_skip', 'priority_processing', 'enterprise_features')),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Reference to payment
    payment_reference TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Ensure unique active privileges
    UNIQUE(user_id, privilege_type, payment_reference)
);

-- Usage Analytics Table - For sales intelligence
CREATE TABLE IF NOT EXISTS usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Usage details
    feature_used VARCHAR(50) NOT NULL,
    credits_consumed INTEGER DEFAULT 1 CHECK (credits_consumed >= 0),
    processing_tier VARCHAR(20) CHECK (processing_tier IN ('free_trial', 'queue_skip', 'premium_instant', 'enterprise')),
    
    -- Session context
    session_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sales Intelligence Table - Lead scoring and qualification
CREATE TABLE IF NOT EXISTS sales_intelligence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    -- Lead scoring
    lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),
    qualification_status VARCHAR(20) DEFAULT 'new' CHECK (qualification_status IN ('new', 'qualified', 'unqualified', 'contacted', 'converted')),
    
    -- Analysis data
    usage_pattern JSONB DEFAULT '{}',
    last_activity TIMESTAMP WITH TIME ZONE,
    
    -- Sales tracking
    sales_notes TEXT,
    follow_up_scheduled TIMESTAMP WITH TIME ZONE,
    contacted_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one record per user
    UNIQUE(user_id)
);

-- ==========================================================================
-- 2. CREATE PERFORMANCE INDEXES
-- ==========================================================================

-- User Credits Indexes
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_trial_exhausted ON user_credits(is_trial_exhausted);
CREATE INDEX IF NOT EXISTS idx_user_credits_updated_at ON user_credits(updated_at DESC);

-- Credit Transactions Indexes
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_timestamp ON credit_transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type, credit_type);

-- Payment Orders Indexes
CREATE INDEX IF NOT EXISTS idx_payment_orders_user_id ON payment_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_orders_status ON payment_orders(status);
CREATE INDEX IF NOT EXISTS idx_payment_orders_created_at ON payment_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_payment_orders_razorpay_payment_id ON payment_orders(razorpay_payment_id);

-- Payment Transactions Indexes
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_order_id ON payment_transactions(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_processed_at ON payment_transactions(processed_at DESC);

-- User Privileges Indexes
CREATE INDEX IF NOT EXISTS idx_user_privileges_user_id ON user_privileges(user_id);
CREATE INDEX IF NOT EXISTS idx_user_privileges_active ON user_privileges(is_active);
CREATE INDEX IF NOT EXISTS idx_user_privileges_expires_at ON user_privileges(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_privileges_type ON user_privileges(privilege_type);

-- Usage Analytics Indexes
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_timestamp ON usage_analytics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_feature ON usage_analytics(feature_used);

-- Sales Intelligence Indexes
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_user_id ON sales_intelligence(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_score ON sales_intelligence(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_status ON sales_intelligence(qualification_status);
CREATE INDEX IF NOT EXISTS idx_sales_intelligence_last_activity ON sales_intelligence(last_activity DESC);

-- ==========================================================================
-- 3. CREATE TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ==========================================================================

-- User Credits updated_at trigger
CREATE TRIGGER update_user_credits_updated_at
    BEFORE UPDATE ON user_credits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sales Intelligence updated_at trigger
CREATE TRIGGER update_sales_intelligence_updated_at
    BEFORE UPDATE ON sales_intelligence
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================================================
-- 4. CREATE HELPER FUNCTIONS FOR PAYMENT PROCESSING
-- ==========================================================================

-- Function to initialize user credits for new users
CREATE OR REPLACE FUNCTION initialize_user_credits_for_new_user(p_user_id UUID)
RETURNS VOID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
    -- Insert initial credits for new user
    INSERT INTO user_credits (user_id, trial_credits, premium_credits, total_used)
    VALUES (p_user_id, 100, 0, 0)
    ON CONFLICT (user_id) DO NOTHING;
    
    -- Log the credit initialization
    INSERT INTO credit_transactions (
        user_id,
        transaction_type,
        credit_type,
        amount,
        balance_after,
        description
    ) VALUES (
        p_user_id,
        'add',
        'trial',
        100,
        100,
        'Initial trial credits granted'
    );
    
    -- Initialize sales intelligence record
    INSERT INTO sales_intelligence (user_id, lead_score, qualification_status, usage_pattern)
    VALUES (p_user_id, 0, 'new', '{}')
    ON CONFLICT (user_id) DO NOTHING;
END;
$$;

-- Function to process successful payment
CREATE OR REPLACE FUNCTION process_successful_payment(
    p_order_id TEXT,
    p_razorpay_payment_id TEXT,
    p_webhook_data JSONB DEFAULT '{}'
)
RETURNS JSONB
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
    v_user_id UUID;
    v_payment_type TEXT;
    v_amount INTEGER;
    v_credits_to_add INTEGER := 0;
    v_result JSONB := '{}';
BEGIN
    -- Get payment order details
    SELECT user_id, payment_type, amount
    INTO v_user_id, v_payment_type, v_amount
    FROM payment_orders
    WHERE order_id = p_order_id AND status = 'created';
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Payment order not found or already processed');
    END IF;
    
    -- Update payment order status
    UPDATE payment_orders
    SET 
        status = 'paid',
        paid_at = NOW(),
        razorpay_payment_id = p_razorpay_payment_id
    WHERE order_id = p_order_id;
    
    -- Create payment transaction record
    INSERT INTO payment_transactions (
        order_id,
        user_id,
        razorpay_payment_id,
        amount,
        status,
        credits_added,
        webhook_data
    ) VALUES (
        p_order_id,
        v_user_id,
        p_razorpay_payment_id,
        v_amount,
        'completed',
        v_credits_to_add,
        p_webhook_data
    );
    
    -- Process credits based on payment type
    IF v_payment_type = 'credit_package_10' THEN
        v_credits_to_add := 10;
    ELSIF v_payment_type = 'credit_package_25' THEN
        v_credits_to_add := 25;
    ELSIF v_payment_type = 'enterprise_upgrade' THEN
        v_credits_to_add := 1000;
    ELSIF v_payment_type = 'queue_skip' THEN
        -- Grant queue skip privilege instead of credits
        INSERT INTO user_privileges (user_id, privilege_type, payment_reference, expires_at)
        VALUES (v_user_id, 'queue_skip', p_order_id, NOW() + INTERVAL '1 hour');
        
        v_result := jsonb_build_object(
            'success', true,
            'privilege_granted', 'queue_skip',
            'expires_at', NOW() + INTERVAL '1 hour'
        );
    END IF;
    
    -- Add credits if applicable
    IF v_credits_to_add > 0 THEN
        -- Update user credits
        UPDATE user_credits
        SET 
            premium_credits = premium_credits + v_credits_to_add,
            updated_at = NOW()
        WHERE user_id = v_user_id;
        
        -- Log credit transaction
        INSERT INTO credit_transactions (
            user_id,
            transaction_type,
            credit_type,
            amount,
            balance_after,
            description
        ) VALUES (
            v_user_id,
            'add',
            'premium',
            v_credits_to_add,
            (SELECT trial_credits + premium_credits FROM user_credits WHERE user_id = v_user_id),
            'Credits purchased via ' || v_payment_type
        );
        
        -- Update payment transaction with credits added
        UPDATE payment_transactions
        SET credits_added = v_credits_to_add
        WHERE order_id = p_order_id AND razorpay_payment_id = p_razorpay_payment_id;
        
        v_result := jsonb_build_object(
            'success', true,
            'credits_added', v_credits_to_add,
            'total_credits', (SELECT trial_credits + premium_credits FROM user_credits WHERE user_id = v_user_id)
        );
    END IF;
    
    -- Update sales intelligence
    UPDATE sales_intelligence
    SET 
        qualification_status = 'converted',
        last_activity = NOW(),
        updated_at = NOW()
    WHERE user_id = v_user_id;
    
    RETURN v_result;
END;
$$;

-- ==========================================================================
-- 5. SETUP ROW LEVEL SECURITY (RLS)
-- ==========================================================================

-- Enable RLS on all payment tables
ALTER TABLE user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_privileges ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_intelligence ENABLE ROW LEVEL SECURITY;

-- User Credits Policies
CREATE POLICY "users_own_credits" ON user_credits
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_view_all_credits" ON user_credits
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Credit Transactions Policies
CREATE POLICY "users_own_credit_transactions" ON credit_transactions
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_view_all_credit_transactions" ON credit_transactions
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Payment Orders Policies
CREATE POLICY "users_own_payment_orders" ON payment_orders
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_view_all_payment_orders" ON payment_orders
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Payment Transactions Policies
CREATE POLICY "users_own_payment_transactions" ON payment_transactions
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_view_all_payment_transactions" ON payment_transactions
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- User Privileges Policies
CREATE POLICY "users_own_privileges" ON user_privileges
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_manage_all_privileges" ON user_privileges
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Usage Analytics Policies
CREATE POLICY "users_own_usage_analytics" ON usage_analytics
    FOR ALL
    USING (auth.uid() = user_id);

CREATE POLICY "admins_view_all_usage_analytics" ON usage_analytics
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Sales Intelligence Policies (Admin only)
CREATE POLICY "admins_manage_sales_intelligence" ON sales_intelligence
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles 
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ==========================================================================
-- 6. CREATE PAYMENT ANALYTICS VIEWS
-- ==========================================================================

-- Payment Analytics View
CREATE VIEW payment_analytics AS
SELECT 
    -- Payment counts
    COUNT(*) as total_payments,
    COUNT(*) FILTER (WHERE status = 'paid') as successful_payments,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_payments,
    COUNT(DISTINCT user_id) as unique_paying_users,
    
    -- Revenue analytics
    SUM(amount) FILTER (WHERE status = 'paid') as total_revenue_paisa,
    ROUND(SUM(amount) FILTER (WHERE status = 'paid') / 100.0, 2) as total_revenue_inr,
    ROUND(AVG(amount) FILTER (WHERE status = 'paid') / 100.0, 2) as avg_payment_inr,
    
    -- Payment type breakdown
    COUNT(*) FILTER (WHERE payment_type = 'queue_skip' AND status = 'paid') as queue_skip_payments,
    COUNT(*) FILTER (WHERE payment_type = 'credit_package_10' AND status = 'paid') as credit_10_payments,
    COUNT(*) FILTER (WHERE payment_type = 'credit_package_25' AND status = 'paid') as credit_25_payments,
    COUNT(*) FILTER (WHERE payment_type = 'enterprise_upgrade' AND status = 'paid') as enterprise_payments,
    
    -- Time-based analytics
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as payments_last_24h,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as payments_last_7d,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as payments_last_30d
FROM payment_orders;

-- Credit Analytics View
CREATE VIEW credit_analytics AS
SELECT 
    -- Credit distribution
    COUNT(*) as total_users_with_credits,
    SUM(trial_credits) as total_trial_credits,
    SUM(premium_credits) as total_premium_credits,
    SUM(total_used) as total_credits_consumed,
    
    -- Usage patterns
    ROUND(AVG(trial_credits), 2) as avg_trial_credits,
    ROUND(AVG(premium_credits), 2) as avg_premium_credits,
    ROUND(AVG(total_used), 2) as avg_credits_used,
    
    -- Status breakdown
    COUNT(*) FILTER (WHERE is_trial_exhausted = true) as exhausted_trial_users,
    COUNT(*) FILTER (WHERE sales_contacted = true) as contacted_users,
    COUNT(*) FILTER (WHERE premium_credits > 0) as premium_users,
    
    -- Recent activity
    COUNT(*) FILTER (WHERE last_used >= NOW() - INTERVAL '24 hours') as active_last_24h,
    COUNT(*) FILTER (WHERE last_used >= NOW() - INTERVAL '7 days') as active_last_7d,
    COUNT(*) FILTER (WHERE last_used >= NOW() - INTERVAL '30 days') as active_last_30d
FROM user_credits;

-- Sales Intelligence View
CREATE VIEW sales_analytics AS
SELECT 
    -- Lead qualification
    COUNT(*) as total_leads,
    COUNT(*) FILTER (WHERE qualification_status = 'qualified') as qualified_leads,
    COUNT(*) FILTER (WHERE qualification_status = 'converted') as converted_leads,
    COUNT(*) FILTER (WHERE qualification_status = 'contacted') as contacted_leads,
    
    -- Lead scoring
    ROUND(AVG(lead_score), 2) as avg_lead_score,
    MAX(lead_score) as max_lead_score,
    COUNT(*) FILTER (WHERE lead_score >= 80) as high_value_leads,
    COUNT(*) FILTER (WHERE lead_score >= 60) as medium_value_leads,
    
    -- Activity tracking
    COUNT(*) FILTER (WHERE last_activity >= NOW() - INTERVAL '7 days') as active_leads_7d,
    COUNT(*) FILTER (WHERE contacted_at IS NOT NULL) as contacted_leads_count,
    COUNT(*) FILTER (WHERE follow_up_scheduled IS NOT NULL) as scheduled_followups
FROM sales_intelligence;

-- ==========================================================================
-- 7. INITIALIZE CREDITS FOR EXISTING USERS
-- ==========================================================================

-- Initialize credits for any existing users who don't have them
INSERT INTO user_credits (user_id, trial_credits, premium_credits, total_used)
SELECT id, 100, 0, 0
FROM user_profiles
WHERE id NOT IN (SELECT user_id FROM user_credits);

-- Initialize sales intelligence for existing users
INSERT INTO sales_intelligence (user_id, lead_score, qualification_status, usage_pattern)
SELECT id, 0, 'new', '{}'
FROM user_profiles
WHERE id NOT IN (SELECT user_id FROM sales_intelligence);

-- ==========================================================================
-- 8. GRANT PERMISSIONS
-- ==========================================================================

-- Grant table permissions
GRANT ALL ON user_credits TO authenticated;
GRANT ALL ON credit_transactions TO authenticated;
GRANT ALL ON payment_orders TO authenticated;
GRANT ALL ON payment_transactions TO authenticated;
GRANT ALL ON user_privileges TO authenticated;
GRANT ALL ON usage_analytics TO authenticated;
GRANT SELECT ON sales_intelligence TO authenticated;
GRANT INSERT, UPDATE, DELETE ON sales_intelligence TO authenticated;

-- Grant view permissions
GRANT SELECT ON payment_analytics TO authenticated;
GRANT SELECT ON credit_analytics TO authenticated;
GRANT SELECT ON sales_analytics TO authenticated;

-- Grant function permissions
GRANT EXECUTE ON FUNCTION initialize_user_credits_for_new_user(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION process_successful_payment(TEXT, TEXT, JSONB) TO authenticated;

-- ==========================================================================
-- 9. VERIFICATION AND SUCCESS REPORTING
-- ==========================================================================

DO $$
DECLARE
    payment_tables_count INTEGER;
    payment_indexes_count INTEGER;
    payment_policies_count INTEGER;
BEGIN
    -- Count created payment objects
    SELECT COUNT(*) INTO payment_tables_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('user_credits', 'credit_transactions', 'payment_orders', 'payment_transactions', 'user_privileges', 'usage_analytics', 'sales_intelligence');
    
    SELECT COUNT(*) INTO payment_indexes_count 
    FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND tablename IN ('user_credits', 'credit_transactions', 'payment_orders', 'payment_transactions', 'user_privileges', 'usage_analytics', 'sales_intelligence');
    
    SELECT COUNT(*) INTO payment_policies_count 
    FROM pg_policies 
    WHERE schemaname = 'public' 
    AND tablename IN ('user_credits', 'credit_transactions', 'payment_orders', 'payment_transactions', 'user_privileges', 'usage_analytics', 'sales_intelligence');
    
    -- Report results
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'PAYMENT SYSTEM TABLES SETUP COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'Payment tables created: %', payment_tables_count;
    RAISE NOTICE 'Payment indexes created: %', payment_indexes_count;
    RAISE NOTICE 'Payment security policies: %', payment_policies_count;
    RAISE NOTICE '==========================================================================';
    
    IF payment_tables_count < 7 THEN
        RAISE EXCEPTION 'ERROR: Payment table creation incomplete!';
    END IF;
    
    RAISE NOTICE 'PAYMENT SYSTEM READY FOR:';
    RAISE NOTICE '✅ RazorPay payment processing';
    RAISE NOTICE '✅ Credit management and tracking';
    RAISE NOTICE '✅ Queue skip privileges';
    RAISE NOTICE '✅ Sales intelligence and lead scoring';
    RAISE NOTICE '✅ Payment analytics and reporting';
    RAISE NOTICE '==========================================================================';
    RAISE NOTICE 'Your payment system tables are ready for Phase 2 implementation!';
    RAISE NOTICE '==========================================================================';
END $$;

-- Final verification queries
SELECT 'SUCCESS: User credits ready' as status, COUNT(*) as user_count FROM user_credits;
SELECT 'SUCCESS: Sales intelligence ready' as status, COUNT(*) as lead_count FROM sales_intelligence;
SELECT 'READY: Payment system' as status, 
       CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payment_orders') THEN 'Ready' ELSE 'Missing' END as payment_status;
