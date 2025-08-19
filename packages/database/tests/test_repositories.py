"""
Tests for repository pattern implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.auth.models import User

from enterprise_database.repositories import (
    BaseRepository,
    ReadOnlyRepository,
    CachedRepository,
    RepositoryRegistry,
    register_repository
)
from enterprise_database.exceptions import RepositoryError, ObjectNotFoundError


# Test model for repository testing
class TestModel(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'test_app'


class TestBaseRepository(TestCase):
    """Test cases for BaseRepository class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repository = BaseRepository(TestModel)
    
    def test_repository_initialization(self):
        """Test repository initialization."""
        # Test with model parameter
        repo = BaseRepository(TestModel)
        self.assertEqual(repo.model, TestModel)
        
        # Test without model should raise error
        with self.assertRaises(RepositoryError):
            BaseRepository()
    
    def test_get_queryset(self):
        """Test get_queryset method."""
        with patch.object(TestModel.objects, 'all') as mock_all:
            mock_queryset = Mock()
            mock_all.return_value = mock_queryset
            
            result = self.repository.get_queryset()
            
            mock_all.assert_called_once()
            self.assertEqual(result, mock_queryset)
    
    def test_get_success(self):
        """Test successful get operation."""
        mock_instance = Mock()
        
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_queryset.get.return_value = mock_instance
            mock_get_queryset.return_value = mock_queryset
            
            result = self.repository.get(id=1)
            
            mock_queryset.get.assert_called_once_with(id=1)
            self.assertEqual(result, mock_instance)
    
    def test_get_not_found(self):
        """Test get operation when object not found."""
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_queryset.get.side_effect = ObjectDoesNotExist()
            mock_get_queryset.return_value = mock_queryset
            
            with self.assertRaises(ObjectNotFoundError):
                self.repository.get(id=999)
    
    def test_get_multiple_objects(self):
        """Test get operation when multiple objects found."""
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_queryset.get.side_effect = MultipleObjectsReturned()
            mock_get_queryset.return_value = mock_queryset
            
            with self.assertRaises(RepositoryError):
                self.repository.get(name='duplicate')
    
    def test_get_or_none_success(self):
        """Test get_or_none with existing object."""
        mock_instance = Mock()
        
        with patch.object(self.repository, 'get') as mock_get:
            mock_get.return_value = mock_instance
            
            result = self.repository.get_or_none(id=1)
            
            mock_get.assert_called_once_with(id=1)
            self.assertEqual(result, mock_instance)
    
    def test_get_or_none_not_found(self):
        """Test get_or_none with non-existing object."""
        with patch.object(self.repository, 'get') as mock_get:
            mock_get.side_effect = ObjectNotFoundError("Not found")
            
            result = self.repository.get_or_none(id=999)
            
            mock_get.assert_called_once_with(id=999)
            self.assertIsNone(result)
    
    def test_filter(self):
        """Test filter operation."""
        mock_queryset = Mock()
        
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_get_queryset.return_value.filter.return_value = mock_queryset
            
            result = self.repository.filter(active=True)
            
            mock_get_queryset.return_value.filter.assert_called_once_with(active=True)
            self.assertEqual(result, mock_queryset)
    
    def test_exclude(self):
        """Test exclude operation."""
        mock_queryset = Mock()
        
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_get_queryset.return_value.exclude.return_value = mock_queryset
            
            result = self.repository.exclude(active=False)
            
            mock_get_queryset.return_value.exclude.assert_called_once_with(active=False)
            self.assertEqual(result, mock_queryset)
    
    def test_all(self):
        """Test all operation."""
        mock_queryset = Mock()
        
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_get_queryset.return_value = mock_queryset
            
            result = self.repository.all()
            
            self.assertEqual(result, mock_queryset)
    
    def test_exists(self):
        """Test exists operation."""
        with patch.object(self.repository, 'filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.exists.return_value = True
            mock_filter.return_value = mock_queryset
            
            result = self.repository.exists(active=True)
            
            mock_filter.assert_called_once_with(active=True)
            mock_queryset.exists.assert_called_once()
            self.assertTrue(result)
    
    def test_count_with_filter(self):
        """Test count operation with filter."""
        with patch.object(self.repository, 'filter') as mock_filter:
            mock_queryset = Mock()
            mock_queryset.count.return_value = 5
            mock_filter.return_value = mock_queryset
            
            result = self.repository.count(active=True)
            
            mock_filter.assert_called_once_with(active=True)
            mock_queryset.count.assert_called_once()
            self.assertEqual(result, 5)
    
    def test_count_without_filter(self):
        """Test count operation without filter."""
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_queryset.count.return_value = 10
            mock_get_queryset.return_value = mock_queryset
            
            result = self.repository.count()
            
            mock_queryset.count.assert_called_once()
            self.assertEqual(result, 10)
    
    def test_create(self):
        """Test create operation."""
        mock_instance = Mock()
        
        with patch.object(TestModel.objects, 'create') as mock_create:
            mock_create.return_value = mock_instance
            
            result = self.repository.create(name='Test', email='test@example.com')
            
            mock_create.assert_called_once_with(name='Test', email='test@example.com')
            self.assertEqual(result, mock_instance)
    
    def test_get_or_create(self):
        """Test get_or_create operation."""
        mock_instance = Mock()
        
        with patch.object(TestModel.objects, 'get_or_create') as mock_get_or_create:
            mock_get_or_create.return_value = (mock_instance, True)
            
            result = self.repository.get_or_create(
                defaults={'email': 'test@example.com'},
                name='Test'
            )
            
            mock_get_or_create.assert_called_once_with(
                defaults={'email': 'test@example.com'},
                name='Test'
            )
            self.assertEqual(result, (mock_instance, True))
    
    def test_update(self):
        """Test update operation."""
        mock_instance = Mock()
        mock_instance.save = Mock()
        
        result = self.repository.update(mock_instance, name='Updated')
        
        self.assertEqual(mock_instance.name, 'Updated')
        mock_instance.save.assert_called_once()
        self.assertEqual(result, mock_instance)
    
    def test_bulk_update(self):
        """Test bulk_update operation."""
        mock_objects = [Mock(), Mock()]
        
        with patch.object(TestModel.objects, 'bulk_update') as mock_bulk_update:
            self.repository.bulk_update(mock_objects, ['name'], batch_size=500)
            
            mock_bulk_update.assert_called_once_with(mock_objects, ['name'], batch_size=500)
    
    def test_delete(self):
        """Test delete operation."""
        mock_instance = Mock()
        mock_instance.delete = Mock()
        
        self.repository.delete(mock_instance)
        
        mock_instance.delete.assert_called_once()
    
    def test_bulk_delete(self):
        """Test bulk_delete operation."""
        mock_queryset = Mock()
        mock_queryset.count.return_value = 3
        mock_queryset.delete = Mock()
        
        with patch.object(self.repository, 'filter') as mock_filter:
            mock_filter.return_value = mock_queryset
            
            result = self.repository.bulk_delete(active=False)
            
            mock_filter.assert_called_once_with(active=False)
            mock_queryset.count.assert_called_once()
            mock_queryset.delete.assert_called_once()
            self.assertEqual(result, 3)
    
    def test_bulk_create(self):
        """Test bulk_create operation."""
        objects_data = [
            {'name': 'Test1', 'email': 'test1@example.com'},
            {'name': 'Test2', 'email': 'test2@example.com'}
        ]
        mock_instances = [Mock(), Mock()]
        
        with patch.object(TestModel.objects, 'bulk_create') as mock_bulk_create:
            mock_bulk_create.return_value = mock_instances
            
            result = self.repository.bulk_create(objects_data, batch_size=500)
            
            # Verify bulk_create was called with model instances
            mock_bulk_create.assert_called_once()
            args, kwargs = mock_bulk_create.call_args
            self.assertEqual(kwargs['batch_size'], 500)
            self.assertEqual(kwargs['ignore_conflicts'], False)
            self.assertEqual(result, mock_instances)
    
    @patch('enterprise_database.repositories.Paginator')
    def test_paginate(self, mock_paginator_class):
        """Test paginate operation."""
        mock_queryset = Mock()
        mock_paginator = Mock()
        mock_page_obj = Mock()
        
        # Setup mocks
        mock_paginator_class.return_value = mock_paginator
        mock_paginator.get_page.return_value = mock_page_obj
        mock_paginator.num_pages = 5
        mock_paginator.count = 100
        
        mock_page_obj.object_list = ['obj1', 'obj2']
        mock_page_obj.number = 2
        mock_page_obj.has_next.return_value = True
        mock_page_obj.has_previous.return_value = True
        mock_page_obj.next_page_number.return_value = 3
        mock_page_obj.previous_page_number.return_value = 1
        
        with patch.object(self.repository, 'filter') as mock_filter:
            mock_filter.return_value = mock_queryset
            
            result = self.repository.paginate(page=2, per_page=20, active=True)
            
            mock_filter.assert_called_once_with(active=True)
            mock_paginator_class.assert_called_once_with(mock_queryset, 20)
            mock_paginator.get_page.assert_called_once_with(2)
            
            expected_result = {
                'objects': ['obj1', 'obj2'],
                'page': 2,
                'pages': 5,
                'per_page': 20,
                'total': 100,
                'has_next': True,
                'has_previous': True,
                'next_page': 3,
                'previous_page': 1,
            }
            self.assertEqual(result, expected_result)
    
    def test_search(self):
        """Test search operation."""
        mock_queryset = Mock()
        
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_get_queryset.return_value.filter.return_value = mock_queryset
            
            result = self.repository.search('test query', ['name', 'email'])
            
            # Verify filter was called with Q objects
            mock_get_queryset.return_value.filter.assert_called_once()
            self.assertEqual(result, mock_queryset)
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_get_queryset.return_value.none.return_value = 'empty_queryset'
            
            result = self.repository.search('', ['name'])
            
            mock_get_queryset.return_value.none.assert_called_once()
            self.assertEqual(result, 'empty_queryset')
    
    @patch('enterprise_database.repositories.transaction')
    def test_create_with_relations(self, mock_transaction):
        """Test create_with_relations operation."""
        mock_instance = Mock()
        mock_relation_manager = Mock()
        
        # Setup instance with relation
        mock_instance.test_relation = mock_relation_manager
        mock_instance.refresh_from_db = Mock()
        
        with patch.object(self.repository, 'create') as mock_create:
            mock_create.return_value = mock_instance
            
            data = {'name': 'Test'}
            relations = {
                'test_relation': [
                    {'field': 'value1'},
                    {'field': 'value2'}
                ]
            }
            
            result = self.repository.create_with_relations(data, relations)
            
            mock_create.assert_called_once_with(**data)
            self.assertEqual(mock_relation_manager.create.call_count, 2)
            mock_instance.refresh_from_db.assert_called_once()
            self.assertEqual(result, mock_instance)
    
    def test_get_related(self):
        """Test get_related operation."""
        mock_instance = Mock()
        mock_relation_manager = Mock()
        mock_queryset = Mock()
        
        mock_instance.test_relation = mock_relation_manager
        mock_relation_manager.filter.return_value = mock_queryset
        
        result = self.repository.get_related(mock_instance, 'test_relation', active=True)
        
        mock_relation_manager.filter.assert_called_once_with(active=True)
        self.assertEqual(result, mock_queryset)
    
    def test_get_related_no_filter(self):
        """Test get_related operation without filter."""
        mock_instance = Mock()
        mock_relation_manager = Mock()
        mock_queryset = Mock()
        
        mock_instance.test_relation = mock_relation_manager
        mock_relation_manager.all.return_value = mock_queryset
        
        result = self.repository.get_related(mock_instance, 'test_relation')
        
        mock_relation_manager.all.assert_called_once()
        self.assertEqual(result, mock_queryset)
    
    def test_get_related_invalid_relation(self):
        """Test get_related with invalid relation name."""
        mock_instance = Mock()
        del mock_instance.invalid_relation  # Ensure attribute doesn't exist
        
        with self.assertRaises(RepositoryError):
            self.repository.get_related(mock_instance, 'invalid_relation')


class TestReadOnlyRepository(TestCase):
    """Test cases for ReadOnlyRepository class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repository = ReadOnlyRepository(TestModel)
    
    def test_create_raises_error(self):
        """Test that create operation raises error."""
        with self.assertRaises(RepositoryError):
            self.repository.create(name='Test')
    
    def test_update_raises_error(self):
        """Test that update operation raises error."""
        mock_instance = Mock()
        with self.assertRaises(RepositoryError):
            self.repository.update(mock_instance, name='Updated')
    
    def test_delete_raises_error(self):
        """Test that delete operation raises error."""
        mock_instance = Mock()
        with self.assertRaises(RepositoryError):
            self.repository.delete(mock_instance)
    
    def test_bulk_create_raises_error(self):
        """Test that bulk_create operation raises error."""
        with self.assertRaises(RepositoryError):
            self.repository.bulk_create([])
    
    def test_bulk_update_raises_error(self):
        """Test that bulk_update operation raises error."""
        with self.assertRaises(RepositoryError):
            self.repository.bulk_update([], [])
    
    def test_bulk_delete_raises_error(self):
        """Test that bulk_delete operation raises error."""
        with self.assertRaises(RepositoryError):
            self.repository.bulk_delete()
    
    def test_read_operations_work(self):
        """Test that read operations still work."""
        with patch.object(self.repository, 'get_queryset') as mock_get_queryset:
            mock_queryset = Mock()
            mock_get_queryset.return_value = mock_queryset
            
            # These should work without errors
            self.repository.all()
            self.repository.filter(active=True)
            self.repository.count()


class TestCachedRepository(TestCase):
    """Test cases for CachedRepository class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.repository = CachedRepository(TestModel, cache_timeout=600)
    
    def test_initialization_with_timeout(self):
        """Test initialization with custom cache timeout."""
        self.assertEqual(self.repository.cache_timeout, 600)
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        key = self.repository._get_cache_key('get', id=1, name='test')
        expected_parts = ['repo', 'testmodel', 'get', '1', 'id:1', 'name:test']
        self.assertTrue(all(part in key for part in expected_parts))
    
    @patch('enterprise_database.repositories.cache')
    def test_get_from_cache_hit(self, mock_cache):
        """Test get operation with cache hit."""
        mock_instance = Mock()
        mock_cache.get.return_value = mock_instance
        
        result = self.repository.get(id=1)
        
        mock_cache.get.assert_called_once()
        self.assertEqual(result, mock_instance)
    
    @patch('enterprise_database.repositories.cache')
    def test_get_from_cache_miss(self, mock_cache):
        """Test get operation with cache miss."""
        mock_instance = Mock()
        mock_cache.get.return_value = None
        
        with patch.object(BaseRepository, 'get') as mock_super_get:
            mock_super_get.return_value = mock_instance
            
            result = self.repository.get(id=1)
            
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()
            mock_super_get.assert_called_once_with(id=1)
            self.assertEqual(result, mock_instance)
    
    @patch('enterprise_database.repositories.cache')
    def test_create_invalidates_cache(self, mock_cache):
        """Test that create operation invalidates cache."""
        mock_instance = Mock()
        
        with patch.object(BaseRepository, 'create') as mock_super_create:
            mock_super_create.return_value = mock_instance
            
            result = self.repository.create(name='Test')
            
            mock_super_create.assert_called_once_with(name='Test')
            mock_cache.clear.assert_called_once()
            self.assertEqual(result, mock_instance)


class TestRepositoryRegistry(TestCase):
    """Test cases for RepositoryRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear registry before each test
        RepositoryRegistry._repositories.clear()
    
    def test_register_repository(self):
        """Test repository registration."""
        RepositoryRegistry.register(TestModel, BaseRepository)
        
        self.assertIn(TestModel, RepositoryRegistry._repositories)
        self.assertEqual(RepositoryRegistry._repositories[TestModel], BaseRepository)
    
    def test_get_repository_registered(self):
        """Test getting registered repository."""
        RepositoryRegistry.register(TestModel, CachedRepository)
        
        repo = RepositoryRegistry.get_repository(TestModel)
        
        self.assertIsInstance(repo, CachedRepository)
        self.assertEqual(repo.model, TestModel)
    
    def test_get_repository_not_registered(self):
        """Test getting repository for unregistered model."""
        repo = RepositoryRegistry.get_repository(TestModel)
        
        self.assertIsInstance(repo, BaseRepository)
        self.assertEqual(repo.model, TestModel)
    
    def test_get_all_repositories(self):
        """Test getting all registered repositories."""
        RepositoryRegistry.register(TestModel, BaseRepository)
        RepositoryRegistry.register(User, CachedRepository)
        
        repos = RepositoryRegistry.get_all_repositories()
        
        self.assertEqual(len(repos), 2)
        self.assertIn(TestModel, repos)
        self.assertIn(User, repos)
        self.assertIsInstance(repos[TestModel], BaseRepository)
        self.assertIsInstance(repos[User], CachedRepository)
    
    def test_register_repository_decorator(self):
        """Test repository registration decorator."""
        @register_repository(TestModel)
        class TestRepository(BaseRepository):
            model = TestModel
        
        self.assertIn(TestModel, RepositoryRegistry._repositories)
        self.assertEqual(RepositoryRegistry._repositories[TestModel], TestRepository)
        
        # Test that decorator returns the class
        self.assertEqual(TestRepository.model, TestModel)


if __name__ == '__main__':
    pytest.main([__file__])