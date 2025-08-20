"""
Core views for the Django Personal Blog System.
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """
    Comprehensive health check endpoint for monitoring and load balancers.
    """
    
    def get(self, request):
        """
        Perform health checks on all critical services.
        """
        health_status = {
            'status': 'healthy',
            'timestamp': self._get_timestamp(),
            'checks': {
                'database': self._check_database(),
                'cache': self._check_cache(),
                'redis': self._check_redis(),
            }
        }
        
        # Determine overall health status
        all_healthy = all(check['status'] == 'healthy' for check in health_status['checks'].values())
        health_status['status'] = 'healthy' if all_healthy else 'unhealthy'
        
        # Return appropriate HTTP status code
        status_code = 200 if all_healthy else 503
        
        return JsonResponse(health_status, status=status_code)
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
    
    def _check_database(self):
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
    
    def _check_cache(self):
        """Check Django cache backend."""
        try:
            test_key = 'health_check_test'
            test_value = 'test_value'
            cache.set(test_key, test_value, 30)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                cache.delete(test_key)
                return {
                    'status': 'healthy',
                    'message': 'Cache is working properly'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Cache test failed - value mismatch'
                }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Cache connection failed: {str(e)}'
            }
    
    def _check_redis(self):
        """Check Redis connectivity directly."""
        try:
            # Try to connect to Redis directly
            redis_client = redis.Redis.from_url(
                getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            )
            redis_client.ping()
            return {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Redis connection failed: {str(e)}'
            }


class ReadinessCheckView(View):
    """
    Readiness check for Kubernetes deployments.
    """
    
    def get(self, request):
        """
        Check if the application is ready to serve traffic.
        """
        try:
            # Check if Django is properly initialized
            from django.apps import apps
            if not apps.ready:
                return HttpResponse('Not ready', status=503)
            
            # Check database migrations
            from django.db.migrations.executor import MigrationExecutor
            from django.db import connections
            
            executor = MigrationExecutor(connections['default'])
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                return HttpResponse('Pending migrations', status=503)
            
            return HttpResponse('Ready', status=200)
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return HttpResponse(f'Not ready: {str(e)}', status=503)


class LivenessCheckView(View):
    """
    Liveness check for Kubernetes deployments.
    """
    
    def get(self, request):
        """
        Simple liveness check - just return 200 if the process is running.
        """
        return HttpResponse('Alive', status=200)


# Error handlers
def handler404(request, exception):
    """Custom 404 error handler."""
    return JsonResponse({
        'error': 'Not Found',
        'message': 'The requested resource was not found.',
        'status_code': 404
    }, status=404)


def handler500(request):
    """Custom 500 error handler."""
    return JsonResponse({
        'error': 'Internal Server Error',
        'message': 'An internal server error occurred.',
        'status_code': 500
    }, status=500)


def handler403(request, exception):
    """Custom 403 error handler."""
    return JsonResponse({
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource.',
        'status_code': 403
    }, status=403)