"""
Database backup and restore utilities.
"""

import os
import gzip
import shutil
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from .config import get_database_config
from .exceptions import DatabaseError


class DatabaseBackup:
    """
    Database backup and restore manager.
    """
    
    def __init__(self, database_alias: str = 'default'):
        """
        Initialize backup manager.
        
        Args:
            database_alias: Database alias to backup
        """
        self.database_alias = database_alias
        self.db_config = settings.DATABASES[database_alias]
        self.backup_dir = getattr(settings, 'DATABASE_BACKUP_DIR', '/tmp/db_backups')
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(
        self,
        output_path: Optional[str] = None,
        compress: bool = True,
        exclude_tables: List[str] = None,
        data_only: bool = False,
        schema_only: bool = False
    ) -> str:
        """
        Create database backup.
        
        Args:
            output_path: Custom output file path
            compress: Whether to compress the backup
            exclude_tables: Tables to exclude from backup
            data_only: Backup data only (no schema)
            schema_only: Backup schema only (no data)
            
        Returns:
            Path to created backup file
        """
        if not output_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{self.database_alias}_{timestamp}.sql"
            if compress:
                filename += ".gz"
            output_path = os.path.join(self.backup_dir, filename)
        
        try:
            if self.db_config['ENGINE'] == 'django.db.backends.postgresql':
                return self._create_postgresql_backup(
                    output_path, compress, exclude_tables, data_only, schema_only
                )
            elif self.db_config['ENGINE'] == 'django.db.backends.mysql':
                return self._create_mysql_backup(
                    output_path, compress, exclude_tables, data_only, schema_only
                )
            elif self.db_config['ENGINE'] == 'django.db.backends.sqlite3':
                return self._create_sqlite_backup(output_path, compress)
            else:
                raise DatabaseError(f"Backup not supported for engine: {self.db_config['ENGINE']}")
        
        except Exception as e:
            raise DatabaseError(f"Backup failed: {str(e)}")
    
    def _create_postgresql_backup(
        self,
        output_path: str,
        compress: bool,
        exclude_tables: List[str],
        data_only: bool,
        schema_only: bool
    ) -> str:
        """Create PostgreSQL backup using pg_dump."""
        cmd = [
            'pg_dump',
            '-h', self.db_config['HOST'],
            '-p', str(self.db_config['PORT']),
            '-U', self.db_config['USER'],
            '-d', self.db_config['NAME'],
            '--verbose',
            '--no-password'
        ]
        
        # Add options based on parameters
        if data_only:
            cmd.append('--data-only')
        elif schema_only:
            cmd.append('--schema-only')
        
        # Exclude tables
        if exclude_tables:
            for table in exclude_tables:
                cmd.extend(['--exclude-table', table])
        
        # Set environment variables
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['PASSWORD']
        
        # Execute backup
        if compress:
            with gzip.open(output_path, 'wt') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
        else:
            with open(output_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
        
        if result.returncode != 0:
            raise DatabaseError(f"pg_dump failed: {result.stderr}")
        
        return output_path
    
    def _create_mysql_backup(
        self,
        output_path: str,
        compress: bool,
        exclude_tables: List[str],
        data_only: bool,
        schema_only: bool
    ) -> str:
        """Create MySQL backup using mysqldump."""
        cmd = [
            'mysqldump',
            '-h', self.db_config['HOST'],
            '-P', str(self.db_config['PORT']),
            '-u', self.db_config['USER'],
            f'-p{self.db_config["PASSWORD"]}',
            '--single-transaction',
            '--routines',
            '--triggers'
        ]
        
        # Add options based on parameters
        if data_only:
            cmd.append('--no-create-info')
        elif schema_only:
            cmd.append('--no-data')
        
        # Add database name
        cmd.append(self.db_config['NAME'])
        
        # Exclude tables
        if exclude_tables:
            for table in exclude_tables:
                cmd.extend(['--ignore-table', f"{self.db_config['NAME']}.{table}"])
        
        # Execute backup
        if compress:
            with gzip.open(output_path, 'wt') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        else:
            with open(output_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise DatabaseError(f"mysqldump failed: {result.stderr}")
        
        return output_path
    
    def _create_sqlite_backup(self, output_path: str, compress: bool) -> str:
        """Create SQLite backup by copying the database file."""
        db_path = self.db_config['NAME']
        
        if compress:
            with open(db_path, 'rb') as f_in:
                with gzip.open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(db_path, output_path)
        
        return output_path
    
    def restore_backup(self, backup_path: str, drop_existing: bool = False) -> None:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            drop_existing: Whether to drop existing database
        """
        if not os.path.exists(backup_path):
            raise DatabaseError(f"Backup file not found: {backup_path}")
        
        try:
            if self.db_config['ENGINE'] == 'django.db.backends.postgresql':
                self._restore_postgresql_backup(backup_path, drop_existing)
            elif self.db_config['ENGINE'] == 'django.db.backends.mysql':
                self._restore_mysql_backup(backup_path, drop_existing)
            elif self.db_config['ENGINE'] == 'django.db.backends.sqlite3':
                self._restore_sqlite_backup(backup_path)
            else:
                raise DatabaseError(f"Restore not supported for engine: {self.db_config['ENGINE']}")
        
        except Exception as e:
            raise DatabaseError(f"Restore failed: {str(e)}")
    
    def _restore_postgresql_backup(self, backup_path: str, drop_existing: bool) -> None:
        """Restore PostgreSQL backup using psql."""
        if drop_existing:
            self._drop_postgresql_database()
            self._create_postgresql_database()
        
        # Determine if file is compressed
        is_compressed = backup_path.endswith('.gz')
        
        cmd = [
            'psql',
            '-h', self.db_config['HOST'],
            '-p', str(self.db_config['PORT']),
            '-U', self.db_config['USER'],
            '-d', self.db_config['NAME'],
            '--quiet'
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['PASSWORD']
        
        if is_compressed:
            with gzip.open(backup_path, 'rt') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, env=env, text=True)
        else:
            with open(backup_path, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, env=env, text=True)
        
        if result.returncode != 0:
            raise DatabaseError(f"psql restore failed: {result.stderr}")
    
    def _restore_mysql_backup(self, backup_path: str, drop_existing: bool) -> None:
        """Restore MySQL backup using mysql."""
        if drop_existing:
            self._drop_mysql_database()
            self._create_mysql_database()
        
        is_compressed = backup_path.endswith('.gz')
        
        cmd = [
            'mysql',
            '-h', self.db_config['HOST'],
            '-P', str(self.db_config['PORT']),
            '-u', self.db_config['USER'],
            f'-p{self.db_config["PASSWORD"]}',
            self.db_config['NAME']
        ]
        
        if is_compressed:
            with gzip.open(backup_path, 'rt') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        else:
            with open(backup_path, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise DatabaseError(f"mysql restore failed: {result.stderr}")
    
    def _restore_sqlite_backup(self, backup_path: str) -> None:
        """Restore SQLite backup by copying the file."""
        db_path = self.db_config['NAME']
        
        # Backup current database
        if os.path.exists(db_path):
            backup_current = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_current)
        
        # Restore from backup
        if backup_path.endswith('.gz'):
            with gzip.open(backup_path, 'rb') as f_in:
                with open(db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            shutil.copy2(backup_path, db_path)
    
    def _drop_postgresql_database(self) -> None:
        """Drop PostgreSQL database."""
        cmd = [
            'dropdb',
            '-h', self.db_config['HOST'],
            '-p', str(self.db_config['PORT']),
            '-U', self.db_config['USER'],
            '--if-exists',
            self.db_config['NAME']
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['PASSWORD']
        
        subprocess.run(cmd, env=env, check=True)
    
    def _create_postgresql_database(self) -> None:
        """Create PostgreSQL database."""
        cmd = [
            'createdb',
            '-h', self.db_config['HOST'],
            '-p', str(self.db_config['PORT']),
            '-U', self.db_config['USER'],
            self.db_config['NAME']
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['PASSWORD']
        
        subprocess.run(cmd, env=env, check=True)
    
    def _drop_mysql_database(self) -> None:
        """Drop MySQL database."""
        cmd = [
            'mysql',
            '-h', self.db_config['HOST'],
            '-P', str(self.db_config['PORT']),
            '-u', self.db_config['USER'],
            f'-p{self.db_config["PASSWORD"]}',
            '-e', f"DROP DATABASE IF EXISTS {self.db_config['NAME']}"
        ]
        
        subprocess.run(cmd, check=True)
    
    def _create_mysql_database(self) -> None:
        """Create MySQL database."""
        cmd = [
            'mysql',
            '-h', self.db_config['HOST'],
            '-P', str(self.db_config['PORT']),
            '-u', self.db_config['USER'],
            f'-p{self.db_config["PASSWORD"]}',
            '-e', f"CREATE DATABASE {self.db_config['NAME']}"
        ]
        
        subprocess.run(cmd, check=True)
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith(f'backup_{self.database_alias}_'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                backups.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'compressed': filename.endswith('.gz')
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10, keep_days: int = 30) -> List[str]:
        """
        Clean up old backup files.
        
        Args:
            keep_count: Number of recent backups to keep
            keep_days: Number of days to keep backups
            
        Returns:
            List of deleted backup files
        """
        backups = self.list_backups()
        deleted_files = []
        
        # Keep recent backups by count
        recent_backups = backups[:keep_count]
        old_backups = backups[keep_count:]
        
        # Keep backups within the specified days
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        for backup in old_backups:
            if backup['created'].timestamp() < cutoff_date:
                try:
                    os.remove(backup['filepath'])
                    deleted_files.append(backup['filename'])
                except OSError as e:
                    print(f"Failed to delete {backup['filename']}: {e}")
        
        return deleted_files
    
    def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        Verify backup file integrity.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Verification results
        """
        if not os.path.exists(backup_path):
            return {'valid': False, 'error': 'File not found'}
        
        try:
            # Check if file can be opened
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rt') as f:
                    # Read first few lines to verify it's a valid SQL dump
                    first_lines = [f.readline() for _ in range(5)]
            else:
                with open(backup_path, 'r') as f:
                    first_lines = [f.readline() for _ in range(5)]
            
            # Basic validation - check for SQL dump markers
            content = ''.join(first_lines).lower()
            is_sql_dump = any(marker in content for marker in [
                'pg_dump', 'mysqldump', 'sqlite', 'create table', 'insert into'
            ])
            
            file_stat = os.stat(backup_path)
            
            return {
                'valid': is_sql_dump,
                'size': file_stat.st_size,
                'created': datetime.fromtimestamp(file_stat.st_ctime),
                'compressed': backup_path.endswith('.gz'),
                'first_lines': first_lines[:3]  # First 3 lines for inspection
            }
        
        except Exception as e:
            return {'valid': False, 'error': str(e)}