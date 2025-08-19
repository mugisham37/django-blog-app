"""
Comments API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'comments-api'

router = DefaultRouter()
router.register(r'comments', api_views.CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
    path('posts/<uuid:post_id>/comments/', api_views.PostCommentsView.as_view(), name='post-comments'),
    path('comments/<uuid:comment_id>/like/', api_views.CommentLikeView.as_view(), name='comment-like'),
    path('comments/<uuid:comment_id>/report/', api_views.CommentReportView.as_view(), name='comment-report'),
]