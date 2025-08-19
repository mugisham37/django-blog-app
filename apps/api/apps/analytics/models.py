"""
Analytics Models
Track user behavior and site analytics.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

User = get_user_model()


class PageView(models.Model):
    """Track page views across the site."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500)
    title = models.CharField(max_length=200, blank=True)
    referrer = models.URLField(max_length=500, blank=True)
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Device information
    device_type = models.CharField(max_length=20, blank=True)  # mobile, tablet, desktop
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    
    # Geographic information
    country = models.CharField(max_length=2, blank=True)  # ISO country code
    city = models.CharField(max_length=100, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    time_on_page = models.PositiveIntegerField(null=True, blank=True)  # seconds
    
    class Meta:
        db_table = 'analytics_page_view'
        verbose_name = _('Page View')
        verbose_name_plural = _('Page Views')
        indexes = [
            models.Index(fields=['url', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"View of {self.url} at {self.timestamp}"


class SearchQuery(models.Model):
    """Track search queries and results."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.CharField(max_length=255)
    results_count = models.PositiveIntegerField()
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField()
    
    # Search metadata
    search_type = models.CharField(max_length=20, default='general')  # general, category, tag
    filters_applied = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_search_query'
        verbose_name = _('Search Query')
        verbose_name_plural = _('Search Queries')
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Search: {self.query} ({self.results_count} results)"


class SearchClickthrough(models.Model):
    """Track clicks on search results."""
    
    search_query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name='clickthroughs')
    clicked_url = models.URLField(max_length=500)
    result_position = models.PositiveIntegerField()  # Position in search results
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_search_clickthrough'
        verbose_name = _('Search Clickthrough')
        verbose_name_plural = _('Search Clickthroughs')
        indexes = [
            models.Index(fields=['search_query']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Click on {self.clicked_url} (position {self.result_position})"


class UserSession(models.Model):
    """Track user sessions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_key = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Session metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=20, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)
    
    # Geographic information
    country = models.CharField(max_length=2, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)  # seconds
    
    # Activity metrics
    page_views = models.PositiveIntegerField(default=0)
    is_bounce = models.BooleanField(default=True)  # True if only one page viewed
    
    class Meta:
        db_table = 'analytics_user_session'
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['started_at']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else 'Anonymous'
        return f"Session by {user_info} at {self.started_at}"
    
    def end_session(self):
        """End the session and calculate duration."""
        self.ended_at = timezone.now()
        self.duration = int((self.ended_at - self.started_at).total_seconds())
        self.save()


class Event(models.Model):
    """Track custom events."""
    
    class EventCategory(models.TextChoices):
        USER_ACTION = 'user_action', _('User Action')
        CONTENT = 'content', _('Content')
        ENGAGEMENT = 'engagement', _('Engagement')
        CONVERSION = 'conversion', _('Conversion')
        ERROR = 'error', _('Error')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=EventCategory.choices)
    
    # Event data
    properties = models.JSONField(default=dict, blank=True)
    value = models.FloatField(null=True, blank=True)  # Numeric value for the event
    
    # User information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(UserSession, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    
    # Context
    url = models.URLField(max_length=500, blank=True)
    referrer = models.URLField(max_length=500, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_event'
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        indexes = [
            models.Index(fields=['name', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Event: {self.name} ({self.category})"


class DailyStats(models.Model):
    """Aggregated daily statistics."""
    
    date = models.DateField(unique=True)
    
    # Page views
    total_page_views = models.PositiveIntegerField(default=0)
    unique_page_views = models.PositiveIntegerField(default=0)
    
    # Users
    total_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    returning_users = models.PositiveIntegerField(default=0)
    
    # Sessions
    total_sessions = models.PositiveIntegerField(default=0)
    bounce_rate = models.FloatField(default=0.0)  # Percentage
    avg_session_duration = models.FloatField(default=0.0)  # Seconds
    
    # Content
    posts_published = models.PositiveIntegerField(default=0)
    comments_posted = models.PositiveIntegerField(default=0)
    
    # Search
    total_searches = models.PositiveIntegerField(default=0)
    unique_search_terms = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_daily_stats'
        verbose_name = _('Daily Stats')
        verbose_name_plural = _('Daily Stats')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Stats for {self.date}"


class PopularContent(models.Model):
    """Track popular content over time."""
    
    class ContentType(models.TextChoices):
        POST = 'post', _('Blog Post')
        CATEGORY = 'category', _('Category')
        TAG = 'tag', _('Tag')
        PAGE = 'page', _('Page')
    
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    content_id = models.CharField(max_length=100)  # Can be UUID or slug
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=500)
    
    # Metrics for the time period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    avg_time_on_page = models.FloatField(default=0.0)  # Seconds
    bounce_rate = models.FloatField(default=0.0)  # Percentage
    
    # Rankings
    rank = models.PositiveIntegerField()
    previous_rank = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_popular_content'
        verbose_name = _('Popular Content')
        verbose_name_plural = _('Popular Content')
        ordering = ['rank']
        indexes = [
            models.Index(fields=['content_type', 'period_start']),
            models.Index(fields=['rank']),
        ]
    
    def __str__(self):
        return f"{self.title} (Rank #{self.rank})"