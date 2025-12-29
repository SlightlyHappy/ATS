-- Backup System Database Schema
-- Tables for tracking backups, health monitoring, and disaster recovery
-- Created: August 3, 2025

-- Backup metadata tracking table
CREATE TABLE IF NOT EXISTS backup_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_name VARCHAR(255) NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_size_mb DECIMAL(10,2) NOT NULL,
    checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,2),
    compressed BOOLEAN DEFAULT false,
    verified BOOLEAN DEFAULT false,
    supabase_synced BOOLEAN DEFAULT false,
    database_health VARCHAR(20),
    backup_type VARCHAR(50) DEFAULT 'full',
    created_by VARCHAR(100) DEFAULT 'system',
    metadata JSONB,
    
    -- Indexing for performance
    INDEX idx_backup_metadata_created_at (created_at),
    INDEX idx_backup_metadata_backup_name (backup_name),
    INDEX idx_backup_metadata_database_health (database_health)
);

-- System health monitoring logs
CREATE TABLE IF NOT EXISTS system_health_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    health_status VARCHAR(20) NOT NULL, -- 'healthy', 'warning', 'critical', 'unknown'
    metrics JSONB NOT NULL, -- JSON containing all health metrics
    issues JSONB, -- JSON array of detected issues
    checked_by VARCHAR(100) NOT NULL,
    check_duration_ms INTEGER,
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexing for performance
    INDEX idx_health_logs_timestamp (check_timestamp),
    INDEX idx_health_logs_status (health_status),
    INDEX idx_health_logs_checked_by (checked_by)
);

-- Backup restoration logs
CREATE TABLE IF NOT EXISTS backup_restore_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_name VARCHAR(255) NOT NULL,
    restore_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    restore_completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,2),
    target_database VARCHAR(255),
    restored_by VARCHAR(100) NOT NULL,
    restore_status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'in_progress'
    error_message TEXT,
    metadata JSONB,
    
    -- Foreign key to backup metadata
    FOREIGN KEY (backup_name) REFERENCES backup_metadata(backup_name) ON DELETE CASCADE,
    
    -- Indexing for performance
    INDEX idx_restore_logs_started_at (restore_started_at),
    INDEX idx_restore_logs_backup_name (backup_name),
    INDEX idx_restore_logs_status (restore_status)
);

-- System alerts and notifications
CREATE TABLE IF NOT EXISTS system_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(50) NOT NULL, -- 'backup_failed', 'health_critical', 'disk_space_low', etc.
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical', 'urgent'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(100),
    auto_resolved BOOLEAN DEFAULT false,
    notification_sent BOOLEAN DEFAULT false,
    metadata JSONB,
    
    -- Indexing for performance
    INDEX idx_alerts_created_at (created_at),
    INDEX idx_alerts_severity (severity),
    INDEX idx_alerts_type (alert_type),
    INDEX idx_alerts_resolved (resolved_at)
);

-- Backup configuration settings
CREATE TABLE IF NOT EXISTS backup_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_name VARCHAR(100) NOT NULL UNIQUE,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100) NOT NULL,
    
    -- Only one active configuration allowed
    CONSTRAINT unique_active_config EXCLUDE (is_active WITH =) WHERE (is_active = true),
    
    -- Indexing for performance
    INDEX idx_backup_configs_name (config_name),
    INDEX idx_backup_configs_active (is_active)
);

-- Performance monitoring for database operations
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metric_type VARCHAR(50) NOT NULL, -- 'query_time', 'connection_pool', 'disk_io', etc.
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(20), -- 'ms', 'percent', 'bytes', etc.
    source_component VARCHAR(100), -- 'backup_manager', 'user_endpoints', 'admin_endpoints'
    metadata JSONB,
    
    -- Indexing for time-series queries
    INDEX idx_performance_timestamp (metric_timestamp),
    INDEX idx_performance_type (metric_type),
    INDEX idx_performance_component (source_component)
);

-- Data retention policy table
CREATE TABLE IF NOT EXISTS data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    retention_days INTEGER NOT NULL,
    cleanup_schedule VARCHAR(50), -- 'daily', 'weekly', 'monthly'
    last_cleanup_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Unique policy per table
    UNIQUE(table_name),
    
    -- Indexing
    INDEX idx_retention_table (table_name),
    INDEX idx_retention_active (is_active)
);

-- Insert default data retention policies
INSERT INTO data_retention_policies (table_name, retention_days, cleanup_schedule, is_active) VALUES
('backup_metadata', 90, 'weekly', true),
('system_health_logs', 60, 'daily', true),
('backup_restore_logs', 180, 'monthly', true),
('system_alerts', 30, 'daily', true),
('performance_metrics', 30, 'daily', true),
('user_activity_detailed', 365, 'weekly', true)
ON CONFLICT (table_name) DO NOTHING;

-- Insert default backup configuration
INSERT INTO backup_configurations (config_name, config_data, is_active, created_by) VALUES 
('default_production', '{
    "max_backup_age_hours": 24,
    "backup_retention_days": 30,
    "backup_directory": "data/backups",
    "enable_compression": true,
    "enable_encryption": false,
    "max_backup_size_gb": 5,
    "backup_verification": true,
    "supabase_sync_enabled": true,
    "health_check_interval": 15,
    "max_response_time_ms": 5000,
    "max_connection_pool_usage": 80,
    "min_free_space_gb": 2,
    "alert_thresholds": {
        "warning": 70,
        "critical": 90
    }
}', true, 'system')
ON CONFLICT (config_name) DO UPDATE SET 
    config_data = EXCLUDED.config_data,
    updated_at = NOW();

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_backup_metadata_size ON backup_metadata(file_size_bytes);
CREATE INDEX IF NOT EXISTS idx_health_logs_metrics ON system_health_logs USING GIN (metrics);
CREATE INDEX IF NOT EXISTS idx_alerts_metadata ON system_alerts USING GIN (metadata);

-- Create function to automatically cleanup old records
CREATE OR REPLACE FUNCTION cleanup_old_records()
RETURNS void AS $$
DECLARE
    policy RECORD;
    cutoff_date TIMESTAMP WITH TIME ZONE;
    deleted_count INTEGER;
BEGIN
    -- Loop through active retention policies
    FOR policy IN SELECT * FROM data_retention_policies WHERE is_active = true LOOP
        cutoff_date := NOW() - INTERVAL '1 day' * policy.retention_days;
        
        -- Execute cleanup based on table name
        CASE policy.table_name
            WHEN 'backup_metadata' THEN
                DELETE FROM backup_metadata WHERE created_at < cutoff_date;
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
            WHEN 'system_health_logs' THEN
                DELETE FROM system_health_logs WHERE check_timestamp < cutoff_date;
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
            WHEN 'backup_restore_logs' THEN
                DELETE FROM backup_restore_logs WHERE restore_started_at < cutoff_date;
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
            WHEN 'system_alerts' THEN
                DELETE FROM system_alerts WHERE created_at < cutoff_date AND resolved_at IS NOT NULL;
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
            WHEN 'performance_metrics' THEN
                DELETE FROM performance_metrics WHERE metric_timestamp < cutoff_date;
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
            WHEN 'user_activity_detailed' THEN
                DELETE FROM user_activity_detailed WHERE created_at < cutoff_date;
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
            ELSE
                CONTINUE;
        END CASE;
        
        -- Update last cleanup timestamp
        UPDATE data_retention_policies 
        SET last_cleanup_at = NOW() 
        WHERE table_name = policy.table_name;
        
        -- Log the cleanup operation
        INSERT INTO system_health_logs (health_status, metrics, checked_by)
        VALUES ('healthy', json_build_object(
            'cleanup_operation', policy.table_name,
            'records_deleted', deleted_count,
            'retention_days', policy.retention_days
        ), 'cleanup_function');
        
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create a function to generate backup health summary
CREATE OR REPLACE FUNCTION get_backup_health_summary()
RETURNS TABLE(
    total_backups INTEGER,
    successful_backups INTEGER,
    last_backup_age_hours DECIMAL,
    avg_backup_size_mb DECIMAL,
    health_status TEXT,
    critical_issues INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_backups,
        COUNT(*) FILTER (WHERE completed_at IS NOT NULL)::INTEGER as successful_backups,
        EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) / 3600 as last_backup_age_hours,
        AVG(file_size_mb) as avg_backup_size_mb,
        CASE 
            WHEN EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) / 3600 > 24 THEN 'critical'
            WHEN EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) / 3600 > 12 THEN 'warning'
            ELSE 'healthy'
        END as health_status,
        (SELECT COUNT(*)::INTEGER FROM system_alerts WHERE severity = 'critical' AND resolved_at IS NULL) as critical_issues
    FROM backup_metadata
    WHERE created_at >= NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Create a function to automatically create alerts for critical conditions
CREATE OR REPLACE FUNCTION check_and_create_alerts()
RETURNS void AS $$
DECLARE
    backup_age_hours DECIMAL;
    critical_health_count INTEGER;
    low_disk_space BOOLEAN := false;
BEGIN
    -- Check backup age
    SELECT EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) / 3600 
    INTO backup_age_hours
    FROM backup_metadata;
    
    IF backup_age_hours > 24 THEN
        INSERT INTO system_alerts (alert_type, severity, title, message, metadata)
        VALUES (
            'backup_overdue',
            'critical',
            'Backup Overdue',
            'No backup has been created in the last 24 hours',
            json_build_object('hours_since_last_backup', backup_age_hours)
        )
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Check for critical health issues
    SELECT COUNT(*) 
    INTO critical_health_count
    FROM system_health_logs 
    WHERE health_status = 'critical' 
        AND check_timestamp >= NOW() - INTERVAL '1 hour';
    
    IF critical_health_count > 0 THEN
        INSERT INTO system_alerts (alert_type, severity, title, message, metadata)
        VALUES (
            'system_health_critical',
            'critical',
            'System Health Critical',
            'Critical health issues detected in the last hour',
            json_build_object('critical_checks_count', critical_health_count)
        );
    END IF;
    
END;
$$ LANGUAGE plpgsql;

-- Add comments to tables for documentation
COMMENT ON TABLE backup_metadata IS 'Tracks all backup operations including metadata, verification status, and sync status';
COMMENT ON TABLE system_health_logs IS 'Records system health checks with detailed metrics and issue tracking';
COMMENT ON TABLE backup_restore_logs IS 'Logs all backup restoration operations for audit and troubleshooting';
COMMENT ON TABLE system_alerts IS 'Manages system alerts and notifications for critical events';
COMMENT ON TABLE backup_configurations IS 'Stores backup system configuration settings';
COMMENT ON TABLE performance_metrics IS 'Collects performance metrics for monitoring and optimization';
COMMENT ON TABLE data_retention_policies IS 'Defines data retention policies for automatic cleanup';

-- Final validation
SELECT 'Backup system database schema created successfully' as status;
