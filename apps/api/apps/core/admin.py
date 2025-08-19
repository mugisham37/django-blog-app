"""
Core admin configuration
"""

from django.contrib import admin
from .models import (
    SiteConfiguration, MenuItem, Redirect, APIKey, AuditLog, CacheInvalidation
)


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Site configuration admin."""
    
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_description', 'site_keywords', 'site_logo', 'site_favicon')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'github_url', 'youtube_url', 'instagram_url')
        }),
        ('SEO Settings', {
            'fields': ('default_meta_title', 'default_meta_description', 'google_analytics_id', 'google_search_console_id')
        }),
        ('Features', {
            'fields': ('enable_comments', 'enable_newsletter', 'enable_search', 'enable_social_sharing')
        }),
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message')
        })
    )
    
    def has_add_permission(self, request):
        # Only allow one configuration
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Menu item admin."""
    
    list_display = ('title', 'location', 'parent', 'order', 'is_active')
    list_filter = ('location', 'is_active', 'parent')
    search_fields = ('title', 'url')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'url', 'location', 'parent')
        }),
        ('Display Options', {
            'fields': ('order', 'is_active', 'open_in_new_tab')
        }),
        ('Styling', {
            'fields': ('css_class', 'icon_class'),
            'classes': ('collapse',)
        })
    )


@admin.register(Redirect)
class RedirectAdmin(admin.ModelAdmin):
    """Redirect admin."""
    
    list_display = ('old_path', 'new_path', 'redirect_type', 'is_active', 'hit_count', 'created_at')
    list_filter = ('redirect_type', 'is_active', 'created_at')
    search_fields = ('old_path', 'new_path')
    readonly_fields = ('hit_count', 'created_at', 'updated_at')


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    """API key admin."""
    
    list_display = ('name', 'user', 'is_active', 'usage_count', 'rate_limit', 'last_used', 'expires_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('name', 'user__username', 'user__email')
    readonly_fields = ('key', 'usage_count', 'last_used', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'user', 'is_active')
        }),
        ('API Key', {
            'fields': ('key',)
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit', 'expires_at')
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit log admin."""
    
    list_display = ('user', 'action_type', 'object_type', 'description_short', 'timestamp')
    list_filter = ('action_type', 'object_type', 'timestamp')
    search_fields = ('user__username', 'description', 'object_id')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'action_type', 'object_type', 'object_id', 'description')
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Extra Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        })
    )
    
    def description_short(self, obj):
        """Show shortened description."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CacheInvalidation)
class CacheInvalidationAdmin(admin.ModelAdmin):
    """Cache invalidation admin."""
    
    list_display = ('cache_key', 'reason', 'triggered_by', 'object_type', 'timestamp')
    list_filter = ('reason', 'object_type', 'timestamp')
    search_fields = ('cache_key', 'cache_pattern', 'reason')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False