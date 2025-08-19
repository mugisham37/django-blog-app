#!/usr/bin/env python3
"""
Command-line interface for the authentication package.

Provides utilities for managing users, roles, and authentication
components from the command line.
"""

import argparse
import sys
import json
import getpass
from typing import Dict, Any
from datetime import datetime

from .models import User, UserStatus, AuthProvider, default_user_repository
from .permissions import default_role_registry, Permission, PermissionAction, PermissionScope
from .security import PasswordHasher
from .strategies import JWTStrategy, JWTConfig
from .mfa import TOTPProvider


def create_user_command(args):
    """Create a new user."""
    password_hasher = PasswordHasher()
    
    # Get password securely
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("Error: Passwords do not match")
            return 1
    
    # Validate password
    validation_result = password_hasher.validate_password_strength(
        password, 
        {"username": args.username, "email": args.email}
    )
    
    if not validation_result["valid"]:
        print("Error: Password validation failed:")
        for error in validation_result["errors"]:
            print(f"  - {error}")
        return 1
    
    # Hash password
    password_hash = password_hasher.hash_password(password)
    
    # Create user
    user = User(
        id=args.user_id or args.username,
        username=args.username,
        email=args.email,
        status=UserStatus.ACTIVE if args.active else UserStatus.PENDING_VERIFICATION,
        auth_provider=AuthProvider.LOCAL
    )
    
    user.security.password_hash = password_hash
    
    # Set profile information
    if args.first_name:
        user.profile.first_name = args.first_name
    if args.last_name:
        user.profile.last_name = args.last_name
    
    # Add roles
    if args.roles:
        for role_name in args.roles:
            if default_role_registry.get_role(role_name):
                user.add_role(role_name)
            else:
                print(f"Warning: Role '{role_name}' not found")
    
    try:
        default_user_repository.create_user(user)
        print(f"User '{args.username}' created successfully")
        
        if args.json:
            print(json.dumps(user.to_dict(), indent=2))
        
        return 0
    except ValueError as e:
        print(f"Error: {e}")
        return 1


def list_users_command(args):
    """List users."""
    status_filter = None
    if args.status:
        try:
            status_filter = UserStatus(args.status)
        except ValueError:
            print(f"Error: Invalid status '{args.status}'")
            return 1
    
    users = default_user_repository.list_users(
        status=status_filter,
        limit=args.limit,
        offset=args.offset
    )
    
    if args.json:
        users_data = [user.to_dict() for user in users]
        print(json.dumps(users_data, indent=2))
    else:
        print(f"{'ID':<20} {'Username':<20} {'Email':<30} {'Status':<15} {'Roles'}")
        print("-" * 100)
        
        for user in users:
            roles_str = ", ".join(user.roles) if user.roles else "None"
            print(f"{user.id:<20} {user.username:<20} {user.email:<30} {user.status.value:<15} {roles_str}")
    
    return 0


def create_role_command(args):
    """Create a new role."""
    role = default_role_registry.create_role(
        name=args.name,
        description=args.description or "",
        parent_roles=args.parent_roles or []
    )
    
    # Add permissions
    if args.permissions:
        for perm_str in args.permissions:
            try:
                # Parse permission string (format: resource:action:scope)
                parts = perm_str.split(":")
                if len(parts) < 2:
                    print(f"Warning: Invalid permission format '{perm_str}'. Use resource:action[:scope]")
                    continue
                
                resource = parts[0]
                action = PermissionAction(parts[1])
                scope = PermissionScope(parts[2]) if len(parts) > 2 else PermissionScope.GLOBAL
                
                permission = Permission(
                    name=f"{resource}.{action.value}",
                    action=action,
                    resource=resource,
                    scope=scope
                )
                
                default_role_registry.register_permission(permission)
                role.add_permission(permission)
                
            except ValueError as e:
                print(f"Warning: Invalid permission '{perm_str}': {e}")
    
    print(f"Role '{args.name}' created successfully")
    
    if args.json:
        print(json.dumps(role.to_dict(), indent=2))
    
    return 0


def list_roles_command(args):
    """List roles."""
    roles = list(default_role_registry.roles.values())
    
    if args.json:
        roles_data = [role.to_dict() for role in roles]
        print(json.dumps(roles_data, indent=2))
    else:
        print(f"{'Name':<20} {'Description':<40} {'Permissions':<10} {'Parents'}")
        print("-" * 80)
        
        for role in roles:
            parents_str = ", ".join(role.parent_roles) if role.parent_roles else "None"
            perm_count = len(role.permissions)
            description = role.description[:37] + "..." if len(role.description) > 40 else role.description
            
            print(f"{role.name:<20} {description:<40} {perm_count:<10} {parents_str}")
    
    return 0


def assign_role_command(args):
    """Assign role to user."""
    user = default_user_repository.get_user_by_username(args.username)
    if not user:
        print(f"Error: User '{args.username}' not found")
        return 1
    
    role = default_role_registry.get_role(args.role)
    if not role:
        print(f"Error: Role '{args.role}' not found")
        return 1
    
    user.add_role(args.role)
    default_user_repository.update_user(user)
    
    print(f"Role '{args.role}' assigned to user '{args.username}'")
    return 0


def generate_token_command(args):
    """Generate JWT token for user."""
    user = default_user_repository.get_user_by_username(args.username)
    if not user:
        print(f"Error: User '{args.username}' not found")
        return 1
    
    if not user.is_active:
        print(f"Error: User '{args.username}' is not active")
        return 1
    
    # Create JWT strategy
    jwt_config = JWTConfig(
        secret_key=args.secret_key or "default-secret-key",
        issuer=args.issuer or "auth-cli",
        audience=args.audience or "api"
    )
    jwt_strategy = JWTStrategy(jwt_config)
    
    # Generate tokens
    user_data = {
        "email": user.email,
        "roles": list(user.roles)
    }
    
    tokens = jwt_strategy.generate_tokens(user.id, user_data)
    
    if args.json:
        token_data = {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_in": tokens.expires_in,
            "token_type": tokens.token_type
        }
        print(json.dumps(token_data, indent=2))
    else:
        print(f"Access Token: {tokens.access_token}")
        print(f"Refresh Token: {tokens.refresh_token}")
        print(f"Expires In: {tokens.expires_in} seconds")
    
    return 0


def setup_totp_command(args):
    """Setup TOTP for user."""
    user = default_user_repository.get_user_by_username(args.username)
    if not user:
        print(f"Error: User '{args.username}' not found")
        return 1
    
    totp_provider = TOTPProvider({
        "issuer_name": args.issuer or "Auth CLI"
    })
    
    setup_data = totp_provider.setup_user_totp(user.id, user.email)
    
    if args.json:
        print(json.dumps(setup_data, indent=2))
    else:
        print(f"TOTP Setup for {user.username}:")
        print(f"Secret Key: {setup_data['secret']}")
        print(f"QR Code (base64): {setup_data['qr_code'][:50]}...")
        print("\nSetup Instructions:")
        for i, instruction in enumerate(setup_data['setup_instructions'], 1):
            print(f"{i}. {instruction}")
    
    return 0


def validate_password_command(args):
    """Validate password strength."""
    password_hasher = PasswordHasher()
    
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Enter password to validate: ")
    
    user_info = {}
    if args.username:
        user_info["username"] = args.username
    if args.email:
        user_info["email"] = args.email
    
    result = password_hasher.validate_password_strength(password, user_info)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Password Strength: {result['strength']} (Score: {result['score']}/5)")
        print(f"Valid: {result['valid']}")
        
        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
    
    return 0 if result['valid'] else 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Authentication package CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create user command
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user")
    create_user_parser.add_argument("username", help="Username")
    create_user_parser.add_argument("email", help="Email address")
    create_user_parser.add_argument("--user-id", help="User ID (defaults to username)")
    create_user_parser.add_argument("--password", help="Password (will prompt if not provided)")
    create_user_parser.add_argument("--first-name", help="First name")
    create_user_parser.add_argument("--last-name", help="Last name")
    create_user_parser.add_argument("--roles", nargs="*", help="Roles to assign")
    create_user_parser.add_argument("--active", action="store_true", help="Create as active user")
    
    # List users command
    list_users_parser = subparsers.add_parser("list-users", help="List users")
    list_users_parser.add_argument("--status", help="Filter by status")
    list_users_parser.add_argument("--limit", type=int, default=100, help="Limit results")
    list_users_parser.add_argument("--offset", type=int, default=0, help="Offset results")
    
    # Create role command
    create_role_parser = subparsers.add_parser("create-role", help="Create a new role")
    create_role_parser.add_argument("name", help="Role name")
    create_role_parser.add_argument("--description", help="Role description")
    create_role_parser.add_argument("--permissions", nargs="*", help="Permissions (resource:action[:scope])")
    create_role_parser.add_argument("--parent-roles", nargs="*", help="Parent roles")
    
    # List roles command
    list_roles_parser = subparsers.add_parser("list-roles", help="List roles")
    
    # Assign role command
    assign_role_parser = subparsers.add_parser("assign-role", help="Assign role to user")
    assign_role_parser.add_argument("username", help="Username")
    assign_role_parser.add_argument("role", help="Role name")
    
    # Generate token command
    generate_token_parser = subparsers.add_parser("generate-token", help="Generate JWT token")
    generate_token_parser.add_argument("username", help="Username")
    generate_token_parser.add_argument("--secret-key", help="JWT secret key")
    generate_token_parser.add_argument("--issuer", help="JWT issuer")
    generate_token_parser.add_argument("--audience", help="JWT audience")
    
    # Setup TOTP command
    setup_totp_parser = subparsers.add_parser("setup-totp", help="Setup TOTP for user")
    setup_totp_parser.add_argument("username", help="Username")
    setup_totp_parser.add_argument("--issuer", help="TOTP issuer name")
    
    # Validate password command
    validate_password_parser = subparsers.add_parser("validate-password", help="Validate password strength")
    validate_password_parser.add_argument("--password", help="Password to validate")
    validate_password_parser.add_argument("--username", help="Username for validation context")
    validate_password_parser.add_argument("--email", help="Email for validation context")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Command dispatch
    commands = {
        "create-user": create_user_command,
        "list-users": list_users_command,
        "create-role": create_role_command,
        "list-roles": list_roles_command,
        "assign-role": assign_role_command,
        "generate-token": generate_token_command,
        "setup-totp": setup_totp_command,
        "validate-password": validate_password_command,
    }
    
    command_func = commands.get(args.command)
    if command_func:
        try:
            return command_func(args)
        except KeyboardInterrupt:
            print("\nOperation cancelled")
            return 1
        except Exception as e:
            print(f"Error: {e}")
            return 1
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())