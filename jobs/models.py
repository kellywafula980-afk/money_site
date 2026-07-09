import re
import json
from datetime import timedelta
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify


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
    
    def get_absolute_url(self):
        return f"/categories/{self.slug}/"
    
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
    # 🆕 SEO-FRIENDLY SLUG
    # ============================================================
    slug = models.SlugField(
        max_length=200, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="SEO-friendly URL slug generated from the title"
    )
    
    # ============================================================
    # 👤 USER RELATIONSHIP
    # ============================================================
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_jobs'
    )
    is_active = models.BooleanField(default=True)
    
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
    # 📊 ANALYTICS
    # ============================================================
    views_count = models.IntegerField(default=0, help_text="Number of times this job has been viewed")

    # ============================================================
    # 🎯 METHODS
    # ============================================================
    def __str__(self):
        return f"{self.title} at {self.company_name}"

    # ---------- SLUG GENERATION ----------
    def save(self, *args, **kwargs):
        """Override save to generate slug from title if not set."""
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            # Check if the slug already exists
            if JobListing.objects.filter(slug=base_slug).exists():
                # If this is a new object (no ID yet), we need to save first to get ID
                if not self.id:
                    super().save(*args, **kwargs)
                    self.slug = f"{base_slug}-{self.id}"
                else:
                    self.slug = f"{base_slug}-{self.id}"
            else:
                self.slug = base_slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the SEO-friendly URL for this job."""
        return f"/jobs/{self.slug}/"

    # ---------- SALARY PARSING FOR STRUCTURED DATA ----------
    @property
    def salary_min(self):
        """Extract minimum salary from salary_range string."""
        if not self.salary_range:
            return None
        numbers = re.findall(r'\d{2,3}[,.]?\d{3}', str(self.salary_range))
        if numbers:
            return int(numbers[0].replace(',', '').replace('.', ''))
        return None

    @property
    def salary_max(self):
        """Extract maximum salary from salary_range string."""
        if not self.salary_range:
            return None
        numbers = re.findall(r'\d{2,3}[,.]?\d{3}', str(self.salary_range))
        if len(numbers) >= 2:
            return int(numbers[1].replace(',', '').replace('.', ''))
        return self.salary_min

    @property
    def valid_through(self):
        """Jobs expire 30 days after posting (for Google for Jobs)."""
        base_date = self.created_at or timezone.now()
        return base_date + timedelta(days=30)

    @property
    def is_remote(self):
        """Return True if the job is remote based on location."""
        if not self.location:
            return True
        return 'remote' in self.location.lower()

    # ---------- FULL DESCRIPTION ----------
    def get_full_description(self):
        """Return full description including all structured sections."""
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

    # ---------- INCREMENT VIEWS ----------
    def increment_views(self):
        """Increment the view count by 1."""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    # ---------- STRUCTURED DATA (JSON-LD) ----------
    def get_structured_data(self):
        """Generate complete Schema.org JSON-LD for Google for Jobs."""
        # Determine employment type
        employment_type = self.employment_type or 'FULL_TIME'
        # Convert to schema format
        employment_type_map = {
            'full-time': 'FULL_TIME',
            'full time': 'FULL_TIME',
            'part-time': 'PART_TIME',
            'part time': 'PART_TIME',
            'contract': 'CONTRACTOR',
            'freelance': 'FREELANCE',
            'internship': 'INTERN',
            'temporary': 'TEMPORARY',
            'remote': 'FULL_TIME',  # Default for remote
        }
        employment_type_schema = employment_type_map.get(
            employment_type.lower(), 
            'FULL_TIME'
        )

        # Build the salary object
        salary_obj = None
        if self.salary_min or self.salary_max:
            salary_obj = {
                "@type": "MonetaryAmount",
                "currency": "USD",
                "value": {
                    "@type": "QuantitativeValue",
                    "unitText": "YEAR"
                }
            }
            if self.salary_min and self.salary_max:
                salary_obj["value"]["minValue"] = self.salary_min
                salary_obj["value"]["maxValue"] = self.salary_max
            elif self.salary_min:
                salary_obj["value"]["value"] = self.salary_min
            elif self.salary_max:
                salary_obj["value"]["value"] = self.salary_max

        # Build the full schema
        schema = {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": self.title,
            "description": self.get_full_description()[:4000] if self.get_full_description() else "",
            "datePosted": self.created_at.isoformat() if self.created_at else "",
            "validThrough": self.valid_through.isoformat(),
            "employmentType": employment_type_schema,
            "hiringOrganization": {
                "@type": "Organization",
                "name": self.company_name,
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": self.location if self.location else "Remote",
                    "addressCountry": "Worldwide",
                }
            },
            "jobLocationType": "TELECOMMUTE" if self.is_remote else "PHYSICAL",
        }

        # Add salary if available
        if salary_obj:
            schema["baseSalary"] = salary_obj

        # Add apply URL
        if self.apply_url:
            schema["directApply"] = True
            # Use apply_url as the application link

        # Add experience level if available
        if self.experience_level:
            schema["experienceRequirements"] = {
                "@type": "OccupationalExperienceRequirements",
                "monthsOfExperience": self._parse_experience_months()
            }

        return schema

    def _parse_experience_months(self):
        """Parse experience level into months for structured data."""
        if not self.experience_level:
            return None
        level = self.experience_level.lower()
        if 'entry' in level or 'junior' in level:
            return 0
        elif 'mid' in level or 'intermediate' in level:
            return 36
        elif 'senior' in level or 'lead' in level:
            return 60
        elif 'manager' in level or 'director' in level:
            return 96
        return None

    # ---------- VIEW COUNT ----------
    def increment_views(self):
        """Increment the view count by 1."""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    class Meta:
        verbose_name_plural = "Job Listings"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['company_name']),
            models.Index(fields=['category']),
            models.Index(fields=['location']),
            models.Index(fields=['created_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
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