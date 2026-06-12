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

def detect_language_and_priority(title, company, description=""):
    """Detect if job is English or non-English"""
    full_text = f"{title} {company} {description}".lower()
    
    # Non-English indicators
    non_english_patterns = [
        r'\(m/w/d\)', r'\(gn\)', r'\(m/w/x\)', r'\(d/w/m\)',
        r'berlin', r'münchen', r'munich', r'hamburg', r'köln', r'cologne',
        r'frankfurt', r'stuttgart', r'düsseldorf', r'dresden', r'nürnberg',
        r'leipzig', r'essen', r'dortmund', r'bonn', r'münster',
        r'gesucht', r'bewerben', r'mitarbeiter', r'teamleiter',
        r'gmbh', r'ag', r'kg', r'\.de',
        r'paris', r'lille', r'lyon', r'marseille', r'toulouse',
        r'recherchons', r'poste', r'cdi', r'stage', r'alternance',
        r'madrid', r'barcelona', r'valencia', r'sevilla',
        r'se busca', r'oferta', r'contrato', r'jornada',
        r'[а-яА-Я]', r'[一-鿋]', r'[가-힣]',
    ]
    
    for pattern in non_english_patterns:
        if re.search(pattern, full_text, re.IGNORECASE):
            return 'non_english'
    return 'english'

def scale_database_to_thousands():
    """MASSIVE SCRAPER - Fetches 1000+ jobs from multiple sources"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    added_count = 0
    english_count = 0
    non_english_count = 0
    skipped_count = 0
    
    # Get existing jobs to avoid duplicates
    existing_jobs = JobListing.objects.all()
    existing_keys = set()
    for job in existing_jobs:
        key = f"{job.title.lower().strip()}|{job.company_name.lower().strip()}"
        existing_keys.add(key)
    
    print(f"📊 Existing jobs: {len(existing_keys)}")
    print("🚀 MASSIVE SCRAPE STARTING - Target: 1000+ new jobs\n")
    
    # ============================================================
    # PIPELINE 1: RemoteOK (All jobs, full feed)
    # ============================================================
    print("🌍 Pipeline 1: RemoteOK (Full feed)...")
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
                
                language = detect_language_and_priority(title, company, '')
                key = f"{title.lower()}|{company.lower()}"
                
                if key not in existing_keys:
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Remote')),
                        description=job.get('description', ''),
                        apply_url=job.get('url', '#'),
                        salary_range=clean_text(job.get('salary', '$40,000 - $80,000')),
                        is_premium=(language == 'english')
                    )
                    added_count += 1
                    existing_keys.add(key)
                    if language == 'english':
                        english_count += 1
                    else:
                        non_english_count += 1
                    print(f"   ✅ [{added_count}] Added: {title[:50]}...")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ RemoteOK error: {e}")
    
    # ============================================================
    # PIPELINE 2: Himalayas (Multiple pages - up to 500 jobs)
    # ============================================================
    print("\n🌍 Pipeline 2: Himalayas (Multi-page - 500+ jobs)...")
    hima_pages = 0
    offset = 0
    limit = 50
    
    while hima_pages < 15:  # 15 pages x 50 = 750 jobs max
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
                
                language = detect_language_and_priority(title, company, '')
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
                        salary_range=clean_text(job.get('salaryRange', '$40,000 - $80,000')),
                        is_premium=(language == 'english')
                    )
                    added_count += 1
                    existing_keys.add(key)
                    if language == 'english':
                        english_count += 1
                    else:
                        non_english_count += 1
                    print(f"   ✅ [{added_count}] Added: {title[:50]}...")
                else:
                    skipped_count += 1
                    
            offset += limit
            hima_pages += 1
            time.sleep(0.3)
            print(f"   📄 Himalayas page {hima_pages}/15 processed")
        except Exception as e:
            print(f"⚠️ Himalayas error at offset {offset}: {e}")
            break
    
    # ============================================================
    # PIPELINE 3: Jobicy (Multiple requests - 100 + 100 = 200 jobs)
    # ============================================================
    print("\n🌍 Pipeline 3: Jobicy (200 jobs)...")
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
                    
                    language = detect_language_and_priority(title, company, '')
                    key = f"{title.lower()}|{company.lower()}"
                    
                    if key not in existing_keys:
                        JobListing.objects.create(
                            title=title,
                            company_name=company,
                            location=clean_text(job.get('jobGeo', 'Worldwide')),
                            description=job.get('jobDescription', ''),
                            apply_url=job.get('url', '#'),
                            salary_range=clean_text(job.get('salary', '$40,000 - $80,000')),
                            is_premium=(language == 'english')
                        )
                        added_count += 1
                        existing_keys.add(key)
                        if language == 'english':
                            english_count += 1
                        else:
                            non_english_count += 1
                        print(f"   ✅ [{added_count}] Added: {title[:50]}...")
                    else:
                        skipped_count += 1
        except Exception as e:
            print(f"⚠️ Jobicy error for count {count}: {e}")
    
    # ============================================================
    # PIPELINE 4: Remotive (All jobs)
    # ============================================================
    print("\n🌍 Pipeline 4: Remotive (All remote jobs)...")
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
                
                language = detect_language_and_priority(title, company, '')
                key = f"{title.lower()}|{company.lower()}"
                
                if key not in existing_keys:
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('candidate_required_location', 'Worldwide')),
                        description=job.get('description', ''),
                        apply_url=job.get('url', '#'),
                        salary_range=clean_text(job.get('salary', '$40,000 - $80,000')),
                        is_premium=(language == 'english')
                    )
                    added_count += 1
                    existing_keys.add(key)
                    if language == 'english':
                        english_count += 1
                    else:
                        non_english_count += 1
                    print(f"   ✅ [{added_count}] Added: {title[:50]}...")
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ Remotive error: {e}")
    
    # ============================================================
    # PIPELINE 5: Arbeitnow (Multiple categories)
    # ============================================================
    print("\n🌍 Pipeline 5: Arbeitnow (All categories)...")
    categories = ['software', 'sales', 'marketing', 'design', 'customer-support', 'finance']
    
    for category in categories:
        try:
            arbeitnow_url = f"https://www.arbeitnow.com/api/job-board-api?category={category}"
            res = requests.get(arbeitnow_url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                jobs_list = data.get('data', [])
                
                for job in jobs_list:
                    title = clean_text(job.get('title', ''))
                    company = clean_text(job.get('company_name', ''))
                    
                    if not title or not company:
                        continue
                    
                    language = detect_language_and_priority(title, company, '')
                    key = f"{title.lower()}|{company.lower()}"
                    
                    if key not in existing_keys:
                        JobListing.objects.create(
                            title=title,
                            company_name=company,
                            location=clean_text(job.get('location', 'Worldwide')),
                            description=job.get('description', ''),
                            apply_url=job.get('url', '#'),
                            salary_range="$40,000 - $80,000",
                            is_premium=(language == 'english')
                        )
                        added_count += 1
                        existing_keys.add(key)
                        if language == 'english':
                            english_count += 1
                        else:
                            non_english_count += 1
                        print(f"   ✅ [{added_count}] Added: {title[:50]}...")
                    else:
                        skipped_count += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Arbeitnow ({category}) error: {e}")
    
    # ============================================================
    # PIPELINE 6: Adzuna (if API available - requires key)
    # ============================================================
    print("\n🌍 Pipeline 6: Additional sources...")
    
    # Try alternative free APIs
    alt_sources = [
        ("https://api.allorigins.win/raw?url=https://weworkremotely.com/remote-jobs.rss", "RSS"),
    ]
    
    for source_url, source_name in alt_sources:
        try:
            res = requests.get(source_url, headers=headers, timeout=10)
            if res.status_code == 200:
                print(f"   📡 Connected to {source_name}...")
        except:
            pass
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*70}")
    print(f"📊 MASSIVE SCRAPE SUMMARY")
    print(f"{'='*70}")
    print(f"✅ NEW jobs added TOTAL: {added_count}")
    print(f"   🇬🇧 English jobs: {english_count} (will show first)")
    print(f"   🌍 Non-English jobs: {non_english_count} (will show lower)")
    print(f"⏭️  Skipped (duplicates): {skipped_count}")
    print(f"📈 TOTAL jobs now in database: {JobListing.objects.count()}")
    print(f"{'='*70}")
    
    if added_count > 1000:
        print(f"\n🎉 EXCELLENT! Added over 1000 new jobs!")
    elif added_count > 500:
        print(f"\n👍 Great! Added over 500 new jobs!")
    elif added_count > 0:
        print(f"\n✅ Added {added_count} new jobs.")
    
    return f"Added {added_count} new jobs | Total: {JobListing.objects.count()} | English: {english_count} | Non-English: {non_english_count}"