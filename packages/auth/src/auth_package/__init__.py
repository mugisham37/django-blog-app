"""
Enterprise Authentication Package

A comprehensive authentication package providing JWT strategies, MFA providers,
OAuth2 integration, and role-based access control (RBAC) for enterprise applications.
"""

from .strategies import (
    JWTStrategy, 
    OAuth2Strategy,
    setup_google_oauth2,
    setup_github_oauth2,
    setup_facebook_oauth2,
    setup_microsoft_oauth2,
    setup_linkedin_oauth2
)
from .mfa import TOTPProvider, SMSProvider, EmailProvider
from .security import PasswordHasher, TokenManager
from .permissions import RoleBasedPermission, Permission, Role
from .models import User, UserRole, UserRepository
from .session_management import SessionManager, DeviceInfo, Session
from .audit_logging import AuditLogger, AuditEvent, AuditEventType, AuditSeverity
from .password_policies import PasswordValidator, PasswordPolicy, AccountLockoutManager

# Django integration (optional)
DJANGO_INTEGRATION_AVAILABLE = False
try:
    import django
    # Only import if Django is properly configured
    from django.conf import settings
    if settings.configured:
        from .django_integration import (
            DjangoUserAdapter,
            JWTAuthenticationBackend,
            RoleBasedPermissionBackend,
            JWTAuthenticationMiddleware,
            PasswordValidationMixin,
            setup_django_integration
        )
        DJANGO_INTEGRATION_AVAILABLE = True
except (ImportError, Exception):
    # Django not available or not configured
    pass

__version__ = "1.0.0"
__all__ = [
    # Core authentication
    "JWTStrategy",
    "OAuth2Strategy",
    "setup_google_oauth2",
    "setup_github_oauth2", 
    "setup_facebook_oauth2",
    "setup_microsoft_oauth2",
    "setup_linkedin_oauth2",
    
    # MFA providers
    "TOTPProvider",
    "SMSProvider",
    "EmailProvider",
    
    # Security utilities
    "PasswordHasher",
    "TokenManager",
    
    # RBAC system
    "RoleBasedPermission",
    "Permission",
    "Role",
    
    # User management
    "User",
    "UserRole",
    "UserRepository",
    
    # Session management
    "SessionManager",
    "DeviceInfo",
    "Session",
    
    # Audit logging
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    
    # Password policies
    "PasswordValidator",
    "PasswordPolicy",
    "AccountLockoutManager",
]

# Add Django integration to __all__ if available
if DJANGO_INTEGRATION_AVAILABLE:
    __all__.extend([
        "DjangoUserAdapter",
        "JWTAuthenticationBackend", 
        "RoleBasedPermissionBackend",
        "JWTAuthenticationMiddleware",
        "PasswordValidationMixin",
        "setup_django_integration"
    ])

# Function to enable Django integration when needed
def enable_django_integration():
    """Enable Django integration if Django is available and configured."""
    global DJANGO_INTEGRATION_AVAILABLE
    try:
        import django
        from django.conf import settings
        if settings.configured:
            from .django_integration import (
                DjangoUserAdapter,
                JWTAuthenticationBackend,
                RoleBasedPermissionBackend,
                JWTAuthenticationMiddleware,
                PasswordValidationMixin,
                setup_django_integration
            )
            DJANGO_INTEGRATION_AVAILABLE = True
            
            # Add to globals for import
            globals().update({
                "DjangoUserAdapter": DjangoUserAdapter,
                "JWTAuthenticationBackend": JWTAuthenticationBackend,
                "RoleBasedPermissionBackend": RoleBasedPermissionBackend,
                "JWTAuthenticationMiddleware": JWTAuthenticationMiddleware,
                "PasswordValidationMixin": PasswordValidationMixin,
                "setup_django_integration": setup_django_integration
            })
            
            return True
    except (ImportError, Exception):
        pass
    
    return False