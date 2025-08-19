"""
API v1 URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'v1'

# Create router for ViewSets
router = DefaultRouter()

# Register ViewSets when they're created
# router.register(r'posts', PostViewSet, basename='post')
# router.register(r'categories', CategoryViewSet, basename='category')
# router.register(r'tags', TagViewSet, basename='tag')
# router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Include app-specific API URLs
    path('accounts/', include('apps.accounts.api_urls')),
    path('blog/', include('apps.blog.api_urls')),
    path('comments/', include('apps.comments.api_urls')),
    path('analytics/', include('apps.analytics.api_urls')),
    path('newsletter/', include('apps.newsletter.api_urls')),
]