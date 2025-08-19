"""
Setup configuration for Enterprise Core package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="enterprise-core",
    version="1.0.0",
    author="Enterprise Development Team",
    author_email="dev@enterprise.com",
    description="Core business logic and utilities for enterprise applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/enterprise/core",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
        "Pillow>=9.0.0",
        "bleach>=5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-django>=4.5.0",
            "pytest-cov>=4.0.0",
            "factory-boy>=3.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "enterprise-core=enterprise_core.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)