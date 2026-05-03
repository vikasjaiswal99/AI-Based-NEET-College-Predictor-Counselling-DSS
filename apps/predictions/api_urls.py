"""predictions/api_urls.py — DRF REST API routes"""
from django.urls import path
from .views import PredictionAPIView
app_name = 'predictions-api'
urlpatterns = [
    path('predict/', PredictionAPIView.as_view(), name='predict'),
]
