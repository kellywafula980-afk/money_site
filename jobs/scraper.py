import requests
import html
import time
from .models import JobListing

# 🏷️ GLOBALGIGS AFFILIATE & NETWORK TRACKING IDENTIFIERS
WHATJOBS_PUBLISHER_ID = "kellywafula_gigs_cpc"
COURSERA_PARTNER_LINK = "https://coursera.pxf.io/c/kellywafula_gigs"
FIVERR_AFFILIATE_LINK = "https://go.fiverr.com/visit/?bta=kellywafula"

def clean_text(text):
    if not text: return ""
    text = html.unescape(text)
    try:
        text = text.encode('latin1').decode('utf-8', errors='ignore')
    except (UnicodeEncodeError, UnicodeDecodeError): pass
    return text.strip()

def route_monetization(title, company, raw_link):
    """Dynamically applies affiliate and CPC tracking modifiers based on job rules."""
    if not raw_link: return ""
    
    if company.lower() in ['doordash', 'unilever', 'nestlé', 'celsius', 'nike', 'coinme']:
        return f"{raw_link}?utm_source=whatjobs&publisher={WHATJOBS_PUBLISHER_ID}&click_mode=cpc"
    elif any(kw in title.lower() for kw in ['design', 'video', 'ugc', 'creative', 'drafter']):
        return f"{FIVERR_AFFILIATE_LINK}&brand=fiverrgigs&landing_page={raw_link}"
    else:
        separator = "&" if "?" in raw_link else "?"
        return f"{raw_link}{separator}ref=kellywafula_gigs&utm_medium=jobboard"

def scale_database_to_thousands():
    """
    Queries multiple programmatic data feeds sequentially to scale the 
    platform's live listings array up to 1,000+ targeted entries.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    added_count = 0

    # Pipeline Phase A: Target RemoteOK tag streams
    tags = ['engineer', 'developer', 'design', 'marketing', 'sales', 'writer', 'recruiter', 'finance']
    print("🚀 Initiating Source A: RemoteOK Categorized Streams...")
    
    for tag in tags:
        url = f"https://remoteok.com/api?tag={tag}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                job_data = response.json()
                # Skip meta data block if array contains objects
                listings = job_data[1:] if isinstance(job_data, list) and len(job_data) > 1 else []
                
                for job in listings:
                    title = clean_text(job.get('position', ''))
                    company = clean_text(job.get('company', ''))
                    location = clean_text(job.get('location', 'Remote'))
                    raw_link = job.get('url', '')
                    
                    if not raw_link or not title or not company: continue
                    if "test" in title.lower(): continue
                    
                    affiliate_link = route_monetization(title, company, raw_link)
                    
                    if not JobListing.objects.filter(title=title, company_name=company).exists():
                        JobListing.objects.create(
                            title=title, company_name=company, location=location,
                            description=job.get('description', ''), apply_url=affiliate_link
                        )
                        added_count += 1
            # Graceful spacing to respect remote rate-limits
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ RemoteOK network exception on tag [{tag}]: {e}")

    # Pipeline Phase B: Inject Himalayas High-Volume Backfill Feed
    print(f"📈 Database at {JobListing.objects.count()} listings. Pulling Source B: Himalayas Engine...")
    offset = 0
    limit = 50
    
    while added_count < 1500: # Cap at a safe buffer to match your goal
        himalayas_url = f"https://himalayas.app/jobs/api?limit={limit}&offset={offset}"
        try:
            res = requests.get(himalayas_url, headers=headers, timeout=10)
            if res.status_code != 200: break
            
            data = res.json()
            jobs_list = data.get('jobs', [])
            if not jobs_list: break
            
            for job in jobs_list:
                title = clean_text(job.get('title', ''))
                company = clean_text(job.get('companyName', ''))
                raw_link = job.get('applicationLink', '')
                
                # Combine location requirements cleanly
                loc_restrictions = job.get('locationRestrictions', [])
                location = ", ".join(loc_restrictions) if loc_restrictions else "Remote"
                
                if not raw_link or not title or not company: continue
                
                affiliate_link = route_monetization(title, company, raw_link)
                
                if not JobListing.objects.filter(title=title, company_name=company).exists():
                    JobListing.objects.create(
                        title=title, company_name=company, location=location,
                        description=job.get('description', ''), apply_url=affiliate_link
                    )
                    added_count += 1
                    
            offset += limit
            if offset >= data.get('totalCount', 0) or offset > 2000: break
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Source B exception at offset {offset}: {e}")
            break

    print(f"💰 Database expansion complete! Injected {added_count} total entries across tracking pipelines.")
    print(f"📊 Current absolute database volume: {JobListing.objects.count()} active rows.")