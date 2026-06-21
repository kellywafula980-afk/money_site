from django.db import models

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


class JobListing(models.Model):
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey('JobCategory', on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    location = models.CharField(max_length=100, default="Remote")
    apply_url = models.URLField(max_length=500, unique=True)
    
    # 💰 MONETIZATION FIELDS
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    salary_range = models.CharField(max_length=100, blank=True, null=True, default="$40,000 - $80,000")
    
    # 🚀 NEW FIELDS FOR ON-SITE APPLICATIONS
    accept_onsite_applications = models.BooleanField(default=True)
    application_email = models.EmailField(blank=True, null=True)
    application_instructions = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company_name}"

    def get_absolute_url(self):
        return f'/jobs/{self.id}/'


class JobApplication(models.Model):
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.full_name} - {self.job.title}"
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
