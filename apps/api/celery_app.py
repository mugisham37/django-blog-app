"""
Celery configuration for Django Personal Blog System.
Advanced configuration with task queues, monitoring, and failure handling.
"""

import os
import logging
from celery import Celery, signals
from celery.exceptions import Retry
from django.conf import settings
from kombu import Queue, Exchange

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('personal_blog')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure task queues with different priorities
app.conf.task_routes = {
    # High priority tasks (critical operations)
    'apps.blog.tasks.publish_scheduled_posts': {'queue': 'high_priority'},
    'apps.core.tasks.send_critical_notification': {'queue': 'high_priority'},
    'apps.accounts.tasks.send_password_reset_email': {'queue': 'high_priority'},
    
    # Medium priority tasks (user-facing operations)
    'apps.comments.tasks.send_comment_notification': {'queue': 'medium_priority'},
    'apps.blog.tasks.process_post_images': {'queue': 'medium_priority'},
    'apps.accounts.tasks.send_welcome_email': {'queue': 'medium_priority'},
    
    # Low priority tasks (background processing)
    'apps.analytics.tasks.update_analytics': {'queue': 'low_priority'},
    'apps.core.tasks.cleanup_old_sessions': {'queue': 'low_priority'},
    'apps.blog.tasks.cleanup_expired_preview_tokens': {'queue': 'low_priority'},
    'apps.analytics.tasks.aggregate_daily_stats': {'queue': 'low_priority'},
}

# Define task queues with different priorities
app.conf.task_default_queue = 'medium_priority'
app.conf.task_queues = (
    Queue('high_priority', Exchange('high_priority'), routing_key='high_priority', 
          queue_arguments={'x-max-priority': 10}),
    Queue('medium_priority', Exchange('medium_priority'), routing_key='medium_priority',
          queue_arguments={'x-max-priority': 5}),
    Queue('low_priority', Exchange('low_priority'), routing_key='low_priority',
          queue_arguments={'x-max-priority': 1}),
    Queue('celery', Exchange('celery'), routing_key='celery'),  # Default queue
)

# Task execution configuration
app.conf.update(
    # Task result backend
    result_backend='redis://localhost:6379/1',
    result_expires=3600,  # Results expire after 1 hour
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Task execution settings
    task_always_eager=False,
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task routing and priority
    task_inherit_parent_priority=True,
    task_default_priority=5,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'publish-scheduled-posts': {
        'task': 'apps.blog.tasks.publish_scheduled_posts',
        'schedule': 60.0,  # Run every minute
        'options': {'queue': 'high_priority', 'priority': 9}
    },
    'update-analytics': {
        'task': 'apps.analytics.tasks.update_analytics',
        'schedule': 300.0,  # Run every 5 minutes
        'options': {'queue': 'low_priority', 'priority': 1}
    },
    'cleanup-old-sessions': {
        'task': 'apps.core.tasks.cleanup_old_sessions',
        'schedule': 3600.0,  # Run every hour
        'options': {'queue': 'low_priority', 'priority': 1}
    },
    'cleanup-expired-preview-tokens': {
        'task': 'apps.blog.tasks.cleanup_expired_preview_tokens',
        'schedule': 1800.0,  # Run every 30 minutes
        'options': {'queue': 'low_priority', 'priority': 1}
    },
    'aggregate-daily-analytics': {
        'task': 'apps.analytics.tasks.aggregate_daily_stats',
        'schedule': 86400.0,  # Run daily
        'options': {'queue': 'low_priority', 'priority': 1}
    },
    'cleanup-failed-tasks': {
        'task': 'apps.core.tasks.cleanup_failed_tasks',
        'schedule': 3600.0,  # Run every hour
        'options': {'queue': 'low_priority', 'priority': 1}
    },
}

app.conf.timezone = 'UTC'

# Configure logging for Celery
logger = logging.getLogger(__name__)

# Task failure handling
@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Handle task failures with logging and notification."""
    logger.error(
        f"Task {sender.name} [{task_id}] failed: {exception}",
        extra={
            'task_id': task_id,
            'task_name': sender.name,
            'exception': str(exception),
            'traceback': traceback,
        }
    )
    
    # Send critical failure notifications for high-priority tasks
    if hasattr(sender, 'request') and sender.request.get('queue') == 'high_priority':
        from apps.core.tasks import send_critical_notification
        send_critical_notification.delay(
            subject=f"Critical Task Failure: {sender.name}",
            message=f"Task {task_id} failed with exception: {exception}",
            task_id=task_id
        )

# Task retry handling
@signals.task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwargs):
    """Handle task retries with logging."""
    logger.warning(
        f"Task {sender.name} [{task_id}] retry: {reason}",
        extra={
            'task_id': task_id,
            'task_name': sender.name,
            'retry_reason': str(reason),
        }
    )

# Task success handling
@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Handle successful task completion."""
    logger.info(f"Task {sender.name} completed successfully")

# Worker ready signal
@signals.worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    logger.info(f"Celery worker {sender.hostname} is ready")

# Worker shutdown signal
@signals.worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Handle worker shutdown signal."""
    logger.info(f"Celery worker {sender.hostname} is shutting down")


# Custom task base class with retry logic
class BaseTaskWithRetry(app.Task):
    """Base task class with exponential backoff retry logic."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False
    
    def retry(self, args=None, kwargs=None, exc=None, throw=True, eta=None, countdown=None, max_retries=None, **options):
        """Custom retry method with exponential backoff."""
        if countdown is None and eta is None:
            # Calculate exponential backoff: 2^retry_count * 60 seconds
            retry_count = self.request.retries
            countdown = min(60 * (2 ** retry_count), self.retry_backoff_max)
            
        logger.warning(
            f"Retrying task {self.name} in {countdown} seconds (attempt {self.request.retries + 1})",
            extra={
                'task_id': self.request.id,
                'task_name': self.name,
                'retry_count': self.request.retries,
                'countdown': countdown,
                'exception': str(exc) if exc else None,
            }
        )
        
        return super().retry(
            args=args, kwargs=kwargs, exc=exc, throw=throw,
            eta=eta, countdown=countdown, max_retries=max_retries, **options
        )


# Set the custom base task class
app.Task = BaseTaskWithRetry


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
    return f'Debug task executed successfully at {self.request.id}'


@app.task(bind=True, queue='high_priority', priority=9)
def health_check_task(self):
    """Health check task for monitoring Celery workers."""
    import time
    from datetime import datetime
    
    start_time = time.time()
    
    # Simulate some work
    time.sleep(1)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'execution_time': execution_time,
        'worker_id': self.request.hostname,
        'task_id': self.request.id,
    }