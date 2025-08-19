"""
Command-line interface for database operations.
"""

import os
import sys
import argparse
from typing import Optional
from django.core.management import execute_from_command_line
from django.conf import settings
from .migrations import MigrationManager
from .seeders import DataSeeder
from .monitoring import DatabaseMonitor


def migrate_command():
    """
    Command-line interface for database migrations.
    """
    parser = argparse.ArgumentParser(description='Database migration management')
    parser.add_argument('--app', help='Specific app to migrate')
    parser.add_argument('--fake', action='store_true', help='Mark migrations as run without executing')
    parser.add_argument('--fake-initial', action='store_true', help='Mark initial migration as run')
    parser.add_argument('--plan', action='store_true', help='Show migration plan without executing')
    parser.add_argument('--check', action='store_true', help='Check for unapplied migrations')
    parser.add_argument('--rollback', help='Rollback to specific migration')
    
    args = parser.parse_args()
    
    try:
        migration_manager = MigrationManager()
        
        if args.check:
            unapplied = migration_manager.get_unapplied_migrations()
            if unapplied:
                print(f"Unapplied migrations found: {len(unapplied)}")
                for migration in unapplied:
                    print(f"  - {migration}")
                sys.exit(1)
            else:
                print("All migrations are up to date")
                sys.exit(0)
        
        elif args.plan:
            plan = migration_manager.get_migration_plan(args.app)
            print("Migration plan:")
            for migration in plan:
                print(f"  - {migration}")
        
        elif args.rollback:
            migration_manager.rollback_to_migration(args.rollback, args.app)
            print(f"Rolled back to migration: {args.rollback}")
        
        else:
            migration_manager.apply_migrations(
                app_label=args.app,
                fake=args.fake,
                fake_initial=args.fake_initial
            )
            print("Migrations applied successfully")
    
    except Exception as e:
        print(f"Migration error: {e}")
        sys.exit(1)


def seed_command():
    """
    Command-line interface for data seeding.
    """
    parser = argparse.ArgumentParser(description='Database seeding management')
    parser.add_argument('--environment', default='development', 
                       choices=['development', 'testing', 'production'],
                       help='Environment to seed for')
    parser.add_argument('--app', help='Specific app to seed')
    parser.add_argument('--fixture', help='Specific fixture to load')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be seeded without executing')
    
    args = parser.parse_args()
    
    try:
        seeder = DataSeeder()
        
        if args.dry_run:
            plan = seeder.get_seeding_plan(args.environment, args.app, args.fixture)
            print("Seeding plan:")
            for item in plan:
                print(f"  - {item}")
        else:
            seeder.seed_data(
                environment=args.environment,
                app_label=args.app,
                fixture_name=args.fixture,
                clear_existing=args.clear
            )
            print("Data seeded successfully")
    
    except Exception as e:
        print(f"Seeding error: {e}")
        sys.exit(1)


def backup_command():
    """
    Command-line interface for database backup.
    """
    parser = argparse.ArgumentParser(description='Database backup management')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--compress', action='store_true', help='Compress backup file')
    parser.add_argument('--exclude-tables', nargs='+', help='Tables to exclude from backup')
    parser.add_argument('--data-only', action='store_true', help='Backup data only (no schema)')
    parser.add_argument('--schema-only', action='store_true', help='Backup schema only (no data)')
    parser.add_argument('--restore', help='Restore from backup file')
    
    args = parser.parse_args()
    
    try:
        from .backup import DatabaseBackup
        backup_manager = DatabaseBackup()
        
        if args.restore:
            backup_manager.restore_backup(args.restore)
            print(f"Database restored from: {args.restore}")
        else:
            backup_file = backup_manager.create_backup(
                output_path=args.output,
                compress=args.compress,
                exclude_tables=args.exclude_tables or [],
                data_only=args.data_only,
                schema_only=args.schema_only
            )
            print(f"Backup created: {backup_file}")
    
    except Exception as e:
        print(f"Backup error: {e}")
        sys.exit(1)


def monitor_command():
    """
    Command-line interface for database monitoring.
    """
    parser = argparse.ArgumentParser(description='Database monitoring')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--connections', action='store_true', help='Show active connections')
    parser.add_argument('--slow-queries', action='store_true', help='Show slow queries')
    parser.add_argument('--health', action='store_true', help='Check database health')
    parser.add_argument('--watch', action='store_true', help='Watch metrics in real-time')
    
    args = parser.parse_args()
    
    try:
        monitor = DatabaseMonitor()
        
        if args.stats:
            stats = monitor.get_database_stats()
            print("Database Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        elif args.connections:
            connections = monitor.get_active_connections()
            print(f"Active Connections: {len(connections)}")
            for conn in connections:
                print(f"  - {conn}")
        
        elif args.slow_queries:
            queries = monitor.get_slow_queries()
            print(f"Slow Queries: {len(queries)}")
            for query in queries:
                print(f"  - {query}")
        
        elif args.health:
            health = monitor.check_health()
            print(f"Database Health: {'OK' if health['healthy'] else 'FAILED'}")
            for check, result in health['checks'].items():
                status = 'PASS' if result else 'FAIL'
                print(f"  {check}: {status}")
        
        elif args.watch:
            print("Watching database metrics (Ctrl+C to stop)...")
            monitor.watch_metrics()
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    except Exception as e:
        print(f"Monitoring error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    
    import django
    django.setup()
    
    # Parse command and execute
    if len(sys.argv) > 1:
        command = sys.argv[1]
        sys.argv = sys.argv[1:]  # Remove script name
        
        if command == 'migrate':
            migrate_command()
        elif command == 'seed':
            seed_command()
        elif command == 'backup':
            backup_command()
        elif command == 'monitor':
            monitor_command()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: migrate, seed, backup, monitor")
            sys.exit(1)
    else:
        print("Usage: python -m enterprise_database <command>")
        print("Available commands: migrate, seed, backup, monitor")
        sys.exit(1)