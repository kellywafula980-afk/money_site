import requests
import html
import time
import re
from .models import JobListing

def clean_text(text):
    if not text: 
        return ""
    text = html.unescape(text)
    return text.strip()

def extract_salary(text):
    """Try to extract salary from job description or title"""
    if not text:
        return None
    
    # Common salary patterns
    patterns = [
        r'\$(\d{2,3}[,.]?\d{3})\s*[-–]\s*\$(\d{2,3}[,.]?\d{3})',  # $50,000 - $80,000
        r'\$(\d{2,3}[,.]?\d{3})\s*[-–]\s*(\d{2,3}[,.]?\d{3})',   # $50,000 - 80,000
        r'(\d{2,3}[,.]?\d{3})\s*[-–]\s*(\d{2,3}[,.]?\d{3})',     # 50,000 - 80,000
        r'\$(\d{2,3}[,.]?\d{3})\+',                               # $50,000+
        r'\$(\d{2,3}[,.]?\d{3})',                                 # $50,000
        r'(\d{2,3}[,.]?\d{3})\s*(?:per year|annually|yearly)',   # 50,000 per year
        r'(\d{2,3}[,.]?\d{3})\s*(?:-)\s*(\d{2,3}[,.]?\d{3})',    # 50,000 - 80,000
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                return f"${match.group(1)} - ${match.group(2)}"
            else:
                return f"${match.group(1)}"
    
    return None

def parse_job_sections(text):
    """Extract structured sections from job description - Enhanced Version"""
    if not text:
        return {}, text
    
    sections = {
        'responsibilities': '',
        'requirements': '',
        'benefits': '',
        'about_company': ''
    }
    
    # More comprehensive patterns with common section headers
    patterns = {
        'responsibilities': r'(?:what you\'ll do|responsibilities|key responsibilities|role overview|duties|job duties|your role|the role|about the role)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:requirements|qualifications|what you\'ll have|you have|benefits|about|$))',
        'requirements': r'(?:what you\'ll have|requirements|qualifications|what you\'ll need|skills|you have|we\'re looking for|required|you bring)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:responsibilities|benefits|about|$))',
        'benefits': r'(?:benefits|perks|what we offer|why join)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:requirements|about|$))',
        'about_company': r'(?:more about us|about us|about the company|company description|who we are|our story|why o9|more about)[:：\s\n]+([^\n]+(?:\n[^\n]+)*?)(?=$)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
            # Remove extracted section from main text to avoid duplication
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Special handling: Look for bullet points that might be responsibilities/requirements
    if not sections['responsibilities'] and text:
        # Look for lists with dashes or numbers
        bullet_pattern = r'[•·-]\s*([^\n]+)'
        bullets = re.findall(bullet_pattern, text)
        if bullets and len(bullets) > 3:
            sections['responsibilities'] = '\n• ' + '\n• '.join(bullets[:5])
    
    return sections, text.strip()

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
    """Scrape jobs and extract real salaries with automatic enrichment"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GigsAggregator/1.0'}
    added_count = 0
    skipped_count = 0
    enriched_count = 0
    
    existing_jobs = JobListing.objects.all()
    existing_keys = set()
    for job in existing_jobs:
        key = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        existing_keys.add(key)
    
    print(f"📊 Existing jobs: {len(existing_keys)}")
    
    # PIPELINE 1: RemoteOK
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
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    # Get salary from job data
                    salary = clean_text(job.get('salary', ''))
                    description = job.get('description', '')
                    
                    # If no salary in job data, try extracting from description
                    if not salary or salary == '$40,000 - $80,000':
                        extracted = extract_salary(description)
                        if extracted:
                            salary = extracted
                    
                    # Create the job
                    new_job = JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Remote')),
                        description=description,
                        apply_url=job.get('url', '#'),
                        salary_range=salary or '$40,000 - $80,000'
                    )
                    
                    # Enrich the job with structured sections
                    if enrich_job_with_sections(new_job):
                        enriched_count += 1
                    
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ Added: {title} at {company} | Salary: {salary or 'Not specified'}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ RemoteOK error: {e}")
    
    # PIPELINE 2: Himalayas
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
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    # Himalayas sometimes has salaryRange
                    salary = clean_text(job.get('salaryRange', ''))
                    description = job.get('description', '')
                    
                    if not salary:
                        extracted = extract_salary(description)
                        if extracted:
                            salary = extracted
                    
                    loc_restrictions = job.get('locationRestrictions', [])
                    location = ", ".join(loc_restrictions) if loc_restrictions else "Worldwide"
                    
                    new_job = JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=location,
                        description=description,
                        apply_url=job.get('applicationLink', '#'),
                        salary_range=salary or '$40,000 - $80,000'
                    )
                    
                    if enrich_job_with_sections(new_job):
                        enriched_count += 1
                    
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ Added: {title} at {company} | Salary: {salary or 'Not specified'}")
                else:
                    skipped_count += 1
                    
            offset += limit
            hima_pages += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Himalayas error: {e}")
            break
    
    # PIPELINE 3: Jobicy
    print("🌍 Fetching from Jobicy...")
    for count in [50, 100]:
        try:
            jobicy_url = f"https://jobicy.com/api/v2/remote-jobs?count={count}"
            res = requests.get(jobicy_url, headers=headers, timeout=15)
            
            if res.status_code == 200:
                data = res.json()
                jobs_list = data.get('jobs', [])
                
                for job in jobs_list:
                    title = clean_text(job.get('jobTitle', ''))
                    company = clean_text(job.get('companyName', ''))
                    
                    if not title or not company:
                        continue
                    
                    key = f"{title.lower()}|{company.lower()}"
                    if key not in existing_keys:
                        description = job.get('jobDescription', '')
                        salary = extract_salary(description) or '$40,000 - $80,000'
                        
                        new_job = JobListing.objects.create(
                            title=title,
                            company_name=company,
                            location=clean_text(job.get('jobGeo', 'Worldwide')),
                            description=description,
                            apply_url=job.get('url', '#'),
                            salary_range=salary
                        )
                        
                        if enrich_job_with_sections(new_job):
                            enriched_count += 1
                        
                        added_count += 1
                        existing_keys.add(key)
                        print(f"   ✅ Added: {title} at {company} | Salary: {salary}")
                    else:
                        skipped_count += 1
        except Exception as e:
            print(f"⚠️ Jobicy error: {e}")
    
    # PIPELINE 4: Remotive
    print("🌍 Fetching from Remotive...")
    try:
        remotive_url = "https://remotive.com/api/remote-jobs"
        res = requests.get(remotive_url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            jobs_list = data.get('jobs', [])
            
            for job in jobs_list:
                title = clean_text(job.get('title', ''))
                company = clean_text(job.get('company_name', ''))
                
                if not title or not company:
                    continue
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    description = job.get('description', '')
                    salary = clean_text(job.get('salary', ''))
                    
                    if not salary:
                        extracted = extract_salary(description)
                        if extracted:
                            salary = extracted
                    
                    new_job = JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('candidate_required_location', 'Worldwide')),
                        description=description,
                        apply_url=job.get('url', '#'),
                        salary_range=salary or '$40,000 - $80,000'
                    )
                    
                    if enrich_job_with_sections(new_job):
                        enriched_count += 1
                    
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ Added: {title} at {company} | Salary: {salary or 'Not specified'}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ Remotive error: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 SCRAPER SUMMARY")
    print(f"{'='*60}")
    print(f"✅ New jobs added: {added_count}")
    print(f"⏭️  Skipped (duplicates): {skipped_count}")
    print(f"📈 Total jobs in database: {JobListing.objects.count()}")
    print(f"🔍 Jobs enriched with structured content: {enriched_count}")
    print(f"{'='*60}")
    
    return f"Added {added_count} new jobs | Total: {JobListing.objects.count()} | Enriched: {enriched_count}"