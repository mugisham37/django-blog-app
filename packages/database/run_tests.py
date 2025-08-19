#!/usr/bin/env python
"""
Test runner for the enterprise database package.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner


def setup_django():
    """Set up Django for testing."""
    # Add the src directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    sys.path.insert(0, src_dir)
    
    # Configure Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    
    # Setup Django
    django.setup()


def run_tests():
    """Run the test suite."""
    setup_django()
    
    # Get the Django test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True, keepdb=False)
    
    # Define test modules to run
    test_modules = [
        'tests.test_repositories',
        'tests.test_connections',
        'tests.test_config',
        'tests.test_migrations',
        'tests.test_monitoring',
        'tests.test_routers',
    ]
    
    # Run tests
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    run_tests()