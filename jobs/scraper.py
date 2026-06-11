import requests
import html
import time
from .models import JobListing

def clean_text(text):
    if not text: return ""
    text = html.unescape(text)
    return text.strip()

def scale_database_to_thousands():
    """Add NEW jobs without deleting existing ones"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) GigsAggregator/1.0'}
    added_count = 0
    skipped_count = 0
    
    # Get existing job titles to avoid duplicates
    existing_titles = set(JobListing.objects.values_list('title', flat=True))
    
    # PIPELINE A: RemoteOK
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
                
                # Only add if not already in database
                if title not in existing_titles:
                    JobListing.objects.create(
                        title=title,
                        company_name=company,
                        location=clean_text(job.get('location', 'Remote')),
                        description=job.get('description', ''),
                        apply_url=job.get('url', '#')
                    )
                    added_count += 1
                    existing_titles.add(title)  # Add to set to avoid duplicates in same run
                else:
                    skipped_count += 1
    except Exception as e:
        print(f"⚠️ RemoteOK error: {e}")
    
    print(f"✅ Added {added_count} new jobs, skipped {skipped_count} existing jobs")
    print(f"📊 Total jobs in database: {JobListing.objects.count()}")
    
    return f"Added {added_count} new jobs"
