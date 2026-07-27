from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from jobs.models import JobListing, JobCategory
from .models import UserProfile

# ============================================================
# JOB POST FORM (existing)
# ============================================================

class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = [
            'title', 'company_name', 'location', 'description',
            'responsibilities', 'requirements', 'benefits',
            'company_description', 'salary_range', 'apply_url',
            'employment_type', 'experience_level', 'is_featured',
            'is_premium', 'accept_onsite_applications', 'application_email',
            'application_instructions'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control'}),
            'apply_url': forms.URLInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_premium': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accept_onsite_applications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'application_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'application_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# ============================================================
# USER PROFILE FORM (existing)
# ============================================================

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['company_name', 'company_website', 'company_logo', 'phone_number', 'bio']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_website': forms.URLInput(attrs={'class': 'form-control'}),
            'company_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

# ============================================================
# 🆕 CUSTOM SIGN-UP FORM (add this)
# ============================================================

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="We'll use this for billing and account notifications.",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-zinc-800/50 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition',
            'placeholder': 'your@email.com'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: add Tailwind classes to the default fields for consistency
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 bg-zinc-800/50 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 bg-zinc-800/50 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition',
            'placeholder': 'Choose a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 bg-zinc-800/50 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500 transition',
            'placeholder': 'Confirm your password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user