"""
Setup configuration for the enterprise authentication package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="enterprise-auth-package",
    version="1.0.0",
    author="Enterprise Development Team",
    author_email="dev@enterprise.com",
    description="Comprehensive authentication package with JWT, MFA, OAuth2, and RBAC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/enterprise/auth-package",
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
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Session",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyJWT>=2.8.0",
        "bcrypt>=4.0.0",
        "cryptography>=41.0.0",
        "pyotp>=2.9.0",
        "qrcode[pil]>=7.4.0",
        "requests>=2.31.0",
        "twilio>=8.5.0",  # Optional SMS provider
        "boto3>=1.28.0",  # Optional AWS SNS provider
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "sms": [
            "twilio>=8.5.0",
        ],
        "aws": [
            "boto3>=1.28.0",
        ],
        "all": [
            "twilio>=8.5.0",
            "boto3>=1.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "auth-cli=auth_package.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)