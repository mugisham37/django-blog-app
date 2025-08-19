"""
Pytest configuration for enterprise_core tests.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def pytest_configure():
    """Configure Django settings for testing."""
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'enterprise_core',
        ],
        SECRET_KEY='test-secret-key-for-testing-only',
        USE_TZ=True,
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
        DEFAULT_FROM_EMAIL='test@example.com',
        # Test-specific settings
        BLACKLISTED_EMAIL_DOMAINS=[],
        REQUIRED_EMAIL_DOMAINS=[],
        MAX_IMAGE_SIZE=5 * 1024 * 1024,  # 5MB
        MIN_IMAGE_WIDTH=50,
        MIN_IMAGE_HEIGHT=50,
        MAX_IMAGE_WIDTH=4000,
        MAX_IMAGE_HEIGHT=4000,
        MAX_FILE_UPLOAD_SIZE=10 * 1024 * 1024,  # 10MB
    )
    
    django.setup()