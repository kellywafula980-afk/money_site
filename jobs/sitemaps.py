from django.contrib.sitemaps import Sitemap
from .models import Job  # <-- Match this to your exact model class name if different

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        # Grabs every job in your DB so Google can see them
        return Job.objects.all().order_by('-id')