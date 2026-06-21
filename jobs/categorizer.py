"""
Auto-categorize jobs based on title and description
"""

import re
from .models import JobListing, JobCategory

def auto_categorize_jobs():
    """Categorize all uncategorized jobs"""
    
    categories = JobCategory.objects.all()
    category_map = {cat.name.lower(): cat for cat in categories}
    
    keywords = {
        'Technology': ['software', 'developer', 'engineer', 'programming', 'code', 'it', 'tech', 'cloud', 'data', 'ai', 'machine learning', 'python', 'java', 'javascript', 'fullstack', 'backend', 'frontend', 'devops', 'react', 'angular', 'node', 'django'],
        'Marketing': ['marketing', 'seo', 'social media', 'content', 'brand', 'digital marketing', 'ppc', 'advertising', 'marketing manager', 'growth', 'campaign'],
        'Sales': ['sales', 'account executive', 'business development', 'client', 'bd', 'sales rep', 'sales manager', 'account manager', 'inside sales'],
        'Healthcare': ['health', 'medical', 'doctor', 'nurse', 'clinical', 'patient', 'care', 'healthcare', 'pharmacy', 'clinical research', 'wellness'],
        'Finance': ['finance', 'accountant', 'financial', 'banking', 'investment', 'tax', 'audit', 'controller', 'analyst', 'treasury'],
        'Education': ['teacher', 'education', 'training', 'instructor', 'curriculum', 'academic', 'tutor', 'professor', 'lecturer'],
        'Administrative': ['administrative', 'assistant', 'office', 'coordinator', 'receptionist', 'secretary', 'admin', 'executive assistant'],
        'Customer Service': ['customer service', 'support', 'customer success', 'help desk', 'call center', 'client service'],
        'Design': ['designer', 'design', 'ui', 'ux', 'graphic', 'creative', 'visual', 'artist', 'product design'],
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
    
    # Get jobs without categories
    uncategorized = JobListing.objects.filter(category__isnull=True)
    total_jobs = uncategorized.count()
    categorized_count = 0
    
    print(f"📊 Found {total_jobs} uncategorized jobs")
    
    for job in uncategorized:
        text = f"{job.title} {job.description}".lower()
        
        best_category = None
        best_score = 0
        
        for cat_name, cat_keywords in keywords.items():
            score = sum(1 for keyword in cat_keywords if keyword in text)
            if score > best_score:
                best_score = score
                best_category = category_map.get(cat_name.lower())
        
        if best_category and best_score >= 2:
            job.category = best_category
            job.save()
            categorized_count += 1
            print(f"✅ Categorized: {job.title[:50]} → {best_category.name}")
    
    print(f"\n📊 Categorized {categorized_count} out of {total_jobs} jobs")
    return categorized_count
