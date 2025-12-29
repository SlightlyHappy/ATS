#!/usr/bin/env python3
"""
Real-time WebSocket Manager for HR ATS System
Provides live updates for resume processing, queue status, and analytics
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
from threading import Thread, Lock
import weakref
from collections import defaultdict

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    from typing import Any as WebSocketServerProtocol

logger = logging.getLogger(__name__)

@dataclass
class RealtimeEvent:
    """Real-time event structure"""
    event_type: str
    event_id: str
    user_id: str
    data: Dict[str, Any]
    timestamp: str
    channel: str = "general"
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class ConnectionInfo:
    """WebSocket connection information"""
    connection_id: str
    user_id: str
    channels: Set[str]
    connected_at: datetime
    last_ping: datetime
    user_agent: str = ""
    ip_address: str = ""

class RealtimeManager:
    """Real-time WebSocket manager for live updates"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.connections: Dict[str, WebSocketServerProtocol] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.event_queue: List[RealtimeEvent] = []
        self.is_running = False
        self.server = None
        self._lock = Lock()
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
    async def start_server(self):
        """Start the WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("WebSockets not available. Install with: pip install websockets")
            return
            
        try:
            self.server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.is_running = True
            logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
            
            # Start background tasks
            await asyncio.gather(
                self.cleanup_task(),
                self.heartbeat_task(),
                self.event_processor()
            )
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        try:
            # Register connection
            self.connections[connection_id] = websocket
            logger.info(f"New WebSocket connection: {connection_id}")
            
            # Send welcome message
            await self.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(connection_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed: {connection_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        finally:
            await self.cleanup_connection(connection_id)
    
    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "authenticate":
                await self.authenticate_connection(connection_id, data)
            elif message_type == "subscribe":
                await self.subscribe_to_channels(connection_id, data.get("channels", []))
            elif message_type == "unsubscribe":
                await self.unsubscribe_from_channels(connection_id, data.get("channels", []))
            elif message_type == "ping":
                await self.handle_ping(connection_id)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from connection {connection_id}")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
    
    async def authenticate_connection(self, connection_id: str, data: Dict[str, Any]):
        """Authenticate WebSocket connection"""
        user_id = data.get("user_id")
        auth_token = data.get("auth_token")
        
        if not user_id or not auth_token:
            await self.send_to_connection(connection_id, {
                "type": "auth_error",
                "error": "Missing user_id or auth_token"
            })
            return
        
        # Validate auth token (integrate with your auth system)
        if not self.validate_auth_token(user_id, auth_token):
            await self.send_to_connection(connection_id, {
                "type": "auth_error", 
                "error": "Invalid authentication"
            })
            return
        
        # Store connection info
        self.connection_info[connection_id] = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            channels=set(),
            connected_at=datetime.utcnow(),
            last_ping=datetime.utcnow(),
            user_agent=data.get("user_agent", ""),
            ip_address=data.get("ip_address", "")
        )
        
        # Track user connections
        with self._lock:
            self.user_connections[user_id].add(connection_id)
        
        await self.send_to_connection(connection_id, {
            "type": "authenticated",
            "user_id": user_id,
            "connection_id": connection_id
        })
        
        logger.info(f"Authenticated connection {connection_id} for user {user_id}")
    
    def validate_auth_token(self, user_id: str, auth_token: str) -> bool:
        """Validate authentication token (implement your auth logic)"""
        # TODO: Integrate with your authentication system
        # For now, simple validation
        return len(auth_token) > 10
    
    async def subscribe_to_channels(self, connection_id: str, channels: List[str]):
        """Subscribe connection to specific channels"""
        if connection_id not in self.connection_info:
            return
        
        connection_info = self.connection_info[connection_id]
        
        with self._lock:
            for channel in channels:
                connection_info.channels.add(channel)
                self.channel_subscriptions[channel].add(connection_id)
        
        await self.send_to_connection(connection_id, {
            "type": "subscribed",
            "channels": channels
        })
        
        logger.info(f"Connection {connection_id} subscribed to channels: {channels}")
    
    async def unsubscribe_from_channels(self, connection_id: str, channels: List[str]):
        """Unsubscribe connection from specific channels"""
        if connection_id not in self.connection_info:
            return
        
        connection_info = self.connection_info[connection_id]
        
        with self._lock:
            for channel in channels:
                connection_info.channels.discard(channel)
                self.channel_subscriptions[channel].discard(connection_id)
        
        await self.send_to_connection(connection_id, {
            "type": "unsubscribed",
            "channels": channels
        })
    
    async def handle_ping(self, connection_id: str):
        """Handle ping message"""
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_ping = datetime.utcnow()
        
        await self.send_to_connection(connection_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_to_connection(self, connection_id: str, data: Dict[str, Any]):
        """Send data to specific connection"""
        if connection_id not in self.connections:
            return
        
        try:
            websocket = self.connections[connection_id]
            await websocket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to send to connection {connection_id}: {e}")
            await self.cleanup_connection(connection_id)
    
    async def broadcast_to_user(self, user_id: str, data: Dict[str, Any]):
        """Send data to all connections for a specific user"""
        if user_id not in self.user_connections:
            return
        
        connection_ids = list(self.user_connections[user_id])
        for connection_id in connection_ids:
            await self.send_to_connection(connection_id, data)
    
    async def broadcast_to_channel(self, channel: str, data: Dict[str, Any]):
        """Send data to all connections subscribed to a channel"""
        if channel not in self.channel_subscriptions:
            return
        
        connection_ids = list(self.channel_subscriptions[channel])
        for connection_id in connection_ids:
            await self.send_to_connection(connection_id, data)
    
    async def cleanup_connection(self, connection_id: str):
        """Clean up connection data"""
        # Remove from connections
        self.connections.pop(connection_id, None)
        
        # Get connection info
        connection_info = self.connection_info.pop(connection_id, None)
        if not connection_info:
            return
        
        # Remove from user connections
        with self._lock:
            if connection_info.user_id in self.user_connections:
                self.user_connections[connection_info.user_id].discard(connection_id)
                if not self.user_connections[connection_info.user_id]:
                    del self.user_connections[connection_info.user_id]
            
            # Remove from channel subscriptions
            for channel in connection_info.channels:
                self.channel_subscriptions[channel].discard(connection_id)
                if not self.channel_subscriptions[channel]:
                    del self.channel_subscriptions[channel]
        
        logger.info(f"Cleaned up connection {connection_id}")
    
    async def cleanup_task(self):
        """Background task to clean up stale connections"""
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                stale_connections = []
                
                for connection_id, info in self.connection_info.items():
                    # Remove connections that haven't pinged in 60 seconds
                    if (current_time - info.last_ping).total_seconds() > 60:
                        stale_connections.append(connection_id)
                
                for connection_id in stale_connections:
                    await self.cleanup_connection(connection_id)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
            
            await asyncio.sleep(30)  # Run every 30 seconds
    
    async def heartbeat_task(self):
        """Send heartbeat to all connections"""
        while self.is_running:
            try:
                heartbeat_data = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                    "server_time": time.time(),
                    "connections": len(self.connections)
                }
                
                # Send to all connections
                for connection_id in list(self.connections.keys()):
                    await self.send_to_connection(connection_id, heartbeat_data)
                
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
            
            await asyncio.sleep(30)  # Send every 30 seconds
    
    async def event_processor(self):
        """Process queued events"""
        while self.is_running:
            try:
                if self.event_queue:
                    with self._lock:
                        events_to_process = self.event_queue.copy()
                        self.event_queue.clear()
                    
                    for event in events_to_process:
                        await self.process_event(event)
                
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
            
            await asyncio.sleep(1)  # Process every second
    
    async def process_event(self, event: RealtimeEvent):
        """Process a single real-time event"""
        event_data = {
            "type": "realtime_event",
            "event": asdict(event)
        }
        
        # Send to specific user if user_id is set
        if event.user_id:
            await self.broadcast_to_user(event.user_id, event_data)
        
        # Send to channel subscribers
        if event.channel:
            await self.broadcast_to_channel(event.channel, event_data)
        
        # Trigger event handlers
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def emit_event(self, event_type: str, user_id: str, data: Dict[str, Any], 
                  channel: str = "general", priority: int = 1):
        """Emit a real-time event"""
        event = RealtimeEvent(
            event_type=event_type,
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            channel=channel,
            priority=priority
        )
        
        with self._lock:
            self.event_queue.append(event)
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler for specific event type"""
        self.event_handlers[event_type].append(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get real-time server statistics"""
        return {
            "total_connections": len(self.connections),
            "authenticated_connections": len(self.connection_info),
            "unique_users": len(self.user_connections),
            "active_channels": len(self.channel_subscriptions),
            "queued_events": len(self.event_queue),
            "server_uptime": time.time() if self.is_running else 0
        }

# Global real-time manager instance
realtime_manager = RealtimeManager()

# Convenience functions for common events
def emit_processing_update(user_id: str, operation_id: str, stage: str, progress: int, data: Dict[str, Any] = None):
    """Emit processing update for bulk operations"""
    realtime_manager.emit_event(
        "processing_update",
        user_id,
        {
            "operation_id": operation_id,
            "stage": stage,
            "progress": progress,
            "details": data or {}
        },
        channel="processing_updates",
        priority=1
    )

def emit_resume_processing_update(user_id: str, resume_id: str, stage: str, progress: int, data: Dict[str, Any] = None):
    """Emit resume processing update"""
    realtime_manager.emit_event(
        "resume_processing_update",
        user_id,
        {
            "resume_id": resume_id,
            "stage": stage,
            "progress": progress,
            "details": data or {}
        },
        channel="resume_processing",
        priority=1
    )

def emit_queue_status_update(user_id: str, position: int, estimated_time: int):
    """Emit queue status update"""
    realtime_manager.emit_event(
        "queue_status_update",
        user_id,
        {
            "queue_position": position,
            "estimated_wait_time": estimated_time
        },
        channel="queue_updates",
        priority=2
    )

# Alias for compatibility
emit_queue_update = emit_queue_status_update

def emit_analytics_update(user_id: str, analytics_data: Dict[str, Any]):
    """Emit real-time analytics update"""
    realtime_manager.emit_event(
        "analytics_update",
        user_id,
        analytics_data,
        channel="analytics",
        priority=3
    )

def emit_system_notification(message: str, notification_type: str = "info"):
    """Emit system-wide notification"""
    realtime_manager.emit_event(
        "system_notification",
        "",  # No specific user
        {
            "message": message,
            "type": notification_type
        },
        channel="system",
        priority=1
    )

# Start server function for integration
def start_realtime_server(host: str = "localhost", port: int = 8765):
    """Start real-time server in background thread"""
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        realtime_manager.host = host
        realtime_manager.port = port
        loop.run_until_complete(realtime_manager.start_server())
    
    if WEBSOCKETS_AVAILABLE:
        thread = Thread(target=run_server, daemon=True)
        thread.start()
        logger.info(f"Started real-time server thread on {host}:{port}")
        return realtime_manager
    else:
        logger.warning("WebSockets not available - real-time features disabled")
        return None
