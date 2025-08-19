"""
Unit tests for blog models.
Tests for Category, Tag, and Post models including relationships and custom methods.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.blog.models import Category, Tag, Post

User = get_user_model()


class CategoryModelTest(TestCase):
    """
    Test cases for Category model including hierarchy and manager methods.
    """
    
    def setUp(self):
        """
        Set up test data for category tests.
        """
        # Create root categories
        self.tech_category = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Technology related posts',
            is_active=True,
            sort_order=1
        )
        
        self.lifestyle_category = Category.objects.create(
            name='Lifestyle',
            slug='lifestyle',
            description='Lifestyle related posts',
            is_active=True,
            sort_order=2
        )
        
        # Create child categories
        self.programming_category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming tutorials and tips',
            parent=self.tech_category,
            is_active=True,
            sort_order=1
        )
        
        self.web_dev_category = Category.objects.create(
            name='Web Development',
            slug='web-development',
            description='Web development topics',
            parent=self.programming_category,
            is_active=True,
            sort_order=1
        )
        
        # Create inactive category
        self.inactive_category = Category.objects.create(
            name='Inactive Category',
            slug='inactive-category',
            is_active=False
        )
    
    def test_category_creation(self):
        """Test basic category creation."""
        category = Category.objects.create(
            name='Test Category',
            description='Test description'
        )
        
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.slug, 'test-category')  # Auto-generated
        self.assertEqual(category.description, 'Test description')
        self.assertTrue(category.is_active)
        self.assertEqual(category.sort_order, 0)
        self.assertIsNone(category.parent)
    
    def test_category_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        category = Category.objects.create(name='Test Category Name')
        self.assertEqual(category.slug, 'test-category-name')
    
    def test_category_unique_constraints(self):
        """Test unique constraints on name and slug."""
        # Test unique name constraint
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Technology')
        
        # Test unique slug constraint
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Different Name', slug='technology')
    
    def test_category_str_representation(self):
        """Test string representation of category."""
        self.assertEqual(str(self.tech_category), 'Technology')
    
    def test_category_get_absolute_url(self):
        """Test get_absolute_url method."""
        expected_url = '/blog/category/technology/'
        # Note: This test assumes URL pattern exists
        # In actual implementation, you might need to adjust based on your URL configuration
        self.assertTrue(self.tech_category.get_absolute_url().endswith('technology/'))
    
    def test_category_hierarchy_methods(self):
        """Test hierarchy-related methods."""
        # Test get_level
        self.assertEqual(self.tech_category.get_level(), 0)  # Root category
        self.assertEqual(self.programming_category.get_level(), 1)  # Child
        self.assertEqual(self.web_dev_category.get_level(), 2)  # Grandchild
        
        # Test get_full_path
        self.assertEqual(self.tech_category.get_full_path(), 'Technology')
        self.assertEqual(self.programming_category.get_full_path(), 'Technology > Programming')
        self.assertEqual(self.web_dev_category.get_full_path(), 'Technology > Programming > Web Development')
        
        # Test get_children
        children = list(self.tech_category.get_children())
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], self.programming_category)
        
        # Test get_ancestors
        ancestors = self.web_dev_category.get_ancestors()
        self.assertEqual(len(ancestors), 2)
        self.assertIn(self.programming_category, ancestors)
        self.assertIn(self.tech_category, ancestors)
        
        # Test get_descendants
        descendants = self.tech_category.get_descendants()
        self.assertEqual(len(descendants), 2)
        self.assertIn(self.programming_category, descendants)
        self.assertIn(self.web_dev_category, descendants)
    
    def test_category_validation(self):
        """Test category validation rules."""
        # Test self-parent validation
        category = Category.objects.create(name='Test Category')
        category.parent = category
        
        with self.assertRaises(ValidationError):
            category.clean()
        
        # Test circular reference validation
        self.programming_category.parent = self.web_dev_category
        
        with self.assertRaises(ValidationError):
            self.programming_category.clean()
    
    def test_category_manager_active(self):
        """Test CategoryManager active method."""
        active_categories = Category.objects.active()
        
        self.assertIn(self.tech_category, active_categories)
        self.assertIn(self.lifestyle_category, active_categories)
        self.assertNotIn(self.inactive_category, active_categories)
    
    def test_category_manager_root_categories(self):
        """Test CategoryManager root_categories method."""
        root_categories = list(Category.objects.root_categories())
        
        self.assertEqual(len(root_categories), 2)
        self.assertIn(self.tech_category, root_categories)
        self.assertIn(self.lifestyle_category, root_categories)
        self.assertNotIn(self.programming_category, root_categories)
    
    def test_category_manager_get_tree(self):
        """Test CategoryManager get_tree method."""
        tree = Category.objects.get_tree()
        
        self.assertEqual(len(tree), 2)  # Two root categories
        
        # Find technology category in tree
        tech_in_tree = next(cat for cat in tree if cat.name == 'Technology')
        self.assertEqual(len(tech_in_tree.children), 1)
        self.assertEqual(tech_in_tree.children[0].name, 'Programming')
        
        # Check nested children
        programming_in_tree = tech_in_tree.children[0]
        self.assertEqual(len(programming_in_tree.children), 1)
        self.assertEqual(programming_in_tree.children[0].name, 'Web Development')
    
    def test_category_manager_get_descendants(self):
        """Test CategoryManager get_descendants method."""
        descendants = Category.objects.get_descendants(self.tech_category)
        
        self.assertEqual(len(descendants), 2)
        self.assertIn(self.programming_category, descendants)
        self.assertIn(self.web_dev_category, descendants)
    
    def test_category_manager_get_ancestors(self):
        """Test CategoryManager get_ancestors method."""
        ancestors = Category.objects.get_ancestors(self.web_dev_category)
        
        self.assertEqual(len(ancestors), 2)
        self.assertEqual(ancestors[0], self.programming_category)  # Direct parent first
        self.assertEqual(ancestors[1], self.tech_category)  # Then grandparent
    
    def test_category_ordering(self):
        """Test category ordering by sort_order and name."""
        categories = list(Category.objects.all().order_by('sort_order', 'name'))
        
        # Should be ordered by sort_order first, then name
        self.assertEqual(categories[0], self.tech_category)  # sort_order=1
        self.assertEqual(categories[1], self.lifestyle_category)  # sort_order=2
    
    def test_category_meta_options(self):
        """Test model meta options."""
        meta = Category._meta
        
        self.assertEqual(meta.verbose_name_plural, 'categories')
        self.assertEqual(meta.ordering, ['sort_order', 'name'])
        
        # Check indexes exist
        index_fields = [index.fields for index in meta.indexes]
        self.assertIn(['is_active', 'sort_order'], index_fields)
        self.assertIn(['parent', 'is_active'], index_fields)


class TagModelTest(TestCase):
    """
    Test cases for Tag model including usage tracking and manager methods.
    """
    
    def setUp(self):
        """
        Set up test data for tag tests.
        """
        # Create tags with different usage counts
        self.python_tag = Tag.objects.create(
            name='Python',
            slug='python',
            description='Python programming language',
            color='#3776ab',
            usage_count=10
        )
        
        self.django_tag = Tag.objects.create(
            name='Django',
            slug='django',
            description='Django web framework',
            color='#092e20',
            usage_count=8
        )
        
        self.javascript_tag = Tag.objects.create(
            name='JavaScript',
            slug='javascript',
            description='JavaScript programming language',
            color='#f7df1e',
            usage_count=5
        )
        
        self.unused_tag = Tag.objects.create(
            name='Unused Tag',
            slug='unused-tag',
            description='A tag that is not used',
            color='#6c757d',
            usage_count=0
        )
    
    def test_tag_creation(self):
        """Test basic tag creation."""
        tag = Tag.objects.create(
            name='Test Tag',
            description='Test description',
            color='#ff0000'
        )
        
        self.assertEqual(tag.name, 'Test Tag')
        self.assertEqual(tag.slug, 'test-tag')  # Auto-generated
        self.assertEqual(tag.description, 'Test description')
        self.assertEqual(tag.color, '#ff0000')
        self.assertEqual(tag.usage_count, 0)
    
    def test_tag_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        tag = Tag.objects.create(name='Test Tag Name')
        self.assertEqual(tag.slug, 'test-tag-name')
    
    def test_tag_unique_constraints(self):
        """Test unique constraints on name and slug."""
        # Test unique name constraint
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='Python')
        
        # Test unique slug constraint
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='Different Name', slug='python')
    
    def test_tag_str_representation(self):
        """Test string representation of tag."""
        self.assertEqual(str(self.python_tag), 'Python')
    
    def test_tag_get_absolute_url(self):
        """Test get_absolute_url method."""
        # Note: This test assumes URL pattern exists
        self.assertTrue(self.python_tag.get_absolute_url().endswith('python/'))
    
    def test_tag_usage_methods(self):
        """Test tag usage increment and decrement methods."""
        initial_count = self.python_tag.usage_count
        
        # Test increment
        self.python_tag.increment_usage()
        self.assertEqual(self.python_tag.usage_count, initial_count + 1)
        
        # Test decrement
        self.python_tag.decrement_usage()
        self.assertEqual(self.python_tag.usage_count, initial_count)
        
        # Test decrement doesn't go below 0
        self.unused_tag.decrement_usage()
        self.assertEqual(self.unused_tag.usage_count, 0)
    
    def test_tag_validation(self):
        """Test tag validation rules."""
        # Test valid color format
        tag = Tag(name='Valid Tag', color='#ff0000')
        tag.clean()  # Should not raise
        
        # Test invalid color format
        tag.color = 'invalid-color'
        with self.assertRaises(ValidationError):
            tag.clean()
        
        # Test invalid color format (wrong length)
        tag.color = '#ff00'
        with self.assertRaises(ValidationError):
            tag.clean()
        
        # Test valid name with allowed characters
        tag.name = 'Valid Tag-Name_123'
        tag.color = '#ff0000'
        tag.clean()  # Should not raise
        
        # Test invalid name with special characters
        tag.name = 'Invalid@Tag!'
        with self.assertRaises(ValidationError):
            tag.clean()
    
    def test_tag_manager_popular(self):
        """Test TagManager popular method."""
        popular_tags = list(Tag.objects.popular(limit=3))
        
        # Should be ordered by usage_count descending
        self.assertEqual(len(popular_tags), 3)
        self.assertEqual(popular_tags[0], self.python_tag)  # usage_count=10
        self.assertEqual(popular_tags[1], self.django_tag)  # usage_count=8
        self.assertEqual(popular_tags[2], self.javascript_tag)  # usage_count=5
        
        # Should not include unused tags
        self.assertNotIn(self.unused_tag, popular_tags)
    
    def test_tag_manager_suggest_similar(self):
        """Test TagManager suggest_similar method."""
        # Create a tag with similar name
        Tag.objects.create(name='Python3', slug='python3')
        
        similar_tags = list(Tag.objects.suggest_similar('python'))
        
        # Should find tags containing 'python' but not exact match
        self.assertEqual(len(similar_tags), 1)
        self.assertEqual(similar_tags[0].name, 'Python3')
        self.assertNotIn(self.python_tag, similar_tags)  # Exact match excluded
    
    def test_tag_manager_get_tag_cloud_data(self):
        """Test TagManager get_tag_cloud_data method."""
        cloud_data = Tag.objects.get_tag_cloud_data(min_usage=1, max_tags=10)
        
        # Should return tags with usage > 0, ordered by usage
        self.assertEqual(len(cloud_data), 3)  # Excludes unused_tag
        self.assertEqual(cloud_data[0], self.python_tag)
        
        # Check relative sizes are calculated
        for tag in cloud_data:
            self.assertTrue(hasattr(tag, 'relative_size'))
            self.assertGreaterEqual(tag.relative_size, 1)
            self.assertLessEqual(tag.relative_size, 5)
    
    def test_tag_manager_unused_tags(self):
        """Test TagManager unused_tags method."""
        unused_tags = list(Tag.objects.unused_tags())
        
        self.assertEqual(len(unused_tags), 1)
        self.assertEqual(unused_tags[0], self.unused_tag)
    
    def test_tag_ordering(self):
        """Test tag ordering by name."""
        tags = list(Tag.objects.all())
        
        # Should be ordered by name alphabetically
        tag_names = [tag.name for tag in tags]
        self.assertEqual(tag_names, sorted(tag_names))
    
    def test_tag_meta_options(self):
        """Test model meta options."""
        meta = Tag._meta
        
        self.assertEqual(meta.ordering, ['name'])
        
        # Check indexes exist
        index_fields = [index.fields for index in meta.indexes]
        self.assertIn(['usage_count'], index_fields)
        self.assertIn(['name'], index_fields)
    
    def test_tag_default_values(self):
        """Test tag default values."""
        tag = Tag.objects.create(name='Default Test')
        
        self.assertEqual(tag.color, '#007bff')  # Default color
        self.assertEqual(tag.usage_count, 0)  # Default usage count
        self.assertEqual(tag.description, '')  # Default empty description


class PostModelTest(TestCase):
    """
    Test cases for Post model including relationships, status workflow, and custom methods.
    """
    
    def setUp(self):
        """
        Set up test data for post tests.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test tags
        self.tag1 = Tag.objects.create(name='Tag1', slug='tag1')
        self.tag2 = Tag.objects.create(name='Tag2', slug='tag2')
        
        # Create test posts
        self.draft_post = Post.objects.create(
            title='Draft Post',
            slug='draft-post',
            content='This is a draft post content.',
            author=self.user,
            category=self.category,
            status=Post.Status.DRAFT
        )
        
        self.published_post = Post.objects.create(
            title='Published Post',
            slug='published-post',
            content='This is a published post content with more words to test reading time calculation.',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=1),
            view_count=100,
            is_featured=True
        )
        
        self.scheduled_post = Post.objects.create(
            title='Scheduled Post',
            slug='scheduled-post',
            content='This is a scheduled post content.',
            author=self.user,
            category=self.category,
            status=Post.Status.SCHEDULED,
            published_at=timezone.now() + timedelta(days=1)
        )
        
        # Add tags to published post
        self.published_post.tags.add(self.tag1, self.tag2)
    
    def test_post_creation(self):
        """Test basic post creation."""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user
        )
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.slug, 'test-post')  # Auto-generated
        self.assertEqual(post.content, 'Test content')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.status, Post.Status.DRAFT)  # Default status
        self.assertFalse(post.is_featured)
        self.assertTrue(post.allow_comments)
        self.assertEqual(post.view_count, 0)
        self.assertGreater(post.reading_time, 0)  # Should be calculated
    
    def test_post_slug_auto_generation(self):
        """Test automatic slug generation from title."""
        post = Post.objects.create(
            title='Test Post Title With Spaces',
            content='Test content',
            author=self.user
        )
        self.assertEqual(post.slug, 'test-post-title-with-spaces')
    
    def test_post_excerpt_auto_generation(self):
        """Test automatic excerpt generation from content."""
        long_content = 'This is a very long content. ' * 20  # Make it long
        post = Post.objects.create(
            title='Test Post',
            content=long_content,
            author=self.user
        )
        
        self.assertTrue(post.excerpt)
        self.assertLessEqual(len(post.excerpt), 253)  # 250 + '...'
        self.assertTrue(post.excerpt.endswith('...'))
    
    def test_post_reading_time_calculation(self):
        """Test reading time calculation."""
        # Create post with known word count
        content = ' '.join(['word'] * 400)  # 400 words
        post = Post.objects.create(
            title='Reading Time Test',
            content=content,
            author=self.user
        )
        
        # Should be 2 minutes (400 words / 200 words per minute)
        self.assertEqual(post.reading_time, 2)
    
    def test_post_published_at_auto_set(self):
        """Test that published_at is set when status changes to published."""
        from django.utils import timezone
        
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            status=Post.Status.DRAFT
        )
        
        # Should not have published_at initially
        self.assertIsNone(post.published_at)
        
        # Change status to published
        post.status = Post.Status.PUBLISHED
        post.save()
        
        # Should now have published_at
        self.assertIsNotNone(post.published_at)
        self.assertLessEqual(post.published_at, timezone.now())
    
    def test_post_str_representation(self):
        """Test string representation of post."""
        self.assertEqual(str(self.draft_post), 'Draft Post')
    
    def test_post_get_absolute_url(self):
        """Test get_absolute_url method."""
        self.assertTrue(self.draft_post.get_absolute_url().endswith('draft-post/'))
    
    def test_post_status_methods(self):
        """Test post status-related methods."""
        # Test is_published
        self.assertTrue(self.published_post.is_published())
        self.assertFalse(self.draft_post.is_published())
        self.assertFalse(self.scheduled_post.is_published())  # Future date
        
        # Test can_be_published
        self.assertTrue(self.draft_post.can_be_published())
        
        # Test post without required fields
        incomplete_post = Post(title='', content='', author=None)
        self.assertFalse(incomplete_post.can_be_published())
    
    def test_post_view_count_increment(self):
        """Test view count increment method."""
        initial_count = self.published_post.view_count
        self.published_post.increment_view_count()
        
        self.assertEqual(self.published_post.view_count, initial_count + 1)
    
    def test_post_navigation_methods(self):
        """Test get_previous_post and get_next_post methods."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create additional posts for navigation testing
        older_post = Post.objects.create(
            title='Older Post',
            content='Older content',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now() - timedelta(days=2)
        )
        
        newer_post = Post.objects.create(
            title='Newer Post',
            content='Newer content',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        # Test navigation from published_post
        previous = self.published_post.get_previous_post()
        next_post = self.published_post.get_next_post()
        
        self.assertEqual(previous, older_post)
        self.assertEqual(next_post, newer_post)
    
    def test_post_related_posts(self):
        """Test get_related_posts method."""
        # Create related post with shared tags
        related_post = Post.objects.create(
            title='Related Post',
            content='Related content',
            author=self.user,
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        related_post.tags.add(self.tag1)  # Share one tag
        
        # Create unrelated post
        unrelated_post = Post.objects.create(
            title='Unrelated Post',
            content='Unrelated content',
            author=self.user,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now()
        )
        
        related_posts = list(self.published_post.get_related_posts())
        
        self.assertIn(related_post, related_posts)
        self.assertNotIn(unrelated_post, related_posts)
        self.assertNotIn(self.published_post, related_posts)  # Exclude self
    
    def test_post_display_methods(self):
        """Test display helper methods."""
        # Test get_status_display_with_date
        status_display = self.published_post.get_status_display_with_date()
        self.assertIn('Published on', status_display)
        
        scheduled_display = self.scheduled_post.get_status_display_with_date()
        self.assertIn('Scheduled for', scheduled_display)
        
        # Test get_reading_time_display
        reading_time_display = self.published_post.get_reading_time_display()
        self.assertTrue(reading_time_display.endswith('read'))
    
    def test_post_validation(self):
        """Test post validation rules."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Test scheduled post validation - missing publish date
        post = Post(
            title='Test',
            content='Test',
            author=self.user,
            status=Post.Status.SCHEDULED
        )
        with self.assertRaises(ValidationError):
            post.clean()
        
        # Test scheduled post validation - past publish date
        post.published_at = timezone.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            post.clean()
        
        # Test published post validation - missing title
        post = Post(
            title='',
            content='Test content',
            author=self.user,
            status=Post.Status.PUBLISHED
        )
        with self.assertRaises(ValidationError):
            post.clean()
        
        # Test published post validation - missing content
        post = Post(
            title='Test Title',
            content='',
            author=self.user,
            status=Post.Status.PUBLISHED
        )
        with self.assertRaises(ValidationError):
            post.clean()
    
    def test_post_managers(self):
        """Test custom post managers."""
        # Test PostManager (default)
        all_posts = list(Post.objects.all())
        self.assertIn(self.draft_post, all_posts)
        self.assertIn(self.published_post, all_posts)
        self.assertIn(self.scheduled_post, all_posts)
        
        # Test PublishedPostManager
        published_posts = list(Post.published.all())
        self.assertIn(self.published_post, published_posts)
        self.assertNotIn(self.draft_post, published_posts)
        self.assertNotIn(self.scheduled_post, published_posts)  # Future date
        
        # Test DraftPostManager
        draft_posts = list(Post.drafts.all())
        self.assertIn(self.draft_post, draft_posts)
        self.assertNotIn(self.published_post, draft_posts)
        self.assertNotIn(self.scheduled_post, draft_posts)
    
    def test_post_unique_constraints(self):
        """Test unique constraints on slug."""
        with self.assertRaises(IntegrityError):
            Post.objects.create(
                title='Different Title',
                slug='draft-post',  # Same slug as existing post
                content='Different content',
                author=self.user
            )
    
    def test_post_ordering(self):
        """Test post ordering by published_at and created_at."""
        posts = list(Post.objects.all())
        
        # Should be ordered by published_at (desc), then created_at (desc)
        for i in range(len(posts) - 1):
            current_post = posts[i]
            next_post = posts[i + 1]
            
            # Compare published_at first, then created_at
            if current_post.published_at and next_post.published_at:
                self.assertGreaterEqual(current_post.published_at, next_post.published_at)
            elif current_post.published_at is None and next_post.published_at is None:
                self.assertGreaterEqual(current_post.created_at, next_post.created_at)
    
    def test_post_meta_options(self):
        """Test model meta options."""
        meta = Post._meta
        
        self.assertEqual(meta.ordering, ['-published_at', '-created_at'])
        
        # Check indexes exist
        index_fields = [index.fields for index in meta.indexes]
        self.assertIn(['status', 'published_at'], index_fields)
        self.assertIn(['author', 'status'], index_fields)
        self.assertIn(['category', 'status'], index_fields)
        
        # Check constraints exist
        constraint_names = [constraint.name for constraint in meta.constraints]
        self.assertIn('positive_reading_time', constraint_names)
        self.assertIn('positive_view_count', constraint_names)
    
    def test_post_soft_delete(self):
        """Test soft delete functionality inherited from SoftDeleteModel."""
        post = Post.objects.create(
            title='Test Delete',
            content='Test content',
            author=self.user
        )
        
        # Test soft delete
        post.delete()
        self.assertTrue(post.is_deleted)
        self.assertIsNotNone(post.deleted_at)
        
        # Test restore
        post.restore()
        self.assertFalse(post.is_deleted)
        self.assertIsNone(post.deleted_at)
    
    def test_post_tag_relationships(self):
        """Test many-to-many relationship with tags."""
        post = Post.objects.create(
            title='Tag Test',
            content='Test content',
            author=self.user
        )
        
        # Add tags
        post.tags.add(self.tag1, self.tag2)
        
        # Test relationships
        self.assertEqual(post.tags.count(), 2)
        self.assertIn(self.tag1, post.tags.all())
        self.assertIn(self.tag2, post.tags.all())
        
        # Test reverse relationship
        self.assertIn(post, self.tag1.posts.all())
        self.assertIn(post, self.tag2.posts.all())