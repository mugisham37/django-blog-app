from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core System'
    
    def ready(self):
        """Import signal handlers when app is ready."""
        try:
            import apps.core.websocket_signals  # noqa
        except ImportError:
            pass
