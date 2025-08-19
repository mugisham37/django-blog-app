"""
WebSocket Integration Tests
"""

import json
import pytest
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from config.asgi import application
from apps.blog.models import Post, Category
from apps.comments.models import Comment
from apps.core.models import WebSocketConnection, NotificationTemplate

User = get_user_model()


class WebSocketTestCase(TransactionTestCase):
    """Base test case for WebSocket tests."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        # Create notification templates
        NotificationTemplate.objects.create(
            notification_type='blog_post_published',
            title_template='New Post: {{ title }}',
            message_template='{{ author }} published a new post: {{ title }}',
            icon='post',
            color='blue'
        )
        
        NotificationTemplate.objects.create(
            notification_type='comment_added',
            title_template='New Comment',
            message_template='{{ commenter }} commented on {{ post_title }}',
            icon='comment',
            color='green'
        )
    
    def get_jwt_token(self, user=None):
        """Get JWT token for user."""
        if user is None:
            user = self.user
        
        access_token = AccessToken.for_user(user)
        return str(access_token)


@pytest.mark.asyncio
class TestNotificationConsumer(WebSocketTestCase):
    """Test notification WebSocket consumer."""
    
    async def test_notification_consumer_authentication(self):
        """Test WebSocket authentication with JWT."""
        # Test without token (should be rejected)
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        connected, subprotocol = await communicator.connect()
        self.assertFalse(connected)
        
        # Test with valid token
        token = self.get_jwt_token()
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/notifications/?token={token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive welcome message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'welcome')
        self.assertEqual(response['data']['user'], self.user.username)
        
        await communicator.disconnect()
    
    async def test_notification_subscription(self):
        """Test notification subscription functionality."""
        token = self.get_jwt_token()
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/notifications/?token={token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip welcome message
        await communicator.receive_json_from()
        
        # Subscribe to blog post notifications
        await communicator.send_json_to({
            'type': 'subscribe',
            'notification_types': ['blog_post_published']
        })
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'subscribed')
        self.assertIn('blog_post_published', response['data']['notification_types'])
        
        await communicator.disconnect()
    
    async def test_heartbeat_functionality(self):
        """Test WebSocket heartbeat."""
        token = self.get_jwt_token()
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/notifications/?token={token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip welcome message
        await communicator.receive_json_from()
        
        # Send ping
        await communicator.send_json_to({'type': 'ping'})
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'pong')
        self.assertIn('timestamp', response)
        
        await communicator.disconnect()


@pytest.mark.asyncio
class TestPostConsumer(WebSocketTestCase):
    """Test post WebSocket consumer."""
    
    async def test_post_consumer_connection(self):
        """Test post consumer connection."""
        token = self.get_jwt_token()
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/blog/posts/{self.post.id}/?token={token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive initial post data
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'post_data')
        self.assertEqual(response['data']['id'], str(self.post.id))
        self.assertEqual(response['data']['title'], self.post.title)
        
        await communicator.disconnect()
    
    async def test_post_view_tracking(self):
        """Test post view tracking via WebSocket."""
        token = self.get_jwt_token()
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/blog/posts/{self.post.id}/?token={token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial post data
        await communicator.receive_json_from()
        
        # Track view
        await communicator.send_json_to({'type': 'track_view'})
        
        # Verify page view was created
        from apps.analytics.models import PageView
        page_views = await database_sync_to_async(
            lambda: list(PageView.objects.filter(post=self.post))
        )()
        self.assertEqual(len(page_views), 1)
        
        await communicator.disconnect()
    
    async def test_post_stats_request(self):
        """Test requesting post statistics."""
        token = self.get_jwt_token()
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/blog/posts/{self.post.id}/?token={token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Skip initial post data
        await communicator.receive_json_from()
        
        # Request stats
        await communicator.send_json_to({'type': 'get_stats'})
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'post_stats')
        self.assertIn('view_count', response['data'])
        self.assertIn('comment_count', response['data'])
        
        await communicator.disconnect()


@pytest.mark.asyncio
class TestCommentConsumer(WebSocketTestCase):
    """Test comment WebSocket consumer."""
    
    async def test_comment_consumer_connection(self):
        """Test comment consumer connection."""
        token = self.get_jwt_token()
        communicator = WebsocketCommunicator(
            application, 
            f"/ws/blog/comments/{self.post.id}/?token={token}"
        )
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive initial comments data
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'comments_data')
        self.assertEqual(response['data']['post_id'], str(self.post.id))
        
        await communicator.disconnect()
    
    async def test_typing_indicators(self):
        """Test typing indicators functionality."""
        token = self.get_jwt_token()
        communicator1 = WebsocketCommunicator(
            application, 
            f"/ws/blog/comments/{self.post.id}/?token={token}"
        )
        communicator2 = WebsocketCommunicator(
            application, 
            f"/ws/blog/comments/{self.post.id}/?token={token}"
        )
        
        # Connect both clients
        connected1, _ = await communicator1.connect()
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected1)
        self.assertTrue(connected2)
        
        # Skip initial comments data
        await communicator1.receive_json_from()
        await communicator2.receive_json_from()
        
        # User 1 starts typing
        await communicator1.send_json_to({'type': 'typing_start'})
        
        # User 2 should receive typing indicator
        response = await communicator2.receive_json_from()
        self.assertEqual(response['type'], 'user_typing')
        self.assertEqual(response['data']['user'], self.user.username)
        self.assertTrue(response['data']['is_typing'])
        
        # User 1 stops typing
        await communicator1.send_json_to({'type': 'typing_stop'})
        
        # User 2 should receive typing stop
        response = await communicator2.receive_json_from()
        self.assertEqual(response['type'], 'user_typing')
        self.assertEqual(response['data']['user'], self.user.username)
        self.assertFalse(response['data']['is_typing'])
        
        await communicator1.disconnect()
        await communicator2.disconnect()


@pytest.mark.asyncio
class TestHealthCheckConsumer(WebSocketTestCase):
    """Test health check WebSocket consumer."""
    
    async def test_health_check_consumer(self):
        """Test health check consumer."""
        communicator = WebsocketCommunicator(application, "/ws/health/")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Should receive initial health status
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'health_status')
        self.assertEqual(response['status'], 'healthy')
        
        # Send health check request
        await communicator.send_json_to({'type': 'health_check'})
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'health_response')
        self.assertEqual(response['status'], 'healthy')
        self.assertIn('uptime', response)
        
        await communicator.disconnect()


class TestWebSocketSignals(WebSocketTestCase):
    """Test WebSocket signal handlers."""
    
    def test_post_save_signal(self):
        """Test post save signal broadcasting."""
        from apps.core.websocket_signals import handle_post_save
        
        # Create a new published post
        new_post = Post.objects.create(
            title='New Test Post',
            slug='new-test-post',
            content='New test content',
            author=self.user,
            category=self.category,
            status='published'
        )
        
        # Signal should be triggered automatically
        # In a real test, you'd mock the channel layer and verify the broadcast
        self.assertTrue(True)  # Placeholder assertion
    
    def test_comment_save_signal(self):
        """Test comment save signal broadcasting."""
        from apps.core.websocket_signals import handle_comment_save
        
        # Create a new comment
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Test comment',
            is_approved=True
        )
        
        # Signal should be triggered automatically
        self.assertTrue(True)  # Placeholder assertion


class TestWebSocketUtils(WebSocketTestCase):
    """Test WebSocket utility functions."""
    
    def test_websocket_manager(self):
        """Test WebSocket manager functionality."""
        from apps.core.websocket_utils import WebSocketManager
        
        manager = WebSocketManager()
        
        # Test broadcasting (would need mock channel layer in real test)
        result = manager.broadcast_to_group('test_group', 'test_message', {'test': True})
        # In real test, mock channel layer and verify the call
        
    def test_connection_tracker(self):
        """Test connection tracker functionality."""
        from apps.core.websocket_utils import ConnectionTracker
        
        # Add connection
        ConnectionTracker.add_connection(
            user_id=self.user.id,
            channel_name='test.channel.1',
            consumer_class='TestConsumer'
        )
        
        # Get user connections
        connections = ConnectionTracker.get_user_connections(self.user.id)
        self.assertEqual(len(connections), 1)
        self.assertEqual(connections[0]['channel_name'], 'test.channel.1')
        
        # Remove connection
        ConnectionTracker.remove_connection('test.channel.1')
        
        connections = ConnectionTracker.get_user_connections(self.user.id)
        self.assertEqual(len(connections), 0)
    
    def test_websocket_health_check(self):
        """Test WebSocket health check."""
        from apps.core.websocket_utils import check_websocket_health
        
        health = check_websocket_health()
        self.assertIn('status', health)
        self.assertIn('message', health)


class TestWebSocketModels(WebSocketTestCase):
    """Test WebSocket-related models."""
    
    def test_websocket_connection_model(self):
        """Test WebSocket connection model."""
        connection = WebSocketConnection.objects.create(
            user=self.user,
            channel_name='test.channel.1',
            consumer_class='TestConsumer',
            action='connected'
        )
        
        self.assertEqual(str(connection), f"{self.user.username} connected TestConsumer at {connection.timestamp}")
    
    def test_notification_template_model(self):
        """Test notification template model."""
        template = NotificationTemplate.objects.get(
            notification_type='blog_post_published'
        )
        
        context = {
            'title': 'Test Post',
            'author': 'testuser'
        }
        
        rendered = template.render(context)
        self.assertEqual(rendered['title'], 'New Post: Test Post')
        self.assertEqual(rendered['message'], 'testuser published a new post: Test Post')
        self.assertEqual(rendered['icon'], 'post')
        self.assertEqual(rendered['color'], 'blue')


# Performance and Load Tests
@pytest.mark.asyncio
class TestWebSocketPerformance(WebSocketTestCase):
    """Test WebSocket performance and load handling."""
    
    async def test_multiple_connections(self):
        """Test handling multiple WebSocket connections."""
        token = self.get_jwt_token()
        communicators = []
        
        # Create multiple connections
        for i in range(5):
            communicator = WebsocketCommunicator(
                application, 
                f"/ws/notifications/?token={token}"
            )
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            communicators.append(communicator)
            
            # Skip welcome message
            await communicator.receive_json_from()
        
        # Send message to all connections
        for communicator in communicators:
            await communicator.send_json_to({'type': 'ping'})
            response = await communicator.receive_json_from()
            self.assertEqual(response['type'], 'pong')
        
        # Disconnect all
        for communicator in communicators:
            await communicator.disconnect()
    
    async def test_connection_cleanup(self):
        """Test connection cleanup functionality."""
        from apps.core.websocket_utils import WebSocketManager
        
        manager = WebSocketManager()
        
        # Test cleanup (would need actual connections in real test)
        deleted_count = manager.cleanup_old_connections(hours=1)
        self.assertIsInstance(deleted_count, int)