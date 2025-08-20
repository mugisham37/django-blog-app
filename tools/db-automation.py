#!/usr/bin/env python3
"""
Database Migration and Seeding Automation

This script provides comprehensive database automation including:
- Migration management with rollback capabilities
- Data seeding for different environments
- Database backup and restore
- Schema validation and optimization
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import django
from django.core.management import execute_from_command_line
from django.conf import settings


class DatabaseAutomation:
    """Database automation and management utilities."""
    
    def __init__(self, django_project_path: str = "apps/api"):
        self.django_project_path = Path(django_project_path)
        self.backup_dir = Path("backups/database")
        self.fixtures_dir = Path("fixtures")
        self.setup_django()
    
    def setup_django(self):
        """Setup Django environment."""
        sys.path.insert(0, str(self.django_project_path))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
        
        try:
            django.setup()
        except Exception as e:
            print(f"Error setting up Django: {e}")
            sys.exit(1)
    
    def run_django_command(self, command: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
        """Run Django management command."""
        cmd = [sys.executable, "manage.py"] + command
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=self.django_project_path,
            capture_output=capture_output,
            text=True
        )
        
        if result.returncode != 0 and not capture_output:
            print(f"Command failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
        
        return result
    
    def create_migrations(self, app_name: Optional[str] = None, dry_run: bool = False) -> bool:
        """Create Django migrations."""
        print("Creating migrations...")
        
        command = ["makemigrations"]
        if app_name:
            command.append(app_name)
        if dry_run:
            command.append("--dry-run")
        
        result = self.run_django_command(command)
        return result.returncode == 0
    
    def apply_migrations(self, app_name: Optional[str] = None, migration_name: Optional[str] = None, fake: bool = False) -> bool:
        """Apply Django migrations."""
        print("Applying migrations...")
        
        command = ["migrate"]
        if app_name:
            command.append(app_name)
            if migration_name:
                command.append(migration_name)
        if fake:
            command.append("--fake")
        
        result = self.run_django_command(command)
        return result.returncode == 0
    
    def rollback_migration(self, app_name: str, migration_name: str) -> bool:
        """Rollback to a specific migration."""
        print(f"Rolling back {app_name} to {migration_name}...")
        
        command = ["migrate", app_name, migration_name]
        result = self.run_django_command(command)
        return result.returncode == 0
    
    def show_migrations(self, app_name: Optional[str] = None) -> List[str]:
        """Show migration status."""
        print("Showing migration status...")
        
        command = ["showmigrations"]
        if app_name:
            command.append(app_name)
        
        result = self.run_django_command(command, capture_output=True)
        if result.returncode == 0:
            return result.stdout.split('\n')
        return []
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create database backup."""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = self.backup_dir / f"{backup_name}.json"
        
        print(f"Creating backup: {backup_file}")
        
        command = ["dumpdata", "--natural-foreign", "--natural-primary", "--indent", "2"]
        result = self.run_django_command(command, capture_output=True)
        
        if result.returncode == 0:
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            print(f"Backup created successfully: {backup_file}")
            return str(backup_file)
        else:
            print(f"Backup failed: {result.stderr}")
            return ""
    
    def restore_backup(self, backup_file: str, flush_first: bool = False) -> bool:
        """Restore database from backup."""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            backup_path = self.backup_dir / backup_file
            if not backup_path.exists():
                print(f"Backup file not found: {backup_file}")
                return False
        
        print(f"Restoring from backup: {backup_path}")
        
        if flush_first:
            print("Flushing database first...")
            flush_result = self.run_django_command(["flush", "--noinput"])
            if flush_result.returncode != 0:
                print("Failed to flush database")
                return False
        
        command = ["loaddata", str(backup_path)]
        result = self.run_django_command(command)
        return result.returncode == 0
    
    def seed_database(self, environment: str = "development") -> bool:
        """Seed database with environment-specific data."""
        print(f"Seeding database for {environment} environment...")
        
        # Create fixtures directory if it doesn't exist
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate fixtures if they don't exist
        self.generate_fixtures(environment)
        
        # Load fixtures
        fixture_files = list(self.fixtures_dir.glob(f"{environment}_*.json"))
        if not fixture_files:
            print(f"No fixtures found for {environment} environment")
            return False
        
        for fixture_file in fixture_files:
            print(f"Loading fixture: {fixture_file}")
            command = ["loaddata", str(fixture_file)]
            result = self.run_django_command(command)
            if result.returncode != 0:
                print(f"Failed to load fixture: {fixture_file}")
                return False
        
        return True
    
    def generate_fixtures(self, environment: str):
        """Generate fixtures for different environments."""
        fixtures = {
            "development": self.get_development_fixtures(),
            "testing": self.get_testing_fixtures(),
            "staging": self.get_staging_fixtures(),
            "production": self.get_production_fixtures()
        }
        
        fixture_data = fixtures.get(environment, {})
        
        for fixture_name, data in fixture_data.items():
            fixture_file = self.fixtures_dir / f"{environment}_{fixture_name}.json"
            
            if not fixture_file.exists():
                print(f"Generating fixture: {fixture_file}")
                with open(fixture_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
    
    def get_development_fixtures(self) -> Dict[str, List[Dict]]:
        """Get development environment fixtures."""
        return {
            "users": [
                {
                    "model": "auth.user",
                    "pk": 1,
                    "fields": {
                        "username": "admin",
                        "email": "admin@example.com",
                        "first_name": "Admin",
                        "last_name": "User",
                        "is_staff": True,
                        "is_superuser": True,
                        "is_active": True,
                        "date_joined": "2024-01-01T00:00:00Z"
                    }
                },
                {
                    "model": "auth.user",
                    "pk": 2,
                    "fields": {
                        "username": "testuser",
                        "email": "test@example.com",
                        "first_name": "Test",
                        "last_name": "User",
                        "is_staff": False,
                        "is_superuser": False,
                        "is_active": True,
                        "date_joined": "2024-01-01T00:00:00Z"
                    }
                }
            ],
            "blog_posts": [
                {
                    "model": "blog.post",
                    "pk": 1,
                    "fields": {
                        "title": "Welcome to Our Blog",
                        "slug": "welcome-to-our-blog",
                        "content": "This is a sample blog post for development.",
                        "author": 1,
                        "status": "published",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            ],
            "categories": [
                {
                    "model": "blog.category",
                    "pk": 1,
                    "fields": {
                        "name": "Technology",
                        "slug": "technology",
                        "description": "Technology related posts"
                    }
                },
                {
                    "model": "blog.category",
                    "pk": 2,
                    "fields": {
                        "name": "Programming",
                        "slug": "programming",
                        "description": "Programming tutorials and tips"
                    }
                }
            ]
        }
    
    def get_testing_fixtures(self) -> Dict[str, List[Dict]]:
        """Get testing environment fixtures."""
        return {
            "test_users": [
                {
                    "model": "auth.user",
                    "pk": 1,
                    "fields": {
                        "username": "testuser1",
                        "email": "test1@example.com",
                        "first_name": "Test",
                        "last_name": "User1",
                        "is_active": True
                    }
                }
            ]
        }
    
    def get_staging_fixtures(self) -> Dict[str, List[Dict]]:
        """Get staging environment fixtures."""
        return {
            "staging_data": [
                {
                    "model": "auth.user",
                    "pk": 1,
                    "fields": {
                        "username": "staging_admin",
                        "email": "staging@example.com",
                        "first_name": "Staging",
                        "last_name": "Admin",
                        "is_staff": True,
                        "is_superuser": True,
                        "is_active": True
                    }
                }
            ]
        }
    
    def get_production_fixtures(self) -> Dict[str, List[Dict]]:
        """Get production environment fixtures (minimal)."""
        return {
            "essential_data": [
                # Only essential data for production
            ]
        }
    
    def validate_schema(self) -> bool:
        """Validate database schema."""
        print("Validating database schema...")
        
        # Check for pending migrations
        result = self.run_django_command(["showmigrations", "--plan"], capture_output=True)
        if "[ ]" in result.stdout:
            print("Warning: There are unapplied migrations")
            return False
        
        # Run Django system checks
        result = self.run_django_command(["check"], capture_output=True)
        if result.returncode != 0:
            print(f"Schema validation failed: {result.stderr}")
            return False
        
        print("Schema validation passed")
        return True
    
    def optimize_database(self) -> bool:
        """Optimize database performance."""
        print("Optimizing database...")
        
        # This would include database-specific optimizations
        # For PostgreSQL: VACUUM, ANALYZE, REINDEX
        # For now, we'll just run Django's optimization commands
        
        try:
            from django.core.management import call_command
            
            # Clear expired sessions
            call_command('clearsessions')
            
            # Clear cache
            call_command('clear_cache')
            
            print("Database optimization completed")
            return True
        except Exception as e:
            print(f"Database optimization failed: {e}")
            return False
    
    def reset_database(self, confirm: bool = False) -> bool:
        """Reset database (WARNING: destroys all data)."""
        if not confirm:
            response = input("This will destroy all data. Are you sure? (yes/no): ")
            if response.lower() != 'yes':
                print("Database reset cancelled")
                return False
        
        print("Resetting database...")
        
        # Flush database
        result = self.run_django_command(["flush", "--noinput"])
        if result.returncode != 0:
            return False
        
        # Apply migrations
        result = self.run_django_command(["migrate"])
        return result.returncode == 0
    
    def create_superuser(self, username: str, email: str, password: str) -> bool:
        """Create Django superuser."""
        print(f"Creating superuser: {username}")
        
        os.environ['DJANGO_SUPERUSER_USERNAME'] = username
        os.environ['DJANGO_SUPERUSER_EMAIL'] = email
        os.environ['DJANGO_SUPERUSER_PASSWORD'] = password
        
        result = self.run_django_command(["createsuperuser", "--noinput"])
        return result.returncode == 0


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Database automation and management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Migration commands
    migrate_parser = subparsers.add_parser('migrate', help='Apply migrations')
    migrate_parser.add_argument('--app', help='Specific app to migrate')
    migrate_parser.add_argument('--migration', help='Specific migration to apply')
    migrate_parser.add_argument('--fake', action='store_true', help='Fake migration')
    
    makemigrations_parser = subparsers.add_parser('makemigrations', help='Create migrations')
    makemigrations_parser.add_argument('--app', help='Specific app to create migrations for')
    makemigrations_parser.add_argument('--dry-run', action='store_true', help='Show what migrations would be created')
    
    rollback_parser = subparsers.add_parser('rollback', help='Rollback migration')
    rollback_parser.add_argument('app', help='App name')
    rollback_parser.add_argument('migration', help='Migration name to rollback to')
    
    # Backup commands
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--name', help='Backup name')
    
    restore_parser = subparsers.add_parser('restore', help='Restore database backup')
    restore_parser.add_argument('backup_file', help='Backup file to restore')
    restore_parser.add_argument('--flush', action='store_true', help='Flush database before restore')
    
    # Seeding commands
    seed_parser = subparsers.add_parser('seed', help='Seed database')
    seed_parser.add_argument('--env', default='development', choices=['development', 'testing', 'staging', 'production'],
                           help='Environment to seed for')
    
    # Utility commands
    subparsers.add_parser('validate', help='Validate database schema')
    subparsers.add_parser('optimize', help='Optimize database')
    subparsers.add_parser('status', help='Show migration status')
    
    reset_parser = subparsers.add_parser('reset', help='Reset database (WARNING: destroys data)')
    reset_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    superuser_parser = subparsers.add_parser('createsuperuser', help='Create superuser')
    superuser_parser.add_argument('--username', required=True, help='Username')
    superuser_parser.add_argument('--email', required=True, help='Email')
    superuser_parser.add_argument('--password', required=True, help='Password')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    db_automation = DatabaseAutomation()
    
    try:
        if args.command == 'migrate':
            success = db_automation.apply_migrations(args.app, args.migration, args.fake)
        elif args.command == 'makemigrations':
            success = db_automation.create_migrations(args.app, args.dry_run)
        elif args.command == 'rollback':
            success = db_automation.rollback_migration(args.app, args.migration)
        elif args.command == 'backup':
            backup_file = db_automation.create_backup(args.name)
            success = bool(backup_file)
        elif args.command == 'restore':
            success = db_automation.restore_backup(args.backup_file, args.flush)
        elif args.command == 'seed':
            success = db_automation.seed_database(args.env)
        elif args.command == 'validate':
            success = db_automation.validate_schema()
        elif args.command == 'optimize':
            success = db_automation.optimize_database()
        elif args.command == 'status':
            migrations = db_automation.show_migrations()
            for migration in migrations:
                print(migration)
            success = True
        elif args.command == 'reset':
            success = db_automation.reset_database(args.confirm)
        elif args.command == 'createsuperuser':
            success = db_automation.create_superuser(args.username, args.email, args.password)
        else:
            print(f"Unknown command: {args.command}")
            success = False
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()