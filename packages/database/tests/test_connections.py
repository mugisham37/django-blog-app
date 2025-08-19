"""
Tests for database connection management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.db import connections

from enterprise_database.connections import ConnectionManager
from enterprise_database.exceptions import DatabaseError


class TestConnectionManager(TestCase):
    """Test cases for ConnectionManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.connection_manager = ConnectionManager()
    
    def test_initialization(self):
        """Test ConnectionManager initialization."""
        self.assertIsInstance(self.connection_manager, ConnectionManager)
        self.assertEqual(self.connection_manager.default_alias, 'default')
    
    @patch('enterprise_database.connections.connections')
    def test_get_connection(self, mock_connections):
        """Test getting database connection."""
        mock_connection = Mock()
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.get_connection('default')
        
        mock_connections.__getitem__.assert_called_once_with('default')
        self.assertEqual(result, mock_connection)
    
    @patch('enterprise_database.connections.connections')
    def test_get_connection_invalid_alias(self, mock_connections):
        """Test getting connection with invalid alias."""
        mock_connections.__getitem__.side_effect = KeyError('invalid')
        
        with self.assertRaises(DatabaseError):
            self.connection_manager.get_connection('invalid')
    
    @patch('enterprise_database.connections.connections')
    def test_close_connection(self, mock_connections):
        """Test closing database connection."""
        mock_connection = Mock()
        mock_connections.__getitem__.return_value = mock_connection
        
        self.connection_manager.close_connection('default')
        
        mock_connection.close.assert_called_once()
    
    @patch('enterprise_database.connections.connections')
    def test_close_all_connections(self, mock_connections):
        """Test closing all database connections."""
        self.connection_manager.close_all_connections()
        
        mock_connections.close_all.assert_called_once()
    
    @patch('enterprise_database.connections.connections')
    def test_test_connection_success(self, mock_connections):
        """Test successful connection test."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.test_connection('default')
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with('SELECT 1')
    
    @patch('enterprise_database.connections.connections')
    def test_test_connection_failure(self, mock_connections):
        """Test failed connection test."""
        mock_connection = Mock()
        mock_connection.cursor.side_effect = Exception('Connection failed')
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.test_connection('default')
        
        self.assertFalse(result)
    
    @patch('enterprise_database.connections.connections')
    def test_get_connection_info(self, mock_connections):
        """Test getting connection information."""
        mock_connection = Mock()
        mock_connection.settings_dict = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_db',
            'HOST': 'localhost',
            'PORT': '5432',
            'USER': 'test_user'
        }
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.get_connection_info('default')
        
        expected_info = {
            'alias': 'default',
            'engine': 'django.db.backends.postgresql',
            'name': 'test_db',
            'host': 'localhost',
            'port': '5432',
            'user': 'test_user',
            'is_connected': True
        }
        
        # Check that all expected keys are present
        for key, value in expected_info.items():
            if key != 'is_connected':  # Skip is_connected as it's mocked
                self.assertEqual(result[key], value)
    
    @patch('enterprise_database.connections.connections')
    def test_get_all_connections_info(self, mock_connections):
        """Test getting all connections information."""
        mock_connections.all.return_value = ['default', 'read_replica']
        
        with patch.object(self.connection_manager, 'get_connection_info') as mock_get_info:
            mock_get_info.side_effect = [
                {'alias': 'default', 'engine': 'postgresql'},
                {'alias': 'read_replica', 'engine': 'postgresql'}
            ]
            
            result = self.connection_manager.get_all_connections_info()
            
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['alias'], 'default')
            self.assertEqual(result[1]['alias'], 'read_replica')
    
    @patch('enterprise_database.connections.connections')
    def test_execute_raw_sql(self, mock_connections):
        """Test executing raw SQL."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('result1',), ('result2',)]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.execute_raw_sql(
            'SELECT name FROM test_table',
            params=['param1'],
            alias='default'
        )
        
        mock_cursor.execute.assert_called_once_with('SELECT name FROM test_table', ['param1'])
        mock_cursor.fetchall.assert_called_once()
        self.assertEqual(result, [('result1',), ('result2',)])
    
    @patch('enterprise_database.connections.connections')
    def test_execute_raw_sql_error(self, mock_connections):
        """Test executing raw SQL with error."""
        mock_connection = Mock()
        mock_connection.cursor.side_effect = Exception('SQL error')
        mock_connections.__getitem__.return_value = mock_connection
        
        with self.assertRaises(DatabaseError):
            self.connection_manager.execute_raw_sql('SELECT 1')
    
    @patch('enterprise_database.connections.connections')
    def test_get_database_size(self, mock_connections):
        """Test getting database size."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1024000,)  # 1MB in bytes
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.get_database_size('default')
        
        self.assertEqual(result, 1024000)
        mock_cursor.execute.assert_called_once()
    
    @patch('enterprise_database.connections.connections')
    def test_get_table_sizes(self, mock_connections):
        """Test getting table sizes."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('table1', 1024),
            ('table2', 2048)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.get_table_sizes('default')
        
        expected_result = {
            'table1': 1024,
            'table2': 2048
        }
        self.assertEqual(result, expected_result)
    
    @patch('enterprise_database.connections.connections')
    def test_get_active_queries(self, mock_connections):
        """Test getting active queries."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (1, 'SELECT * FROM table1', '2023-01-01 10:00:00'),
            (2, 'UPDATE table2 SET field=1', '2023-01-01 10:01:00')
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.get_active_queries('default')
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['pid'], 1)
        self.assertEqual(result[0]['query'], 'SELECT * FROM table1')
    
    @patch('enterprise_database.connections.connections')
    def test_kill_query(self, mock_connections):
        """Test killing a query."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.kill_query(123, 'default')
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
    
    @patch('enterprise_database.connections.connections')
    def test_vacuum_database(self, mock_connections):
        """Test vacuuming database."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.vacuum_database('default')
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with('VACUUM ANALYZE')
    
    @patch('enterprise_database.connections.connections')
    def test_analyze_database(self, mock_connections):
        """Test analyzing database."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.settings_dict = {'ENGINE': 'django.db.backends.postgresql'}
        mock_connections.__getitem__.return_value = mock_connection
        
        result = self.connection_manager.analyze_database('default')
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once_with('ANALYZE')
    
    @patch('enterprise_database.connections.connections')
    def test_get_connection_pool_status(self, mock_connections):
        """Test getting connection pool status."""
        mock_connection = Mock()
        mock_connection.queries_logged = 10
        mock_connection.queries = []
        mock_connections.__getitem__.return_value = mock_connection
        
        # Mock connection pool attributes
        mock_connection.connection = Mock()
        mock_connection.connection.get_dsn_parameters = Mock(return_value={
            'host': 'localhost',
            'port': '5432',
            'dbname': 'test_db'
        })
        
        result = self.connection_manager.get_connection_pool_status('default')
        
        self.assertIn('alias', result)
        self.assertIn('queries_logged', result)
        self.assertEqual(result['alias'], 'default')
        self.assertEqual(result['queries_logged'], 10)
    
    def test_create_connection_pool(self):
        """Test creating connection pool."""
        pool_config = {
            'min_connections': 5,
            'max_connections': 20,
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_pass'
        }
        
        with patch('enterprise_database.connections.psycopg2.pool.ThreadedConnectionPool') as mock_pool:
            mock_pool_instance = Mock()
            mock_pool.return_value = mock_pool_instance
            
            result = self.connection_manager.create_connection_pool(pool_config)
            
            mock_pool.assert_called_once_with(
                minconn=5,
                maxconn=20,
                host='localhost',
                port=5432,
                database='test_db',
                user='test_user',
                password='test_pass'
            )
            self.assertEqual(result, mock_pool_instance)
    
    def test_close_connection_pool(self):
        """Test closing connection pool."""
        mock_pool = Mock()
        
        self.connection_manager.close_connection_pool(mock_pool)
        
        mock_pool.closeall.assert_called_once()
    
    @patch('enterprise_database.connections.time.sleep')
    def test_wait_for_connection(self, mock_sleep):
        """Test waiting for database connection."""
        with patch.object(self.connection_manager, 'test_connection') as mock_test:
            # First call fails, second succeeds
            mock_test.side_effect = [False, True]
            
            result = self.connection_manager.wait_for_connection('default', timeout=10, interval=1)
            
            self.assertTrue(result)
            self.assertEqual(mock_test.call_count, 2)
            mock_sleep.assert_called_once_with(1)
    
    @patch('enterprise_database.connections.time.sleep')
    def test_wait_for_connection_timeout(self, mock_sleep):
        """Test waiting for connection with timeout."""
        with patch.object(self.connection_manager, 'test_connection') as mock_test:
            mock_test.return_value = False
            
            result = self.connection_manager.wait_for_connection('default', timeout=2, interval=1)
            
            self.assertFalse(result)
            # Should try at least twice (initial + after 1 second)
            self.assertGreaterEqual(mock_test.call_count, 2)


if __name__ == '__main__':
    pytest.main([__file__])