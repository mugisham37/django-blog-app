"""
Newsletter API Serializers
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Subscriber, Campaign, EmailLog

User = get_user_model()


class SubscriberSerializer(serializers.ModelSerializer):
    """Serializer for newsletter subscribers."""
    
    class Meta:
        model = Subscriber
        fields = [
            'id', 'email', 'frequency', 'categories', 'is_active',
            'email_verified', 'source', 'subscribed_at', 'updated_at'
        ]
        read_only_fields = ['id', 'subscribed_at', 'updated_at']


class SubscribeSerializer(serializers.Serializer):
    """Serializer for newsletter subscription."""
    
    email = serializers.EmailField()
    frequency = serializers.ChoiceField(
        choices=Subscriber.Frequency.choices,
        default=Subscriber.Frequency.WEEKLY
    )
    source = serializers.CharField(max_length=100, required=False, default='api')
    
    def validate_email(self, value):
        """Validate email format and domain."""
        # Add any custom email validation here
        return value


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for newsletter campaigns."""
    
    created_by = serializers.StringRelatedField(read_only=True)
    open_rate = serializers.ReadOnlyField()
    click_rate = serializers.ReadOnlyField()
    bounce_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'subject', 'campaign_type', 'status',
            'scheduled_at', 'sent_at', 'total_recipients', 'emails_sent',
            'emails_delivered', 'emails_opened', 'emails_clicked',
            'emails_bounced', 'emails_unsubscribed', 'open_rate',
            'click_rate', 'bounce_rate', 'created_by', 'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'sent_at', 'total_recipients', 'emails_sent',
            'emails_delivered', 'emails_opened', 'emails_clicked',
            'emails_bounced', 'emails_unsubscribed', 'created_at',
            'updated_at'
        ]


class CampaignCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating campaigns."""
    
    target_category_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Campaign
        fields = [
            'name', 'subject', 'content_html', 'content_text',
            'campaign_type', 'target_frequency', 'target_category_ids',
            'scheduled_at'
        ]
    
    def create(self, validated_data):
        """Create campaign with target categories."""
        target_category_ids = validated_data.pop('target_category_ids', [])
        
        campaign = Campaign.objects.create(**validated_data)
        
        if target_category_ids:
            from apps.blog.models import Category
            categories = Category.objects.filter(id__in=target_category_ids)
            campaign.target_categories.set(categories)
        
        return campaign
    
    def update(self, instance, validated_data):
        """Update campaign with target categories."""
        target_category_ids = validated_data.pop('target_category_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if target_category_ids is not None:
            from apps.blog.models import Category
            categories = Category.objects.filter(id__in=target_category_ids)
            instance.target_categories.set(categories)
        
        return instance


class EmailLogSerializer(serializers.ModelSerializer):
    """Serializer for email logs."""
    
    class Meta:
        model = EmailLog
        fields = [
            'id', 'email_address', 'subject', 'status', 'queued_at',
            'sent_at', 'delivered_at', 'opened_at', 'clicked_at',
            'error_message', 'bounce_reason'
        ]