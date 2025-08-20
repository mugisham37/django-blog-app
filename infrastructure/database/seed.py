#!/usr/bin/env python3
"""
Database Seeding Script
Manages data seeding for different environments
"""

import os
import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseSeeder:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.seeds_dir = os.path.join(os.path.dirname(__file__), 'seeds')
        
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def execute_sql_file(self, filepath):
        """Execute SQL file"""
        logger.info(f"Executing SQL file: {filepath}")
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(content)
                    conn.commit()
                    logger.info(f"Successfully executed: {filepath}")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to execute {filepath}: {e}")
                    raise
    
    def seed_environment(self, environment):
        """Seed database for specific environment"""
        seed_files = {
            'development': 'development_seed.sql',
            'production': 'production_seed.sql',
            'test': 'test_seed.sql',
            'staging': 'production_seed.sql'  # Use production seed for staging
        }
        
        if environment not in seed_files:
            raise ValueError(f"Unknown environment: {environment}")
        
        seed_file = seed_files[environment]
        seed_path = os.path.join(self.seeds_dir, seed_file)
        
        if not os.path.exists(seed_path):
            raise FileNotFoundError(f"Seed file not found: {seed_path}")
        
        logger.info(f"Seeding database for {environment} environment")
        self.execute_sql_file(seed_path)
        logger.info(f"Database seeding completed for {environment} environment")
    
    def clear_data(self):
        """Clear all data from database (use with caution!)"""
        logger.warning("Clearing all data from database...")
        
        clear_sql = """
        -- Disable triggers temporarily
        SET session_replication_role = replica;
        
        -- Clear all user data tables
        TRUNCATE TABLE user_roles CASCADE;
        TRUNCATE TABLE users CASCADE;
        TRUNCATE TABLE roles CASCADE;
        
        -- Clear blog data if exists
        DROP TABLE IF EXISTS blog_posts CASCADE;
        DROP TABLE IF EXISTS blog_categories CASCADE;
        DROP TABLE IF EXISTS app_settings CASCADE;
        
        -- Clear audit data
        TRUNCATE TABLE audit.audit_log CASCADE;
        
        -- Re-enable triggers
        SET session_replication_role = DEFAULT;
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(clear_sql)
                    conn.commit()
                    logger.info("Database cleared successfully")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to clear database: {e}")
                    raise
    
    def check_database_status(self):
        """Check current database status"""
        status_queries = {
            'users': "SELECT count(*) FROM users",
            'roles': "SELECT count(*) FROM roles",
            'user_roles': "SELECT count(*) FROM user_roles",
            'blog_categories': "SELECT count(*) FROM blog_categories WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'blog_categories')",
            'blog_posts': "SELECT count(*) FROM blog_posts WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'blog_posts')",
            'app_settings': "SELECT count(*) FROM app_settings WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'app_settings')"
        }
        
        status = {}
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table, query in status_queries.items():
                    try:
                        cur.execute(query)
                        result = cur.fetchone()
                        status[table] = result[0] if result else 0
                    except Exception as e:
                        status[table] = f"Error: {e}"
        
        return status
    
    def create_custom_seed(self, name, sql_content):
        """Create a custom seed file"""
        seed_path = os.path.join(self.seeds_dir, f"{name}_seed.sql")
        
        with open(seed_path, 'w') as f:
            f.write(f"-- Custom seed file: {name}\n")
            f.write(f"-- Generated on: {datetime.now().isoformat()}\n\n")
            f.write("BEGIN;\n\n")
            f.write(sql_content)
            f.write("\n\nCOMMIT;\n")
        
        logger.info(f"Custom seed file created: {seed_path}")
        return seed_path

def main():
    parser = argparse.ArgumentParser(description='Database Seeding Tool')
    parser.add_argument('--db-url', required=True, help='Database connection URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Seed command
    seed_parser = subparsers.add_parser('seed', help='Seed database for environment')
    seed_parser.add_argument('environment', choices=['development', 'production', 'test', 'staging'],
                           help='Environment to seed')
    
    # Status command
    subparsers.add_parser('status', help='Show database seeding status')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all data from database')
    clear_parser.add_argument('--confirm', action='store_true', 
                            help='Confirm that you want to clear all data')
    
    # Custom seed command
    custom_parser = subparsers.add_parser('custom', help='Execute custom seed file')
    custom_parser.add_argument('file', help='Path to custom seed SQL file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    seeder = DatabaseSeeder(args.db_url)
    
    try:
        if args.command == 'seed':
            seeder.seed_environment(args.environment)
            
        elif args.command == 'status':
            status = seeder.check_database_status()
            print("\n=== Database Seeding Status ===")
            for table, count in status.items():
                print(f"{table}: {count}")
            
        elif args.command == 'clear':
            if not args.confirm:
                print("⚠️  This will delete ALL data from the database!")
                confirm = input("Type 'DELETE ALL DATA' to confirm: ")
                if confirm != 'DELETE ALL DATA':
                    print("Operation cancelled")
                    return
            
            seeder.clear_data()
            
        elif args.command == 'custom':
            if not os.path.exists(args.file):
                logger.error(f"Custom seed file not found: {args.file}")
                sys.exit(1)
            
            seeder.execute_sql_file(args.file)
    
    except Exception as e:
        logger.error(f"Seeding operation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()