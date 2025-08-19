"""
Tests for role-based authorization system.
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from unittest.mock import Mock, patch

from apps.core.permissions import (
    BlogRoles, BlogPermissions, create_blog_groups_and_permissions,
    assign_user_to_role, remove_user_from_role, get_user_roles,
    user_has_role, user_can_edit_post, user_can_delete_post,
    user_can_moderate_comments, user_can_manage_users,
    user_can_view_analytics, require_role_permission,
    RoleBasedPermissionMixin
)
from apps.core.decorators import (
    require_role, require_any_role, require_author_role,
    require_editor_role, require_administrator_role,
    require_content_creator_role, require_content_manager_role
)
from apps.core.mixins import (
    RoleRequiredMixin, AnyRoleRequiredMixin, AuthorRequiredMixin,
    EditorRequiredMixin, AdministratorRequiredMixin,
    ContentCreatorMixin, ContentManagerMixin, PostOwnershipMixin,
    CommentModerationMixin, UserManagementMixin, AnalyticsViewMixin
)

User = get_user_model()


class BlogPermissionsTestCase(TestCase):
    """Test case for blog permissions and roles."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create test users
        self.author_user = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        self.superuser = User.objects.create_superuser(
            username='superuser',
            email='superuser@test.com',
            password='testpass123'
        )
        
        # Set up permissions and roles
        create_blog_groups_and_permissions()
        
        # Assign roles
        assign_user_to_role(self.author_user, BlogRoles.AUTHOR)
        assign_user_to_role(self.editor_user, BlogRoles.EDITOR)
        assign_user_to_role(self.admin_user, BlogRoles.ADMINISTRATOR)
    
    def test_create_blog_groups_and_permissions(self):
        """Test that blog groups and permissions are created correctly."""
        # Check that all blog roles exist
        for role in BlogRoles.ALL_ROLES:
            self.assertTrue(Group.objects.filter(name=role).exists())
        
        # Check that groups have permissions
        author_group = Group.objects.get(name=BlogRoles.AUTHOR)
        editor_group = Group.objects.get(name=BlogRoles.EDITOR)
        admin_group = Group.objects.get(name=BlogRoles.ADMINISTRATOR)
        
        self.assertGreater(author_group.permissions.count(), 0)
        self.assertGreater(editor_group.permissions.count(), 0)
        self.assertGreater(admin_group.permissions.count(), 0)
        
        # Editor should have more permissions than Author
        self.assertGreater(
            editor_group.permissions.count(),
            author_group.permissions.count()
        )
        
        # Administrator should have more permissions than Editor
        self.assertGreater(
            admin_group.permissions.count(),
            editor_group.permissions.count()
        )
    
    def test_assign_user_to_role(self):
        """Test assigning users to roles."""
        test_user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Test successful assignment
        result = assign_user_to_role(test_user, BlogRoles.AUTHOR)
        self.assertTrue(result)
        self.assertTrue(user_has_role(test_user, BlogRoles.AUTHOR))
        
        # Test invalid role
        result = assign_user_to_role(test_user, 'InvalidRole')
        self.assertFalse(result)
    
    def test_remove_user_from_role(self):
        """Test removing users from roles."""
        # Remove author role
        result = remove_user_from_role(self.author_user, BlogRoles.AUTHOR)
        self.assertTrue(result)
        self.assertFalse(user_has_role(self.author_user, BlogRoles.AUTHOR))
        
        # Test removing non-existent role
        result = remove_user_from_role(self.regular_user, BlogRoles.AUTHOR)
        self.assertTrue(result)  # Should succeed even if user doesn't have the role
    
    def test_get_user_roles(self):
        """Test getting user roles."""
        author_roles = get_user_roles(self.author_user)
        self.assertIn(BlogRoles.AUTHOR, author_roles)
        
        editor_roles = get_user_roles(self.editor_user)
        self.assertIn(BlogRoles.EDITOR, editor_roles)
        
        admin_roles = get_user_roles(self.admin_user)
        self.assertIn(BlogRoles.ADMINISTRATOR, admin_roles)
        
        regular_roles = get_user_roles(self.regular_user)
        self.assertEqual(len(regular_roles), 0)
    
    def test_user_has_role(self):
        """Test checking if user has specific role."""
        self.assertTrue(user_has_role(self.author_user, BlogRoles.AUTHOR))
        self.assertFalse(user_has_role(self.author_user, BlogRoles.EDITOR))
        
        self.assertTrue(user_has_role(self.editor_user, BlogRoles.EDITOR))
        self.assertFalse(user_has_role(self.editor_user, BlogRoles.AUTHOR))
        
        self.assertTrue(user_has_role(self.admin_user, BlogRoles.ADMINISTRATOR))
        self.assertFalse(user_has_role(self.regular_user, BlogRoles.AUTHOR))
    
    @patch('apps.blog.models.Post')
    def test_user_can_edit_post(self, mock_post_model):
        """Test post editing permissions."""
        # Create mock post
        mock_post = Mock()
        mock_post.author = self.author_user
        
        # Author can edit own post
        self.assertTrue(user_can_edit_post(self.author_user, mock_post))
        
        # Author cannot edit other's post
        self.assertFalse(user_can_edit_post(self.regular_user, mock_post))
        
        # Editor can edit any post
        self.assertTrue(user_can_edit_post(self.editor_user, mock_post))
        
        # Administrator can edit any post
        self.assertTrue(user_can_edit_post(self.admin_user, mock_post))
        
        # Superuser can edit any post
        self.assertTrue(user_can_edit_post(self.superuser, mock_post))
    
    @patch('apps.blog.models.Post')
    def test_user_can_delete_post(self, mock_post_model):
        """Test post deletion permissions."""
        # Create mock post
        mock_post = Mock()
        mock_post.author = self.author_user
        
        # Regular user cannot delete posts
        self.assertFalse(user_can_delete_post(self.regular_user, mock_post))
        
        # Editor can delete posts
        self.assertTrue(user_can_delete_post(self.editor_user, mock_post))
        
        # Administrator can delete posts
        self.assertTrue(user_can_delete_post(self.admin_user, mock_post))
        
        # Superuser can delete posts
        self.assertTrue(user_can_delete_post(self.superuser, mock_post))
    
    def test_user_can_moderate_comments(self):
        """Test comment moderation permissions."""
        self.assertFalse(user_can_moderate_comments(self.author_user))
        self.assertTrue(user_can_moderate_comments(self.editor_user))
        self.assertTrue(user_can_moderate_comments(self.admin_user))
        self.assertTrue(user_can_moderate_comments(self.superuser))
        self.assertFalse(user_can_moderate_comments(self.regular_user))
    
    def test_user_can_manage_users(self):
        """Test user management permissions."""
        self.assertFalse(user_can_manage_users(self.author_user))
        self.assertFalse(user_can_manage_users(self.editor_user))
        self.assertTrue(user_can_manage_users(self.admin_user))
        self.assertTrue(user_can_manage_users(self.superuser))
        self.assertFalse(user_can_manage_users(self.regular_user))
    
    def test_user_can_view_analytics(self):
        """Test analytics viewing permissions."""
        self.assertFalse(user_can_view_analytics(self.author_user))
        self.assertTrue(user_can_view_analytics(self.editor_user))
        self.assertTrue(user_can_view_analytics(self.admin_user))
        self.assertTrue(user_can_view_analytics(self.superuser))
        self.assertFalse(user_can_view_analytics(self.regular_user))
    
    def test_require_role_permission(self):
        """Test role permission requirement function."""
        # Test with valid role
        try:
            require_role_permission(
                self.author_user,
                required_roles=[BlogRoles.AUTHOR]
            )
        except PermissionDenied:
            self.fail("Should not raise PermissionDenied for valid role")
        
        # Test with invalid role
        with self.assertRaises(PermissionDenied):
            require_role_permission(
                self.regular_user,
                required_roles=[BlogRoles.AUTHOR]
            )
        
        # Test with unauthenticated user
        anonymous_user = Mock()
        anonymous_user.is_authenticated = False
        
        with self.assertRaises(PermissionDenied):
            require_role_permission(
                anonymous_user,
                required_roles=[BlogRoles.AUTHOR]
            )
        
        # Test superuser bypass
        try:
            require_role_permission(
                self.superuser,
                required_roles=[BlogRoles.AUTHOR]
            )
        except PermissionDenied:
            self.fail("Superuser should bypass role checks")


class RoleBasedDecoratorsTestCase(TestCase):
    """Test case for role-based decorators."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create test users
        self.author_user = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        # Set up permissions and roles
        create_blog_groups_and_permissions()
        assign_user_to_role(self.author_user, BlogRoles.AUTHOR)
        assign_user_to_role(self.editor_user, BlogRoles.EDITOR)
    
    def test_require_role_decorator(self):
        """Test the require_role decorator."""
        @require_role(BlogRoles.AUTHOR)
        def test_view(request):
            return "Success"
        
        # Test with author user
        request = self.factory.get('/')
        request.user = self.author_user
        result = test_view(request)
        self.assertEqual(result, "Success")
        
        # Test with regular user (should be denied)
        request.user = self.regular_user
        response = test_view(request)
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_require_any_role_decorator(self):
        """Test the require_any_role decorator."""
        @require_any_role([BlogRoles.AUTHOR, BlogRoles.EDITOR])
        def test_view(request):
            return "Success"
        
        # Test with author user
        request = self.factory.get('/')
        request.user = self.author_user
        result = test_view(request)
        self.assertEqual(result, "Success")
        
        # Test with editor user
        request.user = self.editor_user
        result = test_view(request)
        self.assertEqual(result, "Success")
        
        # Test with regular user (should be denied)
        request.user = self.regular_user
        response = test_view(request)
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_require_author_role_decorator(self):
        """Test the require_author_role decorator."""
        @require_author_role()
        def test_view(request):
            return "Success"
        
        # Test with author user
        request = self.factory.get('/')
        request.user = self.author_user
        result = test_view(request)
        self.assertEqual(result, "Success")
        
        # Test with regular user (should be denied)
        request.user = self.regular_user
        response = test_view(request)
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_require_editor_role_decorator(self):
        """Test the require_editor_role decorator."""
        @require_editor_role()
        def test_view(request):
            return "Success"
        
        # Test with editor user
        request = self.factory.get('/')
        request.user = self.editor_user
        result = test_view(request)
        self.assertEqual(result, "Success")
        
        # Test with author user (should be denied)
        request.user = self.author_user
        response = test_view(request)
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_require_content_creator_role_decorator(self):
        """Test the require_content_creator_role decorator."""
        @require_content_creator_role()
        def test_view(request):
            return "Success"
        
        # Test with author user
        request = self.factory.get('/')
        request.user = self.author_user
        result = test_view(request)
        self.assertEqual(result, "Success")
        
        # Test with editor user
        request.user = self.editor_user
        result = test_view(request)
        self.assertEqual(result, "Success")
        
        # Test with regular user (should be denied)
        request.user = self.regular_user
        response = test_view(request)
        self.assertIsInstance(response, HttpResponseForbidden)
    
    def test_api_response_mode(self):
        """Test decorators with API response mode."""
        @require_role(BlogRoles.AUTHOR, api_response=True)
        def test_api_view(request):
            return "Success"
        
        # Test with regular user (should return JSON response)
        request = self.factory.get('/api/test/')
        request.user = self.regular_user
        response = test_api_view(request)
        self.assertIsInstance(response, JsonResponse)


class RoleBasedMixinsTestCase(TestCase):
    """Test case for role-based mixins."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        
        # Create test users
        self.author_user = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='testpass123'
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        # Set up permissions and roles
        create_blog_groups_and_permissions()
        assign_user_to_role(self.author_user, BlogRoles.AUTHOR)
        assign_user_to_role(self.editor_user, BlogRoles.EDITOR)
    
    def test_role_required_mixin(self):
        """Test the RoleRequiredMixin."""
        class TestView(RoleRequiredMixin):
            required_role = BlogRoles.AUTHOR
            
            def dispatch(self, request, *args, **kwargs):
                return super().dispatch(request, *args, **kwargs)
        
        view = TestView()
        
        # Test with author user
        request = self.factory.get('/')
        request.user = self.author_user
        try:
            view.dispatch(request)
        except PermissionDenied:
            self.fail("Should not raise PermissionDenied for author user")
        
        # Test with regular user
        request.user = self.regular_user
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)
    
    def test_any_role_required_mixin(self):
        """Test the AnyRoleRequiredMixin."""
        class TestView(AnyRoleRequiredMixin):
            required_roles = [BlogRoles.AUTHOR, BlogRoles.EDITOR]
            
            def dispatch(self, request, *args, **kwargs):
                return super().dispatch(request, *args, **kwargs)
        
        view = TestView()
        
        # Test with author user
        request = self.factory.get('/')
        request.user = self.author_user
        try:
            view.dispatch(request)
        except PermissionDenied:
            self.fail("Should not raise PermissionDenied for author user")
        
        # Test with editor user
        request.user = self.editor_user
        try:
            view.dispatch(request)
        except PermissionDenied:
            self.fail("Should not raise PermissionDenied for editor user")
        
        # Test with regular user
        request.user = self.regular_user
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)
    
    def test_content_creator_mixin(self):
        """Test the ContentCreatorMixin."""
        class TestView(ContentCreatorMixin):
            def dispatch(self, request, *args, **kwargs):
                return super().dispatch(request, *args, **kwargs)
        
        view = TestView()
        
        # Test with author user
        request = self.factory.get('/')
        request.user = self.author_user
        try:
            view.dispatch(request)
        except PermissionDenied:
            self.fail("Should not raise PermissionDenied for author user")
        
        # Test with regular user
        request.user = self.regular_user
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)
    
    def test_content_manager_mixin(self):
        """Test the ContentManagerMixin."""
        class TestView(ContentManagerMixin):
            def dispatch(self, request, *args, **kwargs):
                return super().dispatch(request, *args, **kwargs)
        
        view = TestView()
        
        # Test with editor user
        request = self.factory.get('/')
        request.user = self.editor_user
        try:
            view.dispatch(request)
        except PermissionDenied:
            self.fail("Should not raise PermissionDenied for editor user")
        
        # Test with author user (should be denied)
        request.user = self.author_user
        with self.assertRaises(PermissionDenied):
            view.dispatch(request)
    
    @patch('apps.blog.models.Post')
    def test_post_ownership_mixin(self, mock_post_model):
        """Test the PostOwnershipMixin."""
        class TestView(PostOwnershipMixin):
            def get_queryset(self):
                return mock_post_model.objects.all()
            
            def has_permission(self, obj=None):
                return super().has_permission(obj)
        
        view = TestView()
        
        # Mock post object
        mock_post = Mock()
        mock_post.author = self.author_user
        
        # Test with author user (owner)
        request = self.factory.get('/')
        request.user = self.author_user
        view.request = request
        self.assertTrue(view.has_permission(mock_post))
        
        # Test with editor user (should have access)
        request.user = self.editor_user
        view.request = request
        self.assertTrue(view.has_permission(mock_post))
        
        # Test with regular user (should be denied)
        request.user = self.regular_user
        view.request = request
        self.assertFalse(view.has_permission(mock_post))


class AdminIntegrationTestCase(TestCase):
    """Test case for admin integration."""
    
    def setUp(self):
        """Set up test data."""
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Set up permissions and roles
        create_blog_groups_and_permissions()
    
    def test_admin_role_assignment_actions(self):
        """Test admin actions for role assignment."""
        from apps.accounts.admin import CustomUserAdmin
        
        admin_instance = CustomUserAdmin(User, None)
        
        # Mock request and queryset
        request = Mock()
        queryset = User.objects.filter(pk=self.test_user.pk)
        
        # Test assign author role action
        admin_instance.assign_author_role(request, queryset)
        self.assertTrue(user_has_role(self.test_user, BlogRoles.AUTHOR))
        
        # Test remove author role action
        admin_instance.remove_author_role(request, queryset)
        self.assertFalse(user_has_role(self.test_user, BlogRoles.AUTHOR))
    
    def test_admin_get_user_roles_display(self):
        """Test admin display of user roles."""
        from apps.accounts.admin import CustomUserAdmin
        
        admin_instance = CustomUserAdmin(User, None)
        
        # Test user with no roles
        result = admin_instance.get_user_roles(self.test_user)
        self.assertIn('No roles', result)
        
        # Test user with author role
        assign_user_to_role(self.test_user, BlogRoles.AUTHOR)
        result = admin_instance.get_user_roles(self.test_user)
        self.assertIn('Authors', result)
        self.assertIn('blue', result)  # Check color coding


if __name__ == '__main__':
    pytest.main([__file__])