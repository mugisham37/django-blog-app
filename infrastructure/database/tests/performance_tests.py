#!/usr/bin/env python3
"""
Database Performance Tests
Comprehensive performance testing suite for PostgreSQL database
"""

import time
import psycopg2
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from psycopg2.extras import RealDictCursor
import argparse
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePerformanceTester:
    def __init__(self, connection_string, max_connections=20):
        self.connection_string = connection_string
        self.max_connections = max_connections
        self.results = {}
        
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute query and measure execution time"""
        start_time = time.time()
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchall() if fetch else None
                
        execution_time = time.time() - start_time
        return result, execution_time
    
    def test_connection_performance(self):
        """Test database connection performance"""
        logger.info("Testing connection performance...")
        
        connection_times = []
        
        for i in range(50):
            start_time = time.time()
            try:
                conn = psycopg2.connect(self.connection_string)
                conn.close()
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
            except Exception as e:
                logger.error(f"Connection failed: {e}")
        
        self.results['connection_performance'] = {
            'avg_connection_time': statistics.mean(connection_times),
            'min_connection_time': min(connection_times),
            'max_connection_time': max(connection_times),
            'median_connection_time': statistics.median(connection_times),
            'total_connections_tested': len(connection_times)
        }
    
    def test_simple_queries(self):
        """Test simple query performance"""
        logger.info("Testing simple query performance...")
        
        queries = [
            ("SELECT 1", "simple_select"),
            ("SELECT NOW()", "current_timestamp"),
            ("SELECT count(*) FROM users", "count_users"),
            ("SELECT * FROM users LIMIT 10", "select_users_limit"),
            ("SELECT u.*, r.name as role_name FROM users u LEFT JOIN user_roles ur ON u.id = ur.user_id LEFT JOIN roles r ON ur.role_id = r.id LIMIT 10", "join_query")
        ]
        
        query_results = {}
        
        for query, name in queries:
            times = []
            for _ in range(10):
                try:
                    _, execution_time = self.execute_query(query)
                    times.append(execution_time)
                except Exception as e:
                    logger.error(f"Query failed ({name}): {e}")
            
            if times:
                query_results[name] = {
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'median_time': statistics.median(times)
                }
        
        self.results['simple_queries'] = query_results
    
    def test_concurrent_reads(self, num_threads=10, queries_per_thread=20):
        """Test concurrent read performance"""
        logger.info(f"Testing concurrent reads with {num_threads} threads...")
        
        def read_worker():
            times = []
            for _ in range(queries_per_thread):
                try:
                    _, execution_time = self.execute_query("SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
                    times.append(execution_time)
                except Exception as e:
                    logger.error(f"Concurrent read failed: {e}")
            return times
        
        all_times = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(read_worker) for _ in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    times = future.result()
                    all_times.extend(times)
                except Exception as e:
                    logger.error(f"Thread failed: {e}")
        
        if all_times:
            self.results['concurrent_reads'] = {
                'total_queries': len(all_times),
                'avg_time': statistics.mean(all_times),
                'min_time': min(all_times),
                'max_time': max(all_times),
                'median_time': statistics.median(all_times),
                'queries_per_second': len(all_times) / sum(all_times) if sum(all_times) > 0 else 0
            }
    
    def test_concurrent_writes(self, num_threads=5, writes_per_thread=10):
        """Test concurrent write performance"""
        logger.info(f"Testing concurrent writes with {num_threads} threads...")
        
        def write_worker(thread_id):
            times = []
            for i in range(writes_per_thread):
                try:
                    query = """
                    INSERT INTO audit.audit_log (table_name, operation, new_values, user_id)
                    VALUES (%s, %s, %s, %s)
                    """
                    params = (
                        'performance_test',
                        'INSERT',
                        json.dumps({'thread_id': thread_id, 'iteration': i}),
                        None
                    )
                    _, execution_time = self.execute_query(query, params, fetch=False)
                    times.append(execution_time)
                except Exception as e:
                    logger.error(f"Concurrent write failed: {e}")
            return times
        
        all_times = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(write_worker, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                try:
                    times = future.result()
                    all_times.extend(times)
                except Exception as e:
                    logger.error(f"Write thread failed: {e}")
        
        if all_times:
            self.results['concurrent_writes'] = {
                'total_writes': len(all_times),
                'avg_time': statistics.mean(all_times),
                'min_time': min(all_times),
                'max_time': max(all_times),
                'median_time': statistics.median(all_times),
                'writes_per_second': len(all_times) / sum(all_times) if sum(all_times) > 0 else 0
            }
    
    def test_bulk_operations(self):
        """Test bulk operation performance"""
        logger.info("Testing bulk operations...")
        
        # Test bulk insert
        bulk_insert_query = """
        INSERT INTO audit.audit_log (table_name, operation, new_values)
        SELECT 'bulk_test', 'INSERT', ('{"batch_id": ' || generate_series || '}')::jsonb
        FROM generate_series(1, 1000)
        """
        
        _, bulk_insert_time = self.execute_query(bulk_insert_query, fetch=False)
        
        # Test bulk update
        bulk_update_query = """
        UPDATE audit.audit_log 
        SET new_values = new_values || '{"updated": true}'::jsonb
        WHERE table_name = 'bulk_test'
        """
        
        _, bulk_update_time = self.execute_query(bulk_update_query, fetch=False)
        
        # Test bulk delete
        bulk_delete_query = "DELETE FROM audit.audit_log WHERE table_name = 'bulk_test'"
        
        _, bulk_delete_time = self.execute_query(bulk_delete_query, fetch=False)
        
        self.results['bulk_operations'] = {
            'bulk_insert_1000_records': bulk_insert_time,
            'bulk_update_1000_records': bulk_update_time,
            'bulk_delete_1000_records': bulk_delete_time
        }
    
    def test_index_performance(self):
        """Test index performance"""
        logger.info("Testing index performance...")
        
        # Test queries with and without indexes
        queries = [
            ("SELECT * FROM users WHERE email = 'testuser@test.com'", "email_lookup"),
            ("SELECT * FROM users WHERE username = 'testuser'", "username_lookup"),
            ("SELECT * FROM users WHERE is_active = true", "active_users_lookup"),
            ("SELECT * FROM users ORDER BY created_at DESC LIMIT 10", "recent_users_ordered")
        ]
        
        index_results = {}
        
        for query, name in queries:
            times = []
            for _ in range(5):
                try:
                    _, execution_time = self.execute_query(query)
                    times.append(execution_time)
                except Exception as e:
                    logger.error(f"Index test failed ({name}): {e}")
            
            if times:
                index_results[name] = {
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        
        self.results['index_performance'] = index_results
    
    def test_complex_queries(self):
        """Test complex query performance"""
        logger.info("Testing complex query performance...")
        
        complex_queries = [
            ("""
            SELECT 
                u.username,
                u.email,
                r.name as role_name,
                COUNT(bp.id) as post_count
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            LEFT JOIN blog_posts bp ON u.id = bp.author_id
            WHERE u.is_active = true
            GROUP BY u.id, u.username, u.email, r.name
            ORDER BY post_count DESC
            """, "user_post_statistics"),
            
            ("""
            WITH recent_posts AS (
                SELECT author_id, COUNT(*) as recent_count
                FROM blog_posts
                WHERE created_at > NOW() - INTERVAL '30 days'
                GROUP BY author_id
            )
            SELECT 
                u.username,
                COALESCE(rp.recent_count, 0) as recent_posts
            FROM users u
            LEFT JOIN recent_posts rp ON u.id = rp.author_id
            WHERE u.is_active = true
            ORDER BY recent_posts DESC
            """, "recent_activity_analysis"),
            
            ("""
            SELECT 
                DATE_TRUNC('day', created_at) as day,
                COUNT(*) as registrations
            FROM users
            WHERE created_at > NOW() - INTERVAL '30 days'
            GROUP BY DATE_TRUNC('day', created_at)
            ORDER BY day
            """, "daily_registrations")
        ]
        
        complex_results = {}
        
        for query, name in complex_queries:
            times = []
            for _ in range(3):
                try:
                    _, execution_time = self.execute_query(query)
                    times.append(execution_time)
                except Exception as e:
                    logger.error(f"Complex query failed ({name}): {e}")
            
            if times:
                complex_results[name] = {
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        
        self.results['complex_queries'] = complex_results
    
    def test_transaction_performance(self):
        """Test transaction performance"""
        logger.info("Testing transaction performance...")
        
        # Test simple transaction
        simple_transaction = """
        BEGIN;
        INSERT INTO audit.audit_log (table_name, operation, new_values) 
        VALUES ('transaction_test', 'INSERT', '{"test": true}');
        UPDATE audit.audit_log SET new_values = '{"test": true, "updated": true}' 
        WHERE table_name = 'transaction_test' AND new_values->>'test' = 'true';
        COMMIT;
        """
        
        times = []
        for _ in range(10):
            try:
                _, execution_time = self.execute_query(simple_transaction, fetch=False)
                times.append(execution_time)
            except Exception as e:
                logger.error(f"Transaction test failed: {e}")
        
        # Cleanup
        try:
            self.execute_query("DELETE FROM audit.audit_log WHERE table_name = 'transaction_test'", fetch=False)
        except:
            pass
        
        if times:
            self.results['transaction_performance'] = {
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'transactions_per_second': len(times) / sum(times) if sum(times) > 0 else 0
            }
    
    def run_all_tests(self):
        """Run all performance tests"""
        logger.info("Starting comprehensive database performance tests...")
        
        start_time = time.time()
        
        # Run all test methods
        test_methods = [
            self.test_connection_performance,
            self.test_simple_queries,
            self.test_concurrent_reads,
            self.test_concurrent_writes,
            self.test_bulk_operations,
            self.test_index_performance,
            self.test_complex_queries,
            self.test_transaction_performance
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed: {e}")
        
        total_time = time.time() - start_time
        
        self.results['test_summary'] = {
            'total_test_time': total_time,
            'timestamp': datetime.now().isoformat(),
            'tests_completed': len([k for k in self.results.keys() if k != 'test_summary'])
        }
        
        logger.info(f"Performance tests completed in {total_time:.2f} seconds")
        
        return self.results
    
    def generate_report(self):
        """Generate performance test report"""
        if not self.results:
            return "No test results available"
        
        report = []
        report.append("=" * 60)
        report.append("DATABASE PERFORMANCE TEST REPORT")
        report.append("=" * 60)
        
        if 'test_summary' in self.results:
            summary = self.results['test_summary']
            report.append(f"Test Date: {summary['timestamp']}")
            report.append(f"Total Test Time: {summary['total_test_time']:.2f} seconds")
            report.append(f"Tests Completed: {summary['tests_completed']}")
            report.append("")
        
        for test_name, results in self.results.items():
            if test_name == 'test_summary':
                continue
                
            report.append(f"{test_name.upper().replace('_', ' ')}")
            report.append("-" * 40)
            
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, dict):
                        report.append(f"  {key}:")
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, float):
                                report.append(f"    {subkey}: {subvalue:.4f}s")
                            else:
                                report.append(f"    {subkey}: {subvalue}")
                    else:
                        if isinstance(value, float):
                            report.append(f"  {key}: {value:.4f}s")
                        else:
                            report.append(f"  {key}: {value}")
            
            report.append("")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Database Performance Testing Tool')
    parser.add_argument('--db-url', required=True, help='Database connection URL')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    parser.add_argument('--report', help='Output file for human-readable report')
    parser.add_argument('--threads', type=int, default=10, help='Number of threads for concurrent tests')
    
    args = parser.parse_args()
    
    tester = DatabasePerformanceTester(args.db_url, max_connections=args.threads)
    
    try:
        results = tester.run_all_tests()
        
        # Save JSON results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {args.output}")
        
        # Generate and save report
        report = tester.generate_report()
        
        if args.report:
            with open(args.report, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {args.report}")
        else:
            print(report)
    
    except Exception as e:
        logger.error(f"Performance testing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()