# jobs/admin.py
from django.contrib import admin
from .models import JobListing

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('is_approved', 'is_featured')
    list_editable = ('is_approved', 'is_featured') # Lets us toggle paid posts directly from the list view!