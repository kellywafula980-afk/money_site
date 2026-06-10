from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from jobs.views import debug_jobs, generate_sitemap  # Only need this once

# Try/except to handle the import gracefully
try:
    from jobs.sitemaps import JobSitemap
    sitemaps = {
        'jobs': JobSitemap,
    }
except ImportError:
    # Fallback - create an empty sitemap if the import fails
    from django.contrib.sitemaps import Sitemap
    class FallbackSitemap(Sitemap):
        def items(self):
            return []
    sitemaps = {
        'jobs': FallbackSitemap,
    }
    print("WARNING: Could not import JobSitemap, using fallback")

# Custom view with error handling
def sitemap_with_headers(request):
    try:
        response = sitemap(request, {'sitemaps': sitemaps})
        response['X-Robots-Tag'] = 'index, follow'
        return response
    except Exception as e:
        # Log the error and return a basic sitemap
        import logging
        logging.error(f"Sitemap error: {e}")
        from django.http import HttpResponse
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url>
<loc>https://globalgigs-0096.onrender.com/</loc>
<changefreq>daily</changefreq>
<priority>0.5</priority>
</url>
</urlset>'''
        response = HttpResponse(xml_content, content_type='application/xml')
        response['X-Robots-Tag'] = 'index, follow'
        return response

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('', include('jobs.urls')),
    path('ads.txt', TemplateView.as_view(template_name='jobs/ads.txt', content_type='text/plain')),
    path('google56bce93523ece129.html', TemplateView.as_view(template_name='jobs/google56bce93523ece129.html', content_type='text/html')),
    path('debug/', debug_jobs, name='debug'),

    # Sitemap URLs
    path('sitemap.xml', generate_sitemap, name='sitemap'),
    path('sitemap-new.xml', generate_sitemap, name='sitemap_new'),
]