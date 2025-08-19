"""
Comment signals for notifications and moderation.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment, CommentModerationLog


@receiver(post_save, sender=Comment)
def log_comment_approval(sender, instance, created, **kwargs):
    """Log when a comment is approved."""
    if not created and instance.is_approved and instance.approved_at:
        # Check if this is a new approval
        if not CommentModerationLog.objects.filter(
            comment=instance,
            action=CommentModerationLog.ModerationAction.APPROVED
        ).exists():
            CommentModerationLog.objects.create(
                comment=instance,
                moderator=instance.author if instance.author and instance.author.is_staff else None,
                action=CommentModerationLog.ModerationAction.APPROVED,
                notes='Auto-approved or manually approved'
            )