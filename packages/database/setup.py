"""
Enterprise Database Package Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="enterprise-database",
    version="0.1.0",
    author="Enterprise Team",
    author_email="team@enterprise.com",
    description="Enterprise-grade database abstraction layer with connection pooling and repository patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/enterprise/database-package",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Django",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=4.0,<5.0",
        "psycopg2-binary>=2.9.0",
        "redis>=4.0.0",
        "celery>=5.2.0",
        "python-decouple>=3.6",
        "sqlparse>=0.4.0",
        "django-extensions>=3.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "pytest-cov>=4.0.0",
            "factory-boy>=3.2.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
        ],
        "monitoring": [
            "prometheus-client>=0.15.0",
            "django-prometheus>=2.2.0",
        ],
        "testing": [
            "pytest-benchmark>=4.0.0",
            "pytest-mock>=3.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "db-migrate=enterprise_database.cli:migrate_command",
            "db-seed=enterprise_database.cli:seed_command",
            "db-backup=enterprise_database.cli:backup_command",
        ],
    },
)