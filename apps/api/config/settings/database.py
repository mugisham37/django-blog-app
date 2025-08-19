"""
Database configuration with connection pooling and optimization settings.
"""

import os
from decouple import config

# Database connection pooling configuration
DATABASE_POOL_CONFIG = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': config('DB_NAME', default='personal_blog'),
    'USER': config('DB_USER', default='postgres'),
    'PASSWORD': config('DB_PASSWORD', default=''),
    'HOST': config('DB_HOST', default='localhost'),
    'PORT': config('DB_PORT', default='5432'),
    'OPTIONS': {
        # Connection pooling with pgbouncer-style settings
        'MAX_CONNS': config('DB_MAX_CONNS', default=20, cast=int),
        'MIN_CONNS': config('DB_MIN_CONNS', default=5, cast=int),
        
        # Connection timeout settings
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),  # 10 minutes
        'CONN_HEALTH_CHECKS': config('DB_CONN_HEALTH_CHECKS', default=True, cast=bool),
        
        # PostgreSQL specific optimizations
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4',
        'use_unicode': True,
        
        # Connection pool settings for production
        'POOL_CLASS': 'psycopg2.pool.ThreadedConnectionPool',
        'POOL_SIZE': config('DB_POOL_SIZE', default=10, cast=int),
        'MAX_OVERFLOW': config('DB_MAX_OVERFLOW', default=20, cast=int),
        
        # Query optimization settings
        'autocommit': True,
        'isolation_level': None,
        
        # SSL settings for production
        'sslmode': config('DB_SSL_MODE', default='prefer'),
        'sslcert': config('DB_SSL_CERT', default=''),
        'sslkey': config('DB_SSL_KEY', default=''),
        'sslrootcert': config('DB_SSL_ROOT_CERT', default=''),
        
        # Performance tuning
        'server_side_binding': True,
        'prepared_statements': True,
        'statement_timeout': config('DB_STATEMENT_TIMEOUT', default=30000, cast=int),  # 30 seconds
        'lock_timeout': config('DB_LOCK_TIMEOUT', default=10000, cast=int),  # 10 seconds
        
        # Connection retry settings
        'RETRY_ATTEMPTS': config('DB_RETRY_ATTEMPTS', default=3, cast=int),
        'RETRY_DELAY': config('DB_RETRY_DELAY', default=1, cast=int),
    },
    'TEST': {
        'NAME': config('DB_TEST_NAME', default='test_personal_blog'),
        'CHARSET': 'utf8mb4',
        'COLLATION': 'utf8mb4_unicode_ci',
    }
}

# Read replica configuration for scaling reads
DATABASE_READ_REPLICA_CONFIG = {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': config('DB_READ_NAME', default=DATABASE_POOL_CONFIG['NAME']),
    'USER': config('DB_READ_USER', default=DATABASE_POOL_CONFIG['USER']),
    'PASSWORD': config('DB_READ_PASSWORD', default=DATABASE_POOL_CONFIG['PASSWORD']),
    'HOST': config('DB_READ_HOST', default=DATABASE_POOL_CONFIG['HOST']),
    'PORT': config('DB_READ_PORT', default=DATABASE_POOL_CONFIG['PORT']),
    'OPTIONS': DATABASE_POOL_CONFIG['OPTIONS'].copy(),
}

# Database routing for read/write splitting
DATABASE_ROUTERS = [
    'apps.core.db_router.DatabaseRouter',
]

# Query optimization settings
DATABASES_OPTIMIZATION = {
    # Enable query logging in development
    'ENABLE_QUERY_LOGGING': config('DB_ENABLE_QUERY_LOGGING', default=False, cast=bool),
    'QUERY_LOG_THRESHOLD': config('DB_QUERY_LOG_THRESHOLD', default=0.5, cast=float),  # Log slow queries
    
    # Connection pooling settings
    'ENABLE_CONNECTION_POOLING': config('DB_ENABLE_CONNECTION_POOLING', default=True, cast=bool),
    'CONNECTION_POOL_SIZE': config('DB_CONNECTION_POOL_SIZE', default=10, cast=int),
    'CONNECTION_POOL_MAX_OVERFLOW': config('DB_CONNECTION_POOL_MAX_OVERFLOW', default=20, cast=int),
    
    # Query caching settings
    'ENABLE_QUERY_CACHE': config('DB_ENABLE_QUERY_CACHE', default=True, cast=bool),
    'QUERY_CACHE_TIMEOUT': config('DB_QUERY_CACHE_TIMEOUT', default=300, cast=int),  # 5 minutes
    
    # Bulk operations settings
    'BULK_CREATE_BATCH_SIZE': config('DB_BULK_CREATE_BATCH_SIZE', default=1000, cast=int),
    'BULK_UPDATE_BATCH_SIZE': config('DB_BULK_UPDATE_BATCH_SIZE', default=1000, cast=int),
    
    # Index optimization settings
    'AUTO_CREATE_INDEXES': config('DB_AUTO_CREATE_INDEXES', default=True, cast=bool),
    'INDEX_MAINTENANCE_ENABLED': config('DB_INDEX_MAINTENANCE_ENABLED', default=True, cast=bool),
}

# Database configuration based on environment
def get_database_config(environment='development'):
    """
    Get database configuration based on environment.
    """
    base_config = DATABASE_POOL_CONFIG.copy()
    
    if environment == 'production':
        # Production-specific optimizations
        base_config['OPTIONS'].update({
            'CONN_MAX_AGE': 3600,  # 1 hour
            'MAX_CONNS': 50,
            'MIN_CONNS': 10,
            'POOL_SIZE': 20,
            'MAX_OVERFLOW': 40,
            'prepared_statements': True,
            'server_side_binding': True,
        })
    elif environment == 'testing':
        # Testing-specific settings
        base_config.update({
            'NAME': base_config['TEST']['NAME'],
            'OPTIONS': {
                'CONN_MAX_AGE': 0,  # No connection reuse in tests
                'MAX_CONNS': 5,
                'MIN_CONNS': 1,
                'POOL_SIZE': 2,
                'MAX_OVERFLOW': 5,
            }
        })
    elif environment == 'development':
        # Development-specific settings
        base_config['OPTIONS'].update({
            'CONN_MAX_AGE': 300,  # 5 minutes
            'MAX_CONNS': 10,
            'MIN_CONNS': 2,
            'POOL_SIZE': 5,
            'MAX_OVERFLOW': 10,
        })
    
    return base_config

# Database health check configuration
DATABASE_HEALTH_CHECK = {
    'ENABLED': config('DB_HEALTH_CHECK_ENABLED', default=True, cast=bool),
    'INTERVAL': config('DB_HEALTH_CHECK_INTERVAL', default=30, cast=int),  # seconds
    'TIMEOUT': config('DB_HEALTH_CHECK_TIMEOUT', default=5, cast=int),  # seconds
    'MAX_FAILURES': config('DB_HEALTH_CHECK_MAX_FAILURES', default=3, cast=int),
}

# Database monitoring configuration
DATABASE_MONITORING = {
    'ENABLED': config('DB_MONITORING_ENABLED', default=True, cast=bool),
    'SLOW_QUERY_THRESHOLD': config('DB_SLOW_QUERY_THRESHOLD', default=1.0, cast=float),  # seconds
    'LOG_QUERIES': config('DB_LOG_QUERIES', default=False, cast=bool),
    'METRICS_COLLECTION': config('DB_METRICS_COLLECTION', default=True, cast=bool),
}

# Database backup configuration
DATABASE_BACKUP = {
    'ENABLED': config('DB_BACKUP_ENABLED', default=False, cast=bool),
    'SCHEDULE': config('DB_BACKUP_SCHEDULE', default='0 2 * * *'),  # Daily at 2 AM
    'RETENTION_DAYS': config('DB_BACKUP_RETENTION_DAYS', default=30, cast=int),
    'BACKUP_PATH': config('DB_BACKUP_PATH', default='/backups/database/'),
    'COMPRESSION': config('DB_BACKUP_COMPRESSION', default=True, cast=bool),
}