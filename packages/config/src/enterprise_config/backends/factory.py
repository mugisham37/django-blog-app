"""
Backend factory for creating configuration backends.
"""

from typing import Any, Dict, Optional

from .base import BaseBackend
from .file_backend import FileBackend
from .redis_backend import RedisBackend
from ..exceptions import BackendError


class BackendFactory:
    """
    Factory class for creating configuration backends.
    
    Supports multiple backend types with automatic configuration.
    """

    _backend_classes = {
        "file": FileBackend,
        "redis": RedisBackend,
    }

    @classmethod
    def register_backend(cls, backend_type: str, backend_class: type) -> None:
        """
        Register a new backend type.

        Args:
            backend_type: Name of the backend type
            backend_class: Backend class that implements BaseBackend
        """
        if not issubclass(backend_class, BaseBackend):
            raise ValueError(f"Backend class must inherit from BaseBackend")
        
        cls._backend_classes[backend_type] = backend_class

    @classmethod
    def create_backend(
        self,
        backend_type: str,
        config_path: Optional[str] = None,
        **kwargs,
    ) -> BaseBackend:
        """
        Create configuration backend instance.

        Args:
            backend_type: Type of backend (file, redis, aws_ssm, vault)
            config_path: Path to configuration (for file backend)
            **kwargs: Backend-specific configuration parameters

        Returns:
            Configured backend instance

        Raises:
            BackendError: If backend type is not supported or creation fails
        """
        if backend_type not in self._backend_classes:
            available_types = ", ".join(self._backend_classes.keys())
            raise BackendError(
                f"Unsupported backend type '{backend_type}'. Available types: {available_types}",
                backend_type=backend_type,
                operation="create",
            )

        backend_class = self._backend_classes[backend_type]

        try:
            # Handle backend-specific parameter mapping
            if backend_type == "file":
                return self._create_file_backend(backend_class, config_path, **kwargs)
            elif backend_type == "redis":
                return self._create_redis_backend(backend_class, **kwargs)
            elif backend_type == "aws_ssm":
                return self._create_aws_ssm_backend(backend_class, **kwargs)
            elif backend_type == "vault":
                return self._create_vault_backend(backend_class, **kwargs)
            else:
                # Generic backend creation
                return backend_class(**kwargs)

        except Exception as e:
            raise BackendError(
                f"Failed to create {backend_type} backend: {str(e)}",
                backend_type=backend_type,
                operation="create",
                original_error=e,
            )

    @classmethod
    def _create_file_backend(
        cls,
        backend_class: type,
        config_path: Optional[str],
        **kwargs,
    ) -> FileBackend:
        """Create file backend with proper configuration."""
        params = {
            "config_path": config_path or "config/",
            "file_format": kwargs.get("file_format", "yaml"),
            "encoding": kwargs.get("encoding", "utf-8"),
            "create_dirs": kwargs.get("create_dirs", True),
        }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value

        return backend_class(**params)

    @classmethod
    def _create_redis_backend(
        cls,
        backend_class: type,
        **kwargs,
    ) -> RedisBackend:
        """Create Redis backend with proper configuration."""
        params = {
            "url": kwargs.get("redis_url", kwargs.get("url", "redis://localhost:6379/0")),
            "key_prefix": kwargs.get("key_prefix", "config:"),
            "connection_timeout": kwargs.get("connection_timeout", 30.0),
            "retry_attempts": kwargs.get("retry_attempts", 3),
            "retry_delay": kwargs.get("retry_delay", 1.0),
            "ssl_enabled": kwargs.get("ssl_enabled", False),
            "password": kwargs.get("password"),
        }

        # Add any additional Redis parameters
        redis_params = {}
        for key, value in kwargs.items():
            if key not in params and key.startswith(("redis_", "ssl_", "socket_")):
                redis_params[key] = value

        params.update(redis_params)
        return backend_class(**params)

    @classmethod
    def _create_aws_ssm_backend(
        cls,
        backend_class: type,
        **kwargs,
    ) -> BaseBackend:
        """Create AWS Systems Manager Parameter Store backend."""
        try:
            from .aws_ssm_backend import AWSSSMBackend
            cls._backend_classes["aws_ssm"] = AWSSSMBackend
        except ImportError:
            raise BackendError(
                "AWS SSM backend requires boto3 package",
                backend_type="aws_ssm",
                operation="create",
            )

        params = {
            "region": kwargs.get("aws_region", kwargs.get("region", "us-east-1")),
            "parameter_prefix": kwargs.get("parameter_prefix", "/app/"),
            "decrypt_secure_strings": kwargs.get("decrypt_secure_strings", True),
            "access_key_id": kwargs.get("aws_access_key_id"),
            "secret_access_key": kwargs.get("aws_secret_access_key"),
            "connection_timeout": kwargs.get("connection_timeout", 30.0),
            "retry_attempts": kwargs.get("retry_attempts", 3),
        }

        return backend_class(**params)

    @classmethod
    def _create_vault_backend(
        cls,
        backend_class: type,
        **kwargs,
    ) -> BaseBackend:
        """Create HashiCorp Vault backend."""
        try:
            from .vault_backend import VaultBackend
            cls._backend_classes["vault"] = VaultBackend
        except ImportError:
            raise BackendError(
                "Vault backend requires hvac package",
                backend_type="vault",
                operation="create",
            )

        params = {
            "url": kwargs.get("vault_url", kwargs.get("url", "https://vault.example.com")),
            "token": kwargs.get("vault_token", kwargs.get("token")),
            "mount_point": kwargs.get("mount_point", "secret"),
            "path_prefix": kwargs.get("path_prefix", "app/"),
            "verify_ssl": kwargs.get("verify_ssl", True),
            "connection_timeout": kwargs.get("connection_timeout", 30.0),
            "retry_attempts": kwargs.get("retry_attempts", 3),
        }

        return backend_class(**params)

    @classmethod
    def get_available_backends(cls) -> Dict[str, str]:
        """
        Get list of available backend types with descriptions.

        Returns:
            Dictionary mapping backend types to descriptions
        """
        descriptions = {
            "file": "File-based configuration storage (YAML, JSON, TOML)",
            "redis": "Redis-based distributed configuration storage",
            "aws_ssm": "AWS Systems Manager Parameter Store (requires boto3)",
            "vault": "HashiCorp Vault secret storage (requires hvac)",
        }

        available = {}
        for backend_type in cls._backend_classes.keys():
            available[backend_type] = descriptions.get(
                backend_type, f"{backend_type.title()} backend"
            )

        return available

    @classmethod
    def validate_backend_config(
        cls,
        backend_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Validate backend configuration.

        Args:
            backend_type: Type of backend
            config: Configuration parameters

        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}

        if backend_type not in cls._backend_classes:
            errors["backend_type"] = f"Unsupported backend type: {backend_type}"
            return errors

        # Backend-specific validation
        if backend_type == "file":
            if "config_path" in config:
                import os
                path = config["config_path"]
                if not os.path.exists(os.path.dirname(path) or "."):
                    errors["config_path"] = f"Directory does not exist: {path}"

            file_format = config.get("file_format", "yaml")
            if file_format not in ["yaml", "json", "toml"]:
                errors["file_format"] = f"Unsupported file format: {file_format}"

        elif backend_type == "redis":
            url = config.get("url", config.get("redis_url"))
            if not url:
                errors["url"] = "Redis URL is required"
            elif not url.startswith(("redis://", "rediss://")):
                errors["url"] = "Redis URL must start with redis:// or rediss://"

        elif backend_type == "aws_ssm":
            region = config.get("region", config.get("aws_region"))
            if not region:
                errors["region"] = "AWS region is required"

        elif backend_type == "vault":
            url = config.get("url", config.get("vault_url"))
            if not url:
                errors["url"] = "Vault URL is required"
            elif not url.startswith(("http://", "https://")):
                errors["url"] = "Vault URL must start with http:// or https://"

        return errors

    @classmethod
    def create_from_url(cls, url: str, **kwargs) -> BaseBackend:
        """
        Create backend from URL.

        Args:
            url: Backend URL (e.g., file:///path/to/config, redis://localhost:6379)
            **kwargs: Additional configuration parameters

        Returns:
            Configured backend instance
        """
        if url.startswith("file://"):
            config_path = url[7:]  # Remove 'file://' prefix
            return cls.create_backend("file", config_path=config_path, **kwargs)
        
        elif url.startswith(("redis://", "rediss://")):
            return cls.create_backend("redis", url=url, **kwargs)
        
        elif url.startswith("aws-ssm://"):
            # Format: aws-ssm://region/parameter-prefix
            parts = url[10:].split("/", 1)
            region = parts[0]
            prefix = f"/{parts[1]}/" if len(parts) > 1 else "/app/"
            return cls.create_backend(
                "aws_ssm",
                region=region,
                parameter_prefix=prefix,
                **kwargs
            )
        
        elif url.startswith(("http://", "https://")) and "vault" in url:
            return cls.create_backend("vault", url=url, **kwargs)
        
        else:
            raise BackendError(
                f"Cannot determine backend type from URL: {url}",
                backend_type="unknown",
                operation="create_from_url",
            )