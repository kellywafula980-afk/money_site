from django.contrib.sitemaps import Sitemap
from .models import JobListing, ScrapedJob  # Add any other job models

class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        # Try ALL possible job models
        jobs = JobListing.objects.all()
        
        # If JobListing is empty, try ScrapedJob
        if jobs.count() == 0:
            from .models import ScrapedJob
            jobs = ScrapedJob.objects.all()
            print(f"✅ Using ScrapedJob model, found {jobs.count()} jobs")
        
        # If still empty, try RemoteJob
        if jobs.count() == 0:
            from .models import RemoteJob
            jobs = RemoteJob.objects.all()
            print(f"✅ Using RemoteJob model, found {jobs.count()} jobs")
        
        return jobs

    def location(self, obj):
        # Handle different model types
        if hasattr(obj, 'get_absolute_url'):
            return obj.get_absolute_url()
        return f'/jobs/{obj.id}/'