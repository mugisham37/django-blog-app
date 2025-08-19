# Django Personal Blog System

A comprehensive, enterprise-grade Django backend application designed to power a professional blogging platform. This system demonstrates mastery-level Django development through sophisticated architecture, advanced features, and production-ready implementation.

## Features

- **Content Management**: Rich text editing, hierarchical categories, flexible tagging
- **User Management**: Extended user profiles, role-based permissions, social authentication
- **Interactive Features**: Hierarchical comments, content rating, search functionality
- **Performance**: Multi-level Redis caching, database optimization, background tasks
- **SEO**: XML sitemaps, meta tag generation, Open Graph support
- **Analytics**: Page view tracking, search analytics, comprehensive reporting
- **Security**: Input validation, XSS/CSRF protection, rate limiting
- **API**: RESTful API with Django REST Framework

## Technology Stack

- **Backend**: Django 5.0+, Python 3.11+
- **Database**: PostgreSQL with optimized queries
- **Caching**: Redis for multi-level caching
- **Background Tasks**: Celery with Redis broker
- **Rich Text**: CKEditor integration
- **API**: Django REST Framework
- **Testing**: pytest, Factory Boy, comprehensive test suite

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 13+
- Redis 6+

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd django-personal-blog-system
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements/development.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up database:

```bash
python manage.py migrate
python manage.py createsuperuser
```

6. Collect static files:

```bash
python manage.py collectstatic
```

7. Run development server:

```bash
python manage.py runserver
```

### Background Tasks

Start Celery worker and beat scheduler:

```bash
# Terminal 1: Celery worker
celery -A celery_app worker --loglevel=info

# Terminal 2: Celery beat scheduler
celery -A celery_app beat --loglevel=info
```

## Project Structure

```
django-personal-blog-system/
├── apps/                   # Django applications
│   ├── core/              # Core functionality and utilities
│   ├── accounts/          # User management and authentication
│   ├── blog/              # Blog content management
│   ├── comments/          # Comment system
│   └── analytics/         # Analytics and reporting
├── config/                # Project configuration
│   ├── settings/          # Environment-specific settings
│   ├── urls.py           # URL routing
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
├── templates/             # Django templates
├── static/               # Static files (CSS, JS, images)
├── media/                # User uploads
├── logs/                 # Application logs
├── requirements/         # Dependency management
├── celery_app.py        # Celery configuration
└── manage.py            # Django management script
```

## Configuration

The project uses a modular settings architecture:

- `base.py`: Common settings for all environments
- `development.py`: Development-specific settings
- `production.py`: Production-specific settings
- `testing.py`: Testing-specific settings

## Testing

Run the test suite:

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## API Documentation

The API is built with Django REST Framework and includes:

- Authentication endpoints
- Blog content CRUD operations
- Comment management
- Analytics data access

API documentation is available at `/api/docs/` when running the development server.

## Deployment

The application is production-ready with:

- Docker containerization support
- Comprehensive logging configuration
- Security hardening
- Performance optimization
- Health check endpoints

See deployment documentation for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or support, please open an issue on the GitHub repository.
