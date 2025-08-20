"""
Base settings for Django Personal Blog System.
This file contains settings common to all environments.
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'corsheaders',
    'ckeditor',
    'ckeditor_uploader',
    'django_extensions',
    'django_celery_beat',
    'django_celery_results',
    'channels',
    'compressor',
    'imagekit',
    # 'versatileimagefield',  # Disabled due to libmagic issues on Windows
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.blog',
    'apps.comments',
    'apps.analytics',
    'apps.newsletter',
    'apps.api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'apps.core.security_headers.HTTPSRedirectMiddleware',
    'apps.core.security_headers.SecurityHeadersMiddleware',
    'apps.core.rate_limiting.RateLimitMiddleware',
    'apps.core.middleware.RequestLoggingMiddleware',
    'apps.core.middleware.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'apps.core.csrf_protection.EnhancedCSRFMiddleware',
    'apps.core.csrf_protection.CSRFTokenMiddleware',
    'apps.core.csrf_protection.CSRFTokenRotationMiddleware',
    'apps.core.security_headers.CSPReportingMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.ErrorHandlingMiddleware',
    'apps.core.middleware.AnalyticsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
from .database import get_database_config, DATABASE_READ_REPLICA_CONFIG, DATABASE_ROUTERS

DATABASES = {
    'default': get_database_config('development'),
}

# Add read replica if configured
if config('DB_READ_HOST', default=''):
    DATABASES['read_replica'] = DATABASE_READ_REPLICA_CONFIG

# Database routing
DATABASE_ROUTERS = DATABASE_ROUTERS

# Redis Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'blog',
        'VERSION': 1,
        'TIMEOUT': 300,  # 5 minutes default timeout
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Site framework
SITE_ID = 1

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@personalblog.com')

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = f'{REDIS_URL.rstrip("/0")}/1'  # Use Redis DB 1 for results
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Advanced Celery Configuration
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_IGNORE_RESULT = False
CELERY_TASK_STORE_EAGER_RESULT = True
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour

# Worker Configuration
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True

# Task routing and priority
CELERY_TASK_INHERIT_PARENT_PRIORITY = True
CELERY_TASK_DEFAULT_PRIORITY = 5
CELERY_TASK_DEFAULT_QUEUE = 'medium_priority'

# Task time limits
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes soft limit
CELERY_TASK_TIME_LIMIT = 600       # 10 minutes hard limit

# Task retry configuration
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Security
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_LOG_COLOR = False

# Broker transport options
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'priority_steps': list(range(10)),
    'sep': ':',
    'queue_order_strategy': 'priority',
}

# Task monitoring and failure handling
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_PUBLISH_RETRY = True
CELERY_TASK_PUBLISH_RETRY_POLICY = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2,
}

# Custom task failure settings
CELERY_TASK_ANNOTATIONS = {
    '*': {
        'rate_limit': '100/m',  # Global rate limit
        'time_limit': 600,      # 10 minutes
        'soft_time_limit': 300, # 5 minutes
    },
    'apps.blog.tasks.publish_scheduled_posts': {
        'rate_limit': '60/m',
        'priority': 9,
        'queue': 'high_priority',
    },
    'apps.analytics.tasks.update_analytics': {
        'rate_limit': '10/m',
        'priority': 1,
        'queue': 'low_priority',
    },
    'apps.core.tasks.cleanup_old_sessions': {
        'rate_limit': '1/h',
        'priority': 1,
        'queue': 'low_priority',
    },
}

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
    'VERSION_PARAM': 'version',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'apps.core.throttling.StaffRateThrottle',
        'apps.core.throttling.PremiumUserRateThrottle',
        'apps.core.throttling.BurstRateThrottle',
        'apps.core.throttling.SearchRateThrottle',
        'apps.core.throttling.UploadRateThrottle',
        'apps.core.throttling.DynamicRateThrottle',
        'apps.core.throttling.EndpointSpecificThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',           # Anonymous users: 100 requests per hour
        'user': '1000/hour',          # Regular authenticated users: 1000 requests per hour
        'staff': '5000/hour',         # Staff users: 5000 requests per hour
        'premium': '2000/hour',       # Premium users: 2000 requests per hour
        'burst': '60/min',            # Burst rate for intensive operations
        'search': '30/min',           # Search-specific rate limiting
        'upload': '10/min',           # File upload rate limiting
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata',
}

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_JQUERY_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js'
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_BROWSE_SHOW_DIRS = True
CKEDITOR_ALLOW_NONIMAGE_FILES = False

# File upload restrictions for CKEditor
CKEDITOR_UPLOAD_SLUGIFY_FILENAME = True
CKEDITOR_FILENAME_GENERATOR = 'apps.core.utils.get_filename'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline', 'Strike'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar'],
            ['Styles', 'Format', 'Font', 'FontSize'],
            ['TextColor', 'BGColor'],
            ['Maximize', 'ShowBlocks'],
            ['Source'],
        ],
        'height': 400,
        'width': '100%',
        'toolbarCanCollapse': True,
        'tabSpaces': 4,
        'extraPlugins': ','.join([
            'uploadimage',
            'div',
            'autolink',
            'autoembed',
            'embedsemantic',
            'autogrow',
            'widget',
            'lineutils',
            'clipboard',
            'dialog',
            'dialogui',
            'elementspath',
            'codesnippet',
            'youtube',
        ]),
        'codeSnippet_theme': 'monokai_sublime',
        'youtube_responsive': True,
        'youtube_privacy': True,
        'youtube_related': False,
        'youtube_older': False,
        'youtube_width': 560,
        'youtube_height': 315,
        'removePlugins': 'stylesheetparser',
        'allowedContent': True,
        'removeButtons': 'Underline,Subscript,Superscript',
        'format_tags': 'p;h1;h2;h3;h4;h5;h6;pre;address;div',
        'autoGrow_onStartup': True,
        'autoGrow_minHeight': 200,
        'autoGrow_maxHeight': 600,
        'mathJaxLib': 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-AMS_HTML',
        'tabSpaces': 4,
        'uiColor': '#f8f9fa',
    },
    'admin': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source']
        ],
        'height': 200,
        'width': '100%',
        'toolbarCanCollapse': False,
        'extraPlugins': 'autolink,autoembed',
        'removePlugins': 'stylesheetparser',
        'allowedContent': True,
    },
    'comment': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic'],
            ['Link', 'Unlink'],
            ['RemoveFormat']
        ],
        'height': 150,
        'width': '100%',
        'toolbarCanCollapse': False,
        'removePlugins': 'stylesheetparser',
        'allowedContent': 'b strong i em a[href]; p br',
        'forcePasteAsPlainText': True,
    },
}

# Comprehensive Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS and HSTS Configuration
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional Security Headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Content Security Policy Configuration
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"]
CSP_IMG_SRC = ["'self'", "data:", "https:", "blob:"]
CSP_FONT_SRC = ["'self'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"]
CSP_CONNECT_SRC = ["'self'"]
CSP_MEDIA_SRC = ["'self'"]
CSP_OBJECT_SRC = ["'none'"]
CSP_FRAME_ANCESTORS = ["'none'"]
CSP_BASE_URI = ["'self'"]
CSP_FORM_ACTION = ["'self'"]
CSP_UPGRADE_INSECURE_REQUESTS = not DEBUG

# Permissions Policy (formerly Feature Policy)
PERMISSIONS_POLICY = {
    'geolocation': [],
    'microphone': [],
    'camera': [],
    'payment': [],
    'usb': [],
    'magnetometer': [],
    'gyroscope': [],
    'speaker': [],
    'vibrate': [],
    'fullscreen': ['self'],
    'encrypted-media': ['self'],
}

# Security Monitoring Configuration
SECURITY_MONITORING = {
    'ENABLE_CSP_REPORTING': not DEBUG,
    'CSP_REPORT_URI': '/security/csp-report/',
    'ENABLE_SECURITY_HEADERS_CHECK': True,
    'ENABLE_HTTPS_ENFORCEMENT': not DEBUG,
    'ENABLE_AUDIT_LOGGING': True,
    'ALERT_ON_SECURITY_VIOLATIONS': not DEBUG,
}

# IP Security Configuration
IP_SECURITY = {
    'ENABLE_IP_BLOCKING': True,
    'BLOCK_DURATION_MINUTES': 30,
    'MAX_FAILED_ATTEMPTS': 5,
    'SUSPICIOUS_ACTIVITY_THRESHOLD': 10,
    'WHITELIST_IPS': config('SECURITY_WHITELIST_IPS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]),
    'BLACKLIST_IPS': config('SECURITY_BLACKLIST_IPS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]),
}

# Security Headers Configuration
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cross-Origin-Embedder-Policy': 'require-corp',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
}

# CSRF Settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_AGE = 3600  # 1 hour
CSRF_TOKEN_ROTATION_INTERVAL = 3600  # 1 hour
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000,http://127.0.0.1:8000', cast=lambda v: [s.strip() for s in v.split(',')])

# CORS Settings
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=lambda v: [s.strip() for s in v.split(',')])
CORS_ALLOW_CREDENTIALS = True

# Rate Limiting Configuration
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# Global Rate Limits (requests per minute)
GLOBAL_RATE_LIMITS = {
    'anonymous_user': {'limit': 100, 'window': 60},
    'authenticated_user': {'limit': 300, 'window': 60},
    'api_anonymous': {'limit': 50, 'window': 60},
    'api_authenticated': {'limit': 200, 'window': 60},
}

# Endpoint-specific Rate Limits
ENDPOINT_RATE_LIMITS = {
    'login': {'limit': 5, 'window': 300},
    'register': {'limit': 3, 'window': 300},
    'password_reset': {'limit': 3, 'window': 600},
    'comment_submit': {'limit': 10, 'window': 60},
    'search': {'limit': 30, 'window': 60},
    'contact_form': {'limit': 2, 'window': 300},
}

# Security Monitoring
FAILED_LOGIN_ATTEMPTS_THRESHOLD = 5
IP_BLOCK_DURATION = 1800  # 30 minutes
SUSPICIOUS_ACTIVITY_THRESHOLD = 3

# Custom Validation Settings
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_WIDTH = 4000
MAX_IMAGE_HEIGHT = 4000
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx',
    '.txt', '.zip', '.mp4', '.mp3'
]

# Security Settings for Validators
BLACKLISTED_EMAIL_DOMAINS = [
    'tempmail.org', '10minutemail.com', 'guerrillamail.com',
    'mailinator.com', 'throwaway.email'
]

BLACKLISTED_URL_DOMAINS = [
    'malicious-site.com', 'spam-domain.org'
]

INAPPROPRIATE_WORDS = [
    # Add inappropriate words as needed
]

# Django Compressor Configuration
COMPRESS_ENABLED = not DEBUG
COMPRESS_OFFLINE = not DEBUG
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.rJSMinFilter',
]
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_URL = STATIC_URL
COMPRESS_STORAGE = 'compressor.storage.CompressorFileStorage'

# Static file versioning for cache busting
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Image optimization settings
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.JustInTime'
IMAGEKIT_CACHEFILE_NAMER = 'imagekit.cachefiles.namers.source_name_dot_hash'
IMAGEKIT_SPEC_CACHEFILE_NAMER = 'imagekit.cachefiles.namers.source_name_as_path_dot_hash'
IMAGEKIT_CACHEFILE_DIR = 'CACHE/images'
IMAGEKIT_DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# VersatileImageField Configuration
VERSATILEIMAGEFIELD_SETTINGS = {
    'cache_length': 2592000,  # 30 days
    'cache_name': 'versatileimagefield_cache',
    'jpeg_resize_quality': 70,
    'sized_directory_name': '__sized__',
    'filtered_directory_name': '__filtered__',
    'placeholder_directory_name': '__placeholder__',
    'create_images_on_demand': True,
    'image_key_post_processor': None,
    'progressive_jpeg': False,
}

# Image size variants for responsive images
IMAGE_SIZES = {
    'thumbnail': {'width': 150, 'height': 150, 'crop': True},
    'small': {'width': 300, 'height': 200, 'crop': True},
    'medium': {'width': 600, 'height': 400, 'crop': True},
    'large': {'width': 1200, 'height': 800, 'crop': True},
    'hero': {'width': 1920, 'height': 1080, 'crop': True},
    'avatar_small': {'width': 50, 'height': 50, 'crop': True},
    'avatar_medium': {'width': 100, 'height': 100, 'crop': True},
    'avatar_large': {'width': 200, 'height': 200, 'crop': True},
}

# CDN Configuration (for production)
CDN_URL = config('CDN_URL', default='')
if CDN_URL:
    STATIC_URL = f'{CDN_URL}/static/'
    MEDIA_URL = f'{CDN_URL}/media/'

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# WebSocket Configuration
WEBSOCKET_SETTINGS = {
    'JWT_AUTH_REQUIRED': True,
    'HEARTBEAT_INTERVAL': 30,  # seconds
    'CONNECTION_TIMEOUT': 300,  # 5 minutes
    'MAX_CONNECTIONS_PER_USER': 10,
    'ENABLE_CONNECTION_TRACKING': True,
    'CLEANUP_INTERVAL': 3600,  # 1 hour
}

# Logging Configuration
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
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps.core': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'security': {
            'handlers': ['security', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}