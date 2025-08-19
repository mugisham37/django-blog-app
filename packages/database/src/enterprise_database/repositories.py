"""
Repository pattern implementation for clean data access.
"""

from typing import Any, Dict, List, Optional, Type, Union, QuerySet
from django.db import models, transaction
from django.db.models import Q, QuerySet as DjangoQuerySet
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.paginator import Paginator
from .exceptions import RepositoryError, ObjectNotFoundError


class BaseRepository:
    """
    Base repository class providing common database operations.
    
    This class implements the Repository pattern to provide a clean
    abstraction layer over Django ORM operations.
    """
    
    model: Type[models.Model] = None
    
    def __init__(self, model: Optional[Type[models.Model]] = None):
        """
        Initialize repository with optional model override.
        
        Args:
            model: Django model class to use for operations
        """
        if model:
            self.model = model
        
        if not self.model:
            raise RepositoryError("Repository must have a model defined")
    
    def get_queryset(self) -> DjangoQuerySet:
        """
        Get the base queryset for this repository.
        
        Override this method to customize the base queryset
        (e.g., add select_related, prefetch_related, filters).
        
        Returns:
            Base queryset for the model
        """
        return self.model.objects.all()
    
    def get(self, **kwargs) -> models.Model:
        """
        Get a single object by the given criteria.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            Model instance
            
        Raises:
            ObjectNotFoundError: If object doesn't exist
            MultipleObjectsReturned: If multiple objects found
        """
        try:
            return self.get_queryset().get(**kwargs)
        except ObjectDoesNotExist:
            raise ObjectNotFoundError(f"{self.model.__name__} not found with criteria: {kwargs}")
        except MultipleObjectsReturned:
            raise RepositoryError(f"Multiple {self.model.__name__} objects found with criteria: {kwargs}")
    
    def get_or_none(self, **kwargs) -> Optional[models.Model]:
        """
        Get a single object or return None if not found.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            Model instance or None
        """
        try:
            return self.get(**kwargs)
        except ObjectNotFoundError:
            return None
    
    def filter(self, **kwargs) -> DjangoQuerySet:
        """
        Filter objects by the given criteria.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            Filtered queryset
        """
        return self.get_queryset().filter(**kwargs)
    
    def exclude(self, **kwargs) -> DjangoQuerySet:
        """
        Exclude objects by the given criteria.
        
        Args:
            **kwargs: Exclude criteria
            
        Returns:
            Filtered queryset
        """
        return self.get_queryset().exclude(**kwargs)
    
    def all(self) -> DjangoQuerySet:
        """
        Get all objects.
        
        Returns:
            All objects queryset
        """
        return self.get_queryset()
    
    def exists(self, **kwargs) -> bool:
        """
        Check if objects exist with the given criteria.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            True if objects exist, False otherwise
        """
        return self.filter(**kwargs).exists()
    
    def count(self, **kwargs) -> int:
        """
        Count objects with the given criteria.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            Number of objects
        """
        if kwargs:
            return self.filter(**kwargs).count()
        return self.get_queryset().count()
    
    def create(self, **kwargs) -> models.Model:
        """
        Create a new object.
        
        Args:
            **kwargs: Object data
            
        Returns:
            Created model instance
        """
        return self.model.objects.create(**kwargs)
    
    def get_or_create(self, defaults: Optional[Dict] = None, **kwargs) -> tuple[models.Model, bool]:
        """
        Get an object or create it if it doesn't exist.
        
        Args:
            defaults: Default values for creation
            **kwargs: Lookup criteria
            
        Returns:
            Tuple of (object, created_flag)
        """
        return self.model.objects.get_or_create(defaults=defaults, **kwargs)
    
    def update_or_create(self, defaults: Optional[Dict] = None, **kwargs) -> tuple[models.Model, bool]:
        """
        Update an object or create it if it doesn't exist.
        
        Args:
            defaults: Values to update/create with
            **kwargs: Lookup criteria
            
        Returns:
            Tuple of (object, created_flag)
        """
        return self.model.objects.update_or_create(defaults=defaults, **kwargs)
    
    def update(self, instance: models.Model, **kwargs) -> models.Model:
        """
        Update an existing object.
        
        Args:
            instance: Model instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated model instance
        """
        for field, value in kwargs.items():
            setattr(instance, field, value)
        instance.save()
        return instance
    
    def bulk_update(self, objects: List[models.Model], fields: List[str], batch_size: int = 1000) -> None:
        """
        Bulk update multiple objects.
        
        Args:
            objects: List of model instances to update
            fields: List of field names to update
            batch_size: Number of objects to update per batch
        """
        self.model.objects.bulk_update(objects, fields, batch_size=batch_size)
    
    def delete(self, instance: models.Model) -> None:
        """
        Delete an object.
        
        Args:
            instance: Model instance to delete
        """
        instance.delete()
    
    def bulk_delete(self, **kwargs) -> int:
        """
        Bulk delete objects matching criteria.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            Number of deleted objects
        """
        queryset = self.filter(**kwargs)
        count = queryset.count()
        queryset.delete()
        return count
    
    def bulk_create(self, objects: List[Dict], batch_size: int = 1000, ignore_conflicts: bool = False) -> List[models.Model]:
        """
        Bulk create multiple objects.
        
        Args:
            objects: List of object data dictionaries
            batch_size: Number of objects to create per batch
            ignore_conflicts: Whether to ignore conflicts
            
        Returns:
            List of created model instances
        """
        model_instances = [self.model(**obj_data) for obj_data in objects]
        return self.model.objects.bulk_create(
            model_instances,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts
        )
    
    def paginate(self, page: int = 1, per_page: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Paginate objects with optional filtering.
        
        Args:
            page: Page number (1-based)
            per_page: Number of objects per page
            **kwargs: Filter criteria
            
        Returns:
            Dictionary with pagination data
        """
        queryset = self.filter(**kwargs) if kwargs else self.get_queryset()
        paginator = Paginator(queryset, per_page)
        
        page_obj = paginator.get_page(page)
        
        return {
            'objects': page_obj.object_list,
            'page': page_obj.number,
            'pages': paginator.num_pages,
            'per_page': per_page,
            'total': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
    
    def search(self, query: str, fields: List[str]) -> DjangoQuerySet:
        """
        Search objects across multiple fields.
        
        Args:
            query: Search query
            fields: List of field names to search in
            
        Returns:
            Filtered queryset
        """
        if not query or not fields:
            return self.get_queryset().none()
        
        q_objects = Q()
        for field in fields:
            q_objects |= Q(**{f"{field}__icontains": query})
        
        return self.get_queryset().filter(q_objects)
    
    @transaction.atomic
    def create_with_relations(self, data: Dict[str, Any], relations: Dict[str, Any] = None) -> models.Model:
        """
        Create an object with related objects in a transaction.
        
        Args:
            data: Main object data
            relations: Related objects data
            
        Returns:
            Created model instance with relations
        """
        instance = self.create(**data)
        
        if relations:
            for relation_name, relation_data in relations.items():
                if hasattr(instance, relation_name):
                    relation_manager = getattr(instance, relation_name)
                    
                    if isinstance(relation_data, list):
                        # Many-to-many or reverse foreign key
                        for item_data in relation_data:
                            if isinstance(item_data, dict):
                                relation_manager.create(**item_data)
                            else:
                                relation_manager.add(item_data)
                    elif isinstance(relation_data, dict):
                        # One-to-one or foreign key
                        relation_manager.create(**relation_data)
                    else:
                        # Direct assignment
                        setattr(instance, relation_name, relation_data)
        
        instance.refresh_from_db()
        return instance
    
    def get_related(self, instance: models.Model, relation_name: str, **kwargs) -> DjangoQuerySet:
        """
        Get related objects for an instance.
        
        Args:
            instance: Model instance
            relation_name: Name of the relation
            **kwargs: Filter criteria for related objects
            
        Returns:
            Related objects queryset
        """
        if not hasattr(instance, relation_name):
            raise RepositoryError(f"Relation '{relation_name}' not found on {instance.__class__.__name__}")
        
        relation_manager = getattr(instance, relation_name)
        
        if kwargs:
            return relation_manager.filter(**kwargs)
        return relation_manager.all()


class ReadOnlyRepository(BaseRepository):
    """
    Read-only repository that prevents write operations.
    """
    
    def create(self, **kwargs):
        raise RepositoryError("Create operation not allowed on read-only repository")
    
    def update(self, instance: models.Model, **kwargs):
        raise RepositoryError("Update operation not allowed on read-only repository")
    
    def delete(self, instance: models.Model):
        raise RepositoryError("Delete operation not allowed on read-only repository")
    
    def bulk_create(self, objects: List[Dict], **kwargs):
        raise RepositoryError("Bulk create operation not allowed on read-only repository")
    
    def bulk_update(self, objects: List[models.Model], fields: List[str], **kwargs):
        raise RepositoryError("Bulk update operation not allowed on read-only repository")
    
    def bulk_delete(self, **kwargs):
        raise RepositoryError("Bulk delete operation not allowed on read-only repository")


class CachedRepository(BaseRepository):
    """
    Repository with caching capabilities.
    """
    
    cache_timeout = 300  # 5 minutes default
    cache_key_prefix = "repo"
    
    def __init__(self, model: Optional[Type[models.Model]] = None, cache_timeout: int = None):
        super().__init__(model)
        if cache_timeout is not None:
            self.cache_timeout = cache_timeout
    
    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate cache key for method call."""
        from django.core.cache.utils import make_template_fragment_key
        key_parts = [self.cache_key_prefix, self.model.__name__.lower(), method]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        return ":".join(key_parts)
    
    def _get_from_cache(self, cache_key: str):
        """Get value from cache."""
        from django.core.cache import cache
        return cache.get(cache_key)
    
    def _set_cache(self, cache_key: str, value, timeout: int = None):
        """Set value in cache."""
        from django.core.cache import cache
        cache.set(cache_key, value, timeout or self.cache_timeout)
    
    def _invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries."""
        from django.core.cache import cache
        if pattern:
            # In a real implementation, you'd use a cache backend that supports pattern deletion
            # For now, we'll just clear the entire cache
            cache.clear()
    
    def get(self, **kwargs):
        """Get with caching."""
        cache_key = self._get_cache_key("get", **kwargs)
        result = self._get_from_cache(cache_key)
        
        if result is None:
            result = super().get(**kwargs)
            self._set_cache(cache_key, result)
        
        return result
    
    def filter(self, **kwargs):
        """Filter with caching for simple queries."""
        cache_key = self._get_cache_key("filter", **kwargs)
        result = self._get_from_cache(cache_key)
        
        if result is None:
            result = list(super().filter(**kwargs))
            self._set_cache(cache_key, result)
        
        return result
    
    def create(self, **kwargs):
        """Create and invalidate cache."""
        result = super().create(**kwargs)
        self._invalidate_cache()
        return result
    
    def update(self, instance: models.Model, **kwargs):
        """Update and invalidate cache."""
        result = super().update(instance, **kwargs)
        self._invalidate_cache()
        return result
    
    def delete(self, instance: models.Model):
        """Delete and invalidate cache."""
        super().delete(instance)
        self._invalidate_cache()


# Repository registry for managing multiple repositories
class RepositoryRegistry:
    """
    Registry for managing repository instances.
    """
    
    _repositories = {}
    
    @classmethod
    def register(cls, model: Type[models.Model], repository_class: Type[BaseRepository]):
        """Register a repository for a model."""
        cls._repositories[model] = repository_class
    
    @classmethod
    def get_repository(cls, model: Type[models.Model]) -> BaseRepository:
        """Get repository instance for a model."""
        repository_class = cls._repositories.get(model, BaseRepository)
        return repository_class(model)
    
    @classmethod
    def get_all_repositories(cls) -> Dict[Type[models.Model], BaseRepository]:
        """Get all registered repositories."""
        return {model: cls.get_repository(model) for model in cls._repositories.keys()}


# Decorator for automatic repository registration
def register_repository(model: Type[models.Model]):
    """
    Decorator to automatically register a repository for a model.
    
    Usage:
        @register_repository(User)
        class UserRepository(BaseRepository):
            model = User
    """
    def decorator(repository_class: Type[BaseRepository]):
        RepositoryRegistry.register(model, repository_class)
        return repository_class
    return decorator