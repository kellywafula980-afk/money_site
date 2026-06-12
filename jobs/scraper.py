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

def is_english_job(title, company, description=""):
    """Aggressive check to determine if job is English-only"""
    
    # Combine all text for checking
    full_text = f"{title} {company} {description}".lower()
    
    # German indicators (reject these)
    german_patterns = [
        r'\(m/w/d\)', r'\(gn\)', r'\(m/w/x\)',  # German job markers
        r'berlin', r'münchen', r'munich', r'hamburg', r'köln', r'cologne', r'frankfurt',
        r'stuttgart', r'düsseldorf', r'dresden', r'nürnberg', r'nuremberg', r'hannover',
        r'leipzig', r'essen', r'dortmund', r'bochum', r'wuppertal', r'bielefeld',
        r'bonn', r'münster', r'karlsruhe', r'mannheim', r'augsburg', r'wiesbaden',
        r'mönchengladbach', r'braunschweig', r'chemnitz', r'kiel', r'aachen',
        r'gesucht', r'ihre aufgaben', r'ihr profil', r'wir bieten', r'bewerben',
        r'mitarbeiter', r'teamleiter', r'abteilungsleiter', r'niederlassung',
        r'gehalt', r'urlaub', r'weiterbildung', r'betriebliche altersvorsorge',
        r'homeoffice', r'hybrides arbeiten', r'vertrieb', r'kundenbetreuung',
        r'lohnbuchhalter', r'buchhalter', r'steuerberater', r'wirtschaftsprüfer',
        r'recruiter', r'personalreferent', r'sachbearbeiter', r'projektleiter',
        r'product owner', r'scrum master', r'devops', r'fullstack', r'frontend',
        r'backend', r'developer', r'ingenieur', r'techniker', r'fahrer', r'lagerist',
        r'produktionsmitarbeiter', r'reinigungskraft', r'hausmeister',
        r'www\.', r'\.de', r'gmbh', r'ag', r'kg', r'ohg', r'ev', r'eg'
    ]
    
    # Strong positive English indicators
    english_indicators = [
        r'remote', r'worldwide', r'united states', r'canada', r'uk', r'australia',
        r'english required', r'fluent english', r'us citizen', r'work from home',
        r'full-time', r'part-time', r'contract', r'permanent', r'benefits',
        r'health insurance', r'401k', r'pto', r'vacation', r'salary', r'usd', r'$'
    ]
    
    # Check for German patterns
    for pattern in german_patterns:
        if re.search(pattern, full_text):
            return False
    
    # If description is short and title has German, reject
    if len(description) < 200:
        german_quick_check = [
            r'\bm/w/d\b', r'\bgn\b', r'\bgesucht\b', r'\bihre\b',
            r'\bwir\b', r'\bbewerben\b', r'\bmitarbeiter\b', r'\bteamleiter\b'
        ]
        for pattern in german_quick_check:
            if re.search(pattern, full_text):
                return False
    
    # Accept English jobs from global companies even if location is Germany
    english_companies = [
        r'amazon', r'microsoft', r'google', r'apple', r'meta', r'netflix',
        r'spotify', r'uber', r'airbnb', r'salesforce', r'adobe', r'oracle',
        r'ibm', r'dell', r'hp', r'intel', r'cisco', r'paypal', r'shopify'
    ]
    
    for company_pattern in english_companies:
        if re.search(company_pattern, full_text):
            return True
    
    # If job has English indicators AND no German indicators, accept
    has_english = any(re.search(p, full_text) for p in english_indicators)
    
    # If location is clearly non-German country, accept
    non_german_countries = [r'united states', r'canada', r'uk', r'australia', r'brazil', r'india']
    in_english_country = any(re.search(p, full_text) for p in non_german_countries)
    
    # Default: accept if has English indicators or in English country
    return has_english or in_english_country

def scale_database_to_thousands():
    """Scrape global English remote jobs - filter out German/non-English"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    added_count = 0
    skipped_count = 0
    non_english_skipped = 0
    
    # Get existing jobs to avoid duplicates
    existing_jobs = JobListing.objects.all()
    existing_keys = set()
    for job in existing_jobs:
        key = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        existing_keys.add(key)
    
    print(f"📊 Existing jobs in database: {len(existing_keys)}")
    print("🌍 Filtering: English-language jobs only | Rejecting German/Non-English\n")
    
    # List of sources to scrape
    sources = [
        ("https://remoteok.com/api", "RemoteOK"),
        ("https://remotive.com/api/remote-jobs", "Remotive"),
        ("https://jobicy.com/api/v2/remote-jobs?count=100", "Jobicy"),
        ("https://www.arbeitnow.com/api/job-board-api", "Arbeitnow"),
    ]
    
    for source_url, source_name in sources:
        print(f"🌍 Pipeline: {source_name}...")
        try:
            response = requests.get(source_url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"   ⚠️ {source_name} returned {response.status_code}")
                continue
            
            data = response.json()
            jobs_list = []
            
            # Parse different response formats
            if source_name == "RemoteOK":
                jobs_list = data[1:] if isinstance(data, list) and len(data) > 1 else []
            elif source_name == "Remotive":
                jobs_list = data.get('jobs', [])
            elif source_name == "Jobicy":
                jobs_list = data.get('jobs', [])
            elif source_name == "Arbeitnow":
                jobs_list = data.get('data', [])
            
            for job in jobs_list:
                # Extract fields based on source
                if source_name == "RemoteOK":
                    title = clean_text(job.get('position', ''))
                    company = clean_text(job.get('company', ''))
                    location = clean_text(job.get('location', 'Worldwide'))
                    description = job.get('description', '')
                    apply_url = job.get('url', '#')
                    salary = clean_text(job.get('salary', '$40,000 - $80,000'))
                elif source_name == "Remotive":
                    title = clean_text(job.get('title', ''))
                    company = clean_text(job.get('company_name', ''))
                    location = clean_text(job.get('candidate_required_location', 'Worldwide'))
                    description = job.get('description', '')
                    apply_url = job.get('url', '#')
                    salary = clean_text(job.get('salary', '$40,000 - $80,000'))
                elif source_name == "Jobicy":
                    title = clean_text(job.get('jobTitle', ''))
                    company = clean_text(job.get('companyName', ''))
                    location = clean_text(job.get('jobGeo', 'Worldwide'))
                    description = job.get('jobDescription', '')
                    apply_url = job.get('url', '#')
                    salary = clean_text(job.get('salary', '$40,000 - $80,000'))
                elif source_name == "Arbeitnow":
                    title = clean_text(job.get('title', ''))
                    company = clean_text(job.get('company_name', ''))
                    location = clean_text(job.get('location', 'Worldwide'))
                    description = job.get('description', '')
                    apply_url = job.get('url', '#')
                    salary = "$40,000 - $80,000"
                else:
                    continue
                
                if not title or not company:
                    continue
                
                # Apply English language filter
                if not is_english_job(title, company, description):
                    non_english_skipped += 1
                    continue
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=location,
                        description=description,
                        apply_url=apply_url,
                        salary_range=salary
                    )
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ [{added_count}] Added: {title} at {company} [{location[:30]}]")
                else:
                    skipped_count += 1
                    
        except Exception as e:
            print(f"⚠️ {source_name} error: {e}")
        
        time.sleep(0.5)
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print(f"📊 SCRAPER SUMMARY - ENGLISH JOBS WORLDWIDE")
    print(f"{'='*60}")
    print(f"✅ NEW English jobs added: {added_count}")
    print(f"⏭️  Skipped (already exist): {skipped_count}")
    print(f"🚫 Filtered out (German/Non-English): {non_english_skipped}")
    print(f"📈 TOTAL English jobs in database: {JobListing.objects.count()}")
    print(f"{'='*60}")
    
    if added_count > 0:
        print(f"\n🔔 {added_count} new English jobs added from around the world!")
    
    return f"Added {added_count} new English jobs | Total: {JobListing.objects.count()}"