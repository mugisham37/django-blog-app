"""
Analytics API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'analytics-api'

router = DefaultRouter()
router.register(r'events', api_views.EventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),
    path('page-view/', api_views.PageViewCreateView.as_view(), name='page-view'),
    path('search/', api_views.SearchQueryCreateView.as_view(), name='search-query'),
    path('stats/daily/', api_views.DailyStatsView.as_view(), name='daily-stats'),
    path('stats/popular/', api_views.PopularContentView.as_view(), name='popular-content'),
    path('dashboard/', api_views.AnalyticsDashboardView.as_view(), name='dashboard'),
]