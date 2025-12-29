"""
SocketIO real-time routes - extracted from monolithic app.py
Handles: WebSocket connections, real-time updates, live notifications, status broadcasts
"""

import os
import json
import logging
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect

logger = logging.getLogger(__name__)

# Global dependencies (will be injected during initialization)
auth_middleware = None
db_manager = None
railway_db = None
socketio = None

# Active connections tracking
active_connections = {}
user_rooms = {}

def init_socketio_routes(socketio_instance, auth_mid, database_manager=None, railway_database=None):
    """Initialize SocketIO routes with dependencies"""
    global socketio, auth_middleware, db_manager, railway_db
    
    socketio = socketio_instance
    auth_middleware = auth_mid
    db_manager = database_manager
    railway_db = railway_database
    
    # Register SocketIO event handlers
    register_socketio_handlers()
    
    logger.info("✅ SocketIO routes initialized with real-time capabilities")

def register_socketio_handlers():
    """Register all SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth_data=None):
        """Handle client connection"""
        try:
            logger.info(f"🔌 Client connecting from {request.remote_addr}")
            
            # Get session token from auth data or query params
            session_token = None
            if auth_data and isinstance(auth_data, dict):
                session_token = auth_data.get('token')
            else:
                # Try to get from query parameters
                session_token = request.args.get('token')
            
            if not session_token:
                logger.warning("SocketIO connection rejected: No session token")
                disconnect()
                return False
            
            # Validate session token
            if not auth_middleware:
                logger.warning("SocketIO connection rejected: Auth middleware not available")
                disconnect()
                return False
            
            user = auth_middleware.validate_session_token(session_token)
            if not user:
                logger.warning(f"SocketIO connection rejected: Invalid session token")
                disconnect()
                return False
            
            user_id = user['user_id']
            session_id = request.sid
            
            # Store connection info
            active_connections[session_id] = {
                'user_id': user_id,
                'connected_at': datetime.utcnow(),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'session_token': session_token
            }
            
            # Join user-specific room
            user_room = f"user_{user_id}"
            join_room(user_room)
            user_rooms[session_id] = user_room
            
            logger.info(f"✅ User {user_id} connected via SocketIO (session: {session_id})")
            
            # Send connection confirmation
            emit('connected', {
                'status': 'connected',
                'user_id': user_id,
                'session_id': session_id,
                'server_time': datetime.utcnow().isoformat(),
                'features': [
                    'real_time_processing_updates',
                    'live_notifications',
                    'instant_status_updates'
                ]
            })
            
            # Send any pending notifications
            send_pending_notifications(user_id)
            
            # Log connection activity
            log_socketio_activity(user_id, 'connected', {
                'session_id': session_id,
                'ip_address': request.remote_addr
            })
            
            return True
            
        except Exception as e:
            logger.error(f"SocketIO connection error: {e}")
            disconnect()
            return False
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        try:
            session_id = request.sid
            
            if session_id in active_connections:
                connection_info = active_connections[session_id]
                user_id = connection_info['user_id']
                
                # Leave user room
                if session_id in user_rooms:
                    leave_room(user_rooms[session_id])
                    del user_rooms[session_id]
                
                # Remove from active connections
                del active_connections[session_id]
                
                logger.info(f"👋 User {user_id} disconnected from SocketIO (session: {session_id})")
                
                # Log disconnection activity
                log_socketio_activity(user_id, 'disconnected', {
                    'session_id': session_id,
                    'duration': (datetime.utcnow() - connection_info['connected_at']).total_seconds()
                })
            
        except Exception as e:
            logger.error(f"SocketIO disconnection error: {e}")
    
    @socketio.on('subscribe_resume_processing')
    def handle_subscribe_resume_processing(data):
        """Subscribe to resume processing updates"""
        try:
            session_id = request.sid
            
            if session_id not in active_connections:
                emit('error', {'message': 'Not authenticated'})
                return
            
            resume_id = data.get('resume_id') if data else None
            if not resume_id:
                emit('error', {'message': 'Resume ID required'})
                return
            
            user_id = active_connections[session_id]['user_id']
            
            # Verify user owns this resume
            if not verify_resume_ownership(resume_id, user_id):
                emit('error', {'message': 'Resume not found or access denied'})
                return
            
            # Join resume-specific room
            resume_room = f"resume_{resume_id}"
            join_room(resume_room)
            
            logger.info(f"📡 User {user_id} subscribed to resume {resume_id} processing updates")
            
            # Send current resume status
            current_status = get_resume_status(resume_id, user_id)
            if current_status:
                emit('resume_processing_update', {
                    'resume_id': resume_id,
                    'status': current_status,
                    'subscribed': True
                })
            
        except Exception as e:
            logger.error(f"SocketIO subscribe error: {e}")
            emit('error', {'message': 'Subscription failed'})
    
    @socketio.on('unsubscribe_resume_processing')
    def handle_unsubscribe_resume_processing(data):
        """Unsubscribe from resume processing updates"""
        try:
            resume_id = data.get('resume_id') if data else None
            if resume_id:
                resume_room = f"resume_{resume_id}"
                leave_room(resume_room)
                
                emit('resume_processing_update', {
                    'resume_id': resume_id,
                    'subscribed': False
                })
                
                logger.info(f"📡 Client unsubscribed from resume {resume_id} updates")
            
        except Exception as e:
            logger.error(f"SocketIO unsubscribe error: {e}")
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection keep-alive"""
        try:
            emit('pong', {
                'server_time': datetime.utcnow().isoformat(),
                'status': 'alive'
            })
        except Exception as e:
            logger.error(f"SocketIO ping error: {e}")
    
    @socketio.on('get_status')
    def handle_get_status():
        """Get current user status and stats"""
        try:
            session_id = request.sid
            
            if session_id not in active_connections:
                emit('error', {'message': 'Not authenticated'})
                return
            
            user_id = active_connections[session_id]['user_id']
            
            # Get user status
            user_status = get_user_status(user_id)
            
            emit('status_update', {
                'user_status': user_status,
                'connection_time': active_connections[session_id]['connected_at'].isoformat(),
                'active_sessions': get_user_active_sessions(user_id)
            })
            
        except Exception as e:
            logger.error(f"SocketIO get status error: {e}")
            emit('error', {'message': 'Failed to get status'})

# Broadcasting functions for external use

def broadcast_resume_processing_update(resume_id, user_id, status_data):
    """Broadcast resume processing update to subscribed clients"""
    try:
        if not socketio:
            return
        
        # Broadcast to resume-specific room
        resume_room = f"resume_{resume_id}"
        socketio.emit('resume_processing_update', {
            'resume_id': resume_id,
            'status': status_data,
            'timestamp': datetime.utcnow().isoformat()
        }, room=resume_room)
        
        # Also broadcast to user room for general notifications
        user_room = f"user_{user_id}"
        socketio.emit('notification', {
            'type': 'resume_processing',
            'resume_id': resume_id,
            'message': get_status_message(status_data),
            'timestamp': datetime.utcnow().isoformat()
        }, room=user_room)
        
        logger.info(f"📡 Broadcasted resume {resume_id} status update: {status_data.get('processing_status', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Broadcast resume update error: {e}")

def broadcast_credit_update(user_id, credit_info):
    """Broadcast credit status update to user"""
    try:
        if not socketio:
            return
        
        user_room = f"user_{user_id}"
        socketio.emit('credit_update', {
            'credit_status': credit_info,
            'timestamp': datetime.utcnow().isoformat()
        }, room=user_room)
        
        logger.info(f"📡 Broadcasted credit update to user {user_id}")
        
    except Exception as e:
        logger.error(f"Broadcast credit update error: {e}")

def broadcast_system_notification(user_id, notification_data):
    """Broadcast system notification to user"""
    try:
        if not socketio:
            return
        
        user_room = f"user_{user_id}"
        socketio.emit('system_notification', {
            'notification': notification_data,
            'timestamp': datetime.utcnow().isoformat()
        }, room=user_room)
        
        logger.info(f"📡 Broadcasted system notification to user {user_id}: {notification_data.get('type', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Broadcast system notification error: {e}")

def broadcast_queue_update(user_id, queue_info):
    """Broadcast queue status update to user"""
    try:
        if not socketio:
            return
        
        user_room = f"user_{user_id}"
        socketio.emit('queue_update', {
            'queue_status': queue_info,
            'timestamp': datetime.utcnow().isoformat()
        }, room=user_room)
        
        logger.info(f"📡 Broadcasted queue update to user {user_id}")
        
    except Exception as e:
        logger.error(f"Broadcast queue update error: {e}")

# Helper functions

def verify_resume_ownership(resume_id, user_id):
    """Verify that user owns the resume"""
    try:
        if not railway_db:
            return False
        
        resume = railway_db.execute_read(
            "SELECT user_id FROM resumes WHERE id = %s AND user_id = %s",
            (resume_id, user_id)
        )
        
        return bool(resume)
        
    except Exception as e:
        logger.error(f"Resume ownership verification error: {e}")
        return False

def get_resume_status(resume_id, user_id):
    """Get current resume processing status"""
    try:
        if not railway_db:
            return None
        
        status = railway_db.execute_read("""
            SELECT 
                processing_status, overall_score, ai_provider_used,
                processing_started_at, processing_completed_at, processing_error
            FROM resumes 
            WHERE id = %s AND user_id = %s
        """, (resume_id, user_id))
        
        return status[0] if status else None
        
    except Exception as e:
        logger.error(f"Get resume status error: {e}")
        return None

def get_user_status(user_id):
    """Get comprehensive user status"""
    try:
        if not railway_db:
            return {}
        
        # Get basic user info
        user_info = railway_db.execute_read("""
            SELECT 
                is_premium, trial_credits_used, total_resumes_uploaded,
                total_ai_requests, last_login
            FROM users 
            WHERE user_id = %s
        """, (user_id,))
        
        if not user_info:
            return {}
        
        user_data = user_info[0]
        
        # Get recent activity
        recent_resumes = railway_db.execute_read("""
            SELECT id, filename, processing_status, upload_date
            FROM resumes 
            WHERE user_id = %s 
            ORDER BY upload_date DESC 
            LIMIT 5
        """, (user_id,))
        
        return {
            'user_info': user_data,
            'recent_resumes': recent_resumes or [],
            'last_updated': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get user status error: {e}")
        return {}

def get_user_active_sessions(user_id):
    """Get count of active sessions for user"""
    try:
        count = 0
        for connection in active_connections.values():
            if connection['user_id'] == user_id:
                count += 1
        return count
    except Exception as e:
        logger.error(f"Get active sessions error: {e}")
        return 0

def send_pending_notifications(user_id):
    """Send any pending notifications to newly connected user"""
    try:
        if not railway_db:
            return
        
        # Get unread notifications
        notifications = railway_db.execute_read("""
            SELECT notification_type, message, data, created_at
            FROM user_notifications 
            WHERE user_id = %s AND read_at IS NULL
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        
        if notifications:
            for notification in notifications:
                emit('pending_notification', {
                    'type': notification['notification_type'],
                    'message': notification['message'],
                    'data': json.loads(notification['data']) if notification['data'] else {},
                    'created_at': notification['created_at'].isoformat()
                })
            
            logger.info(f"📬 Sent {len(notifications)} pending notifications to user {user_id}")
        
    except Exception as e:
        logger.error(f"Send pending notifications error: {e}")

def get_status_message(status_data):
    """Generate human-readable status message"""
    try:
        processing_status = status_data.get('processing_status', 'unknown')
        
        if processing_status == 'processing':
            return "AI analysis in progress..."
        elif processing_status == 'completed':
            score = status_data.get('overall_score', 0)
            return f"Analysis completed with score: {score}/100"
        elif processing_status == 'failed':
            return "Analysis failed. Please try again."
        else:
            return f"Status: {processing_status}"
            
    except Exception as e:
        logger.error(f"Get status message error: {e}")
        return "Status update"

def log_socketio_activity(user_id, action, details):
    """Log SocketIO activity"""
    try:
        if railway_db:
            railway_db.execute_write("""
                INSERT INTO user_activity_log (user_id, action, details, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, f"socketio_{action}", json.dumps(details), datetime.utcnow()))
    except Exception as e:
        logger.warning(f"Failed to log SocketIO activity: {e}")

# Connection management utilities

def get_active_connections_count():
    """Get total number of active SocketIO connections"""
    return len(active_connections)

def get_active_users_count():
    """Get number of unique active users"""
    unique_users = set()
    for connection in active_connections.values():
        unique_users.add(connection['user_id'])
    return len(unique_users)

def disconnect_user_sessions(user_id):
    """Disconnect all sessions for a specific user"""
    try:
        sessions_to_disconnect = []
        
        for session_id, connection in active_connections.items():
            if connection['user_id'] == user_id:
                sessions_to_disconnect.append(session_id)
        
        for session_id in sessions_to_disconnect:
            if socketio:
                socketio.disconnect(session_id)
        
        logger.info(f"Disconnected {len(sessions_to_disconnect)} sessions for user {user_id}")
        
    except Exception as e:
        logger.error(f"Disconnect user sessions error: {e}")

# External interface for other modules
def get_socketio_stats():
    """Get SocketIO connection statistics"""
    try:
        return {
            'active_connections': get_active_connections_count(),
            'active_users': get_active_users_count(),
            'connections_by_user': {
                user_id: sum(1 for c in active_connections.values() if c['user_id'] == user_id)
                for user_id in set(c['user_id'] for c in active_connections.values())
            },
            'last_updated': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get SocketIO stats error: {e}")
        return {}
