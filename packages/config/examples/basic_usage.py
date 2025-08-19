#!/usr/bin/env python3
"""
Basic usage example for enterprise configuration management.
"""

from enterprise_config import ConfigManager, Environment
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
    """Database configuration model."""
    host: str
    port: int = 5432
    name: str
    ssl_enabled: bool = True


class AppConfig(BaseModel):
    """Application configuration model."""
    name: str
    version: str
    debug: bool = False


def main():
    """Demonstrate basic configuration usage."""
    
    # Initialize configuration manager
    config = ConfigManager(
        environment=Environment.DEVELOPMENT,
        config_path="config/",
        enable_hot_reload=True
    )

    print("=== Basic Configuration Operations ===")
    
    # Set configuration values
    config.set("app.name", "My Enterprise App")
    config.set("app.version", "1.0.0")
    config.set("app.debug", True)
    
    config.set("database.host", "localhost")
    config.set("database.port", 5432)
    config.set("database.name", "myapp_dev")
    
    # Get configuration values
    app_name = config.get("app.name")
    db_host = config.get("database.host")
    
    print(f"App Name: {app_name}")
    print(f"Database Host: {db_host}")
    
    # Use type-safe configuration models
    print("\n=== Type-Safe Configuration ===")
    
    try:
        app_config = config.get_model(AppConfig, "app")
        print(f"App: {app_config.name} v{app_config.version} (debug: {app_config.debug})")
        
        db_config = config.get_model(DatabaseConfig, "database")
        print(f"Database: {db_config.host}:{db_config.port}/{db_config.name}")
    except Exception as e:
        print(f"Configuration validation error: {e}")
    
    # Feature flags
    print("\n=== Feature Flags ===")
    
    config.set_feature_flag("new_ui", True, environments=[Environment.DEVELOPMENT])
    config.set_feature_flag("beta_features", False)
    
    if config.feature_flag("new_ui"):
        print("✓ New UI is enabled")
    else:
        print("✗ New UI is disabled")
    
    if config.feature_flag("beta_features"):
        print("✓ Beta features are enabled")
    else:
        print("✗ Beta features are disabled")
    
    # Secrets management
    print("\n=== Secrets Management ===")
    
    config.set_secret("api_key", "super-secret-api-key")
    config.set_secret("db_password", "secure-database-password")
    
    try:
        api_key = config.get_secret("api_key")
        print(f"API Key: {api_key[:10]}...")  # Only show first 10 chars
    except Exception as e:
        print(f"Secret error: {e}")
    
    # Configuration change callbacks
    print("\n=== Change Callbacks ===")
    
    def on_config_change(key, old_value, new_value):
        print(f"Config changed: {key} = {old_value} -> {new_value}")
    
    config.on_change(on_config_change)
    
    # This will trigger the callback
    config.set("app.debug", False)
    
    # Export configuration
    print("\n=== Configuration Export ===")
    
    yaml_config = config.export_config("yaml")
    print("YAML Export:")
    print(yaml_config)


if __name__ == "__main__":
    main()