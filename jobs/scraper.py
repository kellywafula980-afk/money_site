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
    """Aggressive scraper - fetches ALL remote jobs from ALL categories (non-tech too)"""
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
    # PIPELINE 1: RemoteOK - All jobs (includes non-tech)
    # ============================================================
    print("🌍 Pipeline 1: RemoteOK (ALL remote jobs - tech, non-tech, everything)...")
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
    # PIPELINE 2: Himalayas - ALL job categories (not just tech)
    # ============================================================
    print("🌍 Pipeline 2: Himalayas (ALL categories - admin, sales, marketing, customer support, etc)...")
    offset = 0
    limit = 50
    hima_pages = 0
    
    # Fetch ALL categories (Himalayas includes non-tech by default)
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
    # PIPELINE 3: Jobicy - Includes ALL job types
    # ============================================================
    print("🌍 Pipeline 3: Jobicy (ALL remote jobs - tech, creative, business, healthcare)...")
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
    # PIPELINE 4: Remotive - ALL remote jobs (includes customer support, sales, etc)
    # ============================================================
    print("🌍 Pipeline 4: Remotive (ALL remote jobs - ALL categories)...")
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
                    # Remotive has good category data
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
    # PIPELINE 5: Indeed (via unofficial API) - ALL job types
    # ============================================================
    print("🌍 Pipeline 5: Finding MORE remote jobs (non-tech focused)...")
    
    # Try alternative API endpoints that have diverse job categories
    alt_sources = [
        ("https://www.arbeitnow.com/api/job-board-api", "arbeitnow"),
        ("https://api.ratemyjob.com/jobs?remote=true", "rate_my_job"),
    ]
    
    for source_url, source_name in alt_sources:
        try:
            res = requests.get(source_url, headers=headers, timeout=10)
            if res.status_code == 200:
                print(f"   📡 Connected to {source_name}...")
                # Attempt to parse if format is known
                try:
                    data = res.json()
                    jobs_data = []
                    if isinstance(data, list):
                        jobs_data = data
                    elif isinstance(data, dict):
                        jobs_data = data.get('jobs', data.get('data', []))
                    
                    for job in jobs_data[:30]:  # Limit to 30 per source
                        if isinstance(job, dict):
                            title = clean_text(job.get('title', job.get('name', '')))
                            company = clean_text(job.get('company', job.get('company_name', '')))
                            
                            if title and company:
                                key = f"{title.lower()}|{company.lower()}"
                                if key not in existing_keys:
                                    JobListing.objects.create(
                                        title=title,
                                        company_name=company,
                                        location=clean_text(job.get('location', job.get('candidate_required_location', 'Remote'))),
                                        description=job.get('description', job.get('about', 'No description provided')),
                                        apply_url=job.get('url', job.get('apply_url', '#')),
                                        salary_range=clean_text(job.get('salary', '$40,000 - $80,000'))
                                    )
                                    added_count += 1
                                    existing_keys.add(key)
                                    print(f"   ✅ [{added_count}] Added: {title} at {company} [via {source_name}]")
                except:
                    pass
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
    
    # Categorize by job types (approximate)
    if added_count > 0:
        print(f"\n🔔 {added_count} new jobs added! Your job board now has diverse roles across ALL industries.")
    
    return f"Added {added_count} new jobs | Total: {JobListing.objects.count()}"