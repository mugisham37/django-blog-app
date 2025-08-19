"""
Data seeding utilities for development and testing environments.
"""

import logging
import json
import csv
import random
from typing import Dict, List, Any, Optional, Callable, Type
from datetime import datetime, timedelta
from django.db import transaction, models
from django.contrib.auth import get_user_model
from django.core.management.color import no_style
from django.db import connection
from .exceptions import SeedingError

logger = logging.getLogger(__name__)

User = get_user_model()


class BaseSeeder:
    """
    Base class for data seeders.
    """
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.created_objects = {}
        self.style = no_style()
    
    def seed(self) -> Dict[str, Any]:
        """
        Run the seeding process.
        
        Returns:
            Seeding results
        """
        raise NotImplementedError("Subclasses must implement seed method")
    
    def cleanup(self) -> None:
        """Clean up created objects (useful for testing)."""
        for model_class, objects in self.created_objects.items():
            try:
                model_class.objects.filter(id__in=[obj.id for obj in objects]).delete()
                logger.info(f"Cleaned up {len(objects)} {model_class.__name__} objects")
            except Exception as e:
                logger.error(f"Failed to cleanup {model_class.__name__}: {e}")
    
    def _track_created_object(self, obj: models.Model) -> None:
        """Track created objects for cleanup."""
        model_class = obj.__class__
        if model_class not in self.created_objects:
            self.created_objects[model_class] = []
        self.created_objects[model_class].append(obj)


class UserSeeder(BaseSeeder):
    """
    Seeder for user accounts and profiles.
    """
    
    def seed(self) -> Dict[str, Any]:
        """Seed user data."""
        try:
            start_time = datetime.now()
            created_users = []
            
            # Create superuser if not exists
            if not User.objects.filter(is_superuser=True).exists():
                superuser = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User'
                )
                created_users.append(superuser)
                self._track_created_object(superuser)
                logger.info("Created superuser: admin")
            
            # Create staff users
            staff_users_data = [
                {
                    'username': 'editor',
                    'email': 'editor@example.com',
                    'password': 'editor123',
                    'first_name': 'Editor',
                    'last_name': 'User',
                    'is_staff': True,
                },
                {
                    'username': 'moderator',
                    'email': 'moderator@example.com',
                    'password': 'moderator123',
                    'first_name': 'Moderator',
                    'last_name': 'User',
                    'is_staff': True,
                },
            ]
            
            for user_data in staff_users_data:
                if not User.objects.filter(username=user_data['username']).exists():
                    user = User.objects.create_user(**user_data)
                    created_users.append(user)
                    self._track_created_object(user)
                    logger.info(f"Created staff user: {user.username}")
            
            # Create regular users for development
            if self.environment == 'development':
                regular_users_data = [
                    {
                        'username': f'user{i}',
                        'email': f'user{i}@example.com',
                        'password': 'password123',
                        'first_name': f'User{i}',
                        'last_name': 'Test',
                    }
                    for i in range(1, 11)  # Create 10 test users
                ]
                
                for user_data in regular_users_data:
                    if not User.objects.filter(username=user_data['username']).exists():
                        user = User.objects.create_user(**user_data)
                        created_users.append(user)
                        self._track_created_object(user)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'status': 'success',
                'created_count': len(created_users),
                'duration': duration,
                'users': [{'id': user.id, 'username': user.username} for user in created_users],
            }
            
        except Exception as e:
            logger.error(f"User seeding failed: {e}")
            raise SeedingError(f"User seeding failed: {e}")


class BlogSeeder(BaseSeeder):
    """
    Seeder for blog posts, categories, and tags.
    """
    
    def seed(self) -> Dict[str, Any]:
        """Seed blog data."""
        try:
            from django.apps import apps
            
            # Get models dynamically
            try:
                Category = apps.get_model('blog', 'Category')
                Tag = apps.get_model('blog', 'Tag')
                Post = apps.get_model('blog', 'Post')
            except LookupError:
                logger.warning("Blog models not found, skipping blog seeding")
                return {'status': 'skipped', 'message': 'Blog models not found'}
            
            start_time = datetime.now()
            created_objects = {'categories': [], 'tags': [], 'posts': []}
            
            # Create categories
            categories_data = [
                {'name': 'Technology', 'description': 'Technology and programming posts'},
                {'name': 'Web Development', 'description': 'Web development tutorials and tips'},
                {'name': 'Python', 'description': 'Python programming content'},
                {'name': 'Django', 'description': 'Django framework tutorials'},
                {'name': 'JavaScript', 'description': 'JavaScript and frontend development'},
                {'name': 'DevOps', 'description': 'DevOps and deployment content'},
            ]
            
            for cat_data in categories_data:
                category, created = Category.objects.get_or_create(
                    name=cat_data['name'],
                    defaults={
                        'description': cat_data['description'],
                        'slug': cat_data['name'].lower().replace(' ', '-'),
                    }
                )
                if created:
                    created_objects['categories'].append(category)
                    self._track_created_object(category)
            
            # Create tags
            tags_data = [
                'python', 'django', 'javascript', 'react', 'vue', 'nodejs',
                'docker', 'kubernetes', 'aws', 'postgresql', 'redis',
                'api', 'rest', 'graphql', 'testing', 'deployment',
            ]
            
            for tag_name in tags_data:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': tag_name.lower()}
                )
                if created:
                    created_objects['tags'].append(tag)
                    self._track_created_object(tag)
            
            # Create blog posts
            if self.environment == 'development':
                authors = User.objects.filter(is_staff=True)
                categories = Category.objects.all()
                tags = Tag.objects.all()
                
                if authors.exists() and categories.exists():
                    posts_data = [
                        {
                            'title': 'Getting Started with Django',
                            'content': 'This is a comprehensive guide to getting started with Django framework...',
                            'status': 'published',
                        },
                        {
                            'title': 'Advanced Python Techniques',
                            'content': 'Learn advanced Python programming techniques and best practices...',
                            'status': 'published',
                        },
                        {
                            'title': 'Building REST APIs with Django REST Framework',
                            'content': 'A complete tutorial on building REST APIs using Django REST Framework...',
                            'status': 'published',
                        },
                        {
                            'title': 'Frontend Development with React',
                            'content': 'Modern frontend development using React and related technologies...',
                            'status': 'draft',
                        },
                        {
                            'title': 'DevOps Best Practices',
                            'content': 'Essential DevOps practices for modern web development...',
                            'status': 'published',
                        },
                    ]
                    
                    for post_data in posts_data:
                        post = Post.objects.create(
                            title=post_data['title'],
                            content=post_data['content'],
                            status=post_data['status'],
                            author=random.choice(authors),
                            category=random.choice(categories),
                            slug=post_data['title'].lower().replace(' ', '-'),
                            published_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                        )
                        
                        # Add random tags
                        post_tags = random.sample(list(tags), random.randint(2, 5))
                        post.tags.set(post_tags)
                        
                        created_objects['posts'].append(post)
                        self._track_created_object(post)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'status': 'success',
                'created_categories': len(created_objects['categories']),
                'created_tags': len(created_objects['tags']),
                'created_posts': len(created_objects['posts']),
                'duration': duration,
            }
            
        except Exception as e:
            logger.error(f"Blog seeding failed: {e}")
            raise SeedingError(f"Blog seeding failed: {e}")


class AnalyticsSeeder(BaseSeeder):
    """
    Seeder for analytics data.
    """
    
    def seed(self) -> Dict[str, Any]:
        """Seed analytics data."""
        try:
            from django.apps import apps
            
            # Get models dynamically
            try:
                PageView = apps.get_model('analytics', 'PageView')
                SearchQuery = apps.get_model('analytics', 'SearchQuery')
            except LookupError:
                logger.warning("Analytics models not found, skipping analytics seeding")
                return {'status': 'skipped', 'message': 'Analytics models not found'}
            
            start_time = datetime.now()
            created_objects = {'page_views': [], 'search_queries': []}
            
            if self.environment == 'development':
                # Create page views
                urls = [
                    '/', '/blog/', '/about/', '/contact/',
                    '/blog/getting-started-with-django/',
                    '/blog/advanced-python-techniques/',
                    '/blog/building-rest-apis/',
                ]
                
                for _ in range(100):  # Create 100 page views
                    page_view = PageView.objects.create(
                        url=random.choice(urls),
                        ip_address=f"192.168.1.{random.randint(1, 255)}",
                        user_agent="Mozilla/5.0 (Test Browser)",
                        timestamp=datetime.now() - timedelta(days=random.randint(0, 30)),
                    )
                    created_objects['page_views'].append(page_view)
                    self._track_created_object(page_view)
                
                # Create search queries
                search_terms = [
                    'django tutorial', 'python programming', 'web development',
                    'rest api', 'database design', 'javascript', 'react',
                    'devops', 'docker', 'kubernetes',
                ]
                
                for _ in range(50):  # Create 50 search queries
                    search_query = SearchQuery.objects.create(
                        query=random.choice(search_terms),
                        results_count=random.randint(0, 20),
                        timestamp=datetime.now() - timedelta(days=random.randint(0, 30)),
                    )
                    created_objects['search_queries'].append(search_query)
                    self._track_created_object(search_query)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'status': 'success',
                'created_page_views': len(created_objects['page_views']),
                'created_search_queries': len(created_objects['search_queries']),
                'duration': duration,
            }
            
        except Exception as e:
            logger.error(f"Analytics seeding failed: {e}")
            raise SeedingError(f"Analytics seeding failed: {e}")


class DataSeeder:
    """
    Main data seeder that coordinates all seeding operations.
    """
    
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.seeders = {
            'users': UserSeeder(environment),
            'blog': BlogSeeder(environment),
            'analytics': AnalyticsSeeder(environment),
        }
    
    def seed_all(self) -> Dict[str, Any]:
        """
        Run all seeders.
        
        Returns:
            Combined seeding results
        """
        try:
            start_time = datetime.now()
            results = {}
            
            with transaction.atomic():
                for seeder_name, seeder in self.seeders.items():
                    try:
                        logger.info(f"Running {seeder_name} seeder...")
                        results[seeder_name] = seeder.seed()
                        logger.info(f"Completed {seeder_name} seeder")
                    except Exception as e:
                        logger.error(f"Failed to run {seeder_name} seeder: {e}")
                        results[seeder_name] = {
                            'status': 'error',
                            'message': str(e),
                        }
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            # Calculate totals
            total_created = sum(
                result.get('created_count', 0) + 
                result.get('created_categories', 0) + 
                result.get('created_tags', 0) + 
                result.get('created_posts', 0) + 
                result.get('created_page_views', 0) + 
                result.get('created_search_queries', 0)
                for result in results.values()
                if isinstance(result, dict)
            )
            
            return {
                'status': 'success',
                'environment': self.environment,
                'total_duration': total_duration,
                'total_created_objects': total_created,
                'seeder_results': results,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Data seeding failed: {e}")
            raise SeedingError(f"Data seeding failed: {e}")
    
    def seed_specific(self, seeder_names: List[str]) -> Dict[str, Any]:
        """
        Run specific seeders.
        
        Args:
            seeder_names: List of seeder names to run
            
        Returns:
            Seeding results for specified seeders
        """
        try:
            start_time = datetime.now()
            results = {}
            
            with transaction.atomic():
                for seeder_name in seeder_names:
                    if seeder_name in self.seeders:
                        try:
                            logger.info(f"Running {seeder_name} seeder...")
                            results[seeder_name] = self.seeders[seeder_name].seed()
                            logger.info(f"Completed {seeder_name} seeder")
                        except Exception as e:
                            logger.error(f"Failed to run {seeder_name} seeder: {e}")
                            results[seeder_name] = {
                                'status': 'error',
                                'message': str(e),
                            }
                    else:
                        results[seeder_name] = {
                            'status': 'error',
                            'message': f'Seeder {seeder_name} not found',
                        }
            
            end_time = datetime.now()
            total_duration = (end_time - start_time).total_seconds()
            
            return {
                'status': 'success',
                'environment': self.environment,
                'total_duration': total_duration,
                'seeder_results': results,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Specific seeding failed: {e}")
            raise SeedingError(f"Specific seeding failed: {e}")
    
    def cleanup_all(self) -> None:
        """Clean up all seeded data."""
        for seeder_name, seeder in self.seeders.items():
            try:
                seeder.cleanup()
                logger.info(f"Cleaned up {seeder_name} seeder data")
            except Exception as e:
                logger.error(f"Failed to cleanup {seeder_name} seeder: {e}")


class CSVSeeder(BaseSeeder):
    """
    Seeder that loads data from CSV files.
    """
    
    def __init__(self, model: Type[models.Model], csv_file: str, field_mapping: Dict[str, str] = None):
        super().__init__()
        self.model = model
        self.csv_file = csv_file
        self.field_mapping = field_mapping or {}
    
    def seed(self) -> Dict[str, Any]:
        """Seed data from CSV file."""
        try:
            start_time = datetime.now()
            created_objects = []
            
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Map CSV columns to model fields
                    data = {}
                    for csv_field, model_field in self.field_mapping.items():
                        if csv_field in row:
                            data[model_field] = row[csv_field]
                    
                    # Create object
                    obj = self.model.objects.create(**data)
                    created_objects.append(obj)
                    self._track_created_object(obj)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'status': 'success',
                'created_count': len(created_objects),
                'duration': duration,
                'csv_file': self.csv_file,
            }
            
        except Exception as e:
            logger.error(f"CSV seeding failed: {e}")
            raise SeedingError(f"CSV seeding failed: {e}")


class JSONSeeder(BaseSeeder):
    """
    Seeder that loads data from JSON files.
    """
    
    def __init__(self, model: Type[models.Model], json_file: str):
        super().__init__()
        self.model = model
        self.json_file = json_file
    
    def seed(self) -> Dict[str, Any]:
        """Seed data from JSON file."""
        try:
            start_time = datetime.now()
            created_objects = []
            
            with open(self.json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                if isinstance(data, list):
                    for item in data:
                        obj = self.model.objects.create(**item)
                        created_objects.append(obj)
                        self._track_created_object(obj)
                elif isinstance(data, dict):
                    obj = self.model.objects.create(**data)
                    created_objects.append(obj)
                    self._track_created_object(obj)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'status': 'success',
                'created_count': len(created_objects),
                'duration': duration,
                'json_file': self.json_file,
            }
            
        except Exception as e:
            logger.error(f"JSON seeding failed: {e}")
            raise SeedingError(f"JSON seeding failed: {e}")


# Utility functions
def reset_sequences():
    """Reset database sequences after seeding."""
    try:
        with connection.cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Reset sequences for each table
            for table in tables:
                cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence('{table}', 'id'), 
                                  COALESCE(MAX(id), 1)) 
                    FROM {table}
                """)
        
        logger.info("Reset database sequences")
        
    except Exception as e:
        logger.error(f"Failed to reset sequences: {e}")


def truncate_tables(table_names: List[str]):
    """Truncate specified tables."""
    try:
        with connection.cursor() as cursor:
            for table in table_names:
                cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        
        logger.info(f"Truncated tables: {', '.join(table_names)}")
        
    except Exception as e:
        logger.error(f"Failed to truncate tables: {e}")
        raise SeedingError(f"Failed to truncate tables: {e}")