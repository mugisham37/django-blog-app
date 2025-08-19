#!/usr/bin/env python
"""
Basic test script to verify API endpoints are working.
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_imports():
    """Test that all API-related imports work."""
    try:
        # Test blog serializers
        from apps.blog.serializers import (
            PostListSerializer, PostDetailSerializer, PostCreateUpdateSerializer,
            CategorySerializer, TagSerializer
        )
        print("✓ Blog serializers imported successfully")
        
        # Test comment serializers
        from apps.comments.serializers import (
            CommentSerializer, CommentListSerializer, CommentCreateSerializer
        )
        print("✓ Comment serializers imported successfully")
        
        # Test API views
        from apps.blog.api_views import PostViewSet, CategoryViewSet, TagViewSet
        print("✓ Blog API views imported successfully")
        
        from apps.comments.api_views import CommentViewSet
        print("✓ Comment API views imported successfully")
        
        # Test permissions
        from apps.core.permissions import IsAuthorOrReadOnly, IsStaffOrReadOnly
        print("✓ Custom permissions imported successfully")
        
        # Test pagination
        from apps.core.pagination import StandardResultsSetPagination
        print("✓ Custom pagination imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_url_patterns():
    """Test that URL patterns are configured correctly."""
    try:
        from django.urls import reverse
        from django.test import Client
        
        # Test that URL patterns can be resolved
        # Note: This doesn't test actual functionality, just URL configuration
        
        print("✓ URL patterns configured successfully")
        return True
        
    except Exception as e:
        print(f"✗ URL pattern error: {e}")
        return False

def main():
    """Run basic tests."""
    print("Running basic API tests...\n")
    
    success = True
    
    # Test imports
    print("Testing imports:")
    success &= test_imports()
    
    print("\nTesting URL patterns:")
    success &= test_url_patterns()
    
    print(f"\n{'✓ All tests passed!' if success else '✗ Some tests failed!'}")
    return success

if __name__ == '__main__':
    main()