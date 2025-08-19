"""
Management command to create initial notification templates
"""

from django.core.management.base import BaseCommand
from apps.core.models import NotificationTemplate


class Command(BaseCommand):
    help = 'Create initial notification templates for WebSocket notifications'
    
    def handle(self, *args, **options):
        templates = [
            {
                'notification_type': 'blog_post_published',
                'title_template': 'New Post: {{ title }}',
                'message_template': '{{ author }} published a new post: {{ title }}',
                'icon': 'post',
                'color': 'blue',
                'sound': 'notification',
                'auto_dismiss_seconds': 5
            },
            {
                'notification_type': 'comment_added',
                'title_template': 'New Comment',
                'message_template': '{{ commenter }} commented on "{{ post_title }}"',
                'icon': 'comment',
                'color': 'green',
                'sound': 'message',
                'auto_dismiss_seconds': 0
            },
            {
                'notification_type': 'user_mentioned',
                'title_template': 'You were mentioned',
                'message_template': '{{ mentioned_by }} mentioned you in a {{ content_type }}',
                'icon': 'mention',
                'color': 'orange',
                'sound': 'alert',
                'auto_dismiss_seconds': 0
            },
            {
                'notification_type': 'newsletter_sent',
                'title_template': 'Newsletter Sent',
                'message_template': 'Newsletter "{{ subject }}" was sent to {{ recipient_count }} subscribers',
                'icon': 'newsletter',
                'color': 'purple',
                'sound': 'success',
                'auto_dismiss_seconds': 3
            },
            {
                'notification_type': 'system_alert',
                'title_template': 'System Alert',
                'message_template': '{{ message }}',
                'icon': 'alert',
                'color': 'red',
                'sound': 'warning',
                'auto_dismiss_seconds': 0
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = NotificationTemplate.objects.update_or_create(
                notification_type=template_data['notification_type'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created notification template: {template.notification_type}'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated notification template: {template.notification_type}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new templates, '
                f'updated {updated_count} existing templates.'
            )
        )