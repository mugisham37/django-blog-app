"""
Command-line interface for configuration management.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .manager import ConfigManager
from .models import Environment
from .exceptions import ConfigurationError


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="enterprise-config",
        description="Enterprise Configuration Management CLI",
    )

    parser.add_argument(
        "--config-path",
        default="config/",
        help="Path to configuration directory (default: config/)",
    )
    
    parser.add_argument(
        "--environment",
        choices=[env.value for env in Environment],
        default=Environment.DEVELOPMENT.value,
        help="Target environment (default: development)",
    )
    
    parser.add_argument(
        "--backend",
        choices=["file", "redis", "aws_ssm", "vault"],
        default="file",
        help="Configuration backend (default: file)",
    )
    
    parser.add_argument(
        "--format",
        choices=["yaml", "json", "toml"],
        default="yaml",
        help="Configuration file format (default: yaml)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument(
        "--schema",
        help="Path to validation schema file",
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Show configuration")
    show_parser.add_argument(
        "--key",
        help="Specific configuration key to show",
    )
    show_parser.add_argument(
        "--output-format",
        choices=["yaml", "json", "table"],
        default="yaml",
        help="Output format (default: yaml)",
    )

    # Set command
    set_parser = subparsers.add_parser("set", help="Set configuration value")
    set_parser.add_argument("key", help="Configuration key")
    set_parser.add_argument("value", help="Configuration value")
    set_parser.add_argument(
        "--type",
        choices=["str", "int", "float", "bool", "json"],
        default="str",
        help="Value type (default: str)",
    )

    # Get command
    get_parser = subparsers.add_parser("get", help="Get configuration value")
    get_parser.add_argument("key", help="Configuration key")
    get_parser.add_argument(
        "--default",
        help="Default value if key not found",
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete configuration key")
    delete_parser.add_argument("key", help="Configuration key to delete")

    # Feature flag commands
    ff_parser = subparsers.add_parser("feature-flag", help="Feature flag management")
    ff_subparsers = ff_parser.add_subparsers(dest="ff_command", help="Feature flag commands")

    # Feature flag set
    ff_set_parser = ff_subparsers.add_parser("set", help="Set feature flag")
    ff_set_parser.add_argument("name", help="Feature flag name")
    ff_set_parser.add_argument("enabled", type=bool_arg, help="Enable/disable flag")
    ff_set_parser.add_argument("--description", help="Flag description")
    ff_set_parser.add_argument("--percentage", type=float, help="Rollout percentage")

    # Feature flag get
    ff_get_parser = ff_subparsers.add_parser("get", help="Get feature flag status")
    ff_get_parser.add_argument("name", help="Feature flag name")
    ff_get_parser.add_argument("--user-group", help="User group for evaluation")

    # Feature flag list
    ff_list_parser = ff_subparsers.add_parser("list", help="List feature flags")

    # Secret commands
    secret_parser = subparsers.add_parser("secret", help="Secret management")
    secret_subparsers = secret_parser.add_subparsers(dest="secret_command", help="Secret commands")

    # Secret set
    secret_set_parser = secret_subparsers.add_parser("set", help="Set secret")
    secret_set_parser.add_argument("name", help="Secret name")
    secret_set_parser.add_argument("value", help="Secret value")

    # Secret get
    secret_get_parser = secret_subparsers.add_parser("get", help="Get secret")
    secret_get_parser.add_argument("name", help="Secret name")

    # Secret list
    secret_list_parser = secret_subparsers.add_parser("list", help="List secrets")
    secret_list_parser.add_argument(
        "--show-values",
        action="store_true",
        help="Show decrypted values (dangerous!)",
    )

    # Export command
    export_parser = subparsers.add_parser("export", help="Export configuration")
    export_parser.add_argument(
        "--output",
        help="Output file path (default: stdout)",
    )
    export_parser.add_argument(
        "--output-format",
        choices=["yaml", "json", "env"],
        default="yaml",
        help="Export format (default: yaml)",
    )

    # Import command
    import_parser = subparsers.add_parser("import", help="Import configuration")
    import_parser.add_argument("file", help="Configuration file to import")
    import_parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing configuration",
    )

    return parser


def bool_arg(value: str) -> bool:
    """Parse boolean argument."""
    if value.lower() in ("true", "1", "yes", "on"):
        return True
    elif value.lower() in ("false", "0", "no", "off"):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected, got: {value}")


def create_config_manager(args) -> ConfigManager:
    """Create configuration manager from CLI arguments."""
    backend_kwargs = {}
    
    if args.backend == "file":
        backend_kwargs["file_format"] = args.format
    
    return ConfigManager(
        environment=args.environment,
        backend=args.backend,
        config_path=args.config_path,
        **backend_kwargs,
    )


def handle_validate(args) -> int:
    """Handle validate command."""
    try:
        config = create_config_manager(args)
        errors = config.validate_configuration()
        
        if errors:
            print("Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print("Configuration validation passed")
            return 0
            
    except Exception as e:
        print(f"Error validating configuration: {e}")
        return 1


def handle_show(args) -> int:
    """Handle show command."""
    try:
        config = create_config_manager(args)
        
        if args.key:
            value = config.get(args.key)
            if value is None:
                print(f"Configuration key '{args.key}' not found")
                return 1
            
            if args.output_format == "json":
                print(json.dumps(value, indent=2, default=str))
            else:
                print(value)
        else:
            all_config = config.get_all()
            
            if args.output_format == "json":
                print(json.dumps(all_config, indent=2, default=str))
            elif args.output_format == "yaml":
                import yaml
                print(yaml.dump(all_config, default_flow_style=False))
            elif args.output_format == "table":
                print_config_table(all_config)
                
        return 0
        
    except Exception as e:
        print(f"Error showing configuration: {e}")
        return 1


def handle_set(args) -> int:
    """Handle set command."""
    try:
        config = create_config_manager(args)
        
        # Convert value to appropriate type
        value = convert_value(args.value, args.type)
        
        config.set(args.key, value)
        print(f"Set {args.key} = {value}")
        return 0
        
    except Exception as e:
        print(f"Error setting configuration: {e}")
        return 1


def handle_get(args) -> int:
    """Handle get command."""
    try:
        config = create_config_manager(args)
        value = config.get(args.key, args.default)
        
        if value is None:
            print(f"Configuration key '{args.key}' not found")
            return 1
            
        print(value)
        return 0
        
    except Exception as e:
        print(f"Error getting configuration: {e}")
        return 1


def handle_delete(args) -> int:
    """Handle delete command."""
    try:
        config = create_config_manager(args)
        
        if config.delete(args.key):
            print(f"Deleted configuration key: {args.key}")
            return 0
        else:
            print(f"Configuration key '{args.key}' not found")
            return 1
            
    except Exception as e:
        print(f"Error deleting configuration: {e}")
        return 1


def handle_feature_flag(args) -> int:
    """Handle feature flag commands."""
    try:
        config = create_config_manager(args)
        
        if args.ff_command == "set":
            config.set_feature_flag(
                flag_name=args.name,
                enabled=args.enabled,
                description=args.description,
                percentage=args.percentage,
            )
            print(f"Set feature flag '{args.name}' = {args.enabled}")
            
        elif args.ff_command == "get":
            enabled = config.feature_flag(
                flag_name=args.name,
                user_group=args.user_group,
            )
            print(f"Feature flag '{args.name}': {enabled}")
            
        elif args.ff_command == "list":
            flags = config.feature_flags.list_flags(config.environment)
            if flags:
                print("Feature flags:")
                for name, flag in flags.items():
                    status = "enabled" if flag.enabled else "disabled"
                    print(f"  {name}: {status}")
                    if flag.description:
                        print(f"    Description: {flag.description}")
            else:
                print("No feature flags found")
                
        return 0
        
    except Exception as e:
        print(f"Error with feature flag: {e}")
        return 1


def handle_secret(args) -> int:
    """Handle secret commands."""
    try:
        config = create_config_manager(args)
        
        if args.secret_command == "set":
            config.set_secret(args.name, args.value)
            print(f"Set secret: {args.name}")
            
        elif args.secret_command == "get":
            try:
                value = config.get_secret(args.name)
                print(value)
            except Exception:
                print(f"Secret '{args.name}' not found")
                return 1
                
        elif args.secret_command == "list":
            secrets = config.secrets.list_secrets(
                environment=config.environment,
                include_values=args.show_values,
            )
            if secrets:
                print("Secrets:")
                for name, info in secrets.items():
                    print(f"  {name}:")
                    if args.show_values and "value" in info:
                        print(f"    Value: {info['value']}")
                    print(f"    Created: {info['created_at']}")
                    print(f"    Updated: {info['updated_at']}")
            else:
                print("No secrets found")
                
        return 0
        
    except Exception as e:
        print(f"Error with secret: {e}")
        return 1


def handle_export(args) -> int:
    """Handle export command."""
    try:
        config = create_config_manager(args)
        exported = config.export_config(args.output_format)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(exported)
            print(f"Configuration exported to: {args.output}")
        else:
            print(exported)
            
        return 0
        
    except Exception as e:
        print(f"Error exporting configuration: {e}")
        return 1


def handle_import(args) -> int:
    """Handle import command."""
    try:
        config = create_config_manager(args)
        
        if not Path(args.file).exists():
            print(f"Import file not found: {args.file}")
            return 1
            
        # Load import data
        with open(args.file, 'r') as f:
            if args.file.endswith('.json'):
                import_data = json.load(f)
            else:
                import yaml
                import_data = yaml.safe_load(f)
        
        if args.merge:
            # Merge with existing configuration
            current_config = config.get_all()
            merged_config = {**current_config, **import_data}
            
            # Save merged configuration
            for key, value in merged_config.items():
                config.set(key, value)
        else:
            # Replace configuration
            for key, value in import_data.items():
                config.set(key, value)
                
        print(f"Configuration imported from: {args.file}")
        return 0
        
    except Exception as e:
        print(f"Error importing configuration: {e}")
        return 1


def convert_value(value: str, value_type: str) -> Any:
    """Convert string value to specified type."""
    if value_type == "str":
        return value
    elif value_type == "int":
        return int(value)
    elif value_type == "float":
        return float(value)
    elif value_type == "bool":
        return bool_arg(value)
    elif value_type == "json":
        return json.loads(value)
    else:
        raise ValueError(f"Unsupported value type: {value_type}")


def print_config_table(config: Dict[str, Any], prefix: str = "") -> None:
    """Print configuration as a table."""
    for key, value in config.items():
        full_key = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            print_config_table(value, full_key)
        else:
            print(f"{full_key:<40} {str(value):<20} {type(value).__name__}")


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "validate":
            return handle_validate(args)
        elif args.command == "show":
            return handle_show(args)
        elif args.command == "set":
            return handle_set(args)
        elif args.command == "get":
            return handle_get(args)
        elif args.command == "delete":
            return handle_delete(args)
        elif args.command == "feature-flag":
            return handle_feature_flag(args)
        elif args.command == "secret":
            return handle_secret(args)
        elif args.command == "export":
            return handle_export(args)
        elif args.command == "import":
            return handle_import(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())