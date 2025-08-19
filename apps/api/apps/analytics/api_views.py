"""
Analytics API Views
RESTful API endpoints for analytics functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, ListAPIView
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta, date
from .models import (
    PageView, SearchQuery, Event, DailyStats, 
    PopularContent, UserSession
)
from .serializers import (
    PageViewSerializer, SearchQuerySerializer, EventSerializer,
    DailyStatsSerializer, PopularContentSerializer
)


class PageViewCreateView(CreateAPIView):
    """Track page views."""
    
    serializer_class = PageViewSerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        """Save page view with metadata."""
        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        # Get or create session
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=session_key,
            ip_address=ip,
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )


class SearchQueryCreateView(CreateAPIView):
    """Track search queries."""
    
    serializer_class = SearchQuerySerializer
    permission_classes = [permissions.AllowAny]
    
    def perform_create(self, serializer):
        """Save search query with metadata."""
        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        # Get session key
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_key=session_key,
            ip_address=ip
        )


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for managing analytics events."""
    
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Filter events based on user permissions."""
        if self.request.user.is_staff:
            return Event.objects.all()
        elif self.request.user.is_authenticated:
            return Event.objects.filter(user=self.request.user)
        return Event.objects.none()
    
    def perform_create(self, serializer):
        """Save event with metadata."""
        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        # Get session
        session = None
        session_key = self.request.session.session_key
        if session_key:
            try:
                session = UserSession.objects.get(session_key=session_key)
            except UserSession.DoesNotExist:
                pass
        
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session=session,
            ip_address=ip,
            url=self.request.data.get('url', ''),
            referrer=self.request.META.get('HTTP_REFERER', '')
        )


class DailyStatsView(ListAPIView):
    """Get daily statistics."""
    
    serializer_class = DailyStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get daily stats for the requested period."""
        if not self.request.user.is_staff:
            return DailyStats.objects.none()
        
        # Get date range from query parameters
        days = int(self.request.query_params.get('days', 30))
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return DailyStats.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('-date')


class PopularContentView(ListAPIView):
    """Get popular content."""
    
    serializer_class = PopularContentSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get popular content for the requested period."""
        # Get parameters
        content_type = self.request.query_params.get('type', 'post')
        days = int(self.request.query_params.get('days', 7))
        limit = int(self.request.query_params.get('limit', 10))
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        return PopularContent.objects.filter(
            content_type=content_type,
            period_start__gte=start_date,
            period_end__lte=end_date
        ).order_by('rank')[:limit]


class AnalyticsDashboardView(APIView):
    """Get analytics dashboard data."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get comprehensive analytics dashboard data."""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Page views
        page_views = PageView.objects.filter(timestamp__gte=start_date)
        total_page_views = page_views.count()
        unique_page_views = page_views.values('ip_address').distinct().count()
        
        # Users
        total_users = page_views.filter(user__isnull=False).values('user').distinct().count()
        
        # Sessions
        sessions = UserSession.objects.filter(started_at__gte=start_date)
        total_sessions = sessions.count()
        avg_session_duration = sessions.aggregate(avg_duration=Avg('duration'))['avg_duration'] or 0
        bounce_sessions = sessions.filter(is_bounce=True).count()
        bounce_rate = (bounce_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Top pages
        top_pages = (
            page_views.values('url', 'title')
            .annotate(views=Count('id'))
            .order_by('-views')[:10]
        )
        
        # Top search queries
        search_queries = SearchQuery.objects.filter(timestamp__gte=start_date)
        top_searches = (
            search_queries.values('query')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Daily trends
        daily_trends = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            day_views = page_views.filter(timestamp__date=current_date).count()
            day_users = page_views.filter(
                timestamp__date=current_date,
                user__isnull=False
            ).values('user').distinct().count()
            
            daily_trends.append({
                'date': current_date.isoformat(),
                'page_views': day_views,
                'users': day_users
            })
            current_date += timedelta(days=1)
        
        # Device breakdown
        device_stats = (
            page_views.values('device_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Browser breakdown
        browser_stats = (
            page_views.values('browser')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Country breakdown
        country_stats = (
            page_views.exclude(country='')
            .values('country')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        return Response({
            'overview': {
                'total_page_views': total_page_views,
                'unique_page_views': unique_page_views,
                'total_users': total_users,
                'total_sessions': total_sessions,
                'avg_session_duration': round(avg_session_duration, 2),
                'bounce_rate': round(bounce_rate, 2)
            },
            'top_pages': list(top_pages),
            'top_searches': list(top_searches),
            'daily_trends': daily_trends,
            'device_stats': list(device_stats),
            'browser_stats': list(browser_stats),
            'country_stats': list(country_stats)
        })