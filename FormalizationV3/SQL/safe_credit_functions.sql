-- Safe Credit System SQL Functions
-- Functions for credit usage statistics and analysis with column existence checks

-- First, ensure usage_analytics table has the required timestamp column
DO $$
BEGIN
    -- Ensure timestamp column exists (primary timestamp column)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usage_analytics' AND column_name = 'timestamp') THEN
        ALTER TABLE usage_analytics ADD COLUMN timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added timestamp column to usage_analytics';
    END IF;
    
    -- Ensure created_at column exists for compatibility
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'usage_analytics' AND column_name = 'created_at') THEN
        ALTER TABLE usage_analytics ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
        RAISE NOTICE 'Added created_at column to usage_analytics';
        
        -- Copy timestamp data to created_at for existing records
        UPDATE usage_analytics SET created_at = timestamp WHERE created_at IS NULL;
    END IF;
END $$;

-- Function to get user credit usage statistics
CREATE OR REPLACE FUNCTION get_user_credit_usage_stats(user_id_param UUID)
RETURNS TABLE (
    user_id UUID,
    trial_credits INTEGER,
    premium_credits INTEGER,
    total_used INTEGER,
    credits_remaining INTEGER,
    daily_usage DECIMAL(8,2),
    weekly_usage DECIMAL(8,2),
    monthly_usage DECIMAL(8,2),
    avg_credits_per_session DECIMAL(8,2),
    last_usage_date TIMESTAMP WITH TIME ZONE,
    usage_trend VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        uc.user_id,
        uc.trial_credits,
        uc.premium_credits,
        uc.total_used,
        (uc.trial_credits + uc.premium_credits) AS credits_remaining,
        
        -- Daily usage (last 24 hours)
        COALESCE(daily_stats.daily_usage, 0) AS daily_usage,
        
        -- Weekly usage (last 7 days)
        COALESCE(weekly_stats.weekly_usage, 0) AS weekly_usage,
        
        -- Monthly usage (last 30 days)
        COALESCE(monthly_stats.monthly_usage, 0) AS monthly_usage,
        
        -- Average credits per session
        COALESCE(session_stats.avg_credits_per_session, 0) AS avg_credits_per_session,
        
        -- Last usage date
        uc.last_used AS last_usage_date,
        
        -- Usage trend analysis
        CASE 
            WHEN COALESCE(weekly_stats.weekly_usage, 0) > COALESCE(prev_week_stats.prev_week_usage, 0) THEN 'increasing'
            WHEN COALESCE(weekly_stats.weekly_usage, 0) < COALESCE(prev_week_stats.prev_week_usage, 0) THEN 'decreasing'
            ELSE 'stable'
        END AS usage_trend
        
    FROM user_credits uc
    
    -- Daily usage stats (last 24 hours)
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS daily_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND COALESCE(ua.timestamp, ua.created_at) >= NOW() - INTERVAL '1 day'
        GROUP BY ua.user_id
    ) daily_stats ON uc.user_id = daily_stats.user_id
    
    -- Weekly usage stats (last 7 days)
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS weekly_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND COALESCE(ua.timestamp, ua.created_at) >= NOW() - INTERVAL '7 days'
        GROUP BY ua.user_id
    ) weekly_stats ON uc.user_id = weekly_stats.user_id
    
    -- Monthly usage stats (last 30 days)
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS monthly_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND COALESCE(ua.timestamp, ua.created_at) >= NOW() - INTERVAL '30 days'
        GROUP BY ua.user_id
    ) monthly_stats ON uc.user_id = monthly_stats.user_id
    
    -- Previous week stats for trend analysis
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS prev_week_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND COALESCE(ua.timestamp, ua.created_at) >= NOW() - INTERVAL '14 days'
        AND COALESCE(ua.timestamp, ua.created_at) < NOW() - INTERVAL '7 days'
        GROUP BY ua.user_id
    ) prev_week_stats ON uc.user_id = prev_week_stats.user_id
    
    -- Session stats (average credits per session)
    LEFT JOIN (
        SELECT 
            ua.user_id,
            AVG(ua.credits_consumed) AS avg_credits_per_session
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND COALESCE(ua.timestamp, ua.created_at) >= NOW() - INTERVAL '30 days'
        GROUP BY ua.user_id
    ) session_stats ON uc.user_id = session_stats.user_id
    
    WHERE uc.user_id = user_id_param;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate weekly credit usage for all users
CREATE OR REPLACE FUNCTION calculate_weekly_credit_usage()
RETURNS TABLE (
    user_id UUID,
    week_start_date DATE,
    week_end_date DATE,
    total_credits_used INTEGER,
    avg_daily_usage DECIMAL(8,2),
    peak_usage_day DATE,
    peak_usage_amount INTEGER,
    usage_pattern VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ua.user_id,
        DATE_TRUNC('week', COALESCE(ua.timestamp, ua.created_at))::DATE AS week_start_date,
        (DATE_TRUNC('week', COALESCE(ua.timestamp, ua.created_at)) + INTERVAL '6 days')::DATE AS week_end_date,
        SUM(ua.credits_consumed) AS total_credits_used,
        AVG(daily_usage.daily_total) AS avg_daily_usage,
        daily_peak.peak_day AS peak_usage_day,
        daily_peak.peak_amount AS peak_usage_amount,
        
        -- Usage pattern analysis
        CASE 
            WHEN COUNT(DISTINCT DATE(COALESCE(ua.timestamp, ua.created_at))) = 7 THEN 'consistent_daily'
            WHEN COUNT(DISTINCT DATE(COALESCE(ua.timestamp, ua.created_at))) >= 5 THEN 'regular_weekday'
            WHEN COUNT(DISTINCT DATE(COALESCE(ua.timestamp, ua.created_at))) <= 2 THEN 'batch_processing'
            ELSE 'irregular'
        END AS usage_pattern
        
    FROM usage_analytics ua
    
    -- Join with daily usage totals
    LEFT JOIN (
        SELECT 
            user_id,
            DATE(COALESCE(timestamp, created_at)) AS usage_date,
            SUM(credits_consumed) AS daily_total
        FROM usage_analytics
        WHERE COALESCE(timestamp, created_at) >= NOW() - INTERVAL '7 days'
        GROUP BY user_id, DATE(COALESCE(timestamp, created_at))
    ) daily_usage ON ua.user_id = daily_usage.user_id
        AND DATE(COALESCE(ua.timestamp, ua.created_at)) = daily_usage.usage_date
    
    -- Join with peak usage day
    LEFT JOIN (
        SELECT 
            user_id,
            DATE(COALESCE(timestamp, created_at)) AS peak_day,
            SUM(credits_consumed) AS peak_amount
        FROM usage_analytics
        WHERE COALESCE(timestamp, created_at) >= NOW() - INTERVAL '7 days'
        GROUP BY user_id, DATE(COALESCE(timestamp, created_at))
        ORDER BY peak_amount DESC
        LIMIT 1
    ) daily_peak ON ua.user_id = daily_peak.user_id
    
    WHERE COALESCE(ua.timestamp, ua.created_at) >= NOW() - INTERVAL '7 days'
    GROUP BY ua.user_id, DATE_TRUNC('week', COALESCE(ua.timestamp, ua.created_at)), daily_peak.peak_day, daily_peak.peak_amount
    ORDER BY week_start_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to analyze credit consumption patterns
CREATE OR REPLACE FUNCTION analyze_credit_consumption_patterns()
RETURNS TABLE (
    pattern_type VARCHAR(50),
    user_count INTEGER,
    avg_credits_per_user DECIMAL(8,2),
    total_credits_consumed INTEGER,
    percentage_of_total DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH user_patterns AS (
        SELECT 
            uc.user_id,
            uc.total_used,
            CASE 
                WHEN uc.total_used = 0 THEN 'inactive'
                WHEN uc.total_used <= 10 THEN 'light_usage'
                WHEN uc.total_used <= 50 THEN 'moderate_usage'
                WHEN uc.total_used <= 200 THEN 'heavy_usage'
                ELSE 'power_user'
            END AS pattern_type
        FROM user_credits uc
    ),
    pattern_stats AS (
        SELECT 
            up.pattern_type,
            COUNT(up.user_id) AS user_count,
            AVG(up.total_used) AS avg_credits_per_user,
            SUM(up.total_used) AS total_credits_consumed
        FROM user_patterns up
        GROUP BY up.pattern_type
    ),
    total_consumption AS (
        SELECT SUM(total_used) AS grand_total
        FROM user_credits
    )
    SELECT 
        ps.pattern_type,
        ps.user_count,
        ps.avg_credits_per_user,
        ps.total_credits_consumed,
        CASE 
            WHEN tc.grand_total > 0 THEN (ps.total_credits_consumed::DECIMAL / tc.grand_total * 100)
            ELSE 0
        END AS percentage_of_total
    FROM pattern_stats ps
    CROSS JOIN total_consumption tc
    ORDER BY ps.total_credits_consumed DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get system-wide credit statistics
CREATE OR REPLACE FUNCTION get_system_credit_stats()
RETURNS TABLE (
    total_users INTEGER,
    active_users INTEGER,
    total_trial_credits INTEGER,
    total_premium_credits INTEGER,
    total_credits_consumed INTEGER,
    avg_credits_per_user DECIMAL(8,2),
    trial_exhausted_users INTEGER,
    sales_contacted_users INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER AS total_users,
        COUNT(CASE WHEN last_used >= NOW() - INTERVAL '30 days' THEN 1 END)::INTEGER AS active_users,
        SUM(trial_credits)::INTEGER AS total_trial_credits,
        SUM(premium_credits)::INTEGER AS total_premium_credits,
        SUM(total_used)::INTEGER AS total_credits_consumed,
        AVG(total_used) AS avg_credits_per_user,
        COUNT(CASE WHEN is_trial_exhausted = true THEN 1 END)::INTEGER AS trial_exhausted_users,
        COUNT(CASE WHEN sales_contacted = true THEN 1 END)::INTEGER AS sales_contacted_users
    FROM user_credits;
END;
$$ LANGUAGE plpgsql;

-- Notification: Functions created successfully
DO $$
BEGIN
    RAISE NOTICE '✅ All credit system functions created successfully!';
    RAISE NOTICE '🔧 Functions use safe column references with COALESCE for compatibility';
    RAISE NOTICE '📊 Functions available: get_user_credit_usage_stats, calculate_weekly_credit_usage, analyze_credit_consumption_patterns, get_system_credit_stats';
END $$;
