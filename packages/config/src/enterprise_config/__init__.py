"""
Enterprise Configuration Management Package

A comprehensive configuration management system for enterprise applications.
"""

from .manager import ConfigManager
from .models import Environment, ConfigModel
from .exceptions import (
    ConfigurationError,
    ValidationError,
    SecretNotFoundError,
    FeatureFlagError,
)
from .feature_flags import FeatureFlagManager
from .secrets import SecretsManager
from .validators import ConfigValidator

__version__ = "1.0.0"
__author__ = "Enterprise Development Team"
__email__ = "dev@enterprise.com"

__all__ = [
    "ConfigManager",
    "Environment",
    "ConfigModel",
    "ConfigurationError",
    "ValidationError",
    "SecretNotFoundError",
    "FeatureFlagError",
    "FeatureFlagManager",
    "SecretsManager",
    "ConfigValidator",
]