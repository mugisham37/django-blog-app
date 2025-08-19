#!/usr/bin/env python
"""
Simple validation script for core abstract models.
This script validates the structure and basic functionality without requiring a full Django test environment.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_abstract_models():
    """Validate the structure of abstract base models."""
    try:
        from apps.core.models import TimeStampedModel, SEOModel, SoftDeleteModel, SoftDeleteManager
        
        print("✓ Successfully imported all abstract models")
        
        # Validate TimeStampedModel
        assert hasattr(TimeStampedModel, '_meta'), "TimeStampedModel should have _meta attribute"
        assert TimeStampedModel._meta.abstract, "TimeStampedModel should be abstract"
        
        # Check fields
        field_names = [f.name for f in TimeStampedModel._meta.get_fields()]
        assert 'created_at' in field_names, "TimeStampedModel should have created_at field"
        assert 'updated_at' in field_names, "TimeStampedModel should have updated_at field"
        
        print("✓ TimeStampedModel validation passed")
        
        # Validate SEOModel
        assert hasattr(SEOModel, '_meta'), "SEOModel should have _meta attribute"
        assert SEOModel._meta.abstract, "SEOModel should be abstract"
        
        # Check fields
        seo_field_names = [f.name for f in SEOModel._meta.get_fields()]
        assert 'meta_title' in seo_field_names, "SEOModel should have meta_title field"
        assert 'meta_description' in seo_field_names, "SEOModel should have meta_description field"
        assert 'og_image' in seo_field_names, "SEOModel should have og_image field"
        
        # Check field properties
        meta_title_field = SEOModel._meta.get_field('meta_title')
        assert meta_title_field.max_length == 60, "meta_title should have max_length=60"
        assert meta_title_field.blank == True, "meta_title should be blank=True"
        
        meta_desc_field = SEOModel._meta.get_field('meta_description')
        assert meta_desc_field.max_length == 160, "meta_description should have max_length=160"
        assert meta_desc_field.blank == True, "meta_description should be blank=True"
        
        og_image_field = SEOModel._meta.get_field('og_image')
        assert og_image_field.upload_to == 'og_images/', "og_image should upload to 'og_images/'"
        assert og_image_field.blank == True, "og_image should be blank=True"
        
        print("✓ SEOModel validation passed")
        
        # Validate SoftDeleteModel
        assert hasattr(SoftDeleteModel, '_meta'), "SoftDeleteModel should have _meta attribute"
        assert SoftDeleteModel._meta.abstract, "SoftDeleteModel should be abstract"
        
        # Check fields
        soft_delete_field_names = [f.name for f in SoftDeleteModel._meta.get_fields()]
        assert 'is_deleted' in soft_delete_field_names, "SoftDeleteModel should have is_deleted field"
        assert 'deleted_at' in soft_delete_field_names, "SoftDeleteModel should have deleted_at field"
        
        # Check field properties
        is_deleted_field = SoftDeleteModel._meta.get_field('is_deleted')
        assert is_deleted_field.default == False, "is_deleted should default to False"
        
        deleted_at_field = SoftDeleteModel._meta.get_field('deleted_at')
        assert deleted_at_field.null == True, "deleted_at should be null=True"
        assert deleted_at_field.blank == True, "deleted_at should be blank=True"
        
        # Check managers
        assert hasattr(SoftDeleteModel, 'objects'), "SoftDeleteModel should have objects manager"
        assert hasattr(SoftDeleteModel, 'active_objects'), "SoftDeleteModel should have active_objects manager"
        assert isinstance(SoftDeleteModel.active_objects, SoftDeleteManager), "active_objects should be SoftDeleteManager instance"
        
        # Check methods
        assert hasattr(SoftDeleteModel, 'delete'), "SoftDeleteModel should have delete method"
        assert hasattr(SoftDeleteModel, 'hard_delete'), "SoftDeleteModel should have hard_delete method"
        assert hasattr(SoftDeleteModel, 'restore'), "SoftDeleteModel should have restore method"
        
        print("✓ SoftDeleteModel validation passed")
        
        # Validate SoftDeleteManager
        assert hasattr(SoftDeleteManager, 'get_queryset'), "SoftDeleteManager should have get_queryset method"
        
        print("✓ SoftDeleteManager validation passed")
        
        print("\n🎉 All abstract model validations passed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def validate_test_structure():
    """Validate that test files are properly structured."""
    try:
        # Check if test file exists
        test_file_path = os.path.join(os.path.dirname(__file__), 'test_core_models.py')
        assert os.path.exists(test_file_path), "test_core_models.py should exist"
        
        # Read and validate test file structure
        with open(test_file_path, 'r') as f:
            content = f.read()
            
        # Check for required test classes
        required_test_classes = [
            'TimeStampedModelTestCase',
            'SEOModelTestCase', 
            'SoftDeleteModelTestCase',
            'CombinedModelTestCase'
        ]
        
        for test_class in required_test_classes:
            assert f"class {test_class}" in content, f"Test file should contain {test_class}"
        
        # Check for required test methods
        required_test_methods = [
            'test_created_at_auto_set',
            'test_updated_at_auto_set',
            'test_meta_title_field_properties',
            'test_meta_description_field_properties',
            'test_og_image_field_properties',
            'test_soft_delete_functionality',
            'test_hard_delete_functionality',
            'test_restore_functionality',
            'test_active_objects_manager_excludes_deleted'
        ]
        
        for test_method in required_test_methods:
            assert f"def {test_method}" in content, f"Test file should contain {test_method}"
        
        print("✓ Test file structure validation passed")
        return True
        
    except AssertionError as e:
        print(f"❌ Test structure validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in test validation: {e}")
        return False

if __name__ == '__main__':
    print("Validating Django Personal Blog System - Core Abstract Models")
    print("=" * 60)
    
    model_validation = validate_abstract_models()
    test_validation = validate_test_structure()
    
    if model_validation and test_validation:
        print("\n✅ All validations passed! Task 2.1 is complete.")
        sys.exit(0)
    else:
        print("\n❌ Some validations failed.")
        sys.exit(1)