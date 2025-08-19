"""
Core WebSocket consumers for general functionality
"""

import json
import asyncio
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone


class BaseWebSocketConsumer(AsyncWebsocketConsumer):
    """Base WebSocket consumer with common functionality."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.heartbeat_task = None
        self.connection_time = None
    
    async def connect(self):
        """Handle WebSocket connection with authentication check."""
        # Check authentication
        if not await self.is_authenticated():
            await self.close(code=4001)  # Unauthorized
            return
        
        self.connection_time = timezone.now()
        await self.accept()
        
        # Start heartbeat
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        
        # Log connection
        await self.log_connection('connected')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Cancel heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Leave room group if exists
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        # Log disconnection
        await self.log_connection('disconnected', close_code)
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                await self.handle_message(data)
                
        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            await self.send_error(f'Error processing message: {str(e)}')
    
    async def handle_message(self, data):
        """Override this method to handle specific message types."""
        pass
    
    async def send_error(self, message):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_notification(self, notification_type, data):
        """Send notification to client."""
        await self.send(text_data=json.dumps({
            'type': notification_type,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def heartbeat_loop(self):
        """Send periodic heartbeat to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat',
                    'timestamp': timezone.now().isoformat()
                }))
        except asyncio.CancelledError:
            pass
    
    async def is_authenticated(self):
        """Check if user is authenticated."""
        return (
            self.scope['user'] and 
            not isinstance(self.scope['user'], AnonymousUser)
        )
    
    @database_sync_to_async
    def log_connection(self, action, close_code=None):
        """Log WebSocket connection events."""
        from .models import WebSocketConnection
        
        try:
            user = self.scope['user'] if not isinstance(self.scope['user'], AnonymousUser) else None
            
            WebSocketConnection.objects.create(
                user=user,
                channel_name=self.channel_name,
                action=action,
                close_code=close_code,
                consumer_class=self.__class__.__name__,
                connection_time=self.connection_time
            )
        except Exception:
            # Don't fail if logging fails
            pass


class NotificationConsumer(BaseWebSocketConsumer):
    """WebSocket consumer for general notifications."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        await super().connect()
        
        if self.scope['user'] and not isinstance(self.scope['user'], AnonymousUser):
            # Join user-specific notification group
            self.room_group_name = f'notifications_{self.scope["user"].id}'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Send welcome message
            await self.send_notification('welcome', {
                'message': 'Connected to notifications',
                'user': self.scope['user'].username
            })
    
    async def handle_message(self, data):
        """Handle specific message types."""
        message_type = data.get('type')
        
        if message_type == 'subscribe':
            # Subscribe to specific notification types
            notification_types = data.get('notification_types', [])
            await self.subscribe_to_notifications(notification_types)
        
        elif message_type == 'unsubscribe':
            # Unsubscribe from notification types
            notification_types = data.get('notification_types', [])
            await self.unsubscribe_from_notifications(notification_types)
    
    async def subscribe_to_notifications(self, notification_types):
        """Subscribe to specific notification types."""
        for notification_type in notification_types:
            group_name = f'notifications_{notification_type}'
            await self.channel_layer.group_add(group_name, self.channel_name)
        
        await self.send_notification('subscribed', {
            'notification_types': notification_types
        })
    
    async def unsubscribe_from_notifications(self, notification_types):
        """Unsubscribe from specific notification types."""
        for notification_type in notification_types:
            group_name = f'notifications_{notification_type}'
            await self.channel_layer.group_discard(group_name, self.channel_name)
        
        await self.send_notification('unsubscribed', {
            'notification_types': notification_types
        })
    
    # Group message handlers
    async def notification_message(self, event):
        """Handle notification messages from group."""
        await self.send_notification('notification', event['data'])
    
    async def blog_post_published(self, event):
        """Handle blog post published notifications."""
        await self.send_notification('blog_post_published', event['data'])
    
    async def comment_added(self, event):
        """Handle comment added notifications."""
        await self.send_notification('comment_added', event['data'])
    
    async def user_mentioned(self, event):
        """Handle user mention notifications."""
        await self.send_notification('user_mentioned', event['data'])


class HealthCheckConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for health checks and monitoring."""
    
    async def connect(self):
        """Accept connection for health checks."""
        await self.accept()
        
        # Send health status
        await self.send(text_data=json.dumps({
            'type': 'health_status',
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'server_time': timezone.now().isoformat()
        }))
    
    async def receive(self, text_data):
        """Handle health check requests."""
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'health_check':
                await self.send(text_data=json.dumps({
                    'type': 'health_response',
                    'status': 'healthy',
                    'timestamp': timezone.now().isoformat(),
                    'uptime': await self.get_uptime()
                }))
        except json.JSONDecodeError:
            pass
    
    @database_sync_to_async
    def get_uptime(self):
        """Get server uptime information."""
        # This would typically get actual server uptime
        return {
            'server_start': timezone.now().isoformat(),
            'current_time': timezone.now().isoformat()
        }