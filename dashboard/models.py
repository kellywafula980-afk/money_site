from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from jobs.models import JobListing


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_website = models.URLField(blank=True, null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_employer = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_posted_jobs_count(self):
        return JobListing.objects.filter(posted_by=self.user).count()
    
    def get_active_jobs_count(self):
        return JobListing.objects.filter(posted_by=self.user, is_active=True).count()
    
    def get_featured_jobs_count(self):
        return JobListing.objects.filter(posted_by=self.user, is_featured=True).count()


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


# ============================================================
# 🆕 SUBSCRIPTION MODEL (ADD THIS)
# ============================================================

class Subscription(models.Model):
    """
    User subscription plans for job posting limits.
    """
    PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='subscription'
    )
    
    # ============================================================
    # PLAN & BILLING
    # ============================================================
    plan_type = models.CharField(
        max_length=20, 
        choices=PLAN_CHOICES, 
        default='starter'
    )
    paystack_subscription_code = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Paystack subscription code (e.g., SUB_xxxxx)"
    )
    paystack_customer_code = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Paystack customer code (e.g., CUS_xxxxx)"
    )
    
    # ============================================================
    # USAGE LIMITS
    # ============================================================
    job_posts_remaining = models.IntegerField(
        default=5,
        help_text="Number of job posts remaining this month. -1 = unlimited (Enterprise)"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Whether the subscription is currently active"
    )
    
    # ============================================================
    # BILLING DATES
    # ============================================================
    start_date = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this subscription expires (if not renewed)"
    )
    next_billing_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the next payment is due"
    )
    
    # ============================================================
    # TIMESTAMPS
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ============================================================
    # 🎯 METHODS
    # ============================================================
    def __str__(self):
        status = 'Active' if self.is_active else 'Inactive'
        return f"{self.user.email} - {self.get_plan_type_display()} ({status})"
    
    def can_post_job(self):
        """Check if the user has remaining job posts."""
        if not self.is_active:
            return False
        if self.plan_type == 'enterprise':
            return True  # Unlimited
        return self.job_posts_remaining > 0
    
    def use_job_post(self):
        """
        Decrement remaining job posts.
        Returns True if successful, False if limit reached.
        """
        if self.plan_type == 'enterprise':
            return True  # Unlimited, no decrement needed
        if self.job_posts_remaining > 0:
            self.job_posts_remaining -= 1
            self.save(update_fields=['job_posts_remaining'])
            return True
        return False
    
    def get_plan_limit(self):
        """Get maximum job posts per month for this plan."""
        limits = {
            'starter': 5,
            'pro': 25,
            'enterprise': -1  # -1 = unlimited
        }
        return limits.get(self.plan_type, 0)
    
    def get_plan_price_kes(self):
        """Get monthly price in KES (as configured in Paystack)."""
        prices = {
            'starter': 3700,
            'pro': 10200,
            'enterprise': 32000
        }
        return prices.get(self.plan_type, 0)
    
    def get_plan_price_usd(self):
        """Get monthly price in USD (approximate)."""
        prices = {
            'starter': 29,
            'pro': 79,
            'enterprise': 249
        }
        return prices.get(self.plan_type, 0)
    
    def reset_monthly_posts(self):
        """Reset job posts for the new month."""
        if self.plan_type != 'enterprise':
            self.job_posts_remaining = self.get_plan_limit()
            self.save(update_fields=['job_posts_remaining'])
    
    def activate(self, plan_type=None):
        """Activate the subscription."""
        if plan_type:
            self.plan_type = plan_type
        self.is_active = True
        self.start_date = timezone.now()
        self.expires_at = timezone.now() + timezone.timedelta(days=30)
        self.next_billing_date = timezone.now() + timezone.timedelta(days=30)
        self.job_posts_remaining = self.get_plan_limit()
        self.save()
    
    def deactivate(self):
        """Deactivate the subscription."""
        self.is_active = False
        self.save()
    
    class Meta:
        verbose_name_plural = "Subscriptions"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['paystack_subscription_code']),
            models.Index(fields=['plan_type']),
        ]