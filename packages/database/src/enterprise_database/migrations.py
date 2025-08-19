"""
Database migration utilities and management.
"""

import os
import logging
import subprocess
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.apps import apps
from .exceptions import MigrationError

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Advanced migration management with rollback capabilities.
    """
    
    def __init__(self, database: str = 'default'):
        self.database = database
        self.connection = connections[database]
        self.executor = MigrationExecutor(self.connection)
        self.loader = MigrationLoader(self.connection)
        self.recorder = MigrationRecorder(self.connection)
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive migration status.
        
        Returns:
            Dictionary with migration status information
        """
        try:
            # Get applied migrations
            applied_migrations = set(self.recorder.applied_migrations())
            
            # Get all available migrations
            all_migrations = set(self.loader.graph.nodes)
            
            # Get unapplied migrations
            unapplied_migrations = all_migrations - applied_migrations
            
            # Get migration plan
            plan = self.executor.migration_plan(self.loader.graph.leaf_nodes())
            
            return {
                'database': self.database,
                'applied_count': len(applied_migrations),
                'unapplied_count': len(unapplied_migrations),
                'total_count': len(all_migrations),
                'applied_migrations': sorted(list(applied_migrations)),
                'unapplied_migrations': sorted(list(unapplied_migrations)),
                'migration_plan': [(migration.app_label, migration.name) for migration, backwards in plan],
                'has_pending_migrations': len(plan) > 0,
                'last_applied': self._get_last_applied_migration(),
            }
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            raise MigrationError(f"Failed to get migration status: {e}")
    
    def _get_last_applied_migration(self) -> Optional[Tuple[str, str]]:
        """Get the last applied migration."""
        try:
            applied = self.recorder.applied_migrations()
            if applied:
                return max(applied, key=lambda x: x)
            return None
        except Exception:
            return None
    
    def migrate(self, app_label: Optional[str] = None, migration_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run database migrations.
        
        Args:
            app_label: Specific app to migrate (optional)
            migration_name: Specific migration to migrate to (optional)
            
        Returns:
            Migration result information
        """
        try:
            start_time = datetime.now()
            
            # Build migration targets
            targets = []
            if app_label and migration_name:
                targets = [(app_label, migration_name)]
            elif app_label:
                # Get latest migration for app
                app_migrations = [
                    (app, name) for (app, name) in self.loader.graph.leaf_nodes()
                    if app == app_label
                ]
                targets = app_migrations
            else:
                # Migrate all apps
                targets = self.loader.graph.leaf_nodes()
            
            # Get migration plan
            plan = self.executor.migration_plan(targets)
            
            if not plan:
                return {
                    'status': 'no_migrations',
                    'message': 'No migrations to apply',
                    'duration': 0,
                }
            
            # Execute migrations
            with transaction.atomic(using=self.database):
                self.executor.migrate(targets)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Successfully applied {len(plan)} migrations in {duration:.2f}s")
            
            return {
                'status': 'success',
                'message': f'Applied {len(plan)} migrations',
                'applied_migrations': [(migration.app_label, migration.name) for migration, backwards in plan],
                'duration': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise MigrationError(f"Migration failed: {e}")
    
    def rollback(self, app_label: str, migration_name: str) -> Dict[str, Any]:
        """
        Rollback to a specific migration.
        
        Args:
            app_label: App label
            migration_name: Migration name to rollback to
            
        Returns:
            Rollback result information
        """
        try:
            start_time = datetime.now()
            
            # Validate migration exists
            if (app_label, migration_name) not in self.loader.graph.nodes:
                raise MigrationError(f"Migration {app_label}.{migration_name} not found")
            
            # Get rollback plan
            targets = [(app_label, migration_name)]
            plan = self.executor.migration_plan(targets)
            
            if not plan:
                return {
                    'status': 'no_rollback',
                    'message': 'No migrations to rollback',
                    'duration': 0,
                }
            
            # Execute rollback
            with transaction.atomic(using=self.database):
                self.executor.migrate(targets)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Successfully rolled back to {app_label}.{migration_name} in {duration:.2f}s")
            
            return {
                'status': 'success',
                'message': f'Rolled back to {app_label}.{migration_name}',
                'rollback_plan': [(migration.app_label, migration.name) for migration, backwards in plan],
                'duration': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise MigrationError(f"Rollback failed: {e}")
    
    def create_migration(self, app_label: str, name: str, auto: bool = True) -> Dict[str, Any]:
        """
        Create a new migration.
        
        Args:
            app_label: App label
            name: Migration name
            auto: Whether to auto-detect changes
            
        Returns:
            Migration creation result
        """
        try:
            start_time = datetime.now()
            
            # Prepare command arguments
            args = [app_label] if app_label else []
            options = {
                'verbosity': 1,
                'interactive': False,
                'dry_run': False,
                'merge': False,
                'empty': not auto,
                'name': name,
            }
            
            # Create migration
            call_command('makemigrations', *args, **options)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Created migration {name} for {app_label} in {duration:.2f}s")
            
            return {
                'status': 'success',
                'message': f'Created migration {name} for {app_label}',
                'app_label': app_label,
                'migration_name': name,
                'duration': duration,
            }
            
        except CommandError as e:
            logger.error(f"Failed to create migration: {e}")
            raise MigrationError(f"Failed to create migration: {e}")
    
    def check_migrations(self) -> Dict[str, Any]:
        """
        Check for migration issues.
        
        Returns:
            Migration check results
        """
        try:
            # Check for unapplied migrations
            status = self.get_migration_status()
            
            issues = []
            
            if status['has_pending_migrations']:
                issues.append({
                    'type': 'unapplied_migrations',
                    'severity': 'warning',
                    'message': f"{status['unapplied_count']} unapplied migrations found",
                    'migrations': status['unapplied_migrations'],
                })
            
            # Check for migration conflicts
            try:
                conflicts = self.loader.detect_conflicts()
                if conflicts:
                    issues.append({
                        'type': 'migration_conflicts',
                        'severity': 'error',
                        'message': 'Migration conflicts detected',
                        'conflicts': conflicts,
                    })
            except Exception as e:
                issues.append({
                    'type': 'conflict_check_failed',
                    'severity': 'warning',
                    'message': f'Failed to check for conflicts: {e}',
                })
            
            return {
                'status': 'error' if any(issue['severity'] == 'error' for issue in issues) else 'warning' if issues else 'ok',
                'issues': issues,
                'total_issues': len(issues),
            }
            
        except Exception as e:
            logger.error(f"Migration check failed: {e}")
            return {
                'status': 'error',
                'issues': [{
                    'type': 'check_failed',
                    'severity': 'error',
                    'message': f'Migration check failed: {e}',
                }],
                'total_issues': 1,
            }
    
    def fake_migration(self, app_label: str, migration_name: str) -> Dict[str, Any]:
        """
        Mark a migration as applied without actually running it.
        
        Args:
            app_label: App label
            migration_name: Migration name
            
        Returns:
            Fake migration result
        """
        try:
            # Validate migration exists
            if (app_label, migration_name) not in self.loader.graph.nodes:
                raise MigrationError(f"Migration {app_label}.{migration_name} not found")
            
            # Mark as applied
            self.recorder.record_applied(app_label, migration_name)
            
            logger.info(f"Marked migration {app_label}.{migration_name} as applied (fake)")
            
            return {
                'status': 'success',
                'message': f'Marked {app_label}.{migration_name} as applied (fake)',
                'app_label': app_label,
                'migration_name': migration_name,
            }
            
        except Exception as e:
            logger.error(f"Failed to fake migration: {e}")
            raise MigrationError(f"Failed to fake migration: {e}")
    
    def unapply_migration(self, app_label: str, migration_name: str) -> Dict[str, Any]:
        """
        Mark a migration as unapplied without running rollback.
        
        Args:
            app_label: App label
            migration_name: Migration name
            
        Returns:
            Unapply result
        """
        try:
            # Validate migration is applied
            if (app_label, migration_name) not in self.recorder.applied_migrations():
                raise MigrationError(f"Migration {app_label}.{migration_name} is not applied")
            
            # Mark as unapplied
            self.recorder.record_unapplied(app_label, migration_name)
            
            logger.info(f"Marked migration {app_label}.{migration_name} as unapplied")
            
            return {
                'status': 'success',
                'message': f'Marked {app_label}.{migration_name} as unapplied',
                'app_label': app_label,
                'migration_name': migration_name,
            }
            
        except Exception as e:
            logger.error(f"Failed to unapply migration: {e}")
            raise MigrationError(f"Failed to unapply migration: {e}")
    
    def export_migration_history(self) -> Dict[str, Any]:
        """
        Export migration history for backup/documentation.
        
        Returns:
            Migration history data
        """
        try:
            status = self.get_migration_status()
            
            # Get detailed migration information
            migration_details = []
            for app_label, migration_name in status['applied_migrations']:
                try:
                    migration = self.loader.get_migration(app_label, migration_name)
                    migration_details.append({
                        'app_label': app_label,
                        'name': migration_name,
                        'dependencies': getattr(migration, 'dependencies', []),
                        'operations_count': len(getattr(migration, 'operations', [])),
                    })
                except Exception as e:
                    migration_details.append({
                        'app_label': app_label,
                        'name': migration_name,
                        'error': str(e),
                    })
            
            return {
                'database': self.database,
                'export_time': datetime.now().isoformat(),
                'status': status,
                'migration_details': migration_details,
            }
            
        except Exception as e:
            logger.error(f"Failed to export migration history: {e}")
            raise MigrationError(f"Failed to export migration history: {e}")


class MigrationBackup:
    """
    Migration backup and restore functionality.
    """
    
    def __init__(self, database: str = 'default'):
        self.database = database
        self.connection = connections[database]
    
    def create_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        Create a database backup before migrations.
        
        Args:
            backup_path: Path to store backup
            
        Returns:
            Backup result information
        """
        try:
            start_time = datetime.now()
            
            # Get database configuration
            db_config = self.connection.settings_dict
            
            # Create backup directory
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '-h', db_config['HOST'],
                '-p', str(db_config['PORT']),
                '-U', db_config['USER'],
                '-d', db_config['NAME'],
                '-f', backup_path,
                '--verbose',
                '--no-password',
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            # Execute backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise MigrationError(f"Backup failed: {result.stderr}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Get backup file size
            backup_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
            
            logger.info(f"Created database backup at {backup_path} in {duration:.2f}s")
            
            return {
                'status': 'success',
                'backup_path': backup_path,
                'backup_size': backup_size,
                'duration': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise MigrationError(f"Backup creation failed: {e}")
    
    def restore_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Restore result information
        """
        try:
            if not os.path.exists(backup_path):
                raise MigrationError(f"Backup file not found: {backup_path}")
            
            start_time = datetime.now()
            
            # Get database configuration
            db_config = self.connection.settings_dict
            
            # Build psql command
            cmd = [
                'psql',
                '-h', db_config['HOST'],
                '-p', str(db_config['PORT']),
                '-U', db_config['USER'],
                '-d', db_config['NAME'],
                '-f', backup_path,
                '--quiet',
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            # Execute restore
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise MigrationError(f"Restore failed: {result.stderr}")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"Restored database from {backup_path} in {duration:.2f}s")
            
            return {
                'status': 'success',
                'backup_path': backup_path,
                'duration': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Backup restore failed: {e}")
            raise MigrationError(f"Backup restore failed: {e}")


# Utility functions
def get_migration_manager(database: str = 'default') -> MigrationManager:
    """Get migration manager for a database."""
    return MigrationManager(database)


def migrate_all_databases() -> Dict[str, Any]:
    """
    Migrate all configured databases.
    
    Returns:
        Results for all databases
    """
    from django.conf import settings
    
    results = {}
    
    for db_alias in settings.DATABASES.keys():
        if db_alias == 'read_replica':
            continue  # Skip read replicas
        
        try:
            manager = MigrationManager(db_alias)
            results[db_alias] = manager.migrate()
        except Exception as e:
            results[db_alias] = {
                'status': 'error',
                'message': str(e),
            }
    
    return results