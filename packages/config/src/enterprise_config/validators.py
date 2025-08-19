"""
Configuration validation system.
"""

import re
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path

from pydantic import BaseModel, ValidationError as PydanticValidationError

from .exceptions import ValidationError


class ConfigValidator:
    """
    Configuration validation with support for:
    - Pydantic model validation
    - Custom validation rules
    - Type checking
    - Required field validation
    - Pattern matching
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize configuration validator.

        Args:
            schema_path: Path to validation schema file
        """
        self.schema_path = schema_path
        self.validation_rules: List[Dict[str, Any]] = []
        self.custom_validators: Dict[str, callable] = {}
        
        if schema_path:
            self._load_schema()

    def _load_schema(self) -> None:
        """Load validation schema from file."""
        if not self.schema_path or not Path(self.schema_path).exists():
            return

        try:
            import yaml
            with open(self.schema_path, 'r') as f:
                schema_data = yaml.safe_load(f)
                
            self.validation_rules = schema_data.get('rules', [])
            
        except Exception as e:
            print(f"Warning: Failed to load validation schema: {e}")

    def has_schema(self) -> bool:
        """Check if validation schema is loaded."""
        return bool(self.validation_rules or self.custom_validators)

    def add_rule(
        self,
        key_pattern: str,
        value_type: str,
        required: bool = False,
        validator_function: Optional[str] = None,
        error_message: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Add validation rule.

        Args:
            key_pattern: Regex pattern for configuration keys
            value_type: Expected value type (str, int, float, bool, list, dict)
            required: Whether the key is required
            validator_function: Name of custom validator function
            error_message: Custom error message
            **kwargs: Additional validation parameters
        """
        rule = {
            'key_pattern': key_pattern,
            'value_type': value_type,
            'required': required,
            'validator_function': validator_function,
            'error_message': error_message,
            **kwargs,
        }
        self.validation_rules.append(rule)

    def add_custom_validator(
        self,
        name: str,
        validator_func: callable,
    ) -> None:
        """
        Add custom validator function.

        Args:
            name: Name of the validator
            validator_func: Function that takes (key, value) and returns (is_valid, error_message)
        """
        self.custom_validators[name] = validator_func

    def validate(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration against rules.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Flatten configuration for validation
        flat_config = self._flatten_dict(config)
        
        # Check required fields
        required_keys = [
            rule['key_pattern'] for rule in self.validation_rules
            if rule.get('required', False)
        ]
        
        for required_pattern in required_keys:
            if not any(re.match(required_pattern, key) for key in flat_config.keys()):
                errors.append(f"Required configuration key matching '{required_pattern}' not found")

        # Validate each configuration key
        for key, value in flat_config.items():
            key_errors = self._validate_key(key, value)
            errors.extend(key_errors)

        if errors:
            raise ValidationError(
                "Configuration validation failed",
                validation_errors={"errors": errors}
            )

    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '.',
    ) -> Dict[str, Any]:
        """Flatten nested dictionary with dot notation keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _validate_key(self, key: str, value: Any) -> List[str]:
        """Validate single configuration key against rules."""
        errors = []
        
        for rule in self.validation_rules:
            if re.match(rule['key_pattern'], key):
                key_errors = self._apply_rule(key, value, rule)
                errors.extend(key_errors)
                
        return errors

    def _apply_rule(self, key: str, value: Any, rule: Dict[str, Any]) -> List[str]:
        """Apply single validation rule to key-value pair."""
        errors = []
        
        # Type validation
        expected_type = rule.get('value_type')
        if expected_type and not self._check_type(value, expected_type):
            error_msg = rule.get('error_message') or f"Key '{key}' must be of type {expected_type}"
            errors.append(error_msg)
            return errors  # Skip other validations if type is wrong

        # Range validation for numbers
        if expected_type in ['int', 'float'] and isinstance(value, (int, float)):
            min_val = rule.get('min_value')
            max_val = rule.get('max_value')
            
            if min_val is not None and value < min_val:
                errors.append(f"Key '{key}' value {value} is less than minimum {min_val}")
            if max_val is not None and value > max_val:
                errors.append(f"Key '{key}' value {value} is greater than maximum {max_val}")

        # Length validation for strings and lists
        if isinstance(value, (str, list)):
            min_length = rule.get('min_length')
            max_length = rule.get('max_length')
            
            if min_length is not None and len(value) < min_length:
                errors.append(f"Key '{key}' length {len(value)} is less than minimum {min_length}")
            if max_length is not None and len(value) > max_length:
                errors.append(f"Key '{key}' length {len(value)} is greater than maximum {max_length}")

        # Pattern validation for strings
        if isinstance(value, str):
            pattern = rule.get('pattern')
            if pattern and not re.match(pattern, value):
                errors.append(f"Key '{key}' value '{value}' does not match pattern '{pattern}'")

        # Allowed values validation
        allowed_values = rule.get('allowed_values')
        if allowed_values and value not in allowed_values:
            errors.append(f"Key '{key}' value '{value}' not in allowed values: {allowed_values}")

        # Custom validator function
        validator_function = rule.get('validator_function')
        if validator_function and validator_function in self.custom_validators:
            try:
                is_valid, error_message = self.custom_validators[validator_function](key, value)
                if not is_valid:
                    errors.append(error_message or f"Custom validation failed for key '{key}'")
            except Exception as e:
                errors.append(f"Custom validator error for key '{key}': {str(e)}")

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            'str': str,
            'int': int,
            'float': (int, float),  # Allow int for float
            'bool': bool,
            'list': list,
            'dict': dict,
            'any': object,
        }
        
        expected_python_type = type_map.get(expected_type.lower())
        if expected_python_type is None:
            return True  # Unknown type, skip validation
            
        return isinstance(value, expected_python_type)

    def validate_model(
        self,
        config: Dict[str, Any],
        model_class: Type[BaseModel],
        key_prefix: str = '',
    ) -> BaseModel:
        """
        Validate configuration against Pydantic model.

        Args:
            config: Configuration dictionary
            model_class: Pydantic model class
            key_prefix: Key prefix for nested validation

        Returns:
            Validated model instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Extract relevant config section if key_prefix provided
            if key_prefix:
                config_section = config
                for key in key_prefix.split('.'):
                    config_section = config_section.get(key, {})
            else:
                config_section = config

            return model_class(**config_section)
            
        except PydanticValidationError as e:
            error_details = {}
            for error in e.errors():
                field_path = '.'.join(str(loc) for loc in error['loc'])
                if key_prefix:
                    field_path = f"{key_prefix}.{field_path}"
                error_details[field_path] = error['msg']
                
            raise ValidationError(
                f"Model validation failed for {model_class.__name__}",
                key=key_prefix,
                validation_errors=error_details,
            )

    def create_schema_template(self) -> Dict[str, Any]:
        """Create validation schema template."""
        return {
            'version': '1.0',
            'description': 'Configuration validation schema',
            'rules': [
                {
                    'key_pattern': r'^app\.name$',
                    'value_type': 'str',
                    'required': True,
                    'min_length': 1,
                    'max_length': 100,
                    'error_message': 'Application name is required and must be 1-100 characters'
                },
                {
                    'key_pattern': r'^app\.debug$',
                    'value_type': 'bool',
                    'required': False,
                    'error_message': 'Debug flag must be boolean'
                },
                {
                    'key_pattern': r'^database\.port$',
                    'value_type': 'int',
                    'required': False,
                    'min_value': 1,
                    'max_value': 65535,
                    'error_message': 'Database port must be between 1 and 65535'
                },
                {
                    'key_pattern': r'^database\.url$',
                    'value_type': 'str',
                    'required': True,
                    'pattern': r'^(postgresql|mysql|sqlite)://',
                    'error_message': 'Database URL must start with postgresql://, mysql://, or sqlite://'
                },
            ]
        }

    def export_schema(self, format: str = 'yaml') -> str:
        """
        Export validation schema in specified format.

        Args:
            format: Export format (yaml, json)

        Returns:
            Formatted schema string
        """
        schema_data = {
            'version': '1.0',
            'rules': self.validation_rules,
        }
        
        if format.lower() == 'json':
            import json
            return json.dumps(schema_data, indent=2)
        elif format.lower() == 'yaml':
            import yaml
            return yaml.dump(schema_data, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def validate_partial(
        self,
        config: Dict[str, Any],
        keys: List[str],
    ) -> List[str]:
        """
        Validate only specific configuration keys.

        Args:
            config: Configuration dictionary
            keys: List of keys to validate

        Returns:
            List of validation errors
        """
        errors = []
        flat_config = self._flatten_dict(config)
        
        for key in keys:
            if key in flat_config:
                key_errors = self._validate_key(key, flat_config[key])
                errors.extend(key_errors)
            else:
                # Check if key is required
                for rule in self.validation_rules:
                    if rule.get('required', False) and re.match(rule['key_pattern'], key):
                        errors.append(f"Required key '{key}' not found")
                        
        return errors