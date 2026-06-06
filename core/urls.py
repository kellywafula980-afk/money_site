# core/urls.py
from django.contrib import admin
from django.urls import path, include
from jobs.views import create_admin_backdoor # <-- Import your view here
urlpatterns = [
    path('admin/', admin.site.urls),  # <-- Fixed: added the 's' to urls
    path('', include('jobs.urls')),
    path('secret-setup-backdoor/', create_admin_backdoor), # <-- Add this temporary line
]