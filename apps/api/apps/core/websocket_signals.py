"""
WebSocket signal handlers for real-time notifications
"""

import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def broadcast_to_group(group_name, message_type, data):
    """Broadcast message to WebSocket group."""
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': message_type,
                'data': data
            }
        )


def broadcast_notification(notification_type, data, user_id=None):
    """Broadcast notification to users."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    # Broadcast to general notifications group
    async_to_sync(channel_layer.group_send)(
        f'notifications_{notification_type}',
        {
            'type': 'notification_message',
            'data': {
                'notification_type': notification_type,
                'data': data
            }
        }
    )
    
    # Broadcast to specific user if provided
    if user_id:
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'data': {
                    'notification_type': notification_type,
                    'data': data
                }
            }
        )


# Blog post signals
@receiver(post_save, sender='blog.Post')
def handle_post_save(sender, instance, created, **kwargs):
    """Handle post save events."""
    from django.utils import timezone
    
    if created and instance.status == 'published':
        # New post published
        data = {
            'id': str(instance.id),
            'title': instance.title,
            'slug': instance.slug,
            'author': instance.author.username,
            'published_at': instance.published_at.isoformat() if instance.published_at else timezone.now().isoformat(),
            'excerpt': instance.excerpt or instance.content[:200] + '...' if len(instance.content) > 200 else instance.content
        }
        
        # Broadcast to post group
        broadcast_to_group(f'post_{instance.id}', 'post_published', data)
        
        # Broadcast general notification
        broadcast_notification('blog_post_published', data)
        
    elif not created:
        # Post updated
        data = {
            'id': str(instance.id),
            'title': instance.title,
            'slug': instance.slug,
            'updated_at': instance.updated_at.isoformat(),
            'status': instance.status
        }
        
        # Broadcast to post group
        broadcast_to_group(f'post_{instance.id}', 'post_update', data)


# Comment signals
@receiver(post_save, sender='comments.Comment')
def handle_comment_save(sender, instance, created, **kwargs):
    """Handle comment save events."""
    if created:
        # New comment added
        data = {
            'id': str(instance.id),
            'post_id': str(instance.post.id),
            'content': instance.content,
            'author': instance.author.username if instance.author else 'Anonymous',
            'created_at': instance.created_at.isoformat(),
            'is_approved': instance.is_approved
        }
        
        # Broadcast to comments group
        broadcast_to_group(f'comments_{instance.post.id}', 'comment_added', data)
        
        # Notify post author if different from comment author
        if instance.post.author != instance.author and instance.is_approved:
            notification_data = {
                'comment_id': str(instance.id),
                'post_title': instance.post.title,
                'post_slug': instance.post.slug,
                'commenter': instance.author.username if instance.author else 'Anonymous',
                'comment_excerpt': instance.content[:100] + '...' if len(instance.content) > 100 else instance.content
            }
            broadcast_notification('comment_added', notification_data, instance.post.author.id)
    
    elif instance.is_approved and not getattr(instance, '_was_approved', False):
        # Comment approved
        data = {
            'id': str(instance.id),
            'post_id': str(instance.post.id),
            'is_approved': True
        }
        
        # Broadcast to comments group
        broadcast_to_group(f'comments_{instance.post.id}', 'comment_approved', data)
        
        # Notify comment author
        if instance.author:
            notification_data = {
                'comment_id': str(instance.id),
                'post_title': instance.post.title,
                'post_slug': instance.post.slug
            }
            broadcast_notification('comment_approved', notification_data, instance.author.id)


@receiver(post_delete, sender='comments.Comment')
def handle_comment_delete(sender, instance, **kwargs):
    """Handle comment delete events."""
    data = {
        'id': str(instance.id),
        'post_id': str(instance.post.id)
    }
    
    # Broadcast to comments group
    broadcast_to_group(f'comments_{instance.post.id}', 'comment_deleted', data)


# Analytics signals
@receiver(post_save, sender='analytics.PageView')
def handle_page_view(sender, instance, created, **kwargs):
    """Handle page view events for real-time analytics."""
    if created and hasattr(instance, 'post') and instance.post:
        # Update post stats
        post_stats = {
            'post_id': str(instance.post.id),
            'view_count': getattr(instance.post, 'view_count', 0),
            'timestamp': instance.timestamp.isoformat()
        }
        
        # Broadcast to post group
        broadcast_to_group(f'post_{instance.post.id}', 'post_stats_update', post_stats)
        
        # Broadcast to analytics dashboard
        broadcast_to_group('analytics_dashboard', 'analytics_update', {
            'type': 'page_view',
            'data': post_stats
        })


# User mention signals (if implemented)
def handle_user_mention(mentioned_user, content_type, object_id, mentioner):
    """Handle user mention notifications."""
    data = {
        'mentioned_by': mentioner.username,
        'content_type': content_type,
        'object_id': str(object_id),
        'timestamp': timezone.now().isoformat()
    }
    
    broadcast_notification('user_mentioned', data, mentioned_user.id)


# Newsletter signals (commented out until Newsletter model is properly defined)
# @receiver(post_save, sender='newsletter.Newsletter')
# def handle_newsletter_sent(sender, instance, created, **kwargs):
#     """Handle newsletter sent events."""
#     if instance.status == 'sent' and not getattr(instance, '_was_sent', False):
#         data = {
#             'newsletter_id': str(instance.id),
#             'subject': instance.subject,
#             'sent_at': instance.sent_at.isoformat() if instance.sent_at else None,
#             'recipient_count': instance.subscribers.count()
#         }
#         
#         # Broadcast to admin users
#         broadcast_notification('newsletter_sent', data)


# System alert function
def broadcast_system_alert(alert_type, message, level='info'):
    """Broadcast system-wide alerts."""
    from django.utils import timezone
    
    data = {
        'alert_type': alert_type,
        'message': message,
        'level': level,
        'timestamp': timezone.now().isoformat()
    }
    
    broadcast_notification('system_alert', data)