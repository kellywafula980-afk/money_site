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

def is_english(text):
    """Check if text is primarily English (skip non-English listings)"""
    if not text:
        return True
    
    # Common non-English characters/patterns to filter out
    non_english_patterns = [
        r'[àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþß]',  # Accented letters (German, French, Spanish)
        r'[а-яА-Я]',  # Cyrillic (Russian, Ukrainian)
        r'[ก-๙]',     # Thai
        r'[一-鿋]',     # Chinese/Japanese/Korean
        r'[가-힣]',     # Korean
        r'[א-ת]',      # Hebrew
        r'[০-৯]',      # Bengali
        r'[\u0600-\u06FF]',  # Arabic
    ]
    
    # Check title (most indicative)
    for pattern in non_english_patterns:
        if re.search(pattern, text):
            return False
    return True

def scale_database_to_thousands():
    """Scrape global English remote jobs - ALL categories, worldwide"""
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
    print("🌍 Filtering: English-language jobs only | Worldwide locations\n")
    
    # ============================================================
    # PIPELINE 1: RemoteOK - Global English jobs
    # ============================================================
    print("🌍 Pipeline 1: RemoteOK (Worldwide English jobs)...")
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
                
                # Skip non-English listings
                if not is_english(title) or not is_english(company):
                    non_english_skipped += 1
                    continue
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Worldwide')),
                        description=job.get('description', ''),
                        apply_url=job.get('url', '#'),
                        salary_range=clean_text(job.get('salary', '$40,000 - $80,000'))
                    )
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ [{added_count}] Added: {title} at {company}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ RemoteOK error: {e}")
    
    # ============================================================
    # PIPELINE 2: Himalayas - Global English jobs
    # ============================================================
    print("\n🌍 Pipeline 2: Himalayas (Worldwide English jobs)...")
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
                
                # Skip non-English listings
                if not is_english(title) or not is_english(company):
                    non_english_skipped += 1
                    continue
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    loc_restrictions = job.get('locationRestrictions', [])
                    location = ", ".join(loc_restrictions) if loc_restrictions else "Worldwide"
                    
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=location,
                        description=job.get('description', ''),
                        apply_url=job.get('applicationLink', '#'),
                        salary_range=clean_text(job.get('salaryRange', '$40,000 - $80,000'))
                    )
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ [{added_count}] Added: {title} at {company}")
                else:
                    skipped_count += 1
                    
            offset += limit
            hima_pages += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Himalayas error: {e}")
            break
    
    # ============================================================
    # PIPELINE 3: Jobicy - Global English jobs
    # ============================================================
    print("\n🌍 Pipeline 3: Jobicy (Worldwide English jobs)...")
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
                    
                    # Skip non-English listings
                    if not is_english(title) or not is_english(company):
                        non_english_skipped += 1
                        continue
                    
                    key = f"{title.lower()}|{company.lower()}"
                    if key not in existing_keys:
                        JobListing.objects.create(
                            title=title,
                            company_name=company,
                            location=clean_text(job.get('jobGeo', 'Worldwide')),
                            description=job.get('jobDescription', ''),
                            apply_url=job.get('url', '#'),
                            salary_range=clean_text(job.get('salary', '$40,000 - $80,000'))
                        )
                        added_count += 1
                        existing_keys.add(key)
                        print(f"   ✅ [{added_count}] Added: {title} at {company}")
                    else:
                        skipped_count += 1
        except Exception as e:
            print(f"⚠️ Jobicy error for count {count}: {e}")
    
    # ============================================================
    # PIPELINE 4: Remotive - Global English jobs (already English-only)
    # ============================================================
    print("\n🌍 Pipeline 4: Remotive (Worldwide English jobs)...")
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
                    category = clean_text(job.get('category', 'General'))
                    
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('candidate_required_location', 'Worldwide')),
                        description=job.get('description', ''),
                        apply_url=job.get('url', '#'),
                        salary_range=clean_text(job.get('salary', '$40,000 - $80,000'))
                    )
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ [{added_count}] Added: {title} at {company} [{category}]")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ Remotive error: {e}")
    
    # ============================================================
    # PIPELINE 5: Arbeitnow - Global English jobs
    # ============================================================
    print("\n🌍 Pipeline 5: Arbeitnow (Global remote jobs)...")
    try:
        arbeitnow_url = "https://www.arbeitnow.com/api/job-board-api"
        res = requests.get(arbeitnow_url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            jobs_list = data.get('data', [])
            
            for job in jobs_list:
                title = clean_text(job.get('title', ''))
                company = clean_text(job.get('company_name', ''))
                
                if not title or not company:
                    continue
                
                # Skip non-English
                if not is_english(title):
                    non_english_skipped += 1
                    continue
                
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Worldwide')),
                        description=job.get('description', ''),
                        apply_url=job.get('url', '#'),
                        salary_range="$40,000 - $80,000"
                    )
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ [{added_count}] Added: {title} at {company}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ Arbeitnow error: {e}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print(f"📊 SCRAPER SUMMARY - ENGLISH JOBS WORLDWIDE")
    print(f"{'='*60}")
    print(f"✅ NEW English jobs added: {added_count}")
    print(f"⏭️  Skipped (already exist): {skipped_count}")
    print(f"🚫 Skipped (non-English): {non_english_skipped}")
    print(f"📈 TOTAL English jobs in database: {JobListing.objects.count()}")
    print(f"{'='*60}")
    
    if added_count > 0:
        print(f"\n🔔 {added_count} new English jobs added from around the world!")
    
    return f"Added {added_count} new English jobs | Total: {JobListing.objects.count()}"