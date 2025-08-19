"""
Feature flag management system.
"""

import hashlib
import random
from typing import Any, Dict, List, Optional
from datetime import datetime

from .models import Environment, FeatureFlag
from .exceptions import FeatureFlagError


class FeatureFlagManager:
    """
    Feature flag management with support for:
    - Environment-specific flags
    - User group targeting
    - Percentage rollouts
    - Time-based activation
    - A/B testing support
    """

    def __init__(self, backend):
        """Initialize feature flag manager with backend."""
        self.backend = backend
        self._flag_cache: Dict[str, FeatureFlag] = {}
        self._load_flags()

    def _load_flags(self) -> None:
        """Load feature flags from backend."""
        try:
            flags_data = self.backend.load_config("feature_flags") or {}
            self._flag_cache = {}
            
            for flag_name, flag_config in flags_data.items():
                try:
                    self._flag_cache[flag_name] = FeatureFlag(
                        name=flag_name,
                        **flag_config
                    )
                except Exception as e:
                    print(f"Warning: Invalid feature flag '{flag_name}': {e}")

        except Exception as e:
            print(f"Warning: Failed to load feature flags: {e}")
            self._flag_cache = {}

    def _save_flags(self) -> None:
        """Save feature flags to backend."""
        flags_data = {}
        for flag_name, flag in self._flag_cache.items():
            flag_dict = flag.dict()
            flag_dict.pop("name", None)  # Remove name as it's the key
            flags_data[flag_name] = flag_dict

        self.backend.save_config("feature_flags", flags_data)

    def is_enabled(
        self,
        flag_name: str,
        environment: Optional[Environment] = None,
        user_group: Optional[str] = None,
        user_id: Optional[str] = None,
        default: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check if feature flag is enabled for given context.

        Args:
            flag_name: Name of the feature flag
            environment: Current environment
            user_group: User group for targeting
            user_id: User ID for percentage rollouts
            default: Default value if flag not found
            context: Additional context for evaluation

        Returns:
            True if feature is enabled, False otherwise
        """
        try:
            flag = self._flag_cache.get(flag_name)
            if not flag:
                return default

            # Check basic activation
            if not flag.is_active(
                environment=environment,
                user_group=user_group,
                current_time=datetime.utcnow(),
            ):
                return False

            # Check percentage rollout
            if flag.percentage is not None and user_id:
                if not self._is_user_in_percentage(flag_name, user_id, flag.percentage):
                    return False

            # Apply context-based rules if any
            if context and flag.metadata.get("context_rules"):
                return self._evaluate_context_rules(flag, context)

            return flag.enabled

        except Exception as e:
            print(f"Error evaluating feature flag '{flag_name}': {e}")
            return default

    def _is_user_in_percentage(
        self, flag_name: str, user_id: str, percentage: float
    ) -> bool:
        """
        Determine if user is in percentage rollout using consistent hashing.
        
        This ensures the same user always gets the same result for a flag.
        """
        # Create a hash of flag_name + user_id for consistency
        hash_input = f"{flag_name}:{user_id}".encode("utf-8")
        hash_value = hashlib.md5(hash_input).hexdigest()
        
        # Convert first 8 characters to integer and get percentage
        hash_int = int(hash_value[:8], 16)
        user_percentage = (hash_int % 10000) / 100.0  # 0-99.99%
        
        return user_percentage < percentage

    def _evaluate_context_rules(
        self, flag: FeatureFlag, context: Dict[str, Any]
    ) -> bool:
        """Evaluate context-based rules for feature flag."""
        rules = flag.metadata.get("context_rules", [])
        
        for rule in rules:
            rule_type = rule.get("type")
            
            if rule_type == "equals":
                key = rule.get("key")
                expected_value = rule.get("value")
                if context.get(key) != expected_value:
                    return False
                    
            elif rule_type == "in":
                key = rule.get("key")
                allowed_values = rule.get("values", [])
                if context.get(key) not in allowed_values:
                    return False
                    
            elif rule_type == "greater_than":
                key = rule.get("key")
                threshold = rule.get("value")
                if context.get(key, 0) <= threshold:
                    return False
                    
            elif rule_type == "less_than":
                key = rule.get("key")
                threshold = rule.get("value")
                if context.get(key, 0) >= threshold:
                    return False

        return True

    def set_flag(
        self,
        flag_name: str,
        enabled: bool,
        description: Optional[str] = None,
        environments: Optional[List[Environment]] = None,
        user_groups: Optional[List[str]] = None,
        percentage: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set or update feature flag configuration.

        Args:
            flag_name: Name of the feature flag
            enabled: Whether the flag is enabled
            description: Human-readable description
            environments: List of environments where flag is active
            user_groups: List of user groups for targeting
            percentage: Percentage rollout (0-100)
            start_date: When the flag becomes active
            end_date: When the flag becomes inactive
            metadata: Additional metadata for the flag
        """
        try:
            flag = FeatureFlag(
                name=flag_name,
                enabled=enabled,
                description=description,
                environments=environments or [],
                user_groups=user_groups or [],
                percentage=percentage,
                start_date=start_date,
                end_date=end_date,
                metadata=metadata or {},
            )

            self._flag_cache[flag_name] = flag
            self._save_flags()

        except Exception as e:
            raise FeatureFlagError(
                f"Failed to set feature flag '{flag_name}': {str(e)}",
                flag_name=flag_name,
            )

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get feature flag configuration."""
        return self._flag_cache.get(flag_name)

    def list_flags(
        self, environment: Optional[Environment] = None
    ) -> Dict[str, FeatureFlag]:
        """
        List all feature flags, optionally filtered by environment.

        Args:
            environment: Filter flags by environment

        Returns:
            Dictionary of flag names to FeatureFlag objects
        """
        if environment is None:
            return self._flag_cache.copy()

        filtered_flags = {}
        for flag_name, flag in self._flag_cache.items():
            if not flag.environments or environment in flag.environments:
                filtered_flags[flag_name] = flag

        return filtered_flags

    def delete_flag(self, flag_name: str) -> bool:
        """
        Delete feature flag.

        Args:
            flag_name: Name of the flag to delete

        Returns:
            True if flag was deleted, False if it didn't exist
        """
        if flag_name in self._flag_cache:
            del self._flag_cache[flag_name]
            self._save_flags()
            return True
        return False

    def enable_flag(self, flag_name: str) -> None:
        """Enable feature flag."""
        flag = self._flag_cache.get(flag_name)
        if flag:
            flag.enabled = True
            self._save_flags()
        else:
            raise FeatureFlagError(f"Feature flag '{flag_name}' not found")

    def disable_flag(self, flag_name: str) -> None:
        """Disable feature flag."""
        flag = self._flag_cache.get(flag_name)
        if flag:
            flag.enabled = False
            self._save_flags()
        else:
            raise FeatureFlagError(f"Feature flag '{flag_name}' not found")

    def set_percentage(self, flag_name: str, percentage: float) -> None:
        """
        Set percentage rollout for feature flag.

        Args:
            flag_name: Name of the feature flag
            percentage: Percentage rollout (0-100)
        """
        if not (0.0 <= percentage <= 100.0):
            raise FeatureFlagError(
                f"Percentage must be between 0 and 100, got {percentage}",
                flag_name=flag_name,
            )

        flag = self._flag_cache.get(flag_name)
        if flag:
            flag.percentage = percentage
            self._save_flags()
        else:
            raise FeatureFlagError(f"Feature flag '{flag_name}' not found")

    def add_user_group(self, flag_name: str, user_group: str) -> None:
        """Add user group to feature flag targeting."""
        flag = self._flag_cache.get(flag_name)
        if flag:
            if user_group not in flag.user_groups:
                flag.user_groups.append(user_group)
                self._save_flags()
        else:
            raise FeatureFlagError(f"Feature flag '{flag_name}' not found")

    def remove_user_group(self, flag_name: str, user_group: str) -> None:
        """Remove user group from feature flag targeting."""
        flag = self._flag_cache.get(flag_name)
        if flag:
            if user_group in flag.user_groups:
                flag.user_groups.remove(user_group)
                self._save_flags()
        else:
            raise FeatureFlagError(f"Feature flag '{flag_name}' not found")

    def get_flag_status(
        self,
        environment: Optional[Environment] = None,
        user_group: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all flags for given context.

        Args:
            environment: Environment to check
            user_group: User group to check

        Returns:
            Dictionary with flag names and their status information
        """
        status = {}
        
        for flag_name, flag in self._flag_cache.items():
            is_active = flag.is_active(
                environment=environment,
                user_group=user_group,
                current_time=datetime.utcnow(),
            )
            
            status[flag_name] = {
                "enabled": flag.enabled,
                "active": is_active,
                "description": flag.description,
                "environments": [env.value for env in flag.environments],
                "user_groups": flag.user_groups,
                "percentage": flag.percentage,
                "start_date": flag.start_date.isoformat() if flag.start_date else None,
                "end_date": flag.end_date.isoformat() if flag.end_date else None,
            }

        return status

    def reload_flags(self) -> None:
        """Reload feature flags from backend."""
        self._load_flags()