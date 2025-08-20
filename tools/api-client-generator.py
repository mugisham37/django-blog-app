#!/usr/bin/env python3
"""
Django REST Framework API Client Generator

This script automatically generates TypeScript API client code from Django REST Framework.
It analyzes DRF viewsets, serializers, and URL patterns to create type-safe API clients.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import importlib.util
import django
from django.apps import apps
from django.conf import settings
from django.urls import get_resolver
from rest_framework import viewsets, serializers
from rest_framework.routers import DefaultRouter


class APIClientGenerator:
    """Generate TypeScript API client from Django REST Framework."""
    
    def __init__(self, django_project_path: str, output_path: str):
        self.django_project_path = Path(django_project_path)
        self.output_path = Path(output_path)
        self.discovered_endpoints = []
        self.discovered_serializers = {}
    
    def setup_django(self):
        """Setup Django environment."""
        sys.path.insert(0, str(self.django_project_path))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
        
        try:
            django.setup()
        except Exception as e:
            print(f"Error setting up Django: {e}")
            sys.exit(1)
    
    def discover_api_endpoints(self):
        """Discover API endpoints from URL patterns."""
        from django.urls import get_resolver
        
        resolver = get_resolver()
        self.discovered_endpoints = []
        
        def extract_endpoints(url_patterns, prefix=''):
            for pattern in url_patterns:
                if hasattr(pattern, 'url_patterns'):
                    # Include pattern (nested URLs)
                    new_prefix = prefix + str(pattern.pattern)
                    extract_endpoints(pattern.url_patterns, new_prefix)
                else:
                    # URL pattern
                    path = prefix + str(pattern.pattern)
                    if hasattr(pattern, 'callback'):
                        callback = pattern.callback
                        if hasattr(callback, 'cls'):
                            # Class-based view
                            view_class = callback.cls
                            if issubclass(view_class, viewsets.ModelViewSet):
                                self.analyze_viewset(view_class, path, pattern.name)
        
        try:
            extract_endpoints(resolver.url_patterns)
        except Exception as e:
            print(f"Error discovering endpoints: {e}")
    
    def analyze_viewset(self, viewset_class, path: str, name: Optional[str]):
        """Analyze a DRF viewset to extract API information."""
        model = getattr(viewset_class, 'queryset', None)
        if model:
            model = model.model
        
        serializer_class = getattr(viewset_class, 'serializer_class', None)
        
        endpoint_info = {
            'viewset': viewset_class.__name__,
            'model': model.__name__ if model else None,
            'path': path,
            'name': name,
            'serializer': serializer_class.__name__ if serializer_class else None,
            'actions': self.get_viewset_actions(viewset_class),
            'permissions': self.get_viewset_permissions(viewset_class),
            'filters': self.get_viewset_filters(viewset_class),
        }
        
        self.discovered_endpoints.append(endpoint_info)
        
        if serializer_class:
            self.analyze_serializer(serializer_class)
    
    def get_viewset_actions(self, viewset_class) -> List[str]:
        """Get available actions for a viewset."""
        actions = []
        
        # Standard ModelViewSet actions
        if hasattr(viewset_class, 'list'):
            actions.append('list')
        if hasattr(viewset_class, 'create'):
            actions.append('create')
        if hasattr(viewset_class, 'retrieve'):
            actions.append('retrieve')
        if hasattr(viewset_class, 'update'):
            actions.append('update')
        if hasattr(viewset_class, 'partial_update'):
            actions.append('partial_update')
        if hasattr(viewset_class, 'destroy'):
            actions.append('destroy')
        
        # Custom actions
        for attr_name in dir(viewset_class):
            attr = getattr(viewset_class, attr_name)
            if hasattr(attr, 'mapping'):
                actions.append(attr_name)
        
        return actions
    
    def get_viewset_permissions(self, viewset_class) -> List[str]:
        """Get permission classes for a viewset."""
        permission_classes = getattr(viewset_class, 'permission_classes', [])
        return [cls.__name__ for cls in permission_classes]
    
    def get_viewset_filters(self, viewset_class) -> Dict[str, Any]:
        """Get filter information for a viewset."""
        filters = {}
        
        if hasattr(viewset_class, 'filterset_class'):
            filters['filterset'] = viewset_class.filterset_class.__name__
        
        if hasattr(viewset_class, 'search_fields'):
            filters['search_fields'] = viewset_class.search_fields
        
        if hasattr(viewset_class, 'ordering_fields'):
            filters['ordering_fields'] = viewset_class.ordering_fields
        
        return filters
    
    def analyze_serializer(self, serializer_class):
        """Analyze a DRF serializer to extract field information."""
        if serializer_class.__name__ in self.discovered_serializers:
            return
        
        serializer_info = {
            'name': serializer_class.__name__,
            'fields': {},
            'read_only_fields': getattr(serializer_class.Meta, 'read_only_fields', []) if hasattr(serializer_class, 'Meta') else [],
            'write_only_fields': [],
        }
        
        # Analyze serializer fields
        serializer_instance = serializer_class()
        for field_name, field in serializer_instance.fields.items():
            field_info = {
                'type': type(field).__name__,
                'required': field.required,
                'read_only': field.read_only,
                'write_only': field.write_only,
                'allow_null': field.allow_null,
                'help_text': getattr(field, 'help_text', ''),
            }
            
            # Handle choices
            if hasattr(field, 'choices'):
                field_info['choices'] = list(field.choices.keys())
            
            # Handle nested serializers
            if isinstance(field, serializers.Serializer):
                field_info['nested_serializer'] = type(field).__name__
                self.analyze_serializer(type(field))
            
            serializer_info['fields'][field_name] = field_info
            
            if field.write_only:
                serializer_info['write_only_fields'].append(field_name)
        
        self.discovered_serializers[serializer_class.__name__] = serializer_info
    
    def generate_api_client_base(self) -> str:
        """Generate base API client class."""
        return '''import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface RequestOptions extends AxiosRequestConfig {
  skipAuth?: boolean;
}

export class ApiClientBase {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private onTokenRefresh?: (tokens: { access: string; refresh: string }) => void;

  constructor(config: ApiClientConfig) {
    this.client = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
       
 this.client.interceptors.request.use(
      (config) => {
        if (!config.skipAuth && this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (this.refreshToken) {
            try {
              const response = await this.refreshAccessToken();
              this.setTokens(response.access_token, this.refreshToken);
              originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
              return this.client(originalRequest);
            } catch (refreshError) {
              this.clearTokens();
              throw refreshError;
            }
          }
        }

        throw error;
      }
    );
  }

  setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
  }

  setTokenRefreshCallback(callback: (tokens: { access: string; refresh: string }) => void) {
    this.onTokenRefresh = callback;
  }

  private async refreshAccessToken(): Promise<{ access_token: string }> {
    const response = await this.client.post('/auth/refresh/', {
      refresh_token: this.refreshToken,
    }, { skipAuth: true });
    return response.data;
  }

  async request<T = any>(config: RequestOptions): Promise<AxiosResponse<T>> {
    return this.client.request<T>(config);
  }

  async get<T = any>(url: string, config?: RequestOptions): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  async post<T = any>(url: string, data?: any, config?: RequestOptions): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  async put<T = any>(url: string, data?: any, config?: RequestOptions): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  async patch<T = any>(url: string, data?: any, config?: RequestOptions): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config);
  }

  async delete<T = any>(url: string, config?: RequestOptions): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail: string;
  code?: string;
}

export class ApiService<T = any> {
  constructor(
    protected client: ApiClientBase,
    protected baseEndpoint: string
  ) {}

  async list(params?: Record<string, any>): Promise<PaginatedResponse<T>> {
    const response = await this.client.get<PaginatedResponse<T>>(this.baseEndpoint, { params });
    return response.data;
  }

  async retrieve(id: string | number): Promise<T> {
    const response = await this.client.get<T>(`${this.baseEndpoint}${id}/`);
    return response.data;
  }

  async create(data: Partial<T>): Promise<T> {
    const response = await this.client.post<T>(this.baseEndpoint, data);
    return response.data;
  }

  async update(id: string | number, data: Partial<T>): Promise<T> {
    const response = await this.client.put<T>(`${this.baseEndpoint}${id}/`, data);
    return response.data;
  }

  async partialUpdate(id: string | number, data: Partial<T>): Promise<T> {
    const response = await this.client.patch<T>(`${this.baseEndpoint}${id}/`, data);
    return response.data;
  }

  async delete(id: string | number): Promise<void> {
    await this.client.delete(`${this.baseEndpoint}${id}/`);
  }
}
'''
    
    def generate_service_class(self, endpoint_info: Dict[str, Any]) -> str:
        """Generate service class for an endpoint."""
        model_name = endpoint_info['model']
        viewset_name = endpoint_info['viewset']
        actions = endpoint_info['actions']
        
        if not model_name:
            return ""
        
        service_name = f"{model_name}Service"
        
        methods = []
        
        # Generate methods based on available actions
        if 'list' in actions:
            methods.append(f"""
  async list(params?: {{
    page?: number;
    page_size?: number;
    search?: string;
    ordering?: string;
    [key: string]: any;
  }}): Promise<PaginatedResponse<{model_name}>> {{
    return super.list(params);
  }}""")
        
        if 'retrieve' in actions:
            methods.append(f"""
  async get(id: string | number): Promise<{model_name}> {{
    return super.retrieve(id);
  }}""")
        
        if 'create' in actions:
            methods.append(f"""
  async create(data: Partial<{model_name}>): Promise<{model_name}> {{
    return super.create(data);
  }}""")
        
        if 'update' in actions:
            methods.append(f"""
  async update(id: string | number, data: Partial<{model_name}>): Promise<{model_name}> {{
    return super.update(id, data);
  }}""")
        
        if 'partial_update' in actions:
            methods.append(f"""
  async patch(id: string | number, data: Partial<{model_name}>): Promise<{model_name}> {{
    return super.partialUpdate(id, data);
  }}""")
        
        if 'destroy' in actions:
            methods.append(f"""
  async delete(id: string | number): Promise<void> {{
    return super.delete(id);
  }}""")
        
        # Add custom actions
        for action in actions:
            if action not in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
                methods.append(f"""
  async {action}(id?: string | number, data?: any): Promise<any> {{
    const url = id ? `${{this.baseEndpoint}}${{id}}/{action}/` : `${{this.baseEndpoint}}{action}/`;
    const response = await this.client.post(url, data);
    return response.data;
  }}""")
        
        methods_str = ''.join(methods)
        
        return f"""export class {service_name} extends ApiService<{model_name}> {{
  constructor(client: ApiClientBase) {{
    super(client, '/api/v1/{model_name.lower()}s/');
  }}{methods_str}
}}"""
    
    def generate_api_client(self) -> str:
        """Generate complete API client."""
        self.setup_django()
        self.discover_api_endpoints()
        
        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate base client
        base_client = self.generate_api_client_base()
        
        # Generate service classes
        services = []
        service_imports = []
        service_exports = []
        
        for endpoint in self.discovered_endpoints:
            if endpoint['model']:
                service_class = self.generate_service_class(endpoint)
                if service_class:
                    services.append(service_class)
                    service_name = f"{endpoint['model']}Service"
                    service_imports.append(f"import {{ {endpoint['model']} }} from '../types/{endpoint['model'].lower()}.types';")
                    service_exports.append(service_name)
        
        # Generate main API client class
        main_client = f"""
export class ApiClient {{
  private baseClient: ApiClientBase;
  
  // Service instances
{chr(10).join([f"  public {endpoint['model'].lower()}s: {endpoint['model']}Service;" for endpoint in self.discovered_endpoints if endpoint['model']])}

  constructor(config: ApiClientConfig) {{
    this.baseClient = new ApiClientBase(config);
    
    // Initialize services
{chr(10).join([f"    this.{endpoint['model'].lower()}s = new {endpoint['model']}Service(this.baseClient);" for endpoint in self.discovered_endpoints if endpoint['model']])}
  }}

  setTokens(accessToken: string, refreshToken: string) {{
    this.baseClient.setTokens(accessToken, refreshToken);
  }}

  clearTokens() {{
    this.baseClient.clearTokens();
  }}

  setTokenRefreshCallback(callback: (tokens: {{ access: string; refresh: string }}) => void) {{
    this.baseClient.setTokenRefreshCallback(callback);
  }}
}}
"""
        
        # Combine all parts
        imports = '\n'.join(set(service_imports))
        services_code = '\n\n'.join(services)
        
        complete_client = f"""// Auto-generated API client
// Generated on: {self.get_timestamp()}
// Do not edit manually - this file is auto-generated

{imports}

{base_client}

{services_code}

{main_client}

// Export everything
export * from './base';
export {{ ApiClient as default }};
"""
        
        # Write to file
        client_file = self.output_path / "index.ts"
        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(complete_client)
        
        # Generate configuration file
        self.generate_config_file()
        
        print(f"API client generated successfully: {client_file}")
        return str(client_file)
    
    def generate_config_file(self):
        """Generate API client configuration file."""
        config_content = f"""// API Client Configuration
// Generated on: {self.get_timestamp()}

export const API_CONFIG = {{
  development: {{
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    timeout: 30000,
  }},
  production: {{
    baseURL: process.env.NEXT_PUBLIC_API_URL || '/api/v1',
    timeout: 30000,
  }},
  staging: {{
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://staging-api.example.com/api/v1',
    timeout: 30000,
  }},
}};

export const getApiConfig = () => {{
  const env = process.env.NODE_ENV || 'development';
  return API_CONFIG[env as keyof typeof API_CONFIG] || API_CONFIG.development;
}};

// Discovered endpoints
export const API_ENDPOINTS = {json.dumps([
    {
        'path': endpoint['path'],
        'model': endpoint['model'],
        'actions': endpoint['actions'],
        'permissions': endpoint['permissions']
    }
    for endpoint in self.discovered_endpoints
], indent=2)};
"""
        
        config_file = self.output_path / "config.ts"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
    
    def get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate TypeScript API client from Django REST Framework')
    parser.add_argument('--django-path', default='apps/api', help='Path to Django project')
    parser.add_argument('--output-path', default='packages/api-client/src/generated', help='Output path for API client')
    parser.add_argument('--watch', action='store_true', help='Watch for changes and regenerate')
    
    args = parser.parse_args()
    
    generator = APIClientGenerator(args.django_path, args.output_path)
    
    if args.watch:
        # Watch mode implementation
        import time
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class APIChangeHandler(FileSystemEventHandler):
            def __init__(self, generator):
                self.generator = generator
                self.last_generated = 0
            
            def on_modified(self, event):
                if event.src_path.endswith('.py') and any(x in event.src_path for x in ['views.py', 'serializers.py', 'urls.py']):
                    current_time = time.time()
                    if current_time - self.last_generated > 2:  # Debounce
                        print(f"API file changed: {event.src_path}")
                        try:
                            self.generator.generate_api_client()
                            self.last_generated = current_time
                        except Exception as e:
                            print(f"Error regenerating API client: {e}")
        
        print("Watching for Django API changes...")
        event_handler = APIChangeHandler(generator)
        observer = Observer()
        observer.schedule(event_handler, args.django_path, recursive=True)
        observer.start()
        
        try:
            # Generate initial client
            generator.generate_api_client()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        generator.generate_api_client()


if __name__ == '__main__':
    main()