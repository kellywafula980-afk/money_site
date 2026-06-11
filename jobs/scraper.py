import requests
import html
import time
from .models import JobListing

def clean_text(text):
    if not text: 
        return ""
    text = html.unescape(text)
    return text.strip()

def scale_database_to_thousands():
    """Add NEW jobs without deleting existing ones - IMPROVED VERSION"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GigsAggregator/1.0'}
    added_count = 0
    skipped_count = 0
    
    # Get existing job identifiers (more reliable than just title)
    existing_jobs = JobListing.objects.all()
    existing_keys = set()
    for job in existing_jobs:
        # Create a unique key from title + company (more accurate)
        key = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        existing_keys.add(key)
    
    print(f"📊 Existing jobs in database: {len(existing_keys)}")
    
    # PIPELINE A: RemoteOK
    print("🚀 Fetching from RemoteOK...")
    try:
        response = requests.get("https://remoteok.com/api", headers=headers, timeout=12)
        if response.status_code == 200:
            job_data = response.json()
            listings = job_data[1:] if isinstance(job_data, list) and len(job_data) > 1 else []
            
            for job in listings:
                title = clean_text(job.get('position', ''))
                company = clean_text(job.get('company', ''))
                
                if not title or not company:
                    continue
                
                # Check if job already exists (by title+company)
                key = f"{title.lower()}|{company.lower()}"
                if key not in existing_keys:
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Remote')),
                        description=job.get('description', ''),
                        apply_url=job.get('url', '#')
                    )
                    added_count += 1
                    existing_keys.add(key)  # Add to set to avoid duplicates in same run
                    print(f"   ✅ Added: {title} at {company}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ RemoteOK error: {e}")
    
    # PIPELINE B: Himalayas
    print("🚀 Fetching from Himalayas...")
    offset = 0
    limit = 20
    
    while offset < 160:
        himalayas_url = f"https://himalayas.app/jobs/api?limit={limit}&offset={offset}"
        try:
            res = requests.get(himalayas_url, headers=headers, timeout=12)
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
                    location = ", ".join(loc_restrictions) if loc_restrictions else "Remote"
                    
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=location,
                        description=job.get('description', ''),
                        apply_url=job.get('applicationLink', '#')
                    )
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ Added: {title} at {company}")
                else:
                    skipped_count += 1
                    
            offset += limit
            time.sleep(0.6)
        except Exception as e:
            print(f"⚠️ Himalayas error at offset {offset}: {e}")
            break
    
    # PIPELINE C: Jobicy
    print("🚀 Fetching from Jobicy...")
    try:
        jobicy_url = "https://jobicy.com/api/v2/remote-jobs?count=50"
        res = requests.get(jobicy_url, headers=headers, timeout=12)
        
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
                        apply_url=job.get('url', '#')
                    )
                    added_count += 1
                    existing_keys.add(key)
                    print(f"   ✅ Added: {title} at {company}")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ Jobicy error: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 SCRAPER SUMMARY")
    print(f"{'='*50}")
    print(f"✅ New jobs added: {added_count}")
    print(f"⏭️  Skipped (already exist): {skipped_count}")
    print(f"📈 Total jobs in database: {JobListing.objects.count()}")
    print(f"{'='*50}")
    
    return f"Added {added_count} new jobs, total: {JobListing.objects.count()}"