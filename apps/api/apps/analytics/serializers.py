"""
Analytics API Serializers
"""

from rest_framework import serializers
from .models import (
    PageView, SearchQuery, Event, DailyStats, 
    PopularContent, UserSession
)


class PageViewSerializer(serializers.ModelSerializer):
    """Serializer for page views."""
    
    class Meta:
        model = PageView
        fields = [
            'url', 'title', 'referrer', 'device_type', 'browser', 'os',
            'country', 'city', 'time_on_page', 'timestamp'
        ]
        read_only_fields = ['timestamp']


class SearchQuerySerializer(serializers.ModelSerializer):
    """Serializer for search queries."""
    
    class Meta:
        model = SearchQuery
        fields = [
            'query', 'results_count', 'search_type', 'filters_applied', 'timestamp'
        ]
        read_only_fields = ['timestamp']


class EventSerializer(serializers.ModelSerializer):
    """Serializer for analytics events."""
    
    class Meta:
        model = Event
        fields = [
            'name', 'category', 'properties', 'value', 'timestamp'
        ]
        read_only_fields = ['timestamp']


class DailyStatsSerializer(serializers.ModelSerializer):
    """Serializer for daily statistics."""
    
    class Meta:
        model = DailyStats
        fields = [
            'date', 'total_page_views', 'unique_page_views', 'total_users',
            'new_users', 'returning_users', 'total_sessions', 'bounce_rate',
            'avg_session_duration', 'posts_published', 'comments_posted',
            'total_searches', 'unique_search_terms'
        ]


class PopularContentSerializer(serializers.ModelSerializer):
    """Serializer for popular content."""
    
    class Meta:
        model = PopularContent
        fields = [
            'content_type', 'content_id', 'title', 'url', 'period_start',
            'period_end', 'views', 'unique_views', 'avg_time_on_page',
            'bounce_rate', 'rank', 'previous_rank'
        ]


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions."""
    
    class Meta:
        model = UserSession
        fields = [
            'session_key', 'device_type', 'browser', 'os', 'country', 'city',
            'started_at', 'last_activity', 'ended_at', 'duration', 'page_views',
            'is_bounce'
        ]