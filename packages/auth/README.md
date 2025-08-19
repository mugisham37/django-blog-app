# Enterprise Authentication Package

A comprehensive authentication package providing JWT strategies, Multi-Factor Authentication (MFA), OAuth2 integration, and Role-Based Access Control (RBAC) for enterprise applications.

## Features

### 🔐 JWT Authentication

- Secure JWT token generation and validation
- Refresh token mechanism with automatic rotation
- Configurable token expiration and security settings
- Token revocation and blacklisting support

### 🛡️ Multi-Factor Authentication (MFA)

- **TOTP (Time-based One-Time Password)**: Compatible with Google Authenticator, Authy, etc.
- **SMS**: Send verification codes via SMS (Twilio, AWS SNS support)
- **Email**: Send verification codes via email with customizable templates
- Backup codes and trusted device management

### 🌐 OAuth2 Integration

- Support for multiple OAuth2 providers (Google, GitHub, Facebook, Microsoft)
- Secure authorization code flow
- User information retrieval from providers
- Configurable redirect URIs and scopes

### 👥 Role-Based Access Control (RBAC)

- Hierarchical role system with inheritance
- Fine-grained permissions with conditions
- Resource-based access control
- Built-in system roles (guest, user, moderator, admin)

### 🔒 Security Features

- Bcrypt password hashing with configurable rounds
- Password strength validation and policies
- Account lockout and rate limiting
- Secure token management and encryption
- Audit logging and security monitoring

## Installation

```bash
# Basic installation
pip install enterprise-auth-package

# With SMS support
pip install enterprise-auth-package[sms]

# With AWS support
pip install enterprise-auth-package[aws]

# With all optional dependencies
pip install enterprise-auth-package[all]

# Development installation
pip install enterprise-auth-package[dev]
```

## Quick Start

### JWT Authentication

```python
from auth_package import JWTStrategy, JWTConfig
from datetime import timedelta

# Configure JWT
config = JWTConfig(
    secret_key="your-secret-key",
    access_token_lifetime=timedelta(minutes=15),
    refresh_token_lifetime=timedelta(days=7)
)

jwt_auth = JWTStrategy(config)

# Generate tokens
tokens = jwt_auth.generate_tokens(
    user_id="user123",
    user_data={"email": "user@example.com", "roles": ["user"]}
)

print(f"Access Token: {tokens.access_token}")
print(f"Refresh Token: {tokens.refresh_token}")

# Validate token
try:
    payload = jwt_auth.validate_token(tokens.access_token)
    print(f"User ID: {payload['user_id']}")
except jwt.InvalidTokenError as e:
    print(f"Invalid token: {e}")

# Refresh access token
new_tokens = jwt_auth.refresh_access_token(tokens.refresh_token)
```

### Multi-Factor Authentication

#### TOTP (Authenticator App)

```python
from auth_package.mfa import TOTPProvider

totp = TOTPProvider()

# Setup TOTP for user
setup_data = totp.setup_user_totp("user123", "user@example.com")
print(f"Secret: {setup_data['secret']}")
print(f"QR Code: {setup_data['qr_code']}")  # Base64 encoded

# Generate challenge
challenge = totp.generate_challenge("user123", setup_data['secret'])
print(f"Challenge ID: {challenge.challenge_id}")

# Verify code
result = totp.verify_challenge(challenge.challenge_id, "123456")
if result.success:
    print("TOTP verified successfully!")
else:
    print(f"Verification failed: {result.message}")
```

#### SMS Authentication

```python
from auth_package.mfa import SMSProvider

# Configure SMS provider (Twilio example)
sms_config = {
    "provider": "twilio",
    "twilio_account_sid": "your_account_sid",
    "twilio_auth_token": "your_auth_token",
    "twilio_from_number": "+1234567890"
}

sms = SMSProvider(sms_config)

# Send SMS challenge
challenge = sms.generate_challenge("user123", "+1234567890")
if challenge.success:
    print(f"SMS sent! Challenge ID: {challenge.challenge_id}")

# Verify SMS code
result = sms.verify_challenge(challenge.challenge_id, "123456")
if result.success:
    print("SMS verified successfully!")
```

### OAuth2 Integration

```python
from auth_package import OAuth2Strategy, setup_google_oauth2

oauth2 = OAuth2Strategy()

# Setup Google OAuth2
google_config = setup_google_oauth2(
    client_id="your_google_client_id",
    client_secret="your_google_client_secret",
    redirect_uri="https://yourapp.com/auth/callback"
)

oauth2.register_provider("google", google_config)

# Get authorization URL
auth_url = oauth2.get_authorization_url("google", state="random_state")
print(f"Redirect user to: {auth_url}")

# Exchange code for token (in your callback handler)
token_data = oauth2.exchange_code_for_token("google", "authorization_code")
access_token = token_data["access_token"]

# Get user info
user_info = oauth2.get_user_info("google", access_token)
print(f"User: {user_info}")
```

### Role-Based Access Control

```python
from auth_package import RoleBasedPermission, Permission, PermissionAction
from auth_package.permissions import default_role_registry

# Create custom permission
blog_edit = Permission(
    name="blog.edit_own",
    action=PermissionAction.UPDATE,
    resource="blog",
    conditions={"owner_id": {"operator": "eq", "value": "user_id"}}
)

# Register permission and assign to role
default_role_registry.register_permission(blog_edit)
default_role_registry.assign_permission_to_role("user", "blog.edit_own")

# Check permissions
rbac = RoleBasedPermission(default_role_registry)

user_roles = ["user"]
context = {"owner_id": "user123", "user_id": "user123"}

can_edit = rbac.check_permission(
    user_roles,
    "blog",
    PermissionAction.UPDATE,
    context
)

if can_edit:
    print("User can edit their own blog posts")
```

### Password Security

```python
from auth_package import PasswordHasher, PasswordPolicy

# Configure password policy
policy = PasswordPolicy(
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digits=True,
    require_special_chars=True
)

hasher = PasswordHasher(rounds=12)
hasher.set_policy(policy)

# Validate password strength
validation = hasher.validate_password_strength(
    "MySecureP@ssw0rd123",
    user_info={"username": "john", "email": "john@example.com"}
)

if validation["valid"]:
    # Hash password
    hashed = hasher.hash_password("MySecureP@ssw0rd123")

    # Verify password
    is_valid = hasher.verify_password("MySecureP@ssw0rd123", hashed)
    print(f"Password valid: {is_valid}")
else:
    print(f"Password errors: {validation['errors']}")
```

### User Management

```python
from auth_package.models import User, UserProfile, UserStatus, default_user_repository

# Create user
user = User(
    id="user123",
    username="john_doe",
    email="john@example.com",
    status=UserStatus.ACTIVE,
    profile=UserProfile(
        first_name="John",
        last_name="Doe",
        display_name="John Doe"
    )
)

# Add roles
user.add_role("user")
user.add_role("blogger")

# Save user
default_user_repository.create_user(user)

# Retrieve user
retrieved_user = default_user_repository.get_user_by_email("john@example.com")
print(f"User: {retrieved_user.profile.full_name}")
print(f"Roles: {retrieved_user.roles}")
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key
JWT_ACCESS_TOKEN_LIFETIME=900  # 15 minutes
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days

# MFA Configuration
MFA_ISSUER_NAME="Your App Name"
MFA_CODE_LIFETIME=300  # 5 minutes

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=auth_package --cov-report=html

# Run specific test categories
pytest -m unit  # Unit tests only
pytest -m integration  # Integration tests only
```

## Development

```bash
# Install in development mode
pip install -e .[dev]

# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
mypy src/

# Run all checks
make check  # If Makefile is available
```

## Security Considerations

1. **Secret Management**: Store JWT secrets and API keys securely
2. **Token Storage**: Use secure storage for refresh tokens (Redis/Database)
3. **Rate Limiting**: Implement rate limiting for authentication endpoints
4. **HTTPS**: Always use HTTPS in production
5. **Password Policies**: Enforce strong password policies
6. **MFA**: Enable MFA for sensitive accounts
7. **Audit Logging**: Log all authentication events
8. **Regular Updates**: Keep dependencies updated

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions:

- GitHub Issues: https://github.com/enterprise/auth-package/issues
- Documentation: https://auth-package.readthedocs.io/
- Email: dev@enterprise.com
