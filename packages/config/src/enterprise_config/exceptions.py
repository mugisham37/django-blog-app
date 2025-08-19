"""
Configuration management exceptions.
"""

from typing import Any, Dict, Optional


class ConfigurationError(Exception):
    """Base exception for configuration-related errors."""

    def __init__(
        self,
        message: str,
        key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.key = key
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.key:
            return f"Configuration error for '{self.key}': {self.message}"
        return f"Configuration error: {self.message}"


class ValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    def __init__(
        self,
        message: str,
        key: Optional[str] = None,
        validation_errors: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, key, {"validation_errors": validation_errors or {}})
        self.validation_errors = validation_errors or {}


class SecretNotFoundError(ConfigurationError):
    """Raised when a required secret is not found."""

    def __init__(self, secret_name: str, backend: Optional[str] = None):
        message = f"Secret '{secret_name}' not found"
        if backend:
            message += f" in backend '{backend}'"
        super().__init__(message, secret_name)
        self.secret_name = secret_name
        self.backend = backend


class FeatureFlagError(ConfigurationError):
    """Raised when feature flag operations fail."""

    def __init__(
        self,
        message: str,
        flag_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, flag_name, {"context": context or {}})
        self.flag_name = flag_name
        self.context = context or {}


class BackendError(ConfigurationError):
    """Raised when configuration backend operations fail."""

    def __init__(
        self,
        message: str,
        backend_type: str,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message,
            details={
                "backend_type": backend_type,
                "operation": operation,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.backend_type = backend_type
        self.operation = operation
        self.original_error = original_error


class EnvironmentError(ConfigurationError):
    """Raised when environment-related operations fail."""

    def __init__(self, message: str, environment: Optional[str] = None):
        super().__init__(message, details={"environment": environment})
        self.environment = environment


class HotReloadError(ConfigurationError):
    """Raised when hot reload operations fail."""

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        watcher_error: Optional[Exception] = None,
    ):
        super().__init__(
            message,
            details={
                "file_path": file_path,
                "watcher_error": str(watcher_error) if watcher_error else None,
            },
        )
        self.file_path = file_path
        self.watcher_error = watcher_error


class EncryptionError(ConfigurationError):
    """Raised when encryption/decryption operations fail."""

    def __init__(
        self,
        message: str,
        operation: str,
        key_id: Optional[str] = None,
    ):
        super().__init__(
            message,
            details={"operation": operation, "key_id": key_id},
        )
        self.operation = operation
        self.key_id = key_id