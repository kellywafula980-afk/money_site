# jobs/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from .models import JobListing, JobApplication
from .forms import JobApplicationForm, JobPostForm
from .scraper import scale_database_to_thousands
from .email_utils import mailer


def job_list_view(request):
    """Renders the live job stream with search functionality"""
    query = request.GET.get('search', '').strip()
    jobs = JobListing.objects.all().order_by('-id')
    
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(company_name__icontains=query) |
            Q(location__icontains=query)
        )
        
    context = {
        'jobs': jobs,
        'search_query': query,
    }
    
    return render(request, 'jobs/home.html', context)


homepage_job_board = job_list_view
content_batcher_dashboard = job_list_view


def job_detail_view(request, job_id):
    """Display a single job listing with application form"""
    job = get_object_or_404(JobListing, id=job_id)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        cover_letter = request.POST.get('cover_letter')
        portfolio_url = request.POST.get('portfolio_url', '')
        
        # Save to database
        application = JobApplication(
            job=job,
            full_name=full_name,
            email=email,
            phone=phone,
            cover_letter=cover_letter,
            portfolio_url=portfolio_url
        )
        application.save()
        
        # 📧 Send confirmation email to applicant
        mailer.send_confirmation(
            to_email=email,
            applicant_name=full_name,
            job_title=job.title,
            company_name=job.company_name
        )
        
        # 📧 Send notification to employer/admin
        mailer.send_employer_notification(application)
        
        # Show success page
        return render(request, 'jobs/application_success.html', {'job': job})
    
    return render(request, 'jobs/job_detail.html', {'job': job})


def secret_trigger_scraper(request):
    """Secure endpoint to populate the live production database"""
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
    """Dynamic sitemap - always shows current jobs"""
    jobs = JobListing.objects.all()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    xml += '<url>\n<loc>https://globalgigs-0096.onrender.com/</loc>\n<changefreq>daily</changefreq>\n<priority>1.0</priority>\n</url>\n'
    
    for job in jobs:
        xml += f'<url>\n<loc>https://globalgigs-0096.onrender.com/jobs/{job.id}/</loc>\n<changefreq>daily</changefreq>\n<priority>0.8</priority>\n</url>\n'
    
    xml += '</urlset>'
    return HttpResponse(xml, content_type='application/xml')


def robots_txt(request):
    content = """User-agent: *
Allow: /

Sitemap: https://globalgigs-0096.onrender.com/sitemap.xml"""
    return HttpResponse(content, content_type='text/plain')


def post_job_page(request):
    """Page where employers can post a job"""
    form = JobPostForm()
    return render(request, 'jobs/post_job.html', {'form': form})


def initiate_payment(request):
    """Initialize Paystack payment for job posting"""
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            request.session['pending_job'] = {
                'title': form.cleaned_data['title'],
                'company_name': form.cleaned_data['company_name'],
                'description': form.cleaned_data['description'],
                'location': form.cleaned_data['location'],
                'salary_range': form.cleaned_data['salary_range'],
            }
            
            import requests
            from django.conf import settings
            
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            data = {
                'email': request.POST.get('email'),
                'amount': 4900 * 100,
                'currency': 'KES',
                'callback_url': request.build_absolute_uri('/payment/callback/'),
                'metadata': {
                    'job_title': form.cleaned_data['title'],
                    'company': form.cleaned_data['company_name'],
                }
            }
            
            try:
                response = requests.post(
                    'https://api.paystack.co/transaction/initialize',
                    headers=headers,
                    json=data,
                    timeout=30
                )
                response_data = response.json()
                
                if response_data.get('status'):
                    return redirect(response_data['data']['authorization_url'])
                else:
                    messages.error(request, f"Payment initialization failed: {response_data.get('message')}")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    
    return redirect('post_job')


def payment_callback(request):
    """Handle Paystack payment callback"""
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, "No payment reference found")
        return redirect('post_job')
    
    import requests
    from django.conf import settings
    
    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
    
    try:
        response = requests.get(
            f'https://api.paystack.co/transaction/verify/{reference}',
            headers=headers,
            timeout=30
        )
        response_data = response.json()
        
        if response_data.get('status') and response_data['data']['status'] == 'success':
            pending_job = request.session.get('pending_job')
            if pending_job:
                job = JobListing.objects.create(
                    title=pending_job['title'],
                    company_name=pending_job['company_name'],
                    description=pending_job['description'],
                    location=pending_job['location'],
                    salary_range=pending_job['salary_range'],
                    apply_url='#',
                    is_approved=True,
                    is_featured=True,
                )
                del request.session['pending_job']
                
                # 📧 Send confirmation to employer about successful job posting
                mailer.send_email(
                    to_email=request.GET.get('email', 'kellysimiyu122@gmail.com'),
                    subject=f"Job Posted: {job.title} at {job.company_name}",
                    body=f"""
Your job has been successfully posted on GlobalGigs!

Job: {job.title}
Company: {job.company_name}
Location: {job.location}
Salary: {job.salary_range}

View your job: https://globalgigs-0096.onrender.com/jobs/{job.id}/

Thank you for using GlobalGigs!
"""
                )
                
                messages.success(request, f'✅ Payment successful! Your job "{job.title}" is now live!')
                return redirect('job_detail', job_id=job.id)
        else:
            messages.error(request, f"Payment verification failed: {response_data.get('message')}")
    except Exception as e:
        messages.error(request, f"Error verifying payment: {str(e)}")
    
    return redirect('post_job')