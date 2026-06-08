import requests
import html
import time
from .models import JobListing

# 🏷️ GLOBALGIGS TRACKING NETWORK CONFIGURATION
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
    """Applies your tracking, CPC parameters, or affiliate modifiers uniformly."""
    if not raw_link: return ""
    
    if company.lower() in ['doordash', 'unilever', 'nestlé', 'celsius', 'nike', 'coinme']:
        return f"{raw_link}?utm_source=whatjobs&publisher={WHATJOBS_PUBLISHER_ID}&click_mode=cpc"
    elif any(kw in title.lower() for kw in ['design', 'video', 'ugc', 'creative', 'drafter', 'logo']):
        return f"{FIVERR_AFFILIATE_LINK}&brand=fiverrgigs&landing_page={raw_link}"
    else:
        separator = "&" if "?" in raw_link else "?"
        return f"{raw_link}{separator}ref=kellywafula_gigs&utm_medium=jobboard"

def scale_database_to_thousands():
    """
    Queries three separate public pipelines completely unfiltered.
    Captures ALL job types, industries, sectors, and skill levels globally.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GigsAggregator/1.0'}
    added_count = 0

    # ----------------------------------------------------
    # PIPELINE A: RemoteOK General Broad Ingestion Feed
    # ----------------------------------------------------
    print("🚀 Connecting to Source A: RemoteOK Full Feed...")
    try:
        response = requests.get("https://remoteok.com/api", headers=headers, timeout=12)
        if response.status_code == 200:
            job_data = response.json()
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
    except Exception as e:
        print(f"⚠️ Source A pipeline error: {e}")

    # ----------------------------------------------------
    # PIPELINE B: Himalayas High-Volume Unfiltered Stream
    # ----------------------------------------------------
    print(f"📈 Midpoint Check: DB at {JobListing.objects.count()} entries. Launching Source B: Himalayas...")
    offset = 0
    limit = 20 # Optimal pagination safe-cap
    
    while offset < 160: # Sequentially fetches 8 consecutive broad block sets
        himalayas_url = f"https://himalayas.app/jobs/api?limit={limit}&offset={offset}"
        try:
            res = requests.get(himalayas_url, headers=headers, timeout=12)
            if res.status_code != 200: break
            
            data = res.json()
            jobs_list = data.get('jobs', [])
            if not jobs_list: break
            
            for job in jobs_list:
                title = clean_text(job.get('title', ''))
                company = clean_text(job.get('companyName', ''))
                raw_link = job.get('applicationLink', '')
                
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
            time.sleep(0.6) # Courteous sleep to avoid server-side rate limits
        except Exception as e:
            print(f"⚠️ Source B execution interruption at offset {offset}: {e}")
            break

    # ----------------------------------------------------
    # PIPELINE C: Jobicy Diverse Global Categories Engine
    # ----------------------------------------------------
    print(f"🔮 Final Stage: DB at {JobListing.objects.count()} entries. Launching Source C: Jobicy Universal...")
    try:
        # Jobicy returns 50 fresh mixed industry listings out of the box without keys
        jobicy_url = "https://jobicy.com/api/v2/remote-jobs?count=50"
        res = requests.get(jobicy_url, headers=headers, timeout=12)
        
        if res.status_code == 200:
            data = res.json()
            jobs_list = data.get('jobs', [])
            
            for job in jobs_list:
                title = clean_text(job.get('jobTitle', ''))
                company = clean_text(job.get('companyName', ''))
                location = clean_text(job.get('jobGeo', 'Worldwide'))
                raw_link = job.get('url', '')
                
                if not raw_link or not title or not company: continue
                
                affiliate_link = route_monetization(title, company, raw_link)
                
                if not JobListing.objects.filter(title=title, company_name=company).exists():
                    JobListing.objects.create(
                        title=title, company_name=company, location=location,
                        description=job.get('jobDescription', ''), apply_url=affiliate_link
                    )
                    added_count += 1
    except Exception as e:
        print(f"⚠️ Source C network pipeline skipped: {e}")

    print(f"✨ Omnichannel aggregation complete! Injected {added_count} brand-new diverse positions.")
    print(f"📊 Global data asset repository volume: {JobListing.objects.count()} active rows.")