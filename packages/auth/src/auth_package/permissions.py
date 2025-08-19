"""
Role-based access control (RBAC) system with permissions and roles.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Set, Any, Optional, Union
from enum import Enum
import json


class PermissionAction(Enum):
    """Standard permission actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


class PermissionScope(Enum):
    """Permission scopes."""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PROJECT = "project"
    RESOURCE = "resource"
    OWNER = "owner"


@dataclass
class Permission:
    """
    Individual permission definition.
    
    Represents a specific action that can be performed on a resource.
    """
    name: str
    action: PermissionAction
    resource: str
    scope: PermissionScope = PermissionScope.GLOBAL
    conditions: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.action.value} {self.resource}"
    
    def __str__(self) -> str:
        return f"{self.resource}:{self.action.value}"
    
    def __hash__(self) -> int:
        return hash((self.name, self.action, self.resource, self.scope))
    
    def matches(self, resource: str, action: PermissionAction, context: Dict[str, Any] = None) -> bool:
        """
        Check if this permission matches the requested resource and action.
        
        Args:
            resource: Resource being accessed
            action: Action being performed
            context: Additional context for condition evaluation
            
        Returns:
            True if permission matches
        """
        # Check basic resource and action match
        if self.resource != resource and self.resource != "*":
            return False
        
        if self.action != action and self.action != PermissionAction.MANAGE:
            return False
        
        # Evaluate conditions if present
        if self.conditions and context:
            return self._evaluate_conditions(context)
        
        return True
    
    def _evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate permission conditions against context.
        
        Args:
            context: Context data for evaluation
            
        Returns:
            True if all conditions are met
        """
        for condition_key, condition_value in self.conditions.items():
            if condition_key not in context:
                return False
            
            context_value = context[condition_key]
            
            # Handle different condition types
            if isinstance(condition_value, dict):
                # Complex condition (e.g., {"operator": "in", "values": [1, 2, 3]})
                operator = condition_value.get("operator", "eq")
                values = condition_value.get("values", condition_value.get("value"))
                
                if operator == "eq" and context_value != values:
                    return False
                elif operator == "in" and context_value not in values:
                    return False
                elif operator == "gt" and context_value <= values:
                    return False
                elif operator == "lt" and context_value >= values:
                    return False
            else:
                # Simple equality check
                if context_value != condition_value:
                    return False
        
        return True


@dataclass
class Role:
    """
    Role definition with permissions and hierarchy.
    
    Represents a collection of permissions that can be assigned to users.
    """
    name: str
    permissions: Set[Permission] = field(default_factory=set)
    parent_roles: Set[str] = field(default_factory=set)
    description: str = ""
    is_system_role: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_permission(self, permission: Permission):
        """Add permission to role."""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission):
        """Remove permission from role."""
        self.permissions.discard(permission)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission."""
        return permission in self.permissions
    
    def add_parent_role(self, role_name: str):
        """Add parent role for inheritance."""
        self.parent_roles.add(role_name)
    
    def remove_parent_role(self, role_name: str):
        """Remove parent role."""
        self.parent_roles.discard(role_name)
    
    def get_all_permissions(self, role_registry: 'RoleRegistry' = None) -> Set[Permission]:
        """
        Get all permissions including inherited ones.
        
        Args:
            role_registry: Registry to resolve parent roles
            
        Returns:
            Set of all permissions
        """
        all_permissions = self.permissions.copy()
        
        if role_registry:
            for parent_role_name in self.parent_roles:
                parent_role = role_registry.get_role(parent_role_name)
                if parent_role:
                    all_permissions.update(parent_role.get_all_permissions(role_registry))
        
        return all_permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            "name": self.name,
            "permissions": [
                {
                    "name": p.name,
                    "action": p.action.value,
                    "resource": p.resource,
                    "scope": p.scope.value,
                    "conditions": p.conditions,
                    "description": p.description
                }
                for p in self.permissions
            ],
            "parent_roles": list(self.parent_roles),
            "description": self.description,
            "is_system_role": self.is_system_role,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Create role from dictionary."""
        permissions = set()
        for perm_data in data.get("permissions", []):
            permission = Permission(
                name=perm_data["name"],
                action=PermissionAction(perm_data["action"]),
                resource=perm_data["resource"],
                scope=PermissionScope(perm_data["scope"]),
                conditions=perm_data.get("conditions", {}),
                description=perm_data.get("description", "")
            )
            permissions.add(permission)
        
        return cls(
            name=data["name"],
            permissions=permissions,
            parent_roles=set(data.get("parent_roles", [])),
            description=data.get("description", ""),
            is_system_role=data.get("is_system_role", False),
            metadata=data.get("metadata", {})
        )


class RoleRegistry:
    """
    Registry for managing roles and permissions.
    
    Provides centralized role management with inheritance support.
    """
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.permissions: Dict[str, Permission] = {}
        self._setup_default_roles()
    
    def register_permission(self, permission: Permission):
        """Register a permission."""
        self.permissions[permission.name] = permission
    
    def get_permission(self, name: str) -> Optional[Permission]:
        """Get permission by name."""
        return self.permissions.get(name)
    
    def register_role(self, role: Role):
        """Register a role."""
        self.roles[role.name] = role
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self.roles.get(name)
    
    def create_role(self, name: str, description: str = "", parent_roles: List[str] = None) -> Role:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            parent_roles: List of parent role names
            
        Returns:
            Created role
        """
        role = Role(
            name=name,
            description=description,
            parent_roles=set(parent_roles or [])
        )
        
        self.register_role(role)
        return role
    
    def delete_role(self, name: str) -> bool:
        """
        Delete a role.
        
        Args:
            name: Role name to delete
            
        Returns:
            True if role was deleted
        """
        if name in self.roles:
            role = self.roles[name]
            if role.is_system_role:
                raise ValueError(f"Cannot delete system role: {name}")
            
            del self.roles[name]
            return True
        
        return False
    
    def assign_permission_to_role(self, role_name: str, permission_name: str):
        """Assign permission to role."""
        role = self.get_role(role_name)
        permission = self.get_permission(permission_name)
        
        if role and permission:
            role.add_permission(permission)
    
    def remove_permission_from_role(self, role_name: str, permission_name: str):
        """Remove permission from role."""
        role = self.get_role(role_name)
        permission = self.get_permission(permission_name)
        
        if role and permission:
            role.remove_permission(permission)
    
    def get_role_permissions(self, role_name: str) -> Set[Permission]:
        """Get all permissions for a role including inherited ones."""
        role = self.get_role(role_name)
        if role:
            return role.get_all_permissions(self)
        return set()
    
    def _setup_default_roles(self):
        """Setup default system roles."""
        # Default permissions
        default_permissions = [
            Permission("user.read", PermissionAction.READ, "user", description="Read user information"),
            Permission("user.update", PermissionAction.UPDATE, "user", description="Update user information"),
            Permission("user.create", PermissionAction.CREATE, "user", description="Create new users"),
            Permission("user.delete", PermissionAction.DELETE, "user", description="Delete users"),
            Permission("user.manage", PermissionAction.MANAGE, "user", description="Full user management"),
            
            Permission("blog.read", PermissionAction.READ, "blog", description="Read blog posts"),
            Permission("blog.create", PermissionAction.CREATE, "blog", description="Create blog posts"),
            Permission("blog.update", PermissionAction.UPDATE, "blog", description="Update blog posts"),
            Permission("blog.delete", PermissionAction.DELETE, "blog", description="Delete blog posts"),
            Permission("blog.manage", PermissionAction.MANAGE, "blog", description="Full blog management"),
            
            Permission("comment.read", PermissionAction.READ, "comment", description="Read comments"),
            Permission("comment.create", PermissionAction.CREATE, "comment", description="Create comments"),
            Permission("comment.update", PermissionAction.UPDATE, "comment", description="Update comments"),
            Permission("comment.delete", PermissionAction.DELETE, "comment", description="Delete comments"),
            
            Permission("system.manage", PermissionAction.MANAGE, "system", description="System administration"),
        ]
        
        for permission in default_permissions:
            self.register_permission(permission)
        
        # Default roles
        guest_role = Role("guest", description="Guest user with read-only access", is_system_role=True)
        guest_role.add_permission(self.get_permission("blog.read"))
        guest_role.add_permission(self.get_permission("comment.read"))
        
        user_role = Role("user", description="Regular user", is_system_role=True)
        user_role.add_permission(self.get_permission("user.read"))
        user_role.add_permission(self.get_permission("user.update"))
        user_role.add_permission(self.get_permission("blog.read"))
        user_role.add_permission(self.get_permission("blog.create"))
        user_role.add_permission(self.get_permission("comment.read"))
        user_role.add_permission(self.get_permission("comment.create"))
        
        moderator_role = Role("moderator", description="Content moderator", is_system_role=True)
        moderator_role.parent_roles.add("user")
        moderator_role.add_permission(self.get_permission("blog.update"))
        moderator_role.add_permission(self.get_permission("blog.delete"))
        moderator_role.add_permission(self.get_permission("comment.update"))
        moderator_role.add_permission(self.get_permission("comment.delete"))
        
        admin_role = Role("admin", description="System administrator", is_system_role=True)
        admin_role.parent_roles.add("moderator")
        admin_role.add_permission(self.get_permission("user.manage"))
        admin_role.add_permission(self.get_permission("blog.manage"))
        admin_role.add_permission(self.get_permission("system.manage"))
        
        self.register_role(guest_role)
        self.register_role(user_role)
        self.register_role(moderator_role)
        self.register_role(admin_role)


class RoleBasedPermission:
    """
    Role-based permission checker.
    
    Provides permission checking functionality for users with roles.
    """
    
    def __init__(self, role_registry: RoleRegistry = None):
        self.role_registry = role_registry or RoleRegistry()
    
    def check_permission(self, 
                        user_roles: List[str], 
                        resource: str, 
                        action: PermissionAction,
                        context: Dict[str, Any] = None) -> bool:
        """
        Check if user has permission to perform action on resource.
        
        Args:
            user_roles: List of user's role names
            resource: Resource being accessed
            action: Action being performed
            context: Additional context for permission evaluation
            
        Returns:
            True if user has permission
        """
        for role_name in user_roles:
            role_permissions = self.role_registry.get_role_permissions(role_name)
            
            for permission in role_permissions:
                if permission.matches(resource, action, context):
                    return True
        
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[Permission]:
        """
        Get all permissions for user based on their roles.
        
        Args:
            user_roles: List of user's role names
            
        Returns:
            Set of all user permissions
        """
        all_permissions = set()
        
        for role_name in user_roles:
            role_permissions = self.role_registry.get_role_permissions(role_name)
            all_permissions.update(role_permissions)
        
        return all_permissions
    
    def can_access_resource(self, 
                           user_roles: List[str], 
                           resource: str, 
                           context: Dict[str, Any] = None) -> Dict[PermissionAction, bool]:
        """
        Check what actions user can perform on a resource.
        
        Args:
            user_roles: List of user's role names
            resource: Resource being checked
            context: Additional context
            
        Returns:
            Dictionary mapping actions to permission status
        """
        result = {}
        
        for action in PermissionAction:
            result[action] = self.check_permission(user_roles, resource, action, context)
        
        return result
    
    def filter_resources_by_permission(self, 
                                     user_roles: List[str], 
                                     resources: List[Dict[str, Any]], 
                                     action: PermissionAction,
                                     resource_type: str) -> List[Dict[str, Any]]:
        """
        Filter resources based on user permissions.
        
        Args:
            user_roles: List of user's role names
            resources: List of resource objects
            action: Required action permission
            resource_type: Type of resource
            
        Returns:
            Filtered list of resources user can access
        """
        filtered_resources = []
        
        for resource in resources:
            context = {"resource_id": resource.get("id"), "owner_id": resource.get("owner_id")}
            
            if self.check_permission(user_roles, resource_type, action, context):
                filtered_resources.append(resource)
        
        return filtered_resources


# Global role registry instance
default_role_registry = RoleRegistry()
default_permission_checker = RoleBasedPermission(default_role_registry)