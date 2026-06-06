# Create your models here.
# jobs/models.py
from django.db import models

class JobListing(models.Model):
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    company_website = models.URLField(blank=True, null=True)
    description = models.TextField()
    location = models.CharField(max_length=100, default="Remote")
    apply_url = models.URLField()
    
    # The Money Makers
    is_approved = models.BooleanField(default=False) # We approve it via admin panel before it goes live
    is_featured = models.BooleanField(default=False) # Companies pay extra to turn this True!
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"