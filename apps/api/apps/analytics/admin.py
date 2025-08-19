"""
Analytics admin configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PageView, SearchQuery, SearchClickthrough, UserSession,
    Event, DailyStats, PopularContent
)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    """Page view admin."""
    
    list_display = ('url_display', 'user', 'device_type', 'browser', 'country', 'timestamp')
    list_filter = ('device_type', 'browser', 'os', 'country', 'timestamp')
    search_fields = ('url', 'title', 'user__username', 'ip_address')
    readonly_fields = ('timestamp',)
    
    def url_display(self, obj):
        """Display shortened URL."""
        return obj.url[:50] + '...' if len(obj.url) > 50 else obj.url
    url_display.short_description = 'URL'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """Search query admin."""
    
    list_display = ('query', 'results_count', 'search_type', 'user', 'timestamp')
    list_filter = ('search_type', 'timestamp')
    search_fields = ('query', 'user__username')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SearchClickthrough)
class SearchClickthroughAdmin(admin.ModelAdmin):
    """Search clickthrough admin."""
    
    list_display = ('search_query', 'clicked_url_display', 'result_position', 'timestamp')
    list_filter = ('result_position', 'timestamp')
    search_fields = ('search_query__query', 'clicked_url')
    readonly_fields = ('timestamp',)
    
    def clicked_url_display(self, obj):
        """Display shortened URL."""
        return obj.clicked_url[:50] + '...' if len(obj.clicked_url) > 50 else obj.clicked_url
    clicked_url_display.short_description = 'Clicked URL'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User session admin."""
    
    list_display = ('user', 'device_type', 'browser', 'country', 'started_at', 'duration_display', 'page_views', 'is_bounce')
    list_filter = ('device_type', 'browser', 'os', 'country', 'is_bounce', 'started_at')
    search_fields = ('user__username', 'session_key', 'ip_address')
    readonly_fields = ('started_at', 'last_activity', 'ended_at', 'duration')
    
    def duration_display(self, obj):
        """Display session duration in readable format."""
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}m {seconds}s"
        return '-'
    duration_display.short_description = 'Duration'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Event admin."""
    
    list_display = ('name', 'category', 'user', 'value', 'url_display', 'timestamp')
    list_filter = ('category', 'name', 'timestamp')
    search_fields = ('name', 'user__username', 'url')
    readonly_fields = ('timestamp',)
    
    def url_display(self, obj):
        """Display shortened URL."""
        if obj.url:
            return obj.url[:50] + '...' if len(obj.url) > 50 else obj.url
        return '-'
    url_display.short_description = 'URL'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    """Daily stats admin."""
    
    list_display = ('date', 'total_page_views', 'unique_page_views', 'total_users', 'total_sessions', 'bounce_rate_display')
    list_filter = ('date',)
    readonly_fields = ('created_at', 'updated_at')
    
    def bounce_rate_display(self, obj):
        """Display bounce rate as percentage."""
        return f"{obj.bounce_rate:.1f}%"
    bounce_rate_display.short_description = 'Bounce Rate'
    
    def has_add_permission(self, request):
        return False


@admin.register(PopularContent)
class PopularContentAdmin(admin.ModelAdmin):
    """Popular content admin."""
    
    list_display = ('title', 'content_type', 'rank', 'views', 'unique_views', 'bounce_rate_display', 'period_start')
    list_filter = ('content_type', 'period_start')
    search_fields = ('title', 'content_id')
    readonly_fields = ('created_at',)
    
    def bounce_rate_display(self, obj):
        """Display bounce rate as percentage."""
        return f"{obj.bounce_rate:.1f}%"
    bounce_rate_display.short_description = 'Bounce Rate'
    
    def has_add_permission(self, request):
        return False