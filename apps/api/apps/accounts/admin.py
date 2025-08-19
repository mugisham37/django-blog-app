"""
Accounts admin configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import Profile, EmailVerification, LoginAttempt

User = get_user_model()


class ProfileInline(admin.StackedInline):
    """Inline profile editor."""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom user admin."""
    
    inlines = (ProfileInline,)
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'status', 'is_staff')
    list_filter = ('role', 'status', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'status', 'email_verified', 'last_login_ip')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'role', 'status')
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Profile admin."""
    
    list_display = ('user', 'display_name', 'location', 'email_notifications', 'created_at')
    list_filter = ('email_notifications', 'comment_notifications', 'newsletter_subscription')
    search_fields = ('user__email', 'user__username', 'bio')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """Email verification admin."""
    
    list_display = ('user', 'email', 'created_at', 'expires_at', 'used')
    list_filter = ('used', 'created_at')
    search_fields = ('user__email', 'email')
    readonly_fields = ('token', 'created_at')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Login attempt admin."""
    
    list_display = ('email', 'ip_address', 'result', 'timestamp')
    list_filter = ('result', 'timestamp')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False