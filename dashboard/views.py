from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models import Count, Q
from django.urls import reverse  # ✅ ADDED for reverse redirection
from jobs.models import JobListing, JobApplication, JobCategory
from .models import UserProfile, SavedJob, Subscription  # ✅ ADDED Subscription
from .forms import JobPostForm, UserProfileForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import traceback
import sys

@login_required
def dashboard_home(request):
    """Main dashboard view"""
    try:
        user = request.user
        
        # Get user's jobs
        user_jobs = JobListing.objects.filter(posted_by=user).order_by('-created_at')
        total_jobs = user_jobs.count()
        active_jobs = user_jobs.filter(is_active=True).count()
        featured_jobs = user_jobs.filter(is_featured=True).count()
        
        # Get applications for user's jobs
        applications = JobApplication.objects.filter(job__in=user_jobs).count()
        
        # Get saved jobs
        saved_jobs = SavedJob.objects.filter(user=user).count()
        
        # Get recent jobs (last 5)
        recent_jobs = user_jobs[:5]
        
        context = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'featured_jobs': featured_jobs,
            'applications': applications,
            'saved_jobs': saved_jobs,
            'recent_jobs': recent_jobs,
            'user': user,
        }
        
        return render(request, 'dashboard/dashboard.html', context)
    except Exception as e:
        print(f"ERROR in dashboard_home: {str(e)}")
        traceback.print_exc()
        return render(request, 'dashboard/error.html', {'error': str(e)})

@login_required
def post_job(request):
    """Redirect to the main job posting page with payment"""
    return redirect('post_job')

@login_required
def edit_job(request, job_id):
    """Edit an existing job"""
    job = get_object_or_404(JobListing, id=job_id, posted_by=request.user)
    categories = JobCategory.objects.all()
    
    if request.method == 'POST':
        form = JobPostForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            job.updated_at = timezone.now()
            
            category_id = request.POST.get('category')
            if category_id and category_id.isdigit():
                try:
                    job.category = JobCategory.objects.get(id=category_id)
                except JobCategory.DoesNotExist:
                    pass
            
            job.save()
            messages.success(request, f'✅ Job "{job.title}" updated successfully!')
            return redirect('dashboard:my_jobs')
    else:
        form = JobPostForm(instance=job)
    
    return render(request, 'dashboard/edit_job.html', {
        'form': form,
        'job': job,
        'categories': categories,
        'user': request.user,
    })

@login_required
def delete_job(request, job_id):
    """Delete a job"""
    job = get_object_or_404(JobListing, id=job_id, posted_by=request.user)
    
    if request.method == 'POST':
        job_title = job.title
        job.delete()
        messages.success(request, f'🗑️ Job "{job_title}" deleted successfully!')
        return redirect('dashboard:my_jobs')
    
    return render(request, 'dashboard/delete_job.html', {'job': job, 'user': request.user})

@login_required
def my_jobs(request):
    """List all jobs posted by the user"""
    user_jobs = JobListing.objects.filter(posted_by=request.user).order_by('-created_at')
    
    # Filters
    status = request.GET.get('status')
    if status == 'active':
        user_jobs = user_jobs.filter(is_active=True)
    elif status == 'inactive':
        user_jobs = user_jobs.filter(is_active=False)
    elif status == 'featured':
        user_jobs = user_jobs.filter(is_featured=True)
    elif status == 'premium':
        user_jobs = user_jobs.filter(is_premium=True)
    
    context = {
        'jobs': user_jobs,
        'status': status,
        'total_count': user_jobs.count(),
        'user': request.user,
    }
    return render(request, 'dashboard/my_jobs.html', context)

@login_required
def saved_jobs(request):
    """List saved jobs"""
    saved = SavedJob.objects.filter(user=request.user).select_related('job').order_by('-saved_at')
    context = {
        'saved': saved,
        'user': request.user,
    }
    return render(request, 'dashboard/saved_jobs.html', context)

@login_required
@require_POST
def save_job(request, job_id):
    """Save a job to favorites"""
    job = get_object_or_404(JobListing, id=job_id)
    
    saved = SavedJob.objects.filter(user=request.user, job=job).first()
    
    if saved:
        saved.delete()
        return JsonResponse({
            'status': 'unsaved', 
            'message': 'Job removed from saved!',
            'saved': False
        })
    else:
        SavedJob.objects.create(user=request.user, job=job)
        return JsonResponse({
            'status': 'saved', 
            'message': 'Job saved successfully!',
            'saved': True
        })
@login_required
def profile(request):
    """User profile management"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # ✅ Save email
            email = request.POST.get('email')
            if email:
                request.user.email = email
                request.user.save()
                messages.success(request, f'✅ Email updated to {email}')
            else:
                messages.warning(request, 'Email cannot be empty.')
            
            form.save()
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('dashboard:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=profile)
    
    user_jobs = JobListing.objects.filter(posted_by=request.user)
    total_jobs = user_jobs.count()
    active_jobs = user_jobs.filter(is_active=True).count()
    
    context = {
        'form': form,
        'profile': profile,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'user': request.user,
    }
    return render(request, 'dashboard/profile.html', context)

@login_required
def applications_view(request):
    """View applications for user's jobs"""
    user_jobs = JobListing.objects.filter(posted_by=request.user)
    applications = JobApplication.objects.filter(job__in=user_jobs).order_by('-submitted_at')
    
    status = request.GET.get('status')
    if status == 'reviewed':
        applications = applications.filter(is_reviewed=True)
    elif status == 'pending':
        applications = applications.filter(is_reviewed=False)
    
    context = {
        'applications': applications,
        'total': applications.count(),
        'status': status,
        'user': request.user,
    }
    return render(request, 'dashboard/applications.html', context)

@login_required
@require_POST
def toggle_job_status(request, job_id):
    """Toggle job active/inactive status"""
    job = get_object_or_404(JobListing, id=job_id, posted_by=request.user)
    job.is_active = not job.is_active
    job.updated_at = timezone.now()
    job.save()
    
    status = 'activated' if job.is_active else 'deactivated'
    messages.success(request, f'✅ Job "{job.title}" {status}!')
    return redirect('dashboard:my_jobs')

@login_required
def dashboard_stats_api(request):
    """Return dashboard statistics as JSON"""
    user = request.user
    user_jobs = JobListing.objects.filter(posted_by=user)
    
    data = {
        'total_jobs': user_jobs.count(),
        'active_jobs': user_jobs.filter(is_active=True).count(),
        'featured_jobs': user_jobs.filter(is_featured=True).count(),
        'premium_jobs': user_jobs.filter(is_premium=True).count(),
        'applications': JobApplication.objects.filter(job__in=user_jobs).count(),
        'saved_jobs': SavedJob.objects.filter(user=user).count(),
        'recent_jobs': [
            {
                'id': job.id,
                'title': job.title,
                'company': job.company_name,
                'created_at': job.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_active': job.is_active,
                'is_featured': job.is_featured,
            }
            for job in user_jobs[:5]
        ]
    }
    return JsonResponse(data)

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '🎉 Account created successfully! Welcome to GlobalGigs!')
            return redirect('dashboard:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def review_application(request, application_id):
    """Mark an application as reviewed"""
    application = get_object_or_404(JobApplication, id=application_id, job__posted_by=request.user)
    application.is_reviewed = True
    application.reviewed_at = timezone.now()
    application.save()
    messages.success(request, f'✅ Application from {application.full_name} marked as reviewed!')
    return redirect('dashboard:applications')


# ============================================================
# 🆕 PRICING & SUBSCRIPTION VIEWS (ADDED)
# ============================================================

def pricing_page(request):
    """
    Display pricing tiers and subscription options.
    """
    plans = [
        {
            'id': 'starter',
            'name': 'Starter',
            'price_kes': 3700,
            'price_usd': 29,
            'posts': 5,
            'features': [
                '5 job posts per month',
                'Standard visibility',
                '30-day job expiry',
                'Basic support',
            ],
            'popular': False,
            'plan_code': 'PLN_starter_abc123',  # 🔁 REPLACE with actual code from Paystack
        },
        {
            'id': 'pro',
            'name': 'Professional',
            'price_kes': 10200,
            'price_usd': 79,
            'posts': 25,
            'features': [
                '25 job posts per month',
                'Featured badge on listings',
                'Highlighted in search results',
                'Social media promotion',
                'Priority support',
            ],
            'popular': True,
            'plan_code': 'PLN_pro_xyz789',  # 🔁 REPLACE with actual code from Paystack
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'price_kes': 32000,
            'price_usd': 249,
            'posts': 'Unlimited',
            'features': [
                'Unlimited job posts',
                'Premium placement on homepage',
                'Dedicated company profile page',
                'Resume database access',
                'Advanced analytics',
                '24/7 priority support',
            ],
            'popular': False,
            'plan_code': 'PLN_enterprise_def456',  # 🔁 REPLACE with actual code from Paystack
        },
    ]
    
    current_subscription = None
    if request.user.is_authenticated:
        try:
            current_subscription = request.user.subscription
        except Subscription.DoesNotExist:
            pass
    
    context = {
        'plans': plans,
        'current_subscription': current_subscription,
    }
    return render(request, 'dashboard/pricing.html', context)


@login_required
def subscribe_plan(request, plan_id):
    """
    Store selected plan in session and redirect to payment initiation.
    """
    valid_plans = ['starter', 'pro', 'enterprise']
    if plan_id not in valid_plans:
        messages.error(request, "Invalid plan selected.")
        return redirect('pricing')
    
    # Store the selected plan in session
    request.session['selected_plan'] = plan_id
    return redirect('jobs:initiate_subscription')
