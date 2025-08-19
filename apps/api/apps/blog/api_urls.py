"""
Blog API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'blog-api'

router = DefaultRouter()
router.register(r'posts', api_views.PostViewSet, basename='post')
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'tags', api_views.TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
    path('posts/<slug:slug>/preview/', api_views.PostPreviewView.as_view(), name='post-preview'),
    path('posts/<slug:slug>/views/', api_views.PostViewCreateView.as_view(), name='post-view'),
    path('search/', api_views.PostSearchView.as_view(), name='post-search'),
    path('featured/', api_views.FeaturedPostsView.as_view(), name='featured-posts'),
]