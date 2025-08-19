"""
Analytics WebSocket consumers for real-time dashboard updates
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class AnalyticsDashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time analytics dashboard."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Check if user is staff
        if not self.scope['user'].is_authenticated or not self.scope['user'].is_staff:
            await self.close()
            return
        
        self.room_group_name = 'analytics_dashboard'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial dashboard data
        dashboard_data = await self.get_dashboard_data()
        await self.send(text_data=json.dumps({
            'type': 'dashboard_data',
            'data': dashboard_data
        }))
    
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
            
            if message_type == 'refresh_dashboard':
                # Send updated dashboard data
                dashboard_data = await self.get_dashboard_data()
                await self.send(text_data=json.dumps({
                    'type': 'dashboard_data',
                    'data': dashboard_data
                }))
            
        except json.JSONDecodeError:
            pass
    
    async def analytics_update(self, event):
        """Send analytics update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'analytics_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_dashboard_data(self):
        """Get current dashboard data."""
        from django.utils import timezone
        from datetime import timedelta
        from .models import PageView, UserSession
        
        # Get data for last 24 hours
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=24)
        
        # Page views
        page_views = PageView.objects.filter(timestamp__gte=start_time)
        total_views = page_views.count()
        unique_views = page_views.values('ip_address').distinct().count()
        
        # Sessions
        sessions = UserSession.objects.filter(started_at__gte=start_time)
        total_sessions = sessions.count()
        
        # Real-time visitors (last 5 minutes)
        recent_time = end_time - timedelta(minutes=5)
        active_visitors = PageView.objects.filter(timestamp__gte=recent_time).values('ip_address').distinct().count()
        
        return {
            'total_views': total_views,
            'unique_views': unique_views,
            'total_sessions': total_sessions,
            'active_visitors': active_visitors,
            'timestamp': end_time.isoformat()
        }