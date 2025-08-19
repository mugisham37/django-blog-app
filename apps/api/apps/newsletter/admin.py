"""
Newsletter admin configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Subscriber, Campaign, EmailLog, EmailTemplate, ClickTracking
)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    """Subscriber admin."""
    
    list_display = ('email', 'frequency', 'is_active', 'email_verified', 'source', 'subscribed_at')
    list_filter = ('frequency', 'is_active', 'email_verified', 'source', 'subscribed_at')
    search_fields = ('email', 'user__username')
    readonly_fields = ('subscribed_at', 'updated_at', 'verification_token', 'unsubscribe_token')
    filter_horizontal = ('categories',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'user', 'frequency', 'categories')
        }),
        ('Status', {
            'fields': ('is_active', 'email_verified', 'verified_at')
        }),
        ('Metadata', {
            'fields': ('source', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('verification_token', 'verification_sent_at'),
            'classes': ('collapse',)
        }),
        ('Unsubscription', {
            'fields': ('unsubscribe_token', 'unsubscribed_at', 'unsubscribe_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_subscribers', 'deactivate_subscribers', 'verify_emails']
    
    def activate_subscribers(self, request, queryset):
        """Activate selected subscribers."""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} subscribers activated.')
    activate_subscribers.short_description = 'Activate selected subscribers'
    
    def deactivate_subscribers(self, request, queryset):
        """Deactivate selected subscribers."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} subscribers deactivated.')
    deactivate_subscribers.short_description = 'Deactivate selected subscribers'
    
    def verify_emails(self, request, queryset):
        """Verify emails for selected subscribers."""
        count = 0
        for subscriber in queryset.filter(email_verified=False):
            subscriber.verify_email()
            count += 1
        self.message_user(request, f'{count} emails verified.')
    verify_emails.short_description = 'Verify selected emails'


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """Campaign admin."""
    
    list_display = ('name', 'campaign_type', 'status', 'total_recipients', 'open_rate_display', 'click_rate_display', 'scheduled_at')
    list_filter = ('campaign_type', 'status', 'created_at', 'scheduled_at')
    search_fields = ('name', 'subject')
    readonly_fields = (
        'total_recipients', 'emails_sent', 'emails_delivered', 'emails_opened',
        'emails_clicked', 'emails_bounced', 'emails_unsubscribed',
        'open_rate', 'click_rate', 'bounce_rate', 'created_at', 'updated_at'
    )
    filter_horizontal = ('target_categories',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'subject', 'campaign_type', 'status')
        }),
        ('Content', {
            'fields': ('content_html', 'content_text')
        }),
        ('Targeting', {
            'fields': ('target_frequency', 'target_categories')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'sent_at')
        }),
        ('Statistics', {
            'fields': (
                'total_recipients', 'emails_sent', 'emails_delivered',
                'emails_opened', 'emails_clicked', 'emails_bounced',
                'emails_unsubscribed', 'open_rate', 'click_rate', 'bounce_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def open_rate_display(self, obj):
        """Display open rate as percentage."""
        return f"{obj.open_rate:.1f}%"
    open_rate_display.short_description = 'Open Rate'
    
    def click_rate_display(self, obj):
        """Display click rate as percentage."""
        return f"{obj.click_rate:.1f}%"
    click_rate_display.short_description = 'Click Rate'
    
    def save_model(self, request, obj, form, change):
        """Set creator if not set."""
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Email log admin."""
    
    list_display = ('email_address', 'campaign', 'status', 'sent_at', 'opened_at', 'clicked_at')
    list_filter = ('status', 'campaign', 'sent_at', 'opened_at')
    search_fields = ('email_address', 'campaign__name', 'subject')
    readonly_fields = (
        'tracking_id', 'queued_at', 'sent_at', 'delivered_at',
        'opened_at', 'clicked_at'
    )
    
    fieldsets = (
        (None, {
            'fields': ('campaign', 'subscriber', 'email_address', 'subject', 'status')
        }),
        ('Tracking', {
            'fields': ('tracking_id',)
        }),
        ('Timeline', {
            'fields': ('queued_at', 'sent_at', 'delivered_at', 'opened_at', 'clicked_at'),
            'classes': ('collapse',)
        }),
        ('Errors', {
            'fields': ('error_message', 'bounce_reason'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Email template admin."""
    
    list_display = ('name', 'template_type', 'is_active', 'is_default', 'created_at')
    list_filter = ('template_type', 'is_active', 'is_default', 'created_at')
    search_fields = ('name', 'subject_template')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template_type', 'is_active', 'is_default')
        }),
        ('Templates', {
            'fields': ('subject_template', 'html_template', 'text_template')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Set creator if not set."""
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClickTracking)
class ClickTrackingAdmin(admin.ModelAdmin):
    """Click tracking admin."""
    
    list_display = ('email_log', 'url_display', 'clicked_at', 'ip_address')
    list_filter = ('clicked_at',)
    search_fields = ('url', 'email_log__email_address')
    readonly_fields = ('clicked_at',)
    
    def url_display(self, obj):
        """Display shortened URL."""
        return obj.url[:50] + '...' if len(obj.url) > 50 else obj.url
    url_display.short_description = 'URL'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False