"""
Debug script to test Apify job scraping
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.job_scraper import JobScraper
import json

def test_scraper():
    """Test scraper and print raw data"""
    
    scraper = JobScraper()
    
    # Run scraper
    jobs = scraper.scrape_jobs(
        keywords="Instructional Design, AI PM, Automation",
        location="Ontario, Canada",
        max_jobs=5,
        job_type="fulltime",
        remote="hybrid"
    )
    
    print(f"\n{'='*60}")
    print(f"SCRAPING RESULTS")
    print(f"{'='*60}")
    print(f"Total jobs scraped: {len(jobs)}")
    print(f"{'='*60}\n")
    
    if jobs:
        # Print first job details
        print("FIRST JOB DETAILS:")
        print(json.dumps(jobs[0], indent=2, default=str))
        
        # Print all job titles
        print(f"\n{'='*60}")
        print("ALL JOB TITLES:")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job.get('title', 'NO TITLE')} at {job.get('company', 'NO COMPANY')}")
            print(f"   URL: {job.get('job_url', 'NO URL')}")
    else:
        print("❌ No jobs were processed!")
        print("Check logs/scraper.log for details")

if __name__ == "__main__":
    test_scraper()
