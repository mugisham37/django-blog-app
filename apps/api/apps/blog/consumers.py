"""
Blog WebSocket consumers for real-time updates
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from apps.core.consumers import BaseWebSocketConsumer


class PostConsumer(BaseWebSocketConsumer):
    """WebSocket consumer for post updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'post_{self.post_id}'
        
        # Check if post exists
        if not await self.post_exists():
            await self.close(code=4004)  # Not found
            return
        
        await super().connect()
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Send initial post data
        post_data = await self.get_post_data()
        await self.send_notification('post_data', post_data)
        
        # Track connection
        await self.track_post_connection('connected')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.track_post_connection('disconnected')
        await super().disconnect(close_code)
    
    async def handle_message(self, data):
        """Handle specific message types."""
        message_type = data.get('type')
        
        if message_type == 'track_view':
            await self.track_post_view()
        elif message_type == 'get_stats':
            stats = await self.get_post_stats()
            await self.send_notification('post_stats', stats)
        elif message_type == 'subscribe_updates':
            # Subscribe to post updates
            await self.send_notification('subscribed', {'post_id': self.post_id})
    
    @database_sync_to_async
    def post_exists(self):
        """Check if post exists."""
        from .models import Post
        return Post.objects.filter(id=self.post_id).exists()
    
    @database_sync_to_async
    def get_post_data(self):
        """Get post data."""
        from .models import Post
        try:
            post = Post.objects.select_related('author', 'category').get(id=self.post_id)
            return {
                'id': str(post.id),
                'title': post.title,
                'slug': post.slug,
                'author': post.author.username,
                'category': post.category.name if post.category else None,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'view_count': getattr(post, 'view_count', 0),
                'comment_count': post.comments.filter(is_approved=True).count()
            }
        except Post.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_post_stats(self):
        """Get post statistics."""
        from .models import Post
        try:
            post = Post.objects.get(id=self.post_id)
            return {
                'view_count': getattr(post, 'view_count', 0),
                'comment_count': post.comments.filter(is_approved=True).count(),
                'like_count': getattr(post, 'like_count', 0),
                'share_count': getattr(post, 'share_count', 0)
            }
        except Post.DoesNotExist:
            return None
    
    @database_sync_to_async
    def track_post_view(self):
        """Track post view in database."""
        from .models import Post
        from apps.analytics.models import PageView
        
        try:
            post = Post.objects.get(id=self.post_id)
            
            # Create page view record
            PageView.objects.create(
                url=f'/posts/{post.slug}/',
                user=self.scope['user'] if not isinstance(self.scope['user'], AnonymousUser) else None,
                ip_address='127.0.0.1',  # Would get from headers in real implementation
                user_agent='WebSocket Client',
                referrer='',
                post=post
            )
            
            # Update post view count if it has this field
            if hasattr(post, 'view_count'):
                post.view_count += 1
                post.save(update_fields=['view_count'])
            
            return True
        except Post.DoesNotExist:
            return False
    
    @database_sync_to_async
    def track_post_connection(self, action):
        """Track post WebSocket connections."""
        from apps.core.models import WebSocketConnection
        
        try:
            WebSocketConnection.objects.create(
                user=self.scope['user'] if not isinstance(self.scope['user'], AnonymousUser) else None,
                channel_name=self.channel_name,
                consumer_class=self.__class__.__name__,
                action=action,
                connection_time=self.connection_time,
                extra_data={'post_id': self.post_id}
            )
        except Exception:
            pass
    
    # Group message handlers
    async def post_update(self, event):
        """Send post update to WebSocket."""
        await self.send_notification('post_update', event['data'])
    
    async def post_stats_update(self, event):
        """Send post statistics update to WebSocket."""
        await self.send_notification('post_stats_update', event['data'])
    
    async def post_published(self, event):
        """Send post published notification."""
        await self.send_notification('post_published', event['data'])


class CommentConsumer(BaseWebSocketConsumer):
    """WebSocket consumer for comment updates."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.typing_users = set()
        self.typing_timeout_task = None
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'comments_{self.post_id}'
        
        # Check if post exists
        if not await self.post_exists():
            await self.close(code=4004)  # Not found
            return
        
        await super().connect()
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Send initial comment data
        comments_data = await self.get_comments_data()
        await self.send_notification('comments_data', comments_data)
    
    async def handle_message(self, data):
        """Handle specific message types."""
        message_type = data.get('type')
        user = self.scope['user']
        
        if message_type == 'typing_start' and not isinstance(user, AnonymousUser):
            await self.handle_typing_start()
        elif message_type == 'typing_stop' and not isinstance(user, AnonymousUser):
            await self.handle_typing_stop()
        elif message_type == 'get_comments':
            comments_data = await self.get_comments_data()
            await self.send_notification('comments_data', comments_data)
    
    async def handle_typing_start(self):
        """Handle typing start event."""
        user = self.scope['user']
        username = user.username
        
        # Add user to typing set
        self.typing_users.add(username)
        
        # Broadcast typing indicator
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user': username,
                'is_typing': True,
                'typing_users': list(self.typing_users)
            }
        )
        
        # Set timeout to auto-stop typing
        if self.typing_timeout_task:
            self.typing_timeout_task.cancel()
        
        self.typing_timeout_task = asyncio.create_task(
            self.auto_stop_typing(username)
        )
    
    async def handle_typing_stop(self):
        """Handle typing stop event."""
        user = self.scope['user']
        username = user.username
        
        # Remove user from typing set
        self.typing_users.discard(username)
        
        # Cancel timeout task
        if self.typing_timeout_task:
            self.typing_timeout_task.cancel()
        
        # Broadcast typing stop
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user': username,
                'is_typing': False,
                'typing_users': list(self.typing_users)
            }
        )
    
    async def auto_stop_typing(self, username):
        """Auto-stop typing after timeout."""
        try:
            await asyncio.sleep(10)  # 10 second timeout
            self.typing_users.discard(username)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user': username,
                    'is_typing': False,
                    'typing_users': list(self.typing_users)
                }
            )
        except asyncio.CancelledError:
            pass
    
    @database_sync_to_async
    def post_exists(self):
        """Check if post exists."""
        from .models import Post
        return Post.objects.filter(id=self.post_id).exists()
    
    @database_sync_to_async
    def get_comments_data(self):
        """Get comments data for the post."""
        from .models import Post
        try:
            post = Post.objects.get(id=self.post_id)
            comments = post.comments.filter(is_approved=True).select_related('author').order_by('-created_at')[:50]
            
            return {
                'post_id': str(self.post_id),
                'comment_count': comments.count(),
                'comments': [
                    {
                        'id': str(comment.id),
                        'content': comment.content,
                        'author': comment.author.username if comment.author else 'Anonymous',
                        'created_at': comment.created_at.isoformat(),
                        'is_approved': comment.is_approved
                    }
                    for comment in comments
                ]
            }
        except Post.DoesNotExist:
            return None
    
    # Group message handlers
    async def comment_added(self, event):
        """Send new comment to WebSocket."""
        await self.send_notification('comment_added', event['data'])
    
    async def comment_updated(self, event):
        """Send comment update to WebSocket."""
        await self.send_notification('comment_updated', event['data'])
    
    async def comment_deleted(self, event):
        """Send comment deletion to WebSocket."""
        await self.send_notification('comment_deleted', event['data'])
    
    async def comment_approved(self, event):
        """Send comment approval notification."""
        await self.send_notification('comment_approved', event['data'])
    
    async def user_typing(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator to the user who is typing
        if event['user'] != (self.scope['user'].username if not isinstance(self.scope['user'], AnonymousUser) else ''):
            await self.send_notification('user_typing', {
                'user': event['user'],
                'is_typing': event['is_typing'],
                'typing_users': event.get('typing_users', [])
            })