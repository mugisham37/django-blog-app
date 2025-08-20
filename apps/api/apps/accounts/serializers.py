"""
Accounts API Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""
    
    social_links = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Profile
        fields = [
            'avatar', 'bio', 'website', 'location', 'birth_date',
            'twitter_handle', 'linkedin_url', 'github_username',
            'show_email', 'show_real_name', 'email_notifications',
            'comment_notifications', 'newsletter_subscription',
            'social_links', 'display_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for users."""
    
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'status', 'email_verified', 'date_joined',
            'last_login', 'is_active', 'profile', 'full_name'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'email_verified', 'status'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class MFASetupSerializer(serializers.Serializer):
    """Serializer for MFA setup."""
    
    mfa_type = serializers.ChoiceField(choices=['totp', 'sms', 'email'])
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    
    def validate(self, attrs):
        mfa_type = attrs.get('mfa_type')
        
        if mfa_type == 'sms' and not attrs.get('phone_number'):
            raise serializers.ValidationError("Phone number is required for SMS MFA")
        
        if mfa_type == 'email' and not attrs.get('email'):
            raise serializers.ValidationError("Email is required for Email MFA")
        
        return attrs


class MFAVerifySerializer(serializers.Serializer):
    """Serializer for MFA verification."""
    
    challenge_id = serializers.CharField(required=False)
    code = serializers.CharField()
    mfa_type = serializers.ChoiceField(choices=['totp', 'sms', 'email'], default='totp')


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value


class SessionSerializer(serializers.Serializer):
    """Serializer for session information."""
    
    session_id = serializers.CharField()
    device_type = serializers.CharField()
    ip_address = serializers.CharField()
    user_agent = serializers.CharField()
    created_at = serializers.DateTimeField()
    last_activity = serializers.DateTimeField()
    is_current = serializers.BooleanField(default=False)