from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from jobs.sitemaps import JobSitemap
from django.http import HttpResponse

# Define the configuration map:
sitemaps = {
    'jobs': JobSitemap,
}

# 🚀 Custom view to override X-Robots-Tag header
def sitemap_with_headers(request):
    response = sitemap(request, {'sitemaps': sitemaps})
    # Override the noindex header that Render/Cloudflare adds
    response['X-Robots-Tag'] = 'index, follow'
    return response

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('', include('jobs.urls')),
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
    path('google56bce93523ece129.html', TemplateView.as_view(template_name='jobs/google56bce93523ece129.html', content_type='text/html')),
    
    # 🚀 USE THIS UPDATED SITEMAP LINE instead of the old one:
    path('sitemap.xml', sitemap_with_headers, name='sitemap'),
]