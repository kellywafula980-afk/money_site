from django import forms
from .models import JobApplication, JobListing  # Add JobListing to the import

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['full_name', 'email', 'phone', 'cover_letter', 'resume', 'portfolio_url']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Tell us why you\'re a great fit...'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+1234567890'}),
            'portfolio_url': forms.URLInput(attrs={'placeholder': 'https://github.com/yourusername'}),
        }

# ADD THIS NEW FORM to your existing forms.py
class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = ['title', 'company_name', 'description', 'location', 'salary_range']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white', 'placeholder': 'e.g., Senior Python Developer'}),
            'company_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white', 'placeholder': 'Your Company Name'}),
            'description': forms.Textarea(attrs={'rows': 10, 'class': 'w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white', 'placeholder': 'Job description, requirements, benefits...'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white', 'placeholder': 'Remote, New York, London...'}),
            'salary_range': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white', 'placeholder': '$50,000 - $80,000'}),
        }