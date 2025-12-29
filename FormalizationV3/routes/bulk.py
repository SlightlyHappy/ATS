#!/usr/bin/env python3
"""
Bulk Operations Routes for HR ATS System
Provides API endpoints for bulk processing operations
"""

from flask import Blueprint, request, jsonify, current_app
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import base64
import tempfile

from utils.bulk_operations import (
    bulk_manager, submit_bulk_resume_upload, submit_bulk_resume_analysis,
    submit_bulk_user_creation, submit_bulk_email_send
)
from utils.response_formatter import EnhancedResponseFormatter
from auth_middleware import require_auth, get_current_user, require_admin
from utils.realtime_manager import emit_resume_processing_update

logger = logging.getLogger(__name__)

# Create blueprint
bulk_bp = Blueprint('bulk', __name__, url_prefix='/api/v1/bulk')

# Initialize response formatter
response_formatter = EnhancedResponseFormatter()

# Global references for dependency injection (set by init_bulk_routes)
database_manager = None
realtime_manager_instance = None
auth_middleware_global = None

@bulk_bp.route('/operations', methods=['GET'])
@require_auth
def list_bulk_operations():
    """List bulk operations for current user"""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        operation_type_filter = request.args.get('operation_type')
        
        # Get user's operations
        user_operations = []
        for operation_id, operation in bulk_manager.operations.items():
            # Admin can see all operations, users can only see their own
            if user.get('is_admin') or operation.user_id == user['id']:
                operation_data = bulk_manager.get_operation_status(operation_id)
                
                # Apply filters
                if status_filter and operation_data['status'] != status_filter:
                    continue
                if operation_type_filter and operation_data['operation_type'] != operation_type_filter:
                    continue
                
                user_operations.append(operation_data)
        
        # Sort by creation date (newest first)
        user_operations.sort(
            key=lambda x: x['timing']['created_at'] or '',
            reverse=True
        )
        
        # Paginate
        total_operations = len(user_operations)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_operations = user_operations[start_idx:end_idx]
        
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total': total_operations,
            'pages': (total_operations + per_page - 1) // per_page,
            'has_next': end_idx < total_operations,
            'has_prev': page > 1
        }
        
        return response_formatter.success(
            data={
                'operations': paginated_operations,
                'pagination': pagination_info,
                'filters': {
                    'status': status_filter,
                    'operation_type': operation_type_filter
                }
            },
            message=f"Retrieved {len(paginated_operations)} operations"
        )
        
    except Exception as e:
        logger.error(f"Error listing bulk operations: {e}")
        return response_formatter.error(
            message="Failed to retrieve bulk operations",
            error_code="BULK_LIST_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/operations/<operation_id>', methods=['GET'])
@require_auth
def get_bulk_operation(operation_id: str):
    """Get specific bulk operation status"""
    try:
        user = get_current_user()
        
        # Check if operation exists
        if operation_id not in bulk_manager.operations:
            return response_formatter.error(
                message="Operation not found",
                error_code="OPERATION_NOT_FOUND"
            ), 404
        
        operation = bulk_manager.operations[operation_id]
        
        # Check permissions
        if not user.get('is_admin') and operation.user_id != user['id']:
            return response_formatter.error(
                message="Access denied",
                error_code="ACCESS_DENIED"
            ), 403
        
        # Get operation status
        operation_data = bulk_manager.get_operation_status(operation_id)
        
        return response_formatter.success(
            data=operation_data,
            message="Operation details retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting bulk operation {operation_id}: {e}")
        return response_formatter.error(
            message="Failed to retrieve operation details",
            error_code="BULK_GET_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/operations/<operation_id>/results', methods=['GET'])
@require_auth
def get_bulk_operation_results(operation_id: str):
    """Get bulk operation results"""
    try:
        user = get_current_user()
        offset = request.args.get('offset', 0, type=int)
        limit = min(request.args.get('limit', 100, type=int), 500)
        
        # Check if operation exists
        if operation_id not in bulk_manager.operations:
            return response_formatter.error(
                message="Operation not found",
                error_code="OPERATION_NOT_FOUND"
            ), 404
        
        operation = bulk_manager.operations[operation_id]
        
        # Check permissions
        if not user.get('is_admin') and operation.user_id != user['id']:
            return response_formatter.error(
                message="Access denied",
                error_code="ACCESS_DENIED"
            ), 403
        
        # Get operation results
        results_data = bulk_manager.get_operation_results(operation_id, offset, limit)
        
        if not results_data:
            return response_formatter.error(
                message="Results not available",
                error_code="RESULTS_NOT_AVAILABLE"
            ), 404
        
        return response_formatter.success(
            data=results_data,
            message="Operation results retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting bulk operation results {operation_id}: {e}")
        return response_formatter.error(
            message="Failed to retrieve operation results",
            error_code="BULK_RESULTS_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/operations/<operation_id>/cancel', methods=['POST'])
@require_auth
def cancel_bulk_operation(operation_id: str):
    """Cancel a bulk operation"""
    try:
        user = get_current_user()
        
        # Check if operation exists
        if operation_id not in bulk_manager.operations:
            return response_formatter.error(
                message="Operation not found",
                error_code="OPERATION_NOT_FOUND"
            ), 404
        
        operation = bulk_manager.operations[operation_id]
        
        # Check permissions
        if not user.get('is_admin') and operation.user_id != user['id']:
            return response_formatter.error(
                message="Access denied",
                error_code="ACCESS_DENIED"
            ), 403
        
        # Cancel operation
        success = bulk_manager.cancel_operation(operation_id)
        
        if success:
            return response_formatter.success(
                message="Operation cancelled successfully"
            )
        else:
            return response_formatter.error(
                message="Operation cannot be cancelled",
                error_code="CANCEL_FAILED",
                details={'reason': 'Operation may already be completed or failed'}
            ), 400
        
    except Exception as e:
        logger.error(f"Error cancelling bulk operation {operation_id}: {e}")
        return response_formatter.error(
            message="Failed to cancel operation",
            error_code="BULK_CANCEL_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/resume-upload', methods=['POST'])
@require_auth
def bulk_resume_upload():
    """Submit bulk resume upload operation"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        files_data = data.get('files', [])
        if not files_data:
            return response_formatter.error(
                message="No files provided",
                error_code="NO_FILES_PROVIDED"
            ), 400
        
        if len(files_data) > 50:  # Limit bulk operations
            return response_formatter.error(
                message="Too many files. Maximum 50 files per batch",
                error_code="TOO_MANY_FILES"
            ), 400
        
        # Process file data
        processed_files = []
        for i, file_data in enumerate(files_data):
            filename = file_data.get('filename')
            file_content = file_data.get('content')  # Base64 encoded
            
            if not filename or not file_content:
                return response_formatter.error(
                    message=f"Invalid file data at index {i}",
                    error_code="INVALID_FILE_DATA"
                ), 400
            
            try:
                # Decode base64 content
                file_bytes = base64.b64decode(file_content)
                processed_files.append({
                    'filename': filename,
                    'file_data': file_bytes
                })
            except Exception as e:
                return response_formatter.error(
                    message=f"Invalid file content at index {i}: {str(e)}",
                    error_code="INVALID_FILE_CONTENT"
                ), 400
        
        # Submit bulk operation
        operation_id = submit_bulk_resume_upload(user['id'], processed_files)
        
        return response_formatter.success(
            data={
                'operation_id': operation_id,
                'total_files': len(processed_files),
                'status': 'submitted'
            },
            message="Bulk resume upload submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in bulk resume upload: {e}")
        return response_formatter.error(
            message="Failed to submit bulk resume upload",
            error_code="BULK_UPLOAD_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/resume-analysis', methods=['POST'])
@require_auth
def bulk_resume_analysis():
    """Submit bulk resume analysis operation"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        resume_ids = data.get('resume_ids', [])
        if not resume_ids:
            return response_formatter.error(
                message="No resume IDs provided",
                error_code="NO_RESUME_IDS"
            ), 400
        
        if len(resume_ids) > 20:  # Limit for analysis operations
            return response_formatter.error(
                message="Too many resumes. Maximum 20 resumes per batch",
                error_code="TOO_MANY_RESUMES"
            ), 400
        
        # Validate resume IDs and ownership
        from railway_database import RailwayDatabase
        db = RailwayDatabase()
        
        # Check if user owns all resumes (unless admin)
        if not user.get('is_admin'):
            owned_resumes = db.execute_read(
                "SELECT id FROM resumes WHERE id = ANY(%s) AND user_id = %s",
                (resume_ids, user['id'])
            )
            owned_ids = {str(r['id']) for r in owned_resumes}
            
            invalid_ids = set(resume_ids) - owned_ids
            if invalid_ids:
                return response_formatter.error(
                    message="Invalid or unauthorized resume IDs",
                    error_code="UNAUTHORIZED_RESUMES",
                    details={'invalid_ids': list(invalid_ids)}
                ), 403
        
        # Submit bulk operation
        operation_id = submit_bulk_resume_analysis(user['id'], resume_ids)
        
        return response_formatter.success(
            data={
                'operation_id': operation_id,
                'total_resumes': len(resume_ids),
                'status': 'submitted'
            },
            message="Bulk resume analysis submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in bulk resume analysis: {e}")
        return response_formatter.error(
            message="Failed to submit bulk resume analysis",
            error_code="BULK_ANALYSIS_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/user-creation', methods=['POST'])
@require_admin
def bulk_user_creation():
    """Submit bulk user creation operation (admin only)"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        users_data = data.get('users', [])
        if not users_data:
            return response_formatter.error(
                message="No user data provided",
                error_code="NO_USER_DATA"
            ), 400
        
        if len(users_data) > 100:  # Limit for user creation
            return response_formatter.error(
                message="Too many users. Maximum 100 users per batch",
                error_code="TOO_MANY_USERS"
            ), 400
        
        # Validate user data
        required_fields = ['email', 'password']
        for i, user_data in enumerate(users_data):
            for field in required_fields:
                if field not in user_data:
                    return response_formatter.error(
                        message=f"Missing {field} in user data at index {i}",
                        error_code="MISSING_USER_FIELD"
                    ), 400
        
        # Submit bulk operation
        operation_id = submit_bulk_user_creation(user['id'], users_data)
        
        return response_formatter.success(
            data={
                'operation_id': operation_id,
                'total_users': len(users_data),
                'status': 'submitted'
            },
            message="Bulk user creation submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in bulk user creation: {e}")
        return response_formatter.error(
            message="Failed to submit bulk user creation",
            error_code="BULK_USER_CREATION_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/email-send', methods=['POST'])
@require_auth
def bulk_email_send():
    """Submit bulk email sending operation"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        recipients = data.get('recipients', [])
        template = data.get('template')
        subject = data.get('subject')
        
        if not recipients:
            return response_formatter.error(
                message="No recipients provided",
                error_code="NO_RECIPIENTS"
            ), 400
        
        if not template or not subject:
            return response_formatter.error(
                message="Template and subject are required",
                error_code="MISSING_EMAIL_DATA"
            ), 400
        
        if len(recipients) > 200:  # Limit for email operations
            return response_formatter.error(
                message="Too many recipients. Maximum 200 recipients per batch",
                error_code="TOO_MANY_RECIPIENTS"
            ), 400
        
        # Validate recipients
        for i, recipient in enumerate(recipients):
            if 'email' not in recipient:
                return response_formatter.error(
                    message=f"Missing email in recipient data at index {i}",
                    error_code="MISSING_RECIPIENT_EMAIL"
                ), 400
        
        # Submit bulk operation
        operation_id = submit_bulk_email_send(user['id'], recipients, template, subject)
        
        return response_formatter.success(
            data={
                'operation_id': operation_id,
                'total_recipients': len(recipients),
                'template': template,
                'subject': subject,
                'status': 'submitted'
            },
            message="Bulk email sending submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in bulk email send: {e}")
        return response_formatter.error(
            message="Failed to submit bulk email sending",
            error_code="BULK_EMAIL_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/data-export', methods=['POST'])
@require_auth
def bulk_data_export():
    """Submit bulk data export operation"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        table_name = data.get('table_name')
        export_type = data.get('export_type', 'csv')
        filters = data.get('filters', {})
        
        if not table_name:
            return response_formatter.error(
                message="Table name is required",
                error_code="MISSING_TABLE_NAME"
            ), 400
        
        # Validate table access (security check)
        allowed_tables = ['resumes', 'users', 'job_postings', 'applications']
        if not user.get('is_admin'):
            allowed_tables = ['resumes']  # Regular users can only export their resumes
            # Add user filter for non-admin users
            filters['user_id'] = user['id']
        
        if table_name not in allowed_tables:
            return response_formatter.error(
                message="Access denied to this table",
                error_code="TABLE_ACCESS_DENIED"
            ), 403
        
        if export_type not in ['csv', 'json']:
            return response_formatter.error(
                message="Invalid export type. Use 'csv' or 'json'",
                error_code="INVALID_EXPORT_TYPE"
            ), 400
        
        # Submit bulk operation
        items = [{}]  # Single item for export operation
        parameters = {
            'export_type': export_type,
            'table_name': table_name,
            'filters': filters
        }
        
        operation_id = bulk_manager.submit_operation(
            'bulk_data_export',
            user['id'],
            items,
            parameters
        )
        
        return response_formatter.success(
            data={
                'operation_id': operation_id,
                'table_name': table_name,
                'export_type': export_type,
                'filters': filters,
                'status': 'submitted'
            },
            message="Bulk data export submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in bulk data export: {e}")
        return response_formatter.error(
            message="Failed to submit bulk data export",
            error_code="BULK_EXPORT_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/performance', methods=['GET'])
@require_auth
def get_bulk_performance():
    """Get bulk operations performance statistics"""
    try:
        user = get_current_user()
        
        # Only admins can see full performance stats
        if not user.get('is_admin'):
            return response_formatter.error(
                message="Admin access required",
                error_code="ADMIN_REQUIRED"
            ), 403
        
        stats = bulk_manager.get_performance_stats()
        
        return response_formatter.success(
            data=stats,
            message="Performance statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting bulk performance: {e}")
        return response_formatter.error(
            message="Failed to retrieve performance statistics",
            error_code="BULK_PERFORMANCE_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/cleanup', methods=['POST'])
@require_admin
def cleanup_old_operations():
    """Clean up old bulk operations (admin only)"""
    try:
        user = get_current_user()
        data = request.get_json() or {}
        
        days_old = data.get('days_old', 7)
        if days_old < 1:
            return response_formatter.error(
                message="days_old must be at least 1",
                error_code="INVALID_DAYS_OLD"
            ), 400
        
        cleaned_count = bulk_manager.cleanup_old_operations(days_old)
        
        return response_formatter.success(
            data={
                'cleaned_operations': cleaned_count,
                'days_old': days_old
            },
            message=f"Cleaned up {cleaned_count} old operations"
        )
        
    except Exception as e:
        logger.error(f"Error cleaning up operations: {e}")
        return response_formatter.error(
            message="Failed to clean up operations",
            error_code="BULK_CLEANUP_ERROR",
            details={'error': str(e)}
        ), 500

@bulk_bp.route('/templates', methods=['GET'])
@require_auth
def get_bulk_templates():
    """Get bulk operation templates and examples"""
    try:
        templates = {
            'bulk_resume_upload': {
                'description': 'Upload multiple resume files',
                'example': {
                    'files': [
                        {
                            'filename': 'resume1.pdf',
                            'content': 'base64_encoded_file_content'
                        }
                    ]
                },
                'max_items': 50,
                'required_fields': ['filename', 'content']
            },
            'bulk_resume_analysis': {
                'description': 'Analyze multiple resumes',
                'example': {
                    'resume_ids': ['123', '456', '789']
                },
                'max_items': 20,
                'required_fields': ['resume_ids']
            },
            'bulk_user_creation': {
                'description': 'Create multiple user accounts (admin only)',
                'example': {
                    'users': [
                        {
                            'email': 'user@example.com',
                            'password': 'secure_password',
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'role': 'user'
                        }
                    ]
                },
                'max_items': 100,
                'required_fields': ['email', 'password'],
                'admin_only': True
            },
            'bulk_email_send': {
                'description': 'Send emails to multiple recipients',
                'example': {
                    'recipients': [
                        {
                            'email': 'recipient@example.com',
                            'template_vars': {'name': 'John'}
                        }
                    ],
                    'template': 'welcome_email',
                    'subject': 'Welcome to our platform'
                },
                'max_items': 200,
                'required_fields': ['recipients', 'template', 'subject']
            },
            'bulk_data_export': {
                'description': 'Export data from database tables',
                'example': {
                    'table_name': 'resumes',
                    'export_type': 'csv',
                    'filters': {'status': 'active'}
                },
                'max_items': 1,
                'required_fields': ['table_name'],
                'export_types': ['csv', 'json']
            }
        }
        
        return response_formatter.success(
            data=templates,
            message="Bulk operation templates retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting bulk templates: {e}")
        return response_formatter.error(
            message="Failed to retrieve templates",
            error_code="BULK_TEMPLATES_ERROR",
            details={'error': str(e)}
        ), 500


def init_bulk_routes(bulk_manager_instance=None, db_manager=None, realtime_manager=None, auth_middleware=None):
    """Initialize bulk routes with dependencies"""
    global bulk_manager, database_manager, realtime_manager_instance, auth_middleware_global
    
    # Store global references for route handlers
    if bulk_manager_instance:
        bulk_manager = bulk_manager_instance
        logger.info("✅ Bulk routes initialized with bulk manager")
    
    if db_manager:
        database_manager = db_manager
        logger.info("✅ Bulk routes initialized with database manager")
    
    if realtime_manager:
        realtime_manager_instance = realtime_manager
        logger.info("✅ Bulk routes initialized with realtime manager")
    
    if auth_middleware:
        auth_middleware_global = auth_middleware
        logger.info("✅ Bulk routes initialized with auth middleware")
    else:
        logger.warning("⚠️ No auth middleware provided - bulk operations may have limited functionality")
    
    logger.info("✅ Bulk routes initialization completed successfully")
    return bulk_bp
