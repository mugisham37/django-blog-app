"""
Global pytest configuration and fixtures for the entire test suite.
"""
import os
import sys
import pytest
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def pytest_configure(config):
    """Configure Django settings for testing."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.api.settings.test')
    django.setup()

@pytest.fixture(scope='session')
def django_db_setup():
    """Set up test database."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass

@pytest.fixture
def api_client():
    """Provide Django REST framework test client."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user_factory):
    """Provide authenticated API client."""
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user_factory):
    """Provide admin authenticated API client."""
    admin = admin_user_factory()
    api_client.force_authenticate(user=admin)
    return api_client

# Performance testing fixtures
@pytest.fixture
def performance_threshold():
    """Default performance thresholds for tests."""
    return {
        'response_time': 0.5,  # 500ms
        'memory_usage': 100,   # 100MB
        'cpu_usage': 80,       # 80%
    }

# Cache testing fixtures
@pytest.fixture
def cache_backend():
    """Provide cache backend for testing."""
    from django.core.cache import cache
    cache.clear()
    yield cache
    cache.clear()

# Mock fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis for testing."""
    import fakeredis
    return fakeredis.FakeStrictRedis()

@pytest.fixture
def mock_celery():
    """Mock Celery for testing."""
    from unittest.mock import Mock
    return Mock()