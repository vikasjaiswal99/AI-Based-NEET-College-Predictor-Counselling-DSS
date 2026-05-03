"""apps/accounts/web_urls.py"""
from django.urls import path
from .views import LoginView, RegisterView, LogoutView, ProfileView

app_name = 'accounts-web'

urlpatterns = [
    path('login/',    LoginView.as_view(),    name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/',   LogoutView.as_view(),   name='logout'),
    path('profile/',  ProfileView.as_view(),  name='profile'),
]
