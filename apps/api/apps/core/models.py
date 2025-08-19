"""
Core Models
Base models and utilities used across the application.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields."""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class SiteConfiguration(models.Model):
    """Site-wide configuration settings."""
    
    # Site information
    site_name = models.CharField(max_length=100, default='Django Personal Blog')
    site_description = models.TextField(blank=True)
    site_keywords = models.CharField(max_length=255, blank=True)
    site_logo = models.ImageField(upload_to='site/', blank=True, null=True)
    site_favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    
    # Contact information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True)
    
    # Social media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    
    # SEO settings
    default_meta_title = models.CharField(max_length=60, blank=True)
    default_meta_description = models.CharField(max_length=160, blank=True)
    google_analytics_id = models.CharField(max_length=20, blank=True)
    google_search_console_id = models.CharField(max_length=100, blank=True)
    
    # Features
    enable_comments = models.BooleanField(default=True)
    enable_newsletter = models.BooleanField(default=True)
    enable_search = models.BooleanField(default=True)
    enable_social_sharing = models.BooleanField(default=True)
    
    # Maintenance
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_site_configuration'
        verbose_name = _('Site Configuration')
        verbose_name_plural = _('Site Configuration')
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration exists
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValueError('Only one site configuration is allowed')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get the site configuration (create if doesn't exist)."""
        config, created = cls.objects.get_or_create(
            pk=1,
            defaults={'site_name': 'Django Personal Blog'}
        )
        return config


class MenuItem(models.Model):
    """Navigation menu items."""
    
    class MenuLocation(models.TextChoices):
        HEADER = 'header', _('Header Menu')
        FOOTER = 'footer', _('Footer Menu')
        SIDEBAR = 'sidebar', _('Sidebar Menu')
    
    title = models.CharField(max_length=100)
    url = models.CharField(max_length=200, help_text=_('URL or path'))
    location = models.CharField(max_length=20, choices=MenuLocation.choices)
    
    # Hierarchy
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    
    # Display options
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=False)
    
    # Styling
    css_class = models.CharField(max_length=50, blank=True)
    icon_class = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_menu_item'
        verbose_name = _('Menu Item')
        verbose_name_plural = _('Menu Items')
        ordering = ['location', 'order', 'title']
        indexes = [
            models.Index(fields=['location', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.location})"


class Redirect(models.Model):
    """URL redirects for SEO and maintenance."""
    
    class RedirectType(models.TextChoices):
        PERMANENT = '301', _('301 Permanent')
        TEMPORARY = '302', _('302 Temporary')
    
    old_path = models.CharField(max_length=200, unique=True)
    new_path = models.CharField(max_length=200)
    redirect_type = models.CharField(
        max_length=3, 
        choices=RedirectType.choices, 
        default=RedirectType.PERMANENT
    )
    
    is_active = models.BooleanField(default=True)
    hit_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_redirect'
        verbose_name = _('Redirect')
        verbose_name_plural = _('Redirects')
        indexes = [
            models.Index(fields=['old_path']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.old_path} → {self.new_path}"


class APIKey(models.Model):
    """API keys for external integrations."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=255, unique=True)
    
    # Permissions
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    is_active = models.BooleanField(default=True)
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Rate limiting
    rate_limit = models.PositiveIntegerField(default=1000, help_text=_('Requests per hour'))
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_api_key'
        verbose_name = _('API Key')
        verbose_name_plural = _('API Keys')
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        if not self.key:
            import secrets
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if API key is valid and not expired."""
        if not self.is_active:
            return False
        
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() < self.expires_at
        
        return True
    
    def increment_usage(self):
        """Increment usage count and update last used."""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class AuditLog(models.Model):
    """Audit log for tracking important actions."""
    
    class ActionType(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        PERMISSION_CHANGE = 'permission_change', _('Permission Change')
        SECURITY_EVENT = 'security_event', _('Security Event')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action details
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    object_type = models.CharField(max_length=50, blank=True)  # Model name
    object_id = models.CharField(max_length=100, blank=True)  # Object ID
    description = models.TextField()
    
    # User and request info
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Additional data
    extra_data = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_audit_log'
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else 'Anonymous'
        return f"{user_info} {self.action_type} {self.object_type} at {self.timestamp}"


class CacheInvalidation(models.Model):
    """Track cache invalidation events."""
    
    cache_key = models.CharField(max_length=255)
    cache_pattern = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=100)
    
    # Metadata
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    object_type = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_cache_invalidation'
        verbose_name = _('Cache Invalidation')
        verbose_name_plural = _('Cache Invalidations')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Cache invalidation: {self.cache_key} ({self.reason})"


class WebSocketConnection(models.Model):
    """Track WebSocket connections for monitoring and debugging."""
    
    class ActionType(models.TextChoices):
        CONNECTED = 'connected', _('Connected')
        DISCONNECTED = 'disconnected', _('Disconnected')
        ERROR = 'error', _('Error')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Connection details
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    channel_name = models.CharField(max_length=255)
    consumer_class = models.CharField(max_length=100)
    
    # Action info
    action = models.CharField(max_length=20, choices=ActionType.choices)
    close_code = models.IntegerField(null=True, blank=True)
    
    # Timing
    connection_time = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional data
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'core_websocket_connection'
        verbose_name = _('WebSocket Connection')
        verbose_name_plural = _('WebSocket Connections')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['consumer_class']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else 'Anonymous'
        return f"{user_info} {self.action} {self.consumer_class} at {self.timestamp}"


class NotificationTemplate(models.Model):
    """Templates for WebSocket notifications."""
    
    class NotificationType(models.TextChoices):
        BLOG_POST_PUBLISHED = 'blog_post_published', _('Blog Post Published')
        COMMENT_ADDED = 'comment_added', _('Comment Added')
        USER_MENTIONED = 'user_mentioned', _('User Mentioned')
        NEWSLETTER_SENT = 'newsletter_sent', _('Newsletter Sent')
        SYSTEM_ALERT = 'system_alert', _('System Alert')
    
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices, unique=True)
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Display options
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=20, blank=True)
    sound = models.CharField(max_length=50, blank=True)
    
    # Behavior
    is_active = models.BooleanField(default=True)
    auto_dismiss_seconds = models.PositiveIntegerField(default=0, help_text=_('0 = no auto dismiss'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_notification_template'
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
    
    def __str__(self):
        return f"{self.get_notification_type_display()}"
    
    def render(self, context):
        """Render notification with context data."""
        from django.template import Template, Context
        
        title = Template(self.title_template).render(Context(context))
        message = Template(self.message_template).render(Context(context))
        
        return {
            'title': title,
            'message': message,
            'icon': self.icon,
            'color': self.color,
            'sound': self.sound,
            'auto_dismiss_seconds': self.auto_dismiss_seconds
        }