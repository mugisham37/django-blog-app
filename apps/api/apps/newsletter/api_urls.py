"""
Newsletter API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'newsletter-api'

router = DefaultRouter()
router.register(r'subscribers', api_views.SubscriberViewSet, basename='subscriber')
router.register(r'campaigns', api_views.CampaignViewSet, basename='campaign')

urlpatterns = [
    path('', include(router.urls)),
    path('subscribe/', api_views.SubscribeView.as_view(), name='subscribe'),
    path('unsubscribe/<str:token>/', api_views.UnsubscribeView.as_view(), name='unsubscribe'),
    path('verify/<str:token>/', api_views.VerifyEmailView.as_view(), name='verify-email'),
    path('track/open/<str:tracking_id>/', api_views.TrackOpenView.as_view(), name='track-open'),
    path('track/click/<str:tracking_id>/', api_views.TrackClickView.as_view(), name='track-click'),
]