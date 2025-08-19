"""
Blog WebSocket consumers for real-time updates
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class PostConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for post updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'post_{self.post_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'post_view':
                # Track post view
                await self.track_post_view()
            
        except json.JSONDecodeError:
            pass
    
    async def post_update(self, event):
        """Send post update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'post_update',
            'data': event['data']
        }))
    
    async def post_stats_update(self, event):
        """Send post statistics update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'post_stats_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def track_post_view(self):
        """Track post view in database."""
        try:
            from .models import Post, PostView
            from django.utils import timezone
            
            post = Post.objects.get(id=self.post_id)
            
            # Create post view record
            PostView.objects.create(
                post=post,
                ip_address='127.0.0.1',  # Would get from scope in real implementation
                user_agent='WebSocket',
                user=self.scope['user'] if self.scope['user'].is_authenticated else None
            )
            
            # Update post view count
            post.view_count += 1
            post.save(update_fields=['view_count'])
            
        except Post.DoesNotExist:
            pass


class CommentConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for comment updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'comments_{self.post_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket."""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'typing_start':
                # Broadcast typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user': self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonymous',
                        'is_typing': True
                    }
                )
            elif message_type == 'typing_stop':
                # Stop typing indicator
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user': self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonymous',
                        'is_typing': False
                    }
                )
            
        except json.JSONDecodeError:
            pass
    
    async def comment_added(self, event):
        """Send new comment to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'comment_added',
            'data': event['data']
        }))
    
    async def comment_updated(self, event):
        """Send comment update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'comment_updated',
            'data': event['data']
        }))
    
    async def comment_deleted(self, event):
        """Send comment deletion to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'comment_deleted',
            'data': event['data']
        }))
    
    async def user_typing(self, event):
        """Send typing indicator to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user': event['user'],
            'is_typing': event['is_typing']
        }))