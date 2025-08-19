"""
Tests for database monitoring functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import connection

from enterprise_database.monitoring import DatabaseMonitor
from enterprise_database.exceptions import DatabaseError


class TestDatabaseMonitor(TestCase):
    """Test cases for DatabaseMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = DatabaseMonitor()
    
    def test_initialization(self):
        """Test DatabaseMonitor initialization."""
        self.assertIsInstance(self.monitor, DatabaseMonitor)
        self.assertEqual(self.monitor.database_alias, 'default')
    
    def test_initialization_with_custom_alias(self):
        """Test DatabaseMonitor initialization with custom alias."""
        monitor = DatabaseMonitor('read_replica')
        self.assertEqual(monitor.database_alias, 'read_replica')
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_database_stats(self, mock_connection):
        """Test getting database statistics."""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            (100,),  # table_count
            (50000,),  # total_size
            (1000,),  # active_connections
            (500,),   # idle_connections
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        stats = self.monitor.get_database_stats()
        
        expected_stats = {
            'table_count': 100,
            'database_size': 50000,
            'active_connections': 1000,
            'idle_connections': 500,
            'total_connections': 1500
        }
        
        self.assertEqual(stats['table_count'], 100)
        self.assertEqual(stats['database_size'], 50000)
        self.assertEqual(stats['active_connections'], 1000)
        self.assertEqual(stats['idle_connections'], 500)
        self.assertEqual(stats['total_connections'], 1500)
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_active_connections(self, mock_connection):
        """Test getting active connections."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (1, 'SELECT * FROM users', 'active', '2023-01-01 10:00:00'),
            (2, 'UPDATE posts SET status=1', 'active', '2023-01-01 10:01:00')
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        connections = self.monitor.get_active_connections()
        
        self.assertEqual(len(connections), 2)
        self.assertEqual(connections[0]['pid'], 1)
        self.assertEqual(connections[0]['query'], 'SELECT * FROM users')
        self.assertEqual(connections[1]['pid'], 2)
        self.assertEqual(connections[1]['query'], 'UPDATE posts SET status=1')
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_slow_queries(self, mock_connection):
        """Test getting slow queries."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('SELECT * FROM large_table WHERE complex_condition', 5.2, 10),
            ('UPDATE users SET last_login=NOW()', 2.8, 5)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        slow_queries = self.monitor.get_slow_queries(threshold=2.0)
        
        self.assertEqual(len(slow_queries), 2)
        self.assertEqual(slow_queries[0]['query'], 'SELECT * FROM large_table WHERE complex_condition')
        self.assertEqual(slow_queries[0]['avg_duration'], 5.2)
        self.assertEqual(slow_queries[0]['call_count'], 10)
    
    @patch('enterprise_database.monitoring.connection')
    def test_check_health_healthy(self, mock_connection):
        """Test health check when database is healthy."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        health = self.monitor.check_health()
        
        self.assertTrue(health['healthy'])
        self.assertTrue(health['checks']['connection'])
        self.assertTrue(health['checks']['query_execution'])
        self.assertIn('timestamp', health)
    
    @patch('enterprise_database.monitoring.connection')
    def test_check_health_unhealthy(self, mock_connection):
        """Test health check when database is unhealthy."""
        mock_connection.cursor.side_effect = Exception('Connection failed')
        
        health = self.monitor.check_health()
        
        self.assertFalse(health['healthy'])
        self.assertFalse(health['checks']['connection'])
        self.assertFalse(health['checks']['query_execution'])
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_table_stats(self, mock_connection):
        """Test getting table statistics."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('users', 1000, 50000, 10000),
            ('posts', 5000, 200000, 50000),
            ('comments', 15000, 300000, 75000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        table_stats = self.monitor.get_table_stats()
        
        self.assertEqual(len(table_stats), 3)
        self.assertEqual(table_stats[0]['table_name'], 'users')
        self.assertEqual(table_stats[0]['row_count'], 1000)
        self.assertEqual(table_stats[0]['table_size'], 50000)
        self.assertEqual(table_stats[0]['index_size'], 10000)
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_index_usage(self, mock_connection):
        """Test getting index usage statistics."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('users', 'idx_users_email', 1000, 950),
            ('posts', 'idx_posts_created', 5000, 4800),
            ('comments', 'idx_comments_post_id', 15000, 14500)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        index_usage = self.monitor.get_index_usage()
        
        self.assertEqual(len(index_usage), 3)
        self.assertEqual(index_usage[0]['table_name'], 'users')
        self.assertEqual(index_usage[0]['index_name'], 'idx_users_email')
        self.assertEqual(index_usage[0]['total_scans'], 1000)
        self.assertEqual(index_usage[0]['index_scans'], 950)
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_lock_stats(self, mock_connection):
        """Test getting lock statistics."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('users', 'AccessShareLock', 5, False),
            ('posts', 'RowExclusiveLock', 2, True),
            ('comments', 'ShareLock', 1, False)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        lock_stats = self.monitor.get_lock_stats()
        
        self.assertEqual(len(lock_stats), 3)
        self.assertEqual(lock_stats[0]['relation'], 'users')
        self.assertEqual(lock_stats[0]['mode'], 'AccessShareLock')
        self.assertEqual(lock_stats[0]['count'], 5)
        self.assertFalse(lock_stats[0]['granted'])
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_cache_hit_ratio(self, mock_connection):
        """Test getting cache hit ratio."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (95.5,)
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        hit_ratio = self.monitor.get_cache_hit_ratio()
        
        self.assertEqual(hit_ratio, 95.5)
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_replication_lag(self, mock_connection):
        """Test getting replication lag."""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (2.5,)
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        lag = self.monitor.get_replication_lag()
        
        self.assertEqual(lag, 2.5)
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_vacuum_stats(self, mock_connection):
        """Test getting vacuum statistics."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('users', '2023-01-01 10:00:00', '2023-01-01 09:00:00', 1000, 50),
            ('posts', '2023-01-01 11:00:00', '2023-01-01 10:30:00', 5000, 200)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        vacuum_stats = self.monitor.get_vacuum_stats()
        
        self.assertEqual(len(vacuum_stats), 2)
        self.assertEqual(vacuum_stats[0]['table_name'], 'users')
        self.assertEqual(vacuum_stats[0]['dead_tuples'], 1000)
        self.assertEqual(vacuum_stats[0]['live_tuples'], 50)
    
    def test_format_bytes(self):
        """Test byte formatting utility."""
        self.assertEqual(self.monitor.format_bytes(1024), '1.0 KB')
        self.assertEqual(self.monitor.format_bytes(1048576), '1.0 MB')
        self.assertEqual(self.monitor.format_bytes(1073741824), '1.0 GB')
        self.assertEqual(self.monitor.format_bytes(500), '500 B')
    
    def test_calculate_percentage(self):
        """Test percentage calculation utility."""
        self.assertEqual(self.monitor.calculate_percentage(25, 100), 25.0)
        self.assertEqual(self.monitor.calculate_percentage(1, 3), 33.33)
        self.assertEqual(self.monitor.calculate_percentage(0, 100), 0.0)
        self.assertEqual(self.monitor.calculate_percentage(100, 0), 0.0)  # Division by zero
    
    @patch('enterprise_database.monitoring.time.sleep')
    @patch('enterprise_database.monitoring.connection')
    def test_watch_metrics(self, mock_connection, mock_sleep):
        """Test watching metrics in real-time."""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            (10,),  # First iteration
            (15,),  # Second iteration
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock KeyboardInterrupt after 2 iterations
        mock_sleep.side_effect = [None, KeyboardInterrupt()]
        
        # This should not raise an exception
        self.monitor.watch_metrics(interval=1, iterations=2)
        
        # Verify sleep was called
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('enterprise_database.monitoring.connection')
    def test_export_metrics_to_json(self, mock_connection):
        """Test exporting metrics to JSON."""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            (100,),  # table_count
            (50000,),  # total_size
            (10,),   # active_connections
            (5,),    # idle_connections
        ]
        mock_cursor.fetchall.return_value = [
            ('users', 1000, 50000, 10000),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            self.monitor.export_metrics_to_json(f.name)
            
            # Read and verify the exported JSON
            with open(f.name, 'r') as read_file:
                data = json.load(read_file)
                
                self.assertIn('database_stats', data)
                self.assertIn('table_stats', data)
                self.assertIn('timestamp', data)
                self.assertEqual(data['database_stats']['table_count'], 100)
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_query_performance_insights(self, mock_connection):
        """Test getting query performance insights."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('SELECT * FROM users WHERE active = true', 100, 2.5, 250.0),
            ('UPDATE posts SET views = views + 1', 50, 1.2, 60.0)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        insights = self.monitor.get_query_performance_insights()
        
        self.assertEqual(len(insights), 2)
        self.assertEqual(insights[0]['query'], 'SELECT * FROM users WHERE active = true')
        self.assertEqual(insights[0]['calls'], 100)
        self.assertEqual(insights[0]['avg_time'], 2.5)
        self.assertEqual(insights[0]['total_time'], 250.0)
    
    @patch('enterprise_database.monitoring.connection')
    def test_analyze_query_plan(self, mock_connection):
        """Test analyzing query execution plan."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('Seq Scan on users  (cost=0.00..15.00 rows=1000 width=32)',),
            ('  Filter: (active = true)',),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        plan = self.monitor.analyze_query_plan('SELECT * FROM users WHERE active = true')
        
        self.assertEqual(len(plan), 2)
        self.assertIn('Seq Scan', plan[0])
        self.assertIn('Filter', plan[1])
    
    @patch('enterprise_database.monitoring.connection')
    def test_get_blocking_queries(self, mock_connection):
        """Test getting blocking queries."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (123, 'UPDATE users SET last_login = NOW()', 456, 'SELECT * FROM users'),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        blocking = self.monitor.get_blocking_queries()
        
        self.assertEqual(len(blocking), 1)
        self.assertEqual(blocking[0]['blocking_pid'], 123)
        self.assertEqual(blocking[0]['blocking_query'], 'UPDATE users SET last_login = NOW()')
        self.assertEqual(blocking[0]['blocked_pid'], 456)
        self.assertEqual(blocking[0]['blocked_query'], 'SELECT * FROM users')


if __name__ == '__main__':
    pytest.main([__file__])