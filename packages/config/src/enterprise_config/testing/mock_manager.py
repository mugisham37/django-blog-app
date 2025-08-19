"""
Mock configuration manager for testing.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Callable
from unittest.mock import MagicMock

from ..models import Environment, ConfigModel, FeatureFlag
from ..exceptions import ConfigurationError, ValidationError

T = TypeVar("T", bound=ConfigModel)


class MockConfigManager:
    """
    Mock configuration manager for testing purposes.
    
    Provides the same interface as ConfigManager but stores everything in memory
    without requiring actual backends or file systems.
    """

    def __init__(
        self,
        environment: Environment = Environment.DEVELOPMENT,
        initial_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize mock configuration manager.

        Args:
            environment: Target environment
            initial_config: Initial configuration data
        """
        self.environment = environment
        self._config_data = initial_config or {}
        self._feature_flags: Dict[str, FeatureFlag] = {}
        self._secrets: Dict[str, str] = {}
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Set configuration value."""
        keys = key.split(".")
        config = self._config_data

        # Navigate to parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        old_value = config.get(keys[-1])
        config[keys[-1]] = value

        # Notify change callbacks
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, value)
            except Exception:
                pass

    def get_model(self, model_class: Type[T], key: str) -> T:
        """Get configuration as a Pydantic model."""
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
        """Delete configuration key."""
        keys = key.split(".")
        config = self._config_data

        # Navigate to parent dictionary
        try:
            for k in keys[:-1]:
                config = config[k]
        except (KeyError, TypeError):
            return False

        # Delete the key
        if keys[-1] in config:
            old_value = config.pop(keys[-1])
            
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
        """Check feature flag status."""
        flag = self._feature_flags.get(flag_name)
        if not flag:
            return default

        return flag.is_active(
            environment=self.environment,
            user_group=user_group,
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
        flag = FeatureFlag(
            name=flag_name,
            enabled=enabled,
            environments=environments or [],
            user_groups=user_groups or [],
            **kwargs,
        )
        self._feature_flags[flag_name] = flag

    def get_secret(self, secret_name: str) -> str:
        """Get secret value."""
        if secret_name not in self._secrets:
            from ..exceptions import SecretNotFoundError
            raise SecretNotFoundError(secret_name)
        return self._secrets[secret_name]

    def set_secret(
        self,
        secret_name: str,
        secret_value: str,
        environments: Optional[List[Environment]] = None,
    ) -> None:
        """Set secret value."""
        self._secrets[secret_name] = secret_value

    def on_change(self, callback: Callable[[str, Any, Any], None]) -> None:
        """Register callback for configuration changes."""
        self._change_callbacks.append(callback)

    def reload(self) -> None:
        """Reload configuration (no-op for mock)."""
        pass

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return self._config_data.copy()

    def validate_configuration(self) -> List[str]:
        """Validate configuration (always passes for mock)."""
        return []

    def export_config(self, format: str = "yaml") -> str:
        """Export configuration in specified format."""
        if format.lower() == "json":
            import json
            return json.dumps(self._config_data, indent=2, default=str)
        elif format.lower() == "yaml":
            import yaml
            return yaml.dump(self._config_data, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    # Mock-specific methods for testing

    def reset(self) -> None:
        """Reset all configuration data."""
        self._config_data.clear()
        self._feature_flags.clear()
        self._secrets.clear()
        self._change_callbacks.clear()

    def load_test_config(self, config: Dict[str, Any]) -> None:
        """Load test configuration data."""
        self._config_data.update(config)

    def load_test_feature_flags(self, flags: Dict[str, Dict[str, Any]]) -> None:
        """Load test feature flags."""
        for flag_name, flag_config in flags.items():
            self.set_feature_flag(flag_name, **flag_config)

    def load_test_secrets(self, secrets: Dict[str, str]) -> None:
        """Load test secrets."""
        self._secrets.update(secrets)

    def get_feature_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags (for testing)."""
        return self._feature_flags.copy()

    def get_secrets(self) -> Dict[str, str]:
        """Get all secrets (for testing)."""
        return self._secrets.copy()

    def simulate_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """Simulate configuration change for testing callbacks."""
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception:
                pass

    def assert_config_equals(self, expected: Dict[str, Any]) -> None:
        """Assert configuration equals expected values."""
        assert self._config_data == expected, f"Config mismatch: {self._config_data} != {expected}"

    def assert_has_key(self, key: str) -> None:
        """Assert configuration has key."""
        assert self.has(key), f"Configuration key '{key}' not found"

    def assert_key_equals(self, key: str, expected_value: Any) -> None:
        """Assert configuration key equals expected value."""
        actual_value = self.get(key)
        assert actual_value == expected_value, f"Key '{key}': {actual_value} != {expected_value}"

    def assert_feature_flag_enabled(self, flag_name: str) -> None:
        """Assert feature flag is enabled."""
        assert self.feature_flag(flag_name), f"Feature flag '{flag_name}' is not enabled"

    def assert_feature_flag_disabled(self, flag_name: str) -> None:
        """Assert feature flag is disabled."""
        assert not self.feature_flag(flag_name), f"Feature flag '{flag_name}' is enabled"

    def assert_has_secret(self, secret_name: str) -> None:
        """Assert secret exists."""
        assert secret_name in self._secrets, f"Secret '{secret_name}' not found"

    def create_mock_backend(self) -> MagicMock:
        """Create mock backend for testing."""
        backend = MagicMock()
        backend.load_config.return_value = self._config_data
        backend.save_config.return_value = None
        backend.delete_config.return_value = True
        backend.list_configs.return_value = list(self._config_data.keys())
        backend.exists.return_value = True
        backend.health_check.return_value = True
        return backend

    # Context manager support
    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.reset()