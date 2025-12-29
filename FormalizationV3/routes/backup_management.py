"""
Backup Management Routes - Admin endpoints for backup operations and health monitoring
Provides comprehensive backup management and system health monitoring capabilities

Created: August 3, 2025
Author: Production Engineering Team
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from typing import Dict, Any, Optional

from auth_middleware import require_admin_auth
from utils.backup_health_manager import get_backup_health_manager
from railway_database import railway_db

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint for backup management routes
backup_bp = Blueprint('backup', __name__, url_prefix='/api/admin/backup')

def _get_standardized_response(success: bool, data: Any = None, message: str = None, error: str = None, code: str = None) -> Dict[str, Any]:
    """Generate standardized API response format"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if success:
        if data is not None:
            response['data'] = data
        if message:
            response['message'] = message
    else:
        if error:
            response['error'] = error
        if code:
            response['code'] = code
    
    return response

@backup_bp.route('/create', methods=['POST'])
@require_admin_auth
def create_backup():
    """
    Create a new database backup
    
    Body:
    {
        "backup_name": "optional_custom_name",
        "compress": true,
        "verify": true,
        "sync_to_supabase": true
    }
    """
    try:
        backup_manager = get_backup_health_manager()
        if not backup_manager:
            return jsonify(_get_standardized_response(
                success=False,
                error="Backup manager not initialized",
                code="BACKUP_MANAGER_ERROR"
            )), 500
        
        # Parse request data
        data = request.get_json() or {}
        backup_name = data.get('backup_name')
        
        # Override configuration if specified
        if 'compress' in data:
            backup_manager.backup_config['enable_compression'] = data['compress']
        if 'verify' in data:
            backup_manager.backup_config['backup_verification'] = data['verify']
        if 'sync_to_supabase' in data:
            backup_manager.backup_config['supabase_sync_enabled'] = data['sync_to_supabase']
        
        # Start backup operation
        logger.info(f"Admin {request.user.get('user_id', 'unknown')} initiated backup: {backup_name or 'auto-generated'}")
        
        # Run backup asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            backup_result = loop.run_until_complete(backup_manager.perform_full_backup(backup_name))
        finally:
            loop.close()
        
        if backup_result['success']:
            return jsonify(_get_standardized_response(
                success=True,
                data=backup_result['backup_metadata'],
                message=backup_result['message']
            ))
        else:
            return jsonify(_get_standardized_response(
                success=False,
                error=backup_result['error'],
                code="BACKUP_FAILED"
            )), 500
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to create backup",
            code="BACKUP_ERROR"
        )), 500

@backup_bp.route('/list', methods=['GET'])
@require_admin_auth
def list_backups():
    """
    List all backups with optional filtering
    
    Query Parameters:
    - limit: Maximum number of backups to return (default: 50)
    - days: Number of days to look back (default: 30)
    - status: Filter by backup status (verified, failed, etc.)
    """
    try:
        backup_manager = get_backup_health_manager()
        if not backup_manager:
            return jsonify(_get_standardized_response(
                success=False,
                error="Backup manager not initialized",
                code="BACKUP_MANAGER_ERROR"
            )), 500
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 200)
        days = int(request.args.get('days', 30))
        status_filter = request.args.get('status')
        
        # Get backup history
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            backup_history = loop.run_until_complete(backup_manager.get_backup_history(limit))
        finally:
            loop.close()
        
        if not backup_history['success']:
            return jsonify(_get_standardized_response(
                success=False,
                error=backup_history['error'],
                code="BACKUP_HISTORY_ERROR"
            )), 500
        
        # Apply additional filters
        backups = backup_history['backups']
        if status_filter:
            backups = [b for b in backups if b.get('database_health') == status_filter]
        
        # Filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        backups = [b for b in backups if datetime.fromisoformat(b['created_at'].replace('Z', '+00:00')) >= cutoff_date]
        
        return jsonify(_get_standardized_response(
            success=True,
            data={
                'backups': backups,
                'statistics': backup_history['statistics'],
                'filters_applied': {
                    'limit': limit,
                    'days': days,
                    'status': status_filter
                },
                'total_returned': len(backups)
            },
            message=f"Retrieved {len(backups)} backups"
        ))
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to list backups",
            code="BACKUP_LIST_ERROR"
        )), 500

@backup_bp.route('/restore', methods=['POST'])
@require_admin_auth
def restore_backup():
    """
    Restore database from backup
    
    Body:
    {
        "backup_name": "backup_20250803_120000",
        "target_database": "optional_target_db",
        "confirm": true
    }
    """
    try:
        backup_manager = get_backup_health_manager()
        if not backup_manager:
            return jsonify(_get_standardized_response(
                success=False,
                error="Backup manager not initialized",
                code="BACKUP_MANAGER_ERROR"
            )), 500
        
        # Parse request data
        data = request.get_json() or {}
        backup_name = data.get('backup_name')
        target_database = data.get('target_database')
        confirm = data.get('confirm', False)
        
        if not backup_name:
            return jsonify(_get_standardized_response(
                success=False,
                error="backup_name is required",
                code="MISSING_BACKUP_NAME"
            )), 400
        
        if not confirm:
            return jsonify(_get_standardized_response(
                success=False,
                error="Confirmation required for restore operation",
                code="CONFIRMATION_REQUIRED"
            )), 400
        
        logger.warning(f"Admin {request.user.get('user_id', 'unknown')} initiated database restore from backup: {backup_name}")
        
        # Run restore operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            restore_result = loop.run_until_complete(backup_manager.restore_from_backup(backup_name, target_database))
        finally:
            loop.close()
        
        if restore_result['success']:
            return jsonify(_get_standardized_response(
                success=True,
                data=restore_result['restore_metadata'],
                message=restore_result['message']
            ))
        else:
            return jsonify(_get_standardized_response(
                success=False,
                error=restore_result['error'],
                code="RESTORE_FAILED"
            )), 500
        
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to restore backup",
            code="RESTORE_ERROR"
        )), 500

@backup_bp.route('/health', methods=['GET'])
@require_admin_auth
def check_system_health():
    """
    Check comprehensive system health including backup status
    
    Query Parameters:
    - detailed: Include detailed metrics (default: false)
    - force_check: Force new health check instead of cached (default: false)
    """
    try:
        backup_manager = get_backup_health_manager()
        if not backup_manager:
            return jsonify(_get_standardized_response(
                success=False,
                error="Backup manager not initialized",
                code="BACKUP_MANAGER_ERROR"
            )), 500
        
        # Parse query parameters
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        force_check = request.args.get('force_check', 'false').lower() == 'true'
        
        # Use cached result if available and not forcing new check
        if not force_check and backup_manager.last_health_check:
            time_since_check = (datetime.utcnow() - backup_manager.last_health_check).total_seconds() / 60
            if time_since_check < backup_manager.health_config['check_interval_minutes']:
                return jsonify(_get_standardized_response(
                    success=True,
                    data={
                        'status': backup_manager.health_status,
                        'issues': backup_manager.health_issues,
                        'last_check': backup_manager.last_health_check.isoformat(),
                        'cached': True
                    },
                    message="Health status (cached)"
                ))
        
        # Perform new health check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            health_result = loop.run_until_complete(backup_manager.check_database_health())
        finally:
            loop.close()
        
        # Prepare response data
        response_data = {
            'status': health_result['status'],
            'message': health_result['message'],
            'issues': health_result.get('issues', []),
            'checked_at': health_result['checked_at'],
            'duration_ms': health_result.get('duration_ms'),
            'cached': False
        }
        
        # Include detailed metrics if requested
        if detailed:
            response_data['detailed_metrics'] = health_result.get('metrics', {})
        
        return jsonify(_get_standardized_response(
            success=True,
            data=response_data,
            message="Health check completed"
        ))
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to check system health",
            code="HEALTH_CHECK_ERROR"
        )), 500

@backup_bp.route('/health/history', methods=['GET'])
@require_admin_auth
def get_health_history():
    """
    Get system health history
    
    Query Parameters:
    - hours: Number of hours to look back (default: 24)
    - status: Filter by health status (healthy, warning, critical)
    - limit: Maximum number of records (default: 100)
    """
    try:
        # Parse query parameters
        hours = int(request.args.get('hours', 24))
        status_filter = request.args.get('status')
        limit = min(int(request.args.get('limit', 100)), 500)
        
        # Query health history from Railway PostgreSQL
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Build query with optional status filter
                base_query = """
                    SELECT 
                        check_timestamp,
                        health_status,
                        metrics,
                        issues,
                        checked_by,
                        check_duration_ms
                    FROM system_health_logs
                    WHERE check_timestamp >= %s
                """
                params = [cutoff_time]
                
                if status_filter:
                    base_query += " AND health_status = %s"
                    params.append(status_filter)
                
                base_query += " ORDER BY check_timestamp DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(base_query, params)
                
                health_records = []
                for row in cursor.fetchall():
                    record = {
                        'check_timestamp': row[0].isoformat() if row[0] else None,
                        'health_status': row[1],
                        'metrics': json.loads(row[2]) if row[2] else {},
                        'issues': json.loads(row[3]) if row[3] else [],
                        'checked_by': row[4],
                        'check_duration_ms': row[5]
                    }
                    health_records.append(record)
                
                # Get summary statistics
                cursor.execute("""
                    SELECT 
                        health_status,
                        COUNT(*) as count,
                        AVG(check_duration_ms) as avg_duration_ms
                    FROM system_health_logs
                    WHERE check_timestamp >= %s
                    GROUP BY health_status
                    ORDER BY health_status
                """, (cutoff_time,))
                
                status_summary = {}
                for row in cursor.fetchall():
                    status_summary[row[0]] = {
                        'count': row[1],
                        'avg_duration_ms': round(float(row[2] or 0), 2)
                    }
        
        return jsonify(_get_standardized_response(
            success=True,
            data={
                'health_records': health_records,
                'summary': {
                    'total_checks': len(health_records),
                    'time_range_hours': hours,
                    'status_breakdown': status_summary
                },
                'filters_applied': {
                    'hours': hours,
                    'status': status_filter,
                    'limit': limit
                }
            },
            message=f"Retrieved {len(health_records)} health records"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching health history: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to fetch health history",
            code="HEALTH_HISTORY_ERROR"
        )), 500

@backup_bp.route('/alerts', methods=['GET'])
@require_admin_auth
def get_system_alerts():
    """
    Get system alerts and notifications
    
    Query Parameters:
    - severity: Filter by alert severity (info, warning, critical, urgent)
    - resolved: Filter by resolution status (true, false)
    - hours: Number of hours to look back (default: 24)
    - limit: Maximum number of alerts (default: 50)
    """
    try:
        # Parse query parameters
        severity_filter = request.args.get('severity')
        resolved_filter = request.args.get('resolved')
        hours = int(request.args.get('hours', 24))
        limit = min(int(request.args.get('limit', 50)), 200)
        
        # Query alerts from Railway PostgreSQL
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                # Build query with filters
                base_query = """
                    SELECT 
                        id,
                        alert_type,
                        severity,
                        title,
                        message,
                        created_at,
                        resolved_at,
                        resolved_by,
                        auto_resolved,
                        notification_sent,
                        metadata
                    FROM system_alerts
                    WHERE created_at >= %s
                """
                params = [cutoff_time]
                
                if severity_filter:
                    base_query += " AND severity = %s"
                    params.append(severity_filter)
                
                if resolved_filter is not None:
                    if resolved_filter.lower() == 'true':
                        base_query += " AND resolved_at IS NOT NULL"
                    else:
                        base_query += " AND resolved_at IS NULL"
                
                base_query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(base_query, params)
                
                alerts = []
                for row in cursor.fetchall():
                    alert = {
                        'id': str(row[0]),
                        'alert_type': row[1],
                        'severity': row[2],
                        'title': row[3],
                        'message': row[4],
                        'created_at': row[5].isoformat() if row[5] else None,
                        'resolved_at': row[6].isoformat() if row[6] else None,
                        'resolved_by': row[7],
                        'auto_resolved': row[8],
                        'notification_sent': row[9],
                        'metadata': json.loads(row[10]) if row[10] else {},
                        'is_resolved': row[6] is not None,
                        'age_hours': (datetime.utcnow() - row[5].replace(tzinfo=None)).total_seconds() / 3600 if row[5] else None
                    }
                    alerts.append(alert)
                
                # Get alert statistics
                cursor.execute("""
                    SELECT 
                        severity,
                        COUNT(*) as total_count,
                        COUNT(*) FILTER (WHERE resolved_at IS NULL) as unresolved_count
                    FROM system_alerts
                    WHERE created_at >= %s
                    GROUP BY severity
                    ORDER BY 
                        CASE severity 
                            WHEN 'urgent' THEN 1
                            WHEN 'critical' THEN 2
                            WHEN 'warning' THEN 3
                            WHEN 'info' THEN 4
                            ELSE 5
                        END
                """, (cutoff_time,))
                
                severity_stats = {}
                for row in cursor.fetchall():
                    severity_stats[row[0]] = {
                        'total': row[1],
                        'unresolved': row[2]
                    }
        
        return jsonify(_get_standardized_response(
            success=True,
            data={
                'alerts': alerts,
                'summary': {
                    'total_alerts': len(alerts),
                    'severity_breakdown': severity_stats,
                    'unresolved_count': sum(alert['is_resolved'] == False for alert in alerts)
                },
                'filters_applied': {
                    'severity': severity_filter,
                    'resolved': resolved_filter,
                    'hours': hours,
                    'limit': limit
                }
            },
            message=f"Retrieved {len(alerts)} alerts"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching system alerts: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to fetch system alerts",
            code="ALERTS_ERROR"
        )), 500

@backup_bp.route('/alerts/<alert_id>/resolve', methods=['POST'])
@require_admin_auth
def resolve_alert(alert_id: str):
    """
    Resolve a system alert
    
    Body:
    {
        "resolution_notes": "Optional resolution notes"
    }
    """
    try:
        # Parse request data
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes', '')
        
        # Update alert in Railway PostgreSQL
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE system_alerts 
                    SET 
                        resolved_at = NOW(),
                        resolved_by = %s,
                        resolution_notes = %s
                    WHERE id = %s AND resolved_at IS NULL
                    RETURNING alert_type, title, created_at
                """, (
                    request.user.get('user_id', 'unknown'),
                    resolution_notes,
                    alert_id
                ))
                
                result = cursor.fetchone()
                if not result:
                    return jsonify(_get_standardized_response(
                        success=False,
                        error="Alert not found or already resolved",
                        code="ALERT_NOT_FOUND"
                    )), 404
                
                conn.commit()
                
                alert_info = {
                    'alert_type': result[0],
                    'title': result[1],
                    'created_at': result[2].isoformat() if result[2] else None,
                    'resolved_by': request.user.get('user_id'),
                    'resolution_notes': resolution_notes
                }
        
        logger.info(f"Admin {request.user.get('user_id', 'unknown')} resolved alert {alert_id}: {alert_info['title']}")
        
        return jsonify(_get_standardized_response(
            success=True,
            data=alert_info,
            message="Alert resolved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to resolve alert",
            code="ALERT_RESOLVE_ERROR"
        )), 500

@backup_bp.route('/config', methods=['GET'])
@require_admin_auth
def get_backup_config():
    """Get current backup configuration"""
    try:
        backup_manager = get_backup_health_manager()
        if not backup_manager:
            return jsonify(_get_standardized_response(
                success=False,
                error="Backup manager not initialized",
                code="BACKUP_MANAGER_ERROR"
            )), 500
        
        # Get current configuration
        config_data = {
            'backup_config': backup_manager.backup_config,
            'health_config': backup_manager.health_config,
            'current_status': {
                'last_health_check': backup_manager.last_health_check.isoformat() if backup_manager.last_health_check else None,
                'health_status': backup_manager.health_status,
                'active_issues': len(backup_manager.health_issues)
            }
        }
        
        return jsonify(_get_standardized_response(
            success=True,
            data=config_data,
            message="Backup configuration retrieved"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching backup config: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to fetch backup configuration",
            code="CONFIG_ERROR"
        )), 500

@backup_bp.route('/config', methods=['PUT'])
@require_admin_auth
def update_backup_config():
    """
    Update backup configuration
    
    Body:
    {
        "backup_config": {
            "backup_retention_days": 30,
            "enable_compression": true,
            ...
        },
        "health_config": {
            "check_interval_minutes": 15,
            ...
        }
    }
    """
    try:
        backup_manager = get_backup_health_manager()
        if not backup_manager:
            return jsonify(_get_standardized_response(
                success=False,
                error="Backup manager not initialized",
                code="BACKUP_MANAGER_ERROR"
            )), 500
        
        # Parse request data
        data = request.get_json() or {}
        backup_config_updates = data.get('backup_config', {})
        health_config_updates = data.get('health_config', {})
        
        # Update configurations
        if backup_config_updates:
            backup_manager.backup_config.update(backup_config_updates)
        
        if health_config_updates:
            backup_manager.health_config.update(health_config_updates)
        
        # Save configuration to database
        config_data = {
            'backup_config': backup_manager.backup_config,
            'health_config': backup_manager.health_config,
            'updated_by': request.user.get('user_id', 'unknown'),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        with railway_db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE backup_configurations 
                    SET 
                        config_data = %s,
                        updated_at = NOW()
                    WHERE is_active = true
                """, (json.dumps(config_data),))
                conn.commit()
        
        logger.info(f"Admin {request.user.get('user_id', 'unknown')} updated backup configuration")
        
        return jsonify(_get_standardized_response(
            success=True,
            data=config_data,
            message="Backup configuration updated successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error updating backup config: {e}")
        return jsonify(_get_standardized_response(
            success=False,
            error="Failed to update backup configuration",
            code="CONFIG_UPDATE_ERROR"
        )), 500

# Initialize backup routes
def init_backup_routes(app):
    """Initialize backup management routes"""
    app.register_blueprint(backup_bp)
    logger.info("Backup management routes initialized successfully")
    return backup_bp
