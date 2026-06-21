from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import JobListing, JobApplication, JobCategory
from .forms import JobApplicationForm, JobPostForm
from .scraper import scale_database_to_thousands
import requests
import json


# ============================================================
# HOMEPAGE & JOB LISTINGS
# ============================================================

def job_list_view(request):
    """Renders the live job stream with search and category filters"""
    query = request.GET.get('search', '').strip()
    category_slug = request.GET.get('category', '')
    
    # Start with all jobs
    jobs = JobListing.objects.all().order_by('-id')
    
    # 🏷️ FILTER BY CATEGORY (checks database for jobs in that category)
    if category_slug:
        try:
            # Get the category from database
            category = JobCategory.objects.get(slug=category_slug)
            # Filter jobs to only those with this category
            jobs = jobs.filter(category=category)
            print(f"🔍 Filtering jobs by category: {category.name} (found {jobs.count()} jobs)")
        except JobCategory.DoesNotExist:
            # If category doesn't exist, return empty results
            jobs = JobListing.objects.none()
            print(f"❌ Category '{category_slug}' not found")
    
    # 🔍 FILTER BY SEARCH QUERY
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(company_name__icontains=query) |
            Q(location__icontains=query)
        )
    
    # Get all categories for the dropdown
    categories = JobCategory.objects.all()
    
    context = {
        'jobs': jobs,
        'search_query': query,
        'categories': categories,
        'current_category': category_slug,
        'category_name': JobCategory.objects.get(slug=category_slug).name if category_slug and JobCategory.objects.filter(slug=category_slug).exists() else None,
    }
    
    return render(request, 'jobs/home.html', context)


# URL Aliases
homepage_job_board = job_list_view
content_batcher_dashboard = job_list_view


# ============================================================
# JOB DETAIL & APPLICATIONS
# ============================================================

def job_detail_view(request, job_id):
    """Display a single job listing with application form"""
    job = get_object_or_404(JobListing, id=job_id)
    
    if request.method == 'POST':
        application = JobApplication(
            job=job,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone', ''),
            cover_letter=request.POST.get('cover_letter'),
            portfolio_url=request.POST.get('portfolio_url', '')
        )
        application.save()
        return render(request, 'jobs/application_success.html', {'job': job})
    
    return render(request, 'jobs/job_detail.html', {'job': job})


# ============================================================
# SCRAPER & DEBUG
# ============================================================

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


def category_debug(request):
    """Debug view to check categories and jobs"""
    output = "<h1>Category Debug</h1>"
    
    categories = JobCategory.objects.all()
    output += f"<p>Total categories: {categories.count()}</p>"
    
    for cat in categories:
        job_count = cat.jobs.count()
        output += f"<p><strong>{cat.icon} {cat.name}</strong>: {job_count} jobs</p>"
        if job_count > 0:
            output += "<ul>"
            for job in cat.jobs.all()[:5]:
                output += f"<li>{job.title}</li>"
            if job_count > 5:
                output += f"<li>... and {job_count - 5} more</li>"
            output += "</ul>"
    
    return HttpResponse(output)


# ============================================================
# SITEMAP & ROBOTS
# ============================================================

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


# ============================================================
# PAYMENT & JOB POSTING (PAYSTACK)
# ============================================================

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
            
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json',
            }
            
            data = {
                'email': request.POST.get('email'),
                'amount': 4900 * 100,
                'currency': 'KES',
                'callback_url': request.build_absolute_uri(reverse('payment_callback')),
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
                messages.success(request, f'✅ Payment successful! Your job "{job.title}" is now live!')
                return redirect('job_detail', job_id=job.id)
        else:
            messages.error(request, f"Payment verification failed: {response_data.get('message')}")
    except Exception as e:
        messages.error(request, f"Error verifying payment: {str(e)}")
    
    return redirect('post_job')


# ============================================================
# MIGRATIONS & UTILITY
# ============================================================

def run_migrations(request):
    """Run migrations via URL (for Render free tier)"""
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized", status=403)
    
    try:
        call_command('migrate')
        return HttpResponse("✅ Migrations completed successfully!")
    except Exception as e:
        return HttpResponse(f"❌ Error: {str(e)}", status=500)


@csrf_exempt
@require_POST
def paystack_webhook(request):
    """Handle Paystack payment webhook notifications"""
    try:
        payload = json.loads(request.body)
        return HttpResponse(status=200)
    except Exception as e:
        return HttpResponse(status=400)

def create_categories_production(request):
    """Create categories on production database"""
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized", status=403)
    
    from .models import JobCategory
    categories = [
        ('Technology', 'technology', '💻'),
        ('Marketing', 'marketing', '📊'),
        ('Sales', 'sales', '🤝'),
        ('Healthcare', 'healthcare', '🏥'),
        ('Finance', 'finance', '💰'),
        ('Education', 'education', '📚'),
        ('Administrative', 'administrative', '📋'),
        ('Customer Service', 'customer-service', '🎧'),
        ('Design', 'design', '🎨'),
        ('Engineering', 'engineering', '🔧'),
        ('HR', 'hr', '👥'),
        ('Legal', 'legal', '⚖️'),
        ('Operations', 'operations', '📦'),
        ('Data', 'data', '📊'),
        ('Product', 'product', '📱'),
        ('Writing', 'writing', '✍️'),
        ('Consulting', 'consulting', '💡'),
        ('Real Estate', 'real-estate', '🏠'),
        ('Media', 'media', '🎬'),
    ]
    
    created = 0
    for name, slug, icon in categories:
        obj, is_new = JobCategory.objects.get_or_create(name=name, slug=slug, icon=icon)
        if is_new:
            created += 1
    
    return HttpResponse(f"✅ Created {created} new categories on production. Total: {JobCategory.objects.count()}")
