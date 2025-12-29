#!/usr/bin/env python3
"""
WebSocket Integration Routes for Flask Application
Provides WebSocket endpoints and real-time event management
"""

from flask import Blueprint, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

from utils.realtime_manager import realtime_manager, emit_resume_processing_update, emit_queue_status_update
from auth_middleware import AuthMiddleware, require_auth
from config import Config

logger = logging.getLogger(__name__)

# Create blueprint for WebSocket routes
websocket_bp = Blueprint('websocket', __name__, url_prefix='/api/v1/ws')

# SocketIO instance (will be initialized in main app)
socketio = None

def init_socketio(app):
    """Initialize SocketIO with Flask app"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        ping_timeout=60,
        ping_interval=25,
        transport=['websocket', 'polling']
    )
    
    # Register event handlers
    register_socketio_events()
    
    logger.info("SocketIO initialized")
    return socketio

def register_socketio_events():
    """Register SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle WebSocket connection"""
        logger.info(f"Client connected: {request.sid}")
        
        # Authenticate if auth data provided
        if auth and 'token' in auth:
            try:
                # Validate token (integrate with your auth system)
                user = validate_socket_auth(auth['token'])
                if user:
                    session['user_id'] = user['id']
                    session['user_email'] = user['email']
                    join_room(f"user_{user['id']}")
                    
                    emit('authenticated', {
                        'user_id': user['id'],
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    emit('auth_error', {'error': 'Invalid authentication'})
                    disconnect()
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                emit('auth_error', {'error': 'Authentication failed'})
                disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        user_id = session.get('user_id')
        if user_id:
            leave_room(f"user_{user_id}")
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """Subscribe to specific channels"""
        user_id = session.get('user_id')
        if not user_id:
            emit('error', {'message': 'Not authenticated'})
            return
        
        channels = data.get('channels', [])
        for channel in channels:
            # Validate channel access
            if can_access_channel(user_id, channel):
                join_room(channel)
                logger.info(f"User {user_id} subscribed to {channel}")
        
        emit('subscribed', {'channels': channels})
    
    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """Unsubscribe from channels"""
        channels = data.get('channels', [])
        for channel in channels:
            leave_room(channel)
        
        emit('unsubscribed', {'channels': channels})
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping request"""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})

def validate_socket_auth(token: str) -> Optional[Dict[str, Any]]:
    """Validate WebSocket authentication token"""
    # TODO: Integrate with your authentication system
    # For now, simple validation
    if len(token) > 10:
        return {
            'id': 'user_123',  # Extract from token
            'email': 'user@example.com'
        }
    return None

def can_access_channel(user_id: str, channel: str) -> bool:
    """Check if user can access specific channel"""
    # Basic channel access control
    public_channels = ['general', 'announcements']
    user_channels = [f'user_{user_id}', 'resume_processing', 'queue_updates']
    
    return channel in public_channels or channel in user_channels

# Flask routes for WebSocket management
@websocket_bp.route('/status', methods=['GET'])
def get_websocket_status():
    """Get WebSocket server status"""
    try:
        stats = realtime_manager.get_stats() if realtime_manager else {}
        
        return jsonify({
            'success': True,
            'data': {
                'websocket_server': 'running' if realtime_manager and realtime_manager.is_running else 'stopped',
                'socketio_server': 'running' if socketio else 'not initialized',
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@websocket_bp.route('/connections', methods=['GET'])
@require_auth
def get_active_connections():
    """Get active WebSocket connections (admin only)"""
    try:
        user = get_current_user()
        if not user.get('is_admin'):
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        if not realtime_manager:
            return jsonify({
                'success': True,
                'data': {'connections': [], 'total': 0}
            })
        
        connections_data = []
        for conn_id, info in realtime_manager.connection_info.items():
            connections_data.append({
                'connection_id': conn_id,
                'user_id': info.user_id,
                'channels': list(info.channels),
                'connected_at': info.connected_at.isoformat(),
                'last_ping': info.last_ping.isoformat(),
                'user_agent': info.user_agent
            })
        
        return jsonify({
            'success': True,
            'data': {
                'connections': connections_data,
                'total': len(connections_data)
            }
        })
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@websocket_bp.route('/broadcast', methods=['POST'])
@require_auth
def broadcast_message():
    """Broadcast message to channels (admin only)"""
    try:
        user = get_current_user()
        if not user.get('is_admin'):
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        data = request.get_json()
        message = data.get('message')
        channels = data.get('channels', ['general'])
        message_type = data.get('type', 'announcement')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Broadcast via SocketIO
        if socketio:
            for channel in channels:
                socketio.emit('broadcast', {
                    'type': message_type,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat(),
                    'sender': 'system'
                }, room=channel)
        
        # Broadcast via WebSocket manager
        if realtime_manager:
            for channel in channels:
                realtime_manager.emit_event(
                    'broadcast_message',
                    '',  # No specific user
                    {
                        'message': message,
                        'type': message_type
                    },
                    channel=channel,
                    priority=1
                )
        
        return jsonify({
            'success': True,
            'message': 'Broadcast sent successfully'
        })
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@websocket_bp.route('/notify-user', methods=['POST'])
@require_auth
def notify_user():
    """Send notification to specific user"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        target_user_id = data.get('user_id')
        message = data.get('message')
        notification_type = data.get('type', 'info')
        
        if not target_user_id or not message:
            return jsonify({
                'success': False,
                'error': 'user_id and message are required'
            }), 400
        
        # Check permissions (users can only notify themselves unless admin)
        if not user.get('is_admin') and user.get('id') != target_user_id:
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403
        
        # Send via SocketIO
        if socketio:
            socketio.emit('notification', {
                'type': notification_type,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f'user_{target_user_id}')
        
        # Send via WebSocket manager
        if realtime_manager:
            realtime_manager.emit_event(
                'user_notification',
                target_user_id,
                {
                    'message': message,
                    'type': notification_type
                },
                priority=1
            )
        
        return jsonify({
            'success': True,
            'message': 'Notification sent successfully'
        })
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper functions for emitting events
def emit_processing_update(user_id: str, resume_id: str, stage: str, progress: int, details: Dict[str, Any] = None):
    """Emit resume processing update via multiple channels"""
    update_data = {
        'resume_id': resume_id,
        'stage': stage,
        'progress': progress,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Emit via SocketIO
    if socketio:
        socketio.emit('processing_update', update_data, room=f'user_{user_id}')
    
    # Emit via WebSocket manager
    emit_resume_processing_update(user_id, resume_id, stage, progress, details)

def emit_queue_update(user_id: str, position: int, estimated_time: int):
    """Emit queue status update via multiple channels"""
    update_data = {
        'queue_position': position,
        'estimated_wait_time': estimated_time,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Emit via SocketIO
    if socketio:
        socketio.emit('queue_update', update_data, room=f'user_{user_id}')
    
    # Emit via WebSocket manager
    emit_queue_status_update(user_id, position, estimated_time)

def emit_analytics_data(user_id: str, analytics: Dict[str, Any]):
    """Emit real-time analytics update"""
    analytics_data = {
        **analytics,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Emit via SocketIO
    if socketio:
        socketio.emit('analytics_update', analytics_data, room=f'user_{user_id}')
    
    # Emit via WebSocket manager
    if realtime_manager:
        realtime_manager.emit_event(
            'analytics_update',
            user_id,
            analytics_data,
            channel='analytics',
            priority=3
        )

def emit_system_alert(message: str, alert_type: str = 'info', target_room: str = 'general'):
    """Emit system-wide alert"""
    alert_data = {
        'message': message,
        'type': alert_type,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Emit via SocketIO
    if socketio:
        socketio.emit('system_alert', alert_data, room=target_room)
    
    # Emit via WebSocket manager
    if realtime_manager:
        realtime_manager.emit_event(
            'system_alert',
            '',  # System-wide
            alert_data,
            channel=target_room,
            priority=1
        )

# WebSocket client helper
def get_websocket_client_code():
    """Generate JavaScript client code for WebSocket connection"""
    return """
// WebSocket Real-time Client for HR ATS
class ATSWebSocketClient {
    constructor(options = {}) {
        this.url = options.url || 'ws://localhost:8765';
        this.authToken = options.authToken || null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectInterval = options.reconnectInterval || 3000;
        this.websocket = null;
        this.eventHandlers = {};
        this.isConnected = false;
        
        this.connect();
    }
    
    connect() {
        try {
            this.websocket = new WebSocket(this.url);
            
            this.websocket.onopen = (event) => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // Authenticate if token available
                if (this.authToken) {
                    this.authenticate(this.authToken);
                }
                
                this.emit('connected', event);
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = (event) => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.emit('disconnected', event);
                
                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.reconnectAttempts++;
                        console.log(`Reconnection attempt ${this.reconnectAttempts}`);
                        this.connect();
                    }, this.reconnectInterval);
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
        }
    }
    
    authenticate(token) {
        this.authToken = token;
        this.send({
            type: 'authenticate',
            auth_token: token,
            user_agent: navigator.userAgent,
            timestamp: new Date().toISOString()
        });
    }
    
    subscribe(channels) {
        this.send({
            type: 'subscribe',
            channels: Array.isArray(channels) ? channels : [channels]
        });
    }
    
    unsubscribe(channels) {
        this.send({
            type: 'unsubscribe',
            channels: Array.isArray(channels) ? channels : [channels]
        });
    }
    
    send(data) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }
    
    handleMessage(data) {
        const messageType = data.type;
        
        switch (messageType) {
            case 'realtime_event':
                this.emit('event', data.event);
                this.emit(data.event.event_type, data.event);
                break;
            case 'authenticated':
                this.emit('authenticated', data);
                break;
            case 'auth_error':
                this.emit('auth_error', data);
                break;
            case 'heartbeat':
                this.emit('heartbeat', data);
                break;
            default:
                this.emit(messageType, data);
        }
    }
    
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    off(event, handler) {
        if (this.eventHandlers[event]) {
            const index = this.eventHandlers[event].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[event].splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
        }
    }
}

// Usage example:
// const wsClient = new ATSWebSocketClient({
//     url: 'ws://localhost:8765',
//     authToken: 'your-auth-token'
// });
// 
// wsClient.on('resume_processing_update', (event) => {
//     console.log('Processing update:', event);
// });
// 
// wsClient.subscribe(['resume_processing', 'queue_updates']);
"""

@websocket_bp.route('/client-code', methods=['GET'])
def get_client_code():
    """Get WebSocket client JavaScript code"""
    return jsonify({
        'success': True,
        'data': {
            'client_code': get_websocket_client_code(),
            'usage_instructions': [
                "Include the client code in your frontend",
                "Create new ATSWebSocketClient instance",
                "Authenticate with token",
                "Subscribe to relevant channels",
                "Listen for events"
            ]
        }
    })


def init_websocket_routes(realtime_manager=None, db_manager=None):
    """Initialize WebSocket routes with dependencies"""
    global realtime_manager_instance
    
    if realtime_manager:
        realtime_manager_instance = realtime_manager
        logger.info("WebSocket routes initialized with realtime manager")
    
    if db_manager:
        logger.info("WebSocket routes initialized with database manager")
    
    return websocket_bp
