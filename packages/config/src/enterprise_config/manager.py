"""
Main configuration manager implementation.
"""

import os
import re
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable, Union
from pathlib import Path
from datetime import datetime

from .models import Environment, ConfigModel, HotReloadConfig
from .backends import BackendFactory
from .feature_flags import FeatureFlagManager
from .secrets import SecretsManager
from .validators import ConfigValidator
from .hot_reload import HotReloadWatcher
from .exceptions import ConfigurationError, ValidationError

T = TypeVar("T", bound=ConfigModel)


class ConfigManager:
    """
    Main configuration manager for enterprise applications.
    
    Provides centralized configuration management with support for:
    - Environment-specific configurations
    - Feature flags
    - Secure secrets management
    - Configuration validation
    - Hot reloading
    - Multiple backends
    """

    def __init__(
        self,
        environment: Union[Environment, str] = Environment.DEVELOPMENT,
        backend: str = "file",
        config_path: Optional[str] = None,
        enable_hot_reload: bool = False,
        validation_schema: Optional[str] = None,
        **backend_kwargs,
    ):
        """
        Initialize configuration manager.

        Args:
            environment: Target environment (development, staging, production)
            backend: Configuration backend type (file, redis, aws_ssm, vault)
            config_path: Path to configuration files (for file backend)
            enable_hot_reload: Enable automatic configuration reloading
            validation_schema: Path to validation schema file
            **backend_kwargs: Additional backend-specific configuration
        """
        # Set environment
        if isinstance(environment, str):
            self.environment = Environment.from_string(environment)
        else:
            self.environment = environment

        # Initialize backend
        self.backend = BackendFactory.create_backend(
            backend_type=backend,
            config_path=config_path,
            **backend_kwargs,
        )

        # Initialize managers
        self.feature_flags = FeatureFlagManager(self.backend)
        self.secrets = SecretsManager(self.backend)
        self.validator = ConfigValidator(validation_schema)

        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Hot reload setup
        self.hot_reload_enabled = enable_hot_reload
        self._hot_reload_watcher: Optional[HotReloadWatcher] = None
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []

        if enable_hot_reload:
            self._setup_hot_reload()

        # Load initial configuration
        self._load_configuration()

    def _setup_hot_reload(self) -> None:
        """Set up hot reload watcher."""
        if hasattr(self.backend, "get_watch_paths"):
            watch_paths = self.backend.get_watch_paths()
            if watch_paths:
                self._hot_reload_watcher = HotReloadWatcher(
                    watch_paths=watch_paths,
                    callback=self._handle_config_change,
                )
                self._hot_reload_watcher.start()

    def _load_configuration(self) -> None:
        """Load configuration from backend."""
        try:
            # Load base configuration
            base_config = self.backend.load_config("base")
            if base_config:
                self._config_cache.update(base_config)

            # Load environment-specific configuration
            env_config = self.backend.load_config(self.environment.value)
            if env_config:
                self._merge_config(self._config_cache, env_config)

            # Process environment variable substitutions
            self._process_env_substitutions()

            # Validate configuration
            if self.validator.has_schema():
                self.validator.validate(self._config_cache)

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _process_env_substitutions(self) -> None:
        """Process environment variable substitutions in configuration values."""
        env_pattern = re.compile(r"\$\{([^}]+)\}")

        def substitute_value(value: Any) -> Any:
            if isinstance(value, str):
                def replace_env_var(match):
                    env_var = match.group(1)
                    default_value = None
                    
                    # Handle default values: ${VAR_NAME:default_value}
                    if ":" in env_var:
                        env_var, default_value = env_var.split(":", 1)
                    
                    return os.getenv(env_var, default_value or match.group(0))
                
                return env_pattern.sub(replace_env_var, value)
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [substitute_value(item) for item in value]
            return value

        self._config_cache = substitute_value(self._config_cache)

    def _handle_config_change(self, file_path: str) -> None:
        """Handle configuration file changes."""
        try:
            old_config = self._config_cache.copy()
            self._load_configuration()
            
            # Notify change callbacks
            for callback in self._change_callbacks:
                try:
                    callback(file_path, old_config, self._config_cache)
                except Exception as e:
                    # Log error but don't fail the reload
                    print(f"Error in config change callback: {e}")

        except Exception as e:
            print(f"Error reloading configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            keys = key.split(".")
            value = self._config_cache

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

        except Exception:
            return default

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Configuration value
            persist: Whether to persist the change to backend
        """
        keys = key.split(".")
        config = self._config_cache

        # Navigate to parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        old_value = config.get(keys[-1])
        config[keys[-1]] = value

        # Persist if requested
        if persist:
            try:
                self.backend.save_config(self.environment.value, self._config_cache)
            except Exception as e:
                # Rollback on failure
                if old_value is not None:
                    config[keys[-1]] = old_value
                else:
                    config.pop(keys[-1], None)
                raise ConfigurationError(f"Failed to persist configuration: {str(e)}")

        # Notify change callbacks
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, value)
            except Exception:
                pass  # Don't fail on callback errors

    def get_model(self, model_class: Type[T], key: str) -> T:
        """
        Get configuration as a Pydantic model.

        Args:
            model_class: Pydantic model class
            key: Configuration key

        Returns:
            Validated model instance

        Raises:
            ValidationError: If configuration doesn't match model schema
        """
        config_data = self.get(key)
        if config_data is None:
            raise ConfigurationError(f"Configuration key '{key}' not found")

        try:
            return model_class(**config_data)
        except Exception as e:
            raise ValidationError(
                f"Failed to validate configuration for key '{key}'",
                key=key,
                validation_errors={"model_validation": str(e)},
            )

    def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        return self.get(key) is not None

    def delete(self, key: str, persist: bool = True) -> bool:
        """
        Delete configuration key.

        Args:
            key: Configuration key to delete
            persist: Whether to persist the change to backend

        Returns:
            True if key was deleted, False if key didn't exist
        """
        keys = key.split(".")
        config = self._config_cache

        # Navigate to parent dictionary
        try:
            for k in keys[:-1]:
                config = config[k]
        except (KeyError, TypeError):
            return False

        # Delete the key
        if keys[-1] in config:
            old_value = config.pop(keys[-1])
            
            # Persist if requested
            if persist:
                try:
                    self.backend.save_config(self.environment.value, self._config_cache)
                except Exception as e:
                    # Rollback on failure
                    config[keys[-1]] = old_value
                    raise ConfigurationError(f"Failed to persist configuration: {str(e)}")

            # Notify change callbacks
            for callback in self._change_callbacks:
                try:
                    callback(key, old_value, None)
                except Exception:
                    pass

            return True

        return False

    def feature_flag(
        self,
        flag_name: str,
        default: bool = False,
        user_group: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check feature flag status.

        Args:
            flag_name: Feature flag name
            default: Default value if flag not found
            user_group: User group for flag evaluation
            context: Additional context for flag evaluation

        Returns:
            Feature flag status
        """
        return self.feature_flags.is_enabled(
            flag_name=flag_name,
            environment=self.environment,
            user_group=user_group,
            default=default,
            context=context,
        )

    def set_feature_flag(
        self,
        flag_name: str,
        enabled: bool,
        environments: Optional[List[Environment]] = None,
        user_groups: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """Set feature flag configuration."""
        self.feature_flags.set_flag(
            flag_name=flag_name,
            enabled=enabled,
            environments=environments,
            user_groups=user_groups,
            **kwargs,
        )

    def get_secret(self, secret_name: str) -> str:
        """Get decrypted secret value."""
        return self.secrets.get_secret(secret_name, self.environment)

    def set_secret(
        self,
        secret_name: str,
        secret_value: str,
        environments: Optional[List[Environment]] = None,
    ) -> None:
        """Set encrypted secret value."""
        self.secrets.set_secret(
            secret_name=secret_name,
            secret_value=secret_value,
            environments=environments,
        )

    def on_change(self, callback: Callable[[str, Any, Any], None]) -> None:
        """
        Register callback for configuration changes.

        Args:
            callback: Function to call when configuration changes.
                     Signature: callback(key: str, old_value: Any, new_value: Any)
        """
        self._change_callbacks.append(callback)

    def reload(self) -> None:
        """Manually reload configuration from backend."""
        self._load_configuration()

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return self._config_cache.copy()

    def get_environment_config(self, environment: Environment) -> Dict[str, Any]:
        """Get configuration for specific environment."""
        temp_config = {}
        
        # Load base configuration
        base_config = self.backend.load_config("base")
        if base_config:
            temp_config.update(base_config)

        # Load environment-specific configuration
        env_config = self.backend.load_config(environment.value)
        if env_config:
            self._merge_config(temp_config, env_config)

        return temp_config

    def validate_configuration(self) -> List[str]:
        """
        Validate current configuration against schema.

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.validator.has_schema():
            return ["No validation schema configured"]

        try:
            self.validator.validate(self._config_cache)
            return []
        except ValidationError as e:
            return [str(e)]

    def export_config(self, format: str = "yaml") -> str:
        """
        Export configuration in specified format.

        Args:
            format: Export format (yaml, json, toml)

        Returns:
            Configuration as formatted string
        """
        if format.lower() == "json":
            import json
            return json.dumps(self._config_cache, indent=2, default=str)
        elif format.lower() == "yaml":
            import yaml
            return yaml.dump(self._config_cache, default_flow_style=False)
        elif format.lower() == "toml":
            import toml
            return toml.dumps(self._config_cache)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        if self._hot_reload_watcher:
            self._hot_reload_watcher.stop()

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, "_hot_reload_watcher") and self._hot_reload_watcher:
            self._hot_reload_watcher.stop()