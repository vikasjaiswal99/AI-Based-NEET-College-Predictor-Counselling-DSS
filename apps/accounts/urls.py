"""accounts/urls.py — REST API routes"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
app_name = 'accounts'
urlpatterns = [
    path('token/',         TokenObtainPairView.as_view(),  name='token'),
    path('token/refresh/', TokenRefreshView.as_view(),     name='token-refresh'),
    path('token/logout/',  TokenBlacklistView.as_view(),   name='token-logout'),
]
