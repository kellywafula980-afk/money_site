# jobs/views.py
from django.shortcuts import render, redirect
from .models import JobListing

def home(request):
    jobs = JobListing.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')
    return render(request, 'jobs/home.html', {'jobs': jobs})

def post_job(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        company_name = request.POST.get('company_name')
        company_website = request.POST.get('company_website')
        apply_url = request.POST.get('apply_url')
        description = request.POST.get('description')
        upgrade_featured = request.POST.get('upgrade_featured') # Will be 'on' if checked

        # Save to database
        job = JobListing.objects.create(
            title=title,
            company_name=company_name,
            company_website=company_website,
            apply_url=apply_url,
            description=description,
            is_approved=False, # We approve manually after verification/payment
            is_featured=True if upgrade_featured == 'on' else False
        )

        if upgrade_featured == 'on':
            # Redirect them to our zero-cost checkout layout
            return render(request, 'jobs/success.html', {'job': job, 'payment_required': True})
        
        return render(request, 'jobs/success.html', {'job': job, 'payment_required': False})

    return render(request, 'jobs/post_job.html')

from django.http import HttpResponse
from django.contrib.auth.models import User

def create_admin_backdoor(request):
    # Check if your admin account already exists to prevent duplication errors
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="root" # <-- Change this password to whatever you want!
        )
        return HttpResponse("🚀 Success! Superuser created. Username: admin")
    else:
        return HttpResponse("⚠️ Admin account already exists in your Postgres cloud database.")