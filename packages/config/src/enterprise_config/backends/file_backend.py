"""
File-based configuration backend.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .base import BaseBackend
from ..exceptions import BackendError


class FileBackend(BaseBackend):
    """
    File-based configuration backend supporting YAML, JSON, and TOML formats.
    
    Configuration files are stored in a directory structure:
    config/
    ├── base.yaml
    ├── development.yaml
    ├── staging.yaml
    ├── production.yaml
    ├── feature_flags.yaml
    └── secrets.yaml
    """

    def __init__(
        self,
        config_path: str = "config/",
        file_format: str = "yaml",
        encoding: str = "utf-8",
        create_dirs: bool = True,
    ):
        """
        Initialize file backend.

        Args:
            config_path: Path to configuration directory
            file_format: File format (yaml, json, toml)
            encoding: File encoding
            create_dirs: Whether to create directories if they don't exist
        """
        self.config_path = Path(config_path)
        self.file_format = file_format.lower()
        self.encoding = encoding

        if create_dirs:
            self.config_path.mkdir(parents=True, exist_ok=True)

        # Validate format
        if self.file_format not in ["yaml", "json", "toml"]:
            raise ValueError(f"Unsupported file format: {file_format}")

        # Import required modules based on format
        if self.file_format == "toml":
            try:
                import toml
                self._toml = toml
            except ImportError:
                raise ImportError("toml package required for TOML format")

    def _get_file_path(self, config_name: str) -> Path:
        """Get full file path for configuration name."""
        return self.config_path / f"{config_name}.{self.file_format}"

    def _load_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from file."""
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                if self.file_format == "yaml":
                    return yaml.safe_load(f) or {}
                elif self.file_format == "json":
                    return json.load(f) or {}
                elif self.file_format == "toml":
                    return self._toml.load(f) or {}

        except Exception as e:
            raise BackendError(
                f"Failed to load configuration from {file_path}: {str(e)}",
                backend_type="file",
                operation="load",
                original_error=e,
            )

    def _save_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding=self.encoding) as f:
                if self.file_format == "yaml":
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                elif self.file_format == "json":
                    json.dump(data, f, indent=2, ensure_ascii=False)
                elif self.file_format == "toml":
                    self._toml.dump(data, f)

        except Exception as e:
            raise BackendError(
                f"Failed to save configuration to {file_path}: {str(e)}",
                backend_type="file",
                operation="save",
                original_error=e,
            )

    def load_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Load configuration by name."""
        file_path = self._get_file_path(config_name)
        return self._load_file(file_path)

    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """Save configuration by name."""
        file_path = self._get_file_path(config_name)
        self._save_file(file_path, config_data)

    def delete_config(self, config_name: str) -> bool:
        """Delete configuration by name."""
        file_path = self._get_file_path(config_name)
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                raise BackendError(
                    f"Failed to delete configuration {config_name}: {str(e)}",
                    backend_type="file",
                    operation="delete",
                    original_error=e,
                )
        return False

    def list_configs(self) -> List[str]:
        """List all available configuration names."""
        if not self.config_path.exists():
            return []

        configs = []
        pattern = f"*.{self.file_format}"
        
        try:
            for file_path in self.config_path.glob(pattern):
                if file_path.is_file():
                    configs.append(file_path.stem)
        except Exception as e:
            raise BackendError(
                f"Failed to list configurations: {str(e)}",
                backend_type="file",
                operation="list",
                original_error=e,
            )

        return sorted(configs)

    def exists(self, config_name: str) -> bool:
        """Check if configuration exists."""
        file_path = self._get_file_path(config_name)
        return file_path.exists()

    def get_watch_paths(self) -> List[str]:
        """Get paths to watch for configuration changes."""
        return [str(self.config_path)]

    def get_file_info(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Get file information for configuration.

        Args:
            config_name: Name of the configuration

        Returns:
            File information dictionary or None if not found
        """
        file_path = self._get_file_path(config_name)
        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()
            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "format": self.file_format,
            }
        except Exception:
            return None

    def backup_configs(self, backup_dir: str) -> List[str]:
        """
        Backup all configurations to directory.

        Args:
            backup_dir: Directory to store backups

        Returns:
            List of backed up configuration names
        """
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        backed_up = []
        
        for config_name in self.list_configs():
            try:
                config_data = self.load_config(config_name)
                if config_data:
                    backup_file = backup_path / f"{config_name}.{self.file_format}"
                    self._save_file(backup_file, config_data)
                    backed_up.append(config_name)
            except Exception as e:
                print(f"Warning: Failed to backup {config_name}: {e}")

        return backed_up

    def restore_configs(self, backup_dir: str) -> List[str]:
        """
        Restore configurations from backup directory.

        Args:
            backup_dir: Directory containing backups

        Returns:
            List of restored configuration names
        """
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            raise BackendError(
                f"Backup directory does not exist: {backup_dir}",
                backend_type="file",
                operation="restore",
            )

        restored = []
        pattern = f"*.{self.file_format}"
        
        for backup_file in backup_path.glob(pattern):
            try:
                config_name = backup_file.stem
                config_data = self._load_file(backup_file)
                if config_data:
                    self.save_config(config_name, config_data)
                    restored.append(config_name)
            except Exception as e:
                print(f"Warning: Failed to restore {backup_file.name}: {e}")

        return restored

    def validate_files(self) -> Dict[str, List[str]]:
        """
        Validate all configuration files.

        Returns:
            Dictionary with config names and their validation errors
        """
        validation_results = {}
        
        for config_name in self.list_configs():
            errors = []
            try:
                config_data = self.load_config(config_name)
                if config_data is None:
                    errors.append("Failed to load configuration")
                elif not isinstance(config_data, dict):
                    errors.append("Configuration must be a dictionary")
            except Exception as e:
                errors.append(f"Load error: {str(e)}")
                
            validation_results[config_name] = errors

        return validation_results

    def get_config_size(self, config_name: str) -> Optional[int]:
        """Get configuration file size in bytes."""
        file_path = self._get_file_path(config_name)
        if file_path.exists():
            return file_path.stat().st_size
        return None

    def get_total_size(self) -> int:
        """Get total size of all configuration files."""
        total_size = 0
        for config_name in self.list_configs():
            size = self.get_config_size(config_name)
            if size:
                total_size += size
        return total_size