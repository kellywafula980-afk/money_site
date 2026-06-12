import requests
import html
import time
import random
from .models import JobListing

def clean_text(text):
    if not text: 
        return ""
    text = html.unescape(text)
    return text.strip()

def scale_database_to_thousands():
    """Aggressive scraper - fetches ALL remote jobs from multiple sources"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    added_count = 0
    skipped_count = 0
    
    # Get existing jobs to avoid duplicates
    existing_jobs = JobListing.objects.all()
    existing_keys = set()
    for job in existing_jobs:
        key = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        existing_keys.add(key)
    
    print(f"📊 Existing jobs in database: {len(existing_keys)}")
    
    # ============================================================
    # PIPELINE 1: RemoteOK - Full feed (all jobs, no filter)
    # ============================================================
    print("🌍 Pipeline 1: RemoteOK (All remote jobs)...")
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
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Remote')),
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
    # PIPELINE 2: Himalayas - All categories (full scrape)
    # ============================================================
    print("🌍 Pipeline 2: Himalayas (All job categories)...")
    offset = 0
    limit = 50
    hima_pages = 0
    
    while hima_pages < 5:  # Fetch 5 pages of 50 jobs = 250 jobs
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
    # PIPELINE 3: Jobicy - All 100 jobs (max allowed)
    # ============================================================
    print("🌍 Pipeline 3: Jobicy (All remote categories)...")
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
    # PIPELINE 4: Remotive - All active remote jobs
    # ============================================================
    print("🌍 Pipeline 4: Remotive (All active remote jobs)...")
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
                    print(f"   ✅ [{added_count}] Added: {title} at {company}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ Remotive error: {e}")
    
    # ============================================================
    # PIPELINE 5: RealJobGuru (if available)
    # ============================================================
    print("🌍 Pipeline 5: Alternative job sources...")
    alt_sources = [
        "https://www.arbeitnow.com/api/job-board-api",
        "https://jobsearch.api.jobtechdev.se/search?q=remote",
        "https://api.ratemyjob.com/jobs?remote=true"
    ]
    
    for source in alt_sources:
        try:
            res = requests.get(source, headers=headers, timeout=10)
            if res.status_code == 200:
                print(f"   📡 Connected to {source[:50]}...")
                # Parse based on expected format (varies by source)
        except:
            pass  # Silently skip unavailable sources
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print(f"📊 SCRAPER SUMMARY - FINAL REPORT")
    print(f"{'='*60}")
    print(f"✅ NEW jobs added today: {added_count}")
    print(f"⏭️  SKIPPED (already exist): {skipped_count}")
    print(f"📈 TOTAL jobs in database: {JobListing.objects.count()}")
    print(f"{'='*60}")
    
    # Trigger sitemap refresh notification
    if added_count > 0:
        print(f"\n🔔 {added_count} new jobs added! Sitemap will auto-update.")
    
    return f"Added {added_count} new jobs | Total: {JobListing.objects.count()}"