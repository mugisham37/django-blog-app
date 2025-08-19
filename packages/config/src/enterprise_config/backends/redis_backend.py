"""
Redis-based configuration backend.
"""

import json
from typing import Any, Dict, List, Optional

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:
    redis = None
    RedisError = Exception

from .base import BaseBackend
from ..exceptions import BackendError


class RedisBackend(BaseBackend):
    """
    Redis-based configuration backend for distributed configuration storage.
    
    Configuration is stored as JSON strings in Redis with configurable key prefixes.
    Supports Redis clustering and SSL connections.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "config:",
        connection_timeout: float = 30.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        ssl_enabled: bool = False,
        password: Optional[str] = None,
        **redis_kwargs,
    ):
        """
        Initialize Redis backend.

        Args:
            url: Redis connection URL
            key_prefix: Prefix for configuration keys
            connection_timeout: Connection timeout in seconds
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
            ssl_enabled: Whether to use SSL connection
            password: Redis password
            **redis_kwargs: Additional Redis connection parameters
        """
        if redis is None:
            raise ImportError("redis package is required for Redis backend")

        self.url = url
        self.key_prefix = key_prefix
        self.connection_timeout = connection_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Parse Redis URL and create connection
        try:
            self.redis_client = redis.from_url(
                url,
                socket_timeout=connection_timeout,
                socket_connect_timeout=connection_timeout,
                ssl=ssl_enabled,
                password=password,
                decode_responses=True,
                **redis_kwargs,
            )
            
            # Test connection
            self.redis_client.ping()
            
        except Exception as e:
            raise BackendError(
                f"Failed to connect to Redis: {str(e)}",
                backend_type="redis",
                operation="connect",
                original_error=e,
            )

    def _get_key(self, config_name: str) -> str:
        """Get full Redis key for configuration name."""
        return f"{self.key_prefix}{config_name}"

    def _execute_with_retry(self, operation: callable, *args, **kwargs) -> Any:
        """Execute Redis operation with retry logic."""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                return operation(*args, **kwargs)
            except RedisError as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    import time
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
                
        raise BackendError(
            f"Redis operation failed after {self.retry_attempts} attempts: {str(last_error)}",
            backend_type="redis",
            operation="retry",
            original_error=last_error,
        )

    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Load configuration by name."""
        try:
            key = self._get_key(config_name)
            
            def _load():
                data = self.redis_client.get(key)
                if data is None:
                    return None
                return json.loads(data)
                
            return self._execute_with_retry(_load)
            
        except json.JSONDecodeError as e:
            raise BackendError(
                f"Failed to decode JSON for config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="load",
                original_error=e,
            )
        except Exception as e:
            raise BackendError(
                f"Failed to load config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="load",
                original_error=e,
            )

    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """Save configuration by name."""
        try:
            key = self._get_key(config_name)
            data = json.dumps(config_data, ensure_ascii=False, separators=(',', ':'))
            
            def _save():
                return self.redis_client.set(key, data)
                
            self._execute_with_retry(_save)
            
        except json.JSONEncodeError as e:
            raise BackendError(
                f"Failed to encode JSON for config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="save",
                original_error=e,
            )
        except Exception as e:
            raise BackendError(
                f"Failed to save config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="save",
                original_error=e,
            )

    def delete_config(self, config_name: str) -> bool:
        """Delete configuration by name."""
        try:
            key = self._get_key(config_name)
            
            def _delete():
                return self.redis_client.delete(key) > 0
                
            return self._execute_with_retry(_delete)
            
        except Exception as e:
            raise BackendError(
                f"Failed to delete config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="delete",
                original_error=e,
            )

    def list_configs(self) -> List[str]:
        """List all available configuration names."""
        try:
            pattern = f"{self.key_prefix}*"
            
            def _list():
                keys = self.redis_client.keys(pattern)
                return [key[len(self.key_prefix):] for key in keys]
                
            return sorted(self._execute_with_retry(_list))
            
        except Exception as e:
            raise BackendError(
                f"Failed to list configurations: {str(e)}",
                backend_type="redis",
                operation="list",
                original_error=e,
            )

    def exists(self, config_name: str) -> bool:
        """Check if configuration exists."""
        try:
            key = self._get_key(config_name)
            
            def _exists():
                return self.redis_client.exists(key) > 0
                
            return self._execute_with_retry(_exists)
            
        except Exception as e:
            raise BackendError(
                f"Failed to check existence of config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="exists",
                original_error=e,
            )

    def health_check(self) -> bool:
        """Check if Redis backend is healthy."""
        try:
            def _ping():
                return self.redis_client.ping()
                
            return self._execute_with_retry(_ping)
            
        except Exception:
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """Get Redis connection information."""
        try:
            info = self.redis_client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "keyspace": info.get("keyspace", {}),
            }
        except Exception:
            return {}

    def set_expiry(self, config_name: str, seconds: int) -> bool:
        """
        Set expiry time for configuration.

        Args:
            config_name: Name of the configuration
            seconds: Expiry time in seconds

        Returns:
            True if expiry was set successfully
        """
        try:
            key = self._get_key(config_name)
            
            def _expire():
                return self.redis_client.expire(key, seconds)
                
            return self._execute_with_retry(_expire)
            
        except Exception as e:
            raise BackendError(
                f"Failed to set expiry for config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="expire",
                original_error=e,
            )

    def get_ttl(self, config_name: str) -> int:
        """
        Get time-to-live for configuration.

        Args:
            config_name: Name of the configuration

        Returns:
            TTL in seconds (-1 if no expiry, -2 if key doesn't exist)
        """
        try:
            key = self._get_key(config_name)
            
            def _ttl():
                return self.redis_client.ttl(key)
                
            return self._execute_with_retry(_ttl)
            
        except Exception as e:
            raise BackendError(
                f"Failed to get TTL for config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="ttl",
                original_error=e,
            )

    def atomic_update(
        self,
        config_name: str,
        update_func: callable,
    ) -> Dict[str, Any]:
        """
        Atomically update configuration using Redis transactions.

        Args:
            config_name: Name of the configuration
            update_func: Function that takes current config and returns updated config

        Returns:
            Updated configuration data
        """
        key = self._get_key(config_name)
        
        def _atomic_update():
            with self.redis_client.pipeline() as pipe:
                while True:
                    try:
                        # Watch the key for changes
                        pipe.watch(key)
                        
                        # Get current value
                        current_data = pipe.get(key)
                        if current_data:
                            current_config = json.loads(current_data)
                        else:
                            current_config = {}
                        
                        # Apply update function
                        updated_config = update_func(current_config)
                        
                        # Start transaction
                        pipe.multi()
                        pipe.set(key, json.dumps(updated_config, ensure_ascii=False))
                        
                        # Execute transaction
                        pipe.execute()
                        return updated_config
                        
                    except redis.WatchError:
                        # Key was modified, retry
                        continue
                        
        try:
            return self._execute_with_retry(_atomic_update)
        except Exception as e:
            raise BackendError(
                f"Failed to atomically update config '{config_name}': {str(e)}",
                backend_type="redis",
                operation="atomic_update",
                original_error=e,
            )

    def bulk_load(self, config_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Load multiple configurations in a single operation.

        Args:
            config_names: List of configuration names to load

        Returns:
            Dictionary mapping config names to their data (None if not found)
        """
        try:
            keys = [self._get_key(name) for name in config_names]
            
            def _bulk_load():
                values = self.redis_client.mget(keys)
                result = {}
                for i, (name, value) in enumerate(zip(config_names, values)):
                    if value is not None:
                        result[name] = json.loads(value)
                    else:
                        result[name] = None
                return result
                
            return self._execute_with_retry(_bulk_load)
            
        except Exception as e:
            raise BackendError(
                f"Failed to bulk load configurations: {str(e)}",
                backend_type="redis",
                operation="bulk_load",
                original_error=e,
            )

    def bulk_save(self, configs: Dict[str, Dict[str, Any]]) -> None:
        """
        Save multiple configurations in a single operation.

        Args:
            configs: Dictionary mapping config names to their data
        """
        try:
            def _bulk_save():
                pipe = self.redis_client.pipeline()
                for config_name, config_data in configs.items():
                    key = self._get_key(config_name)
                    data = json.dumps(config_data, ensure_ascii=False)
                    pipe.set(key, data)
                pipe.execute()
                
            self._execute_with_retry(_bulk_save)
            
        except Exception as e:
            raise BackendError(
                f"Failed to bulk save configurations: {str(e)}",
                backend_type="redis",
                operation="bulk_save",
                original_error=e,
            )

    def clear_all_configs(self) -> int:
        """
        Clear all configurations with the configured prefix.

        Returns:
            Number of configurations deleted
        """
        try:
            pattern = f"{self.key_prefix}*"
            
            def _clear_all():
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
                
            return self._execute_with_retry(_clear_all)
            
        except Exception as e:
            raise BackendError(
                f"Failed to clear all configurations: {str(e)}",
                backend_type="redis",
                operation="clear_all",
                original_error=e,
            )