"""
Tests for configuration manager.
"""

import pytest
import tempfile
import os
from pathlib import Path

from enterprise_config import ConfigManager, Environment
from enterprise_config.exceptions import ConfigurationError, ValidationError
from enterprise_config.testing import MockConfigManager


class TestConfigManager:
    """Test configuration manager functionality."""

    def test_basic_configuration(self):
        """Test basic configuration operations."""
        with MockConfigManager() as config:
            # Test setting and getting values
            config.set("app.name", "Test App")
            config.set("app.debug", True)
            config.set("database.port", 5432)

            assert config.get("app.name") == "Test App"
            assert config.get("app.debug") is True
            assert config.get("database.port") == 5432

    def test_nested_configuration(self):
        """Test nested configuration access."""
        with MockConfigManager() as config:
            config.set("database.connection.host", "localhost")
            config.set("database.connection.port", 5432)

            assert config.get("database.connection.host") == "localhost"
            assert config.get("database.connection.port") == 5432

    def test_configuration_defaults(self):
        """Test configuration default values."""
        with MockConfigManager() as config:
            assert config.get("nonexistent.key", "default") == "default"
            assert config.get("another.key") is None

    def test_configuration_deletion(self):
        """Test configuration key deletion."""
        with MockConfigManager() as config:
            config.set("temp.key", "value")
            assert config.has("temp.key")

            assert config.delete("temp.key") is True
            assert not config.has("temp.key")
            assert config.delete("nonexistent.key") is False

    def test_feature_flags(self):
        """Test feature flag functionality."""
        with MockConfigManager() as config:
            # Set feature flag
            config.set_feature_flag("new_feature", True)
            assert config.feature_flag("new_feature") is True

            # Test default value
            assert config.feature_flag("nonexistent_flag", default=False) is False

    def test_secrets_management(self):
        """Test secrets management."""
        with MockConfigManager() as config:
            # Set and get secret
            config.set_secret("api_key", "secret-value")
            assert config.get_secret("api_key") == "secret-value"

            # Test nonexistent secret
            with pytest.raises(Exception):
                config.get_secret("nonexistent_secret")

    def test_configuration_export(self):
        """Test configuration export."""
        with MockConfigManager() as config:
            config.set("app.name", "Test App")
            config.set("app.version", "1.0.0")

            # Test YAML export
            yaml_export = config.export_config("yaml")
            assert "app:" in yaml_export
            assert "name: Test App" in yaml_export

            # Test JSON export
            json_export = config.export_config("json")
            assert '"app"' in json_export
            assert '"name": "Test App"' in json_export

    def test_change_callbacks(self):
        """Test configuration change callbacks."""
        with MockConfigManager() as config:
            changes = []

            def track_changes(key, old_value, new_value):
                changes.append((key, old_value, new_value))

            config.on_change(track_changes)

            config.set("test.key", "value1")
            config.set("test.key", "value2")
            config.delete("test.key")

            assert len(changes) == 3
            assert changes[0] == ("test.key", None, "value1")
            assert changes[1] == ("test.key", "value1", "value2")
            assert changes[2] == ("test.key", "value2", None)


class TestFileBackend:
    """Test file backend functionality."""

    def test_file_backend_yaml(self):
        """Test file backend with YAML format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config"
            
            # Create configuration manager
            config = ConfigManager(
                backend="file",
                config_path=str(config_path),
                environment=Environment.DEVELOPMENT,
            )

            # Set configuration
            config.set("app.name", "Test App")
            config.set("database.host", "localhost")

            # Verify file was created
            config_file = config_path / "development.yaml"
            assert config_file.exists()

            # Create new manager and verify persistence
            config2 = ConfigManager(
                backend="file",
                config_path=str(config_path),
                environment=Environment.DEVELOPMENT,
            )

            assert config2.get("app.name") == "Test App"
            assert config2.get("database.host") == "localhost"

    def test_environment_specific_config(self):
        """Test environment-specific configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config"
            config_path.mkdir()

            # Create base configuration
            base_config = config_path / "base.yaml"
            base_config.write_text("""
app:
  name: "Base App"
  debug: false
database:
  host: "localhost"
  port: 5432
""")

            # Create development configuration
            dev_config = config_path / "development.yaml"
            dev_config.write_text("""
app:
  debug: true
database:
  host: "dev-db"
""")

            # Test development environment
            config = ConfigManager(
                backend="file",
                config_path=str(config_path),
                environment=Environment.DEVELOPMENT,
            )

            assert config.get("app.name") == "Base App"  # From base
            assert config.get("app.debug") is True  # Overridden in dev
            assert config.get("database.host") == "dev-db"  # Overridden in dev
            assert config.get("database.port") == 5432  # From base

    def test_environment_variable_substitution(self):
        """Test environment variable substitution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config"
            config_path.mkdir()

            # Set environment variable
            os.environ["TEST_DB_HOST"] = "test-database"

            try:
                # Create configuration with env var
                config_file = config_path / "base.yaml"
                config_file.write_text("""
database:
  host: "${TEST_DB_HOST}"
  port: 5432
""")

                config = ConfigManager(
                    backend="file",
                    config_path=str(config_path),
                    environment=Environment.DEVELOPMENT,
                )

                assert config.get("database.host") == "test-database"

            finally:
                # Clean up environment variable
                os.environ.pop("TEST_DB_HOST", None)


class TestValidation:
    """Test configuration validation."""

    def test_validation_errors(self):
        """Test validation error handling."""
        with MockConfigManager() as config:
            # Test validation always passes for mock
            errors = config.validate_configuration()
            assert errors == []


class TestFeatureFlags:
    """Test feature flag functionality."""

    def test_feature_flag_environments(self):
        """Test feature flags with environment restrictions."""
        with MockConfigManager(environment=Environment.DEVELOPMENT) as config:
            # Set flag for development only
            config.set_feature_flag(
                "dev_feature",
                enabled=True,
                environments=[Environment.DEVELOPMENT],
            )

            assert config.feature_flag("dev_feature") is True

            # Change to production environment
            config.environment = Environment.PRODUCTION
            assert config.feature_flag("dev_feature") is False

    def test_feature_flag_user_groups(self):
        """Test feature flags with user group targeting."""
        with MockConfigManager() as config:
            # Set flag for beta users only
            config.set_feature_flag(
                "beta_feature",
                enabled=True,
                user_groups=["beta_users"],
            )

            assert config.feature_flag("beta_feature", user_group="beta_users") is True
            assert config.feature_flag("beta_feature", user_group="regular_users") is False


if __name__ == "__main__":
    pytest.main([__file__])