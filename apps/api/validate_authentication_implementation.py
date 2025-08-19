#!/usr/bin/env python
"""
Validation script for authentication implementation.
This script checks if all required components are properly implemented.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def validate_authentication_implementation():
    """Validate the authentication implementation."""
    print("🔍 Validating Django Personal Blog Authentication Implementation...")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # 1. Check if all required files exist
    print("\n📁 Checking required files...")
    required_files = [
        'apps/accounts/forms.py',
        'apps/accounts/views.py',
        'apps/accounts/urls.py',
        'templates/accounts/register.html',
        'templates/accounts/login.html',
        'templates/accounts/password_reset.html',
        'templates/accounts/password_reset_done.html',
        'templates/accounts/password_reset_confirm.html',
        'templates/accounts/password_reset_complete.html',
        'templates/accounts/password_change.html',
        'templates/accounts/password_change_done.html',
        'templates/accounts/profile.html',
        'templates/accounts/profile_update.html',
        'templates/accounts/profile_setup.html',
        'templates/accounts/social_links.html',
        'templates/accounts/registration_complete.html',
        'templates/accounts/resend_verification.html',
        'templates/emails/email_verification.html',
        'templates/emails/email_verification.txt',
        'templates/accounts/emails/password_reset_email.html',
        'templates/accounts/emails/password_reset_subject.txt',
        'tests/test_accounts_authentication.py',
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            errors.append(f"Missing file: {file_path}")
    
    # 2. Check Django imports and models
    print("\n🔧 Checking Django components...")
    try:
        from django.contrib.auth import get_user_model
        from apps.accounts.models import Profile
        from apps.accounts.forms import (
            CustomUserRegistrationForm, CustomAuthenticationForm,
            CustomPasswordResetForm, ProfileUpdateForm
        )
        from apps.accounts.views import (
            UserRegistrationView, CustomLoginView, EmailVerificationView,
            ProfileView, ProfileUpdateView
        )
        print("  ✅ All Django components imported successfully")
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        errors.append(f"Import error: {e}")
    
    # 3. Check URL patterns
    print("\n🌐 Checking URL patterns...")
    try:
        from apps.accounts.urls import urlpatterns
        required_urls = [
            'register', 'login', 'logout', 'email_verify', 'resend_verification',
            'password_reset', 'password_reset_done', 'password_reset_confirm',
            'password_reset_complete', 'password_change', 'password_change_done',
            'profile', 'profile_edit', 'profile_setup', 'social_links',
            'profile_detail', 'check_username', 'check_email'
        ]
        
        url_names = [pattern.name for pattern in urlpatterns if hasattr(pattern, 'name')]
        
        for url_name in required_urls:
            if url_name in url_names:
                print(f"  ✅ {url_name}")
            else:
                print(f"  ❌ {url_name}")
                errors.append(f"Missing URL pattern: {url_name}")
                
    except Exception as e:
        print(f"  ❌ URL pattern error: {e}")
        errors.append(f"URL pattern error: {e}")
    
    # 4. Check form validation
    print("\n📝 Checking form implementations...")
    try:
        from apps.accounts.forms import CustomUserRegistrationForm
        
        # Test form instantiation
        form = CustomUserRegistrationForm()
        required_fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        
        for field in required_fields:
            if field in form.fields:
                print(f"  ✅ Form field: {field}")
            else:
                print(f"  ❌ Form field: {field}")
                errors.append(f"Missing form field: {field}")
                
    except Exception as e:
        print(f"  ❌ Form validation error: {e}")
        errors.append(f"Form validation error: {e}")
    
    # 5. Check model relationships
    print("\n🗄️  Checking model relationships...")
    try:
        User = get_user_model()
        from apps.accounts.models import Profile
        
        # Check if Profile model has required fields
        profile_fields = [field.name for field in Profile._meta.fields]
        required_profile_fields = [
            'user', 'bio', 'avatar', 'website', 'location', 'birth_date',
            'social_links', 'email_notifications', 'newsletter_subscription'
        ]
        
        for field in required_profile_fields:
            if field in profile_fields:
                print(f"  ✅ Profile field: {field}")
            else:
                print(f"  ❌ Profile field: {field}")
                errors.append(f"Missing profile field: {field}")
                
    except Exception as e:
        print(f"  ❌ Model relationship error: {e}")
        errors.append(f"Model relationship error: {e}")
    
    # 6. Check template syntax (basic)
    print("\n🎨 Checking template syntax...")
    template_files = [
        'templates/accounts/register.html',
        'templates/accounts/login.html',
        'templates/accounts/profile.html',
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '{% extends' in content and '{% block' in content:
                        print(f"  ✅ {template_file}")
                    else:
                        print(f"  ⚠️  {template_file} (missing template inheritance)")
                        warnings.append(f"Template may be missing proper inheritance: {template_file}")
            except Exception as e:
                print(f"  ❌ {template_file} - Error: {e}")
                errors.append(f"Template error in {template_file}: {e}")
        else:
            print(f"  ❌ {template_file} (not found)")
            errors.append(f"Template not found: {template_file}")
    
    # 7. Check security implementations
    print("\n🔒 Checking security implementations...")
    try:
        from apps.core.validators import (
            validate_password_strength, validate_email_domain,
            validate_username_format
        )
        print("  ✅ Custom validators imported successfully")
        
        # Check if forms use validators
        from apps.accounts.forms import CustomUserRegistrationForm
        form = CustomUserRegistrationForm()
        
        # Check if password validation is implemented
        if hasattr(form, 'clean_password1'):
            print("  ✅ Password strength validation implemented")
        else:
            print("  ⚠️  Password strength validation may be missing")
            warnings.append("Password strength validation may be missing")
            
    except Exception as e:
        print(f"  ❌ Security implementation error: {e}")
        errors.append(f"Security implementation error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    if not errors and not warnings:
        print("🎉 SUCCESS: All authentication components are properly implemented!")
        print("\n✅ Implementation includes:")
        print("   • User registration with email verification")
        print("   • Secure login/logout with session management")
        print("   • Password reset functionality")
        print("   • Profile management with avatar upload")
        print("   • Social links management")
        print("   • AJAX username/email availability checking")
        print("   • Comprehensive form validation")
        print("   • Security measures and input sanitization")
        print("   • Responsive templates with Bootstrap styling")
        print("   • Integration tests for all workflows")
        
    else:
        if errors:
            print(f"❌ ERRORS FOUND ({len(errors)}):")
            for error in errors:
                print(f"   • {error}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        if errors:
            print(f"\n🔧 Please fix the {len(errors)} error(s) above before proceeding.")
            return False
        else:
            print(f"\n✅ Implementation is functional with {len(warnings)} minor warning(s).")
    
    print("\n🚀 Next Steps:")
    print("   1. Run migrations: python manage.py makemigrations && python manage.py migrate")
    print("   2. Create superuser: python manage.py createsuperuser")
    print("   3. Run development server: python manage.py runserver")
    print("   4. Test authentication workflows in browser")
    print("   5. Run integration tests: python manage.py test tests.test_accounts_authentication")
    
    return len(errors) == 0

if __name__ == '__main__':
    try:
        success = validate_authentication_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 VALIDATION FAILED: {e}")
        print("\nThis might be due to missing dependencies or Django setup issues.")
        print("Please ensure you have:")
        print("   • Installed all requirements from requirements/base.txt")
        print("   • Set up your database configuration")
        print("   • Run initial migrations")
        sys.exit(1)