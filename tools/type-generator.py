#!/usr/bin/env python3
"""
Django Model to TypeScript Type Generator

This script automatically generates TypeScript interfaces from Django models.
It analyzes Django models and creates corresponding TypeScript type definitions.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import importlib.util
import django
from django.apps import apps
from django.db import models
from django.conf import settings


class DjangoTypeGenerator:
    """Generate TypeScript types from Django models."""
    
    def __init__(self, django_project_path: str, output_path: str):
        self.django_project_path = Path(django_project_path)
        self.output_path = Path(output_path)
        self.type_mappings = {
            'AutoField': 'number',
            'BigAutoField': 'number',
            'BigIntegerField': 'number',
            'BooleanField': 'boolean',
            'CharField': 'string',
            'DateField': 'string',  # ISO date string
            'DateTimeField': 'string',  # ISO datetime string
            'DecimalField': 'number',
            'EmailField': 'string',
            'FileField': 'string',  # URL string
            'FloatField': 'number',
            'ImageField': 'string',  # URL string
            'IntegerField': 'number',
            'JSONField': 'any',
            'PositiveIntegerField': 'number',
            'PositiveSmallIntegerField': 'number',
            'SlugField': 'string',
            'SmallIntegerField': 'number',
            'TextField': 'string',
            'TimeField': 'string',  # ISO time string
            'URLField': 'string',
            'UUIDField': 'string',
            'ForeignKey': 'number',  # ID reference
            'OneToOneField': 'number',  # ID reference
            'ManyToManyField': 'number[]',  # Array of IDs
        }
    
    def setup_django(self):
        """Setup Django environment."""
        sys.path.insert(0, str(self.django_project_path))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
        
        try:
            django.setup()
        except Exception as e:
            print(f"Error setting up Django: {e}")
            sys.exit(1)
    
    def get_field_type(self, field) -> str:
        """Get TypeScript type for Django field."""
        field_type = type(field).__name__
        
        # Handle special cases
        if hasattr(field, 'choices') and field.choices:
            # Create union type for choices
            choices = [f"'{choice[0]}'" for choice in field.choices]
            return ' | '.join(choices)
        
        # Handle foreign key relationships
        if isinstance(field, (models.ForeignKey, models.OneToOneField)):
            related_model = field.related_model
            return f"{related_model.__name__} | number"
        
        if isinstance(field, models.ManyToManyField):
            related_model = field.related_model
            return f"{related_model.__name__}[] | number[]"
        
        return self.type_mappings.get(field_type, 'any')
    
    def is_field_optional(self, field) -> bool:
        """Check if field is optional in TypeScript."""
        return field.null or field.blank or hasattr(field, 'default')
    
    def generate_model_interface(self, model) -> str:
        """Generate TypeScript interface for a Django model."""
        model_name = model.__name__
        fields = []
        
        # Add model fields
        for field in model._meta.fields:
            field_name = field.name
            field_type = self.get_field_type(field)
            optional = self.is_field_optional(field)
            
            # Add field documentation if available
            help_text = getattr(field, 'help_text', '')
            if help_text:
                fields.append(f"  /** {help_text} */")
            
            optional_marker = '?' if optional else ''
            fields.append(f"  {field_name}{optional_marker}: {field_type};")
        
        # Add many-to-many fields
        for field in model._meta.many_to_many:
            field_name = field.name
            related_model = field.related_model
            fields.append(f"  {field_name}?: {related_model.__name__}[] | number[];")
        
        # Add reverse foreign key relationships
        for rel in model._meta.related_objects:
            if isinstance(rel, (models.ManyToOneRel, models.OneToOneRel)):
                field_name = rel.get_accessor_name()
                related_model = rel.related_model
                if isinstance(rel, models.ManyToOneRel):
                    fields.append(f"  {field_name}?: {related_model.__name__}[];")
                else:
                    fields.append(f"  {field_name}?: {related_model.__name__};")
        
        interface_body = '\n'.join(fields)
        
        return f"""export interface {model_name} {{
{interface_body}
}}"""
    
    def generate_api_response_types(self) -> str:
        """Generate common API response types."""
        return '''// Common API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T = any> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

export interface ValidationError {
  [field: string]: string[];
}

// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
}
'''
    
    def generate_types(self):
        """Generate all TypeScript types."""
        self.setup_django()
        
        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate types for each app
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('apps.'):
                app_name = app_config.name.split('.')[-1]
                interfaces = []
                
                # Generate interfaces for all models in the app
                for model in app_config.get_models():
                    interface = self.generate_model_interface(model)
                    interfaces.append(interface)
                
                if interfaces:
                    # Write app-specific types file
                    content = f'''// Auto-generated TypeScript types for {app_name} app
// Generated on: {self.get_timestamp()}
// Do not edit manually - this file is auto-generated

{chr(10).join(interfaces)}
'''
                    
                    output_file = self.output_path / f"{app_name}.types.ts"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"Generated types for {app_name}: {output_file}")
        
        # Generate common API types
        api_types = self.generate_api_response_types()
        api_types_file = self.output_path / "api.types.ts"
        with open(api_types_file, 'w', encoding='utf-8') as f:
            f.write(f'''// Common API Types
// Generated on: {self.get_timestamp()}
// Do not edit manually - this file is auto-generated

{api_types}
''')
        
        # Generate index file that exports all types
        self.generate_index_file()
        
        print(f"TypeScript types generated successfully in {self.output_path}")
    
    def generate_index_file(self):
        """Generate index.ts file that exports all types."""
        type_files = list(self.output_path.glob("*.types.ts"))
        exports = []
        
        for type_file in type_files:
            module_name = type_file.stem.replace('.types', '')
            exports.append(f"export * from './{type_file.stem}';")
        
        index_content = f'''// Auto-generated TypeScript types index
// Generated on: {self.get_timestamp()}
// Do not edit manually - this file is auto-generated

{chr(10).join(exports)}
'''
        
        index_file = self.output_path / "index.ts"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate TypeScript types from Django models')
    parser.add_argument('--django-path', default='apps/api', help='Path to Django project')
    parser.add_argument('--output-path', default='packages/types/src/generated', help='Output path for TypeScript types')
    parser.add_argument('--watch', action='store_true', help='Watch for changes and regenerate')
    
    args = parser.parse_args()
    
    generator = DjangoTypeGenerator(args.django_path, args.output_path)
    
    if args.watch:
        # Watch mode implementation
        import time
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class ModelChangeHandler(FileSystemEventHandler):
            def __init__(self, generator):
                self.generator = generator
                self.last_generated = 0
            
            def on_modified(self, event):
                if event.src_path.endswith('.py') and 'models.py' in event.src_path:
                    current_time = time.time()
                    if current_time - self.last_generated > 2:  # Debounce
                        print(f"Model file changed: {event.src_path}")
                        try:
                            self.generator.generate_types()
                            self.last_generated = current_time
                        except Exception as e:
                            print(f"Error regenerating types: {e}")
        
        print("Watching for Django model changes...")
        event_handler = ModelChangeHandler(generator)
        observer = Observer()
        observer.schedule(event_handler, args.django_path, recursive=True)
        observer.start()
        
        try:
            # Generate initial types
            generator.generate_types()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        generator.generate_types()


if __name__ == '__main__':
    main()