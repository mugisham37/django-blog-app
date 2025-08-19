"""
Comments admin configuration
"""

from django.contrib import admin
from django.utils.html import format_html, strip_tags
from .models import Comment, CommentLike, CommentReport, CommentModerationLog


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Comment admin."""
    
    list_display = ('content_preview', 'author_display', 'post', 'is_approved', 'is_spam', 'created_at')
    list_filter = ('is_approved', 'is_spam', 'is_edited', 'created_at', 'post__category')
    search_fields = ('content', 'author__username', 'guest_name', 'guest_email', 'post__title')
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent', 'reply_count')
    
    fieldsets = (
        (None, {
            'fields': ('post', 'content', 'parent')
        }),
        ('Author', {
            'fields': ('author', 'guest_name', 'guest_email', 'guest_website')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_spam', 'is_edited', 'approved_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'reply_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_comments', 'mark_as_spam', 'mark_as_not_spam']
    
    def content_preview(self, obj):
        """Show preview of comment content."""
        content = strip_tags(obj.content)
        return content[:50] + '...' if len(content) > 50 else content
    content_preview.short_description = 'Content'
    
    def author_display(self, obj):
        """Display author name."""
        return obj.get_author_name()
    author_display.short_description = 'Author'
    
    def approve_comments(self, request, queryset):
        """Approve selected comments."""
        count = 0
        for comment in queryset:
            if not comment.is_approved:
                comment.approve()
                count += 1
        
        self.message_user(request, f'{count} comments approved.')
    approve_comments.short_description = 'Approve selected comments'
    
    def mark_as_spam(self, request, queryset):
        """Mark selected comments as spam."""
        count = 0
        for comment in queryset:
            if not comment.is_spam:
                comment.mark_as_spam()
                count += 1
        
        self.message_user(request, f'{count} comments marked as spam.')
    mark_as_spam.short_description = 'Mark as spam'
    
    def mark_as_not_spam(self, request, queryset):
        """Mark selected comments as not spam."""
        count = queryset.filter(is_spam=True).update(is_spam=False)
        self.message_user(request, f'{count} comments unmarked as spam.')
    mark_as_not_spam.short_description = 'Mark as not spam'


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    """Comment like admin."""
    
    list_display = ('comment_preview', 'user', 'is_like', 'created_at')
    list_filter = ('is_like', 'created_at')
    search_fields = ('comment__content', 'user__username')
    readonly_fields = ('created_at',)
    
    def comment_preview(self, obj):
        """Show preview of comment."""
        content = strip_tags(obj.comment.content)
        return content[:30] + '...' if len(content) > 30 else content
    comment_preview.short_description = 'Comment'
    
    def has_add_permission(self, request):
        return False


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    """Comment report admin."""
    
    list_display = ('comment_preview', 'reporter', 'reason', 'is_resolved', 'created_at')
    list_filter = ('reason', 'is_resolved', 'created_at')
    search_fields = ('comment__content', 'reporter__username', 'description')
    readonly_fields = ('created_at', 'resolved_at')
    
    fieldsets = (
        (None, {
            'fields': ('comment', 'reporter', 'reason', 'description')
        }),
        ('Resolution', {
            'fields': ('is_resolved', 'resolved_by', 'resolution_notes', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['resolve_reports']
    
    def comment_preview(self, obj):
        """Show preview of reported comment."""
        content = strip_tags(obj.comment.content)
        return content[:30] + '...' if len(content) > 30 else content
    comment_preview.short_description = 'Comment'
    
    def resolve_reports(self, request, queryset):
        """Resolve selected reports."""
        count = 0
        for report in queryset.filter(is_resolved=False):
            report.resolve(request.user, 'Resolved via admin action')
            count += 1
        
        self.message_user(request, f'{count} reports resolved.')
    resolve_reports.short_description = 'Resolve selected reports'


@admin.register(CommentModerationLog)
class CommentModerationLogAdmin(admin.ModelAdmin):
    """Comment moderation log admin."""
    
    list_display = ('comment_preview', 'moderator', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('comment__content', 'moderator__username', 'notes')
    readonly_fields = ('timestamp',)
    
    def comment_preview(self, obj):
        """Show preview of comment."""
        content = strip_tags(obj.comment.content)
        return content[:30] + '...' if len(content) > 30 else content
    comment_preview.short_description = 'Comment'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False