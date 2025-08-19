"""
Production settings for Django Personal Blog System.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Enhanced security settings for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Secure cookie configuration
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Enhanced HSTS configuration for production
SECURE_HSTS_SECONDS = 63072000  # 2 years
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional production security settings
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Enable security monitoring in production
SECURITY_MONITORING.update({
    'ENABLE_CSP_REPORTING': True,
    'ENABLE_SECURITY_HEADERS_CHECK': True,
    'ENABLE_HTTPS_ENFORCEMENT': True,
    'ENABLE_AUDIT_LOGGING': True,
    'ALERT_ON_SECURITY_VIOLATIONS': True,
})

# Stricter CSP for production
CSP_UPGRADE_INSECURE_REQUESTS = True
CSP_BLOCK_ALL_MIXED_CONTENT = True

# Enhanced IP security for production
IP_SECURITY.update({
    'ENABLE_IP_BLOCKING': True,
    'BLOCK_DURATION_MINUTES': 60,  # Longer blocks in production
    'MAX_FAILED_ATTEMPTS': 3,  # Stricter in production
    'SUSPICIOUS_ACTIVITY_THRESHOLD': 5,  # Lower threshold in production
})

# Database with production optimizations
from .database import get_database_config

DATABASES = {
    'default': get_database_config('production'),
}

# Add read replica for production if configured
if config('DB_READ_HOST', default=''):
    from .database import DATABASE_READ_REPLICA_CONFIG
    DATABASES['read_replica'] = DATABASE_READ_REPLICA_CONFIG

# Static files for production with optimization
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Enable compression in production
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# Optimize compression settings for production
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]

COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.rJSMinFilter',
]

# Use separate storage for compressed files
COMPRESS_STORAGE = 'compressor.storage.CompressorFileStorage'

# Image optimization for production
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.OptimisticStrategy'
VERSATILEIMAGEFIELD_SETTINGS = {
    'cache_length': 2592000 * 12,  # 1 year
    'cache_name': 'versatileimagefield_cache',
    'jpeg_resize_quality': 75,  # Slightly lower quality for production
    'sized_directory_name': '__sized__',
    'filtered_directory_name': '__filtered__',
    'placeholder_directory_name': '__placeholder__',
    'create_images_on_demand': False,  # Pre-generate in production
    'image_key_post_processor': None,
    'progressive_jpeg': True,
}

# CDN configuration for production
CDN_URL = config('CDN_URL', default='')
if CDN_URL:
    STATIC_URL = f'{CDN_URL}/static/'
    MEDIA_URL = f'{CDN_URL}/media/'
    
    # Update compressor settings for CDN
    COMPRESS_URL = STATIC_URL
    COMPRESS_ROOT = STATIC_ROOT

# Cache configuration optimized for production
CACHES['default'].update({
    'TIMEOUT': 3600,  # 1 hour default timeout in production
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'PARSER_CLASS': 'redis.connection.HiredisParser',
        'CONNECTION_POOL_KWARGS': {
            'max_connections': 100,  # More connections for production
            'retry_on_timeout': True,
        },
        'COMPRESSOR': 'redis.connection.HiredisCompressor',
    },
})

# Add separate cache for compressed files
CACHES['compressor'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': config('REDIS_COMPRESSOR_URL', default=REDIS_URL),
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'CONNECTION_POOL_KWARGS': {
            'max_connections': 50,
        },
    },
    'KEY_PREFIX': 'compressor',
    'TIMEOUT': 86400 * 30,  # 30 days for compressed files
}

COMPRESS_CACHE_BACKEND = 'compressor'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Comprehensive logging for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024*1024*15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 1024*1024*15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'error'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}