"""
Configuration models and data structures.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator


class Environment(str, Enum):
    """Supported environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """Create Environment from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"Invalid environment: {value}")


class ConfigModel(BaseModel):
    """Base model for configuration objects."""

    class Config:
        """Pydantic configuration."""

        extra = "forbid"
        validate_assignment = True
        use_enum_values = True


class FeatureFlag(ConfigModel):
    """Feature flag configuration model."""

    name: str
    enabled: bool = False
    description: Optional[str] = None
    environments: List[Environment] = Field(default_factory=list)
    user_groups: List[str] = Field(default_factory=list)
    percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("percentage")
    def validate_percentage(cls, v):
        """Validate percentage is between 0 and 100."""
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError("Percentage must be between 0.0 and 100.0")
        return v

    @validator("end_date")
    def validate_end_date(cls, v, values):
        """Validate end_date is after start_date."""
        if v and "start_date" in values and values["start_date"]:
            if v <= values["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v

    def is_active(
        self,
        environment: Optional[Environment] = None,
        user_group: Optional[str] = None,
        current_time: Optional[datetime] = None,
    ) -> bool:
        """Check if feature flag is active for given context."""
        if not self.enabled:
            return False

        # Check environment
        if environment and self.environments and environment not in self.environments:
            return False

        # Check user group
        if user_group and self.user_groups and user_group not in self.user_groups:
            return False

        # Check time window
        current_time = current_time or datetime.utcnow()
        if self.start_date and current_time < self.start_date:
            return False
        if self.end_date and current_time > self.end_date:
            return False

        return True


class SecretConfig(ConfigModel):
    """Secret configuration model."""

    name: str
    encrypted_value: str
    encryption_key_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    environments: List[Environment] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_accessible_in_environment(self, environment: Environment) -> bool:
        """Check if secret is accessible in given environment."""
        return not self.environments or environment in self.environments


class ConfigSource(ConfigModel):
    """Configuration source metadata."""

    path: str
    type: str  # file, redis, aws_ssm, vault, etc.
    last_modified: Optional[datetime] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfigEntry(ConfigModel):
    """Individual configuration entry."""

    key: str
    value: Any
    source: ConfigSource
    environment: Optional[Environment] = None
    encrypted: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConfigSnapshot(ConfigModel):
    """Configuration snapshot for auditing."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    environment: Environment
    entries: List[ConfigEntry]
    checksum: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationRule(ConfigModel):
    """Configuration validation rule."""

    key_pattern: str
    value_type: str
    required: bool = False
    default_value: Optional[Any] = None
    validator_function: Optional[str] = None
    error_message: Optional[str] = None


class ConfigSchema(ConfigModel):
    """Configuration schema definition."""

    name: str
    version: str
    description: Optional[str] = None
    rules: List[ValidationRule]
    environments: List[Environment] = Field(default_factory=list)


class HotReloadConfig(ConfigModel):
    """Hot reload configuration."""

    enabled: bool = True
    watch_paths: List[str] = Field(default_factory=list)
    debounce_seconds: float = 1.0
    recursive: bool = True
    ignore_patterns: List[str] = Field(default_factory=lambda: ["*.tmp", "*.swp", "*~"])


class BackendConfig(ConfigModel):
    """Backend configuration base class."""

    type: str
    connection_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


class FileBackendConfig(BackendConfig):
    """File backend configuration."""

    type: str = "file"
    config_path: str = "config/"
    file_format: str = "yaml"  # yaml, json, toml
    encoding: str = "utf-8"


class RedisBackendConfig(BackendConfig):
    """Redis backend configuration."""

    type: str = "redis"
    url: str = "redis://localhost:6379/0"
    key_prefix: str = "config:"
    ssl_enabled: bool = False
    password: Optional[str] = None


class AWSSSMBackendConfig(BackendConfig):
    """AWS Systems Manager Parameter Store backend configuration."""

    type: str = "aws_ssm"
    region: str = "us-east-1"
    parameter_prefix: str = "/app/"
    decrypt_secure_strings: bool = True
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None


class VaultBackendConfig(BackendConfig):
    """HashiCorp Vault backend configuration."""

    type: str = "vault"
    url: str = "https://vault.example.com"
    token: Optional[str] = None
    mount_point: str = "secret"
    path_prefix: str = "app/"
    verify_ssl: bool = True