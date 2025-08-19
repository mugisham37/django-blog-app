"""
Management command to cleanup old WebSocket connections
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.core.models import WebSocketConnection
from apps.core.websocket_utils import WebSocketManager


class Command(BaseCommand):
    help = 'Cleanup old WebSocket connection records'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Delete connections older than this many hours (default: 24)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Get connections to delete
        old_connections = WebSocketConnection.objects.filter(
            timestamp__lt=cutoff_time
        )
        
        count = old_connections.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} WebSocket connection records '
                    f'older than {hours} hours'
                )
            )
            
            # Show some examples
            if count > 0:
                self.stdout.write('Examples of records that would be deleted:')
                for conn in old_connections[:5]:
                    self.stdout.write(f'  - {conn}')
                
                if count > 5:
                    self.stdout.write(f'  ... and {count - 5} more')
        else:
            # Actually delete
            deleted_count = old_connections.delete()[0]
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} WebSocket connection records'
                )
            )
        
        # Show current stats
        manager = WebSocketManager()
        stats = manager.get_active_connections()
        
        self.stdout.write('\nCurrent WebSocket Statistics:')
        self.stdout.write(f'  Total recent connections: {stats["total_connections"]}')
        self.stdout.write(f'  Unique users: {stats["unique_users"]}')
        self.stdout.write(f'  Anonymous connections: {stats["anonymous_connections"]}')
        
        if stats['by_consumer']:
            self.stdout.write('  By consumer type:')
            for consumer, count in stats['by_consumer'].items():
                self.stdout.write(f'    {consumer}: {count}')