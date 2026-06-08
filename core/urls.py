from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView  # 👈 MAKE SURE THIS IMPORT IS HERE

urlpatterns = [
    path('admin/', admin.site.admin_site_urls), # or your standard admin path
    path('', include('jobs.urls')),
    
    # 💰 PASTE THIS MAGIC LINE RIGHT HERE FOR GOOGLE
    path('ads.txt', TemplateView.as_view(template_name='ads.txt', content_type='text/plain')),
    
]
