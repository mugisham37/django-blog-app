"""
Tests for database routing functionality.
"""

import pytest
from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
from django.contrib.auth.models import User

from enterprise_database.routers import (
    DatabaseRouter,
    ReadWriteRouter,
    MultiTenantRouter,
    ShardingRouter,
    get_database_for_model
)


class TestDatabaseRouter(TestCase):
    """Test cases for DatabaseRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = DatabaseRouter()
    
    def test_db_for_read_primary_only_model(self):
        """Test routing reads for primary-only models."""
        result = self.router.db_for_read(User)
        self.assertEqual(result, 'default')
    
    @override_settings(DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'read_replica': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
    })
    @patch.object(DatabaseRouter, '_in_transaction')
    def test_db_for_read_with_replica(self, mock_in_transaction):
        """Test routing reads to replica when available."""
        mock_in_transaction.return_value = False
        
        # Create a mock model that's not in PRIMARY_ONLY_MODELS
        mock_model = Mock()
        mock_model._meta.app_label = 'blog'
        mock_model.__name__ = 'Post'
        
        result = self.router.db_for_read(mock_model)
        self.assertEqual(result, 'read_replica')
    
    @patch.object(DatabaseRouter, '_in_transaction')
    def test_db_for_read_in_transaction(self, mock_in_transaction):
        """Test routing reads when in transaction."""
        mock_in_transaction.return_value = True
        
        mock_model = Mock()
        mock_model._meta.app_label = 'blog'
        mock_model.__name__ = 'Post'
        
        result = self.router.db_for_read(mock_model)
        self.assertEqual(result, 'default')
    
    def test_db_for_write(self):
        """Test routing writes always to primary."""
        mock_model = Mock()
        mock_model._meta.app_label = 'blog'
        mock_model.__name__ = 'Post'
        
        result = self.router.db_for_write(mock_model)
        self.assertEqual(result, 'default')
    
    def test_db_for_write_with_app_mapping(self):
        """Test routing writes with app-specific mapping."""
        self.router.APP_DATABASE_MAPPING = {'analytics': 'analytics_db'}
        
        mock_model = Mock()
        mock_model._meta.app_label = 'analytics'
        mock_model.__name__ = 'Event'
        
        result = self.router.db_for_write(mock_model)
        self.assertEqual(result, 'analytics_db')
    
    @override_settings(DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'read_replica': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
    })
    def test_allow_relation(self):
        """Test allowing relations between objects."""
        obj1 = Mock()
        obj1._state.db = 'default'
        
        obj2 = Mock()
        obj2._state.db = 'read_replica'
        
        result = self.router.allow_relation(obj1, obj2)
        self.assertTrue(result)
    
    def test_allow_relation_different_databases(self):
        """Test disallowing relations between incompatible databases."""
        obj1 = Mock()
        obj1._state.db = 'default'
        
        obj2 = Mock()
        obj2._state.db = 'external_db'
        
        result = self.router.allow_relation(obj1, obj2)
        self.assertIsNone(result)
    
    def test_allow_migrate_read_replica(self):
        """Test preventing migrations on read replica."""
        result = self.router.allow_migrate('read_replica', 'blog')
        self.assertFalse(result)
    
    def test_allow_migrate_default(self):
        """Test allowing migrations on default database."""
        result = self.router.allow_migrate('default', 'blog')
        self.assertTrue(result)
    
    def test_allow_migrate_app_mapping(self):
        """Test migrations with app-specific mapping."""
        self.router.APP_DATABASE_MAPPING = {'analytics': 'analytics_db'}
        
        result = self.router.allow_migrate('analytics_db', 'analytics')
        self.assertTrue(result)
        
        result = self.router.allow_migrate('default', 'analytics')
        self.assertFalse(result)
    
    @override_settings(DATABASES={
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
        'read_replica': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
    })
    def test_has_read_replica(self):
        """Test checking for read replica availability."""
        self.assertTrue(self.router._has_read_replica())
    
    def test_has_read_replica_false(self):
        """Test checking for read replica when not available."""
        with override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3'}}):
            self.assertFalse(self.router._has_read_replica())


class TestReadWriteRouter(TestCase):
    """Test cases for ReadWriteRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = ReadWriteRouter()
    
    @patch.object(ReadWriteRouter, '_has_read_replica')
    @patch.object(ReadWriteRouter, '_in_transaction')
    def test_route_read_to_replica(self, mock_in_transaction, mock_has_replica):
        """Test determining if reads should go to replica."""
        mock_in_transaction.return_value = False
        mock_has_replica.return_value = True
        
        mock_model = Mock()
        mock_model._meta.app_label = 'blog'
        mock_model.__name__ = 'Post'
        
        result = self.router.route_read_to_replica(mock_model)
        self.assertTrue(result)
    
    def test_route_read_to_replica_primary_only(self):
        """Test not routing primary-only models to replica."""
        result = self.router.route_read_to_replica(User)
        self.assertFalse(result)
    
    @patch.object(ReadWriteRouter, '_in_transaction')
    def test_route_read_to_replica_in_transaction(self, mock_in_transaction):
        """Test not routing to replica when in transaction."""
        mock_in_transaction.return_value = True
        
        mock_model = Mock()
        mock_model._meta.app_label = 'blog'
        mock_model.__name__ = 'Post'
        
        result = self.router.route_read_to_replica(mock_model)
        self.assertFalse(result)
    
    @patch.object(ReadWriteRouter, 'db_for_read')
    def test_get_database_for_model_read(self, mock_db_for_read):
        """Test getting database for read operation."""
        mock_db_for_read.return_value = 'read_replica'
        
        mock_model = Mock()
        result = self.router.get_database_for_model(mock_model, 'read')
        
        self.assertEqual(result, 'read_replica')
        mock_db_for_read.assert_called_once_with(mock_model)
    
    @patch.object(ReadWriteRouter, 'db_for_write')
    def test_get_database_for_model_write(self, mock_db_for_write):
        """Test getting database for write operation."""
        mock_db_for_write.return_value = 'default'
        
        mock_model = Mock()
        result = self.router.get_database_for_model(mock_model, 'write')
        
        self.assertEqual(result, 'default')
        mock_db_for_write.assert_called_once_with(mock_model)


class TestMultiTenantRouter(TestCase):
    """Test cases for MultiTenantRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = MultiTenantRouter()
    
    def test_get_tenant_database_default(self):
        """Test getting default database for unknown tenant."""
        result = self.router.get_tenant_database('unknown_tenant')
        self.assertEqual(result, 'default')
    
    def test_set_and_get_tenant_database(self):
        """Test setting and getting tenant database."""
        self.router.set_tenant_database('tenant1', 'tenant1_db')
        result = self.router.get_tenant_database('tenant1')
        self.assertEqual(result, 'tenant1_db')
    
    @patch.object(MultiTenantRouter, 'get_tenant_database')
    def test_db_for_read_with_tenant(self, mock_get_tenant_db):
        """Test routing reads with tenant context."""
        mock_get_tenant_db.return_value = 'tenant1_db'
        
        mock_model = Mock()
        result = self.router.db_for_read(mock_model, tenant_id='tenant1')
        
        self.assertEqual(result, 'tenant1_db')
        mock_get_tenant_db.assert_called_once_with('tenant1')
    
    @patch.object(DatabaseRouter, 'db_for_read')
    def test_db_for_read_without_tenant(self, mock_super_db_for_read):
        """Test routing reads without tenant context."""
        mock_super_db_for_read.return_value = 'default'
        
        mock_model = Mock()
        result = self.router.db_for_read(mock_model)
        
        self.assertEqual(result, 'default')
        mock_super_db_for_read.assert_called_once()
    
    @patch.object(MultiTenantRouter, 'get_tenant_database')
    def test_db_for_write_with_tenant(self, mock_get_tenant_db):
        """Test routing writes with tenant context."""
        mock_get_tenant_db.return_value = 'tenant1_db'
        
        mock_model = Mock()
        result = self.router.db_for_write(mock_model, tenant_id='tenant1')
        
        self.assertEqual(result, 'tenant1_db')
        mock_get_tenant_db.assert_called_once_with('tenant1')


class TestShardingRouter(TestCase):
    """Test cases for ShardingRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = ShardingRouter()
        self.router.SHARDING_RULES = {
            'auth.User': {
                'field': 'id',
                'shards': ['shard1', 'shard2', 'shard3', 'shard4'],
            }
        }
    
    def test_get_shard_for_instance(self):
        """Test getting shard for model instance."""
        user = User(id=123)
        user._meta = Mock()
        user._meta.app_label = 'auth'
        
        result = self.router.get_shard_for_instance(user)
        
        # Should return one of the configured shards
        self.assertIn(result, ['shard1', 'shard2', 'shard3', 'shard4'])
    
    def test_get_shard_for_instance_no_rule(self):
        """Test getting shard for model without sharding rule."""
        mock_instance = Mock()
        mock_instance._meta.app_label = 'blog'
        mock_instance.__class__.__name__ = 'Post'
        
        result = self.router.get_shard_for_instance(mock_instance)
        self.assertIsNone(result)
    
    @patch.object(ShardingRouter, 'get_shard_for_instance')
    def test_db_for_read_with_shard(self, mock_get_shard):
        """Test routing reads with sharding."""
        mock_get_shard.return_value = 'shard2'
        
        user = User(id=123)
        result = self.router.db_for_read(User, instance=user)
        
        self.assertEqual(result, 'shard2')
        mock_get_shard.assert_called_once_with(user)
    
    @patch.object(DatabaseRouter, 'db_for_read')
    def test_db_for_read_without_instance(self, mock_super_db_for_read):
        """Test routing reads without instance."""
        mock_super_db_for_read.return_value = 'default'
        
        result = self.router.db_for_read(User)
        
        self.assertEqual(result, 'default')
        mock_super_db_for_read.assert_called_once()
    
    @patch.object(ShardingRouter, 'get_shard_for_instance')
    def test_db_for_write_with_shard(self, mock_get_shard):
        """Test routing writes with sharding."""
        mock_get_shard.return_value = 'shard3'
        
        user = User(id=456)
        result = self.router.db_for_write(User, instance=user)
        
        self.assertEqual(result, 'shard3')
        mock_get_shard.assert_called_once_with(user)


class TestUtilityFunctions(TestCase):
    """Test cases for utility functions."""
    
    @patch('enterprise_database.routers.router')
    def test_get_database_for_model_read(self, mock_router):
        """Test utility function for getting read database."""
        mock_router.db_for_read.return_value = 'read_replica'
        
        result = get_database_for_model(User, 'read')
        
        self.assertEqual(result, 'read_replica')
        mock_router.db_for_read.assert_called_once_with(User)
    
    @patch('enterprise_database.routers.router')
    def test_get_database_for_model_write(self, mock_router):
        """Test utility function for getting write database."""
        mock_router.db_for_write.return_value = 'default'
        
        result = get_database_for_model(User, 'write')
        
        self.assertEqual(result, 'default')
        mock_router.db_for_write.assert_called_once_with(User)
    
    @patch('enterprise_database.routers.router')
    def test_get_database_for_model_fallback(self, mock_router):
        """Test utility function fallback to default."""
        mock_router.db_for_read.return_value = None
        
        result = get_database_for_model(User, 'read')
        
        self.assertEqual(result, 'default')


if __name__ == '__main__':
    pytest.main([__file__])