"""
Unit tests for core abstract base models.
"""

from django.test import TestCase
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
import tempfile
import os

from apps.core.models import TimeStampedModel, SEOModel, SoftDeleteModel


# Test models that inherit from abstract base models
class TestTimeStampedModel(TimeStampedModel):
    """Test model for TimeStampedModel testing."""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'


class TestSEOModel(SEOModel):
    """Test model for SEOModel testing."""
    title = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'


class TestSoftDeleteModel(SoftDeleteModel):
    """Test model for SoftDeleteModel testing."""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'


class TestCombinedModel(TimeStampedModel, SEOModel, SoftDeleteModel):
    """Test model that combines all abstract models."""
    title = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'


class TimeStampedModelTestCase(TestCase):
    """Test cases for TimeStampedModel abstract base model."""

    def setUp(self):
        """Set up test data."""
        self.test_obj = TestTimeStampedModel.objects.create(name="Test Object")

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        self.assertIsNotNone(self.test_obj.created_at)
        self.assertIsInstance(self.test_obj.created_at, timezone.datetime)

    def test_updated_at_auto_set(self):
        """Test that updated_at is automatically set on creation."""
        self.assertIsNotNone(self.test_obj.updated_at)
        self.assertIsInstance(self.test_obj.updated_at, timezone.datetime)

    def test_created_at_not_changed_on_update(self):
        """Test that created_at doesn't change when object is updated."""
        original_created_at = self.test_obj.created_at
        
        # Wait a small amount to ensure time difference
        import time
        time.sleep(0.01)
        
        self.test_obj.name = "Updated Name"
        self.test_obj.save()
        
        self.assertEqual(self.test_obj.created_at, original_created_at)

    def test_updated_at_changes_on_update(self):
        """Test that updated_at changes when object is updated."""
        original_updated_at = self.test_obj.updated_at
        
        # Wait a small amount to ensure time difference
        import time
        time.sleep(0.01)
        
        self.test_obj.name = "Updated Name"
        self.test_obj.save()
        
        self.assertNotEqual(self.test_obj.updated_at, original_updated_at)
        self.assertGreater(self.test_obj.updated_at, original_updated_at)

    def test_timestamps_are_timezone_aware(self):
        """Test that timestamps are timezone-aware."""
        self.assertIsNotNone(self.test_obj.created_at.tzinfo)
        self.assertIsNotNone(self.test_obj.updated_at.tzinfo)

    def test_model_is_abstract(self):
        """Test that TimeStampedModel is abstract."""
        self.assertTrue(TimeStampedModel._meta.abstract)


class SEOModelTestCase(TestCase):
    """Test cases for SEOModel abstract base model."""

    def setUp(self):
        """Set up test data."""
        self.test_obj = TestSEOModel.objects.create(title="Test SEO Object")

    def test_meta_title_field_properties(self):
        """Test meta_title field properties."""
        field = TestSEOModel._meta.get_field('meta_title')
        self.assertEqual(field.max_length, 60)
        self.assertTrue(field.blank)
        self.assertIn("SEO title", field.help_text)

    def test_meta_description_field_properties(self):
        """Test meta_description field properties."""
        field = TestSEOModel._meta.get_field('meta_description')
        self.assertEqual(field.max_length, 160)
        self.assertTrue(field.blank)
        self.assertIn("SEO description", field.help_text)

    def test_og_image_field_properties(self):
        """Test og_image field properties."""
        field = TestSEOModel._meta.get_field('og_image')
        self.assertEqual(field.upload_to, 'og_images/')
        self.assertTrue(field.blank)
        self.assertIn("Open Graph", field.help_text)

    def test_seo_fields_can_be_blank(self):
        """Test that SEO fields can be left blank."""
        obj = TestSEOModel.objects.create(title="Test")
        self.assertEqual(obj.meta_title, "")
        self.assertEqual(obj.meta_description, "")
        self.assertFalse(obj.og_image)

    def test_meta_title_max_length_validation(self):
        """Test that meta_title respects max_length constraint."""
        long_title = "x" * 61  # Exceeds 60 character limit
        obj = TestSEOModel(title="Test", meta_title=long_title)
        
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_meta_description_max_length_validation(self):
        """Test that meta_description respects max_length constraint."""
        long_description = "x" * 161  # Exceeds 160 character limit
        obj = TestSEOModel(title="Test", meta_description=long_description)
        
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_seo_fields_with_valid_data(self):
        """Test SEO fields with valid data."""
        obj = TestSEOModel.objects.create(
            title="Test",
            meta_title="Test Meta Title",
            meta_description="Test meta description for SEO purposes."
        )
        
        self.assertEqual(obj.meta_title, "Test Meta Title")
        self.assertEqual(obj.meta_description, "Test meta description for SEO purposes.")

    def test_model_is_abstract(self):
        """Test that SEOModel is abstract."""
        self.assertTrue(SEOModel._meta.abstract)

    def test_og_image_upload_path(self):
        """Test that og_image uses correct upload path."""
        # Create a simple test image file
        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
        uploaded_file = SimpleUploadedFile(
            name='test_image.gif',
            content=image_content,
            content_type='image/gif'
        )
        
        obj = TestSEOModel.objects.create(
            title="Test",
            og_image=uploaded_file
        )
        
        self.assertTrue(obj.og_image.name.startswith('og_images/'))
        
        # Clean up the uploaded file
        if obj.og_image and os.path.exists(obj.og_image.path):
            os.remove(obj.og_image.path)


class SoftDeleteModelTestCase(TestCase):
    """Test cases for SoftDeleteModel abstract base model."""

    def setUp(self):
        """Set up test data."""
        self.test_obj = TestSoftDeleteModel.objects.create(name="Test Object")

    def test_is_deleted_default_false(self):
        """Test that is_deleted defaults to False."""
        self.assertFalse(self.test_obj.is_deleted)

    def test_deleted_at_default_null(self):
        """Test that deleted_at defaults to None."""
        self.assertIsNone(self.test_obj.deleted_at)

    def test_soft_delete_functionality(self):
        """Test soft delete functionality."""
        self.test_obj.delete()
        
        self.assertTrue(self.test_obj.is_deleted)
        self.assertIsNotNone(self.test_obj.deleted_at)
        self.assertIsInstance(self.test_obj.deleted_at, timezone.datetime)

    def test_hard_delete_functionality(self):
        """Test hard delete functionality."""
        obj_id = self.test_obj.id
        self.test_obj.hard_delete()
        
        with self.assertRaises(TestSoftDeleteModel.DoesNotExist):
            TestSoftDeleteModel.objects.get(id=obj_id)

    def test_restore_functionality(self):
        """Test restore functionality."""
        # First soft delete
        self.test_obj.delete()
        self.assertTrue(self.test_obj.is_deleted)
        
        # Then restore
        self.test_obj.restore()
        self.assertFalse(self.test_obj.is_deleted)
        self.assertIsNone(self.test_obj.deleted_at)

    def test_default_manager_includes_deleted(self):
        """Test that default manager includes soft-deleted objects."""
        self.test_obj.delete()
        
        # Default manager should include deleted objects
        self.assertEqual(TestSoftDeleteModel.objects.count(), 1)
        self.assertTrue(TestSoftDeleteModel.objects.first().is_deleted)

    def test_active_objects_manager_excludes_deleted(self):
        """Test that active_objects manager excludes soft-deleted objects."""
        self.test_obj.delete()
        
        # Active manager should exclude deleted objects
        self.assertEqual(TestSoftDeleteModel.active_objects.count(), 0)

    def test_active_objects_manager_includes_non_deleted(self):
        """Test that active_objects manager includes non-deleted objects."""
        # Create another non-deleted object
        TestSoftDeleteModel.objects.create(name="Active Object")
        
        # Soft delete the first object
        self.test_obj.delete()
        
        # Active manager should only include the non-deleted object
        self.assertEqual(TestSoftDeleteModel.active_objects.count(), 1)
        self.assertEqual(TestSoftDeleteModel.active_objects.first().name, "Active Object")

    def test_model_is_abstract(self):
        """Test that SoftDeleteModel is abstract."""
        self.assertTrue(SoftDeleteModel._meta.abstract)

    def test_soft_delete_preserves_object_in_db(self):
        """Test that soft delete preserves object in database."""
        obj_id = self.test_obj.id
        self.test_obj.delete()
        
        # Object should still exist in database
        obj = TestSoftDeleteModel.objects.get(id=obj_id)
        self.assertTrue(obj.is_deleted)

    def test_multiple_soft_deletes_idempotent(self):
        """Test that multiple soft deletes are idempotent."""
        original_deleted_at = None
        
        # First soft delete
        self.test_obj.delete()
        original_deleted_at = self.test_obj.deleted_at
        
        # Wait a bit
        import time
        time.sleep(0.01)
        
        # Second soft delete
        self.test_obj.delete()
        
        # deleted_at should be updated
        self.assertGreater(self.test_obj.deleted_at, original_deleted_at)


class CombinedModelTestCase(TestCase):
    """Test cases for model that combines all abstract base models."""

    def setUp(self):
        """Set up test data."""
        self.test_obj = TestCombinedModel.objects.create(title="Combined Test")

    def test_all_abstract_model_functionality(self):
        """Test that all abstract model functionality works together."""
        # Test TimeStampedModel functionality
        self.assertIsNotNone(self.test_obj.created_at)
        self.assertIsNotNone(self.test_obj.updated_at)
        
        # Test SEOModel functionality
        self.test_obj.meta_title = "Test Meta Title"
        self.test_obj.meta_description = "Test description"
        self.test_obj.save()
        
        # Test SoftDeleteModel functionality
        self.assertFalse(self.test_obj.is_deleted)
        self.test_obj.delete()
        self.assertTrue(self.test_obj.is_deleted)
        
        # Test that object still has timestamps after soft delete
        self.assertIsNotNone(self.test_obj.created_at)
        self.assertIsNotNone(self.test_obj.updated_at)
        self.assertIsNotNone(self.test_obj.deleted_at)

    def test_managers_work_with_combined_model(self):
        """Test that managers work correctly with combined model."""
        # Create another object and soft delete the first
        TestCombinedModel.objects.create(title="Active Object")
        self.test_obj.delete()
        
        # Test manager behavior
        self.assertEqual(TestCombinedModel.objects.count(), 2)  # Includes deleted
        self.assertEqual(TestCombinedModel.active_objects.count(), 1)  # Excludes deleted

    def test_field_inheritance_no_conflicts(self):
        """Test that field inheritance doesn't create conflicts."""
        # Verify all expected fields exist
        field_names = [f.name for f in TestCombinedModel._meta.get_fields()]
        
        expected_fields = [
            'id', 'title',  # Model fields
            'created_at', 'updated_at',  # TimeStampedModel
            'meta_title', 'meta_description', 'og_image',  # SEOModel
            'is_deleted', 'deleted_at'  # SoftDeleteModel
        ]
        
        for field in expected_fields:
            self.assertIn(field, field_names)