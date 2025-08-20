"""
Django integration utilities for the authentication package.

Provides Django-specific adapters, middleware, and utilities for seamless
integration with Django applications.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

try:
    from django.contrib.auth.models import AbstractUser
    from django.contrib.auth.backends import BaseBackend
    from django.http import HttpRequest, HttpResponse
    from django.conf import settings
    from django.core.exceptions import ValidationError
    from django.utils.deprecation import MiddlewareMixin
    from django.contrib.auth import get_user_model
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Create dummy classes for non-Django environments
    class AbstractUser:
        pass
    class BaseBackend:
        pass
    class HttpRequest:
        pass
    class HttpResponse:
        pass
    class ValidationError(Exception):
        pass
    class MiddlewareMixin:
        pass

from .strategies import JWTStrategy, JWTConfig
from .security import PasswordHasher
from .permissions import RoleBasedPermission, default_role_registry
from .models import User as AuthUser, UserStatus, AuthProvider
from .session_management import SessionManager, DeviceInfo, default_session_manager
from .audit_logging import AuditLogger, AuditEventType, AuditSeverity, default_audit_logger
from .password_policies import PasswordValidator, AccountLockoutManager, default_password_validator, default_lockout_manager
from .mfa import TOTPProvider, SMSProvider, EmailProvider

logger = logging.getLogger(__name__)


class DjangoUserAdapter:
    """
    Adapter to bridge Django User model with auth package User model.
    
    Provides conversion between Django User instances and auth package
    User instances for seamless integration.
    """
    
    @staticmethod
    def from_django_user(django_user) -> AuthUser:
        """
        Convert Django User to auth package User.
        
        Args:
            django_user: Django User instance
            
        Returns:
            AuthUser instance
        """
        if not DJANGO_AVAILABLE:
            raise ImportError("Django is not available")
        
        # Map Django user status to auth package status
        status_mapping = {
            True: UserStatus.ACTIVE,
            False: UserStatus.INACTIVE
        }
        
        auth_user = AuthUser(
            id=str(django_user.pk),
            username=django_user.username,
            email=django_user.email,
            status=status_mapping.get(django_user.is_active, UserStatus.INACTIVE),
            auth_provider=AuthProvider.LOCAL,
            email_verified=getattr(django_user, 'email_verified', False),
            created_at=django_user.date_joined,
            updated_at=getattr(django_user, 'updated_at', django_user.date_joined)
        )
        
        # Set profile information if available
        if hasattr(django_user, 'first_name'):
            auth_user.profile.first_name = django_user.first_name
        if hasattr(django_user, 'last_name'):
            auth_user.profile.last_name = django_user.last_name
        
        # Set roles from Django groups
        if hasattr(django_user, 'groups'):
            auth_user.roles = set(group.name for group in django_user.groups.all())
        
        return auth_user
    
    @staticmethod
    def to_django_user(auth_user: AuthUser, django_user_class=None):
        """
        Update Django User from auth package User.
        
        Args:
            auth_user: AuthUser instance
            django_user_class: Django User model class
            
        Returns:
            Django User instance
        """
        if not DJANGO_AVAILABLE:
            raise ImportError("Django is not available")
        
        if django_user_class is None:
            django_user_class = get_user_model()
        
        # Try to get existing user or create new one
        try:
            django_user = django_user_class.objects.get(pk=auth_user.id)
        except django_user_class.DoesNotExist:
            django_user = django_user_class(pk=auth_user.id)
        
        # Update basic fields
        django_user.username = auth_user.username
        django_user.email = auth_user.email
        django_user.is_active = auth_user.status == UserStatus.ACTIVE
        
        # Update profile fields if available
        if hasattr(django_user, 'first_name'):
            django_user.first_name = auth_user.profile.first_name
        if hasattr(django_user, 'last_name'):
            django_user.last_name = auth_user.profile.last_name
        
        return django_user


class JWTAuthenticationBackend(BaseBackend):
    """
    Enhanced Django authentication backend with advanced security features.
    
    Integrates JWT tokens, session management, audit logging, account lockout,
    and MFA support with Django's authentication system.
    """
    
    def __init__(self):
        if not DJANGO_AVAILABLE:
            raise ImportError("Django is not available")
        
        # Initialize components from Django settings
        jwt_config = JWTConfig(
            secret_key=getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY),
            algorithm=getattr(settings, 'JWT_ALGORITHM', 'HS256'),
            issuer=getattr(settings, 'JWT_ISSUER', 'django-app'),
            audience=getattr(settings, 'JWT_AUDIENCE', 'api')
        )
        self.jwt_strategy = JWTStrategy(jwt_config)
        self.password_hasher = PasswordHasher()
        self.session_manager = default_session_manager
        self.audit_logger = default_audit_logger
        self.lockout_manager = default_lockout_manager
        self.password_validator = default_password_validator
    
    def authenticate(self, request, username=None, password=None, token=None, mfa_token=None, **kwargs):
        """
        Enhanced authentication with security features.
        
        Args:
            request: Django request object
            username: Username for password authentication
            password: Password for password authentication
            token: JWT token for token authentication
            mfa_token: MFA verification token
            
        Returns:
            Django User instance if authentication successful
        """
        User = get_user_model()
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if token:
            # JWT token authentication
            return self._authenticate_token(token, ip_address, user_agent)
        
        elif username and password:
            # Username/password authentication with security checks
            return self._authenticate_credentials(username, password, ip_address, user_agent, request)
        
        return None
    
    def _authenticate_token(self, token: str, ip_address: str, user_agent: str):
        """Authenticate using JWT token."""
        try:
            payload = self.jwt_strategy.validate_token(token, "access")
            user_id = payload.get("user_id")
            session_id = payload.get("session_id")
            
            if user_id:
                User = get_user_model()
                user = User.objects.get(pk=user_id)
                
                # Validate session if session_id is present
                if session_id:
                    device_info = DeviceInfo(
                        device_id=f"web_{user_id}",
                        user_agent=user_agent,
                        ip_address=ip_address
                    )
                    
                    if not self.session_manager.validate_session(session_id, device_info):
                        self.audit_logger.log_authentication_event(
                            AuditEventType.LOGIN_FAILURE,
                            str(user_id),
                            ip_address,
                            user_agent,
                            "failure",
                            {"reason": "invalid_session"}
                        )
                        return None
                
                # Log successful token authentication
                self.audit_logger.log_authentication_event(
                    AuditEventType.LOGIN_SUCCESS,
                    str(user_id),
                    ip_address,
                    user_agent,
                    "success",
                    {"method": "jwt_token"}
                )
                
                return user
                
        except Exception as e:
            logger.warning(f"JWT authentication failed: {e}")
            self.audit_logger.log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                "unknown",
                ip_address,
                user_agent,
                "failure",
                {"reason": "invalid_token", "error": str(e)}
            )
        
        return None
    
    def _authenticate_credentials(self, username: str, password: str, ip_address: str, 
                                user_agent: str, request):
        """Authenticate using username/password with security checks."""
        User = get_user_model()
        
        try:
            # Try to find user by username or email
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=username)
                except User.DoesNotExist:
                    user = None
            
            if not user:
                # Record failed attempt for unknown user
                self.lockout_manager.record_login_attempt(
                    username, ip_address, False, user_agent
                )
                
                self.audit_logger.log_authentication_event(
                    AuditEventType.LOGIN_FAILURE,
                    username,
                    ip_address,
                    user_agent,
                    "failure",
                    {"reason": "user_not_found"}
                )
                
                # Run password hasher to prevent timing attacks
                self.password_hasher.verify_password(password, "dummy_hash")
                return None
            
            user_id = str(user.pk)
            
            # Check account lockout
            if self.lockout_manager.is_account_locked(user_id):
                lockout_info = self.lockout_manager.get_lockout_info(user_id)
                
                self.audit_logger.log_authentication_event(
                    AuditEventType.LOGIN_FAILURE,
                    user_id,
                    ip_address,
                    user_agent,
                    "failure",
                    {"reason": "account_locked", "lockout_info": lockout_info}
                )
                
                return None
            
            # Verify password
            password_hash = getattr(user, 'password_hash', user.password)
            
            if self.password_hasher.verify_password(password, password_hash):
                # Successful authentication
                
                # Record successful login
                self.lockout_manager.record_login_attempt(
                    user_id, ip_address, True, user_agent
                )
                
                # Create session
                device_info = DeviceInfo(
                    device_id=f"web_{user_id}_{ip_address}",
                    user_agent=user_agent,
                    ip_address=ip_address,
                    device_type="web"
                )
                
                session = self.session_manager.create_session(
                    user_id, device_info, "password"
                )
                
                # Store session ID in request for later use
                if hasattr(request, 'session'):
                    request.session['auth_session_id'] = session.session_id
                
                # Log successful authentication
                self.audit_logger.log_authentication_event(
                    AuditEventType.LOGIN_SUCCESS,
                    user_id,
                    ip_address,
                    user_agent,
                    "success",
                    {"method": "password", "session_id": session.session_id}
                )
                
                return user
            else:
                # Failed authentication
                lockout_result = self.lockout_manager.record_login_attempt(
                    user_id, ip_address, False, user_agent
                )
                
                self.audit_logger.log_authentication_event(
                    AuditEventType.LOGIN_FAILURE,
                    user_id,
                    ip_address,
                    user_agent,
                    "failure",
                    {
                        "reason": "invalid_password",
                        "attempts_remaining": lockout_result.get("attempts_remaining"),
                        "require_captcha": lockout_result.get("require_captcha")
                    }
                )
                
                return None
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            self.audit_logger.log_authentication_event(
                AuditEventType.LOGIN_FAILURE,
                username,
                ip_address,
                user_agent,
                "error",
                {"reason": "system_error", "error": str(e)}
            )
            return None
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def get_user(self, user_id):
        """Get user by ID."""
        if not DJANGO_AVAILABLE:
            return None
        
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class RoleBasedPermissionBackend(BaseBackend):
    """
    Django permission backend using role-based access control.
    
    Integrates the auth package RBAC system with Django's
    permission framework.
    """
    
    def __init__(self):
        self.permission_checker = RoleBasedPermission(default_role_registry)
    
    def authenticate(self, request, **kwargs):
        """This backend doesn't authenticate users."""
        return None
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has permission.
        
        Args:
            user_obj: Django User instance
            perm: Permission string (e.g., 'blog.create')
            obj: Optional object for object-level permissions
            
        Returns:
            True if user has permission
        """
        if not user_obj or not user_obj.is_active:
            return False
        
        # Convert Django user to auth user
        auth_user = DjangoUserAdapter.from_django_user(user_obj)
        
        # Parse permission string
        if '.' in perm:
            resource, action_str = perm.split('.', 1)
        else:
            resource = perm
            action_str = 'read'
        
        # Map action string to PermissionAction
        from .permissions import PermissionAction
        action_mapping = {
            'add': PermissionAction.CREATE,
            'create': PermissionAction.CREATE,
            'view': PermissionAction.READ,
            'read': PermissionAction.READ,
            'change': PermissionAction.UPDATE,
            'update': PermissionAction.UPDATE,
            'delete': PermissionAction.DELETE,
            'execute': PermissionAction.EXECUTE,
            'manage': PermissionAction.MANAGE,
        }
        
        action = action_mapping.get(action_str, PermissionAction.READ)
        
        # Build context for permission checking
        context = {}
        if obj:
            context['resource_id'] = getattr(obj, 'id', None)
            context['owner_id'] = getattr(obj, 'owner_id', getattr(obj, 'user_id', None))
        
        return self.permission_checker.check_permission(
            list(auth_user.roles),
            resource,
            action,
            context
        )
    
    def has_module_perms(self, user_obj, app_label):
        """Check if user has any permissions for app."""
        return user_obj and user_obj.is_active


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Django middleware for JWT token authentication.
    
    Automatically authenticates users based on JWT tokens
    in request headers or cookies.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        if DJANGO_AVAILABLE:
            jwt_config = JWTConfig(
                secret_key=getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY),
                algorithm=getattr(settings, 'JWT_ALGORITHM', 'HS256')
            )
            self.jwt_strategy = JWTStrategy(jwt_config)
    
    def process_request(self, request):
        """Process incoming request for JWT authentication."""
        if not DJANGO_AVAILABLE:
            return None
        
        # Skip authentication for certain paths
        skip_paths = getattr(settings, 'JWT_SKIP_PATHS', ['/admin/', '/static/', '/media/'])
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Extract token from Authorization header or cookie
        token = self._extract_token(request)
        
        if token:
            try:
                payload = self.jwt_strategy.validate_token(token, "access")
                user_id = payload.get("user_id")
                
                if user_id:
                    User = get_user_model()
                    try:
                        user = User.objects.get(pk=user_id)
                        request.user = user
                        request.jwt_payload = payload
                    except User.DoesNotExist:
                        pass
            except Exception as e:
                logger.debug(f"JWT authentication failed: {e}")
        
        return None
    
    def _extract_token(self, request):
        """Extract JWT token from request."""
        # Check Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Check cookie
        cookie_name = getattr(settings, 'JWT_COOKIE_NAME', 'access_token')
        return request.COOKIES.get(cookie_name)


class PasswordValidationMixin:
    """
    Mixin for Django password validation using auth package.
    
    Provides password strength validation and policy enforcement
    for Django forms and user models.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.password_hasher = PasswordHasher()
    
    def validate_password_strength(self, password, user_info=None):
        """
        Validate password strength using auth package.
        
        Args:
            password: Password to validate
            user_info: User information for validation
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        if not DJANGO_AVAILABLE:
            return
        
        validation_result = self.password_hasher.validate_password_strength(
            password, user_info or {}
        )
        
        if not validation_result["valid"]:
            raise ValidationError(validation_result["errors"])
        
        # Add warnings as messages if available
        if validation_result["warnings"] and hasattr(self, 'add_message'):
            from django.contrib import messages
            for warning in validation_result["warnings"]:
                self.add_message(messages.WARNING, warning)


def setup_django_integration():
    """
    Setup Django integration for the auth package.
    
    Configures authentication backends, middleware, and other
    Django-specific settings for the auth package.
    """
    if not DJANGO_AVAILABLE:
        raise ImportError("Django is not available")
    
    # Add authentication backends
    auth_backends = list(getattr(settings, 'AUTHENTICATION_BACKENDS', []))
    
    jwt_backend = 'auth_package.django_integration.JWTAuthenticationBackend'
    rbac_backend = 'auth_package.django_integration.RoleBasedPermissionBackend'
    
    if jwt_backend not in auth_backends:
        auth_backends.append(jwt_backend)
    
    if rbac_backend not in auth_backends:
        auth_backends.append(rbac_backend)
    
    settings.AUTHENTICATION_BACKENDS = auth_backends
    
    # Add JWT middleware
    middleware = list(getattr(settings, 'MIDDLEWARE', []))
    jwt_middleware = 'auth_package.django_integration.JWTAuthenticationMiddleware'
    
    if jwt_middleware not in middleware:
        # Insert after security middleware but before auth middleware
        auth_middleware_index = None
        for i, mw in enumerate(middleware):
            if 'AuthenticationMiddleware' in mw:
                auth_middleware_index = i
                break
        
        if auth_middleware_index is not None:
            middleware.insert(auth_middleware_index, jwt_middleware)
        else:
            middleware.append(jwt_middleware)
    
    settings.MIDDLEWARE = middleware
    
    logger.info("Django integration for auth package configured successfully")


# Django management command helpers
def create_default_roles():
    """Create default roles in the role registry."""
    # Default roles are already created in RoleRegistry.__init__
    logger.info("Default roles created in role registry")


def sync_django_users_with_auth_package():
    """
    Sync existing Django users with auth package user repository.
    
    Useful for migrating existing Django applications to use
    the auth package.
    """
    if not DJANGO_AVAILABLE:
        raise ImportError("Django is not available")
    
    from .models import default_user_repository
    
    User = get_user_model()
    synced_count = 0
    
    for django_user in User.objects.all():
        try:
            auth_user = DjangoUserAdapter.from_django_user(django_user)
            default_user_repository.create_user(auth_user)
            synced_count += 1
        except ValueError:
            # User already exists, update instead
            auth_user = DjangoUserAdapter.from_django_user(django_user)
            default_user_repository.update_user(auth_user)
            synced_count += 1
        except Exception as e:
            logger.error(f"Failed to sync user {django_user.username}: {e}")
    
    logger.info(f"Synced {synced_count} Django users with auth package")
    return synced_count