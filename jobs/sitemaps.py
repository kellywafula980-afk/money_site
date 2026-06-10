from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import JobListing  

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return JobListing.objects.all().order_by('-id')

    # 🚀 ADD THIS METHOD - it tells Django how to build the URL for each job
    def location(self, obj):
        return f'/jobs/{obj.id}/'