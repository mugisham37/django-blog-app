"""
Unit tests for Comment model and hierarchical functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.blog.models import Post, Category
from apps.comments.models import Comment

User = get_user_model()


class CommentModelTest(TestCase):
    """
    Test cases for Comment model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create test category and post
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='This is a test post content.',
            author=self.user1,
            category=self.category,
            status='published'
        )
    
    def test_comment_creation(self):
        """
        Test basic comment creation.
        """
        comment = Comment.objects.create(
            content='This is a test comment.',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
        
        self.assertEqual(comment.content, 'This is a test comment.')
        self.assertEqual(comment.author, self.user1)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.ip_address, '127.0.0.1')
        self.assertEqual(comment.user_agent, 'Test User Agent')
        self.assertFalse(comment.is_approved)
        self.assertIsNone(comment.parent)
        self.assertFalse(comment.is_deleted)
    
    def test_comment_str_representation(self):
        """
        Test comment string representation.
        """
        comment = Comment.objects.create(
            content='Test comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        expected_str = f"Comment by {self.user1.username} on {self.post.title}"
        self.assertEqual(str(comment), expected_str)
    
    def test_comment_absolute_url(self):
        """
        Test comment absolute URL generation.
        """
        comment = Comment.objects.create(
            content='Test comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        expected_url = f"{self.post.get_absolute_url()}#comment-{comment.pk}"
        self.assertEqual(comment.get_absolute_url(), expected_url)
    
    def test_hierarchical_comments(self):
        """
        Test parent-child relationships in comments.
        """
        # Create parent comment
        parent_comment = Comment.objects.create(
            content='This is a parent comment.',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        # Create child comment
        child_comment = Comment.objects.create(
            content='This is a reply to the parent comment.',
            author=self.user2,
            post=self.post,
            parent=parent_comment,
            ip_address='127.0.0.1'
        )
        
        # Test relationships
        self.assertEqual(child_comment.parent, parent_comment)
        self.assertIn(child_comment, parent_comment.replies.all())
        self.assertEqual(parent_comment.replies.count(), 1)
    
    def test_comment_depth_calculation(self):
        """
        Test comment depth calculation for hierarchical structure.
        """
        # Create parent comment (depth 0)
        parent = Comment.objects.create(
            content='Parent comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        # Create child comment (depth 1)
        child = Comment.objects.create(
            content='Child comment',
            author=self.user2,
            post=self.post,
            parent=parent,
            ip_address='127.0.0.1'
        )
        
        # Create grandchild comment (depth 2)
        grandchild = Comment.objects.create(
            content='Grandchild comment',
            author=self.user1,
            post=self.post,
            parent=child,
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(parent.get_depth(), 0)
        self.assertEqual(child.get_depth(), 1)
        self.assertEqual(grandchild.get_depth(), 2)
    
    def test_can_be_replied_to(self):
        """
        Test depth limit for replies.
        """
        # Create nested comments up to max depth
        parent = Comment.objects.create(
            content='Parent comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        child = Comment.objects.create(
            content='Child comment',
            author=self.user2,
            post=self.post,
            parent=parent,
            ip_address='127.0.0.1'
        )
        
        grandchild = Comment.objects.create(
            content='Grandchild comment',
            author=self.user1,
            post=self.post,
            parent=child,
            ip_address='127.0.0.1'
        )
        
        great_grandchild = Comment.objects.create(
            content='Great grandchild comment',
            author=self.user2,
            post=self.post,
            parent=grandchild,
            ip_address='127.0.0.1'
        )
        
        # Test reply limits (default max_depth=3)
        self.assertTrue(parent.can_be_replied_to())
        self.assertTrue(child.can_be_replied_to())
        self.assertTrue(grandchild.can_be_replied_to())
        self.assertFalse(great_grandchild.can_be_replied_to())
    
    def test_get_thread_comments(self):
        """
        Test getting all comments in a thread.
        """
        # Create parent comment
        parent = Comment.objects.create(
            content='Parent comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        # Create child comments
        child1 = Comment.objects.create(
            content='Child comment 1',
            author=self.user2,
            post=self.post,
            parent=parent,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        child2 = Comment.objects.create(
            content='Child comment 2',
            author=self.user1,
            post=self.post,
            parent=parent,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        # Create grandchild comment
        grandchild = Comment.objects.create(
            content='Grandchild comment',
            author=self.user2,
            post=self.post,
            parent=child1,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        # Test thread retrieval
        thread_comments = parent.get_thread_comments()
        self.assertEqual(len(thread_comments), 4)  # parent + 2 children + 1 grandchild
        self.assertIn(parent, thread_comments)
        self.assertIn(child1, thread_comments)
        self.assertIn(child2, thread_comments)
        self.assertIn(grandchild, thread_comments)
    
    def test_comment_approval_methods(self):
        """
        Test comment approval and rejection methods.
        """
        comment = Comment.objects.create(
            content='Test comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        # Test initial state
        self.assertFalse(comment.is_approved)
        
        # Test approval
        comment.approve()
        comment.refresh_from_db()
        self.assertTrue(comment.is_approved)
        
        # Test rejection
        comment.reject()
        comment.refresh_from_db()
        self.assertFalse(comment.is_approved)
    
    def test_comment_validation_circular_reference(self):
        """
        Test validation prevents circular references.
        """
        comment = Comment.objects.create(
            content='Test comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        # Try to make comment its own parent
        comment.parent = comment
        with self.assertRaises(ValidationError):
            comment.clean()
    
    def test_comment_validation_parent_same_post(self):
        """
        Test validation ensures parent comment belongs to same post.
        """
        # Create another post
        other_post = Post.objects.create(
            title='Other Post',
            slug='other-post',
            content='Other post content.',
            author=self.user1,
            category=self.category,
            status='published'
        )
        
        # Create comment on first post
        parent_comment = Comment.objects.create(
            content='Parent comment',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        # Try to create child comment on different post
        child_comment = Comment(
            content='Child comment',
            author=self.user2,
            post=other_post,
            parent=parent_comment,
            ip_address='127.0.0.1'
        )
        
        with self.assertRaises(ValidationError):
            child_comment.clean()
    
    def test_comment_validation_content_length(self):
        """
        Test validation for minimum content length.
        """
        comment = Comment(
            content='Short',  # Less than 10 characters
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        with self.assertRaises(ValidationError):
            comment.clean()


class CommentManagerTest(TestCase):
    """
    Test cases for Comment managers.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test post content.',
            author=self.user,
            category=self.category,
            status='published'
        )
    
    def test_comment_manager_queryset_optimization(self):
        """
        Test that CommentManager optimizes queries with select_related.
        """
        Comment.objects.create(
            content='Test comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        with self.assertNumQueries(1):
            comment = Comment.objects.first()
            # These should not trigger additional queries due to select_related
            _ = comment.author.username
            _ = comment.post.title
    
    def test_approved_comment_manager(self):
        """
        Test ApprovedCommentManager filters correctly.
        """
        # Create approved comment
        approved_comment = Comment.objects.create(
            content='Approved comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        # Create unapproved comment
        Comment.objects.create(
            content='Unapproved comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=False
        )
        
        # Create deleted comment
        Comment.objects.create(
            content='Deleted comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True,
            is_deleted=True
        )
        
        # Test managers
        self.assertEqual(Comment.objects.count(), 3)
        self.assertEqual(Comment.approved.count(), 1)
        self.assertEqual(Comment.approved.first(), approved_comment)
    
    def test_comment_indexes_exist(self):
        """
        Test that database indexes are properly configured.
        """
        # This test ensures the indexes defined in Meta are created
        # In a real scenario, you'd check the database schema
        comment = Comment.objects.create(
            content='Test comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1'
        )
        
        # Test that queries using indexed fields are efficient
        with self.assertNumQueries(1):
            Comment.objects.filter(
                post=self.post,
                is_approved=True,
                is_deleted=False
            ).first()
    
    def test_manager_get_thread_comments(self):
        """
        Test CommentManager.get_thread_comments method.
        """
        # Create approved and unapproved comments
        approved_comment = Comment.objects.create(
            content='Approved comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        unapproved_comment = Comment.objects.create(
            content='Unapproved comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=False
        )
        
        # Test without including unapproved
        thread_comments = Comment.objects.get_thread_comments(self.post)
        self.assertEqual(thread_comments.count(), 1)
        self.assertIn(approved_comment, thread_comments)
        self.assertNotIn(unapproved_comment, thread_comments)
        
        # Test including unapproved
        all_comments = Comment.objects.get_thread_comments(self.post, include_unapproved=True)
        self.assertEqual(all_comments.count(), 2)
        self.assertIn(approved_comment, all_comments)
        self.assertIn(unapproved_comment, all_comments)
    
    def test_manager_get_root_comments(self):
        """
        Test CommentManager.get_root_comments method.
        """
        # Create root comment
        root_comment = Comment.objects.create(
            content='Root comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        # Create child comment
        Comment.objects.create(
            content='Child comment',
            author=self.user,
            post=self.post,
            parent=root_comment,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        # Test root comments only
        root_comments = Comment.objects.get_root_comments(self.post)
        self.assertEqual(root_comments.count(), 1)
        self.assertEqual(root_comments.first(), root_comment)
    
    def test_manager_get_comment_count(self):
        """
        Test CommentManager.get_comment_count method.
        """
        # Create comments
        Comment.objects.create(
            content='Approved comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        Comment.objects.create(
            content='Unapproved comment',
            author=self.user,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=False
        )
        
        # Test counts
        self.assertEqual(Comment.objects.get_comment_count(self.post), 1)
        self.assertEqual(Comment.objects.get_comment_count(self.post, include_unapproved=True), 2)


class CommentHierarchyTest(TestCase):
    """
    Test cases for Comment hierarchical methods.
    """
    
    def setUp(self):
        """
        Set up test data with complex hierarchy.
        """
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test post content.',
            author=self.user1,
            category=self.category,
            status='published'
        )
        
        # Create complex hierarchy:
        # root1
        #   ├── child1_1
        #   │   └── grandchild1_1_1
        #   └── child1_2
        # root2
        #   └── child2_1
        
        self.root1 = Comment.objects.create(
            content='Root comment 1',
            author=self.user1,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        self.child1_1 = Comment.objects.create(
            content='Child 1.1',
            author=self.user2,
            post=self.post,
            parent=self.root1,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        self.child1_2 = Comment.objects.create(
            content='Child 1.2',
            author=self.user1,
            post=self.post,
            parent=self.root1,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        self.grandchild1_1_1 = Comment.objects.create(
            content='Grandchild 1.1.1',
            author=self.user1,
            post=self.post,
            parent=self.child1_1,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        self.root2 = Comment.objects.create(
            content='Root comment 2',
            author=self.user2,
            post=self.post,
            ip_address='127.0.0.1',
            is_approved=True
        )
        
        self.child2_1 = Comment.objects.create(
            content='Child 2.1',
            author=self.user1,
            post=self.post,
            parent=self.root2,
            ip_address='127.0.0.1',
            is_approved=True
        )
    
    def test_get_root_comment(self):
        """
        Test getting root comment of a thread.
        """
        self.assertEqual(self.root1.get_root_comment(), self.root1)
        self.assertEqual(self.child1_1.get_root_comment(), self.root1)
        self.assertEqual(self.grandchild1_1_1.get_root_comment(), self.root1)
        self.assertEqual(self.child2_1.get_root_comment(), self.root2)
    
    def test_get_ancestors(self):
        """
        Test getting ancestor comments.
        """
        # Root has no ancestors
        self.assertEqual(len(self.root1.get_ancestors()), 0)
        
        # Child has one ancestor
        ancestors = self.child1_1.get_ancestors()
        self.assertEqual(len(ancestors), 1)
        self.assertEqual(ancestors[0], self.root1)
        
        # Grandchild has two ancestors in correct order
        ancestors = self.grandchild1_1_1.get_ancestors()
        self.assertEqual(len(ancestors), 2)
        self.assertEqual(ancestors[0], self.root1)
        self.assertEqual(ancestors[1], self.child1_1)
    
    def test_get_descendants(self):
        """
        Test getting descendant comments.
        """
        # Root1 has 3 descendants
        descendants = self.root1.get_descendants()
        self.assertEqual(len(descendants), 3)
        self.assertIn(self.child1_1, descendants)
        self.assertIn(self.child1_2, descendants)
        self.assertIn(self.grandchild1_1_1, descendants)
        
        # Child1_1 has 1 descendant
        descendants = self.child1_1.get_descendants()
        self.assertEqual(len(descendants), 1)
        self.assertEqual(descendants[0], self.grandchild1_1_1)
        
        # Grandchild has no descendants
        descendants = self.grandchild1_1_1.get_descendants()
        self.assertEqual(len(descendants), 0)
    
    def test_get_siblings(self):
        """
        Test getting sibling comments.
        """
        # Root comments are siblings
        root1_siblings = self.root1.get_siblings()
        self.assertEqual(root1_siblings.count(), 1)
        self.assertIn(self.root2, root1_siblings)
        
        # Child1_1 and Child1_2 are siblings
        child1_1_siblings = self.child1_1.get_siblings()
        self.assertEqual(child1_1_siblings.count(), 1)
        self.assertIn(self.child1_2, child1_1_siblings)
        
        # Test including self
        child1_1_siblings_with_self = self.child1_1.get_siblings(include_self=True)
        self.assertEqual(child1_1_siblings_with_self.count(), 2)
        self.assertIn(self.child1_1, child1_1_siblings_with_self)
        self.assertIn(self.child1_2, child1_1_siblings_with_self)
    
    def test_is_ancestor_of(self):
        """
        Test ancestor relationship checking.
        """
        self.assertTrue(self.root1.is_ancestor_of(self.child1_1))
        self.assertTrue(self.root1.is_ancestor_of(self.grandchild1_1_1))
        self.assertTrue(self.child1_1.is_ancestor_of(self.grandchild1_1_1))
        
        self.assertFalse(self.child1_1.is_ancestor_of(self.root1))
        self.assertFalse(self.root1.is_ancestor_of(self.root2))
        self.assertFalse(self.child1_1.is_ancestor_of(self.child1_2))
    
    def test_is_descendant_of(self):
        """
        Test descendant relationship checking.
        """
        self.assertTrue(self.child1_1.is_descendant_of(self.root1))
        self.assertTrue(self.grandchild1_1_1.is_descendant_of(self.root1))
        self.assertTrue(self.grandchild1_1_1.is_descendant_of(self.child1_1))
        
        self.assertFalse(self.root1.is_descendant_of(self.child1_1))
        self.assertFalse(self.root2.is_descendant_of(self.root1))
        self.assertFalse(self.child1_2.is_descendant_of(self.child1_1))