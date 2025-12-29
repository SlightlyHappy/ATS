"""
WebSocket service for real-time notifications and updates.
Handles queue status updates, analysis completion notifications, and live dashboard data.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from app.models.user import User
from app.models.queue import AnalysisQueue, QueueStatus, BatchUpload
from app.models.analysis import Analysis
from app.models.admin import AdminUser
import json

logger = logging.getLogger(__name__)

class WebSocketService:
    """Service to manage WebSocket connections and real-time notifications."""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connected_users = {}  # session_id -> user_info
        self.user_sessions = {}   # user_id -> [session_ids]
        self.admin_sessions = {}  # admin_id -> [session_ids]
        self.connection_stats = {
            'total_connections': 0,
            'current_connections': 0,
            'peak_connections': 0,
            'reconnections': 0,
            'errors': 0
        }
        
    def register_handlers(self):
        """Register all WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection."""
            try:
                # Use the socketio instance's built-in request context
                session_id = self.socketio.request.sid if hasattr(self.socketio, 'request') else None
                if not session_id:
                    # Fallback for different flask-socketio versions
                    import flask_socketio
                    session_id = getattr(flask_socketio, 'request', {}).get('sid', 'unknown')
                
                logger.info(f"Client connected: {session_id}")
                
                # Update connection statistics
                self.connection_stats['total_connections'] += 1
                self.connection_stats['current_connections'] += 1
                if self.connection_stats['current_connections'] > self.connection_stats['peak_connections']:
                    self.connection_stats['peak_connections'] = self.connection_stats['current_connections']
                
                # Send connection confirmation with server info
                emit('connected', {
                    'status': 'connected',
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'server_info': {
                        'version': '2.0.0',
                        'features': ['real_time_updates', 'queue_monitoring', 'admin_dashboard', 'backup_progress']
                    }
                })
                
            except Exception as e:
                logger.error(f"Error handling connection: {str(e)}")
                self.connection_stats['errors'] += 1
                disconnect()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            try:
                # Use the socketio instance's built-in request context
                session_id = self.socketio.request.sid if hasattr(self.socketio, 'request') else None
                if not session_id:
                    # Fallback for different flask-socketio versions  
                    import flask_socketio
                    session_id = getattr(flask_socketio, 'request', {}).get('sid', 'unknown')
                
                self._remove_user_session(session_id)
                self.connection_stats['current_connections'] = max(0, self.connection_stats['current_connections'] - 1)
                logger.info(f"Client disconnected: {session_id}")
                
            except Exception as e:
                logger.error(f"Error handling disconnection: {str(e)}")
                self.connection_stats['errors'] += 1
        
        @self.socketio.on('authenticate')
        def handle_authenticate(data):
            """Authenticate user and join appropriate rooms."""
            try:
                # Use the socketio instance's built-in request context
                session_id = self.socketio.request.sid if hasattr(self.socketio, 'request') else None
                if not session_id:
                    # Fallback for different flask-socketio versions
                    import flask_socketio
                    session_id = getattr(flask_socketio, 'request', {}).get('sid', 'unknown')
                
                user_id = data.get('user_id')
                user_type = data.get('user_type', 'user')  # 'user' or 'admin'
                
                if not user_id:
                    emit('auth_error', {'error': 'User ID required'})
                    return
                
                # Verify user exists
                if user_type == 'admin':
                    user = AdminUser.query.get(user_id)
                    if not user:
                        emit('auth_error', {'error': 'Admin user not found'})
                        return
                else:
                    user = User.query.get(user_id)
                    if not user:
                        emit('auth_error', {'error': 'User not found'})
                        return
                
                # Store user session info
                self.connected_users[session_id] = {
                    'user_id': user_id,
                    'user_type': user_type,
                    'email': user.email,
                    'connected_at': datetime.utcnow()
                }
                
                # Add to user sessions tracking
                if user_type == 'admin':
                    if user_id not in self.admin_sessions:
                        self.admin_sessions[user_id] = []
                    self.admin_sessions[user_id].append(session_id)
                    
                    # Join admin rooms
                    join_room('admin_dashboard')
                    join_room('admin_notifications')
                else:
                    if user_id not in self.user_sessions:
                        self.user_sessions[user_id] = []
                    self.user_sessions[user_id].append(session_id)
                
                # Join user-specific room
                join_room(f'user_{user_id}')
                
                # Join queue updates room
                join_room('queue_updates')
                
                emit('authenticated', {
                    'status': 'authenticated',
                    'user_id': user_id,
                    'user_type': user_type,
                    'rooms': self._get_user_rooms(user_id, user_type)
                })
                
                logger.info(f"User {user_id} ({user_type}) authenticated with session {session_id}")
                
            except Exception as e:
                logger.error(f"Error authenticating user: {str(e)}")
                emit('auth_error', {'error': 'Authentication failed'})
        
        @self.socketio.on('join_queue_room')
        def handle_join_queue_room(data):
            """Join queue-specific room for updates."""
            try:
                queue_id = data.get('queue_id')
                if queue_id:
                    join_room(f'queue_{queue_id}')
                    emit('joined_queue_room', {'queue_id': queue_id})
                    
            except Exception as e:
                logger.error(f"Error joining queue room: {str(e)}")
        
        @self.socketio.on('leave_queue_room')
        def handle_leave_queue_room(data):
            """Leave queue-specific room."""
            try:
                queue_id = data.get('queue_id')
                if queue_id:
                    leave_room(f'queue_{queue_id}')
                    emit('left_queue_room', {'queue_id': queue_id})
                    
            except Exception as e:
                logger.error(f"Error leaving queue room: {str(e)}")
        
        @self.socketio.on('request_queue_status')
        def handle_request_queue_status(data):
            """Handle request for current queue status."""
            try:
                # Use the socketio instance's built-in request context
                session_id = self.socketio.request.sid if hasattr(self.socketio, 'request') else None
                if not session_id:
                    # Fallback for different flask-socketio versions
                    import flask_socketio
                    session_id = getattr(flask_socketio, 'request', {}).get('sid', 'unknown')
                
                user_id = data.get('user_id')
                session_info = self.connected_users.get(session_id)
                
                if not session_info:
                    emit('error', {'error': 'Not authenticated'})
                    return
                
                # Get queue status and emit to requesting user
                from app.services.queue_service import QueueService
                queue_service = QueueService()
                status = queue_service.get_queue_status(user_id)
                
                emit('queue_status_update', status)
                
            except Exception as e:
                logger.error(f"Error handling queue status request: {str(e)}")
                emit('error', {'error': 'Failed to get queue status'})
        
        @self.socketio.on('request_dashboard_data')
        def handle_request_dashboard_data():
            """Handle request for admin dashboard data."""
            try:
                # Use the socketio instance's built-in request context
                session_id = self.socketio.request.sid if hasattr(self.socketio, 'request') else None
                if not session_id:
                    # Fallback for different flask-socketio versions
                    import flask_socketio
                    session_id = getattr(flask_socketio, 'request', {}).get('sid', 'unknown')
                
                session_info = self.connected_users.get(session_id)
                
                if not session_info or session_info.get('user_type') != 'admin':
                    emit('error', {'error': 'Admin access required'})
                    return
                
                # Get dashboard data
                dashboard_data = self._get_dashboard_data()
                emit('dashboard_data_update', dashboard_data)
                
            except Exception as e:
                logger.error(f"Error handling dashboard data request: {str(e)}")
                emit('error', {'error': 'Failed to get dashboard data'})
    
    def get_connection_stats(self):
        """Get WebSocket connection statistics."""
        return {
            **self.connection_stats,
            'active_users': len(self.user_sessions),
            'active_admins': len(self.admin_sessions),
            'total_sessions': len(self.connected_users)
        }
    
    def broadcast_system_alert(self, alert_type: str, message: str, severity: str = 'info', details: Optional[Dict[str, Any]] = None):
        """Broadcast system-wide alert to all connected users.
        Now supports optional details payload to carry structured data.
        """
        try:
            alert_data = {
                'type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Include additional details if provided
            if details is not None:
                alert_data['details'] = details
            
            # Send to all connected users
            self.socketio.emit('system_alert', alert_data)
            
            # Log the alert
            logger.info(f"System alert broadcasted: {alert_type} - {message}")
            
        except Exception as e:
            logger.error(f"Error broadcasting system alert: {str(e)}")
    
    def cleanup_stale_connections(self):
        """Clean up stale connections (called periodically)."""
        try:
            stale_sessions = []
            current_time = datetime.utcnow()
            
            for session_id, user_info in self.connected_users.items():
                # Check if connection is older than timeout (30 minutes)
                connected_at = user_info.get('connected_at')
                if connected_at and (current_time - connected_at).seconds > 1800:
                    stale_sessions.append(session_id)
            
            # Remove stale sessions
            for session_id in stale_sessions:
                self._remove_user_session(session_id)
                logger.info(f"Removed stale session: {session_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up stale connections: {str(e)}")
    
    def send_health_check(self):
        """Send health check ping to all connected clients."""
        try:
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'server_load': self.get_connection_stats()
            }
            
            self.socketio.emit('health_check', health_data)
            
        except Exception as e:
            logger.error(f"Error sending health check: {str(e)}")
    
    def notify_queue_progress(self, queue_id: str, progress_data: Dict[str, Any]):
        """Send queue progress update with enhanced error handling."""
        try:
            # Send to queue-specific room
            self.socketio.emit('queue_progress_update', {
                'queue_id': queue_id,
                'progress': progress_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'queue_{queue_id}')
            
            # Also send to user room if user_id is available
            if 'user_id' in progress_data:
                self.socketio.emit('user_queue_update', {
                    'queue_id': queue_id,
                    'progress': progress_data,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"user_{progress_data['user_id']}")
                
        except Exception as e:
            logger.error(f"Error sending queue progress update: {str(e)}")
    
    def notify_analysis_complete(self, analysis_id: str, user_id: str, results: Dict[str, Any]):
        """Send analysis completion notification."""
        try:
            notification_data = {
                'analysis_id': analysis_id,
                'status': 'completed',
                'results_summary': {
                    'total_score': results.get('total_score'),
                    'confidence': results.get('confidence'),
                    'processing_time': results.get('processing_time')
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send to user room
            self.socketio.emit('analysis_completed', notification_data, room=f'user_{user_id}')
            
            # Send to admin dashboard
            self.socketio.emit('new_analysis_completed', {
                'user_id': user_id,
                'analysis_id': analysis_id,
                'completion_time': datetime.utcnow().isoformat()
            }, room='admin_dashboard')
            
        except Exception as e:
            logger.error(f"Error sending analysis completion notification: {str(e)}")
    
    def emergency_shutdown_notification(self):
        """Send emergency shutdown notification to all users."""
        try:
            shutdown_data = {
                'type': 'emergency_shutdown',
                'message': 'System maintenance in progress. Please save your work.',
                'estimated_downtime': '15 minutes',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.socketio.emit('emergency_notification', shutdown_data)
            logger.critical("Emergency shutdown notification sent to all users")
            
        except Exception as e:
            logger.error(f"Error sending emergency shutdown notification: {str(e)}")

    def emit_backup_progress(self, backup_id: str, status: str, progress_pct: int, message: str | None = None):
        """Emit backup progress updates to admin dashboards."""
        try:
            payload = {
                'backup_id': backup_id,
                'status': status,
                'progress_pct': progress_pct,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.socketio.emit('backup_progress', payload, room='admin_dashboard')
        except Exception as e:
            logger.error(f"Failed to emit backup_progress: {e}")

    def _remove_user_session(self, session_id: str):
        """Remove user session from tracking."""
        if session_id in self.connected_users:
            user_info = self.connected_users[session_id]
            user_id = user_info['user_id']
            user_type = user_info['user_type']
            
            # Remove from user sessions
            if user_type == 'admin' and user_id in self.admin_sessions:
                if session_id in self.admin_sessions[user_id]:
                    self.admin_sessions[user_id].remove(session_id)
                if not self.admin_sessions[user_id]:
                    del self.admin_sessions[user_id]
            elif user_id in self.user_sessions:
                if session_id in self.user_sessions[user_id]:
                    self.user_sessions[user_id].remove(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            del self.connected_users[session_id]
    
    def _get_user_rooms(self, user_id: str, user_type: str) -> List[str]:
        """Get list of rooms user should be in."""
        rooms = [f'user_{user_id}', 'queue_updates']
        
        if user_type == 'admin':
            rooms.extend(['admin_dashboard', 'admin_notifications'])
        
        return rooms
    
    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data for admin users."""
        try:
            from app.services.queue_service import QueueService
            from app.models.user import User
            from app.models.resume import Resume
            from app.models.analysis import Analysis
            
            queue_service = QueueService()
            
            # Get queue statistics
            queue_stats = queue_service.get_queue_status()
            
            # Get user statistics
            total_users = User.query.count()
            active_users = len(self.user_sessions)
            
            # Get processing statistics
            total_resumes = Resume.query.count()
            total_analyses = Analysis.query.count()
            
            # Get recent activity
            recent_queues = AnalysisQueue.query.order_by(
                AnalysisQueue.created_at.desc()
            ).limit(10).all()
            
            return {
                'queue_stats': queue_stats,
                'user_stats': {
                    'total': total_users,
                    'active': active_users,
                    'connected_sessions': len(self.connected_users)
                },
                'processing_stats': {
                    'total_resumes': total_resumes,
                    'total_analyses': total_analyses
                },
                'recent_activity': [item.to_dict() for item in recent_queues],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {'error': 'Failed to load dashboard data'}


# Global WebSocket service instance
websocket_service = None

def init_websocket_service(socketio: SocketIO):
    """Initialize the global WebSocket service."""
    global websocket_service
    websocket_service = WebSocketService(socketio)
    websocket_service.register_handlers()
    return websocket_service
