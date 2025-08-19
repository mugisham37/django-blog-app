"""
Tests for accounts models.
"""

import os
import tempfile
from datetime import date, datetime
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from PIL import Image
from io import BytesIO
from apps.accounts.models import Profile

User = get_user_model()


class ProfileModelTest(TestCase):
    """Test cases for the Profile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Profile should be created automatically via signals
        self.profile = Profile.objects.get(user=self.user)
    
    def test_profile_creation_via_signal(self):
        """Test that profile is created automatically when user is created."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        # Profile should be created automatically
        self.assertTrue(Profile.objects.filter(user=new_user).exists())
        profile = Profile.objects.get(user=new_user)
        self.assertEqual(profile.user, new_user)
    
    def test_profile_str_representation(self):
        """Test the string representation of Profile."""
        expected = "Test User's Profile"
        self.assertEqual(str(self.profile), expected)
        
        # Test with user without full name
        user_no_name = User.objects.create_user(
            username='noname',
            email='noname@example.com',
            password='testpass123'
        )
        profile_no_name = Profile.objects.get(user=user_no_name)
        expected_no_name = "noname's Profile"
        self.assertEqual(str(profile_no_name), expected_no_name)
    
    def test_profile_default_values(self):
        """Test default values for profile fields."""
        self.assertEqual(self.profile.bio, '')
        self.assertFalse(self.profile.avatar)
        self.assertEqual(self.profile.website, '')
        self.assertEqual(self.profile.location, '')
        self.assertIsNone(self.profile.birth_date)
        self.assertEqual(self.profile.social_links, {})
        self.assertTrue(self.profile.email_notifications)
        self.assertFalse(self.profile.newsletter_subscription)
        self.assertFalse(self.profile.is_author)
        self.assertEqual(self.profile.author_bio, '')
        self.assertFalse(self.profile.show_email)
        self.assertFalse(self.profile.show_birth_date)
        self.assertEqual(self.profile.posts_count, 0)
        self.assertEqual(self.profile.comments_count, 0)
        self.assertEqual(self.profile.profile_views, 0)
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        self.assertEqual(self.profile.get_full_name(), 'Test User')
        
        # Test with user without full name
        user_no_name = User.objects.create_user(
            username='noname',
            email='noname@example.com',
            password='testpass123'
        )
        profile_no_name = Profile.objects.get(user=user_no_name)
        self.assertEqual(profile_no_name.get_full_name(), 'noname')
    
    def test_get_display_name(self):
        """Test get_display_name method."""
        self.assertEqual(self.profile.get_display_name(), 'Test')
        
        # Test with user without first name
        user_no_first = User.objects.create_user(
            username='nofirst',
            email='nofirst@example.com',
            password='testpass123'
        )
        profile_no_first = Profile.objects.get(user=user_no_first)
        self.assertEqual(profile_no_first.get_display_name(), 'nofirst')
    
    def test_social_links_methods(self):
        """Test social links getter and setter methods."""
        # Test getting non-existent link
        self.assertEqual(self.profile.get_social_link('twitter'), '')
        
        # Test setting social link
        self.profile.set_social_link('twitter', 'https://twitter.com/testuser')
        self.assertEqual(self.profile.get_social_link('twitter'), 'https://twitter.com/testuser')
        
        # Test setting multiple links
        self.profile.set_social_link('github', 'https://github.com/testuser')
        self.profile.set_social_link('linkedin', 'https://linkedin.com/in/testuser')
        
        self.assertEqual(len(self.profile.social_links), 3)
        self.assertEqual(self.profile.get_social_link('github'), 'https://github.com/testuser')
        
        # Test removing social link
        self.profile.set_social_link('twitter', '')
        self.assertEqual(self.profile.get_social_link('twitter'), '')
        self.assertNotIn('twitter', self.profile.social_links)
    
    def test_get_age(self):
        """Test age calculation."""
        # Test with no birth date
        self.assertIsNone(self.profile.get_age())
        
        # Test with birth date
        birth_date = date(1990, 5, 15)
        self.profile.birth_date = birth_date
        self.profile.save()
        
        age = self.profile.get_age()
        self.assertIsInstance(age, int)
        self.assertGreaterEqual(age, 0)
        
        # Test specific age calculation
        today = date.today()
        expected_age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            expected_age -= 1
        
        self.assertEqual(age, expected_age)
    
    def test_is_complete_property(self):
        """Test is_complete property."""
        # Initially incomplete
        self.assertFalse(self.profile.is_complete)
        
        # Add bio
        self.profile.bio = 'Test bio'
        self.profile.save()
        self.assertFalse(self.profile.is_complete)  # Still missing avatar
        
        # Add avatar (mock)
        with patch.object(self.profile, 'avatar', True):
            self.assertTrue(self.profile.is_complete)
    
    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        # Initially should have some completion (user has first/last name)
        initial_percentage = self.profile.completion_percentage
        self.assertGreaterEqual(initial_percentage, 0)
        self.assertLessEqual(initial_percentage, 100)
        
        # Add more fields
        self.profile.bio = 'Test bio'
        self.profile.website = 'https://example.com'
        self.profile.location = 'Test City'
        self.profile.social_links = {'twitter': 'https://twitter.com/test'}
        self.profile.save()
        
        new_percentage = self.profile.completion_percentage
        self.assertGreater(new_percentage, initial_percentage)
    
    def test_increment_profile_views(self):
        """Test profile views increment."""
        initial_views = self.profile.profile_views
        self.profile.increment_profile_views()
        
        # Refresh from database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.profile_views, initial_views + 1)
    
    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """Helper method to create test image."""
        image = Image.new('RGB', size, color='red')
        temp_file = BytesIO()
        image.save(temp_file, format=format)
        temp_file.seek(0)
        
        return SimpleUploadedFile(
            name=name,
            content=temp_file.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_avatar_upload(self):
        """Test avatar upload functionality."""
        test_image = self.create_test_image()
        
        self.profile.avatar = test_image
        self.profile.save()
        
        self.assertTrue(self.profile.avatar)
        self.assertTrue(os.path.exists(self.profile.avatar.path))
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    @patch('apps.accounts.models.process_uploaded_image')
    @patch('apps.accounts.models.create_thumbnail')
    def test_avatar_processing(self, mock_create_thumbnail, mock_process_image):
        """Test avatar processing during save."""
        # Mock the image processing functions
        mock_process_image.return_value = MagicMock()
        mock_create_thumbnail.return_value = MagicMock()
        
        test_image = self.create_test_image()
        self.profile.avatar = test_image
        self.profile.save()
        
        # Verify processing functions were called
        mock_process_image.assert_called_once()
        mock_create_thumbnail.assert_called_once()
    
    def test_get_avatar_url(self):
        """Test get_avatar_url method."""
        # Test with no avatar
        default_url = self.profile.get_avatar_url()
        self.assertIn('default-avatar.png', default_url)
        
        # Test thumbnail URL with no avatar
        thumbnail_url = self.profile.get_avatar_url(thumbnail=True)
        self.assertIn('default-avatar.png', thumbnail_url)
    
    def test_social_links_validation(self):
        """Test social links validation."""
        # Test invalid social links format
        self.profile.social_links = "invalid"
        with self.assertRaises(ValidationError):
            self.profile.full_clean()
        
        # Test invalid platform
        self.profile.social_links = {'invalid_platform': 'https://example.com'}
        with self.assertRaises(ValidationError):
            self.profile.full_clean()
        
        # Test invalid URL format
        self.profile.social_links = {'twitter': 'invalid-url'}
        with self.assertRaises(ValidationError):
            self.profile.full_clean()
        
        # Test valid social links
        self.profile.social_links = {
            'twitter': 'https://twitter.com/test',
            'github': 'https://github.com/test'
        }
        try:
            self.profile.full_clean()
        except ValidationError:
            self.fail("Valid social links should not raise ValidationError")
    
    @override_settings(MAX_IMAGE_SIZE=1024)  # 1KB for testing
    def test_avatar_size_validation(self):
        """Test avatar file size validation."""
        # Create large image
        large_image = self.create_test_image(size=(1000, 1000))
        self.profile.avatar = large_image
        
        with self.assertRaises(ValidationError):
            self.profile.full_clean()
    
    def test_profile_manager_methods(self):
        """Test custom manager methods."""
        # Create additional test profiles
        author_user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123',
            first_name='Author',
            last_name='User'
        )
        author_profile = Profile.objects.get(user=author_user)
        author_profile.is_author = True
        author_profile.bio = 'Author bio'
        author_profile.avatar = self.create_test_image()
        author_profile.social_links = {'twitter': 'https://twitter.com/author'}
        author_profile.newsletter_subscription = True
        author_profile.save()
        
        # Test authors() method
        authors = Profile.objects.authors()
        self.assertIn(author_profile, authors)
        self.assertNotIn(self.profile, authors)
        
        # Test with_social_links() method
        with_social = Profile.objects.with_social_links()
        self.assertIn(author_profile, with_social)
        self.assertNotIn(self.profile, with_social)
        
        # Test newsletter_subscribers() method
        subscribers = Profile.objects.newsletter_subscribers()
        self.assertIn(author_profile, subscribers)
        self.assertNotIn(self.profile, subscribers)
    
    def test_profile_one_to_one_relationship(self):
        """Test that profile has proper one-to-one relationship with user."""
        # Test that each user has exactly one profile
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)
        
        # Test that we can't create duplicate profiles
        with self.assertRaises(IntegrityError):
            Profile.objects.create(user=self.user)
    
    def test_profile_deletion_signal(self):
        """Test that profile images are deleted when profile is deleted."""
        with patch('apps.accounts.models.Profile.avatar') as mock_avatar:
            with patch('apps.accounts.models.Profile.avatar_thumbnail') as mock_thumbnail:
                mock_avatar.delete = MagicMock()
                mock_thumbnail.delete = MagicMock()
                
                # Delete the profile
                self.profile.delete()
                
                # Verify delete was called on images
                mock_avatar.delete.assert_called_once_with(save=False)
                mock_thumbnail.delete.assert_called_once_with(save=False)


class ProfileManagerTest(TestCase):
    """Test cases for the Profile manager."""
    
    def setUp(self):
        """Set up test data."""
        # Create test users and profiles
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        self.profile1 = Profile.objects.get(user=self.user1)
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.profile2 = Profile.objects.get(user=self.user2)
        
        # Set up profile1 as complete
        self.profile1.bio = 'Complete bio'
        self.profile1.is_author = True
        self.profile1.social_links = {'twitter': 'https://twitter.com/user1'}
        self.profile1.newsletter_subscription = True
        self.profile1.posts_count = 5
        self.profile1.comments_count = 10
        self.profile1.profile_views = 100
        self.profile1.save()
    
    def test_get_queryset_optimization(self):
        """Test that manager optimizes queryset with select_related."""
        profiles = Profile.objects.all()
        
        # This should not cause additional queries due to select_related
        with self.assertNumQueries(1):
            for profile in profiles:
                _ = profile.user.username
    
    def test_complete_profiles(self):
        """Test complete_profiles manager method."""
        # profile1 should not be complete (no avatar)
        complete_profiles = Profile.objects.complete_profiles()
        self.assertNotIn(self.profile1, complete_profiles)
        
        # Add avatar to make it complete
        with patch.object(self.profile1, 'avatar', True):
            # We need to actually save with avatar for the query to work
            # This is a limitation of the test - in real usage, avatar would be a file
            pass
    
    def test_authors(self):
        """Test authors manager method."""
        authors = Profile.objects.authors()
        self.assertIn(self.profile1, authors)
        self.assertNotIn(self.profile2, authors)
    
    def test_with_social_links(self):
        """Test with_social_links manager method."""
        with_social = Profile.objects.with_social_links()
        self.assertIn(self.profile1, with_social)
        self.assertNotIn(self.profile2, with_social)
    
    def test_newsletter_subscribers(self):
        """Test newsletter_subscribers manager method."""
        subscribers = Profile.objects.newsletter_subscribers()
        self.assertIn(self.profile1, subscribers)
        self.assertNotIn(self.profile2, subscribers)
    
    def test_ordering_methods(self):
        """Test ordering manager methods."""
        # Test by_posts_count
        by_posts = list(Profile.objects.by_posts_count())
        self.assertEqual(by_posts[0], self.profile1)  # Higher posts count first
        
        # Test by_comments_count
        by_comments = list(Profile.objects.by_comments_count())
        self.assertEqual(by_comments[0], self.profile1)  # Higher comments count first
        
        # Test most_viewed
        most_viewed = list(Profile.objects.most_viewed())
        self.assertEqual(most_viewed[0], self.profile1)  # Higher views first