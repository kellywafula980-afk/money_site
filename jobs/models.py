from django.db import models
from django.urls import reverse


class ScriptBatch(models.Model):
    TONE_CHOICES = [
        ('viral', 'Viral Hook/Aggressive'),
        ('story', 'Deep Storytelling'),
        ('brainrot', 'Gen-Z / Brainrot'),
        ('educational', 'Informative/Educational'),
    ]
    topic = models.CharField(max_length=255)
    tone = models.CharField(max_length=50, choices=TONE_CHOICES, default='viral')
    raw_response = models.TextField()
    audio_url = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch for {self.topic} ({self.get_tone_display()})"


class EmailCampaign(models.Model):
    user_network = models.CharField(max_length=100, default="Global")
    service_offered = models.CharField(max_length=255)
    target_industry = models.CharField(max_length=255)
    generated_pitch = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_offered} targeting {self.target_industry}"


class JobCategory(models.Model):
    """Job categories for better organization"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Job Categories"
        ordering = ['name']


class JobListing(models.Model):
    # ============================================================
    # BASE FIELDS
    # ============================================================
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        JobCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='jobs'
    )
    location = models.CharField(max_length=100, default="Remote")
    apply_url = models.URLField(max_length=500, unique=True)
    
    # ============================================================
    # 🆕 RICH CONTENT FIELDS (For Better SEO & User Experience)
    # ============================================================
    responsibilities = models.TextField(
        blank=True, 
        null=True,
        help_text="Extracted key responsibilities for this role"
    )
    requirements = models.TextField(
        blank=True, 
        null=True,
        help_text="Extracted requirements and qualifications"
    )
    benefits = models.TextField(
        blank=True, 
        null=True,
        help_text="Extracted benefits and perks"
    )
    company_description = models.TextField(
        blank=True, 
        null=True,
        help_text="Description of the company hiring"
    )
    employment_type = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Full-time, Part-time, Contract, etc."
    )
    experience_level = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Entry level, Mid-level, Senior, etc."
    )
    
    # ============================================================
    # 💰 MONETIZATION FIELDS
    # ============================================================
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    salary_range = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        default="$40,000 - $80,000"
    )
    
    # ============================================================
    # 🚀 ON-SITE APPLICATION FIELDS
    # ============================================================
    accept_onsite_applications = models.BooleanField(default=True)
    application_email = models.EmailField(blank=True, null=True)
    application_instructions = models.TextField(blank=True, null=True)
    
    # ============================================================
    # 📅 TIMESTAMPS
    # ============================================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ============================================================
    # 🎯 METHODS
    # ============================================================
    def __str__(self):
        return f"{self.title} at {self.company_name}"

    def get_absolute_url(self):
        return f'/jobs/{self.id}/'
    
    def get_full_description(self):
        """Return full description including all structured sections"""
        parts = []
        if self.description:
            parts.append(self.description)
        if self.responsibilities:
            parts.append(f"\n\n**Key Responsibilities:**\n{self.responsibilities}")
        if self.requirements:
            parts.append(f"\n\n**Requirements:**\n{self.requirements}")
        if self.benefits:
            parts.append(f"\n\n**Benefits:**\n{self.benefits}")
        if self.company_description:
            parts.append(f"\n\n**About the Company:**\n{self.company_description}")
        return "\n".join(parts)
    
    def get_structured_data(self):
        """Generate structured data for JSON-LD schema"""
        return {
            'title': self.title,
            'company': self.company_name,
            'location': self.location,
            'salary': self.salary_range,
            'date_posted': self.created_at.strftime('%Y-%m-%d'),
            'description': self.get_full_description()[:4000],
            'employment_type': self.employment_type or 'FULL_TIME',
            'hiring_organization': {
                '@type': 'Organization',
                'name': self.company_name,
            },
            'job_location': {
                '@type': 'Place',
                'address': {
                    '@type': 'PostalAddress',
                    'addressLocality': self.location or 'Remote',
                    'addressCountry': 'Worldwide',
                }
            },
        }
    
    class Meta:
        verbose_name_plural = "Job Listings"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['company_name']),
            models.Index(fields=['category']),
            models.Index(fields=['location']),
            models.Index(fields=['created_at']),
        ]


class JobApplication(models.Model):
    # ============================================================
    # RELATIONSHIPS
    # ============================================================
    job = models.ForeignKey(
        JobListing, 
        on_delete=models.CASCADE, 
        related_name='applications'
    )
    
    # ============================================================
    # APPLICANT INFORMATION
    # ============================================================
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    cover_letter = models.TextField()
    resume = models.FileField(
        upload_to='resumes/%Y/%m/%d/', 
        blank=True, 
        null=True
    )
    portfolio_url = models.URLField(blank=True, null=True)
    
    # ============================================================
    # STATUS & TIMESTAMPS
    # ============================================================
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about this applicant")
    
    # ============================================================
    # 🎯 METHODS
    # ============================================================
    def __str__(self):
        return f"{self.full_name} - {self.job.title}"
    
    def mark_as_reviewed(self):
        from django.utils import timezone
        self.is_reviewed = True
        self.reviewed_at = timezone.now()
        self.save()
    
    class Meta:
        verbose_name_plural = "Job Applications"
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['job', 'submitted_at']),
            models.Index(fields=['email']),
            models.Index(fields=['is_reviewed']),
        ]