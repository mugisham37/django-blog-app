"""
Enterprise Database Package

A comprehensive database abstraction layer providing enterprise-grade features
including connection pooling, repository patterns, read replica management,
and database utilities.
"""

__version__ = "0.1.0"
__author__ = "Enterprise Team"
__email__ = "team@enterprise.com"

from .config import (
    get_database_config,
    DatabaseConfig,
    setup_read_replica,
)
from .repositories import BaseRepository
from .connections import ConnectionManager
from .migrations import MigrationManager
from .seeders import DataSeeder
from .monitoring import DatabaseMonitor
from .routers import DatabaseRouter

__all__ = [
    "get_database_config",
    "DatabaseConfig", 
    "setup_read_replica",
    "BaseRepository",
    "ConnectionManager",
    "MigrationManager",
    "DataSeeder",
    "DatabaseMonitor",
    "DatabaseRouter",
]