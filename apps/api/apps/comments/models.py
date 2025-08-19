"""
Comments Models
Handles blog post comments and replies.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

User = get_user_model()


class CommentManager(models.Manager):
    """Custom manager for Comment model."""
    
    def approved(self):
        """Get approved comments."""
        return self.filter(is_approved=True)
    
    def pending(self):
        """Get pending comments."""
        return self.filter(is_approved=False, is_spam=False)
    
    def spam(self):
        """Get spam comments."""
        return self.filter(is_spam=True)


class Comment(models.Model):
    """Blog post comment model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content
    content = models.TextField(max_length=1000, help_text=_('Comment content'))
    
    # Relationships
    post = models.ForeignKey(
        'blog.Post', 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments',
        null=True,
        blank=True
    )
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    
    # Guest user fields (for non-authenticated users)
    guest_name = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_website = models.URLField(blank=True)
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    
    # Metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    objects = CommentManager()
    
    class Meta:
        db_table = 'blog_comment'
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'is_approved']),
            models.Index(fields=['author']),
            models.Index(fields=['parent']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        author_name = self.get_author_name()
        return f"Comment by {author_name} on {self.post.title}"
    
    def save(self, *args, **kwargs):
        # Auto-approve comments from staff users
        if self.author and self.author.is_staff and not self.is_approved:
            self.is_approved = True
            self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return f"{self.post.get_absolute_url()}#comment-{self.id}"
    
    def get_author_name(self):
        """Get the display name for the comment author."""
        if self.author:
            return self.author.get_full_name() or self.author.username
        return self.guest_name or 'Anonymous'
    
    def get_author_email(self):
        """Get the email for the comment author."""
        if self.author:
            return self.author.email
        return self.guest_email
    
    def get_author_website(self):
        """Get the website for the comment author."""
        if self.author and hasattr(self.author, 'profile'):
            return self.author.profile.website
        return self.guest_website
    
    @property
    def is_reply(self):
        """Check if this comment is a reply to another comment."""
        return self.parent is not None
    
    @property
    def reply_count(self):
        """Get number of approved replies."""
        return self.replies.filter(is_approved=True).count()
    
    def get_replies(self):
        """Get approved replies to this comment."""
        return self.replies.approved().order_by('created_at')
    
    def approve(self):
        """Approve the comment."""
        self.is_approved = True
        self.approved_at = timezone.now()
        self.is_spam = False
        self.save()
    
    def mark_as_spam(self):
        """Mark comment as spam."""
        self.is_spam = True
        self.is_approved = False
        self.save()
    
    def can_be_edited_by(self, user):
        """Check if user can edit this comment."""
        if not user.is_authenticated:
            return False
        
        # Author can edit within 15 minutes
        if self.author == user:
            from datetime import timedelta
            edit_window = timedelta(minutes=15)
            return timezone.now() - self.created_at < edit_window
        
        # Staff can always edit
        return user.is_staff


class CommentLike(models.Model):
    """Comment likes/dislikes."""
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_like = models.BooleanField(default=True)  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blog_comment_like'
        verbose_name = _('Comment Like')
        verbose_name_plural = _('Comment Likes')
        unique_together = ['comment', 'user']
        indexes = [
            models.Index(fields=['comment', 'is_like']),
        ]
    
    def __str__(self):
        action = 'liked' if self.is_like else 'disliked'
        return f"{self.user.username} {action} comment {self.comment.id}"


class CommentReport(models.Model):
    """Comment reports for moderation."""
    
    class ReportReason(models.TextChoices):
        SPAM = 'spam', _('Spam')
        INAPPROPRIATE = 'inappropriate', _('Inappropriate Content')
        HARASSMENT = 'harassment', _('Harassment')
        OFF_TOPIC = 'off_topic', _('Off Topic')
        OTHER = 'other', _('Other')
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=ReportReason.choices)
    description = models.TextField(blank=True)
    
    # Moderation
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='resolved_reports'
    )
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'blog_comment_report'
        verbose_name = _('Comment Report')
        verbose_name_plural = _('Comment Reports')
        unique_together = ['comment', 'reporter']
        indexes = [
            models.Index(fields=['comment', 'is_resolved']),
            models.Index(fields=['reporter']),
        ]
    
    def __str__(self):
        return f"Report on comment {self.comment.id} by {self.reporter.username}"
    
    def resolve(self, resolved_by, notes=''):
        """Resolve the report."""
        self.is_resolved = True
        self.resolved_by = resolved_by
        self.resolution_notes = notes
        self.resolved_at = timezone.now()
        self.save()


class CommentModerationLog(models.Model):
    """Log of comment moderation actions."""
    
    class ModerationAction(models.TextChoices):
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        MARKED_SPAM = 'marked_spam', _('Marked as Spam')
        EDITED = 'edited', _('Edited')
        DELETED = 'deleted', _('Deleted')
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='moderation_logs')
    moderator = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ModerationAction.choices)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blog_comment_moderation_log'
        verbose_name = _('Comment Moderation Log')
        verbose_name_plural = _('Comment Moderation Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['comment']),
            models.Index(fields=['moderator']),
        ]
    
    def __str__(self):
        return f"{self.moderator.username} {self.action} comment {self.comment.id}"