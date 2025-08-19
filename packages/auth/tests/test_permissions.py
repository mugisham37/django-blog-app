"""
Tests for role-based access control (RBAC) system.
"""

import pytest
from auth_package.permissions import (
    Permission, Role, RoleRegistry, RoleBasedPermission,
    PermissionAction, PermissionScope, default_role_registry
)


class TestPermission:
    """Test Permission class."""
    
    def test_permission_creation(self):
        """Test permission creation."""
        permission = Permission(
            name="user.read",
            action=PermissionAction.READ,
            resource="user",
            scope=PermissionScope.GLOBAL,
            description="Read user information"
        )
        
        assert permission.name == "user.read"
        assert per