"""
Newsletter Models
Handles newsletter subscriptions and campaigns.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
import uuid

User = get_user_model()


class SubscriberManager(models.Manager):
    """Custom manager for Subscriber model."""
    
    def active(self):
        """Get active subscribers."""
        return self.filter(is_active=True, email_verified=True)
    
    def by_frequency(self, frequency):
        """Get subscribers by frequency preference."""
        return self.active().filter(frequency=frequency)


class Subscriber(models.Model):
    """Newsletter subscriber model."""
    
    class Frequency(models.TextChoices):
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
        NEVER = 'never', _('Never')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    
    # Optional user link
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='newsletter_subscription'
    )
    
    # Subscription preferences
    frequency = models.CharField(
        max_length=20, 
        choices=Frequency.choices, 
        default=Frequency.WEEKLY
    )
    categories = models.ManyToManyField(
        'blog.Category', 
        blank=True,
        help_text=_('Categories to receive updates about')
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    source = models.CharField(max_length=100, blank=True)  # Where they subscribed from
    
    # Verification
    verification_token = models.CharField(max_length=255, blank=True)
    verification_sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Unsubscription
    unsubscribe_token = models.CharField(max_length=255, unique=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    unsubscribe_reason = models.TextField(blank=True)
    
    # Timestamps
    subscribed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = SubscriberManager()
    
    class Meta:
        db_table = 'newsletter_subscriber'
        verbose_name = _('Subscriber')
        verbose_name_plural = _('Subscribers')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'email_verified']),
            models.Index(fields=['frequency']),
        ]
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            import secrets
            self.unsubscribe_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def verify_email(self):
        """Verify the subscriber's email."""
        self.email_verified = True
        self.verified_at = timezone.now()
        self.verification_token = ''
        self.save()
    
    def unsubscribe(self, reason=''):
        """Unsubscribe the user."""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.unsubscribe_reason = reason
        self.save()
    
    def resubscribe(self):
        """Resubscribe the user."""
        self.is_active = True
        self.unsubscribed_at = None
        self.unsubscribe_reason = ''
        self.save()


class Campaign(models.Model):
    """Newsletter campaign model."""
    
    class CampaignType(models.TextChoices):
        NEWSLETTER = 'newsletter', _('Newsletter')
        ANNOUNCEMENT = 'announcement', _('Announcement')
        DIGEST = 'digest', _('Digest')
        PROMOTIONAL = 'promotional', _('Promotional')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        SCHEDULED = 'scheduled', _('Scheduled')
        SENDING = 'sending', _('Sending')
        SENT = 'sent', _('Sent')
        CANCELLED = 'cancelled', _('Cancelled')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=200)
    
    # Content
    content_html = RichTextUploadingField()
    content_text = models.TextField(help_text=_('Plain text version'))
    
    # Campaign settings
    campaign_type = models.CharField(max_length=20, choices=CampaignType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    
    # Targeting
    target_frequency = models.CharField(
        max_length=20, 
        choices=Subscriber.Frequency.choices,
        null=True,
        blank=True,
        help_text=_('Send to subscribers with this frequency preference')
    )
    target_categories = models.ManyToManyField(
        'blog.Category',
        blank=True,
        help_text=_('Send to subscribers interested in these categories')
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_recipients = models.PositiveIntegerField(default=0)
    emails_sent = models.PositiveIntegerField(default=0)
    emails_delivered = models.PositiveIntegerField(default=0)
    emails_opened = models.PositiveIntegerField(default=0)
    emails_clicked = models.PositiveIntegerField(default=0)
    emails_bounced = models.PositiveIntegerField(default=0)
    emails_unsubscribed = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'newsletter_campaign'
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['campaign_type']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def open_rate(self):
        """Calculate email open rate."""
        if self.emails_delivered == 0:
            return 0
        return (self.emails_opened / self.emails_delivered) * 100
    
    @property
    def click_rate(self):
        """Calculate email click rate."""
        if self.emails_delivered == 0:
            return 0
        return (self.emails_clicked / self.emails_delivered) * 100
    
    @property
    def bounce_rate(self):
        """Calculate email bounce rate."""
        if self.emails_sent == 0:
            return 0
        return (self.emails_bounced / self.emails_sent) * 100
    
    def get_target_subscribers(self):
        """Get subscribers that match the campaign targeting."""
        queryset = Subscriber.objects.active()
        
        if self.target_frequency:
            queryset = queryset.filter(frequency=self.target_frequency)
        
        if self.target_categories.exists():
            queryset = queryset.filter(categories__in=self.target_categories.all()).distinct()
        
        return queryset


class EmailLog(models.Model):
    """Log of individual email sends."""
    
    class Status(models.TextChoices):
        QUEUED = 'queued', _('Queued')
        SENT = 'sent', _('Sent')
        DELIVERED = 'delivered', _('Delivered')
        OPENED = 'opened', _('Opened')
        CLICKED = 'clicked', _('Clicked')
        BOUNCED = 'bounced', _('Bounced')
        COMPLAINED = 'complained', _('Complained')
        UNSUBSCRIBED = 'unsubscribed', _('Unsubscribed')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='email_logs')
    subscriber = models.ForeignKey(Subscriber, on_delete=models.CASCADE, related_name='email_logs')
    
    # Email details
    email_address = models.EmailField()
    subject = models.CharField(max_length=200)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    
    # Timestamps
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(blank=True)
    bounce_reason = models.TextField(blank=True)
    
    # Tracking
    tracking_id = models.CharField(max_length=255, unique=True)
    
    class Meta:
        db_table = 'newsletter_email_log'
        verbose_name = _('Email Log')
        verbose_name_plural = _('Email Logs')
        indexes = [
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['subscriber']),
            models.Index(fields=['tracking_id']),
        ]
    
    def __str__(self):
        return f"Email to {self.email_address} for {self.campaign.name}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_id:
            import secrets
            self.tracking_id = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)


class EmailTemplate(models.Model):
    """Reusable email templates."""
    
    class TemplateType(models.TextChoices):
        NEWSLETTER = 'newsletter', _('Newsletter')
        WELCOME = 'welcome', _('Welcome')
        VERIFICATION = 'verification', _('Email Verification')
        UNSUBSCRIBE = 'unsubscribe', _('Unsubscribe Confirmation')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TemplateType.choices)
    
    # Template content
    subject_template = models.CharField(max_length=200)
    html_template = models.TextField()
    text_template = models.TextField()
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'newsletter_email_template'
        verbose_name = _('Email Template')
        verbose_name_plural = _('Email Templates')
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
        ]
    
    def __str__(self):
        return self.name


class ClickTracking(models.Model):
    """Track clicks in newsletter emails."""
    
    email_log = models.ForeignKey(EmailLog, on_delete=models.CASCADE, related_name='clicks')
    url = models.URLField(max_length=500)
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    class Meta:
        db_table = 'newsletter_click_tracking'
        verbose_name = _('Click Tracking')
        verbose_name_plural = _('Click Tracking')
        indexes = [
            models.Index(fields=['email_log']),
            models.Index(fields=['clicked_at']),
        ]
    
    def __str__(self):
        return f"Click on {self.url} at {self.clicked_at}"