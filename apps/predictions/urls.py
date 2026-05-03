"""predictions/urls.py — Web UI routes"""
from django.urls import path
from .views import (
    PredictView, FormulaView, ScholarshipView, PredictionAPIView,
    PredictionHistoryView, CollegeExplorerView,
    ExportPDFView, CompareView, TrendView, AIChatbotView, AboutView
)

app_name = 'predictions'

urlpatterns = [
    path('',               PredictView.as_view(),            name='predict'),
    path('formula/',       FormulaView.as_view(),            name='formula'),
    path('scholarships/',  ScholarshipView.as_view(),        name='scholarships'),
    path('history/',       PredictionHistoryView.as_view(),  name='history'),
    path('colleges/',      CollegeExplorerView.as_view(),    name='colleges'),
    path('compare/',       CompareView.as_view(),            name='compare'),
    path('trends/',        TrendView.as_view(),              name='trends'),
    path('export-pdf/',    ExportPDFView.as_view(),          name='export-pdf'),
    path('chat/',          AIChatbotView.as_view(),          name='chat'),
    path('about/',         AboutView.as_view(),              name='about'),
    path('api/predict/',   PredictionAPIView.as_view(),      name='api-predict'),
]
