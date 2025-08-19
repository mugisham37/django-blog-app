"""
URL configuration for Django Personal Blog System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

# Import sitemaps
from apps.blog.sitemaps import (
    PostSitemap, CategorySitemap, TagSitemap, 
    StaticViewSitemap, NewsSitemap
)

sitemaps = {
    'posts': PostSitemap,
    'categories': CategorySitemap,
    'tags': TagSitemap,
    'static': StaticViewSitemap,
    'news': NewsSitemap,
}

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # CKEditor
    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # API Documentation
    path('api/docs/', include('apps.core.urls.api_docs', namespace='api-docs')),
    
    # API v1
    path('api/v1/', include('apps.blog.urls.api', namespace='blog-api-v1')),
    path('api/v1/', include('apps.comments.urls.api', namespace='comments-api-v1')),
    
    # Social media APIs
    path('api/social/', include('apps.blog.urls.social', namespace='social')),
    
    # API (default to v1 for backward compatibility)
    path('api/', include('apps.blog.urls.api', namespace='blog-api')),
    path('api/', include('apps.comments.urls.api', namespace='comments-api')),
    
    # Analytics
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    
    # Core security URLs
    path('core/', include('apps.core.urls', namespace='core')),
    path('security/', include('apps.core.security_urls', namespace='security')),
    
    # Main application URLs
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('comments/', include('apps.comments.urls', namespace='comments')),
    path('newsletter/', include('apps.newsletter.urls', namespace='newsletter')),
    path('', include('apps.blog.urls', namespace='blog')),
    
    # SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    
    # Health check
    path('health/', TemplateView.as_view(template_name='health.html'), name='health_check'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    # if 'debug_toolbar' in settings.INSTALLED_APPS:
    #     import debug_toolbar
    #     urlpatterns = [
    #         path('__debug__/', include(debug_toolbar.urls)),
    #     ] + urlpatterns

# Custom error handlers
handler404 = 'apps.core.views.handler404'
handler500 = 'apps.core.views.handler500'
handler403 = 'apps.core.views.handler403'