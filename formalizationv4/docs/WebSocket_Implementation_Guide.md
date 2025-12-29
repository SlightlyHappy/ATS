# 🔌 WebSocket Implementation Guide

## Overview

This document outlines the WebSocket implementation for real-time queue updates and notifications in the AI Resume Analysis system.

## Features Implemented

### ✅ Core WebSocket Features
- **Real-time queue updates**: Live status changes for analysis queue items
- **Push notifications**: Browser notifications for completed analyses
- **Live dashboard**: Real-time statistics and monitoring
- **Admin monitoring**: Enhanced admin features with system oversight
- **Batch processing updates**: Real-time progress tracking for batch uploads

### ✅ WebSocket Events

#### Client → Server Events
- `authenticate`: Authenticate user and join appropriate rooms
- `join_queue_room`: Join queue-specific room for updates
- `leave_queue_room`: Leave queue-specific room
- `request_queue_status`: Request current queue status
- `request_dashboard_data`: Request admin dashboard data

#### Server → Client Events
- `connected`: Connection confirmation
- `authenticated`: Authentication success
- `auth_error`: Authentication failure
- `queue_item_update`: Individual queue item status change
- `queue_update`: General queue status update
- `analysis_completed`: Analysis completion notification
- `batch_update`: Batch processing progress update
- `push_notification`: Browser notification data
- `system_alert`: System-wide alerts
- `dashboard_data_update`: Admin dashboard data update

### ✅ REST API Endpoints

All endpoints are under `/api/v1/websocket/`:

- `GET /stats`: Real-time system statistics
- `GET /queue/live`: Live queue data for dashboard
- `GET /analytics/hourly`: Hourly analytics for last 24 hours
- `GET /analytics/users`: User analytics and activity
- `GET /system/health`: Detailed system health information
- `POST /broadcast/test`: Send test broadcast (admin)
- `POST /dashboard/refresh`: Trigger dashboard refresh (admin)

## Architecture

### WebSocket Service (`app/services/websocket_service.py`)
- Manages WebSocket connections and rooms
- Handles user authentication and authorization
- Provides notification methods for other services
- Tracks connected users and sessions

### Queue Service Integration
- Updated `QueueService` to send WebSocket notifications
- Notifications sent on status changes:
  - Queue position updates
  - Analysis start/completion
  - Batch progress updates
  - Failures and retries

### Room-based Architecture
- `user_{user_id}`: User-specific notifications
- `queue_{queue_id}`: Queue item-specific updates
- `queue_updates`: General queue updates
- `admin_dashboard`: Admin dashboard data
- `admin_notifications`: Admin-specific alerts

## Usage Examples

### Frontend Integration

```javascript
// Connect to WebSocket
const socket = io();

// Authenticate user
socket.emit('authenticate', {
    user_id: 'your-user-id',
    user_type: 'user' // or 'admin'
});

// Listen for queue updates
socket.on('queue_item_update', (data) => {
    console.log('Queue update:', data);
    updateQueueDisplay(data);
});

// Listen for analysis completion
socket.on('analysis_completed', (data) => {
    console.log('Analysis complete:', data);
    showNotification('Analysis Complete!');
});

// Request current queue status
socket.emit('request_queue_status', {
    user_id: 'your-user-id'
});
```

### Push Notifications

```javascript
// Request notification permission
Notification.requestPermission();

// Listen for push notification data
socket.on('push_notification', (data) => {
    if (Notification.permission === 'granted') {
        new Notification(data.title, {
            body: data.body,
            icon: data.icon,
            tag: 'resume-analysis'
        });
    }
});
```

### Admin Dashboard

```javascript
// Admin authentication
socket.emit('authenticate', {
    user_id: 'admin-user-id',
    user_type: 'admin'
});

// Request dashboard data
socket.emit('request_dashboard_data');

// Listen for dashboard updates
socket.on('dashboard_data_update', (data) => {
    updateDashboard(data);
});

// Send system alert
fetch('/api/v1/websocket/broadcast/test', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: 'System maintenance in 10 minutes',
        type: 'maintenance',
        level: 'warning'
    })
});
```

## Configuration

### Production Deployment
- Uses `eventlet` worker for Gunicorn
- Single worker required for WebSocket functionality
- CORS configured for cross-origin requests

### Environment Variables
```bash
# WebSocket configuration
FLASK_ENV=production
PORT=8000

# For Railway deployment
SERVICE_TYPE=web  # or 'worker' for background processing
```

### Requirements
```
Flask-SocketIO==5.3.6
eventlet==0.33.3
python-socketio[client]==5.8.0  # For testing
```

## Testing

### Manual Testing
Access the live dashboard at: `http://localhost:8000/api/v1/dashboard`

### Automated Testing
```bash
# Run WebSocket functionality tests
python test_websocket.py

# Run load test with multiple clients
python test_websocket.py --load-test --clients 10

# Test against remote server
python test_websocket.py --url https://your-app.railway.app
```

### Test Features
- Connection establishment
- User and admin authentication
- Queue status updates
- Real-time notifications
- Dashboard data flow
- Broadcast functionality
- Load testing with multiple clients

## Integration with Existing System

### Queue Service Updates
The `QueueService` class has been enhanced with WebSocket notification methods:
- `_notify_websocket_update()`: Send queue item updates
- `_notify_analysis_completed()`: Send completion notifications
- `_notify_batch_update()`: Send batch progress updates

### Model Enhancements
- Added `progress` property to `BatchUpload` model
- Enhanced `to_dict()` methods for better WebSocket data serialization
- Added completion tracking for real-time progress

### API Blueprint Registration
New WebSocket blueprint registered at `/api/v1/websocket/` for REST endpoints that complement WebSocket functionality.

## Security Considerations

### Authentication
- Users must authenticate before receiving notifications
- Room-based access control prevents unauthorized data access
- Admin features require explicit admin authentication

### Rate Limiting
- WebSocket connections respect existing Flask-Limiter configuration
- Connection limits prevent resource exhaustion
- Graceful disconnection handling

### Data Privacy
- Users only receive notifications for their own queue items
- Admin users have broader access but with audit trails
- No sensitive data transmitted over WebSocket without encryption

## Performance

### Scalability
- Room-based architecture allows efficient targeting
- Connection tracking prevents memory leaks
- Automatic cleanup of disconnected sessions

### Monitoring
- Connection statistics available via REST API
- Health checks include WebSocket system status
- Real-time metrics for admin dashboard

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check if server is running with eventlet worker
   - Verify CORS configuration
   - Check firewall/proxy settings

2. **Authentication Failed**
   - Ensure user exists in database
   - Check user_id format (UUID)
   - Verify user_type parameter

3. **No Notifications Received**
   - Confirm authentication success
   - Check room membership
   - Verify notification permissions

### Debug Tools
- Browser dev tools for WebSocket inspection
- Server logs show connection/disconnection events
- Test script provides comprehensive diagnostics

## Future Enhancements

### Planned Features
- File upload progress tracking via WebSocket
- Real-time collaboration features
- Advanced analytics streaming
- Mobile app push notification integration

### Scalability Improvements
- Redis adapter for multi-server deployments
- Connection pooling optimizations
- Advanced rate limiting per user type

---

## Implementation Summary

✅ **Completed Features:**
- WebSocket server with Flask-SocketIO
- Real-time queue status updates
- Push notification system
- Live admin dashboard backend
- Comprehensive testing suite
- Production-ready configuration

🎯 **Key Benefits:**
- Immediate user feedback on queue status
- Reduced API polling overhead
- Enhanced user experience with real-time updates
- Comprehensive admin monitoring capabilities
- Browser push notifications for better engagement

This implementation fulfills the roadmap requirements for:
- ✅ **WebSocket Implementation**: Real-time queue updates and notifications
- ✅ **Live Dashboard Backend**: WebSocket endpoints for real-time data
- ✅ **Push Notifications**: Browser notifications for completed analyses
