#!/usr/bin/env python
"""
Simple validation script for Profile model implementation.
This script validates the model structure and basic functionality.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
if not settings.configured:
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
            'apps.core',
            'apps.accounts',
        ],
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
        MEDIA_ROOT='/tmp/test_media',
        STATIC_URL='/static/',
        MAX_IMAGE_SIZE=5 * 1024 * 1024,
    )

django.setup()

# Now we can import our models
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile
from apps.accounts.managers import ProfileManager

User = get_user_model()

def validate_profile_model():
    """Validate the Profile model structure and basic functionality."""
    print("🔍 Validating Profile model...")
    
    # Test 1: Model structure
    print("✅ Testing model structure...")
    
    # Check that Profile model exists
    assert Profile is not None, "Profile model should exist"
    
    # Check that Profile has the expected fields
    expected_fields = [
        'user', 'bio', 'avatar', 'avatar_thumbnail', 'website', 'location',
        'birth_date', 'social_links', 'email_notifications', 'newsletter_subscription',
        'is_author', 'author_bio', 'show_email', 'show_birth_date',
        'posts_count', 'comments_count', 'profile_views', 'created_at', 'updated_at'
    ]
    
    profile_fields = [field.name for field in Profile._meta.fields]
    for field in expected_fields:
        assert field in profile_fields, f"Profile should have {field} field"
    
    print("✅ Model structure validation passed")
    
    # Test 2: Manager
    print("✅ Testing custom manager...")
    
    assert hasattr(Profile, 'objects'), "Profile should have objects manager"
    assert isinstance(Profile.objects, ProfileManager), "Profile should use ProfileManager"
    
    # Check manager methods exist
    manager_methods = ['authors', 'with_social_links', 'newsletter_subscribers', 
                      'by_posts_count', 'by_comments_count', 'most_viewed']
    for method in manager_methods:
        assert hasattr(Profile.objects, method), f"ProfileManager should have {method} method"
    
    print("✅ Manager validation passed")
    
    # Test 3: Model methods
    print("✅ Testing model methods...")
    
    # Check that Profile has expected methods
    expected_methods = [
        'get_full_name', 'get_display_name', 'get_social_link', 'set_social_link',
        'get_age', 'increment_profile_views', 'get_avatar_url'
    ]
    
    for method in expected_methods:
        assert hasattr(Profile, method), f"Profile should have {method} method"
    
    print("✅ Model methods validation passed")
    
    # Test 4: Properties
    print("✅ Testing model properties...")
    
    expected_properties = ['is_complete', 'completion_percentage']
    for prop in expected_properties:
        assert hasattr(Profile, prop), f"Profile should have {prop} property"
    
    print("✅ Properties validation passed")
    
    # Test 5: Meta options
    print("✅ Testing meta options...")
    
    assert Profile._meta.verbose_name == 'Profile', "Verbose name should be set"
    assert Profile._meta.verbose_name_plural == 'Profiles', "Verbose name plural should be set"
    assert Profile._meta.ordering == ['-created_at'], "Ordering should be by created_at desc"
    
    print("✅ Meta options validation passed")
    
    print("🎉 All Profile model validations passed!")

def validate_managers():
    """Validate the custom managers."""
    print("🔍 Validating custom managers...")
    
    # Test ProfileManager
    from apps.accounts.managers import ProfileManager, CustomUserManager
    
    # Check ProfileManager methods
    manager = ProfileManager()
    manager.model = Profile
    
    # These methods should exist and be callable
    methods_to_test = [
        'get_queryset', 'complete_profiles', 'authors', 'with_social_links',
        'newsletter_subscribers', 'by_posts_count', 'by_comments_count', 'most_viewed'
    ]
    
    for method_name in methods_to_test:
        method = getattr(manager, method_name)
        assert callable(method), f"{method_name} should be callable"
    
    print("✅ ProfileManager validation passed")
    
    # Test CustomUserManager
    user_manager = CustomUserManager()
    user_manager.model = User
    
    assert hasattr(user_manager, 'create_user'), "CustomUserManager should have create_user method"
    assert hasattr(user_manager, 'create_superuser'), "CustomUserManager should have create_superuser method"
    
    print("✅ CustomUserManager validation passed")
    print("🎉 All manager validations passed!")

def validate_admin():
    """Validate admin configuration."""
    print("🔍 Validating admin configuration...")
    
    from apps.accounts.admin import ProfileAdmin, CustomUserAdmin, ProfileInline
    
    # Check that admin classes exist
    assert ProfileAdmin is not None, "ProfileAdmin should exist"
    assert CustomUserAdmin is not None, "CustomUserAdmin should exist"
    assert ProfileInline is not None, "ProfileInline should exist"
    
    # Check ProfileAdmin configuration
    assert hasattr(ProfileAdmin, 'list_display'), "ProfileAdmin should have list_display"
    assert hasattr(ProfileAdmin, 'list_filter'), "ProfileAdmin should have list_filter"
    assert hasattr(ProfileAdmin, 'search_fields'), "ProfileAdmin should have search_fields"
    assert hasattr(ProfileAdmin, 'fieldsets'), "ProfileAdmin should have fieldsets"
    
    print("✅ Admin configuration validation passed")
    print("🎉 All admin validations passed!")

if __name__ == '__main__':
    try:
        validate_profile_model()
        validate_managers()
        validate_admin()
        print("\n🎉 ALL VALIDATIONS PASSED! Profile model implementation is complete.")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)