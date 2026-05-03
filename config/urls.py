"""
config/urls.py — Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

api_v1 = [
    path('auth/',        include('apps.accounts.urls',    namespace='accounts')),
    path('colleges/',    include('apps.colleges.urls',    namespace='colleges')),
    path('predictions/', include('apps.predictions.api_urls', namespace='predictions-api')),
    path('counselling/', include('apps.counselling.urls', namespace='counselling')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Web UI (HTML views)
    path('',       include('apps.predictions.urls', namespace='predictions')),
    path('auth/',  include('apps.accounts.web_urls', namespace='accounts-web')),

    # REST API v1
    path('api/v1/', include((api_v1, 'v1'))),

    # API Docs
    path('api/schema/',       SpectacularAPIView.as_view(),       name='schema'),
    path('api/docs/',         SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/',   SpectacularRedocView.as_view(url_name='schema'),   name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
