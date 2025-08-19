#!/usr/bin/env python
"""
Validation script for Comment model and hierarchical functionality.
This script validates the implementation without running Django tests.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.blog.models import Post, Category
from apps.comments.models import Comment

User = get_user_model()


def validate_comment_model():
    """
    Validate Comment model implementation.
    """
    print("🔍 Validating Comment Model Implementation...")
    
    # Test 1: Model Structure
    print("\n1. Testing Comment Model Structure...")
    
    # Check required fields exist
    required_fields = ['content', 'author', 'post', 'parent', 'is_approved', 'ip_address', 'user_agent']
    model_fields = [field.name for field in Comment._meta.get_fields()]
    
    for field in required_fields:
        if field in model_fields:
            print(f"   ✅ Field '{field}' exists")
        else:
            print(f"   ❌ Field '{field}' missing")
            return False
    
    # Test 2: Managers
    print("\n2. Testing Custom Managers...")
    
    if hasattr(Comment, 'objects') and hasattr(Comment.objects, 'get_thread_comments'):
        print("   ✅ CommentManager with get_thread_comments method exists")
    else:
        print("   ❌ CommentManager missing get_thread_comments method")
        return False
    
    if hasattr(Comment, 'approved'):
        print("   ✅ ApprovedCommentManager exists")
    else:
        print("   ❌ ApprovedCommentManager missing")
        return False
    
    # Test 3: Create test data
    print("\n3. Creating test data...")
    
    try:
        # Create test user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print("   ✅ Test user created")
        
        # Create test category and post
        category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test post content.',
            author=user,
            category=category,
            status='published'
        )
        print("   ✅ Test post created")
        
    except Exception as e:
        print(f"   ❌ Error creating test data: {e}")
        return False
    
    # Test 4: Comment Creation
    print("\n4. Testing Comment Creation...")
    
    try:
        comment = Comment.objects.create(
            content='This is a test comment.',
            author=user,
            post=post,
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        print("   ✅ Comment created successfully")
        print(f"   ✅ Comment string representation: {str(comment)}")
        
    except Exception as e:
        print(f"   ❌ Error creating comment: {e}")
        return False
    
    # Test 5: Hierarchical Structure
    print("\n5. Testing Hierarchical Structure...")
    
    try:
        # Create parent comment
        parent_comment = Comment.objects.create(
            content='Parent comment',
            author=user,
            post=post,
            ip_address='127.0.0.1'
        )
        
        # Create child comment
        child_comment = Comment.objects.create(
            content='Child comment',
            author=user,
            post=post,
            parent=parent_comment,
            ip_address='127.0.0.1'
        )
        
        # Test relationships
        if child_comment.parent == parent_comment:
            print("   ✅ Parent-child relationship works")
        else:
            print("   ❌ Parent-child relationship failed")
            return False
        
        if child_comment in parent_comment.replies.all():
            print("   ✅ Reverse relationship works")
        else:
            print("   ❌ Reverse relationship failed")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing hierarchy: {e}")
        return False
    
    # Test 6: Depth Calculation
    print("\n6. Testing Depth Calculation...")
    
    try:
        # Create nested comments
        grandchild_comment = Comment.objects.create(
            content='Grandchild comment',
            author=user,
            post=post,
            parent=child_comment,
            ip_address='127.0.0.1'
        )
        
        # Test depth calculation
        if parent_comment.get_depth() == 0:
            print("   ✅ Parent depth is 0")
        else:
            print(f"   ❌ Parent depth is {parent_comment.get_depth()}, expected 0")
            return False
        
        if child_comment.get_depth() == 1:
            print("   ✅ Child depth is 1")
        else:
            print(f"   ❌ Child depth is {child_comment.get_depth()}, expected 1")
            return False
        
        if grandchild_comment.get_depth() == 2:
            print("   ✅ Grandchild depth is 2")
        else:
            print(f"   ❌ Grandchild depth is {grandchild_comment.get_depth()}, expected 2")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing depth calculation: {e}")
        return False
    
    # Test 7: Tree Traversal Methods
    print("\n7. Testing Tree Traversal Methods...")
    
    try:
        # Test get_root_comment
        if grandchild_comment.get_root_comment() == parent_comment:
            print("   ✅ get_root_comment works")
        else:
            print("   ❌ get_root_comment failed")
            return False
        
        # Test get_ancestors
        ancestors = grandchild_comment.get_ancestors()
        if len(ancestors) == 2 and ancestors[0] == parent_comment and ancestors[1] == child_comment:
            print("   ✅ get_ancestors works")
        else:
            print("   ❌ get_ancestors failed")
            return False
        
        # Test get_descendants
        descendants = parent_comment.get_descendants()
        if len(descendants) >= 2:  # Should include child and grandchild
            print("   ✅ get_descendants works")
        else:
            print("   ❌ get_descendants failed")
            return False
        
        # Test can_be_replied_to
        if parent_comment.can_be_replied_to():
            print("   ✅ can_be_replied_to works for shallow comments")
        else:
            print("   ❌ can_be_replied_to failed for shallow comments")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing tree traversal: {e}")
        return False
    
    # Test 8: Approval Methods
    print("\n8. Testing Approval Methods...")
    
    try:
        # Test initial state
        if not comment.is_approved:
            print("   ✅ Comment starts unapproved")
        else:
            print("   ❌ Comment should start unapproved")
            return False
        
        # Test approval
        comment.approve()
        comment.refresh_from_db()
        if comment.is_approved:
            print("   ✅ approve() method works")
        else:
            print("   ❌ approve() method failed")
            return False
        
        # Test rejection
        comment.reject()
        comment.refresh_from_db()
        if not comment.is_approved:
            print("   ✅ reject() method works")
        else:
            print("   ❌ reject() method failed")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing approval methods: {e}")
        return False
    
    # Test 9: Manager Methods
    print("\n9. Testing Manager Methods...")
    
    try:
        # Test get_thread_comments
        thread_comments = Comment.objects.get_thread_comments(post)
        print(f"   ✅ get_thread_comments returned {thread_comments.count()} comments")
        
        # Test get_root_comments
        root_comments = Comment.objects.get_root_comments(post)
        print(f"   ✅ get_root_comments returned {root_comments.count()} root comments")
        
        # Test get_comment_count
        comment_count = Comment.objects.get_comment_count(post)
        print(f"   ✅ get_comment_count returned {comment_count} comments")
        
    except Exception as e:
        print(f"   ❌ Error testing manager methods: {e}")
        return False
    
    # Test 10: Validation
    print("\n10. Testing Validation...")
    
    try:
        # Test content length validation
        short_comment = Comment(
            content='Short',  # Less than 10 characters
            author=user,
            post=post,
            ip_address='127.0.0.1'
        )
        
        try:
            short_comment.clean()
            print("   ❌ Content length validation failed")
            return False
        except ValidationError:
            print("   ✅ Content length validation works")
        
        # Test circular reference prevention
        comment.parent = comment
        try:
            comment.clean()
            print("   ❌ Circular reference validation failed")
            return False
        except ValidationError:
            print("   ✅ Circular reference validation works")
        
    except Exception as e:
        print(f"   ❌ Error testing validation: {e}")
        return False
    
    print("\n✅ All Comment Model tests passed!")
    return True


def cleanup_test_data():
    """
    Clean up test data.
    """
    print("\n🧹 Cleaning up test data...")
    try:
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(username='testuser').delete()
        print("   ✅ Test data cleaned up")
    except Exception as e:
        print(f"   ⚠️  Error cleaning up: {e}")


if __name__ == '__main__':
    try:
        success = validate_comment_model()
        if success:
            print("\n🎉 Comment Model Implementation Validation: PASSED")
        else:
            print("\n❌ Comment Model Implementation Validation: FAILED")
            sys.exit(1)
    finally:
        cleanup_test_data()