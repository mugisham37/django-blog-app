"""
Database package exceptions.
"""


class DatabaseError(Exception):
    """Base exception for database package."""
    pass


class RepositoryError(DatabaseError):
    """Exception raised by repository operations."""
    pass


class ObjectNotFoundError(RepositoryError):
    """Exception raised when an object is not found."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised for connection-related issues."""
    pass


class MigrationError(DatabaseError):
    """Exception raised for migration-related issues."""
    pass


class SeedingError(DatabaseError):
    """Exception raised for data seeding issues."""
    pass


class BackupError(DatabaseError):
    """Exception raised for backup/restore issues."""
    pass


class MonitoringError(DatabaseError):
    """Exception raised for monitoring issues."""
    pass