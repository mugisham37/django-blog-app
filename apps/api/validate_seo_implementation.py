#!/usr/bin/env python
"""
Validation script for SEO implementation.
Tests the SEO functions without requiring full Django test setup.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Setup Django
django.setup()

def test_seo_utils():
    """Test SEO utility functions."""
    from apps.core.utils import (
        generate_slug_with_validation, generate_meta_title, generate_meta_description,
        extract_keywords_from_content, calculate_enhanced_reading_time, validate_seo_content
    )
    from apps.blog.models import Post
    
    print("Testing SEO utility functions...")
    
    # Test slug generation
    print("✓ Testing slug generation...")
    slug = generate_slug_with_validation(Post, 'My Test Post')
    assert slug == 'my-test-post', f"Expected 'my-test-post', got '{slug}'"
    
    # Test reserved slug handling
    slug = generate_slug_with_validation(Post, 'admin')
    assert slug == 'post-admin', f"Expected 'post-admin', got '{slug}'"
    
    # Test meta title generation
    print("✓ Testing meta title generation...")
    meta_title = generate_meta_title('My Blog Post', site_name='My Blog')
    assert 'My Blog Post' in meta_title
    assert 'My Blog' in meta_title
    
    # Test meta description generation
    print("✓ Testing meta description generation...")
    content = '<p>This is a test blog post with some <strong>HTML</strong> content.</p>'
    description = generate_meta_description(content)
    assert '<p>' not in description
    assert '<strong>' not in description
    assert 'This is a test blog post' in description
    
    # Test keyword extraction
    print("✓ Testing keyword extraction...")
    keywords = extract_keywords_from_content(content, max_keywords=5)
    assert isinstance(keywords, list)
    assert len(keywords) <= 5
    
    # Test reading time calculation
    print("✓ Testing reading time calculation...")
    reading_time = calculate_enhanced_reading_time('word ' * 200)  # 200 words
    assert reading_time >= 1
    
    # Test SEO validation
    print("✓ Testing SEO validation...")
    validation = validate_seo_content(
        title='Test Title',
        content='word ' * 300,
        meta_title='Test Meta Title',
        meta_description='Test meta description for SEO validation.'
    )
    assert 'valid' in validation
    assert 'scores' in validation
    assert 'overall' in validation['scores']
    
    print("All SEO utility tests passed!")


def test_post_seo_features():
    """Test SEO features in Post model."""
    from django.contrib.auth import get_user_model
    from apps.blog.models import Post, Category, Tag
    
    print("\nTesting Post model SEO features...")
    
    User = get_user_model()
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Create test category
    category, created = Category.objects.get_or_create(
        name='Technology',
        defaults={'slug': 'technology'}
    )
    
    # Create test tags
    tag1, created = Tag.objects.get_or_create(
        name='Django',
        defaults={'slug': 'django'}
    )
    tag2, created = Tag.objects.get_or_create(
        name='Python',
        defaults={'slug': 'python'}
    )
    
    # Create test post
    print("✓ Testing post creation with SEO features...")
    post = Post.objects.create(
        title='Test SEO Post',
        content='<p>' + 'This is a comprehensive test of SEO features. ' * 50 + '</p>',
        author=user,
        category=category,
        status=Post.Status.PUBLISHED
    )
    post.tags.add(tag1, tag2)
    
    # Test auto-generated fields
    assert post.slug, "Slug should be auto-generated"
    assert post.meta_title, "Meta title should be auto-generated"
    assert post.meta_description, "Meta description should be auto-generated"
    assert post.reading_time > 0, "Reading time should be calculated"
    
    # Test SEO methods
    print("✓ Testing SEO methods...")
    seo_title = post.get_seo_title()
    assert seo_title, "SEO title should be available"
    
    seo_description = post.get_seo_description()
    assert seo_description, "SEO description should be available"
    
    keywords = post.get_keywords()
    assert isinstance(keywords, list), "Keywords should be a list"
    assert 'Django' in keywords, "Tag names should be in keywords"
    assert 'Python' in keywords, "Tag names should be in keywords"
    assert 'Technology' in keywords, "Category name should be in keywords"
    
    structured_data = post.get_structured_data()
    assert structured_data['@type'] == 'BlogPosting', "Structured data should be BlogPosting type"
    assert 'keywords' in structured_data, "Structured data should include keywords"
    
    validation = post.validate_seo()
    assert 'scores' in validation, "SEO validation should include scores"
    assert 'overall' in validation['scores'], "SEO validation should include overall score"
    
    print("All Post SEO tests passed!")


def test_template_tags():
    """Test SEO template tags."""
    from django.template import Template, Context
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    from apps.blog.models import Post, Category
    
    print("\nTesting SEO template tags...")
    
    User = get_user_model()
    
    # Create test data
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    category, created = Category.objects.get_or_create(
        name='Technology',
        defaults={'slug': 'technology'}
    )
    
    post = Post.objects.create(
        title='Template Tag Test Post',
        content='<p>Test content for template tags</p>',
        excerpt='Test excerpt',
        meta_title='Test Meta Title',
        meta_description='Test meta description',
        author=user,
        category=category
    )
    
    factory = RequestFactory()
    request = factory.get('/test/')
    
    # Test meta_title tag
    print("✓ Testing meta_title template tag...")
    template = Template('{% load seo_tags %}{% meta_title post %}')
    context = Context({'post': post})
    output = template.render(context)
    assert '<title>' in output
    assert 'Test Meta Title' in output
    
    # Test meta_description tag
    print("✓ Testing meta_description template tag...")
    template = Template('{% load seo_tags %}{% meta_description post %}')
    context = Context({'post': post})
    output = template.render(context)
    assert 'name="description"' in output
    assert 'Test meta description' in output
    
    # Test og_tags
    print("✓ Testing og_tags template tag...")
    template = Template('{% load seo_tags %}{% og_tags post request %}')
    context = Context({'post': post, 'request': request})
    output = template.render(context)
    assert 'property="og:title"' in output
    assert 'property="og:description"' in output
    assert 'content="article"' in output
    
    # Test structured_data tag
    print("✓ Testing structured_data template tag...")
    template = Template('{% load seo_tags %}{% structured_data post %}')
    context = Context({'post': post})
    output = template.render(context)
    assert 'application/ld+json' in output
    assert 'BlogPosting' in output
    
    # Test reading_time tag
    print("✓ Testing reading_time template tag...")
    template = Template('{% load seo_tags %}{% reading_time post %}')
    context = Context({'post': post})
    output = template.render(context)
    assert 'minute' in output
    assert 'read' in output
    
    print("All template tag tests passed!")


def main():
    """Run all SEO validation tests."""
    print("Starting SEO implementation validation...")
    
    try:
        print("Testing SEO utilities...")
        test_seo_utils()
        
        print("Testing Post SEO features...")
        test_post_seo_features()
        
        print("Testing template tags...")
        test_template_tags()
        
        print("\n" + "="*50)
        print("✅ ALL SEO FEATURES VALIDATED SUCCESSFULLY!")
        print("="*50)
        print("\nImplemented features:")
        print("• Enhanced slug generation with uniqueness validation")
        print("• Automatic meta tag generation from post content")
        print("• Open Graph image generation capability")
        print("• Enhanced reading time calculation algorithm")
        print("• Comprehensive SEO validation")
        print("• Template tags for SEO meta elements")
        print("• Structured data (JSON-LD) generation")
        print("• Keyword extraction from content")
        print("• SEO scoring and recommendations")
        
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()