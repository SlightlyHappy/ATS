# 🚀 WebSocket Features Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Application
```bash
# Development mode
python run.py

# Production mode (Railway)
python start.py
```

### 3. Access Features

#### Live Dashboard
Open your browser to: `http://localhost:8000/api/v1/dashboard`

#### Test WebSocket Connection
```bash
python test_websocket.py
```

#### Test with Load
```bash
python test_websocket.py --load-test --clients 5
```

## Features Available

### ✅ Real-time Queue Updates
- Live queue position changes
- Processing status updates
- Completion notifications
- Error handling with retries

### ✅ Push Notifications
- Browser notifications for completed analyses
- Batch processing completion alerts
- System maintenance notifications
- Customizable notification preferences

### ✅ Live Dashboard Backend
- Real-time system statistics
- Queue monitoring with live updates
- User activity tracking
- Performance metrics
- System health monitoring

### ✅ Admin Features
- Real-time dashboard data streaming
- System alerts and broadcasts
- Connected user monitoring
- Queue management controls

## API Endpoints

### WebSocket Events
```javascript
// Connect and authenticate
socket.emit('authenticate', {
    user_id: 'your-user-id',
    user_type: 'user' // or 'admin'
});

// Get queue status
socket.emit('request_queue_status', {
    user_id: 'your-user-id'
});

// Admin dashboard data
socket.emit('request_dashboard_data');
```

### REST Endpoints
```bash
# System statistics
GET /api/v1/websocket/stats

# Live queue data
GET /api/v1/websocket/queue/live

# Analytics
GET /api/v1/websocket/analytics/hourly
GET /api/v1/websocket/analytics/users

# System health
GET /api/v1/websocket/system/health

# Admin functions
POST /api/v1/websocket/broadcast/test
POST /api/v1/websocket/dashboard/refresh
```

## Production Deployment

### Railway Configuration
The application is already configured for Railway deployment with:
- Eventlet worker for WebSocket support
- CORS configuration for cross-origin requests
- Health checks and monitoring
- Auto-scaling support

### Environment Variables
```bash
FLASK_ENV=production
PORT=8000
SERVICE_TYPE=web
```

## Integration Examples

### Frontend JavaScript
```javascript
// Basic WebSocket connection
const socket = io();

// Authentication
socket.emit('authenticate', {
    user_id: 'user-123',
    user_type: 'user'
});

// Queue updates
socket.on('queue_item_update', (data) => {
    updateQueueDisplay(data);
});

// Analysis completion
socket.on('analysis_completed', (data) => {
    showNotification('Analysis Complete!');
});

// Push notifications
socket.on('push_notification', (data) => {
    new Notification(data.title, {
        body: data.body,
        icon: data.icon
    });
});
```

### Python Client
```python
import socketio

sio = socketio.Client()

@sio.event
def queue_item_update(data):
    print(f"Queue update: {data}")

sio.connect('http://localhost:8000')
sio.emit('authenticate', {
    'user_id': 'user-123',
    'user_type': 'user'
})
```

## Testing

### Manual Testing
1. Open the dashboard: `http://localhost:8000/api/v1/dashboard`
2. Enter a test user ID and authenticate
3. Upload a resume via the API
4. Watch real-time updates in the dashboard

### Automated Testing
```bash
# Run comprehensive tests
python test_websocket.py

# Test specific features
python test_websocket.py --url http://localhost:8000

# Load testing
python test_websocket.py --load-test --clients 10
```

## Troubleshooting

### Common Issues

#### WebSocket Connection Failed
- Ensure server is running with eventlet worker
- Check if port 8000 is accessible
- Verify CORS configuration

#### No Real-time Updates
- Confirm user authentication
- Check WebSocket event listeners
- Verify user has queue items

#### Push Notifications Not Working
- Grant notification permission in browser
- Check HTTPS requirement for some browsers
- Verify notification event handling

### Debug Steps
1. Check browser console for errors
2. Monitor server logs for WebSocket events
3. Use the test script for diagnostics
4. Verify database connectivity

## Next Steps

With WebSocket implementation complete, the next priorities are:

1. **Admin Dashboard Frontend**: Web interface for the live dashboard backend
2. **Enhanced Analytics**: More detailed user behavior tracking
3. **Mobile Integration**: Push notifications for mobile apps
4. **Advanced Features**: Real-time collaboration, live chat support

---

## 🎉 Implementation Complete!

The WebSocket implementation provides:
- ✅ Real-time queue updates and notifications
- ✅ Live dashboard backend with streaming data
- ✅ Browser push notifications for completed analyses
- ✅ Admin monitoring and system alerts
- ✅ Production-ready configuration
- ✅ Comprehensive testing suite

This completes the high-priority real-time infrastructure requirements from the project roadmap!
