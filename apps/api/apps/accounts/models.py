"""
User Account Models
Handles user authentication, profiles, and account management.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
# from versatileimagefield.fields import VersatileImageField
import uuid


class User(AbstractUser):
    """Extended User model with additional fields."""
    
    class UserRole(models.TextChoices):
        READER = 'reader', _('Reader')
        AUTHOR = 'author', _('Author')
        EDITOR = 'editor', _('Editor')
        ADMIN = 'admin', _('Administrator')
    
    class UserStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
        PENDING = 'pending', _('Pending Verification')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        max_length=20, 
        choices=UserRole.choices, 
        default=UserRole.READER,
        help_text=_('User role determines permissions')
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.PENDING,
        help_text=_('Account status')
    )
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'pk': self.pk})
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def has_role(self, role):
        """Check if user has specific role."""
        return self.role == role
    
    def is_author_or_above(self):
        """Check if user can create content."""
        return self.role in [self.UserRole.AUTHOR, self.UserRole.EDITOR, self.UserRole.ADMIN]
    
    def is_editor_or_above(self):
        """Check if user can edit content."""
        return self.role in [self.UserRole.EDITOR, self.UserRole.ADMIN]


class Profile(models.Model):
    """User profile with additional information."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_('Profile picture')
    )
    bio = models.TextField(max_length=500, blank=True, help_text=_('Short biography'))
    website = models.URLField(blank=True, help_text=_('Personal website'))
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Social media links
    twitter_handle = models.CharField(max_length=50, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_username = models.CharField(max_length=50, blank=True)
    
    # Privacy settings
    show_email = models.BooleanField(default=False)
    show_real_name = models.BooleanField(default=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    comment_notifications = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'pk': self.user.pk})
    
    @property
    def display_name(self):
        """Get the display name based on privacy settings."""
        if self.show_real_name and self.user.full_name:
            return self.user.full_name
        return self.user.username
    
    @property
    def social_links(self):
        """Get all social media links."""
        links = {}
        if self.twitter_handle:
            links['twitter'] = f"https://twitter.com/{self.twitter_handle}"
        if self.linkedin_url:
            links['linkedin'] = self.linkedin_url
        if self.github_username:
            links['github'] = f"https://github.com/{self.github_username}"
        if self.website:
            links['website'] = self.website
        return links


class EmailVerification(models.Model):
    """Email verification tokens."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification'
        verbose_name = _('Email Verification')
        verbose_name_plural = _('Email Verifications')
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"Verification for {self.email}"
    
    def is_expired(self):
        """Check if token is expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid and not used."""
        return not self.used and not self.is_expired()


class LoginAttempt(models.Model):
    """Track login attempts for security."""
    
    class AttemptResult(models.TextChoices):
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')
        BLOCKED = 'blocked', _('Blocked')
    
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    result = models.CharField(max_length=20, choices=AttemptResult.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempt'
        verbose_name = _('Login Attempt')
        verbose_name_plural = _('Login Attempts')
        indexes = [
            models.Index(fields=['email', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.result} at {self.timestamp}"