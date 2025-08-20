#!/usr/bin/env python3
"""
PostgreSQL Performance Monitoring Script
Collects and analyzes database performance metrics
"""

import psycopg2
import json
import time
import argparse
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLMonitor:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        
    def get_connection(self):
        return psycopg2.connect(self.connection_string)
    
    def execute_query(self, query, params=None):
        """Execute query and return results"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()
    
    def get_slow_queries(self, limit=20):
        """Get slowest queries from pg_stat_statements"""
        query = """
        SELECT 
            query,
            calls,
            total_time,
            mean_time,
            min_time,
            max_time,
            stddev_time,
            rows,
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements 
        WHERE query NOT LIKE '%pg_stat_statements%'
        ORDER BY mean_time DESC 
        LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def get_database_stats(self):
        """Get database-level statistics"""
        query = """
        SELECT 
            datname,
            numbackends,
            xact_commit,
            xact_rollback,
            blks_read,
            blks_hit,
            tup_returned,
            tup_fetched,
            tup_inserted,
            tup_updated,
            tup_deleted,
            conflicts,
            temp_files,
            temp_bytes,
            deadlocks,
            blk_read_time,
            blk_write_time
        FROM pg_stat_database 
        WHERE datname NOT IN ('template0', 'template1')
        """
        return self.execute_query(query)
    
    def get_table_stats(self):
        """Get table-level statistics"""
        query = """
        SELECT 
            schemaname,
            tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            idx_tup_fetch,
            n_tup_ins,
            n_tup_upd,
            n_tup_del,
            n_live_tup,
            n_dead_tup,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze,
            vacuum_count,
            autovacuum_count,
            analyze_count,
            autoanalyze_count
        FROM pg_stat_user_tables 
        ORDER BY seq_scan + idx_scan DESC
        """
        return self.execute_query(query)
    
    def get_index_stats(self):
        """Get index usage statistics"""
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch,
            pg_size_pretty(pg_relation_size(indexrelid)) AS size
        FROM pg_stat_user_indexes 
        ORDER BY idx_scan DESC
        """
        return self.execute_query(query)
    
    def get_unused_indexes(self):
        """Get unused or rarely used indexes"""
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan,
            pg_size_pretty(pg_relation_size(indexrelid)) AS size,
            pg_relation_size(indexrelid) AS size_bytes
        FROM pg_stat_user_indexes 
        WHERE idx_scan < 10
        ORDER BY pg_relation_size(indexrelid) DESC
        """
        return self.execute_query(query)
    
    def get_connection_stats(self):
        """Get connection statistics"""
        query = """
        SELECT 
            state,
            count(*) as connections,
            max(now() - query_start) as max_duration,
            avg(now() - query_start) as avg_duration
        FROM pg_stat_activity 
        WHERE pid != pg_backend_pid()
        GROUP BY state
        ORDER BY connections DESC
        """
        return self.execute_query(query)
    
    def get_lock_stats(self):
        """Get current locks"""
        query = """
        SELECT 
            l.mode,
            l.locktype,
            l.granted,
            count(*) as count
        FROM pg_locks l
        GROUP BY l.mode, l.locktype, l.granted
        ORDER BY count DESC
        """
        return self.execute_query(query)
    
    def get_cache_hit_ratio(self):
        """Get cache hit ratio"""
        query = """
        SELECT 
            'buffer_cache' as cache_type,
            sum(blks_hit) as hits,
            sum(blks_read) as reads,
            CASE 
                WHEN sum(blks_hit) + sum(blks_read) = 0 THEN 0
                ELSE round(100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2)
            END as hit_ratio
        FROM pg_stat_database
        UNION ALL
        SELECT 
            'index_cache' as cache_type,
            sum(idx_blks_hit) as hits,
            sum(idx_blks_read) as reads,
            CASE 
                WHEN sum(idx_blks_hit) + sum(idx_blks_read) = 0 THEN 0
                ELSE round(100.0 * sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read)), 2)
            END as hit_ratio
        FROM pg_statio_user_indexes
        """
        return self.execute_query(query)
    
    def get_replication_stats(self):
        """Get replication statistics"""
        query = """
        SELECT 
            client_addr,
            application_name,
            state,
            sent_lsn,
            write_lsn,
            flush_lsn,
            replay_lsn,
            write_lag,
            flush_lag,
            replay_lag,
            sync_state
        FROM pg_stat_replication
        """
        return self.execute_query(query)
    
    def analyze_performance(self):
        """Perform comprehensive performance analysis"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'slow_queries': [],
            'database_stats': [],
            'table_stats': [],
            'index_stats': [],
            'unused_indexes': [],
            'connection_stats': [],
            'lock_stats': [],
            'cache_hit_ratio': [],
            'replication_stats': [],
            'recommendations': []
        }
        
        try:
            # Collect statistics
            analysis['slow_queries'] = [dict(row) for row in self.get_slow_queries()]
            analysis['database_stats'] = [dict(row) for row in self.get_database_stats()]
            analysis['table_stats'] = [dict(row) for row in self.get_table_stats()]
            analysis['index_stats'] = [dict(row) for row in self.get_index_stats()]
            analysis['unused_indexes'] = [dict(row) for row in self.get_unused_indexes()]
            analysis['connection_stats'] = [dict(row) for row in self.get_connection_stats()]
            analysis['lock_stats'] = [dict(row) for row in self.get_lock_stats()]
            analysis['cache_hit_ratio'] = [dict(row) for row in self.get_cache_hit_ratio()]
            analysis['replication_stats'] = [dict(row) for row in self.get_replication_stats()]
            
            # Generate recommendations
            analysis['recommendations'] = self.generate_recommendations(analysis)
            
        except Exception as e:
            logger.error(f"Error during performance analysis: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def generate_recommendations(self, analysis):
        """Generate performance recommendations based on analysis"""
        recommendations = []
        
        # Check cache hit ratio
        for cache in analysis['cache_hit_ratio']:
            if cache['hit_ratio'] < 95:
                recommendations.append({
                    'type': 'cache',
                    'severity': 'high' if cache['hit_ratio'] < 90 else 'medium',
                    'message': f"{cache['cache_type']} hit ratio is {cache['hit_ratio']}% (should be >95%)",
                    'suggestion': 'Consider increasing shared_buffers or effective_cache_size'
                })
        
        # Check for unused indexes
        if analysis['unused_indexes']:
            total_size = sum(idx.get('size_bytes', 0) for idx in analysis['unused_indexes'])
            if total_size > 100 * 1024 * 1024:  # 100MB
                recommendations.append({
                    'type': 'index',
                    'severity': 'medium',
                    'message': f"Found {len(analysis['unused_indexes'])} unused indexes consuming significant space",
                    'suggestion': 'Consider dropping unused indexes to save space and improve write performance'
                })
        
        # Check for slow queries
        slow_queries = [q for q in analysis['slow_queries'] if q.get('mean_time', 0) > 1000]  # >1 second
        if slow_queries:
            recommendations.append({
                'type': 'query',
                'severity': 'high',
                'message': f"Found {len(slow_queries)} queries with average execution time >1 second",
                'suggestion': 'Review and optimize slow queries, consider adding indexes'
            })
        
        # Check for tables with high sequential scan ratio
        for table in analysis['table_stats']:
            seq_scans = table.get('seq_scan', 0)
            idx_scans = table.get('idx_scan', 0)
            total_scans = seq_scans + idx_scans
            
            if total_scans > 1000 and seq_scans / total_scans > 0.1:  # >10% sequential scans
                recommendations.append({
                    'type': 'table',
                    'severity': 'medium',
                    'message': f"Table {table['tablename']} has high sequential scan ratio ({seq_scans}/{total_scans})",
                    'suggestion': 'Consider adding indexes for frequently queried columns'
                })
        
        # Check for tables needing vacuum
        for table in analysis['table_stats']:
            dead_tuples = table.get('n_dead_tup', 0)
            live_tuples = table.get('n_live_tup', 0)
            
            if live_tuples > 0 and dead_tuples / live_tuples > 0.1:  # >10% dead tuples
                recommendations.append({
                    'type': 'maintenance',
                    'severity': 'medium',
                    'message': f"Table {table['tablename']} has {dead_tuples} dead tuples ({dead_tuples/live_tuples*100:.1f}%)",
                    'suggestion': 'Consider running VACUUM or adjusting autovacuum settings'
                })
        
        return recommendations
    
    def monitor_continuously(self, interval=60, duration=3600):
        """Monitor database performance continuously"""
        start_time = time.time()
        
        logger.info(f"Starting continuous monitoring for {duration} seconds with {interval}s intervals")
        
        while time.time() - start_time < duration:
            try:
                analysis = self.analyze_performance()
                
                # Log key metrics
                cache_ratios = {c['cache_type']: c['hit_ratio'] for c in analysis['cache_hit_ratio']}
                slow_query_count = len([q for q in analysis['slow_queries'] if q.get('mean_time', 0) > 1000])
                
                logger.info(f"Cache hit ratios: {cache_ratios}, Slow queries: {slow_query_count}")
                
                # Save detailed analysis to file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"performance_analysis_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(analysis, f, indent=2, default=str)
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='PostgreSQL Performance Monitor')
    parser.add_argument('--db-url', required=True, help='Database connection URL')
    parser.add_argument('--analyze', action='store_true', help='Run one-time analysis')
    parser.add_argument('--monitor', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds')
    parser.add_argument('--duration', type=int, default=3600, help='Monitoring duration in seconds')
    parser.add_argument('--output', help='Output file for analysis results')
    
    args = parser.parse_args()
    
    monitor = PostgreSQLMonitor(args.db_url)
    
    if args.analyze:
        analysis = monitor.analyze_performance()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            logger.info(f"Analysis saved to {args.output}")
        else:
            print(json.dumps(analysis, indent=2, default=str))
    
    elif args.monitor:
        monitor.monitor_continuously(args.interval, args.duration)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()