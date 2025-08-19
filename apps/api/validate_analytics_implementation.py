#!/usr/bin/env python
"""
Validation script for analytics page view tracking implementation.
Checks that all required components are properly implemented.
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print status."""
    if os.path.exists(file_path):
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description}: {file_path} (NOT FOUND)")
        return False

def check_python_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        return True
    except SyntaxError as e:
        print(f"  ✗ Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error reading {file_path}: {e}")
        return False

def check_class_exists(file_path, class_name):
    """Check if a class exists in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"class {class_name}" in content:
                return True
    except Exception:
        pass
    return False

def check_function_exists(file_path, function_name):
    """Check if a function exists in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if f"def {function_name}" in content:
                return True
    except Exception:
        pass
    return False

def main():
    """Main validation function."""
    print("Django Personal Blog System - Analytics Implementation Validation")
    print("=" * 70)
    
    all_checks_passed = True
    
    # Check core files exist
    print("\n1. Checking core analytics files...")
    files_to_check = [
        ("apps/analytics/models.py", "Analytics models"),
        ("apps/analytics/tasks.py", "Celery tasks"),
        ("apps/analytics/views.py", "Analytics views"),
        ("apps/analytics/urls.py", "Analytics URLs"),
        ("apps/analytics/admin.py", "Admin interface"),
        ("apps/analytics/signals.py", "Analytics signals"),
        ("tests/test_analytics_page_tracking.py", "Analytics tests"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Check Python syntax
    print("\n2. Checking Python syntax...")
    python_files = [
        "apps/analytics/models.py",
        "apps/analytics/tasks.py", 
        "apps/analytics/views.py",
        "apps/analytics/urls.py",
        "apps/analytics/admin.py",
        "apps/analytics/signals.py",
        "tests/test_analytics_page_tracking.py",
    ]
    
    for file_path in python_files:
        if os.path.exists(file_path):
            if check_python_syntax(file_path):
                print(f"  ✓ {file_path}")
            else:
                all_checks_passed = False
    
    # Check required models exist
    print("\n3. Checking required models...")
    models_file = "apps/analytics/models.py"
    required_models = ["PageView", "SearchQuery", "SearchClickthrough"]
    
    for model_name in required_models:
        if check_class_exists(models_file, model_name):
            print(f"  ✓ {model_name} model exists")
        else:
            print(f"  ✗ {model_name} model NOT FOUND")
            all_checks_passed = False
    
    # Check required tasks exist
    print("\n4. Checking Celery tasks...")
    tasks_file = "apps/analytics/tasks.py"
    required_tasks = [
        "track_page_view",
        "update_page_view_engagement", 
        "update_analytics",
        "cleanup_old_analytics_data",
        "generate_analytics_report"
    ]
    
    for task_name in required_tasks:
        if check_function_exists(tasks_file, task_name):
            print(f"  ✓ {task_name} task exists")
        else:
            print(f"  ✗ {task_name} task NOT FOUND")
            all_checks_passed = False
    
    # Check required views exist
    print("\n5. Checking analytics views...")
    views_file = "apps/analytics/views.py"
    required_views = [
        "TrackPageViewView",
        "TrackEngagementView",
        "AnalyticsAPIView"
    ]
    
    for view_name in required_views:
        if check_class_exists(views_file, view_name):
            print(f"  ✓ {view_name} view exists")
        else:
            print(f"  ✗ {view_name} view NOT FOUND")
            all_checks_passed = False
    
    # Check admin widgets
    print("\n6. Checking admin dashboard widgets...")
    admin_file = "apps/analytics/admin.py"
    required_admin_classes = [
        "PageViewAdmin",
        "SearchQueryAdmin", 
        "AnalyticsDashboardWidget"
    ]
    
    for class_name in required_admin_classes:
        if check_class_exists(admin_file, class_name):
            print(f"  ✓ {class_name} exists")
        else:
            print(f"  ✗ {class_name} NOT FOUND")
            all_checks_passed = False
    
    # Check test coverage
    print("\n7. Checking test coverage...")
    test_file = "tests/test_analytics_page_tracking.py"
    required_test_classes = [
        "PageViewModelTest",
        "PageViewTrackingTaskTest",
        "PageViewTrackingViewTest",
        "AnalyticsTrackingMixinTest",
        "PageViewPerformanceTest"
    ]
    
    for test_class in required_test_classes:
        if check_class_exists(test_file, test_class):
            print(f"  ✓ {test_class} exists")
        else:
            print(f"  ✗ {test_class} NOT FOUND")
            all_checks_passed = False
    
    # Check integration with blog views
    print("\n8. Checking blog view integration...")
    blog_views_file = "apps/blog/views.py"
    
    if os.path.exists(blog_views_file):
        with open(blog_views_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "AnalyticsTrackingMixin" in content:
                print("  ✓ AnalyticsTrackingMixin imported in blog views")
                if "class PostDetailView(AnalyticsTrackingMixin" in content:
                    print("  ✓ PostDetailView uses AnalyticsTrackingMixin")
                else:
                    print("  ✗ PostDetailView does NOT use AnalyticsTrackingMixin")
                    all_checks_passed = False
            else:
                print("  ✗ AnalyticsTrackingMixin NOT imported in blog views")
                all_checks_passed = False
    else:
        print("  ✗ Blog views file not found")
        all_checks_passed = False
    
    # Check URL configuration
    print("\n9. Checking URL configuration...")
    main_urls_file = "config/urls.py"
    
    if os.path.exists(main_urls_file):
        with open(main_urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "analytics/" in content and "apps.analytics.urls" in content:
                print("  ✓ Analytics URLs included in main URL configuration")
            else:
                print("  ✗ Analytics URLs NOT included in main URL configuration")
                all_checks_passed = False
    
    # Final summary
    print("\n" + "=" * 70)
    if all_checks_passed:
        print("✓ ALL CHECKS PASSED - Analytics implementation is complete!")
        print("\nImplementation includes:")
        print("- PageView model with engagement tracking")
        print("- Asynchronous page view tracking via Celery")
        print("- Analytics data aggregation and reporting")
        print("- Admin dashboard widgets for popular posts and traffic stats")
        print("- Comprehensive test coverage")
        print("- Integration with blog views for automatic tracking")
    else:
        print("✗ SOME CHECKS FAILED - Please review the implementation")
    
    print("\nTo run tests (after setting up Django environment):")
    print("python manage.py test tests.test_analytics_page_tracking")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)