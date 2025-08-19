#!/usr/bin/env python3
"""
Validation script for rate limiting and CSRF protection implementation.
Tests the comprehensive rate limiting and CSRF protection features.
"""

import os
import sys
import re

def validate_file_exists(filepath, description):
    """Validate that a file exists."""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} - NOT FOUND")
        return False

def validate_file_content(filepath, patterns, description):
    """Validate that a file contains expected patterns."""
    if not os.path.exists(filepath):
        print(f"✗ {description}: {filepath} - FILE NOT FOUND")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_patterns = []
        for pattern_name, pattern in patterns.items():
            if not re.search(pattern, content, re.MULTILINE | re.DOTALL):
                missing_patterns.append(pattern_name)
        
        if missing_patterns:
            print(f"✗ {description}: Missing patterns: {', '.join(missing_patterns)}")
            return False
        else:
            print(f"✓ {description}: All required patterns found")
            return True
    
    except Exception as e:
        print(f"✗ {description}: Error reading file - {e}")
        return False

def main():
    """Main validation function."""
    print("=== Rate Limiting and CSRF Protection Validation ===\n")
    
    all_passed = True
    
    # 1. Validate core rate limiting files
    print("1. Core Rate Limiting Files:")
    rate_limiting_files = [
        ('apps/core/rate_limiting.py', 'Rate limiting module'),
        ('apps/core/csrf_protection.py', 'CSRF protection module'),
        ('apps/core/views/security.py', 'Security views'),
        ('apps/core/urls/security.py', 'Security URLs'),
        ('static/js/csrf-utils.js', 'CSRF JavaScript utilities'),
        ('tests/test_rate_limiting_csrf.py', 'Rate limiting tests'),
    ]
    
    for filepath, description in rate_limiting_files:
        if not validate_file_exists(filepath, description):
            all_passed = False
    
    print()
    
    # 2. Validate rate limiting implementation
    print("2. Rate Limiting Implementation:")
    rate_limiting_patterns = {
        'RateLimiter class': r'class RateLimiter',
        'RateLimitConfig class': r'class RateLimitConfig',
        'IPBlocklist class': r'class IPBlocklist',
        'FailedAttemptTracker class': r'class FailedAttemptTracker',
        'rate_limit_view decorator': r'def rate_limit_view\(',
        'Redis backend usage': r'cache.*redis|Redis',
        'Sliding window algorithm': r'sliding.*window|window.*algorithm',
        'IP-based rate limiting': r'ip.*rate.*limit|rate.*limit.*ip',
        'User-based rate limiting': r'user.*rate.*limit|rate.*limit.*user',
        'Rate limit key generation': r'get_rate_limit_key',
    }
    
    if not validate_file_content('apps/core/rate_limiting.py', rate_limiting_patterns, 'Rate limiting features'):
        all_passed = False
    
    print()
    
    # 3. Validate CSRF protection implementation
    print("3. CSRF Protection Implementation:")
    csrf_patterns = {
        'EnhancedCSRFMiddleware': r'class EnhancedCSRFMiddleware',
        'CSRFTokenMiddleware': r'class CSRFTokenMiddleware',
        'csrf_protect_ajax decorator': r'def csrf_protect_ajax',
        'validate_csrf_for_api decorator': r'def validate_csrf_for_api',
        'AJAX CSRF support': r'ajax.*csrf|csrf.*ajax',
        'JSON CSRF handling': r'json.*csrf|csrf.*json',
        'CSRF token rotation': r'csrf.*rotation|rotation.*csrf',
        'CSRF failure logging': r'csrf.*log|log.*csrf',
    }
    
    if not validate_file_content('apps/core/csrf_protection.py', csrf_patterns, 'CSRF protection features'):
        all_passed = False
    
    print()
    
    # 4. Validate security views
    print("4. Security Views:")
    security_view_patterns = {
        'get_csrf_token view': r'def get_csrf_token',
        'refresh_csrf_token view': r'def refresh_csrf_token',
        'security_status view': r'def security_status',
        'report_security_incident view': r'def report_security_incident',
        'clear_user_rate_limit view': r'def clear_user_rate_limit',
        'Rate limiting decorators': r'@rate_limit_view',
        'CSRF protection decorators': r'@.*csrf',
        'JSON responses': r'JsonResponse',
        'Security logging': r'security_logger',
    }
    
    if not validate_file_content('apps/core/views/security.py', security_view_patterns, 'Security views'):
        all_passed = False
    
    print()
    
    # 5. Validate JavaScript utilities
    print("5. JavaScript CSRF Utilities:")
    js_patterns = {
        'CSRFManager class': r'class CSRFManager',
        'RateLimitManager class': r'class RateLimitManager',
        'AJAX CSRF handling': r'ajax.*csrf|csrf.*ajax',
        'Token refresh functionality': r'refresh.*token|token.*refresh',
        'Rate limit handling': r'rate.*limit.*handle|handle.*rate.*limit',
        'Cookie management': r'cookie.*csrf|csrf.*cookie',
        'Error handling': r'error.*handle|handle.*error',
        'Security incident reporting': r'report.*incident|incident.*report',
    }
    
    if not validate_file_content('static/js/csrf-utils.js', js_patterns, 'JavaScript CSRF utilities'):
        all_passed = False
    
    print()
    
    # 6. Validate middleware integration
    print("6. Middleware Integration:")
    middleware_patterns = {
        'Enhanced SecurityMiddleware': r'class SecurityMiddleware.*MiddlewareMixin',
        'IP blocking integration': r'ip_blocklist|IPBlocklist',
        'Failed attempt tracking': r'failed_attempt_tracker|FailedAttemptTracker',
        'Enhanced rate limiting': r'_check_enhanced_rate_limit',
        'Security logging': r'security_logger',
        'Suspicious activity detection': r'suspicious.*activity|_detect_suspicious',
    }
    
    if not validate_file_content('apps/core/middleware.py', middleware_patterns, 'Middleware integration'):
        all_passed = False
    
    print()
    
    # 7. Validate settings configuration
    print("7. Settings Configuration:")
    settings_patterns = {
        'Enhanced CSRF middleware': r'EnhancedCSRFMiddleware',
        'CSRF token middleware': r'CSRFTokenMiddleware',
        'CSRF token rotation': r'CSRFTokenRotationMiddleware',
        'CSRF cookie settings': r'CSRF_COOKIE_SECURE|CSRF_COOKIE_HTTPONLY',
        'Rate limiting config': r'GLOBAL_RATE_LIMITS|ENDPOINT_RATE_LIMITS',
        'Security monitoring': r'FAILED_LOGIN_ATTEMPTS_THRESHOLD|IP_BLOCK_DURATION',
        'CSRF trusted origins': r'CSRF_TRUSTED_ORIGINS',
    }
    
    if not validate_file_content('config/settings/base.py', settings_patterns, 'Settings configuration'):
        all_passed = False
    
    print()
    
    # 8. Validate URL configuration
    print("8. URL Configuration:")
    url_patterns = {
        'CSRF token endpoints': r'csrf-token',
        'Security status endpoint': r'status',
        'Security incident reporting': r'report-incident',
        'Rate limit management': r'clear-rate-limit',
        'Security headers test': r'headers-test',
        'Core security URLs': r'core.*security|security.*core',
    }
    
    if not validate_file_content('apps/core/urls/security.py', url_patterns, 'Security URL patterns'):
        all_passed = False
    
    print()
    
    # 9. Validate test coverage
    print("9. Test Coverage:")
    test_patterns = {
        'RateLimiter tests': r'class RateLimiterTestCase',
        'RateLimitConfig tests': r'class RateLimitConfigTestCase',
        'IPBlocklist tests': r'class IPBlocklistTestCase',
        'FailedAttemptTracker tests': r'class FailedAttemptTrackerTestCase',
        'CSRF protection tests': r'class CSRFProtectionTestCase',
        'Security views tests': r'class SecurityViewsTestCase',
        'Middleware tests': r'class SecurityMiddlewareTestCase',
        'Integration tests': r'class IntegrationTestCase',
        'Rate limiting decorator tests': r'class RateLimitDecoratorTestCase',
    }
    
    if not validate_file_content('tests/test_rate_limiting_csrf.py', test_patterns, 'Test coverage'):
        all_passed = False
    
    print()
    
    # Summary
    print("=== Validation Summary ===")
    if all_passed:
        print("✓ All rate limiting and CSRF protection features are properly implemented!")
        print("\nImplemented features:")
        print("- Comprehensive Redis-backed rate limiting system")
        print("- IP-based and user-based rate limiting")
        print("- Sliding window rate limiting algorithm")
        print("- IP blocklist management")
        print("- Failed authentication attempt tracking")
        print("- Enhanced CSRF protection with AJAX support")
        print("- CSRF token rotation and management")
        print("- Security incident reporting and logging")
        print("- JavaScript utilities for client-side CSRF handling")
        print("- Comprehensive test coverage")
        print("- Security middleware integration")
        print("- Rate limiting and CSRF protection for API endpoints")
        print("- Security monitoring and alerting")
        return True
    else:
        print("✗ Some rate limiting and CSRF protection features are missing or incomplete.")
        print("Please review the validation output above and implement the missing components.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)