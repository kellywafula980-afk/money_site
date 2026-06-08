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