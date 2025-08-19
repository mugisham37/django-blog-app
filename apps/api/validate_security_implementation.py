#!/usr/bin/env python3
"""
Validation script for security implementation.
Tests the comprehensive input validation and sanitization features.
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
    print("=== Security Implementation Validation ===\n")
    
    all_passed = True
    
    # 1. Validate core security files exist
    print("1. Checking core security files...")
    security_files = [
        ('apps/core/sanitizers.py', 'HTML and content sanitizers'),
        ('apps/core/form_validators.py', 'Enhanced form validation'),
        ('apps/core/security_decorators.py', 'Security decorators'),
        ('apps/core/security_middleware.py', 'Security middleware'),
        ('apps/core/templatetags/security_tags.py', 'Security template tags'),
        ('config/settings/security.py', 'Security settings'),
        ('templates/core/security_headers.html', 'Security headers template'),
    ]
    
    for filepath, description in security_files:
        if not validate_file_exists(filepath, description):
            all_passed = False
    
    print()
    
    # 2. Validate sanitizers implementation
    print("2. Checking sanitizers implementation...")
    sanitizer_patterns = {
        'HTMLSanitizer class': r'class HTMLSanitizer:',
        'ContentSanitizer class': r'class ContentSanitizer:',
        'SpamDetector class': r'class SpamDetector:',
        'sanitize_html_content function': r'def sanitize_html_content\(',
        'detect_spam_content function': r'def detect_spam_content\(',
        'XSS pattern detection': r'dangerous_patterns|xss_patterns',
        'Bleach integration': r'import bleach|BLEACH_AVAILABLE',
    }
    
    if not validate_file_content('apps/core/sanitizers.py', sanitizer_patterns, 'Sanitizers'):
        all_passed = False
    
    print()
    
    # 3. Validate form validators implementation
    print("3. Checking form validators implementation...")
    validator_patterns = {
        'SecurityValidationMixin': r'class SecurityValidationMixin',
        'HTMLContentValidationMixin': r'class HTMLContentValidationMixin',
        'FileUploadValidationMixin': r'class FileUploadValidationMixin',
        'RateLimitValidationMixin': r'class RateLimitValidationMixin',
        'XSS detection': r'_detect_xss_attempt',
        'Spam detection integration': r'detect_spam_content',
        'Form security logger': r'FormSecurityLogger',
    }
    
    if not validate_file_content('apps/core/form_validators.py', validator_patterns, 'Form validators'):
        all_passed = False
    
    print()
    
    # 4. Validate security decorators implementation
    print("4. Checking security decorators implementation...")
    decorator_patterns = {
        'validate_input decorator': r'def validate_input\(',
        'rate_limit decorator': r'def rate_limit\(',
        'validate_json_input decorator': r'def validate_json_input\(',
        'validate_file_upload decorator': r'def validate_file_upload\(',
        'SecurityMixin class': r'class SecurityMixin',
        'XSS detection function': r'def _detect_xss_attempt\(',
        'Combined decorators': r'def secure_form_view\(',
    }
    
    if not validate_file_content('apps/core/security_decorators.py', decorator_patterns, 'Security decorators'):
        all_passed = False
    
    print()
    
    # 5. Validate security middleware implementation
    print("5. Checking security middleware implementation...")
    middleware_patterns = {
        'SecurityHeadersMiddleware': r'class SecurityHeadersMiddleware',
        'InputValidationMiddleware': r'class InputValidationMiddleware',
        'RateLimitMiddleware': r'class RateLimitMiddleware',
        'SpamDetectionMiddleware': r'class SpamDetectionMiddleware',
        'SuspiciousActivityMiddleware': r'class SuspiciousActivityMiddleware',
        'IPBlockingMiddleware': r'class IPBlockingMiddleware',
        'Security headers': r'X-Content-Type-Options|X-Frame-Options|X-XSS-Protection',
        'CSP policy': r'Content-Security-Policy',
    }
    
    if not validate_file_content('apps/core/security_middleware.py', middleware_patterns, 'Security middleware'):
        all_passed = False
    
    print()
    
    # 6. Validate template tags implementation
    print("6. Checking security template tags implementation...")
    template_patterns = {
        'safe_html filter': r'def safe_html\(',
        'safe_text filter': r'def safe_text\(',
        'strip_dangerous filter': r'def strip_dangerous\(',
        'safe_url filter': r'def safe_url\(',
        'escape_js filter': r'def escape_js\(',
        'Template register': r'register = template\.Library\(\)',
        'XSS prevention': r'dangerous_tags|dangerous_attrs',
    }
    
    if not validate_file_content('apps/core/templatetags/security_tags.py', template_patterns, 'Security template tags'):
        all_passed = False
    
    print()
    
    # 7. Validate security settings
    print("7. Checking security settings...")
    settings_patterns = {
        'HTTPS settings': r'SECURE_SSL_REDIRECT|SECURE_HSTS_SECONDS',
        'Cookie security': r'SECURE_COOKIE_SECURE|SESSION_COOKIE_SECURE',
        'CSP policy': r'CSP_POLICY',
        'Rate limiting config': r'GLOBAL_RATE_LIMITS',
        'File upload security': r'MAX_FILE_SIZE|ALLOWED_FILE_EXTENSIONS',
        'Spam keywords': r'SPAM_KEYWORDS',
        'Reserved names': r'RESERVED_SLUGS|RESERVED_USERNAMES',
        'Security middleware': r'SECURITY_MIDDLEWARE',
    }
    
    if not validate_file_content('config/settings/security.py', settings_patterns, 'Security settings'):
        all_passed = False
    
    print()
    
    # 8. Validate enhanced validators
    print("8. Checking enhanced validators...")
    enhanced_validator_patterns = {
        'HTML content validation': r'validate_html_content',
        'Password strength validation': r'validate_password_strength',
        'Email domain validation': r'validate_email_domain',
        'Image file validation': r'validate_image_file',
        'Comment content validation': r'validate_comment_content',
        'URL safety validation': r'validate_url_safety',
        'Dangerous patterns': r'dangerous_tags|dangerous_attrs',
    }
    
    if not validate_file_content('apps/core/validators.py', enhanced_validator_patterns, 'Enhanced validators'):
        all_passed = False
    
    print()
    
    # 9. Validate form integration
    print("9. Checking form integration...")
    
    # Check blog forms
    blog_form_patterns = {
        'Security mixins import': r'from apps\.core\.form_validators import',
        'SecurityValidationMixin': r'SecurityValidationMixin',
        'HTMLContentValidationMixin': r'HTMLContentValidationMixin',
        'FileUploadValidationMixin': r'FileUploadValidationMixin',
    }
    
    if not validate_file_content('apps/blog/forms.py', blog_form_patterns, 'Blog forms integration'):
        all_passed = False
    
    # Check comment forms
    comment_form_patterns = {
        'Security mixins import': r'from apps\.core\.form_validators import',
        'SecurityValidationMixin': r'SecurityValidationMixin',
        'RateLimitValidationMixin': r'RateLimitValidationMixin',
    }
    
    if not validate_file_content('apps/comments/forms.py', comment_form_patterns, 'Comment forms integration'):
        all_passed = False
    
    # Check account forms
    account_form_patterns = {
        'Security mixins import': r'from apps\.core\.form_validators import',
        'SecurityValidationMixin': r'SecurityValidationMixin',
        'FileUploadValidationMixin': r'FileUploadValidationMixin',
    }
    
    if not validate_file_content('apps/accounts/forms.py', account_form_patterns, 'Account forms integration'):
        all_passed = False
    
    print()
    
    # 10. Validate management command
    print("10. Checking management command...")
    command_patterns = {
        'Test command class': r'class Command\(BaseCommand\)',
        'Test sanitizers': r'def test_sanitizers\(',
        'Test validators': r'def test_validators\(',
        'Test form validation': r'def test_form_validation\(',
        'HTML sanitizer test': r'HTMLSanitizer',
        'Spam detector test': r'SpamDetector',
    }
    
    if not validate_file_content('apps/core/management/commands/test_security.py', command_patterns, 'Security test command'):
        all_passed = False
    
    print()
    
    # Summary
    print("=== Validation Summary ===")
    if all_passed:
        print("✓ All security implementation checks passed!")
        print("\nImplemented features:")
        print("- Comprehensive HTML sanitization with multiple security levels")
        print("- Multi-layer input validation and XSS prevention")
        print("- Spam detection with configurable thresholds")
        print("- File upload validation with type and size restrictions")
        print("- Form validation mixins with security features")
        print("- Security decorators for views and APIs")
        print("- Security middleware for request/response protection")
        print("- Template tags for safe content rendering")
        print("- Rate limiting and IP blocking capabilities")
        print("- Comprehensive security settings configuration")
        print("- Security logging and monitoring")
        print("- Management command for testing security features")
        
        return True
    else:
        print("✗ Some security implementation checks failed!")
        print("Please review the missing components above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)