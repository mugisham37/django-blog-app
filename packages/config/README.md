# Enterprise Configuration Management Package

A comprehensive configuration management system for enterprise applications with support for environment-specific configurations, feature flags, secure secrets management, and hot-reloading capabilities.

## Features

- **Environment-specific Configuration**: Manage configurations for development, staging, and production environments
- **Feature Flag System**: Runtime configuration with dynamic feature toggling
- **Secure Secrets Management**: Encrypted storage and retrieval of sensitive configuration data
- **Configuration Validation**: Type checking and validation using Pydantic models
- **Hot-reloading**: Dynamic configuration updates without application restart
- **Multiple Backends**: Support for file-based, Redis, AWS Parameter Store, and HashiCorp Vault backends
- **Configuration Inheritance**: Hierarchical configuration with environment-specific overrides
- **Audit Logging**: Track configuration changes and access patterns

## Installation

```bash
pip install enterprise-config

# With optional dependencies
pip install enterprise-config[aws,vault,dev]
```

## Quick Start

```python
from enterprise_config import ConfigManager, Environment

# Initialize configuration manager
config = ConfigManager(
    environment=Environment.DEVELOPMENT,
    config_path="config/",
    enable_hot_reload=True
)

# Access configuration values
database_url = config.get("database.url")
feature_enabled = config.feature_flag("new_feature", default=False)

# Type-safe configuration access
@config.model
class DatabaseConfig:
    host: str
    port: int = 5432
    name: str
    ssl_enabled: bool = True

db_config = config.get_model(DatabaseConfig, "database")
```

## Configuration Structure

```yaml
# config/base.yaml
app:
  name: "Enterprise Application"
  version: "1.0.0"
  debug: false

database:
  host: "localhost"
  port: 5432
  name: "enterprise_db"

# config/development.yaml
app:
  debug: true

database:
  host: "dev-db.local"
  name: "enterprise_dev"

# config/production.yaml
database:
  host: "${DB_HOST}"
  ssl_enabled: true
```

## Environment Variables

Configuration values can reference environment variables using `${VAR_NAME}` syntax:

```yaml
database:
  url: "${DATABASE_URL}"
  password: "${DB_PASSWORD}"
```

## Feature Flags

```python
# Define feature flags
config.set_feature_flag("new_ui", True, environments=["development", "staging"])
config.set_feature_flag("beta_features", False, user_groups=["beta_users"])

# Use feature flags
if config.feature_flag("new_ui"):
    render_new_ui()
else:
    render_legacy_ui()
```

## Secrets Management

```python
# Store encrypted secrets
config.set_secret("api_key", "secret-api-key-value")
config.set_secret("db_password", "super-secret-password")

# Retrieve secrets (automatically decrypted)
api_key = config.get_secret("api_key")
```

## Configuration Backends

### File Backend (Default)

```python
config = ConfigManager(backend="file", config_path="config/")
```

### Redis Backend

```python
config = ConfigManager(
    backend="redis",
    redis_url="redis://localhost:6379/0",
    key_prefix="app:config"
)
```

### AWS Parameter Store Backend

```python
config = ConfigManager(
    backend="aws_ssm",
    aws_region="us-east-1",
    parameter_prefix="/myapp/"
)
```

### HashiCorp Vault Backend

```python
config = ConfigManager(
    backend="vault",
    vault_url="https://vault.example.com",
    vault_token="your-vault-token"
)
```

## Hot Reloading

Enable automatic configuration reloading when files change:

```python
config = ConfigManager(enable_hot_reload=True)

# Register callback for configuration changes
@config.on_change
def handle_config_change(key: str, old_value: Any, new_value: Any):
    print(f"Configuration changed: {key} = {new_value}")
```

## Validation and Type Safety

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class AppConfig(BaseModel):
    name: str
    version: str
    debug: bool = False
    allowed_hosts: List[str] = Field(default_factory=list)
    secret_key: Optional[str] = None

# Validate configuration against model
app_config = config.get_model(AppConfig, "app")
```

## CLI Usage

```bash
# Validate configuration
enterprise-config validate --config-path config/

# Show current configuration
enterprise-config show --environment production

# Set feature flag
enterprise-config feature-flag set new_feature true --environment development

# Encrypt secrets
enterprise-config secret set api_key "my-secret-value"
```

## Testing

```python
import pytest
from enterprise_config import ConfigManager
from enterprise_config.testing import MockConfigManager

def test_feature_flag():
    config = MockConfigManager()
    config.set_feature_flag("test_feature", True)

    assert config.feature_flag("test_feature") is True
```

## License

MIT License - see LICENSE file for details.
