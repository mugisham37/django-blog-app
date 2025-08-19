#!/usr/bin/env python3
"""
Enterprise Configuration Management Package Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="enterprise-config",
    version="1.0.0",
    author="Enterprise Development Team",
    author_email="dev@enterprise.com",
    description="Centralized configuration management for enterprise applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/enterprise/config-package",
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0",
        "cryptography>=41.0.0",
        "redis>=4.5.0",
        "watchdog>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "aws": [
            "boto3>=1.26.0",
        ],
        "vault": [
            "hvac>=1.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "enterprise-config=enterprise_config.cli:main",
        ],
    },
)