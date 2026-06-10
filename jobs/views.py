from django.shortcuts import render
from django.db.models import Q
from .models import JobListing

def job_list_view(request):
    """
    Renders the live job stream and enforces strict, high-intent keyword matching.
    Prevents boilerplate description texts from hijacking and breaking user queries.
    """
    # Grab the 'search' parameter passed from the front-end template form
    query = request.GET.get('search', '').strip()
    
    # Fetch all job listings ordered by descending primary key IDs (Latest First)
    jobs = JobListing.objects.all().order_by('-id')
    
    if query:
        # Aggressive Title, Company, and Location matching.
        # This keeps search intent highly precise and filters out out-of-context listings.
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(company_name__icontains=query) |
            Q(location__icontains=query)
        )
        
    context = {
        'jobs': jobs,
        'search_query': query,  # Sent back to maintain the value inside the search bar element
    }
    
    # Render explicitly down into your home.html layout mapping
    return render(request, 'jobs/home.html', context)

# 🔗 Explicit URL Routing Aliases
# Automatically maps your project's core/urls.py legacy path definitions directly here
homepage_job_board = job_list_view
content_batcher_dashboard = job_list_view

from django.http import HttpResponse
from .scraper import scale_database_to_thousands

def secret_trigger_scraper(request):
    """A secure, browser-accessible endpoint to populate the live production database."""
    # Simple security key check so random users can't trigger it
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized access.", status=403)
        
    try:
        scale_database_to_thousands()
        return HttpResponse("🚀 Database successfully scaled to 1,000+ live jobs!", status=200)
    except Exception as e:
        return HttpResponse(f"⚠️ Error running scraper: {str(e)}", status=500)
from django.http import HttpResponse
from .models import JobListing

def debug_jobs(request):
    """Shows how many jobs are in the database"""
    count = JobListing.objects.count()
    first_job = JobListing.objects.first()
    
    output = f"""
    <h1>Database Debug</h1>
    <p>Total JobListing objects: <strong>{count}</strong></p>
    """
    
    if first_job:
        output += f"""
        <h2>First Job:</h2>
        <ul>
            <li>ID: {first_job.id}</li>
            <li>Title: {first_job.title}</li>
            <li>Company: {first_job.company_name}</li>
            <li>Created: {first_job.created_at}</li>
        </ul>
        """
    else:
        output += "<p>⚠️ No jobs found in JobListing table!</p>"
    
    return HttpResponse(output)