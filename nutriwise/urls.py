# urls.py
from django.urls import path
from . import views
from .models import UserProfile

app_name = 'nutriwise'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # This is the default dashboard
    path('dashboard/', views.dashboard, name='dashboard'),  # Keeps the dashboard route for the main dashboard
    path('dashboard2/', views.dashboard2, name='dashboard2'),  # Separate route for dashboard2
    path('update_profile/', views.update_profile, name='update_profile'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('entry/<int:entry_id>/', views.analysis_result, name='analysis_result'),
    path('profile/', views.profile, name='profile'),]
