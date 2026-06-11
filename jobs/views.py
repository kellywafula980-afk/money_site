from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from .models import JobListing
from .forms import JobApplicationForm
from .scraper import scale_database_to_thousands

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

def generate_sitemap(request):
    """Direct sitemap generator - bypasses Django's sitemap framework and shows ALL jobs"""
    jobs = JobListing.objects.all()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Add homepage
    xml += '''<url>
<loc>https://globalgigs-0096.onrender.com/</loc>
<changefreq>daily</changefreq>
<priority>1.0</priority>
</url>\n'''
    
    # Add each job
    for job in jobs:
        xml += f'''<url>
<loc>https://globalgigs-0096.onrender.com/jobs/{job.id}/</loc>
<changefreq>daily</changefreq>
<priority>0.8</priority>
</url>\n'''
    
    xml += '</urlset>'
    return HttpResponse(xml, content_type='application/xml')

def job_detail_view(request, job_id):
    """Display a single job listing with application form"""
    from django.shortcuts import get_object_or_404, render
    from .models import JobListing, JobApplication
    
    job = get_object_or_404(JobListing, id=job_id)
    
    if request.method == 'POST':
        # Save to database
        application = JobApplication(
            job=job,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            cover_letter=request.POST.get('cover_letter'),
            portfolio_url=request.POST.get('portfolio_url', '')
        )
        application.save()
        
        # Show success page using template
        return render(request, 'jobs/application_success.html', {'job': job})
    
    return render(request, 'jobs/job_detail.html', {'job': job})


import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from .forms import JobPostForm

stripe.api_key = settings.STRIPE_SECRET_KEY

def post_job_page(request):
    """Page where employers can post a job"""
    form = JobPostForm()
    return render(request, 'jobs/post_job.html', {
        'form': form,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    })

def create_checkout_session(request):
    """Creates Stripe checkout session for job posting"""
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            # Save job data in session temporarily
            request.session['pending_job'] = {
                'title': form.cleaned_data['title'],
                'company_name': form.cleaned_data['company_name'],
                'description': form.cleaned_data['description'],
                'location': form.cleaned_data['location'],
                'salary_range': form.cleaned_data['salary_range'],
            }
            
            # Create Stripe checkout session
            try:
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'usd',
                                'unit_amount': 4900,  # $49.00
                                'product_data': {
                                    'name': 'Job Posting - 30 Days',
                                    'description': 'Post your job for 30 days on GlobalGigs',
                                },
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url=request.build_absolute_uri(reverse('payment_success')),
                    cancel_url=request.build_absolute_uri(reverse('payment_cancel')),
                )
                return redirect(checkout_session.url)
            except Exception as e:
                return HttpResponse(f"Error creating checkout: {e}")
    return redirect('post_job')

def payment_success(request):
    """Handle successful payment and save job"""
    pending_job = request.session.get('pending_job')
    if pending_job:
        job = JobListing.objects.create(
            title=pending_job['title'],
            company_name=pending_job['company_name'],
            description=pending_job['description'],
            location=pending_job['location'],
            salary_range=pending_job['salary_range'],
            apply_url='#',  # Placeholder, employer can update
            is_approved=True,
            is_featured=True,  # Featured for paid jobs
        )
        del request.session['pending_job']
        return render(request, 'jobs/payment_success.html', {'job': job})
    return redirect('home')

def payment_cancel(request):
    """Handle cancelled payment"""
    return render(request, 'jobs/payment_cancel.html')
def robots_txt(request):
    from django.http import HttpResponse
    content = """User-agent: *
Allow: /

Sitemap: https://globalgigs-0096.onrender.com/sitemap.xml"""
    return HttpResponse(content, content_type='text/plain')
