from django.shortcuts import render
from .models import JobListing, ScriptBatch

# Keep your old content_batcher_dashboard code exactly as it is...

def homepage_job_board(request):
    """
    Pulls all approved, scraped job listings and displays them on the frontend
    """
    # Fetch the latest 50 jobs so the page loads lighting fast
    jobs = JobListing.objects.filter(is_approved=True).order_by('-created_at')[:50]
    
    return render(request, 'jobs/home.html', {'jobs': jobs})