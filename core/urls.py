# core/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # <-- Fixed: added the 's' to urls
    path('', include('jobs.urls')),
]