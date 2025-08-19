"""
Database connection management with pooling and read replica support.
"""

import logging
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional, Generator
from django.db import connections, connection
from django.db.utils import ConnectionHandler
from django.conf import settings
from .exceptions import ConnectionError
from .config import DATABASE_HEALTH_CHECK, DATABASE_MONITORING

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Advanced connection manager with pooling and health monitoring.
    """
    
    _instance = None
    _lock = threading.Lock()
    _health_status = {}
    _connection_stats = {
        'total_connections': 0,
        'active_connections': 0,
        'failed_connections': 0,
        'connection_errors': [],
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_monitoring()
    
    def _setup_monitoring(self):
        """Setup connection monitoring if enabled."""
        if DATABASE_MONITORING.get('ENABLED', True):
            # Start health check thread
            if DATABASE_HEALTH_CHECK.get('ENABLED', True):
                self._start_health_check_thread()
    
    def _start_health_check_thread(self):
        """Start background thread for health checks."""
        def health_check_worker():
            while True:
                try:
                    self._perform_health_checks()
                    time.sleep(DATABASE_HEALTH_CHECK.get('INTERVAL', 30))
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                    time.sleep(5)  # Short delay on error
        
        thread = threading.Thread(target=health_check_worker, daemon=True)
        thread.start()
    
    def _perform_health_checks(self):
        """Perform health checks on all database connections."""
        for alias in connections:
            try:
                conn = connections[alias]
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                
                self._health_status[alias] = {
                    'status': 'healthy',
                    'last_check': time.time(),
                    'error': None,
                }
            except Exception as e:
                self._health_status[alias] = {
                    'status': 'unhealthy',
                    'last_check': time.time(),
                    'error': str(e),
                }
                logger.warning(f"Database {alias} health check failed: {e}")
    
    @contextmanager
    def get_connection(self, alias: str = 'default') -> Generator[Any, None, None]:
        """
        Get a database connection with automatic cleanup.
        
        Args:
            alias: Database alias to use
            
        Yields:
            Database connection
            
        Raises:
            ConnectionError: If connection fails
        """
        conn = None
        try:
            self._connection_stats['total_connections'] += 1
            self._connection_stats['active_connections'] += 1
            
            conn = connections[alias]
            
            # Ensure connection is open
            conn.ensure_connection()
            
            yield conn
            
        except Exception as e:
            self._connection_stats['failed_connections'] += 1
            self._connection_stats['connection_errors'].append({
                'alias': alias,
                'error': str(e),
                'timestamp': time.time(),
            })
            
            # Keep only last 100 errors
            if len(self._connection_stats['connection_errors']) > 100:
                self._connection_stats['connection_errors'] = \
                    self._connection_stats['connection_errors'][-100:]
            
            logger.error(f"Database connection error for {alias}: {e}")
            raise ConnectionError(f"Failed to get connection for {alias}: {e}")
        
        finally:
            self._connection_stats['active_connections'] -= 1
            
            # Close connection if needed
            if conn and not conn.in_atomic_block:
                conn.close()
    
    @contextmanager
    def get_read_connection(self) -> Generator[Any, None, None]:
        """
        Get a read-only database connection (uses read replica if available).
        
        Yields:
            Database connection for read operations
        """
        # Try read replica first, fallback to default
        read_alias = 'read_replica' if 'read_replica' in connections else 'default'
        
        with self.get_connection(read_alias) as conn:
            yield conn
    
    @contextmanager
    def get_write_connection(self) -> Generator[Any, None, None]:
        """
        Get a write database connection (always uses primary database).
        
        Yields:
            Database connection for write operations
        """
        with self.get_connection('default') as conn:
            yield conn
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary with connection statistics
        """
        return self._connection_stats.copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status for all database connections.
        
        Returns:
            Dictionary with health status for each database
        """
        return self._health_status.copy()
    
    def is_healthy(self, alias: str = 'default') -> bool:
        """
        Check if a database connection is healthy.
        
        Args:
            alias: Database alias to check
            
        Returns:
            True if healthy, False otherwise
        """
        status = self._health_status.get(alias, {})
        return status.get('status') == 'healthy'
    
    def reset_connection(self, alias: str = 'default') -> None:
        """
        Reset a database connection.
        
        Args:
            alias: Database alias to reset
        """
        try:
            connections[alias].close()
            logger.info(f"Reset connection for database {alias}")
        except Exception as e:
            logger.error(f"Failed to reset connection for {alias}: {e}")
    
    def close_all_connections(self) -> None:
        """Close all database connections."""
        connections.close_all()
        logger.info("Closed all database connections")


class ConnectionPool:
    """
    Custom connection pool implementation.
    """
    
    def __init__(
        self,
        min_connections: int = 5,
        max_connections: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
    ):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        
        self._pool = []
        self._overflow = []
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # Pre-create minimum connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections."""
        for _ in range(self.min_connections):
            conn = self._create_connection()
            if conn:
                self._pool.append(conn)
    
    def _create_connection(self):
        """Create a new database connection."""
        try:
            # This would create an actual database connection
            # For now, we'll return a placeholder
            self._created_connections += 1
            return f"connection_{self._created_connections}"
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            Database connection
        """
        conn = None
        is_overflow = False
        
        try:
            with self._lock:
                # Try to get from main pool
                if self._pool:
                    conn = self._pool.pop()
                # Try overflow if main pool is empty
                elif len(self._overflow) < self.max_overflow:
                    conn = self._create_connection()
                    if conn:
                        self._overflow.append(conn)
                        is_overflow = True
                else:
                    raise ConnectionError("Connection pool exhausted")
            
            if not conn:
                raise ConnectionError("Failed to get connection from pool")
            
            yield conn
            
        finally:
            if conn:
                with self._lock:
                    if is_overflow:
                        # Remove overflow connections
                        if conn in self._overflow:
                            self._overflow.remove(conn)
                    else:
                        # Return to main pool
                        if len(self._pool) < self.max_connections:
                            self._pool.append(conn)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'overflow_size': len(self._overflow),
                'total_created': self._created_connections,
                'min_connections': self.min_connections,
                'max_connections': self.max_connections,
                'max_overflow': self.max_overflow,
            }


# Global connection manager instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return connection_manager


# Utility functions for common connection operations
def execute_query(query: str, params: Optional[tuple] = None, alias: str = 'default') -> Any:
    """
    Execute a raw SQL query.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        alias: Database alias to use
        
    Returns:
        Query results
    """
    with connection_manager.get_connection(alias) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def execute_read_query(query: str, params: Optional[tuple] = None) -> Any:
    """
    Execute a read-only query (uses read replica if available).
    
    Args:
        query: SQL query to execute
        params: Query parameters
        
    Returns:
        Query results
    """
    with connection_manager.get_read_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


def execute_write_query(query: str, params: Optional[tuple] = None) -> Any:
    """
    Execute a write query (uses primary database).
    
    Args:
        query: SQL query to execute
        params: Query parameters
        
    Returns:
        Query results
    """
    with connection_manager.get_write_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()