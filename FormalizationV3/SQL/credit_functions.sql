-- Credit System SQL Functions
-- Functions for credit usage statistics and analysis

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
    
    -- Daily usage calculation
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS daily_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND ua.timestamp >= NOW() - INTERVAL '1 day'
        GROUP BY ua.user_id
    ) daily_stats ON uc.user_id = daily_stats.user_id
    
    -- Weekly usage calculation
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS weekly_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND ua.timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY ua.user_id
    ) weekly_stats ON uc.user_id = weekly_stats.user_id
    
    -- Monthly usage calculation
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS monthly_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND ua.timestamp >= NOW() - INTERVAL '30 days'
        GROUP BY ua.user_id
    ) monthly_stats ON uc.user_id = monthly_stats.user_id
    
    -- Previous week usage for trend analysis
    LEFT JOIN (
        SELECT 
            ua.user_id,
            SUM(ua.credits_consumed) AS prev_week_usage
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND ua.timestamp >= NOW() - INTERVAL '14 days'
        AND ua.timestamp < NOW() - INTERVAL '7 days'
        GROUP BY ua.user_id
    ) prev_week_stats ON uc.user_id = prev_week_stats.user_id
    
    -- Session statistics
    LEFT JOIN (
        SELECT 
            ua.user_id,
            AVG(ua.credits_consumed) AS avg_credits_per_session
        FROM usage_analytics ua
        WHERE ua.user_id = user_id_param
        AND ua.timestamp >= NOW() - INTERVAL '30 days'
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
        DATE_TRUNC('week', ua.timestamp)::DATE AS week_start_date,
        (DATE_TRUNC('week', ua.timestamp) + INTERVAL '6 days')::DATE AS week_end_date,
        SUM(ua.credits_consumed) AS total_credits_used,
        AVG(daily_usage.daily_total) AS avg_daily_usage,
        daily_peak.peak_day AS peak_usage_day,
        daily_peak.peak_amount AS peak_usage_amount,
        
        -- Usage pattern analysis
        CASE 
            WHEN COUNT(DISTINCT DATE(ua.timestamp)) = 7 THEN 'consistent_daily'
            WHEN COUNT(DISTINCT DATE(ua.timestamp)) >= 5 THEN 'regular_weekday'
            WHEN COUNT(DISTINCT DATE(ua.timestamp)) <= 2 THEN 'batch_processing'
            ELSE 'irregular'
        END AS usage_pattern
        
    FROM usage_analytics ua
    
    -- Join with daily usage totals
    LEFT JOIN (
        SELECT 
            user_id,
            DATE(timestamp) AS usage_date,
            SUM(credits_consumed) AS daily_total
        FROM usage_analytics
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY user_id, DATE(timestamp)
    ) daily_usage ON ua.user_id = daily_usage.user_id 
        AND DATE(ua.timestamp) = daily_usage.usage_date
    
    -- Find peak usage day
    LEFT JOIN (
        SELECT DISTINCT ON (user_id)
            user_id,
            DATE(timestamp) AS peak_day,
            SUM(credits_consumed) AS peak_amount
        FROM usage_analytics
        WHERE timestamp >= NOW() - INTERVAL '7 days'
        GROUP BY user_id, DATE(timestamp)
        ORDER BY user_id, peak_amount DESC
    ) daily_peak ON ua.user_id = daily_peak.user_id
    
    WHERE ua.timestamp >= NOW() - INTERVAL '7 days'
    GROUP BY ua.user_id, DATE_TRUNC('week', ua.timestamp), daily_peak.peak_day, daily_peak.peak_amount
    ORDER BY ua.user_id, week_start_date;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate monthly credit trends
CREATE OR REPLACE FUNCTION calculate_monthly_credit_trends()
RETURNS TABLE (
    user_id UUID,
    month_year TEXT,
    total_credits_used INTEGER,
    trial_credits_used INTEGER,
    premium_credits_used INTEGER,
    avg_weekly_usage DECIMAL(8,2),
    growth_rate DECIMAL(5,2),
    usage_efficiency DECIMAL(5,2),
    predicted_next_month INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH monthly_usage AS (
        SELECT 
            ua.user_id,
            TO_CHAR(ua.timestamp, 'YYYY-MM') AS month_year,
            SUM(ua.credits_consumed) AS total_used,
            SUM(CASE WHEN ua.processing_tier = 'free_trial' THEN ua.credits_consumed ELSE 0 END) AS trial_used,
            SUM(CASE WHEN ua.processing_tier != 'free_trial' THEN ua.credits_consumed ELSE 0 END) AS premium_used,
            COUNT(DISTINCT DATE(ua.timestamp)) AS active_days
        FROM usage_analytics ua
        WHERE ua.timestamp >= NOW() - INTERVAL '3 months'
        GROUP BY ua.user_id, TO_CHAR(ua.timestamp, 'YYYY-MM')
    ),
    growth_calc AS (
        SELECT 
            current_month.*,
            LAG(current_month.total_used) OVER (PARTITION BY current_month.user_id ORDER BY current_month.month_year) AS prev_month_usage
        FROM monthly_usage current_month
    )
    SELECT 
        gc.user_id,
        gc.month_year,
        gc.total_used AS total_credits_used,
        gc.trial_used AS trial_credits_used,
        gc.premium_used AS premium_credits_used,
        (gc.total_used / 4.0) AS avg_weekly_usage,
        
        -- Growth rate calculation
        CASE 
            WHEN gc.prev_month_usage IS NULL OR gc.prev_month_usage = 0 THEN 0
            ELSE ((gc.total_used - gc.prev_month_usage) * 100.0 / gc.prev_month_usage)
        END AS growth_rate,
        
        -- Usage efficiency (credits per active day)
        CASE 
            WHEN gc.active_days > 0 THEN (gc.total_used * 100.0 / gc.active_days) / 30.0
            ELSE 0
        END AS usage_efficiency,
        
        -- Simple prediction for next month (based on current trend)
        CASE 
            WHEN gc.prev_month_usage IS NULL THEN gc.total_used
            ELSE GREATEST(0, gc.total_used + (gc.total_used - gc.prev_month_usage))
        END AS predicted_next_month
        
    FROM growth_calc gc
    ORDER BY gc.user_id, gc.month_year DESC;
END;
$$ LANGUAGE plpgsql;

-- Helper function to get credit usage summary for sales dashboard
CREATE OR REPLACE FUNCTION get_credit_usage_summary()
RETURNS TABLE (
    total_users INTEGER,
    active_users_today INTEGER,
    active_users_week INTEGER,
    total_credits_consumed_today INTEGER,
    total_credits_consumed_week INTEGER,
    avg_credits_per_user DECIMAL(8,2),
    high_usage_users INTEGER,
    trial_exhausted_users INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT uc.user_id)::INTEGER AS total_users,
        
        COUNT(DISTINCT CASE 
            WHEN ua_today.user_id IS NOT NULL THEN ua_today.user_id 
        END)::INTEGER AS active_users_today,
        
        COUNT(DISTINCT CASE 
            WHEN ua_week.user_id IS NOT NULL THEN ua_week.user_id 
        END)::INTEGER AS active_users_week,
        
        COALESCE(SUM(ua_today.daily_credits), 0)::INTEGER AS total_credits_consumed_today,
        COALESCE(SUM(ua_week.weekly_credits), 0)::INTEGER AS total_credits_consumed_week,
        
        AVG(uc.total_used) AS avg_credits_per_user,
        
        COUNT(CASE 
            WHEN uc.total_used > 75 THEN 1 
        END)::INTEGER AS high_usage_users,
        
        COUNT(CASE 
            WHEN uc.is_trial_exhausted = TRUE THEN 1 
        END)::INTEGER AS trial_exhausted_users
        
    FROM user_credits uc
    
    -- Today's usage
    LEFT JOIN (
        SELECT 
            user_id,
            SUM(credits_consumed) AS daily_credits
        FROM usage_analytics
        WHERE timestamp >= CURRENT_DATE
        GROUP BY user_id
    ) ua_today ON uc.user_id = ua_today.user_id
    
    -- This week's usage
    LEFT JOIN (
        SELECT 
            user_id,
            SUM(credits_consumed) AS weekly_credits
        FROM usage_analytics
        WHERE timestamp >= DATE_TRUNC('week', NOW())
        GROUP BY user_id
    ) ua_week ON uc.user_id = ua_week.user_id;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_timestamp ON usage_analytics(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_timestamp ON usage_analytics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_total_used ON user_credits(total_used);
