#!/usr/bin/env python3
"""
WebSocket Client Example for Testing Django Channels Implementation

This script demonstrates how to connect to the WebSocket endpoints
and test the real-time functionality.

Usage:
    python websocket_client_example.py --token YOUR_JWT_TOKEN
"""

import asyncio
import websockets
import json
import argparse
from datetime import datetime


class WebSocketClient:
    """Simple WebSocket client for testing."""
    
    def __init__(self, base_url="ws://localhost:8000"):
        self.base_url = base_url
        self.token = None
    
    def set_token(self, token):
        """Set JWT token for authentication."""
        self.token = token
    
    async def connect_to_notifications(self):
        """Connect to notifications WebSocket."""
        url = f"{self.base_url}/ws/notifications/"
        if self.token:
            url += f"?token={self.token}"
        
        print(f"Connecting to notifications: {url}")
        
        try:
            async with websockets.connect(url) as websocket:
                print("✅ Connected to notifications WebSocket")
                
                # Listen for messages
                async def listen():
                    async for message in websocket:
                        data = json.loads(message)
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Notification: {data}")
                
                # Send test messages
                async def send_test_messages():
                    await asyncio.sleep(2)
                    
                    # Subscribe to blog notifications
                    await websocket.send(json.dumps({
                        'type': 'subscribe',
                        'notification_types': ['blog_post_published', 'comment_added']
                    }))
                    
                    await asyncio.sleep(2)
                    
                    # Send ping
                    await websocket.send(json.dumps({'type': 'ping'}))
                
                # Run both tasks
                await asyncio.gather(listen(), send_test_messages())
        
        except Exception as e:
            print(f"❌ Error connecting to notifications: {e}")
    
    async def connect_to_post(self, post_id):
        """Connect to post WebSocket."""
        url = f"{self.base_url}/ws/blog/posts/{post_id}/"
        if self.token:
            url += f"?token={self.token}"
        
        print(f"Connecting to post {post_id}: {url}")
        
        try:
            async with websockets.connect(url) as websocket:
                print(f"✅ Connected to post {post_id} WebSocket")
                
                # Listen for messages
                async def listen():
                    async for message in websocket:
                        data = json.loads(message)
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Post Update: {data}")
                
                # Send test messages
                async def send_test_messages():
                    await asyncio.sleep(2)
                    
                    # Track view
                    await websocket.send(json.dumps({'type': 'track_view'}))
                    
                    await asyncio.sleep(2)
                    
                    # Get stats
                    await websocket.send(json.dumps({'type': 'get_stats'}))
                
                # Run both tasks
                await asyncio.gather(listen(), send_test_messages())
        
        except Exception as e:
            print(f"❌ Error connecting to post: {e}")
    
    async def connect_to_comments(self, post_id):
        """Connect to comments WebSocket."""
        url = f"{self.base_url}/ws/blog/comments/{post_id}/"
        if self.token:
            url += f"?token={self.token}"
        
        print(f"Connecting to comments for post {post_id}: {url}")
        
        try:
            async with websockets.connect(url) as websocket:
                print(f"✅ Connected to comments WebSocket")
                
                # Listen for messages
                async def listen():
                    async for message in websocket:
                        data = json.loads(message)
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Comment Update: {data}")
                
                # Send test messages
                async def send_test_messages():
                    await asyncio.sleep(2)
                    
                    # Start typing
                    await websocket.send(json.dumps({'type': 'typing_start'}))
                    
                    await asyncio.sleep(3)
                    
                    # Stop typing
                    await websocket.send(json.dumps({'type': 'typing_stop'}))
                    
                    await asyncio.sleep(2)
                    
                    # Get comments
                    await websocket.send(json.dumps({'type': 'get_comments'}))
                
                # Run both tasks
                await asyncio.gather(listen(), send_test_messages())
        
        except Exception as e:
            print(f"❌ Error connecting to comments: {e}")
    
    async def test_health_check(self):
        """Test health check WebSocket."""
        url = f"{self.base_url}/ws/health/"
        
        print(f"Testing health check: {url}")
        
        try:
            async with websockets.connect(url) as websocket:
                print("✅ Connected to health check WebSocket")
                
                # Listen for initial message
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Health Status: {data}")
                
                # Send health check request
                await websocket.send(json.dumps({'type': 'health_check'}))
                
                # Get response
                message = await websocket.recv()
                data = json.loads(message)
                print(f"Health Response: {data}")
        
        except Exception as e:
            print(f"❌ Error with health check: {e}")


async def main():
    """Main function to run WebSocket tests."""
    parser = argparse.ArgumentParser(description='WebSocket Client Example')
    parser.add_argument('--token', help='JWT token for authentication')
    parser.add_argument('--url', default='ws://localhost:8000', help='WebSocket base URL')
    parser.add_argument('--post-id', help='Post ID for testing post/comment WebSockets')
    parser.add_argument('--test', choices=['notifications', 'post', 'comments', 'health', 'all'], 
                       default='all', help='Which WebSocket to test')
    
    args = parser.parse_args()
    
    client = WebSocketClient(args.url)
    
    if args.token:
        client.set_token(args.token)
        print(f"🔑 Using JWT token: {args.token[:20]}...")
    else:
        print("⚠️  No JWT token provided - some endpoints may reject connection")
    
    print(f"🚀 Starting WebSocket tests against {args.url}")
    print("=" * 60)
    
    try:
        if args.test == 'health' or args.test == 'all':
            print("\n📊 Testing Health Check WebSocket...")
            await client.test_health_check()
            await asyncio.sleep(1)
        
        if args.test == 'notifications' or args.test == 'all':
            print("\n🔔 Testing Notifications WebSocket...")
            await asyncio.wait_for(client.connect_to_notifications(), timeout=30)
            await asyncio.sleep(1)
        
        if (args.test == 'post' or args.test == 'all') and args.post_id:
            print(f"\n📝 Testing Post WebSocket for post {args.post_id}...")
            await asyncio.wait_for(client.connect_to_post(args.post_id), timeout=30)
            await asyncio.sleep(1)
        
        if (args.test == 'comments' or args.test == 'all') and args.post_id:
            print(f"\n💬 Testing Comments WebSocket for post {args.post_id}...")
            await asyncio.wait_for(client.connect_to_comments(args.post_id), timeout=30)
    
    except asyncio.TimeoutError:
        print("⏰ Test timed out")
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("\n✅ WebSocket tests completed")


if __name__ == "__main__":
    # Install required package if not available
    try:
        import websockets
    except ImportError:
        print("❌ websockets package not found. Install with: pip install websockets")
        exit(1)
    
    asyncio.run(main())