import requests
import html
import time
import re
from datetime import timedelta
from django.utils import timezone
from .models import JobListing, JobCategory

def clean_text(text):
    if not text: 
        return ""
    text = html.unescape(text)
    return text.strip()

def is_relevant_job(title, description, company_name=""):
    """Filter out spam, irrelevant, or low-quality jobs"""
    if not description or len(description) < 100:
        return False
    
    text = f"{title} {description} {company_name}".lower()
    banned_keywords = [
        'amazon billing', 'amazon payment', 'amazon card', 'update payment',
        'crypto', 'bitcoin', 'ethereum', 'dogecoin', 'wallet',
        'earn money fast', 'make money online', 'passive income',
        'forex trading', 'binary options', 'get rich quick',
        'paypal billing', 'free money', 'instant cash',
        'survey', 'referral', 'affiliate marketing',
        'work for free', 'unpaid internship', 'volunteer'
    ]
    
    for keyword in banned_keywords:
        if keyword in text:
            return False
    
    words = text.split()
    if len(words) > 0:
        word_count = {}
        for word in words:
            if len(word) > 3:
                word_count[word] = word_count.get(word, 0) + 1
        
        threshold = len(words) * 0.2
        for count in word_count.values():
            if count > threshold and count > 10:
                return False
    
    return True

def extract_salary(text):
    """Extract salary from text, return None if not found"""
    if not text:
        return None
    
    patterns = [
        r'\$(\d{2,3}[,.]?\d{3})\s*[-–]\s*\$(\d{2,3}[,.]?\d{3})',
        r'\$(\d{2,3}[,.]?\d{3})\s*[-–]\s*(\d{2,3}[,.]?\d{3})',
        r'(\d{2,3}[,.]?\d{3})\s*[-–]\s*(\d{2,3}[,.]?\d{3})',
        r'\$(\d{2,3}[,.]?\d{3})\+',
        r'\$(\d{2,3}[,.]?\d{3})',
        r'(\d{2,3}[,.]?\d{3})\s*(?:per year|annually|yearly)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                return f"${match.group(1)} - ${match.group(2)}"
            else:
                return f"${match.group(1)}"
    
    return None

def assign_category_to_job(job):
    """Automatically assign a category to a job based on keywords"""
    if not job:
        return None
    
    categories = JobCategory.objects.all()
    if not categories.exists():
        return None
    
    text = f"{job.title} {job.description}".lower()
    
    category_keywords = {
        'Technology': ['software', 'developer', 'engineer', 'programming', 'code', 'it', 'tech', 'cloud', 'data', 'ai', 'python', 'java', 'javascript', 'react', 'django', 'fullstack', 'backend', 'frontend', 'devops', 'cyber', 'security', 'network'],
        'Marketing': ['marketing', 'seo', 'social media', 'content', 'brand', 'digital', 'ppc', 'advertising', 'growth', 'campaign'],
        'Sales': ['sales', 'account executive', 'business development', 'sales rep', 'sales manager', 'account manager'],
        'Healthcare': ['health', 'medical', 'doctor', 'nurse', 'clinical', 'patient', 'care', 'healthcare', 'pharmacy', 'wellness'],
        'Finance': ['finance', 'accountant', 'financial', 'banking', 'investment', 'tax', 'audit', 'controller', 'treasury'],
        'Education': ['teacher', 'education', 'training', 'instructor', 'curriculum', 'academic', 'tutor'],
        'Administrative': ['administrative', 'assistant', 'office', 'coordinator', 'receptionist', 'admin'],
        'Customer Service': ['customer service', 'support', 'customer success', 'help desk', 'call center'],
        'Design': ['designer', 'design', 'ui', 'ux', 'graphic', 'creative', 'visual', 'artist'],
        'Engineering': ['mechanical', 'electrical', 'civil', 'construction', 'architect', 'structural'],
        'HR': ['human resources', 'hr', 'recruitment', 'recruiter', 'talent', 'people operations'],
        'Legal': ['legal', 'law', 'attorney', 'paralegal', 'compliance', 'regulatory'],
        'Operations': ['operations', 'supply chain', 'logistics', 'procurement', 'inventory', 'warehouse'],
        'Data': ['data scientist', 'data analyst', 'data engineer', 'business intelligence', 'analytics'],
        'Product': ['product manager', 'product owner', 'product management', 'product development'],
        'Writing': ['writer', 'editor', 'content', 'copywriter', 'journalist', 'author'],
        'Consulting': ['consultant', 'consulting', 'advisory', 'strategy'],
        'Real Estate': ['real estate', 'property', 'realtor', 'broker'],
        'Media': ['media', 'video', 'content creator', 'influencer', 'broadcast', 'production'],
    }
    
    best_category = None
    best_score = 0
    
    for cat_name, keywords in category_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_category = categories.filter(name=cat_name).first()
    
    if best_category and best_score >= 2:
        job.category = best_category
        job.save()
        return best_category
    
    return None

def parse_job_sections(text):
    """Extract structured sections from job description without mutating text"""
    if not text:
        return {}, text
    
    sections = {
        'responsibilities': '',
        'requirements': '',
        'benefits': '',
        'about_company': ''
    }
    
    description_text = text
    
    patterns = {
        'responsibilities': r'(?:what you\'ll do|responsibilities|key responsibilities|role overview|duties|job duties|your role|the role|about the role)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:requirements|qualifications|what you\'ll have|you have|benefits|about|$))',
        'requirements': r'(?:what you\'ll have|requirements|qualifications|what you\'ll need|skills|you have|we\'re looking for|required|you bring)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:responsibilities|benefits|about|$))',
        'benefits': r'(?:benefits|perks|what we offer|why join)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:requirements|about|$))',
        'about_company': r'(?:more about us|about us|about the company|company description|who we are|our story|more about)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=$)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, description_text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
    
    if not sections['responsibilities'] and description_text:
        bullet_pattern = r'[•·-]\s*([^\n]+)'
        bullets = re.findall(bullet_pattern, description_text)
        if bullets and len(bullets) > 3:
            sections['responsibilities'] = '\n• ' + '\n• '.join(bullets[:5])
    
    return sections, description_text

def enrich_job_with_sections(job):
    """Enrich a single job with parsed sections"""
    if not job.description:
        return False
    
    try:
        parsed, clean_desc = parse_job_sections(job.description)
        if parsed:
            job.responsibilities = parsed.get('responsibilities', '')
            job.requirements = parsed.get('requirements', '')
            job.benefits = parsed.get('benefits', '')
            job.company_description = parsed.get('about_company', '')
            job.save()
            return True
    except Exception as e:
        print(f"⚠️ Error enriching job {job.id}: {e}")
    
    return False

def scale_database_to_thousands():
    """Scrape jobs with quality filtering and automatic categorization"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GigsAggregator/1.0'}
    added_count = 0
    skipped_count = 0
    filtered_count = 0
    enriched_count = 0
    categorized_count = 0
    
    cutoff = timezone.now() - timedelta(days=90)
    existing_jobs = JobListing.objects.filter(created_at__gte=cutoff)
    existing_keys = set()
    for job in existing_jobs:
        key = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        existing_keys.add(key)
    
    print(f"📊 Existing jobs (last 90 days): {len(existing_keys)}")
    
    # RemoteOK
    print("🌍 Fetching from RemoteOK...")
    try:
        response = requests.get("https://remoteok.com/api", headers=headers, timeout=15)
        if response.status_code == 200:
            job_data = response.json()
            listings = job_data[1:] if isinstance(job_data, list) and len(job_data) > 1 else []
            
            for job in listings:
                title = clean_text(job.get('position', ''))
                company = clean_text(job.get('company', ''))
                
                if not title or not company:
                    continue
                
                description = job.get('description', '')
                if not is_relevant_job(title, description, company):
                    filtered_count += 1
                    continue
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    # Extract salary - NO HARDCODED FALLBACK
                    salary = clean_text(job.get('salary', ''))
                    
                    if not salary:
                        extracted = extract_salary(description)
                        if extracted:
                            salary = extracted
                        # If no salary found, leave as None (don't add hardcoded)
                    
                    new_job = JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Remote')),
                        description=description,
                        apply_url=job.get('url', '#'),
                        salary_range=salary,  # This will be None if no salary found
                        is_active=True,
                        is_approved=True,
                    )
                    
                    if assign_category_to_job(new_job):
                        categorized_count += 1
                    
                    if enrich_job_with_sections(new_job):
                        enriched_count += 1
                    
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ Added: {title} at {company}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ RemoteOK error: {e}")
    
    # Himalayas
    print("🌍 Fetching from Himalayas...")
    offset = 0
    limit = 50
    hima_pages = 0
    
    while hima_pages < 5:
        himalayas_url = f"https://himalayas.app/jobs/api?limit={limit}&offset={offset}"
        try:
            res = requests.get(himalayas_url, headers=headers, timeout=15)
            if res.status_code != 200:
                break
            
            data = res.json()
            jobs_list = data.get('jobs', [])
            if not jobs_list:
                break
            
            for job in jobs_list:
                title = clean_text(job.get('title', ''))
                company = clean_text(job.get('companyName', ''))
                
                if not title or not company:
                    continue
                
                description = job.get('description', '')
                if not is_relevant_job(title, description, company):
                    filtered_count += 1
                    continue
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    # Extract salary - NO HARDCODED FALLBACK
                    salary = clean_text(job.get('salaryRange', ''))
                    
                    if not salary:
                        extracted = extract_salary(description)
                        if extracted:
                            salary = extracted
                        # If no salary found, leave as None (don't add hardcoded)
                    
                    loc_restrictions = job.get('locationRestrictions', [])
                    location = ", ".join(loc_restrictions) if loc_restrictions else "Worldwide"
                    
                    new_job = JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=location,
                        description=description,
                        apply_url=job.get('applicationLink', '#'),
                        salary_range=salary,  # This will be None if no salary found
                        is_active=True,
                        is_approved=True,
                    )
                    
                    if assign_category_to_job(new_job):
                        categorized_count += 1
                    
                    if enrich_job_with_sections(new_job):
                        enriched_count += 1
                    
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ Added: {title} at {company}")
                else:
                    skipped_count += 1
                    
            offset += limit
            hima_pages += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Himalayas error: {e}")
            break
    
    print(f"\n{'='*60}")
    print(f"📊 SCRAPER SUMMARY")
    print(f"{'='*60}")
    print(f"✅ New jobs added: {added_count}")
    print(f"⏭️  Skipped (duplicates): {skipped_count}")
    print(f"🚫 Filtered (low quality/spam): {filtered_count}")
    print(f"📈 Total jobs in database: {JobListing.objects.count()}")
    print(f"🔍 Jobs enriched: {enriched_count}")
    print(f"🏷️  Jobs categorized: {categorized_count}")
    print(f"{'='*60}")
    
    return f"Added {added_count} new jobs | Total: {JobListing.objects.count()} | Filtered: {filtered_count} | Categorized: {categorized_count}"
