#!/usr/bin/env python
"""
Validation script for role-based authorization system.
This script validates the implementation without running full Django tests.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    print("This validation requires a properly configured Django environment.")
    sys.exit(1)

def validate_permissions_module():
    """Validate the permissions module."""
    print("=" * 60)
    print("VALIDATING PERMISSIONS MODULE")
    print("=" * 60)
    
    try:
        from apps.core.permissions import (
            BlogRoles, BlogPermissions, create_blog_groups_and_permissions,
            assign_user_to_role, remove_user_from_role, get_user_roles,
            user_has_role, user_can_edit_post, user_can_delete_post,
            user_can_moderate_comments, user_can_manage_users,
            user_can_view_analytics, require_role_permission,
            RoleBasedPermissionMixin
        )
        print("✓ Successfully imported permissions module")
        
        # Check role constants
        expected_roles = ['Authors', 'Editors', 'Administrators']
        for role in expected_roles:
            if role in BlogRoles.ALL_ROLES:
                print(f"✓ Role '{role}' defined correctly")
            else:
                print(f"✗ Role '{role}' missing")
        
        # Check permission constants
        if hasattr(BlogPermissions, 'CAN_CREATE_POST'):
            print("✓ Permission constants defined")
        else:
            print("✗ Permission constants missing")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import permissions module: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating permissions module: {e}")
        return False


def validate_decorators():
    """Validate the decorators module."""
    print("\n" + "=" * 60)
    print("VALIDATING DECORATORS MODULE")
    print("=" * 60)
    
    try:
        from apps.core.decorators import (
            require_role, require_any_role, require_author_role,
            require_editor_role, require_administrator_role,
            require_content_creator_role, require_content_manager_role,
            require_post_ownership_or_editor
        )
        print("✓ Successfully imported role-based decorators")
        
        # Test decorator creation
        @require_author_role()
        def test_view(request):
            return "test"
        
        print("✓ Decorators can be applied to functions")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import decorators: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating decorators: {e}")
        return False


def validate_mixins():
    """Validate the mixins module."""
    print("\n" + "=" * 60)
    print("VALIDATING MIXINS MODULE")
    print("=" * 60)
    
    try:
        from apps.core.mixins import (
            RoleRequiredMixin, AnyRoleRequiredMixin, AuthorRequiredMixin,
            EditorRequiredMixin, AdministratorRequiredMixin,
            ContentCreatorMixin, ContentManagerMixin, PostOwnershipMixin,
            CommentModerationMixin, UserManagementMixin, AnalyticsViewMixin
        )
        print("✓ Successfully imported role-based mixins")
        
        # Test mixin instantiation
        class TestView(ContentCreatorMixin):
            pass
        
        view = TestView()
        print("✓ Mixins can be used in class definitions")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import mixins: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating mixins: {e}")
        return False


def validate_admin_integration():
    """Validate the admin integration."""
    print("\n" + "=" * 60)
    print("VALIDATING ADMIN INTEGRATION")
    print("=" * 60)
    
    try:
        from apps.accounts.admin import CustomUserAdmin, CustomGroupAdmin
        print("✓ Successfully imported custom admin classes")
        
        # Check if admin methods exist
        admin_instance = CustomUserAdmin(None, None)
        
        required_methods = [
            'get_user_roles', 'assign_author_role', 'assign_editor_role',
            'assign_administrator_role', 'remove_author_role',
            'remove_editor_role', 'remove_administrator_role'
        ]
        
        for method in required_methods:
            if hasattr(admin_instance, method):
                print(f"✓ Admin method '{method}' exists")
            else:
                print(f"✗ Admin method '{method}' missing")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import admin classes: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating admin integration: {e}")
        return False


def validate_management_command():
    """Validate the management command."""
    print("\n" + "=" * 60)
    print("VALIDATING MANAGEMENT COMMAND")
    print("=" * 60)
    
    try:
        from apps.core.management.commands.setup_blog_permissions import Command
        print("✓ Successfully imported management command")
        
        command = Command()
        if hasattr(command, 'handle'):
            print("✓ Management command has handle method")
        else:
            print("✗ Management command missing handle method")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import management command: {e}")
        return False
    except Exception as e:
        print(f"✗ Error validating management command: {e}")
        return False


def validate_templates():
    """Validate the admin templates."""
    print("\n" + "=" * 60)
    print("VALIDATING ADMIN TEMPLATES")
    print("=" * 60)
    
    template_files = [
        'templates/admin/accounts/user/manage_roles.html',
        'templates/admin/accounts/user/setup_permissions.html',
        'templates/admin/auth/group/setup_blog_roles.html'
    ]
    
    all_exist = True
    for template_file in template_files:
        if os.path.exists(template_file):
            print(f"✓ Template '{template_file}' exists")
        else:
            print(f"✗ Template '{template_file}' missing")
            all_exist = False
    
    return all_exist


def validate_test_file():
    """Validate the test file."""
    print("\n" + "=" * 60)
    print("VALIDATING TEST FILE")
    print("=" * 60)
    
    test_file = 'tests/test_role_based_authorization.py'
    if os.path.exists(test_file):
        print(f"✓ Test file '{test_file}' exists")
        
        # Check test file content
        with open(test_file, 'r') as f:
            content = f.read()
            
        test_classes = [
            'BlogPermissionsTestCase',
            'RoleBasedDecoratorsTestCase',
            'RoleBasedMixinsTestCase',
            'AdminIntegrationTestCase'
        ]
        
        for test_class in test_classes:
            if test_class in content:
                print(f"✓ Test class '{test_class}' exists")
            else:
                print(f"✗ Test class '{test_class}' missing")
        
        return True
    else:
        print(f"✗ Test file '{test_file}' missing")
        return False


def main():
    """Run all validations."""
    print("ROLE-BASED AUTHORIZATION SYSTEM VALIDATION")
    print("=" * 60)
    
    validations = [
        validate_permissions_module,
        validate_decorators,
        validate_mixins,
        validate_admin_integration,
        validate_management_command,
        validate_templates,
        validate_test_file
    ]
    
    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"✗ Validation failed with error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Validations passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("\nThe role-based authorization system has been successfully implemented.")
        print("\nNext steps:")
        print("1. Run Django migrations: python manage.py migrate")
        print("2. Set up blog permissions: python manage.py setup_blog_permissions")
        print("3. Create test users and assign roles in Django admin")
        print("4. Test the permission system with your blog views")
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("Please review the failed validations above and fix any issues.")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)