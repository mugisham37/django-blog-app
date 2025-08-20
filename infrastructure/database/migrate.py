#!/usr/bin/env python3
"""
Database Migration Management Script
Handles forward migrations, rollbacks, and migration status tracking
"""

import os
import sys
import hashlib
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def calculate_checksum(self, content):
        """Calculate SHA-256 checksum of migration content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def ensure_migrations_table(self):
        """Ensure schema_migrations table exists"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(20) PRIMARY KEY,
                        description TEXT,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        checksum VARCHAR(64)
                    )
                """)
                conn.commit()
    
    def get_applied_migrations(self):
        """Get list of applied migrations"""
        self.ensure_migrations_table()
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM schema_migrations ORDER BY version")
                return cur.fetchall()
    
    def get_available_migrations(self):
        """Get list of available migration files"""
        migrations = []
        if not os.path.exists(self.migrations_dir):
            return migrations
            
        for filename in sorted(os.listdir(self.migrations_dir)):
            if filename.endswith('.sql') and not filename.startswith('rollback_'):
                version = filename.split('_')[0]
                migrations.append({
                    'version': version,
                    'filename': filename,
                    'path': os.path.join(self.migrations_dir, filename)
                })
        return migrations
    
    def get_pending_migrations(self):
        """Get migrations that haven't been applied yet"""
        applied = {m['version'] for m in self.get_applied_migrations()}
        available = self.get_available_migrations()
        return [m for m in available if m['version'] not in applied]
    
    def apply_migration(self, migration):
        """Apply a single migration"""
        logger.info(f"Applying migration {migration['version']}: {migration['filename']}")
        
        with open(migration['path'], 'r') as f:
            content = f.read()
        
        checksum = self.calculate_checksum(content)
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    # Execute migration
                    cur.execute(content)
                    
                    # Record migration (if not already recorded by the migration itself)
                    cur.execute("""
                        INSERT INTO schema_migrations (version, description, checksum)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (version) DO UPDATE SET
                            checksum = EXCLUDED.checksum,
                            applied_at = NOW()
                    """, (migration['version'], f"Migration {migration['filename']}", checksum))
                    
                    conn.commit()
                    logger.info(f"Successfully applied migration {migration['version']}")
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to apply migration {migration['version']}: {e}")
                    raise
    
    def rollback_migration(self, version):
        """Rollback a specific migration"""
        rollback_file = f"rollback_{version}.sql"
        rollback_path = os.path.join(self.migrations_dir, rollback_file)
        
        if not os.path.exists(rollback_path):
            raise FileNotFoundError(f"Rollback file not found: {rollback_file}")
        
        logger.info(f"Rolling back migration {version}")
        
        with open(rollback_path, 'r') as f:
            content = f.read()
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    # Execute rollback
                    cur.execute(content)
                    
                    # Remove migration record
                    cur.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
                    
                    conn.commit()
                    logger.info(f"Successfully rolled back migration {version}")
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to rollback migration {version}: {e}")
                    raise
    
    def migrate_up(self, target_version=None):
        """Apply pending migrations up to target version"""
        pending = self.get_pending_migrations()
        
        if target_version:
            pending = [m for m in pending if m['version'] <= target_version]
        
        if not pending:
            logger.info("No pending migrations to apply")
            return
        
        for migration in pending:
            self.apply_migration(migration)
        
        logger.info(f"Applied {len(pending)} migrations")
    
    def migrate_down(self, target_version):
        """Rollback migrations down to target version"""
        applied = self.get_applied_migrations()
        to_rollback = [m for m in applied if m['version'] > target_version]
        to_rollback.sort(key=lambda x: x['version'], reverse=True)
        
        if not to_rollback:
            logger.info("No migrations to rollback")
            return
        
        for migration in to_rollback:
            self.rollback_migration(migration['version'])
        
        logger.info(f"Rolled back {len(to_rollback)} migrations")
    
    def status(self):
        """Show migration status"""
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        print("\n=== Migration Status ===")
        print(f"Applied migrations: {len(applied)}")
        print(f"Available migrations: {len(available)}")
        print(f"Pending migrations: {len(pending)}")
        
        if applied:
            print("\nApplied migrations:")
            for migration in applied:
                print(f"  ✓ {migration['version']} - {migration['applied_at']}")
        
        if pending:
            print("\nPending migrations:")
            for migration in pending:
                print(f"  ○ {migration['version']} - {migration['filename']}")
        
        if not pending:
            print("\n✓ Database is up to date")

def main():
    parser = argparse.ArgumentParser(description='Database Migration Tool')
    parser.add_argument('--db-url', required=True, help='Database connection URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show migration status')
    
    # Migrate up command
    up_parser = subparsers.add_parser('up', help='Apply pending migrations')
    up_parser.add_argument('--target', help='Target migration version')
    
    # Migrate down command
    down_parser = subparsers.add_parser('down', help='Rollback migrations')
    down_parser.add_argument('target', help='Target migration version to rollback to')
    
    # Create migration command
    create_parser = subparsers.add_parser('create', help='Create new migration file')
    create_parser.add_argument('name', help='Migration name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    migrator = DatabaseMigrator(args.db_url)
    
    try:
        if args.command == 'status':
            migrator.status()
        elif args.command == 'up':
            migrator.migrate_up(args.target)
        elif args.command == 'down':
            migrator.migrate_down(args.target)
        elif args.command == 'create':
            # Create new migration file
            available = migrator.get_available_migrations()
            next_version = f"{len(available) + 1:03d}"
            filename = f"{next_version}_{args.name.replace(' ', '_').lower()}.sql"
            filepath = os.path.join(migrator.migrations_dir, filename)
            
            template = f"""-- Migration {next_version}: {args.name}
-- Description: {args.name}

BEGIN;

-- Add your migration SQL here

-- Record migration
INSERT INTO schema_migrations (version, description, checksum) 
VALUES ('{next_version}', '{args.name}', 'placeholder_checksum');

COMMIT;
"""
            
            with open(filepath, 'w') as f:
                f.write(template)
            
            # Create rollback file
            rollback_filepath = os.path.join(migrator.migrations_dir, f"rollback_{next_version}.sql")
            rollback_template = f"""-- Rollback script for migration {next_version}
-- This script reverses: {args.name}

BEGIN;

-- Add your rollback SQL here

-- Remove migration record
DELETE FROM schema_migrations WHERE version = '{next_version}';

COMMIT;
"""
            
            with open(rollback_filepath, 'w') as f:
                f.write(rollback_template)
            
            print(f"Created migration files:")
            print(f"  {filename}")
            print(f"  rollback_{next_version}.sql")
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()