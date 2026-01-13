# Job Autopilot - Job Scraper
# Apify-based Indeed job scraping with caching

import os
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from apify_client import ApifyClient
from modules.database import Job, SessionLocal
from modules.cache_manager import cache_manager
from modules.logger_config import scraper_logger

load_dotenv()

class JobScraper:
    """Scrape jobs from Indeed using Apify"""
    
    def __init__(self):
        self.api_token = os.getenv("APIFY_API_TOKEN")
        self.actor_id = os.getenv("APIFY_INDEED_ACTOR_ID", "MXLpngmVpE8WTESQr")
        
        if not self.api_token:
            scraper_logger.error("APIFY_API_TOKEN not found!")
            raise ValueError("APIFY_API_TOKEN is required")
        
        self.client = ApifyClient(self.api_token)
        scraper_logger.info("Apify client initialized")
    
    def scrape_jobs(
        self,
        keywords: str = None,
        location: str = "Ontario, Canada",
        max_jobs: int = 20,
        job_type: str = "fulltime",
        remote: str = "hybrid"
    ) -> List[Dict]:
        """
        Scrape jobs from Indeed
        
        Args:
            keywords: Search keywords (default from env)
            location: Job location
            max_jobs: Maximum number of jobs to scrape
            job_type: Job type (fulltime, parttime, contract)
            remote: Remote status (remote, hybrid, onsite)
        
        Returns:
            list: Job data dictionaries
        """
        # Use default keywords from environment if not provided
        if not keywords:
            keywords = os.getenv("DEFAULT_KEYWORDS", "Instructional Design, L&D, EdTech")
        
        scraper_logger.info(f"Starting job scrape: {keywords} in {location}")
        
        # Apify actor input
        run_input = {
            "country": "ca",
            "query": keywords,
            "location": location,
            "maxRows": max_jobs,
            "jobType": job_type,
            "remote": remote,
            "enableUniqueJobs": True,
            "fromAge": "7"  # NEW: Only jobs posted in last 7 days
        }
        
        try:
            # Run the Apify actor
            scraper_logger.info(f"Running Apify actor: {self.actor_id}")
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            # Fetch results
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)
            
            scraper_logger.info(f"Scraped {len(items)} jobs from Indeed")
            
            # Process and cache jobs
            processed_jobs = []
            for i, item in enumerate(items):
                try:
                    job_data = self._process_job_data(item)
                    
                    # Skip if processing failed (returns empty dict)
                    if not job_data or not job_data.get("job_url"):
                        scraper_logger.warning(f"Skipping job {i+1}: Missing job_url after processing")
                        continue
                    
                    # Check cache first
                    cached = cache_manager.get_cached_job(job_data["job_url"])
                    if cached:
                        scraper_logger.debug(f"Using cached job: {job_data['title']}")
                        processed_jobs.append(cached)
                    else:
                        # Cache new job
                        cache_manager.cache_job(job_data["job_url"], job_data, ttl_days=7)
                        processed_jobs.append(job_data)
                
                except Exception as e:
                    scraper_logger.error(f"Failed to process job {i+1}: {e}", exc_info=True)
                    continue
            
            scraper_logger.info(f"Successfully processed {len(processed_jobs)} jobs")
            return processed_jobs
        
        except Exception as e:
            scraper_logger.error(f"Apify scraping failed: {e}", exc_info=True)
            return []
    
    def _process_job_data(self, raw_job: Dict) -> Dict:
        """
        Process raw Apify job data into standardized format
        
        Args:
            raw_job: Raw job data from Apify
        
        Returns:
            dict: Processed job data
        """
        try:
            # Extract job URL with multiple fallbacks
            job_url = (
                raw_job.get("url") or 
                raw_job.get("link") or 
                raw_job.get("jobUrl") or 
                raw_job.get("positionUrl") or
                raw_job.get("jobLink") or
                raw_job.get("applyLink") or
                ""
            )
            
            # If still no job_url, log FULL raw data to help debug
            if not job_url:
                scraper_logger.error(f"No job_url found! Available keys: {list(raw_job.keys())}")
                scraper_logger.error(f"FULL Raw job data: {json.dumps(raw_job, indent=2, default=str)}")
                return {}
            
            # Extract posted date
            posted_date = raw_job.get("datePublished") or raw_job.get("postedAt")
            if posted_date:
                try:
                    posted_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
                except:
                    posted_date = None
            
            # Extract expiration date (if available)
            expiration_date = raw_job.get("validThrough") or raw_job.get("expirationDate")
            if expiration_date:
                try:
                    expiration_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                except:
                    expiration_date = None
            
            # Extract company name (Apify uses different field names)
            company = (
                raw_job.get("companyName") or 
                raw_job.get("company") or 
                raw_job.get("hiringOrganization", {}).get("name") or 
                "Company Not Listed"
            )
            
            # Extract location
            location = raw_job.get("location") or raw_job.get("jobLocation", {}).get("address") or "Remote"
            
            # Extract salary - handle both dict and string formats
            salary = "Not specified"
            salary_data = raw_job.get("salary")
            if salary_data:
                if isinstance(salary_data, dict):
                    salary = salary_data.get("salaryText") or salary_data.get("text") or "Not specified"
                elif isinstance(salary_data, str):
                    salary = salary_data
            
            # Determine job category based on title/description
            category = self._categorize_job(
                raw_job.get("title", ""),
                raw_job.get("descriptionText", "") or raw_job.get("description", "")
            )
            
            # Safe location check for is_remote
            is_remote = raw_job.get("isRemote", False)
            if location and isinstance(location, str):
                is_remote = is_remote or ("remote" in location.lower())
            
            processed = {
                "title": raw_job.get("title", "Unknown Position"),
                "company": company,
                "description": raw_job.get("descriptionText") or raw_job.get("description") or "",
                "location": location,
                "salary": salary,
                "is_remote": is_remote,
                
                # Date fields
                "posted_date": posted_date,
                "expiration_date": expiration_date,
                "job_age": raw_job.get("jobAge", ""),  # "17 hours ago"
                
                # URLs
                "job_url": job_url,
                "apply_url": raw_job.get("applyUrl") or raw_job.get("applicationUrl") or job_url,
                "company_url": raw_job.get("companyUrl"),
                "company_logo_url": raw_job.get("companyLogoUrl"),
                "header_image_url": raw_job.get("headerImageUrl"),
                
                # Job details
                "job_type": raw_job.get("jobType", ""),  # fulltime, parttime
                "occupation": raw_job.get("occupation", ""),
                "benefits": raw_job.get("benefits", ""),
                "rating": str(raw_job.get("rating", "")) if raw_job.get("rating") else None,
                
                # Category & source
                "job_category": category,
                "scraped_source": "apify"
            }
            
            return processed
        
        except Exception as e:
            scraper_logger.error(f"Failed to process job data: {e}", exc_info=True)
            scraper_logger.debug(f"Problematic raw_job keys: {list(raw_job.keys()) if raw_job else 'None'}")
            return {}
    
    def _categorize_job(self, title: str, description: str) -> str:
        """
        Categorize job based on title and description
        
        Args:
            title: Job title
            description: Job description
        
        Returns:
            str: Job category ('edtech', 'ai_pm', 'automation', 'l&d', 'other')
        """
        text = f"{title} {description}".lower()
        
        # EdTech keywords
        if any(kw in text for kw in ["edtech", "education technology", "instructional", "learning management", "lms"]):
            return "edtech"
        
        # AI PM keywords
        if any(kw in text for kw in ["ai product", "ai pm", "ai manager", "machine learning product"]):
            return "ai_pm"
        
        # Automation keywords
        if any(kw in text for kw in ["automation", "workflow", "rpa", "process automation", "n8n", "zapier"]):
            return "automation"
        
        # L&D keywords
        if any(kw in text for kw in ["learning development", "l&d", "training", "professional development"]):
            return "l&d"
        
        return "other"
    
    def save_jobs_to_db(self, jobs: List[Dict]) -> int:
        """
        Save scraped jobs to database
        
        Args:
            jobs: List of job dictionaries
        
        Returns:
            int: Number of jobs saved
        """
        try:
            db = SessionLocal()
        except Exception as e:
            scraper_logger.warning(f"Database not available (DEMO mode): {e}")
            return 0
        
        saved_count = 0
        
        try:
            for job_data in jobs:
                # Check if job already exists (by URL)
                existing = db.query(Job).filter(Job.job_url == job_data["job_url"]).first()
                
                if existing:
                    scraper_logger.debug(f"Job already exists: {job_data['title']}")
                    continue
                
                # Create new job
                new_job = Job(**job_data)
                db.add(new_job)
                saved_count += 1
            
            db.commit()
            scraper_logger.info(f"Saved {saved_count} new jobs to database")
            
        except Exception as e:
            db.rollback()
            scraper_logger.error(f"Failed to save jobs to database: {e}", exc_info=True)
        
        finally:
            db.close()
        
        return saved_count
    
    def get_recent_jobs(self, days: int = 3) -> List[Job]:
        """
        Get jobs posted within last N days
        
        Args:
            days: Number of days to look back
        
        Returns:
            list: Job objects
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            jobs = db.query(Job).filter(Job.posted_date >= cutoff_date).all()
            scraper_logger.info(f"Retrieved {len(jobs)} jobs from last {days} days")
            return jobs
        finally:
            db.close()

# Example usage
if __name__ == "__main__":
    scraper = JobScraper()
    jobs = scraper.scrape_jobs(
        keywords="Instructional Design, AI PM, Automation",
        location="Ontario, Canada",
        max_jobs=10
    )
    
    print(f"Found {len(jobs)} jobs")
    for job in jobs[:3]:
        print(f"- {job['title']} at {job['company']}")
    
    # Save to database
    saved = scraper.save_jobs_to_db(jobs)
    print(f"Saved {saved} jobs to database")
