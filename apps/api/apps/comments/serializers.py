"""
Comments API Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Comment, CommentLike, CommentReport

User = get_user_model()


class CommentAuthorSerializer(serializers.ModelSerializer):
    """Serializer for comment authors."""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""
    
    author = CommentAuthorSerializer(read_only=True)
    author_name = serializers.ReadOnlyField(source='get_author_name')
    author_website = serializers.ReadOnlyField(source='get_author_website')
    reply_count = serializers.ReadOnlyField()
    is_reply = serializers.ReadOnlyField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'author_name', 'author_website',
            'guest_name', 'guest_email', 'guest_website', 'is_approved',
            'is_spam', 'is_edited', 'created_at', 'updated_at',
            'reply_count', 'is_reply', 'replies'
        ]
        read_only_fields = [
            'is_approved', 'is_spam', 'is_edited', 'created_at', 'updated_at'
        ]
    
    def get_replies(self, obj):
        """Get replies to this comment."""
        if obj.is_reply:  # Don't show nested replies for replies
            return []
        
        replies = obj.get_replies()
        return CommentSerializer(replies, many=True, context=self.context).data


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""
    
    parent_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Comment
        fields = [
            'content', 'guest_name', 'guest_email', 'guest_website', 'parent_id'
        ]
    
    def validate(self, attrs):
        """Validate comment data."""
        request = self.context['request']
        
        # If user is not authenticated, require guest fields
        if not request.user.is_authenticated:
            if not attrs.get('guest_name'):
                raise serializers.ValidationError('Name is required for guest comments')
            if not attrs.get('guest_email'):
                raise serializers.ValidationError('Email is required for guest comments')
        
        # Validate parent comment
        parent_id = attrs.get('parent_id')
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id)
                if parent.parent:  # Don't allow nested replies
                    raise serializers.ValidationError('Cannot reply to a reply')
                attrs['parent'] = parent
            except Comment.DoesNotExist:
                raise serializers.ValidationError('Parent comment not found')
        
        return attrs
    
    def create(self, validated_data):
        """Create comment with parent if specified."""
        parent_id = validated_data.pop('parent_id', None)
        parent = validated_data.pop('parent', None)
        
        comment = Comment.objects.create(**validated_data)
        
        if parent:
            comment.parent = parent
            comment.save()
        
        return comment


class CommentLikeSerializer(serializers.ModelSerializer):
    """Serializer for comment likes."""
    
    class Meta:
        model = CommentLike
        fields = ['is_like', 'created_at']
        read_only_fields = ['created_at']


class CommentReportSerializer(serializers.ModelSerializer):
    """Serializer for comment reports."""
    
    class Meta:
        model = CommentReport
        fields = ['reason', 'description']
    
    def validate_description(self, value):
        """Validate description for 'other' reason."""
        reason = self.initial_data.get('reason')
        if reason == CommentReport.ReportReason.OTHER and not value:
            raise serializers.ValidationError(
                'Description is required when reason is "other"'
            )
        return value