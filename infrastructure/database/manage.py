#!/usr/bin/env python3
"""
Database Management CLI
Comprehensive database management tool for development and production
"""

import os
import sys
import argparse
import subprocess
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.compose_file = os.path.join(self.base_dir, 'docker-compose.database.yml')
        
    def run_command(self, command, check=True):
        """Run shell command"""
        logger.info(f"Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if check and result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command)
        
        return result
    
    def start_services(self, services=None, profiles=None):
        """Start database services"""
        cmd = f"docker-compose -f {self.compose_file} up -d"
        
        if profiles:
            for profile in profiles:
                cmd += f" --profile {profile}"
        
        if services:
            cmd += f" {' '.join(services)}"
        
        self.run_command(cmd)
        logger.info("Database services started successfully")
    
    def stop_services(self, services=None):
        """Stop database services"""
        cmd = f"docker-compose -f {self.compose_file} down"
        
        if services:
            cmd = f"docker-compose -f {self.compose_file} stop {' '.join(services)}"
        
        self.run_command(cmd)
        logger.info("Database services stopped")
    
    def restart_services(self, services=None):
        """Restart database services"""
        cmd = f"docker-compose -f {self.compose_file} restart"
        
        if services:
            cmd += f" {' '.join(services)}"
        
        self.run_command(cmd)
        logger.info("Database services restarted")
    
    def show_status(self):
        """Show status of database services"""
        cmd = f"docker-compose -f {self.compose_file} ps"
        result = self.run_command(cmd, check=False)
        print(result.stdout)
    
    def show_logs(self, service=None, follow=False, tail=100):
        """Show logs for database services"""
        cmd = f"docker-compose -f {self.compose_file} logs"
        
        if follow:
            cmd += " -f"
        
        if tail:
            cmd += f" --tail {tail}"
        
        if service:
            cmd += f" {service}"
        
        self.run_command(cmd, check=False)
    
    def execute_sql(self, sql, database=None):
        """Execute SQL command"""
        db_name = database or os.getenv('POSTGRES_DB', 'enterprise_db')
        
        cmd = f"""docker-compose -f {self.compose_file} exec postgres-primary psql -U postgres -d {db_name} -c "{sql}" """
        
        result = self.run_command(cmd, check=False)
        print(result.stdout)
        
        if result.returncode != 0:
            print(result.stderr)
    
    def run_migrations(self, direction='up', target=None):
        """Run database migrations"""
        db_url = self.get_database_url()
        
        cmd = f"python {os.path.join(self.base_dir, 'migrate.py')} --db-url '{db_url}' {direction}"
        
        if target:
            cmd += f" {target}"
        
        self.run_command(cmd)
    
    def seed_database(self, environment='development'):
        """Seed database with sample data"""
        db_url = self.get_database_url()
        
        cmd = f"python {os.path.join(self.base_dir, 'seed.py')} --db-url '{db_url}' seed {environment}"
        
        self.run_command(cmd)
    
    def backup_database(self, output_file=None):
        """Create database backup"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"backup_{timestamp}.sql"
        
        cmd = f"docker-compose -f {self.compose_file} exec postgres-primary pg_dump -U postgres enterprise_db > {output_file}"
        
        self.run_command(cmd)
        logger.info(f"Database backup created: {output_file}")
    
    def restore_database(self, backup_file, force=False):
        """Restore database from backup"""
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return
        
        if not force:
            confirm = input(f"This will overwrite the current database. Continue? (y/N): ")
            if confirm.lower() != 'y':
                logger.info("Restore cancelled")
                return
        
        # Copy backup file to container and restore
        cmd = f"""
        docker cp {backup_file} $(docker-compose -f {self.compose_file} ps -q postgres-primary):/tmp/restore.sql &&
        docker-compose -f {self.compose_file} exec postgres-primary psql -U postgres -d enterprise_db -f /tmp/restore.sql
        """
        
        self.run_command(cmd)
        logger.info("Database restored successfully")
    
    def run_performance_tests(self, output_file=None):
        """Run database performance tests"""
        db_url = self.get_database_url()
        
        cmd = f"python {os.path.join(self.base_dir, 'tests', 'performance_tests.py')} --db-url '{db_url}'"
        
        if output_file:
            cmd += f" --output {output_file}"
        
        self.run_command(cmd)
    
    def monitor_performance(self, duration=3600):
        """Monitor database performance"""
        db_url = self.get_database_url()
        
        cmd = f"python {os.path.join(self.base_dir, 'monitoring', 'performance_monitor.py')} --db-url '{db_url}' --monitor --duration {duration}"
        
        self.run_command(cmd)
    
    def get_database_url(self):
        """Get database connection URL"""
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        database = os.getenv('POSTGRES_DB', 'enterprise_db')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def setup_development(self):
        """Setup development environment"""
        logger.info("Setting up development database environment...")
        
        # Start core services
        self.start_services(['postgres-primary', 'redis', 'pgbouncer'])
        
        # Wait for services to be ready
        import time
        time.sleep(10)
        
        # Run migrations
        self.run_migrations('up')
        
        # Seed with development data
        self.seed_database('development')
        
        logger.info("Development environment setup completed!")
    
    def setup_production(self):
        """Setup production environment"""
        logger.info("Setting up production database environment...")
        
        # Start all production services
        self.start_services(profiles=['monitoring', 'backup'])
        
        # Wait for services to be ready
        import time
        time.sleep(15)
        
        # Run migrations
        self.run_migrations('up')
        
        # Seed with production data
        self.seed_database('production')
        
        logger.info("Production environment setup completed!")
    
    def health_check(self):
        """Perform health check on database services"""
        logger.info("Performing database health check...")
        
        checks = {
            'postgres_primary': self._check_postgres_primary(),
            'postgres_replica': self._check_postgres_replica(),
            'redis': self._check_redis(),
            'pgbouncer': self._check_pgbouncer()
        }
        
        print("\n=== Database Health Check Results ===")
        for service, status in checks.items():
            status_icon = "✅" if status['healthy'] else "❌"
            print(f"{status_icon} {service}: {status['message']}")
        
        return all(check['healthy'] for check in checks.values())
    
    def _check_postgres_primary(self):
        """Check PostgreSQL primary server"""
        try:
            result = self.run_command(
                f"docker-compose -f {self.compose_file} exec postgres-primary pg_isready -U postgres",
                check=False
            )
            return {
                'healthy': result.returncode == 0,
                'message': 'Primary database is ready' if result.returncode == 0 else 'Primary database is not ready'
            }
        except Exception as e:
            return {'healthy': False, 'message': f'Error checking primary: {e}'}
    
    def _check_postgres_replica(self):
        """Check PostgreSQL replica server"""
        try:
            result = self.run_command(
                f"docker-compose -f {self.compose_file} exec postgres-replica pg_isready -U postgres",
                check=False
            )
            return {
                'healthy': result.returncode == 0,
                'message': 'Replica database is ready' if result.returncode == 0 else 'Replica database is not ready'
            }
        except Exception as e:
            return {'healthy': False, 'message': f'Error checking replica: {e}'}
    
    def _check_redis(self):
        """Check Redis server"""
        try:
            result = self.run_command(
                f"docker-compose -f {self.compose_file} exec redis redis-cli ping",
                check=False
            )
            return {
                'healthy': 'PONG' in result.stdout,
                'message': 'Redis is responding' if 'PONG' in result.stdout else 'Redis is not responding'
            }
        except Exception as e:
            return {'healthy': False, 'message': f'Error checking Redis: {e}'}
    
    def _check_pgbouncer(self):
        """Check PgBouncer connection pooler"""
        try:
            result = self.run_command(
                f"docker-compose -f {self.compose_file} exec pgbouncer nc -z localhost 6432",
                check=False
            )
            return {
                'healthy': result.returncode == 0,
                'message': 'PgBouncer is ready' if result.returncode == 0 else 'PgBouncer is not ready'
            }
        except Exception as e:
            return {'healthy': False, 'message': f'Error checking PgBouncer: {e}'}

def main():
    parser = argparse.ArgumentParser(description='Database Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start database services')
    start_parser.add_argument('--services', nargs='+', help='Specific services to start')
    start_parser.add_argument('--profiles', nargs='+', help='Docker compose profiles to include')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop database services')
    stop_parser.add_argument('--services', nargs='+', help='Specific services to stop')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart database services')
    restart_parser.add_argument('--services', nargs='+', help='Specific services to restart')
    
    # Status command
    subparsers.add_parser('status', help='Show status of database services')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show logs for database services')
    logs_parser.add_argument('--service', help='Specific service to show logs for')
    logs_parser.add_argument('--follow', '-f', action='store_true', help='Follow log output')
    logs_parser.add_argument('--tail', type=int, default=100, help='Number of lines to show')
    
    # SQL command
    sql_parser = subparsers.add_parser('sql', help='Execute SQL command')
    sql_parser.add_argument('query', help='SQL query to execute')
    sql_parser.add_argument('--database', help='Database name')
    
    # Migration commands
    migrate_parser = subparsers.add_parser('migrate', help='Run database migrations')
    migrate_parser.add_argument('direction', choices=['up', 'down', 'status'], help='Migration direction')
    migrate_parser.add_argument('--target', help='Target migration version')
    
    # Seed command
    seed_parser = subparsers.add_parser('seed', help='Seed database with sample data')
    seed_parser.add_argument('environment', choices=['development', 'production', 'test'], help='Environment to seed for')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--output', help='Output file path')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument('backup_file', help='Backup file to restore from')
    restore_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Performance commands
    perf_parser = subparsers.add_parser('performance', help='Run performance tests')
    perf_parser.add_argument('--output', help='Output file for results')
    
    monitor_parser = subparsers.add_parser('monitor', help='Monitor database performance')
    monitor_parser.add_argument('--duration', type=int, default=3600, help='Monitoring duration in seconds')
    
    # Setup commands
    subparsers.add_parser('setup-dev', help='Setup development environment')
    subparsers.add_parser('setup-prod', help='Setup production environment')
    
    # Health check command
    subparsers.add_parser('health', help='Perform health check on database services')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DatabaseManager()
    
    try:
        if args.command == 'start':
            manager.start_services(args.services, args.profiles)
        elif args.command == 'stop':
            manager.stop_services(args.services)
        elif args.command == 'restart':
            manager.restart_services(args.services)
        elif args.command == 'status':
            manager.show_status()
        elif args.command == 'logs':
            manager.show_logs(args.service, args.follow, args.tail)
        elif args.command == 'sql':
            manager.execute_sql(args.query, args.database)
        elif args.command == 'migrate':
            manager.run_migrations(args.direction, args.target)
        elif args.command == 'seed':
            manager.seed_database(args.environment)
        elif args.command == 'backup':
            manager.backup_database(args.output)
        elif args.command == 'restore':
            manager.restore_database(args.backup_file, args.force)
        elif args.command == 'performance':
            manager.run_performance_tests(args.output)
        elif args.command == 'monitor':
            manager.monitor_performance(args.duration)
        elif args.command == 'setup-dev':
            manager.setup_development()
        elif args.command == 'setup-prod':
            manager.setup_production()
        elif args.command == 'health':
            healthy = manager.health_check()
            sys.exit(0 if healthy else 1)
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()