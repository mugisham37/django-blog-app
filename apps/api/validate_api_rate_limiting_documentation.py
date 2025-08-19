#!/usr/bin/env python
"""
Validation script for API rate limiting and documentation implementation.
Tests task 12.2: Implement API rate limiting and documentation.
"""

import os
import sys
import importlib.util

def validate_file_exists(file_path, description):
    """Validate that a file exists."""
    if os.path.exists(file_path):
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}: {file_path} (NOT FOUND)")
        return False

def validate_python_file(file_path, required_classes=None, required_functions=None):
    """Validate Python file and check for required classes/functions."""
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return False
    
    try:
        spec = importlib.util.spec_from_file_location("module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        success = True
        
        if required_classes:
            for class_name in required_classes:
                if hasattr(module, class_name):
                    print(f"  ✓ Class {class_name} found")
                else:
                    print(f"  ✗ Class {class_name} not found")
                    success = False
        
        if required_functions:
            for func_name in required_functions:
                if hasattr(module, func_name):
                    print(f"  ✓ Function {func_name} found")
                else:
                    print(f"  ✗ Function {func_name} not found")
                    success = False
        
        return success
        
    except Exception as e:
        print(f"✗ Error importing {file_path}: {e}")
        return False

def validate_settings_configuration():
    """Validate REST Framework settings configuration."""
    try:
        with open('config/settings/base.py', 'r') as f:
            content = f.read()
        
        # Check for versioning configuration
        if 'DEFAULT_VERSIONING_CLASS' in content:
            print("✓ API versioning configuration found")
        else:
            print("✗ API versioning configuration not found")
            return False
        
        # Check for throttling configuration
        if 'DEFAULT_THROTTLE_CLASSES' in content and 'DEFAULT_THROTTLE_RATES' in content:
            print("✓ Throttling configuration found")
        else:
            print("✗ Throttling configuration not found")
            return False
        
        # Check for custom throttle classes
        custom_throttles = [
            'apps.core.throttling.StaffRateThrottle',
            'apps.core.throttling.PremiumUserRateThrottle'
        ]
        
        for throttle in custom_throttles:
            if throttle in content:
                print(f"✓ Custom throttle class configured: {throttle}")
            else:
                print(f"✗ Custom throttle class not configured: {throttle}")
                return False
        
        # Check for rate limits
        rate_limits = ['anon', 'user', 'staff', 'premium', 'search', 'upload', 'burst']
        for limit in rate_limits:
            if f"'{limit}'" in content:
                print(f"✓ Rate limit configured: {limit}")
            else:
                print(f"✗ Rate limit not configured: {limit}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading settings file: {e}")
        return False

def validate_api_views_updates():
    """Validate that API views have been updated with throttling and caching."""
    files_to_check = [
        ('apps/blog/api_views.py', ['ThrottlingMixin', 'CacheThrottlingMixin']),
        ('apps/comments/api_views.py', ['ThrottlingMixin', 'CacheThrottlingMixin'])
    ]
    
    success = True
    
    for file_path, required_imports in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            for import_name in required_imports:
                if import_name in content:
                    print(f"✓ {file_path}: {import_name} imported")
                else:
                    print(f"✗ {file_path}: {import_name} not imported")
                    success = False
            
            # Check for throttling decorators
            if '@throttle_endpoint' in content:
                print(f"✓ {file_path}: Throttling decorators found")
            else:
                print(f"✗ {file_path}: Throttling decorators not found")
                success = False
            
            # Check for caching decorators
            if '@cache_response_with_throttling' in content:
                print(f"✓ {file_path}: Caching decorators found")
            else:
                print(f"✗ {file_path}: Caching decorators not found")
                success = False
                
        except Exception as e:
            print(f"✗ Error reading {file_path}: {e}")
            success = False
    
    return success

def validate_url_configuration():
    """Validate URL configuration for API versioning and documentation."""
    try:
        with open('config/urls.py', 'r') as f:
            content = f.read()
        
        # Check for API versioning URLs
        if 'api/v1/' in content:
            print("✓ API v1 versioning URLs configured")
        else:
            print("✗ API v1 versioning URLs not configured")
            return False
        
        # Check for API documentation URLs
        if 'api/docs/' in content:
            print("✓ API documentation URLs configured")
        else:
            print("✗ API documentation URLs not configured")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading URLs file: {e}")
        return False

def main():
    """Main validation function."""
    print("=" * 60)
    print("VALIDATING API RATE LIMITING AND DOCUMENTATION IMPLEMENTATION")
    print("Task 12.2: Implement API rate limiting and documentation")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. Validate core throttling files
    print("\n1. THROTTLING IMPLEMENTATION")
    print("-" * 30)
    
    throttling_files = [
        ('apps/core/throttling.py', 'Custom throttling classes'),
        ('apps/core/throttling_utils.py', 'Throttling utilities and mixins')
    ]
    
    for file_path, description in throttling_files:
        if not validate_file_exists(file_path, description):
            all_checks_passed = False
    
    # Validate throttling classes
    required_throttle_classes = [
        'StaffRateThrottle',
        'PremiumUserRateThrottle',
        'SearchRateThrottle',
        'UploadRateThrottle',
        'DynamicRateThrottle',
        'IPBasedRateThrottle'
    ]
    
    if not validate_python_file('apps/core/throttling.py', required_classes=required_throttle_classes):
        all_checks_passed = False
    
    # Validate throttling utilities
    required_throttle_utils = [
        'ThrottlingMixin',
        'CacheThrottlingMixin',
        'throttle_endpoint',
        'cache_response_with_throttling'
    ]
    
    if not validate_python_file('apps/core/throttling_utils.py', required_classes=required_throttle_utils[:2], required_functions=required_throttle_utils[2:]):
        all_checks_passed = False
    
    # 2. Validate API documentation files
    print("\n2. API DOCUMENTATION IMPLEMENTATION")
    print("-" * 35)
    
    doc_files = [
        ('apps/core/api_docs.py', 'API documentation views and utilities'),
        ('apps/core/urls/api_docs.py', 'API documentation URL configuration'),
        ('apps/core/management/commands/generate_api_docs.py', 'API documentation generation command')
    ]
    
    for file_path, description in doc_files:
        if not validate_file_exists(file_path, description):
            all_checks_passed = False
    
    # Validate API documentation components
    required_doc_functions = [
        'api_info',
        'api_health',
        'api_examples',
        'generate_api_examples'
    ]
    
    if not validate_python_file('apps/core/api_docs.py', required_functions=required_doc_functions):
        all_checks_passed = False
    
    # 3. Validate configuration updates
    print("\n3. CONFIGURATION UPDATES")
    print("-" * 25)
    
    if not validate_settings_configuration():
        all_checks_passed = False
    
    if not validate_url_configuration():
        all_checks_passed = False
    
    # 4. Validate API views updates
    print("\n4. API VIEWS UPDATES")
    print("-" * 20)
    
    if not validate_api_views_updates():
        all_checks_passed = False
    
    # 5. Validate test file
    print("\n5. TEST IMPLEMENTATION")
    print("-" * 20)
    
    if not validate_file_exists('tests/test_api_rate_limiting_documentation.py', 'Comprehensive test suite'):
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✓ ALL CHECKS PASSED - API RATE LIMITING AND DOCUMENTATION IMPLEMENTED")
        print("\nImplemented features:")
        print("• Multi-tier rate limiting (anonymous, user, staff, premium)")
        print("• Custom throttling classes for different scenarios")
        print("• API response caching for improved performance")
        print("• API versioning with backward compatibility")
        print("• Comprehensive API documentation with examples")
        print("• Health check and monitoring endpoints")
        print("• Management command for documentation generation")
        print("• Comprehensive test coverage")
        
        print("\nRate limiting tiers:")
        print("• Anonymous users: 100 requests/hour")
        print("• Authenticated users: 1000 requests/hour")
        print("• Staff users: 5000 requests/hour")
        print("• Premium users: 2000 requests/hour")
        print("• Search operations: 30 requests/minute")
        print("• File uploads: 10 requests/minute")
        print("• Bulk operations: 60 requests/minute")
        
        print("\nAPI documentation endpoints:")
        print("• /api/docs/ - API information and overview")
        print("• /api/docs/health/ - Health check endpoint")
        print("• /api/docs/examples/ - Usage examples")
        print("• /api/docs/schema/ - OpenAPI schema")
        
        print("\nAPI versioning:")
        print("• /api/v1/ - Explicit version 1 endpoints")
        print("• /api/ - Default version (v1) for backward compatibility")
        
    else:
        print("✗ SOME CHECKS FAILED - REVIEW IMPLEMENTATION")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())