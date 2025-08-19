"""
Database monitoring and health check utilities.
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.db import connections, connection
from django.db.utils import OperationalError
from django.core.cache import cache
from .config import DATABASE_MONITORING, DATABASE_HEALTH_CHECK
from .exceptions import MonitoringError

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """
    Comprehensive database monitoring and metrics collection.
    """
    
    def __init__(self, database: str = 'default'):
        self.database = database
        self.connection = connections[database]
        self.metrics_cache_key = f"db_metrics_{database}"
        self.health_cache_key = f"db_health_{database}"
        self._monitoring_enabled = DATABASE_MONITORING.get('ENABLED', True)
        self._slow_query_threshold = DATABASE_MONITORING.get('SLOW_QUERY_THRESHOLD', 1.0)
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive database health check.
        
        Returns:
            Health check results
        """
        try:
            start_time = time.time()
            health_data = {
                'database': self.database,
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy',
                'checks': {},
                'metrics': {},
            }
            
            # Basic connectivity check
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                health_data['checks']['connectivity'] = {'status': 'ok', 'message': 'Database is reachable'}
            except Exception as e:
                health_data['checks']['connectivity'] = {'status': 'error', 'message': str(e)}
                health_data['status'] = 'unhealthy'
            
            # Connection pool status
            try:
                pool_status = self._check_connection_pool()
                health_data['checks']['connection_pool'] = pool_status
                if pool_status['status'] != 'ok':
                    health_data['status'] = 'degraded'
            except Exception as e:
                health_data['checks']['connection_pool'] = {'status': 'error', 'message': str(e)}
            
            # Database size and usage
            try:
                db_stats = self._get_database_stats()
                health_data['metrics']['database_stats'] = db_stats
            except Exception as e:
                health_data['checks']['database_stats'] = {'status': 'error', 'message': str(e)}
            
            # Active connections
            try:
                connection_stats = self._get_connection_stats()
                health_data['metrics']['connections'] = connection_stats
                
                # Check if too many connections
                if connection_stats.get('active_connections', 0) > 80:  # 80% threshold
                    health_data['checks']['connection_limit'] = {
                        'status': 'warning',
                        'message': 'High number of active connections'
                    }
                    health_data['status'] = 'degraded'
            except Exception as e:
                health_data['checks']['connections'] = {'status': 'error', 'message': str(e)}
            
            # Slow queries check
            try:
                slow_queries = self._get_slow_queries()
                health_data['metrics']['slow_queries'] = slow_queries
                
                if slow_queries.get('count', 0) > 10:  # More than 10 slow queries
                    health_data['checks']['slow_queries'] = {
                        'status': 'warning',
                        'message': f"Found {slow_queries['count']} slow queries"
                    }
              