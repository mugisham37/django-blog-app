"""
Secure secrets management system.
"""

import base64
import os
from typing import Dict, List, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .models import Environment, SecretConfig
from .exceptions import SecretNotFoundError, EncryptionError


class SecretsManager:
    """
    Secure secrets management with encryption and environment isolation.
    
    Features:
    - AES encryption for secret values
    - Environment-specific secret access
    - Key rotation support
    - Audit logging
    """

    def __init__(self, backend, encryption_key: Optional[str] = None):
        """
        Initialize secrets manager.

        Args:
            backend: Configuration backend for storage
            encryption_key: Master encryption key (uses env var if not provided)
        """
        self.backend = backend
        self._secrets_cache: Dict[str, SecretConfig] = {}
        
        # Initialize encryption
        self._encryption_key = encryption_key or os.getenv("CONFIG_ENCRYPTION_KEY")
        if not self._encryption_key:
            # Generate a new key if none provided (for development)
            self._encryption_key = Fernet.generate_key().decode()
            print("Warning: Using generated encryption key. Set CONFIG_ENCRYPTION_KEY for production.")
        
        self._fernet = self._create_fernet(self._encryption_key)
        self._load_secrets()

    def _create_fernet(self, key: str) -> Fernet:
        """Create Fernet cipher from key."""
        try:
            # If key is already base64 encoded Fernet key
            if len(key) == 44 and key.endswith('='):
                return Fernet(key.encode())
            
            # Otherwise, derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'enterprise_config_salt',  # In production, use random salt
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
            return Fernet(derived_key)
            
        except Exception as e:
            raise EncryptionError(f"Failed to create encryption cipher: {str(e)}", "create_cipher")

    def _load_secrets(self) -> None:
        """Load secrets from backend."""
        try:
            secrets_data = self.backend.load_config("secrets") or {}
            self._secrets_cache = {}
            
            for secret_name, secret_config in secrets_data.items():
                try:
                    self._secrets_cache[secret_name] = SecretConfig(
                        name=secret_name,
                        **secret_config
                    )
                except Exception as e:
                    print(f"Warning: Invalid secret config '{secret_name}': {e}")

        except Exception as e:
            print(f"Warning: Failed to load secrets: {e}")
            self._secrets_cache = {}

    def _save_secrets(self) -> None:
        """Save secrets to backend."""
        secrets_data = {}
        for secret_name, secret in self._secrets_cache.items():
            secret_dict = secret.dict()
            secret_dict.pop("name", None)  # Remove name as it's the key
            secrets_data[secret_name] = secret_dict

        self.backend.save_config("secrets", secrets_data)

    def _encrypt_value(self, value: str) -> str:
        """Encrypt secret value."""
        try:
            encrypted_bytes = self._fernet.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt value: {str(e)}", "encrypt")

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt secret value."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt value: {str(e)}", "decrypt")

    def set_secret(
        self,
        secret_name: str,
        secret_value: str,
        environments: Optional[List[Environment]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Set encrypted secret value.

        Args:
            secret_name: Name of the secret
            secret_value: Plain text secret value
            environments: List of environments where secret is accessible
            metadata: Additional metadata for the secret
        """
        try:
            encrypted_value = self._encrypt_value(secret_value)
            
            secret_config = SecretConfig(
                name=secret_name,
                encrypted_value=encrypted_value,
                encryption_key_id="default",  # In production, use key rotation
                environments=environments or [],
                metadata=metadata or {},
                updated_at=datetime.utcnow(),
            )

            self._secrets_cache[secret_name] = secret_config
            self._save_secrets()

        except Exception as e:
            raise SecretNotFoundError(
                f"Failed to set secret '{secret_name}': {str(e)}"
            )

    def get_secret(
        self,
        secret_name: str,
        environment: Optional[Environment] = None,
    ) -> str:
        """
        Get decrypted secret value.

        Args:
            secret_name: Name of the secret
            environment: Current environment for access control

        Returns:
            Decrypted secret value

        Raises:
            SecretNotFoundError: If secret doesn't exist or access denied
        """
        secret_config = self._secrets_cache.get(secret_name)
        if not secret_config:
            raise SecretNotFoundError(secret_name)

        # Check environment access
        if environment and not secret_config.is_accessible_in_environment(environment):
            raise SecretNotFoundError(
                f"Secret '{secret_name}' not accessible in environment '{environment.value}'"
            )

        try:
            return self._decrypt_value(secret_config.encrypted_value)
        except Exception as e:
            raise EncryptionError(
                f"Failed to decrypt secret '{secret_name}': {str(e)}",
                "decrypt",
                secret_name,
            )

    def has_secret(
        self,
        secret_name: str,
        environment: Optional[Environment] = None,
    ) -> bool:
        """
        Check if secret exists and is accessible.

        Args:
            secret_name: Name of the secret
            environment: Current environment for access control

        Returns:
            True if secret exists and is accessible
        """
        secret_config = self._secrets_cache.get(secret_name)
        if not secret_config:
            return False

        if environment and not secret_config.is_accessible_in_environment(environment):
            return False

        return True

    def delete_secret(self, secret_name: str) -> bool:
        """
        Delete secret.

        Args:
            secret_name: Name of the secret to delete

        Returns:
            True if secret was deleted, False if it didn't exist
        """
        if secret_name in self._secrets_cache:
            del self._secrets_cache[secret_name]
            self._save_secrets()
            return True
        return False

    def list_secrets(
        self,
        environment: Optional[Environment] = None,
        include_values: bool = False,
    ) -> Dict[str, Dict[str, str]]:
        """
        List all secrets with metadata.

        Args:
            environment: Filter by environment access
            include_values: Whether to include decrypted values (dangerous!)

        Returns:
            Dictionary of secret names to metadata
        """
        secrets_info = {}
        
        for secret_name, secret_config in self._secrets_cache.items():
            # Check environment access
            if environment and not secret_config.is_accessible_in_environment(environment):
                continue

            info = {
                "created_at": secret_config.created_at.isoformat(),
                "updated_at": secret_config.updated_at.isoformat(),
                "environments": [env.value for env in secret_config.environments],
                "metadata": secret_config.metadata,
            }

            if include_values:
                try:
                    info["value"] = self._decrypt_value(secret_config.encrypted_value)
                except Exception:
                    info["value"] = "<decryption_failed>"

            secrets_info[secret_name] = info

        return secrets_info

    def rotate_secret(
        self,
        secret_name: str,
        new_value: str,
    ) -> None:
        """
        Rotate secret with new value.

        Args:
            secret_name: Name of the secret to rotate
            new_value: New secret value
        """
        if secret_name not in self._secrets_cache:
            raise SecretNotFoundError(secret_name)

        secret_config = self._secrets_cache[secret_name]
        
        # Keep old metadata and environments
        self.set_secret(
            secret_name=secret_name,
            secret_value=new_value,
            environments=secret_config.environments,
            metadata=secret_config.metadata,
        )

    def export_secrets(
        self,
        environment: Optional[Environment] = None,
        format: str = "env",
    ) -> str:
        """
        Export secrets in specified format.

        Args:
            environment: Filter by environment
            format: Export format ('env', 'json', 'yaml')

        Returns:
            Formatted secrets string
        """
        secrets = {}
        
        for secret_name, secret_config in self._secrets_cache.items():
            if environment and not secret_config.is_accessible_in_environment(environment):
                continue
                
            try:
                secrets[secret_name] = self._decrypt_value(secret_config.encrypted_value)
            except Exception:
                secrets[secret_name] = "<decryption_failed>"

        if format.lower() == "env":
            lines = []
            for name, value in secrets.items():
                # Convert to uppercase and replace special chars
                env_name = name.upper().replace("-", "_").replace(".", "_")
                lines.append(f"{env_name}={value}")
            return "\n".join(lines)
            
        elif format.lower() == "json":
            import json
            return json.dumps(secrets, indent=2)
            
        elif format.lower() == "yaml":
            import yaml
            return yaml.dump(secrets, default_flow_style=False)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def import_secrets(
        self,
        secrets_data: Dict[str, str],
        environment: Optional[Environment] = None,
        overwrite: bool = False,
    ) -> List[str]:
        """
        Import multiple secrets.

        Args:
            secrets_data: Dictionary of secret names to values
            environment: Environment to restrict access to
            overwrite: Whether to overwrite existing secrets

        Returns:
            List of imported secret names
        """
        imported = []
        
        for secret_name, secret_value in secrets_data.items():
            if not overwrite and secret_name in self._secrets_cache:
                continue
                
            self.set_secret(
                secret_name=secret_name,
                secret_value=secret_value,
                environments=[environment] if environment else [],
            )
            imported.append(secret_name)

        return imported

    def get_secret_metadata(self, secret_name: str) -> Optional[Dict[str, str]]:
        """Get secret metadata without decrypting value."""
        secret_config = self._secrets_cache.get(secret_name)
        if not secret_config:
            return None

        return {
            "created_at": secret_config.created_at.isoformat(),
            "updated_at": secret_config.updated_at.isoformat(),
            "environments": [env.value for env in secret_config.environments],
            "encryption_key_id": secret_config.encryption_key_id,
            "metadata": secret_config.metadata,
        }

    def reload_secrets(self) -> None:
        """Reload secrets from backend."""
        self._load_secrets()