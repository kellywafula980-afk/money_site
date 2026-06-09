from django.contrib.sitemaps import Sitemap
# 🚀 Change this to JobListing
from .models import JobListing  

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        # 🚀 Change this to JobListing
        return JobListing.objects.all().order_by('-id')