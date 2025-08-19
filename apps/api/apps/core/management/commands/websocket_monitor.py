"""
Management command to monitor WebSocket connections
"""

import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.websocket_utils import WebSocketManager, check_websocket_health
from apps.core.models import WebSocketConnection


class Command(BaseCommand):
    help = 'Monitor WebSocket connections and system health'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Monitoring interval in seconds (default: 30)'
        )
        
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously (Ctrl+C to stop)'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        continuous = options['continuous']
        
        self.stdout.write(
            self.style.SUCCESS('Starting WebSocket monitoring...')
        )
        
        try:
            if continuous:
                while True:
                    self.show_status()
                    time.sleep(interval)
            else:
                self.show_status()
        
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nMonitoring stopped by user')
            )
    
    def show_status(self):
        """Show current WebSocket status."""
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.stdout.write(f'\n=== WebSocket Status at {timestamp} ===')
        
        # Health check
        health = check_websocket_health()
        status_style = self.style.SUCCESS if health['status'] == 'healthy' else self.style.ERROR
        self.stdout.write(f'System Health: {status_style(health["status"])}')
        self.stdout.write(f'Message: {health["message"]}')
        
        if 'channel_layer' in health:
            self.stdout.write(f'Channel Layer: {health["channel_layer"]}')
        
        # Connection statistics
        manager = WebSocketManager()
        stats = manager.get_active_connections()
        
        self.stdout.write('\nConnection Statistics:')
        self.stdout.write(f'  Total connections (last hour): {stats["total_connections"]}')
        self.stdout.write(f'  Unique users: {stats["unique_users"]}')
        self.stdout.write(f'  Anonymous connections: {stats["anonymous_connections"]}')
        
        if stats['by_consumer']:
            self.stdout.write('\n  By Consumer Type:')
            for consumer, count in stats['by_consumer'].items():
                self.stdout.write(f'    {consumer}: {count}')
        
        # Recent activity
        recent_connections = WebSocketConnection.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).order_by('-timestamp')[:10]
        
        if recent_connections:
            self.stdout.write('\nRecent Activity (last 5 minutes):')
            for conn in recent_connections:
                user_info = conn.user.username if conn.user else 'Anonymous'
                action_style = self.style.SUCCESS if conn.action == 'connected' else self.style.WARNING
                self.stdout.write(
                    f'  {conn.timestamp.strftime("%H:%M:%S")} - '
                    f'{user_info} {action_style(conn.action)} '
                    f'{conn.consumer_class}'
                )
        else:
            self.stdout.write('\nNo recent activity')
        
        self.stdout.write('-' * 50)