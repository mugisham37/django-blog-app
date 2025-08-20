#!/usr/bin/env python3
"""
Django App Template Generator

This template generates a complete Django app structure with:
- Models with proper relationships and validation
- Serializers with comprehensive field handling
- ViewSets with proper permissions and filtering
- URL patterns with API versioning
- Tests with factory-based data generation
- Admin interface configuration
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any


class DjangoAppTemplate:
    """Generate Django app from template."""
    
    def __init__(self, app_name: str, model_config: Dict[str, Any]):
        self.app_name = app_name
        self.model_config = model_config
        self.app_path = Path(f"apps/api/apps/{app_name}")
    
    def generate_app(self):
        """Generate complete Django app."""
        print(f"Generating Django app: {self.app_name}")
        
        # Create app directory structure
        self.create_directory_structure()
        
        # Generate files
        self.generate_init_file()
        self.generate_apps_file()
        self.generate_models()
        self.generate_serializers()
        self.generate_views()
        self.generate_urls()
        self.generate_admin()
        self.generate_tests()
        self.generate_permissions()
        self.generate_filters()
        
        print(f"Django app '{self.app_name}' generated successfully!")
    
    def create_directory_structure(self):
        """Create Django app directory structure."""
        directories = [
            self.app_path,
            self.app_path / "migrations",
            self.app_path / "tests",
            self.app_path / "management",
            self.app_path / "management" / "commands",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            init_file = directory / "__init__.py"
            if not init_file.exists():
                init_file.write_text("")
    
    def generate_init_file(self):
        """Generate __init__.py file."""
        content = f'''"""
{self.app_name.title()} Django App

This app handles {self.model_config.get('description', f'{self.app_name} functionality')}.
"""

default_app_config = 'apps.{self.app_name}.apps.{self.app_name.title()}Config'
'''
        
        init_file = self.app_path / "__init__.py"
        init_file.write_text(content)
    
    def generate_apps_file(self):
        """Generate apps.py file."""
        content = f'''from django.apps import AppConfig


class {self.app_name.title()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{self.app_name}'
    verbose_name = '{self.app_name.title()}'
    
    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.{self.app_name}.signals  # noqa F401
        except ImportError:
            pass
'''
        
        apps_file = self.app_path / "apps.py"
        apps_file.write_text(content)
    
    def generate_models(self):
        """Generate models.py file."""
        models = self.model_config.get('models', {})
        
        imports = '''from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.text import slugify
from django.urls import reverse
from enterprise_core.models import BaseModel, TimestampedModel
from enterprise_core.validators import validate_slug
'''
        
        model_classes = []
        
        for model_name, model_fields in models.items():
            model_class = self.generate_model_class(model_name, model_fields)
            model_classes.append(model_class)
        
        content = f'''{imports}


{chr(10).join(model_classes)}
'''
        
        models_file = self.app_path / "models.py"
        models_file.write_text(content)
    
    def generate_model_class(self, model_name: str, fields: Dict[str, Any]) -> str:
        """Generate individual model class."""
        class_name = model_name.title()
        
        field_definitions = []
        methods = []
        
        # Generate field definitions
        for field_name, field_config in fields.items():
            field_def = self.generate_field_definition(field_name, field_config)
            field_definitions.append(f"    {field_def}")
        
        # Generate common methods
        methods.append(f'''    def __str__(self):
        return self.{fields.get('str_field', 'name')}
    
    def get_absolute_url(self):
        return reverse('{self.app_name}:{model_name.lower()}-detail', kwargs={{'pk': self.pk}})''')
        
        # Generate save method if slug field exists
        if any(field.get('type') == 'slug' for field in fields.values()):
            slug_source = next((name for name, field in fields.items() if field.get('slug_source')), 'name')
            methods.append(f'''    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.{slug_source})
        super().save(*args, **kwargs)''')
        
        meta_options = []
        if 'ordering' in fields:
            meta_options.append(f"        ordering = {fields['ordering']}")
        if 'verbose_name' in fields:
            meta_options.append(f"        verbose_name = '{fields['verbose_name']}'")
            meta_options.append(f"        verbose_name_plural = '{fields.get('verbose_name_plural', fields['verbose_name'] + 's')}'")
        
        meta_class = f'''    
    class Meta:
{chr(10).join(meta_options) if meta_options else "        pass"}''' if meta_options else ""
        
        return f'''class {class_name}(TimestampedModel):
    """{fields.get('description', f'{class_name} model')}."""
    
{chr(10).join(field_definitions)}
{meta_class}
{chr(10).join(methods)}'''
    
    def generate_field_definition(self, field_name: str, field_config: Dict[str, Any]) -> str:
        """Generate Django model field definition."""
        field_type = field_config.get('type', 'CharField')
        
        field_mapping = {
            'char': 'CharField',
            'text': 'TextField',
            'slug': 'SlugField',
            'email': 'EmailField',
            'url': 'URLField',
            'integer': 'IntegerField',
            'decimal': 'DecimalField',
            'boolean': 'BooleanField',
            'date': 'DateField',
            'datetime': 'DateTimeField',
            'foreign_key': 'ForeignKey',
            'many_to_many': 'ManyToManyField',
            'one_to_one': 'OneToOneField',
            'json': 'JSONField',
            'file': 'FileField',
            'image': 'ImageField',
        }
        
        django_field = field_mapping.get(field_type, 'CharField')
        
        options = []
        
        # Handle field options
        if 'max_length' in field_config:
            options.append(f"max_length={field_config['max_length']}")
        
        if 'null' in field_config:
            options.append(f"null={field_config['null']}")
        
        if 'blank' in field_config:
            options.append(f"blank={field_config['blank']}")
        
        if 'default' in field_config:
            default_value = field_config['default']
            if isinstance(default_value, str):
                options.append(f"default='{default_value}'")
            else:
                options.append(f"default={default_value}")
        
        if 'help_text' in field_config:
            options.append(f"help_text='{field_config['help_text']}'")
        
        if 'verbose_name' in field_config:
            options.append(f"verbose_name='{field_config['verbose_name']}'")
        
        if 'choices' in field_config:
            choices_name = f"{field_name.upper()}_CHOICES"
            options.append(f"choices={choices_name}")
        
        # Handle relationship fields
        if field_type in ['foreign_key', 'one_to_one']:
            related_model = field_config.get('related_model', 'User')
            options.insert(0, f"'{related_model}'")
            if field_config.get('on_delete'):
                options.append(f"on_delete=models.{field_config['on_delete']}")
        
        if field_type == 'many_to_many':
            related_model = field_config.get('related_model', 'User')
            options.insert(0, f"'{related_model}'")
        
        # Handle decimal field
        if field_type == 'decimal':
            options.append(f"max_digits={field_config.get('max_digits', 10)}")
            options.append(f"decimal_places={field_config.get('decimal_places', 2)}")
        
        options_str = ', '.join(options)
        
        return f"{field_name} = models.{django_field}({options_str})"
    
    def generate_serializers(self):
        """Generate serializers.py file."""
        models = self.model_config.get('models', {})
        
        imports = f'''from rest_framework import serializers
from .models import {', '.join(model.title() for model in models.keys())}
'''
        
        serializer_classes = []
        
        for model_name in models.keys():
            serializer_class = self.generate_serializer_class(model_name)
            serializer_classes.append(serializer_class)
        
        content = f'''{imports}


{chr(10).join(serializer_classes)}
'''
        
        serializers_file = self.app_path / "serializers.py"
        serializers_file.write_text(content)
    
    def generate_serializer_class(self, model_name: str) -> str:
        """Generate serializer class."""
        class_name = model_name.title()
        
        return f'''class {class_name}Serializer(serializers.ModelSerializer):
    """{class_name} serializer with comprehensive field handling."""
    
    class Meta:
        model = {class_name}
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate(self, data):
        """Custom validation logic."""
        # Add custom validation here
        return data


class {class_name}CreateSerializer({class_name}Serializer):
    """Serializer for creating {class_name} instances."""
    
    class Meta({class_name}Serializer.Meta):
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class {class_name}UpdateSerializer({class_name}Serializer):
    """Serializer for updating {class_name} instances."""
    
    class Meta({class_name}Serializer.Meta):
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class {class_name}ListSerializer({class_name}Serializer):
    """Serializer for listing {class_name} instances."""
    
    class Meta({class_name}Serializer.Meta):
        fields = ('id', 'name', 'created_at', 'updated_at')  # Adjust fields as needed'''
    
    def generate_views(self):
        """Generate views.py file."""
        models = self.model_config.get('models', {})
        
        imports = f'''from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import {', '.join(model.title() for model in models.keys())}
from .serializers import {', '.join(f'{model.title()}Serializer' for model in models.keys())}
from .filters import {', '.join(f'{model.title()}Filter' for model in models.keys())}
from .permissions import {', '.join(f'{model.title()}Permission' for model in models.keys())}
'''
        
        viewset_classes = []
        
        for model_name in models.keys():
            viewset_class = self.generate_viewset_class(model_name)
            viewset_classes.append(viewset_class)
        
        content = f'''{imports}


{chr(10).join(viewset_classes)}
'''
        
        views_file = self.app_path / "views.py"
        views_file.write_text(content)
    
    def generate_viewset_class(self, model_name: str) -> str:
        """Generate viewset class."""
        class_name = model_name.title()
        
        return f'''class {class_name}ViewSet(viewsets.ModelViewSet):
    """{class_name} viewset with comprehensive CRUD operations."""
    
    queryset = {class_name}.objects.all()
    serializer_class = {class_name}Serializer
    permission_classes = [{class_name}Permission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = {class_name}Filter
    search_fields = ['name']  # Adjust fields as needed
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return {class_name}CreateSerializer
        elif self.action in ['update', 'partial_update']:
            return {class_name}UpdateSerializer
        elif self.action == 'list':
            return {class_name}ListSerializer
        return super().get_serializer_class()
    
    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        """Custom action example."""
        instance = self.get_object()
        # Add custom logic here
        serializer = self.get_serializer(instance)
        return Response(serializer.data)'''
    
    def generate_urls(self):
        """Generate urls.py file."""
        models = self.model_config.get('models', {})
        
        imports = '''from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
'''
        
        router_registrations = []
        for model_name in models.keys():
            class_name = model_name.title()
            router_registrations.append(f"router.register(r'{model_name}s', views.{class_name}ViewSet)")
        
        content = f'''{imports}

app_name = '{self.app_name}'

router = DefaultRouter()
{chr(10).join(router_registrations)}

urlpatterns = [
    path('', include(router.urls)),
]
'''
        
        urls_file = self.app_path / "urls.py"
        urls_file.write_text(content)
    
    def generate_admin(self):
        """Generate admin.py file."""
        models = self.model_config.get('models', {})
        
        imports = f'''from django.contrib import admin
from .models import {', '.join(model.title() for model in models.keys())}
'''
        
        admin_classes = []
        
        for model_name in models.keys():
            admin_class = self.generate_admin_class(model_name)
            admin_classes.append(admin_class)
        
        registrations = []
        for model_name in models.keys():
            class_name = model_name.title()
            registrations.append(f"admin.site.register({class_name}, {class_name}Admin)")
        
        content = f'''{imports}


{chr(10).join(admin_classes)}


# Register models
{chr(10).join(registrations)}
'''
        
        admin_file = self.app_path / "admin.py"
        admin_file.write_text(content)
    
    def generate_admin_class(self, model_name: str) -> str:
        """Generate admin class."""
        class_name = model_name.title()
        
        return f'''@admin.register({class_name})
class {class_name}Admin(admin.ModelAdmin):
    """{class_name} admin configuration."""
    
    list_display = ('id', 'name', 'created_at', 'updated_at')  # Adjust fields as needed
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name',)  # Adjust fields as needed
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {{
            'fields': ('name',)  # Adjust fields as needed
        }}),
        ('Timestamps', {{
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }}),
    )'''
    
    def generate_tests(self):
        """Generate test files."""
        # Create test directory structure
        test_files = [
            'test_models.py',
            'test_serializers.py',
            'test_views.py',
            'test_permissions.py',
            'factories.py'
        ]
        
        for test_file in test_files:
            method_name = f"generate_{test_file.replace('.py', '').replace('test_', '')}"
            if hasattr(self, method_name):
                content = getattr(self, method_name)()
                file_path = self.app_path / "tests" / test_file
                file_path.write_text(content)
    
    def generate_models_test(self) -> str:
        """Generate model tests."""
        models = self.model_config.get('models', {})
        
        imports = f'''from django.test import TestCase
from django.contrib.auth.models import User
from ..models import {', '.join(model.title() for model in models.keys())}
from .factories import {', '.join(f'{model.title()}Factory' for model in models.keys())}
'''
        
        test_classes = []
        
        for model_name in models.keys():
            test_class = f'''class {model_name.title()}ModelTest(TestCase):
    """Test {model_name.title()} model."""
    
    def setUp(self):
        self.{model_name} = {model_name.title()}Factory()
    
    def test_str_representation(self):
        """Test string representation."""
        self.assertIsInstance(str(self.{model_name}), str)
    
    def test_get_absolute_url(self):
        """Test get_absolute_url method."""
        url = self.{model_name}.get_absolute_url()
        self.assertIsInstance(url, str)'''
            
            test_classes.append(test_class)
        
        return f'''{imports}


{chr(10).join(test_classes)}
'''
    
    def generate_factories(self) -> str:
        """Generate factory classes for testing."""
        models = self.model_config.get('models', {})
        
        imports = f'''import factory
from django.contrib.auth.models import User
from ..models import {', '.join(model.title() for model in models.keys())}
'''
        
        factory_classes = []
        
        for model_name in models.keys():
            factory_class = f'''class {model_name.title()}Factory(factory.django.DjangoModelFactory):
    """Factory for {model_name.title()} model."""
    
    class Meta:
        model = {model_name.title()}
    
    name = factory.Faker('name')  # Adjust fields as needed'''
            
            factory_classes.append(factory_class)
        
        return f'''{imports}


{chr(10).join(factory_classes)}
'''
    
    def generate_permissions(self):
        """Generate permissions.py file."""
        models = self.model_config.get('models', {})
        
        imports = '''from rest_framework import permissions
'''
        
        permission_classes = []
        
        for model_name in models.keys():
            permission_class = f'''class {model_name.title()}Permission(permissions.BasePermission):
    """{model_name.title()} permission class."""
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated'''
            
            permission_classes.append(permission_class)
        
        content = f'''{imports}


{chr(10).join(permission_classes)}
'''
        
        permissions_file = self.app_path / "permissions.py"
        permissions_file.write_text(content)
    
    def generate_filters(self):
        """Generate filters.py file."""
        models = self.model_config.get('models', {})
        
        imports = f'''import django_filters
from .models import {', '.join(model.title() for model in models.keys())}
'''
        
        filter_classes = []
        
        for model_name in models.keys():
            filter_class = f'''class {model_name.title()}Filter(django_filters.FilterSet):
    """{model_name.title()} filter class."""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    created_at = django_filters.DateFromToRangeFilter()
    
    class Meta:
        model = {model_name.title()}
        fields = ['name', 'created_at']  # Adjust fields as needed'''
            
            filter_classes.append(filter_class)
        
        content = f'''{imports}


{chr(10).join(filter_classes)}
'''
        
        filters_file = self.app_path / "filters.py"
        filters_file.write_text(content)


# Example usage configuration
EXAMPLE_CONFIG = {
    'description': 'Blog management functionality',
    'models': {
        'post': {
            'description': 'Blog post model',
            'str_field': 'title',
            'fields': {
                'title': {'type': 'char', 'max_length': 200, 'verbose_name': 'Title'},
                'slug': {'type': 'slug', 'max_length': 200, 'slug_source': 'title'},
                'content': {'type': 'text', 'verbose_name': 'Content'},
                'author': {'type': 'foreign_key', 'related_model': 'User', 'on_delete': 'CASCADE'},
                'status': {
                    'type': 'char', 
                    'max_length': 20, 
                    'choices': [('draft', 'Draft'), ('published', 'Published')],
                    'default': 'draft'
                },
                'featured': {'type': 'boolean', 'default': False},
                'views_count': {'type': 'integer', 'default': 0},
            },
            'ordering': ['-created_at'],
            'verbose_name': 'Blog Post',
            'verbose_name_plural': 'Blog Posts'
        },
        'category': {
            'description': 'Blog category model',
            'str_field': 'name',
            'fields': {
                'name': {'type': 'char', 'max_length': 100, 'verbose_name': 'Name'},
                'slug': {'type': 'slug', 'max_length': 100, 'slug_source': 'name'},
                'description': {'type': 'text', 'blank': True, 'verbose_name': 'Description'},
            },
            'ordering': ['name'],
            'verbose_name': 'Category',
            'verbose_name_plural': 'Categories'
        }
    }
}


def main():
    """CLI interface for Django app template generator."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Generate Django app from template')
    parser.add_argument('app_name', help='Name of the Django app to generate')
    parser.add_argument('--config', help='Path to JSON configuration file')
    parser.add_argument('--example', action='store_true', help='Use example configuration')
    
    args = parser.parse_args()
    
    if args.example:
        config = EXAMPLE_CONFIG
    elif args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    else:
        print("Please provide either --config or --example")
        sys.exit(1)
    
    generator = DjangoAppTemplate(args.app_name, config)
    generator.generate_app()


if __name__ == '__main__':
    main()