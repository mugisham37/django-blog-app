"""
Security settings for Django Personal Blog System.
Comprehensive security configuration for production deployment.
"""

import os
from django.core.management.utils import get_random_secret_key

# Security Keys and Tokens
SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())

# HTTPS and SSL Settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie Security
SECURE_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

# Session Security
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Content Security Policy
CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.ckeditor.com https://cdnjs.cloudflare.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https: blob:; "
    "media-src 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "upgrade-insecure-requests;"
)

# File Upload Security
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5MB
MAX_IMAGE_WIDTH = 4000
MAX_IMAGE_HEIGHT = 4000
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100

ALLOWED_FILE_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
    '.pdf', '.doc', '.docx', '.txt',           # Documents
    '.zip', '.tar', '.gz'                      # Archives
]

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Email Domain Security
BLACKLISTED_EMAIL_DOMAINS = [
    'tempmail.org', '10minutemail.com', 'guerrillamail.com',
    'mailinator.com', 'throwaway.email', 'temp-mail.org',
    'yopmail.com', 'maildrop.cc', 'sharklasers.com'
]

# URL Domain Security
BLACKLISTED_URL_DOMAINS = [
    'malware-site.com', 'phishing-site.com'  # Add known malicious domains
]

SUSPICIOUS_DOMAINS = [
    'bit.ly', 'tinyurl.com', 'goo.gl'  # URL shorteners (optional)
]

# Rate Limiting Configuration
GLOBAL_RATE_LIMITS = {
    'default': {'requests': 100, 'window': 300},    # 100 requests per 5 minutes
    'POST': {'requests': 20, 'window': 300},        # 20 POST requests per 5 minutes
    'login': {'requests': 5, 'window': 300},        # 5 login attempts per 5 minutes
    'register': {'requests': 3, 'window': 3600},    # 3 registrations per hour
    'comment': {'requests': 10, 'window': 600},     # 10 comments per 10 minutes
    'upload': {'requests': 5, 'window': 600},       # 5 uploads per 10 minutes
}

# IP Blocking Configuration
BLOCKED_IPS = [
    # Add known malicious IPs
]

BLOCKED_NETWORKS = [
    # Add blocked IP networks in CIDR notation
    # '192.168.1.0/24',
]

# Content Validation
SPAM_KEYWORDS = [
    'viagra', 'cialis', 'casino', 'lottery', 'winner',
    'congratulations', 'click here', 'free money',
    'make money', 'work from home', 'weight loss',
    'diet pills', 'miracle cure', 'guaranteed',
    'limited time', 'act now', 'urgent', 'exclusive offer',
    'buy now', 'discount', 'sale', 'cheap', 'free',
    'win', 'prize', 'cash', 'loan', 'credit'
]

INAPPROPRIATE_WORDS = [
    # Add inappropriate words for content filtering
]

# Reserved Names
RESERVED_SLUGS = [
    'admin', 'api', 'www', 'mail', 'blog', 'post', 'posts',
    'category', 'categories', 'tag', 'tags', 'search', 'archive',
    'feed', 'rss', 'sitemap', 'robots', 'about', 'contact',
    'login', 'logout', 'register', 'profile', 'settings',
    'dashboard', 'help', 'support', 'privacy', 'terms'
]

RESERVED_USERNAMES = [
    'admin', 'administrator', 'root', 'system', 'api',
    'www', 'mail', 'support', 'help', 'info', 'contact',
    'blog', 'post', 'user', 'account', 'profile',
    'settings', 'config', 'test', 'demo', 'guest',
    'anonymous', 'moderator', 'staff'
]

# Middleware Configuration
SECURITY_MIDDLEWARE = [
    'apps.core.security_middleware.SecurityHeadersMiddleware',
    'apps.core.security_middleware.IPBlockingMiddleware',
    'apps.core.security_middleware.RateLimitMiddleware',
    'apps.core.security_middleware.InputValidationMiddleware',
    'apps.core.security_middleware.SpamDetectionMiddleware',
    'apps.core.security_middleware.SuspiciousActivityMiddleware',
    'apps.core.security_middleware.RequestLoggingMiddleware',
]

# Paths to skip certain security checks
SKIP_INPUT_VALIDATION_PATHS = [
    '/admin/',
    '/api/upload/',
    '/ckeditor/',
    '/health/',
]

SKIP_RATE_LIMIT_PATHS = [
    '/admin/',
    '/health/',
    '/static/',
    '/media/',
]

LOG_SENSITIVE_PATHS = [
    '/login/',
    '/logout/',
    '/admin/',
    '/api/',
    '/upload/',
    '/register/',
    '/password/',
]

# Logging Configuration
LOG_ALL_REQUESTS = False  # Set to True for detailed logging

# Password Validation
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

# CSRF Protection
CSRF_FAILURE_VIEW = 'apps.core.views.csrf_failure'
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_TRUSTED_ORIGINS = [
    # Add your trusted origins
    # 'https://yourdomain.com',
]

# Additional Security Settings
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Data Retention
DATA_RETENTION_DAYS = 365  # Keep logs for 1 year
FAILED_LOGIN_RETENTION_DAYS = 30
SECURITY_LOG_RETENTION_DAYS = 90

# Honeypot Configuration (for spam detection)
HONEYPOT_FIELD_NAME = 'email_confirm'  # Hidden field name
HONEYPOT_VALUE = ''  # Expected value (empty)

# Account Security
MAX_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_DURATION = 1800  # 30 minutes
PASSWORD_RESET_TIMEOUT = 3600    # 1 hour

# API Security
API_RATE_LIMIT_AUTHENTICATED = '100/h'  # 100 requests per hour for authenticated users
API_RATE_LIMIT_ANONYMOUS = '20/h'       # 20 requests per hour for anonymous users

# File Upload Scanning (if antivirus is available)
SCAN_UPLOADED_FILES = False  # Set to True if you have antivirus scanning
QUARANTINE_SUSPICIOUS_FILES = True

# Security Headers for Development
if os.environ.get('DJANGO_ENV') == 'development':
    SECURE_SSL_REDIRECT = False
    SECURE_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0

# Security Monitoring
ENABLE_SECURITY_MONITORING = True
SECURITY_ALERT_EMAIL = os.environ.get('SECURITY_ALERT_EMAIL', 'admin@example.com')
SECURITY_ALERT_THRESHOLD = 10  # Number of violations before sending alert

# Backup Security
BACKUP_ENCRYPTION_KEY = os.environ.get('BACKUP_ENCRYPTION_KEY')
BACKUP_RETENTION_DAYS = 30

# Database Security
DATABASES_REQUIRE_SSL = True
DATABASE_CONNECTION_TIMEOUT = 30

# Cache Security
CACHE_KEY_PREFIX = 'blog_'
CACHE_VERSION = 1

# Third-party Integration Security
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    # Add your production domains
]

# Security Testing
SECURITY_TEST_MODE = os.environ.get('SECURITY_TEST_MODE', 'False').lower() == 'true'

if SECURITY_TEST_MODE:
    # Relaxed settings for security testing
    GLOBAL_RATE_LIMITS = {
        'default': {'requests': 1000, 'window': 300},
        'POST': {'requests': 200, 'window': 300},
        'login': {'requests': 50, 'window': 300},
    }