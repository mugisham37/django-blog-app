from django.apps import AppConfig


class CommentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comments'
    verbose_name = 'Comments System'
    
    def ready(self):
        """Initialize comment configurations when Django starts."""
        import apps.comments.signals
