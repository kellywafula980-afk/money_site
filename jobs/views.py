import json
import os
from urllib.parse import unquote

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.http import HttpResponse, Http404, FileResponse
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import JobListing, JobApplication, JobCategory
from .forms import JobApplicationForm, JobPostForm


# ============================================================
# ROBOTS.TXT (MUST BE DEFINED FIRST)
# ============================================================

def robots_txt(request):
    content = """User-agent: *
Allow: /

Sitemap: https://globalgigs-0096.onrender.com/sitemap.xml"""
    return HttpResponse(content, content_type='text/plain')


# ============================================================
# HOMEPAGE & JOB LISTINGS
# ============================================================

def job_list_view(request):
    """Renders the live job stream with search and category filters"""
    query = request.GET.get('search', '').strip()
    category_slug = request.GET.get('category', '')

    jobs = JobListing.objects.filter(is_active=True).order_by('-id')

    if category_slug:
        try:
            category = JobCategory.objects.get(slug=category_slug)
            jobs = jobs.filter(category=category)
        except JobCategory.DoesNotExist:
            jobs = JobListing.objects.none()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(company_name__icontains=query) |
            Q(location__icontains=query)
        )

    categories = JobCategory.objects.all()

    category_name = None
    if category_slug and JobCategory.objects.filter(slug=category_slug).exists():
        category_name = JobCategory.objects.get(slug=category_slug).name

    context = {
        'jobs': jobs,
        'search_query': query,
        'categories': categories,
        'current_category': category_slug,
        'category_name': category_name,
    }

    # Make sure you have templates/jobs/home.html
    return render(request, 'jobs/home.html', context)


homepage_job_board = job_list_view
content_batcher_dashboard = job_list_view


# ============================================================
# JOB DETAIL (SLUG VERSION)
# ============================================================

def job_detail_view(request, slug):
    job = get_object_or_404(JobListing, slug=slug, is_active=True)
    job.increment_views()

    if not job.responsibilities and job.description:
        try:
            from .scraper import parse_job_sections
            parsed, clean_desc = parse_job_sections(job.description)
            if parsed:
                job.responsibilities = parsed.get('responsibilities', '')
                job.requirements = parsed.get('requirements', '')
                job.benefits = parsed.get('benefits', '')
                job.company_description = parsed.get('about_company', '')
                job.save()
        except Exception as e:
            print(f"⚠️ Error parsing job {job.id}: {e}")

    related_jobs = JobListing.objects.filter(
        category=job.category
    ).exclude(id=job.id)[:6] if job.category else []

    if not related_jobs and job.title:
        title_words = job.title.split()[:3]
        if title_words:
            related_jobs = JobListing.objects.filter(
                Q(title__icontains=title_words[0]) |
                Q(company_name__icontains=job.company_name[:20])
            ).exclude(id=job.id)[:6]

    if request.method == 'POST':
        if 'full_name' in request.POST and 'email' in request.POST:
            try:
                application = JobApplication(
                    job=job,
                    full_name=request.POST.get('full_name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone', ''),
                    cover_letter=request.POST.get('cover_letter'),
                    portfolio_url=request.POST.get('portfolio_url', '')
                )
                if request.FILES.get('resume'):
                    application.resume = request.FILES['resume']
                application.save()
                messages.success(request, f'✅ Your application for {job.title} has been submitted successfully!')
                return redirect('jobs:detail', slug=job.slug)
            except Exception as e:
                messages.error(request, f'❌ Error submitting application: {str(e)}')
                return redirect('jobs:detail', slug=job.slug)

    schema_json = json.dumps(job.get_structured_data())

    context = {
        'job': job,
        'related_jobs': related_jobs,
        'schema_json': schema_json,
    }
    return render(request, 'jobs/job_detail.html', context)


def legacy_job_detail(request, job_id):
    job = get_object_or_404(JobListing, id=job_id, is_active=True)
    return redirect('jobs:detail', slug=job.slug, permanent=True)


# ============================================================
# COMPANY LANDING PAGES
# ============================================================

def company_list(request):
    companies = JobListing.objects.filter(is_active=True).values('company_name').annotate(
        total=Count('id')
    ).order_by('-total')
    return render(request, 'jobs/company_list.html', {'companies': companies})


def company_detail(request, company_name):
    jobs = JobListing.objects.filter(
        company_name__iexact=company_name,
        is_active=True
    ).order_by('-created_at')
    return render(request, 'jobs/company_detail.html', {
        'jobs': jobs,
        'company': company_name,
        'total': jobs.count()
    })


# ============================================================
# CATEGORY LANDING PAGES
# ============================================================

def category_list(request):
    category_list = []
    for cat in JobCategory.objects.all():
        count = cat.jobs.filter(is_active=True).count()
        if count > 0:
            category_list.append((cat, count))
    category_list.sort(key=lambda x: x[1], reverse=True)
    return render(request, 'jobs/category_list.html', {'categories': category_list})


def category_detail(request, category_name):
    category = get_object_or_404(JobCategory, name__iexact=category_name)
    jobs = category.jobs.filter(is_active=True).order_by('-created_at')
    return render(request, 'jobs/category_detail.html', {
        'jobs': jobs,
        'category': category,
        'total': jobs.count()
    })


# ============================================================
# SITEMAP
# ============================================================

def generate_sitemap(request):
    jobs = JobListing.objects.filter(is_active=True).order_by('-created_at')

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    # Homepage
    xml += f'''<url>
    <loc>https://globalgigs-0096.onrender.com/</loc>
    <lastmod>{jobs.first().created_at.strftime("%Y-%m-%d") if jobs.exists() else "2026-01-01"}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
</url>\n'''

    # Job pages
    for job in jobs:
        xml += f'''<url>
    <loc>https://globalgigs-0096.onrender.com/jobs/{job.slug}/</loc>
    <lastmod>{job.created_at.strftime("%Y-%m-%d")}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
</url>\n'''

    # Company pages
    companies = JobListing.objects.filter(is_active=True).values('company_name').distinct()
    for company in companies:
        xml += f'''<url>
    <loc>https://globalgigs-0096.onrender.com/companies/{company['company_name']}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
</url>\n'''

    # Category pages
    categories = JobCategory.objects.filter(jobs__is_active=True).distinct()
    for cat in categories:
        xml += f'''<url>
    <loc>https://globalgigs-0096.onrender.com/categories/{cat.name}/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
</url>\n'''

    xml += '</urlset>'
    return HttpResponse(xml, content_type='application/xml')


# ============================================================
# SCRAPER & ENRICHMENT
# ============================================================

def secret_trigger_scraper(request):
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized access.", status=403)

    try:
        from .scraper import scale_database_to_thousands
        result = scale_database_to_thousands()
        return HttpResponse(f"🚀 {result}", status=200)
    except Exception as e:
        return HttpResponse(f"⚠️ Error running scraper: {str(e)}", status=500)


def enrich_jobs_endpoint(request):
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized", status=403)

    from .scraper import parse_job_sections
    jobs = JobListing.objects.all()
    count = 0
    errors = 0

    for job in jobs:
        if job.description:
            try:
                parsed, clean_desc = parse_job_sections(job.description)
                if parsed:
                    job.responsibilities = parsed.get('responsibilities', '')
                    job.requirements = parsed.get('requirements', '')
                    job.benefits = parsed.get('benefits', '')
                    job.company_description = parsed.get('about_company', '')
                    job.save()
                    count += 1
            except Exception as e:
                errors += 1

    return HttpResponse(f"✅ Enriched {count} jobs. Errors: {errors}")


# ============================================================
# DEBUG VIEWS
# ============================================================

def debug_jobs(request):
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
            <li>Slug: {first_job.slug}</li>
            <li>Created: {first_job.created_at}</li>
            <li>Has Responsibilities: {bool(first_job.responsibilities)}</li>
            <li>Has Requirements: {bool(first_job.requirements)}</li>
        </ul>
        """
    else:
        output += "<p>⚠️ No jobs found in JobListing table!</p>"

    return HttpResponse(output)


def category_debug(request):
    output = "<h1>Category Debug</h1>"

    categories = JobCategory.objects.all()
    output += f"<p>Total categories: {categories.count()}</p>"

    for cat in categories:
        job_count = cat.jobs.filter(is_active=True).count()
        output += f"<p><strong>{cat.icon} {cat.name}</strong>: {job_count} jobs</p>"
        if job_count > 0:
            output += "<ul>"
            for job in cat.jobs.filter(is_active=True)[:5]:
                output += f"<li>{job.title}</li>"
            if job_count > 5:
                output += f"<li>... and {job_count - 5} more</li>"
            output += "</ul>"

    return HttpResponse(output)


# ============================================================
# JOB POSTING & PAYMENT (PAYSTACK)
# ============================================================

def post_job_page(request):
    form = JobPostForm()
    return render(request, 'jobs/post_job.html', {'form': form})


def initiate_payment(request):
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
                import requests as req
                response = req.post(
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
    reference = request.GET.get('reference')

    if not reference:
        messages.error(request, "No payment reference found")
        return redirect('post_job')

    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}

    try:
        import requests as req
        response = req.get(
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
                    is_active=True,
                )
                job.save()  # generate slug
                del request.session['pending_job']
                messages.success(request, f'✅ Payment successful! Your job "{job.title}" is now live!')
                return redirect('jobs:detail', slug=job.slug)
        else:
            messages.error(request, f"Payment verification failed: {response_data.get('message')}")
    except Exception as e:
        messages.error(request, f"Error verifying payment: {str(e)}")

    return redirect('post_job')


# ============================================================
# UTILITY & MIGRATION ENDPOINTS
# ============================================================

def run_migrations(request):
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
    try:
        payload = json.loads(request.body)
        return HttpResponse(status=200)
    except Exception:
        return HttpResponse(status=400)


def create_categories_production(request):
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized", status=403)

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


def categorize_jobs_production(request):
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized", status=403)

    try:
        from .categorizer import auto_categorize_jobs
        count = auto_categorize_jobs()
        return HttpResponse(f"✅ Categorized {count} jobs on production")
    except ImportError:
        return HttpResponse("⚠️ Categorizer module not found", status=500)


def force_assign_categories(request):
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized", status=403)

    keywords = {
        'Technology': ['software', 'developer', 'engineer', 'programming', 'code', 'it', 'tech', 'cloud', 'data', 'ai', 'python', 'java', 'javascript', 'react', 'django', 'fullstack', 'backend', 'frontend', 'devops'],
        'Marketing': ['marketing', 'seo', 'social media', 'content', 'brand', 'digital marketing', 'ppc', 'advertising', 'growth', 'campaign'],
        'Sales': ['sales', 'account executive', 'business development', 'sales rep', 'sales manager', 'account manager', 'inside sales', 'bd'],
        'Healthcare': ['health', 'medical', 'doctor', 'nurse', 'clinical', 'patient', 'care', 'healthcare', 'pharmacy', 'wellness'],
        'Finance': ['finance', 'accountant', 'financial', 'banking', 'investment', 'tax', 'audit', 'controller', 'treasury'],
        'Education': ['teacher', 'education', 'training', 'instructor', 'curriculum', 'academic', 'tutor', 'professor'],
        'Administrative': ['administrative', 'assistant', 'office', 'coordinator', 'receptionist', 'admin', 'executive assistant'],
        'Customer Service': ['customer service', 'support', 'customer success', 'help desk', 'call center', 'client service'],
        'Design': ['designer', 'design', 'ui', 'ux', 'graphic', 'creative', 'visual', 'artist'],
        'Engineering': ['mechanical', 'electrical', 'civil', 'construction', 'architect', 'structural', 'project engineer'],
        'HR': ['human resources', 'hr', 'recruitment', 'recruiter', 'talent', 'people operations', 'hiring'],
        'Legal': ['legal', 'law', 'attorney', 'paralegal', 'compliance', 'regulatory', 'contract'],
        'Operations': ['operations', 'supply chain', 'logistics', 'procurement', 'inventory', 'warehouse'],
        'Data': ['data scientist', 'data analyst', 'data engineer', 'business intelligence', 'analytics'],
        'Product': ['product manager', 'product owner', 'product management', 'product development'],
        'Writing': ['writer', 'editor', 'content', 'copywriter', 'journalist', 'author'],
        'Consulting': ['consultant', 'consulting', 'advisory', 'strategy', 'management consulting'],
        'Real Estate': ['real estate', 'property', 'realtor', 'broker', 'property management'],
        'Media': ['media', 'video', 'content creator', 'influencer', 'broadcast', 'production'],
    }

    category_map = {cat.name.lower(): cat for cat in JobCategory.objects.all()}
    jobs = JobListing.objects.filter(category__isnull=True)
    total = jobs.count()
    categorized = 0

    for job in jobs:
        text = f"{job.title} {job.description}".lower()
        best_cat = None
        best_score = 0

        for cat_name, cat_keywords in keywords.items():
            score = sum(1 for kw in cat_keywords if kw in text)
            if score > best_score:
                best_score = score
                best_cat = category_map.get(cat_name.lower())

        if best_cat and best_score >= 2:
            job.category = best_cat
            job.save()
            categorized += 1

    return HttpResponse(f"✅ Categorized {categorized} out of {total} jobs")


def simple_categorize(request):
    key = request.GET.get('key')
    if key != 'candy2026':
        return HttpResponse("Unauthorized", status=403)
    return force_assign_categories(request)


# ============================================================
# MEDIA FILE SERVING
# ============================================================

def serve_media_file(request, file_path):
    file_path = unquote(file_path)
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)

    if not full_path.startswith(os.path.abspath(settings.MEDIA_ROOT)):
        raise Http404("Access denied")

    if os.path.exists(full_path) and os.path.isfile(full_path):
        content_type = 'application/octet-stream'
        if full_path.endswith('.pdf'):
            content_type = 'application/pdf'
        elif full_path.endswith('.doc'):
            content_type = 'application/msword'
        elif full_path.endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif full_path.endswith('.jpg') or full_path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif full_path.endswith('.png'):
            content_type = 'image/png'

        try:
            response = FileResponse(open(full_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(full_path)}"'
            return response
        except Exception as e:
            raise Http404(f"Error opening file: {str(e)}")

    raise Http404("File not found")