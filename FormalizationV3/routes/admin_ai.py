#!/usr/bin/env python3
"""
Admin AI Configuration Routes
Allows admin to configure AI models per user
"""

import logging
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import json

# Import unified AI processor
from utils.unified_ai_processor import get_unified_processor, AIProvider

logger = logging.getLogger(__name__)

# Create blueprint
admin_ai_bp = Blueprint('admin_ai', __name__, url_prefix='/api/admin/ai')

# Global variables for dependencies (will be injected)
railway_db = None
auth_middleware = None

def init_admin_ai_routes(railway_database, auth_mid):
    """Initialize admin AI routes with required dependencies."""
    global railway_db, auth_middleware
    railway_db = railway_database
    auth_middleware = auth_mid
    logger.info("Admin AI configuration routes initialized")

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get current user from auth middleware
            user = auth_middleware.get_current_user(request)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Check if user is admin
            if user.get('access_type') != 'admin':
                return jsonify({
                    'success': False,
                    'error': 'Admin access required',
                    'code': 'ADMIN_REQUIRED'
                }), 403
            
            # Add user to request context
            request.admin_user = user
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Admin auth error: {e}")
            return jsonify({
                'success': False,
                'error': 'Authentication error',
                'code': 'AUTH_ERROR'
            }), 500
    
    return decorated_function

@admin_ai_bp.route('/providers', methods=['GET'])
@require_admin_auth
def get_available_providers():
    """Get list of available AI providers and their status"""
    try:
        unified_processor = get_unified_processor(railway_db)
        providers = unified_processor.get_available_providers()
        
        return jsonify({
            'success': True,
            'data': {
                'providers': providers,
                'total_providers': len(providers)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI providers: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get AI providers',
            'code': 'PROVIDER_ERROR'
        }), 500

@admin_ai_bp.route('/users/<user_id>/provider', methods=['GET'])
@require_admin_auth
def get_user_ai_provider(user_id):
    """Get AI provider configuration for a specific user"""
    try:
        # Verify user exists
        user_data = railway_db.execute_read(
            "SELECT id, email, full_name FROM user_profiles WHERE id = %s",
            (user_id,)
        )
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        user = user_data[0]
        
        # Get user's AI configuration
        ai_settings = railway_db.execute_read("""
            SELECT ai_provider, ai_model, set_by_admin, admin_user_id, 
                   enabled, created_at, updated_at
            FROM user_ai_settings 
            WHERE user_id = %s
        """, (user_id,))
        
        # Get AI processing statistics
        processing_stats = railway_db.execute_read("""
            SELECT 
                ai_provider,
                COUNT(*) as total_requests,
                AVG(processing_time_ms) as avg_processing_time,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
                MAX(created_at) as last_used
            FROM ai_processing_logs 
            WHERE user_id = %s 
            GROUP BY ai_provider
            ORDER BY last_used DESC
        """, (user_id,))
        
        if ai_settings:
            config = ai_settings[0]
            
            # Get admin who set the configuration
            admin_info = None
            if config['admin_user_id']:
                admin_data = railway_db.execute_read(
                    "SELECT email, full_name FROM user_profiles WHERE id = %s",
                    (config['admin_user_id'],)
                )
                if admin_data:
                    admin_info = {
                        'id': config['admin_user_id'],
                        'email': admin_data[0]['email'],
                        'name': admin_data[0]['full_name']
                    }
            
            return jsonify({
                'success': True,
                'data': {
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'name': user['full_name']
                    },
                    'ai_configuration': {
                        'provider': config['ai_provider'],
                        'model': config['ai_model'],
                        'set_by_admin': config['set_by_admin'],
                        'admin_info': admin_info,
                        'enabled': config['enabled'],
                        'created_at': config['created_at'].isoformat() if config['created_at'] else None,
                        'updated_at': config['updated_at'].isoformat() if config['updated_at'] else None
                    },
                    'usage_statistics': [
                        {
                            'provider': stat['ai_provider'],
                            'total_requests': stat['total_requests'],
                            'avg_processing_time_ms': round(stat['avg_processing_time'], 2) if stat['avg_processing_time'] else 0,
                            'success_rate': round((stat['successful_requests'] / stat['total_requests']) * 100, 2) if stat['total_requests'] > 0 else 0,
                            'last_used': stat['last_used'].isoformat() if stat['last_used'] else None
                        }
                        for stat in processing_stats
                    ]
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            # User has default configuration
            return jsonify({
                'success': True,
                'data': {
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'name': user['full_name']
                    },
                    'ai_configuration': {
                        'provider': 'ollama',
                        'model': 'llama3.1:8b',
                        'set_by_admin': False,
                        'admin_info': None,
                        'enabled': True,
                        'created_at': None,
                        'updated_at': None
                    },
                    'usage_statistics': [
                        {
                            'provider': stat['ai_provider'],
                            'total_requests': stat['total_requests'],
                            'avg_processing_time_ms': round(stat['avg_processing_time'], 2) if stat['avg_processing_time'] else 0,
                            'success_rate': round((stat['successful_requests'] / stat['total_requests']) * 100, 2) if stat['total_requests'] > 0 else 0,
                            'last_used': stat['last_used'].isoformat() if stat['last_used'] else None
                        }
                        for stat in processing_stats
                    ]
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Error getting user AI provider for {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get user AI configuration',
            'code': 'CONFIG_ERROR'
        }), 500

@admin_ai_bp.route('/users/<user_id>/provider', methods=['PUT'])
@require_admin_auth
def set_user_ai_provider(user_id):
    """Set AI provider configuration for a specific user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request data required',
                'code': 'DATA_REQUIRED'
            }), 400
        
        provider_name = data.get('provider')
        model = data.get('model')
        
        if not provider_name:
            return jsonify({
                'success': False,
                'error': 'AI provider is required',
                'code': 'PROVIDER_REQUIRED'
            }), 400
        
        # Validate provider
        try:
            provider = AIProvider(provider_name)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid AI provider: {provider_name}',
                'code': 'INVALID_PROVIDER'
            }), 400
        
        # Verify user exists
        user_data = railway_db.execute_read(
            "SELECT id, email, full_name FROM user_profiles WHERE id = %s",
            (user_id,)
        )
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        user = user_data[0]
        admin_user_id = request.admin_user['id']
        
        # Set AI provider using unified processor
        unified_processor = get_unified_processor(railway_db)
        success = unified_processor.set_user_ai_provider(
            user_id=user_id,
            provider=provider,
            model=model,
            admin_user_id=admin_user_id
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to set AI provider',
                'code': 'SET_FAILED'
            }), 500
        
        # Log admin action
        try:
            railway_db.execute_write("""
                INSERT INTO activity_logs (user_id, action, details, metadata, created_at)
                VALUES (%s, 'admin_set_ai_provider', %s, %s, NOW())
            """, (
                admin_user_id,
                json.dumps({
                    'target_user_id': user_id,
                    'target_user_email': user['email'],
                    'ai_provider': provider_name,
                    'ai_model': model
                }),
                json.dumps({
                    'admin_action': True,
                    'target_user': True,
                    'ai_configuration': True
                })
            ))
        except Exception as log_error:
            logger.warning(f"Failed to log admin AI configuration change: {log_error}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['full_name']
                },
                'ai_configuration': {
                    'provider': provider_name,
                    'model': model,
                    'set_by_admin': True,
                    'admin_user_id': admin_user_id,
                    'updated_at': datetime.utcnow().isoformat()
                }
            },
            'message': f'AI provider set to {provider_name} for user {user["email"]}',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error setting user AI provider for {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to set AI provider',
            'code': 'SET_ERROR'
        }), 500

@admin_ai_bp.route('/users', methods=['GET'])
@require_admin_auth
def list_users_with_ai_config():
    """List all users with their AI configuration"""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search', '').strip()
        provider_filter = request.args.get('provider', '').strip()
        
        # Build query with filters
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(up.email ILIKE %s OR up.full_name ILIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        if provider_filter:
            where_conditions.append("uas.ai_provider = %s")
            params.append(provider_filter)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT up.id)
            FROM user_profiles up
            LEFT JOIN user_ai_settings uas ON up.id = uas.user_id
            {where_clause}
        """
        
        total_count = railway_db.execute_read(count_query, params)[0]['count']
        
        # Get users with AI configuration
        offset = (page - 1) * per_page
        users_query = f"""
            SELECT 
                up.id,
                up.email,
                up.full_name,
                up.access_type,
                up.created_at as user_created_at,
                uas.ai_provider,
                uas.ai_model,
                uas.set_by_admin,
                uas.enabled as ai_enabled,
                uas.updated_at as ai_updated_at,
                admin.email as admin_email,
                admin.full_name as admin_name
            FROM user_profiles up
            LEFT JOIN user_ai_settings uas ON up.id = uas.user_id
            LEFT JOIN user_profiles admin ON uas.admin_user_id = admin.id
            {where_clause}
            ORDER BY up.created_at DESC
            LIMIT %s OFFSET %s
        """
        
        params.extend([per_page, offset])
        users_data = railway_db.execute_read(users_query, params)
        
        # Format response
        users = []
        for user in users_data:
            users.append({
                'id': user['id'],
                'email': user['email'],
                'name': user['full_name'],
                'access_type': user['access_type'],
                'created_at': user['user_created_at'].isoformat() if user['user_created_at'] else None,
                'ai_configuration': {
                    'provider': user['ai_provider'] or 'ollama',
                    'model': user['ai_model'] or 'llama3.1:8b',
                    'set_by_admin': user['set_by_admin'] or False,
                    'enabled': user['ai_enabled'] if user['ai_enabled'] is not None else True,
                    'updated_at': user['ai_updated_at'].isoformat() if user['ai_updated_at'] else None,
                    'admin_info': {
                        'email': user['admin_email'],
                        'name': user['admin_name']
                    } if user['admin_email'] else None
                }
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users': users,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                },
                'filters': {
                    'search': search,
                    'provider': provider_filter
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error listing users with AI config: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list users',
            'code': 'LIST_ERROR'
        }), 500

@admin_ai_bp.route('/statistics', methods=['GET'])
@require_admin_auth
def get_ai_usage_statistics():
    """Get overall AI usage statistics across all users"""
    try:
        # Get provider usage statistics
        provider_stats = railway_db.execute_read("""
            SELECT 
                ai_provider,
                COUNT(*) as total_requests,
                AVG(processing_time_ms) as avg_processing_time,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
                SUM(tokens_used) as total_tokens,
                SUM(cost_estimate) as total_cost
            FROM ai_processing_logs 
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY ai_provider
            ORDER BY total_requests DESC
        """)
        
        # Get user adoption statistics
        user_stats = railway_db.execute_read("""
            SELECT 
                uas.ai_provider,
                COUNT(DISTINCT uas.user_id) as user_count
            FROM user_ai_settings uas
            WHERE uas.enabled = true
            GROUP BY uas.ai_provider
            
            UNION ALL
            
            SELECT 
                'ollama' as ai_provider,
                COUNT(*) as user_count
            FROM user_profiles up
            WHERE up.id NOT IN (SELECT user_id FROM user_ai_settings WHERE enabled = true)
        """)
        
        # Get recent AI configuration changes
        recent_changes = railway_db.execute_read("""
            SELECT 
                uas.user_id,
                up.email,
                up.full_name,
                uas.ai_provider,
                uas.ai_model,
                uas.updated_at,
                admin.email as admin_email
            FROM user_ai_settings uas
            JOIN user_profiles up ON uas.user_id = up.id
            LEFT JOIN user_profiles admin ON uas.admin_user_id = admin.id
            WHERE uas.updated_at >= NOW() - INTERVAL '7 days'
            ORDER BY uas.updated_at DESC
            LIMIT 10
        """)
        
        return jsonify({
            'success': True,
            'data': {
                'provider_usage': [
                    {
                        'provider': stat['ai_provider'],
                        'total_requests': stat['total_requests'],
                        'avg_processing_time_ms': round(stat['avg_processing_time'], 2) if stat['avg_processing_time'] else 0,
                        'success_rate': round((stat['successful_requests'] / stat['total_requests']) * 100, 2) if stat['total_requests'] > 0 else 0,
                        'total_tokens': stat['total_tokens'] or 0,
                        'total_cost': float(stat['total_cost']) if stat['total_cost'] else 0.0
                    }
                    for stat in provider_stats
                ],
                'user_adoption': [
                    {
                        'provider': stat['ai_provider'],
                        'user_count': stat['user_count']
                    }
                    for stat in user_stats
                ],
                'recent_changes': [
                    {
                        'user_id': change['user_id'],
                        'user_email': change['email'],
                        'user_name': change['full_name'],
                        'provider': change['ai_provider'],
                        'model': change['ai_model'],
                        'updated_at': change['updated_at'].isoformat() if change['updated_at'] else None,
                        'admin_email': change['admin_email']
                    }
                    for change in recent_changes
                ]
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI usage statistics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get AI statistics',
            'code': 'STATS_ERROR'
        }), 500
