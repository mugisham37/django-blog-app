# WebSocket Implementation Guide

This document describes the Django Channels WebSocket implementation for real-time features.

## Overview

The WebSocket implementation provides real-time communication for:

- Blog post updates and notifications
- Comment system with typing indicators
- Real-time analytics dashboard
- System notifications and alerts
- Health monitoring

## Architecture

### Components

1. **ASGI Application** (`config/asgi.py`)

   - Handles both HTTP and WebSocket protocols
   - JWT authentication middleware for WebSockets
   - URL routing for different WebSocket endpoints

2. **Consumers** (`apps/*/consumers.py`)

   - `NotificationConsumer`: General notifications
   - `PostConsumer`: Post-specific updates
   - `CommentConsumer`: Comment system with typing indicators
   - `AnalyticsDashboardConsumer`: Real-time analytics
   - `HealthCheckConsumer`: System health monitoring

3. **Authentication** (`apps/core/websocket_auth.py`)

   - JWT token-based authentication for WebSocket connections
   - Token validation and user resolution

4. **Signal Handlers** (`apps/core/websocket_signals.py`)

   - Automatic broadcasting of model changes
   - Real-time notifications for blog posts, comments, etc.

5. **Utilities** (`apps/core/websocket_utils.py`)
   - WebSocket management and broadcasting utilities
   - Connection tracking and monitoring

## WebSocket Endpoints

### Authentication Required

All WebSocket endpoints require JWT authentication via query parameter:

```
ws://localhost:8000/ws/endpoint/?token=YOUR_JWT_TOKEN
```

### Available Endpoints

1. **Notifications**: `/ws/notifications/`

   - General user notifications
   - Subscription to specific notification types

2. **Post Updates**: `/ws/blog/posts/{post_id}/`

   - Real-time post statistics
   - Post content updates
   - View tracking

3. **Comments**: `/ws/blog/comments/{post_id}/`

   - Real-time comment updates
   - Typing indicators
   - Comment approval notifications

4. **Analytics Dashboard**: `/ws/analytics/dashboard/`

   - Real-time analytics data (staff only)
   - Live visitor counts
   - Page view statistics

5. **Health Check**: `/ws/health/`
   - System health monitoring
   - No authentication required

## Usage Examples

### JavaScript Client

```javascript
// Connect to notifications
const token = "your-jwt-token";
const ws = new WebSocket(
  `ws://localhost:8000/ws/notifications/?token=${token}`
);

ws.onopen = function (event) {
  console.log("Connected to notifications");

  // Subscribe to blog notifications
  ws.send(
    JSON.stringify({
      type: "subscribe",
      notification_types: ["blog_post_published", "comment_added"],
    })
  );
};

ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("Notification:", data);

  if (data.type === "notification") {
    showNotification(data.data);
  }
};

// Heartbeat to keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ping" }));
  }
}, 30000);
```

### Python Client

```python
import asyncio
import websockets
import json

async def connect_to_notifications():
    token = "your-jwt-token"
    uri = f"ws://localhost:8000/ws/notifications/?token={token}"

    async with websockets.connect(uri) as websocket:
        # Subscribe to notifications
        await websocket.send(json.dumps({
            'type': 'subscribe',
            'notification_types': ['blog_post_published']
        }))

        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(connect_to_notifications())
```

## Message Types

### Client to Server Messages

#### Notifications WebSocket

```json
{
    "type": "subscribe",
    "notification_types": ["blog_post_published", "comment_added"]
}

{
    "type": "unsubscribe",
    "notification_types": ["comment_added"]
}

{
    "type": "ping"
}
```

#### Post WebSocket

```json
{
    "type": "track_view"
}

{
    "type": "get_stats"
}

{
    "type": "subscribe_updates"
}
```

#### Comments WebSocket

```json
{
    "type": "typing_start"
}

{
    "type": "typing_stop"
}

{
    "type": "get_comments"
}
```

### Server to Client Messages

#### Common Messages

```json
{
    "type": "heartbeat",
    "timestamp": "2024-01-01T12:00:00Z"
}

{
    "type": "pong",
    "timestamp": "2024-01-01T12:00:00Z"
}

{
    "type": "error",
    "message": "Error description",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Notification Messages

```json
{
  "type": "notification",
  "data": {
    "notification_type": "blog_post_published",
    "title": "New Post: Sample Title",
    "message": "John published a new post: Sample Title",
    "icon": "post",
    "color": "blue",
    "data": {
      "post_id": "123",
      "title": "Sample Title",
      "author": "John"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Post Update Messages

```json
{
  "type": "post_stats",
  "data": {
    "view_count": 150,
    "comment_count": 5,
    "like_count": 12
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Comment Messages

```json
{
    "type": "comment_added",
    "data": {
        "id": "456",
        "post_id": "123",
        "content": "Great post!",
        "author": "Jane",
        "created_at": "2024-01-01T12:00:00Z"
    },
    "timestamp": "2024-01-01T12:00:00Z"
}

{
    "type": "user_typing",
    "data": {
        "user": "Jane",
        "is_typing": true,
        "typing_users": ["Jane", "Bob"]
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Configuration

### Django Settings

```python
# WebSocket Configuration
WEBSOCKET_SETTINGS = {
    'JWT_AUTH_REQUIRED': True,
    'HEARTBEAT_INTERVAL': 30,  # seconds
    'CONNECTION_TIMEOUT': 300,  # 5 minutes
    'MAX_CONNECTIONS_PER_USER': 10,
    'ENABLE_CONNECTION_TRACKING': True,
    'CLEANUP_INTERVAL': 3600,  # 1 hour
}

# Channel Layers (Redis)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}
```

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    # ... other JWT settings
}
```

## Deployment

### Development

1. Install Redis:

   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server

   # macOS
   brew install redis

   # Windows
   # Use Docker or WSL
   ```

2. Start Redis:

   ```bash
   redis-server
   ```

3. Run Django with ASGI:

   ```bash
   # Development
   python manage.py runserver

   # Production (use Daphne or Uvicorn)
   daphne -b 0.0.0.0 -p 8000 config.asgi:application
   ```

### Production

1. **Use Daphne or Uvicorn**:

   ```bash
   # Daphne
   daphne -b 0.0.0.0 -p 8000 config.asgi:application

   # Uvicorn
   uvicorn config.asgi:application --host 0.0.0.0 --port 8000
   ```

2. **Redis Cluster** for scaling:

   ```python
   CHANNEL_LAYERS = {
       'default': {
           'BACKEND': 'channels_redis.core.RedisChannelLayer',
           'CONFIG': {
               "hosts": [
                   ('redis-node-1', 6379),
                   ('redis-node-2', 6379),
                   ('redis-node-3', 6379),
               ],
           },
       },
   }
   ```

3. **Load Balancer Configuration**:

   ```nginx
   upstream websocket_backend {
       server 127.0.0.1:8000;
       server 127.0.0.1:8001;
   }

   server {
       location /ws/ {
           proxy_pass http://websocket_backend;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## Monitoring and Management

### Management Commands

1. **Monitor WebSocket connections**:

   ```bash
   python manage.py websocket_monitor --continuous --interval 30
   ```

2. **Cleanup old connection records**:
   ```bash
   python manage.py websocket_cleanup --hours 24
   ```

### Health Checks

```python
from apps.core.websocket_utils import check_websocket_health

health = check_websocket_health()
print(health)  # {'status': 'healthy', 'message': '...'}
```

### Connection Statistics

```python
from apps.core.websocket_utils import WebSocketManager

manager = WebSocketManager()
stats = manager.get_active_connections()
print(stats)
```

## Testing

### Unit Tests

```bash
# Run WebSocket tests
python manage.py test apps.core.tests.test_websocket_integration

# Run with coverage
coverage run --source='.' manage.py test apps.core.tests.test_websocket_integration
coverage report
```

### Manual Testing

Use the provided WebSocket client:

```bash
# Test all endpoints
python websocket_client_example.py --token YOUR_JWT_TOKEN --post-id 123

# Test specific endpoint
python websocket_client_example.py --test notifications --token YOUR_JWT_TOKEN
```

## Troubleshooting

### Common Issues

1. **Connection Refused**:

   - Check if Redis is running
   - Verify ASGI server is running (not just WSGI)
   - Check firewall settings

2. **Authentication Errors**:

   - Verify JWT token is valid and not expired
   - Check token is passed in query parameter
   - Ensure JWT settings are correct

3. **Messages Not Broadcasting**:

   - Check Redis connection
   - Verify signal handlers are registered
   - Check channel layer configuration

4. **Performance Issues**:
   - Monitor Redis memory usage
   - Check connection limits
   - Consider Redis clustering for scale

### Debug Mode

Enable WebSocket debugging:

```python
# settings.py
LOGGING = {
    'loggers': {
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Connection Limits

Monitor and limit connections:

```python
# In consumer connect method
from apps.core.websocket_utils import ConnectionTracker

user_connections = ConnectionTracker.get_user_connections(user.id)
if len(user_connections) >= settings.WEBSOCKET_SETTINGS['MAX_CONNECTIONS_PER_USER']:
    await self.close(code=4008)  # Policy violation
```

## Security Considerations

1. **Authentication**: All endpoints require valid JWT tokens
2. **Rate Limiting**: Implement connection limits per user
3. **Input Validation**: Validate all incoming WebSocket messages
4. **CORS**: Configure allowed origins for WebSocket connections
5. **Monitoring**: Log and monitor WebSocket connections for abuse

## Performance Tips

1. **Connection Pooling**: Use Redis connection pooling
2. **Message Batching**: Batch multiple updates when possible
3. **Selective Broadcasting**: Only send updates to relevant users
4. **Connection Cleanup**: Regularly clean up stale connections
5. **Monitoring**: Monitor Redis memory and connection counts
