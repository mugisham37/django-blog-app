"""
Tests for database configuration management.
"""

import pytest
from unittest.mock import Mock, patch
from django.test import TestCase, override_settings

from enterprise_database.config import (
    DatabaseConfig,
    get_database_config,
    setup_read_replica,
    validate_database_config,
    get_connection_pool_config
)
from enterprise_database.exceptions import DatabaseConfigError


class TestDatabaseConfig(TestCase):
    """Test cases for DatabaseConfig class."""
    
    def test_initialization_with_defaults(self):
        """Test DatabaseConfig initialization with default values."""
        config = DatabaseConfig()
        
        self.assertEqual(config.engine, 'django.db.backends.postgresql')
        self.assertEqual(config.name, 'personal_blog')
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 5432)
        self.assertEqual(config.user, 'postgres')
        self.assertEqual(config.password, '')
        self.assertEqual(config.conn_max_age, 600)
        self.assertTrue(config.conn_health_checks)
    
    def test_initialization_with_custom_values(self):
        """Test DatabaseConfig initialization with custom values."""
        config = DatabaseConfig(
            engine='django.db.backends.mysql',
            name='custom_db',
            host='db.example.com',
            port=3306,
            user='custom_user',
            password='secret',
            conn_max_age=300,
            conn_health_checks=False
        )
        
        self.assertEqual(config.engine, 'django.db.backends.mysql')
        self.assertEqual(config.name, 'custom_db')
        self.assertEqual(config.host, 'db.example.com')
        self.assertEqual(config.port, 3306)
        self.assertEqual(config.user, 'custom_user')
        self.assertEqual(config.password, 'secret')
        self.assertEqual(config.conn_max_age, 300)
        self.assertFalse(config.conn_health_checks)
    
    def test_to_django_config(self):
        """Test converting to Django database configuration."""
        config = DatabaseConfig(
            name='test_db',
            host='test_host',
            port=5432,
            user='test_user',
            password='test_pass'
        )
        
        django_config = config.to_django_config()
        
        expected_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_db',
            'HOST': 'test_host',
            'PORT': 5432,
            'USER': 'test_user',
            'PASSWORD': 'test_pass',
            'OPTIONS': {
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
                'MAX_CONNS': 20,
                'MIN_CONNS': 5,
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
                'use_unicode': True,
                'POOL_CLASS': 'psycopg2.pool.ThreadedConnectionPool',
                'POOL_SIZE': 10,
                'MAX_OVERFLOW': 20,
                'autocommit': True,
                'isolation_level': None,
                'sslmode': 'prefer',
                'sslcert': '',
                'sslkey': '',
                'sslrootcert': '',
                'server_side_binding': True,
                'prepared_statements': True,
                'statement_timeout': 30000,
                'lock_timeout': 10000,
                'RETRY_ATTEMPTS': 3,
                'RETRY_DELAY': 1,
            },
            'TEST': {
                'NAME': 'test_test_db',
                'CHARSET': 'utf8mb4',
                'COLLATION': 'utf8mb4_unicode_ci',
            }
        }
        
        self.assertEqual(django_config['ENGINE'], expected_config['ENGINE'])
        self.assertEqual(django_config['NAME'], expected_config['NAME'])
        self.assertEqual(django_config['HOST'], expected_config['HOST'])
        self.assertEqual(django_config['PORT'], expected_config['PORT'])
        self.assertEqual(django_config['USER'], expected_config['USER'])
        self.assertEqual(django_config['PASSWORD'], expected_config['PASSWORD'])
        self.assertIn('OPTIONS', django_config)
        self.assertIn('TEST', django_config)
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = DatabaseConfig()
        
        # Should not raise any exception
        config.validate()
    
    def test_validate_invalid_engine(self):
        """Test validation with invalid engine."""
        config = DatabaseConfig(engine='invalid.engine')
        
        with self.assertRaises(DatabaseConfigError):
            config.validate()
    
    def test_validate_empty_name(self):
        """Test validation with empty database name."""
        config = DatabaseConfig(name='')
        
        with self.assertRaises(DatabaseConfigError):
            config.validate()
    
    def test_validate_invalid_port(self):
        """Test validation with invalid port."""
        config = DatabaseConfig(port=0)
        
        with self.assertRaises(DatabaseConfigError):
            config.validate()
    
    def test_validate_negative_conn_max_age(self):
        """Test validation with negative conn_max_age."""
        config = DatabaseConfig(conn_max_age=-1)
        
        with self.assertRaises(DatabaseConfigError):
            config.validate()
    
    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            'engine': 'django.db.backends.mysql',
            'name': 'test_db',
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_pass',
            'conn_max_age': 300,
            'conn_health_checks': False
        }
        
        config = DatabaseConfig.from_dict(config_dict)
        
        self.assertEqual(config.engine, 'django.db.backends.mysql')
        self.assertEqual(config.name, 'test_db')
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 3306)
        self.assertEqual(config.user, 'test_user')
        self.assertEqual(config.password, 'test_pass')
        self.assertEqual(config.conn_max_age, 300)
        self.assertFalse(config.conn_health_checks)
    
    def test_from_dict_with_missing_keys(self):
        """Test creating config from dictionary with missing keys."""
        config_dict = {
            'name': 'test_db',
            'host': 'localhost'
        }
        
        config = DatabaseConfig.from_dict(config_dict)
        
        # Should use defaults for missing keys
        self.assertEqual(config.name, 'test_db')
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.engine, 'django.db.backends.postgresql')  # default
        self.assertEqual(config.port, 5432)  # default
    
    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = DatabaseConfig(
            name='test_db',
            host='test_host',
            port=5432,
            user='test_user'
        )
        
        config_dict = config.to_dict()
        
        expected_keys = [
            'engine', 'name', 'host', 'port', 'user', 'password',
            'conn_max_age', 'conn_health_checks', 'max_conns', 'min_conns',
            'pool_size', 'max_overflow', 'ssl_mode', 'ssl_cert', 'ssl_key',
            'ssl_root_cert', 'statement_timeout', 'lock_timeout',
            'retry_attempts', 'retry_delay'
        ]
        
        for key in expected_keys:
            self.assertIn(key, config_dict)
        
        self.assertEqual(config_dict['name'], 'test_db')
        self.assertEqual(config_dict['host'], 'test_host')
        self.assertEqual(config_dict['port'], 5432)
        self.assertEqual(config_dict['user'], 'test_user')


class TestDatabaseConfigFunctions(TestCase):
    """Test cases for database configuration functions."""
    
    @patch('enterprise_database.config.config')
    def test_get_database_config_development(self, mock_config):
        """Test getting database config for development environment."""
        # Mock environment variables
        mock_config.side_effect = lambda key, default=None, cast=None: {
            'DB_NAME': 'dev_db',
            'DB_USER': 'dev_user',
            'DB_PASSWORD': 'dev_pass',
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_MAX_CONNS': '10',
            'DB_MIN_CONNS': '2',
            'DB_CONN_MAX_AGE': '300',
            'DB_CONN_HEALTH_CHECKS': 'True'
        }.get(key, default)
        
        db_config = get_database_config('development')
        
        self.assertEqual(db_config['NAME'], 'dev_db')
        self.assertEqual(db_config['USER'], 'dev_user')
        self.assertEqual(db_config['PASSWORD'], 'dev_pass')
        self.assertEqual(db_config['HOST'], 'localhost')
        self.assertEqual(db_config['PORT'], '5432')
        self.assertEqual(db_config['OPTIONS']['CONN_MAX_AGE'], 300)
        self.assertEqual(db_config['OPTIONS']['MAX_CONNS'], 10)
    
    @patch('enterprise_database.config.config')
    def test_get_database_config_production(self, mock_config):
        """Test getting database config for production environment."""
        mock_config.side_effect = lambda key, default=None, cast=None: {
            'DB_NAME': 'prod_db',
            'DB_USER': 'prod_user',
            'DB_PASSWORD': 'prod_pass',
            'DB_HOST': 'prod.db.com',
            'DB_PORT': '5432'
        }.get(key, default)
        
        db_config = get_database_config('production')
        
        self.assertEqual(db_config['NAME'], 'prod_db')
        self.assertEqual(db_config['OPTIONS']['CONN_MAX_AGE'], 3600)  # Production default
        self.assertEqual(db_config['OPTIONS']['MAX_CONNS'], 50)  # Production default
        self.assertEqual(db_config['OPTIONS']['POOL_SIZE'], 20)  # Production default
    
    @patch('enterprise_database.config.config')
    def test_get_database_config_testing(self, mock_config):
        """Test getting database config for testing environment."""
        mock_config.side_effect = lambda key, default=None, cast=None: {
            'DB_NAME': 'test_db',
            'DB_TEST_NAME': 'test_test_db'
        }.get(key, default)
        
        db_config = get_database_config('testing')
        
        self.assertEqual(db_config['NAME'], 'test_test_db')  # Uses test database name
        self.assertEqual(db_config['OPTIONS']['CONN_MAX_AGE'], 0)  # No connection reuse in tests
        self.assertEqual(db_config['OPTIONS']['MAX_CONNS'], 5)  # Testing default
    
    def test_get_database_config_invalid_environment(self):
        """Test getting database config for invalid environment."""
        with self.assertRaises(DatabaseConfigError):
            get_database_config('invalid_env')
    
    @patch('enterprise_database.config.config')
    def test_setup_read_replica(self, mock_config):
        """Test setting up read replica configuration."""
        mock_config.side_effect = lambda key, default=None, cast=None: {
            'DB_READ_NAME': 'replica_db',
            'DB_READ_USER': 'replica_user',
            'DB_READ_PASSWORD': 'replica_pass',
            'DB_READ_HOST': 'replica.db.com',
            'DB_READ_PORT': '5432'
        }.get(key, default)
        
        primary_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'primary_db',
            'USER': 'primary_user',
            'PASSWORD': 'primary_pass',
            'HOST': 'primary.db.com',
            'PORT': '5432',
            'OPTIONS': {'CONN_MAX_AGE': 600}
        }
        
        replica_config = setup_read_replica(primary_config)
        
        self.assertEqual(replica_config['NAME'], 'replica_db')
        self.assertEqual(replica_config['USER'], 'replica_user')
        self.assertEqual(replica_config['PASSWORD'], 'replica_pass')
        self.assertEqual(replica_config['HOST'], 'replica.db.com')
        self.assertEqual(replica_config['PORT'], '5432')
        self.assertEqual(replica_config['ENGINE'], primary_config['ENGINE'])
        self.assertEqual(replica_config['OPTIONS'], primary_config['OPTIONS'])
    
    @patch('enterprise_database.config.config')
    def test_setup_read_replica_fallback_to_primary(self, mock_config):
        """Test setting up read replica with fallback to primary config."""
        mock_config.side_effect = lambda key, default=None, cast=None: default
        
        primary_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'primary_db',
            'USER': 'primary_user',
            'PASSWORD': 'primary_pass',
            'HOST': 'primary.db.com',
            'PORT': '5432',
            'OPTIONS': {'CONN_MAX_AGE': 600}
        }
        
        replica_config = setup_read_replica(primary_config)
        
        # Should fallback to primary config values
        self.assertEqual(replica_config['NAME'], 'primary_db')
        self.assertEqual(replica_config['USER'], 'primary_user')
        self.assertEqual(replica_config['HOST'], 'primary.db.com')
    
    def test_validate_database_config_valid(self):
        """Test validation of valid database configuration."""
        valid_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_db',
            'HOST': 'localhost',
            'PORT': 5432,
            'USER': 'test_user',
            'PASSWORD': 'test_pass'
        }
        
        # Should not raise any exception
        validate_database_config(valid_config)
    
    def test_validate_database_config_missing_engine(self):
        """Test validation with missing ENGINE."""
        invalid_config = {
            'NAME': 'test_db',
            'HOST': 'localhost'
        }
        
        with self.assertRaises(DatabaseConfigError):
            validate_database_config(invalid_config)
    
    def test_validate_database_config_missing_name(self):
        """Test validation with missing NAME."""
        invalid_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': 'localhost'
        }
        
        with self.assertRaises(DatabaseConfigError):
            validate_database_config(invalid_config)
    
    def test_validate_database_config_invalid_engine(self):
        """Test validation with invalid ENGINE."""
        invalid_config = {
            'ENGINE': 'invalid.backend',
            'NAME': 'test_db',
            'HOST': 'localhost'
        }
        
        with self.assertRaises(DatabaseConfigError):
            validate_database_config(invalid_config)
    
    def test_validate_database_config_invalid_port(self):
        """Test validation with invalid PORT."""
        invalid_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_db',
            'HOST': 'localhost',
            'PORT': 'invalid_port'
        }
        
        with self.assertRaises(DatabaseConfigError):
            validate_database_config(invalid_config)
    
    @patch('enterprise_database.config.config')
    def test_get_connection_pool_config(self, mock_config):
        """Test getting connection pool configuration."""
        mock_config.side_effect = lambda key, default=None, cast=None: {
            'DB_POOL_SIZE': '15',
            'DB_MAX_OVERFLOW': '25',
            'DB_POOL_TIMEOUT': '30',
            'DB_POOL_RECYCLE': '3600'
        }.get(key, default)
        
        pool_config = get_connection_pool_config()
        
        expected_config = {
            'pool_size': 15,
            'max_overflow': 25,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'pool_reset_on_return': 'commit'
        }
        
        self.assertEqual(pool_config['pool_size'], 15)
        self.assertEqual(pool_config['max_overflow'], 25)
        self.assertEqual(pool_config['pool_timeout'], 30)
        self.assertEqual(pool_config['pool_recycle'], 3600)
        self.assertTrue(pool_config['pool_pre_ping'])
        self.assertEqual(pool_config['pool_reset_on_return'], 'commit')
    
    @patch('enterprise_database.config.config')
    def test_get_connection_pool_config_defaults(self, mock_config):
        """Test getting connection pool configuration with defaults."""
        mock_config.side_effect = lambda key, default=None, cast=None: default
        
        pool_config = get_connection_pool_config()
        
        # Should use default values
        self.assertEqual(pool_config['pool_size'], 10)
        self.assertEqual(pool_config['max_overflow'], 20)
        self.assertEqual(pool_config['pool_timeout'], 30)
        self.assertEqual(pool_config['pool_recycle'], 3600)


if __name__ == '__main__':
    pytest.main([__file__])