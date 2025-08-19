"""
Accounts API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'accounts-api'

router = DefaultRouter()
router.register(r'users', api_views.UserViewSet, basename='user')
router.register(r'profiles', api_views.ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', api_views.RegisterView.as_view(), name='register'),
    path('auth/login/', api_views.LoginView.as_view(), name='login'),
    path('auth/logout/', api_views.LogoutView.as_view(), name='logout'),
    path('auth/verify-email/', api_views.VerifyEmailView.as_view(), name='verify-email'),
    path('auth/resend-verification/', api_views.ResendVerificationView.as_view(), name='resend-verification'),
    path('auth/password-reset/', api_views.PasswordResetView.as_view(), name='password-reset'),
    path('auth/password-reset-confirm/', api_views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]