"""
WebSocket utility functions and management
"""

import json
import asyncio
from typing import Dict, List, Optional
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache


class WebSocketManager:
    """Manage WebSocket connections and broadcasting."""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def broadcast_to_group(self, group_name: str, message_type: str, data: dict):
        """Broadcast message to a WebSocket group."""
        if not self.channel_layer:
            return False
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    'data': data,
                    'timestamp': timezone.now().isoformat()
                }
            )
            return True
        except Exception as e:
            # Log error but don't fail
            print(f"WebSocket broadcast error: {e}")
            return False
    
    def broadcast_to_user(self, user_id: int, message_type: str, data: dict):
        """Broadcast message to a specific user."""
        group_name = f'notifications_{user_id}'
        return self.broadcast_to_group(group_name, message_type, data)
    
    def broadcast_to_users(self, user_ids: List[int], message_type: str, data: dict):
        """Broadcast message to multiple users."""
        results = []
        for user_id in user_ids:
            result = self.broadcast_to_user(user_id, message_type, data)
            results.append(result)
        return all(results)
    
    def broadcast_notification(self, notification_type: str, data: dict, 
                             user_id: Optional[int] = None, 
                             user_ids: Optional[List[int]] = None):
        """Broadcast notification with template rendering."""
        from .models import NotificationTemplate
        
        try:
            # Get notification template
            template = NotificationTemplate.objects.get(
                notification_type=notification_type,
                is_active=True
            )
            
            # Render notification
            rendered = template.render(data)
            
            notification_data = {
                'notification_type': notification_type,
                'title': rendered['title'],
                'message': rendered['message'],
                'icon': rendered['icon'],
                'color': rendered['color'],
                'sound': rendered['sound'],
                'auto_dismiss_seconds': rendered['auto_dismiss_seconds'],
                'data': data
            }
            
            # Broadcast to specific users
            if user_id:
                return self.broadcast_to_user(user_id, 'notification_message', notification_data)
            elif user_ids:
                return self.broadcast_to_users(user_ids, 'notification_message', notification_data)
            else:
                # Broadcast to general notification group
                return self.broadcast_to_group(
                    f'notifications_{notification_type}', 
                    'notification_message', 
                    notification_data
                )
        
        except NotificationTemplate.DoesNotExist:
            # Fallback to simple notification
            simple_data = {
                'notification_type': notification_type,
                'title': notification_type.replace('_', ' ').title(),
                'message': str(data),
                'data': data
            }
            
            if user_id:
                return self.broadcast_to_user(user_id, 'notification_message', simple_data)
            elif user_ids:
                return self.broadcast_to_users(user_ids, 'notification_message', simple_data)
            else:
                return self.broadcast_to_group(
                    f'notifications_{notification_type}', 
                    'notification_message', 
                    simple_data
                )
    
    def get_active_connections(self) -> Dict:
        """Get statistics about active WebSocket connections."""
        from .models import WebSocketConnection
        from datetime import timedelta
        
        # Get connections from last hour
        recent_time = timezone.now() - timedelta(hours=1)
        
        connections = WebSocketConnection.objects.filter(
            timestamp__gte=recent_time,
            action='connected'
        )
        
        stats = {
            'total_connections': connections.count(),
            'unique_users': connections.filter(user__isnull=False).values('user').distinct().count(),
            'anonymous_connections': connections.filter(user__isnull=True).count(),
            'by_consumer': {}
        }
        
        # Group by consumer class
        for connection in connections:
            consumer = connection.consumer_class
            if consumer not in stats['by_consumer']:
                stats['by_consumer'][consumer] = 0
            stats['by_consumer'][consumer] += 1
        
        return stats
    
    def cleanup_old_connections(self, hours: int = 24):
        """Clean up old WebSocket connection records."""
        from .models import WebSocketConnection
        from datetime import timedelta
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        deleted_count = WebSocketConnection.objects.filter(
            timestamp__lt=cutoff_time
        ).delete()[0]
        
        return deleted_count


class ConnectionTracker:
    """Track active WebSocket connections in cache."""
    
    CACHE_PREFIX = 'ws_connections'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def add_connection(cls, user_id: Optional[int], channel_name: str, 
                      consumer_class: str, extra_data: Optional[Dict] = None):
        """Add connection to tracker."""
        connection_key = f"{cls.CACHE_PREFIX}:{channel_name}"
        connection_data = {
            'user_id': user_id,
            'channel_name': channel_name,
            'consumer_class': consumer_class,
            'connected_at': timezone.now().isoformat(),
            'extra_data': extra_data or {}
        }
        
        cache.set(connection_key, connection_data, cls.CACHE_TIMEOUT)
        
        # Add to user's connection list
        if user_id:
            user_connections_key = f"{cls.CACHE_PREFIX}:user:{user_id}"
            user_connections = cache.get(user_connections_key, [])
            if channel_name not in user_connections:
                user_connections.append(channel_name)
                cache.set(user_connections_key, user_connections, cls.CACHE_TIMEOUT)
    
    @classmethod
    def remove_connection(cls, channel_name: str):
        """Remove connection from tracker."""
        connection_key = f"{cls.CACHE_PREFIX}:{channel_name}"
        connection_data = cache.get(connection_key)
        
        if connection_data:
            user_id = connection_data.get('user_id')
            
            # Remove from user's connection list
            if user_id:
                user_connections_key = f"{cls.CACHE_PREFIX}:user:{user_id}"
                user_connections = cache.get(user_connections_key, [])
                if channel_name in user_connections:
                    user_connections.remove(channel_name)
                    cache.set(user_connections_key, user_connections, cls.CACHE_TIMEOUT)
            
            # Remove connection data
            cache.delete(connection_key)
    
    @classmethod
    def get_user_connections(cls, user_id: int) -> List[Dict]:
        """Get all connections for a user."""
        user_connections_key = f"{cls.CACHE_PREFIX}:user:{user_id}"
        channel_names = cache.get(user_connections_key, [])
        
        connections = []
        for channel_name in channel_names:
            connection_key = f"{cls.CACHE_PREFIX}:{channel_name}"
            connection_data = cache.get(connection_key)
            if connection_data:
                connections.append(connection_data)
        
        return connections
    
    @classmethod
    def get_connection_stats(cls) -> Dict:
        """Get connection statistics."""
        # This would require scanning cache keys, which is not efficient
        # In production, consider using Redis sets or other data structures
        return {
            'message': 'Connection stats require Redis-specific implementation'
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()


# Utility functions
def send_notification_to_user(user_id: int, notification_type: str, data: dict):
    """Send notification to a specific user."""
    return ws_manager.broadcast_notification(notification_type, data, user_id=user_id)


def send_notification_to_users(user_ids: List[int], notification_type: str, data: dict):
    """Send notification to multiple users."""
    return ws_manager.broadcast_notification(notification_type, data, user_ids=user_ids)


def broadcast_system_message(message: str, level: str = 'info'):
    """Broadcast system-wide message."""
    data = {
        'message': message,
        'level': level,
        'timestamp': timezone.now().isoformat()
    }
    return ws_manager.broadcast_to_group('system_messages', 'system_message', data)


def notify_post_published(post):
    """Notify users when a new post is published."""
    data = {
        'post_id': str(post.id),
        'title': post.title,
        'slug': post.slug,
        'author': post.author.username,
        'published_at': post.published_at.isoformat() if post.published_at else None
    }
    
    return ws_manager.broadcast_notification('blog_post_published', data)


def notify_comment_added(comment):
    """Notify users when a comment is added."""
    data = {
        'comment_id': str(comment.id),
        'post_id': str(comment.post.id),
        'post_title': comment.post.title,
        'author': comment.author.username if comment.author else 'Anonymous',
        'content_preview': comment.content[:100] + '...' if len(comment.content) > 100 else comment.content
    }
    
    # Notify post author
    if comment.post.author != comment.author:
        return ws_manager.broadcast_notification('comment_added', data, user_id=comment.post.author.id)
    
    return True


def check_websocket_health():
    """Check WebSocket system health."""
    channel_layer = get_channel_layer()
    
    if not channel_layer:
        return {
            'status': 'error',
            'message': 'Channel layer not configured'
        }
    
    try:
        # Test basic functionality
        async_to_sync(channel_layer.group_send)(
            'health_check',
            {
                'type': 'health_test',
                'data': {'test': True}
            }
        )
        
        return {
            'status': 'healthy',
            'message': 'WebSocket system operational',
            'channel_layer': str(type(channel_layer).__name__)
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': f'WebSocket system error: {str(e)}'
        }