"""
Tests for configuration backends.
"""

import pytest
import tempfile
import json
from pathlib import Path

from enterprise_config.backends import FileBackend, BackendFactory
from enterprise_config.exceptions import BackendError


class TestFileBackend:
    """Test file backend functionality."""

    def test_yaml_operations(self):
        """Test YAML file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = FileBackend(config_path=temp_dir, file_format="yaml")

            # Test save and load
            config_data = {"app": {"name": "Test App", "debug": True}}
            backend.save_config("test", config_data)

            loaded_data = backend.load_config("test")
            assert loaded_data == config_data

            # Test exists
            assert backend.exists("test") is True
            assert backend.exists("nonexistent") is False

            # Test list
            configs = backend.list_configs()
            assert "test" in configs

            # Test delete
            assert backend.delete_config("test") is True
            assert backend.exists("test") is False

    def test_json_operations(self):
        """Test JSON file operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = FileBackend(config_path=temp_dir, file_format="json")

            config_data = {"database": {"host": "localhost", "port": 5432}}
            backend.save_config("db_config", config_data)

            loaded_data = backend.load_config("db_config")
            assert loaded_data == config_data

    def test_nonexistent_config(self):
        """Test loading nonexistent configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = FileBackend(config_path=temp_dir)

            result = backend.load_config("nonexistent")
            assert result is None

    def test_invalid_format(self):
        """Test invalid file format."""
        with pytest.raises(ValueError):
            FileBackend(file_format="invalid")

    def test_backup_and_restore(self):
        """Test backup and restore functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            backup_dir = Path(temp_dir) / "backup"

            backend = FileBackend(config_path=str(config_dir))

            # Create test configurations
            backend.save_config("app", {"name": "Test App"})
            backend.save_config("db", {"host": "localhost"})

            # Backup configurations
            backed_up = backend.backup_configs(str(backup_dir))
            assert "app" in backed_up
            assert "db" in backed_up

            # Delete original configs
            backend.delete_config("app")
            backend.delete_config("db")

            # Restore from backup
            restored = backend.restore_configs(str(backup_dir))
            assert "app" in restored
            assert "db" in restored

            # Verify restoration
            assert backend.load_config("app") == {"name": "Test App"}
            assert backend.load_config("db") == {"host": "localhost"}


class TestBackendFactory:
    """Test backend factory functionality."""

    def test_create_file_backend(self):
        """Test creating file backend."""
        backend = BackendFactory.create_backend("file", config_path="test/")
        assert isinstance(backend, FileBackend)

    def test_unsupported_backend(self):
        """Test creating unsupported backend."""
        with pytest.raises(BackendError):
            BackendFactory.create_backend("unsupported")

    def test_available_backends(self):
        """Test getting available backends."""
        backends = BackendFactory.get_available_backends()
        assert "file" in backends
        assert isinstance(backends["file"], str)

    def test_validate_backend_config(self):
        """Test backend configuration validation."""
        # Valid file backend config
        errors = BackendFactory.validate_backend_config("file", {
            "config_path": "config/",
            "file_format": "yaml",
        })
        assert len(errors) == 0

        # Invalid file format
        errors = BackendFactory.validate_backend_config("file", {
            "file_format": "invalid",
        })
        assert "file_format" in errors

    def test_create_from_url(self):
        """Test creating backend from URL."""
        backend = BackendFactory.create_from_url("file:///tmp/config")
        assert isinstance(backend, FileBackend)


if __name__ == "__main__":
    pytest.main([__file__])