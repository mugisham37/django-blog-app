"""
Database routing for read/write splitting and multi-database support.
"""

import logging
from typing import Optional, Type, Any
from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class DatabaseRouter:
    """
    Database router for read/write splitting and multi-database operations.
    
    This router automatically routes read operations to read replicas
    and write operations to the primary database.
    """
    
    # Models that should always use the primary database
    PRIMARY_ONLY_MODELS = {
        'auth.User',
        'auth.Group',
        'auth.Permission',
        'contenttypes.ContentType',
        'sessions.Session',
        'admin.LogEntry',
    }
    
    # Apps that should use specific databases
    APP_DATABASE_MAPPING = {
        # 'analytics': 'analytics_db',
        # 'logs': 'logs_db',
    }
    
    def db_for_read(self, model: Type[models.Model], **hints) -> Optional[str]:
        """
        Suggest the database to read from.
        
        Args:
            model: Model class
            **hints: Additional hints
            
        Returns:
            Database alias or None
        """
        app_label = model._meta.app_label
        model_name = f"{app_label}.{model.__name__}"
        
        # Check if model should always use primary
        if model_name in self.PRIMARY_ONLY_MODELS:
            return 'default'
        
        # Check app-specific database mapping
        if app_label in self.APP_DATABASE_MAPPING:
            return self.APP_DATABASE_MAPPING[app_label]
        
        # Use read replica if available and not in transaction
        if self._has_read_replica() and not self._in_transaction():
            logger.debug(f"Routing read for {model_name} to read replica")
            return 'read_replica'
        
        # Default to primary database
        return 'default'
    
    def db_for_write(self, model: Type[models.Model], **hints) -> Optional[str]:
        """
        Suggest the database to write to.
        
        Args:
            model: Model class
            **hints: Additional hints
            
        Returns:
            Database alias or None
        """
        app_label = model._meta.app_label
        model_name = f"{app_label}.{model.__name__}"
        
        # Check app-specific database mapping
        if app_label in self.APP_DATABASE_MAPPING:
            return self.APP_DATABASE_MAPPING[app_label]
        
        # All writes go to primary database
        logger.debug(f"Routing write for {model_name} to primary database")
        return 'default'
    
    def allow_relation(self, obj1: models.Model, obj2: models.Model, **hints) -> Optional[bool]:
        """
        Allow relations between objects.
        
        Args:
            obj1: First model instance
            obj2: Second model instance
            **hints: Additional hints
            
        Returns:
            True if relation is allowed, False if not, None if no opinion
        """
        db_set = {'default'}
        
        # Add read replica to allowed databases
        if self._has_read_replica():
            db_set.add('read_replica')
        
        # Add app-specific databases
        db_set.update(self.APP_DATABASE_MAPPING.values())
        
        # Allow relations if both objects are in allowed databases
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        
        return None
    
    def allow_migrate(self, db: str, app_label: str, model_name: str = None, **hints) -> Optional[bool]:
        """
        Determine if migration should be run on a database.
        
        Args:
            db: Database alias
            app_label: App label
            model_name: Model name
            **hints: Additional hints
            
        Returns:
            True if migration is allowed, False if not, None if no opinion
        """
        # Don't migrate to read replicas
        if db == 'read_replica':
            return False
        
        # Check app-specific database mapping
        if app_label in self.APP_DATABASE_MAPPING:
            return db == self.APP_DATABASE_MAPPING[app_label]
        
        # Default apps go to default database
        return db == 'default'
    
    def _has_read_replica(self) -> bool:
        """Check if read replica is configured."""
        databases = getattr(settings, 'DATABASES', {})
        return 'read_replica' in databases
    
    def _in_transaction(self) -> bool:
        """Check if currently in a database transaction."""
        from django.db import transaction
        try:
            return transaction.get_connection().in_atomic_block
        except Exception:
            return False


class ReadWriteRouter(DatabaseRouter):
    """
    Enhanced router with explicit read/write routing methods.
    """
    
    def route_read_to_replica(self, model: Type[models.Model]) -> bool:
        """
        Determine if reads for this model should go to replica.
        
        Args:
            model: Model class
            
        Returns:
            True if should use replica, False otherwise
        """
        app_label = model._meta.app_label
        model_name = f"{app_label}.{model.__name__}"
        
        # Never route these to replica
        if model_name in self.PRIMARY_ONLY_MODELS:
            return False
        
        # Don't route to replica if in transaction
        if self._in_transaction():
            return False
        
        # Check if replica is available
        return self._has_read_replica()
    
    def get_database_for_model(self, model: Type[models.Model], operation: str = 'read') -> str:
        """
        Get the appropriate database for a model and operation.
        
        Args:
            model: Model class
            operation: Type of operation ('read' or 'write')
            
        Returns:
            Database alias
        """
        if operation == 'write':
            return self.db_for_write(model) or 'default'
        else:
            return self.db_for_read(model) or 'default'


class MultiTenantRouter(DatabaseRouter):
    """
    Router for multi-tenant applications.
    """
    
    def __init__(self):
        super().__init__()
        self.tenant_databases = {}
    
    def get_tenant_database(self, tenant_id: str) -> str:
        """
        Get database for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Database alias for the tenant
        """
        return self.tenant_databases.get(tenant_id, 'default')
    
    def set_tenant_database(self, tenant_id: str, database: str) -> None:
        """
        Set database for a specific tenant.
        
        Args:
            tenant_id: Tenant identifier
            database: Database alias
        """
        self.tenant_databases[tenant_id] = database
    
    def db_for_read(self, model: Type[models.Model], **hints) -> Optional[str]:
        """Route reads based on tenant context."""
        # Get tenant from hints or thread-local storage
        tenant_id = hints.get('tenant_id')
        if tenant_id:
            return self.get_tenant_database(tenant_id)
        
        return super().db_for_read(model, **hints)
    
    def db_for_write(self, model: Type[models.Model], **hints) -> Optional[str]:
        """Route writes based on tenant context."""
        # Get tenant from hints or thread-local storage
        tenant_id = hints.get('tenant_id')
        if tenant_id:
            return self.get_tenant_database(tenant_id)
        
        return super().db_for_write(model, **hints)


class ShardingRouter(DatabaseRouter):
    """
    Router for database sharding based on model attributes.
    """
    
    SHARDING_RULES = {
        # Example: shard users by user_id
        # 'auth.User': {
        #     'field': 'id',
        #     'shards': ['shard1', 'shard2', 'shard3', 'shard4'],
        # },
    }
    
    def get_shard_for_instance(self, instance: models.Model) -> Optional[str]:
        """
        Get shard database for a model instance.
        
        Args:
            instance: Model instance
            
        Returns:
            Shard database alias or None
        """
        model_name = f"{instance._meta.app_label}.{instance.__class__.__name__}"
        
        if model_name not in self.SHARDING_RULES:
            return None
        
        rule = self.SHARDING_RULES[model_name]
        field_value = getattr(instance, rule['field'])
        
        # Simple hash-based sharding
        shard_index = hash(field_value) % len(rule['shards'])
        return rule['shards'][shard_index]
    
    def db_for_read(self, model: Type[models.Model], **hints) -> Optional[str]:
        """Route reads based on sharding rules."""
        instance = hints.get('instance')
        if instance:
            shard = self.get_shard_for_instance(instance)
            if shard:
                return shard
        
        return super().db_for_read(model, **hints)
    
    def db_for_write(self, model: Type[models.Model], **hints) -> Optional[str]:
        """Route writes based on sharding rules."""
        instance = hints.get('instance')
        if instance:
            shard = self.get_shard_for_instance(instance)
            if shard:
                return shard
        
        return super().db_for_write(model, **hints)


# Utility functions for router management
def get_database_for_model(model: Type[models.Model], operation: str = 'read') -> str:
    """
    Get the appropriate database for a model and operation.
    
    Args:
        model: Model class
        operation: Type of operation ('read' or 'write')
        
    Returns:
        Database alias
    """
    from django.db import router
    
    if operation == 'write':
        return router.db_for_write(model) or 'default'
    else:
        return router.db_for_read(model) or 'default'


def using_database(database: str):
    """
    Context manager to temporarily use a specific database.
    
    Args:
        database: Database alias to use
        
    Usage:
        with using_database('read_replica'):
            users = User.objects.all()
    """
    from django.db import connections
    
    class DatabaseContext:
        def __init__(self, db_alias):
            self.db_alias = db_alias
            self.original_db = None
        
        def __enter__(self):
            # This is a simplified implementation
            # In practice, you'd need to modify the ORM's database selection
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            # Restore original database selection
            pass
    
    return DatabaseContext(database)