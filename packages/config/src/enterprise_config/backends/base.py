"""
Base backend interface for configuration storage.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseBackend(ABC):
    """
    Abstract base class for configuration backends.
    
    All configuration backends must implement these methods.
    """

    @abstractmethod
    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Load configuration by name.

        Args:
            config_name: Name of the configuration (e.g., 'base', 'development')

        Returns:
            Configuration dictionary or None if not found
        """
        pass

    @abstractmethod
    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """
        Save configuration by name.

        Args:
            config_name: Name of the configuration
            config_data: Configuration data to save
        """
        pass

    @abstractmethod
    def delete_config(self, config_name: str) -> bool:
        """
        Delete configuration by name.

        Args:
            config_name: Name of the configuration to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_configs(self) -> List[str]:
        """
        List all available configuration names.

        Returns:
            List of configuration names
        """
        pass

    @abstractmethod
    def exists(self, config_name: str) -> bool:
        """
        Check if configuration exists.

        Args:
            config_name: Name of the configuration

        Returns:
            True if configuration exists
        """
        pass

    def get_watch_paths(self) -> List[str]:
        """
        Get paths to watch for configuration changes.
        
        Returns:
            List of paths to watch (empty if not supported)
        """
        return []

    def health_check(self) -> bool:
        """
        Check if backend is healthy and accessible.

        Returns:
            True if backend is healthy
        """
        try:
            self.list_configs()
            return True
        except Exception:
            return False

    def backup_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Create backup of configuration.

        Args:
            config_name: Name of the configuration to backup

        Returns:
            Configuration data or None if not found
        """
        return self.load_config(config_name)

    def restore_config(
        self,
        config_name: str,
        backup_data: Dict[str, Any],
    ) -> None:
        """
        Restore configuration from backup.

        Args:
            config_name: Name of the configuration
            backup_data: Backup data to restore
        """
        self.save_config(config_name, backup_data)