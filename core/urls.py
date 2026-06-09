from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

# 🚀 1. Add these two imports:
from django.contrib.sitemaps.views import sitemap
from jobs.sitemaps import JobSitemap

# 🚀 2. Define the configuration map:
sitemaps = {
    'jobs': JobSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('', include('jobs.urls')),
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
    path('google56bce93523ece129.html', TemplateView.as_view(template_name='jobs/google56bce93523ece129.html', content_type='text/html')),
    
    # 🚀 3. ADD THIS EXACT SITEMAP LINE:
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]