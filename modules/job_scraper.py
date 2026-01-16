# Job Autopilot - Job Scraper
# Apify-based Indeed job scraping with caching

import os
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv
from apify_client import ApifyClient
from modules.database import Job, Application, SessionLocal
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
        # scraper_logger.info("Apify client initialized")
    
    def scrape_jobs(
        self,
        keywords: str = None,
        location: str = "Ontario, Canada",
        max_jobs: int = 20,
        job_type: str = "fulltime",
        remote: str = "hybrid",
        days_ago: int = 7  # Allow configuring days
    ) -> List[Dict]:
        """
        Scrape jobs from Indeed
        
        Args:
            keywords: Search keywords (default from env)
            location: Job location
            max_jobs: Maximum number of jobs to scrape
            job_type: Job type (fulltime, parttime, contract)
            remote: Remote status (remote, hybrid, onsite)
            days_ago: Fetch jobs posted within last N days (default 7)
        
        Returns:
            list: Job data dictionaries
        """
        # Use default keywords from environment if not provided
        if not keywords:
            keywords = os.getenv("DEFAULT_KEYWORDS", "Instructional Design, L&D, EdTech")
        
        scraper_logger.info(f"Starting job scrape: {keywords} in {location} (Last {days_ago} days)")
        
        # Apify actor input
        run_input = {
            "country": "ca",
            "query": keywords,
            "location": location,
            "maxRows": max_jobs,
            "jobType": job_type,
            "remote": remote,
            "enableUniqueJobs": True,
            "maxAge": days_ago,   # Common parameter name for scrapers
            "fromAge": days_ago,  # Indeed URL parameter name
            "publishedWithinDays": days_ago  # Another common variant
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
            
            # POST-PROCESSING: Date filter (Apify Actor may not respect maxAge param)
            cutoff_date = datetime.utcnow() - timedelta(days=days_ago)
            filtered_jobs = []
            unknown_date_count = 0
            
            for job in processed_jobs:
                posted = job.get('posted_date')
                if posted:
                    # Handle both datetime and string formats
                    if isinstance(posted, str):
                        try:
                            posted = datetime.fromisoformat(posted.replace('Z', '+00:00'))
                        except:
                            posted = None
                    
                    if posted and posted >= cutoff_date:
                        filtered_jobs.append(job)
                    else:
                        scraper_logger.debug(f"Filtered out old job: {job['title']} (posted {posted})")
                else:
                    # No date available - keep but flag
                    job['_date_unknown'] = True
                    filtered_jobs.append(job)
                    unknown_date_count += 1
            
            scraper_logger.info(f"Date filter: {len(processed_jobs)} → {len(filtered_jobs)} (last {days_ago} days, {unknown_date_count} unknown date)")
            return filtered_jobs
        
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
            
            # Extract location - ensure it's always a string
            location_raw = raw_job.get("location") or raw_job.get("jobLocation")
            
            if isinstance(location_raw, dict):
                # Location is a dict, extract city from it
                location = (
                    location_raw.get("city") or 
                    location_raw.get("formattedAddressShort") or
                    location_raw.get("formattedAddress") or
                    location_raw.get("address") or
                    "Remote"
                )
            elif isinstance(location_raw, str):
                # Location is already a string
                location = location_raw
            else:
                location = "Remote"
            
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
                "description": self.clean_html_tags(raw_job.get("descriptionText") or raw_job.get("description") or ""),
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
                "scraped_source": "apify",
                
                # NEW: Apollo Agent fields
                "company_domain": self.extract_company_domain(
                    raw_job.get("applyUrl") or raw_job.get("companyUrl") or job_url
                ),
                "hr_contact_status": "pending"  # Will be updated after Apollo scraping
            }
            
            return processed
        
        except Exception as e:
            scraper_logger.error(f"Failed to process job data: {e}", exc_info=True)
            scraper_logger.debug(f"Problematic raw_job keys: {list(raw_job.keys()) if raw_job else 'None'}")
            return {}

    def extract_company_domain(self, url: str) -> Optional[str]:
        """
        Extract clean company domain from a URL (apply_url or company_url).
        Removes common sub-prefixes like 'careers.', 'jobs.', 'www.'.
        
        Args:
            url: The URL to extract domain from (e.g., 'https://careers.openai.com/apply/123')
        
        Returns:
            str: Clean domain (e.g., 'openai.com') or None if extraction fails
        """
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            prefixes_to_remove = ['careers.', 'jobs.', 'job.', 'hiring.', 'apply.', 'www.']
            for prefix in prefixes_to_remove:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # Validate domain has at least one dot
            if '.' not in domain:
                return None
            
            # Filter out ATS/HR systems and job aggregators (useless for Apollo search)
            ats_and_aggregator_domains = [
                # Job aggregators
                'indeed.com', 'ca.indeed.com', 'linkedin.com', 'glassdoor.com', 'ziprecruiter.com',
                # ATS systems
                'rippling.com', 'ats.rippling.com', 'greenhouse.io', 'lever.co', 'workday.com',
                'icims.com', 'smartrecruiters.com', 'bamboohr.com', 'jobvite.com',
                'ultipro.com', 'taleo.net', 'successfactors.com', 'myworkdayjobs.com'
            ]
            
            # Check if domain contains any of the blocked patterns
            for blocked in ats_and_aggregator_domains:
                if blocked in domain:
                    scraper_logger.debug(f"Skipping ATS/aggregator domain: {domain}")
                    return None
            
            scraper_logger.debug(f"Extracted domain: {domain} from {url}")
            return domain
            
        except Exception as e:
            scraper_logger.warning(f"Failed to extract domain from {url}: {e}")
            return None


    def clean_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception as e:
            scraper_logger.warning(f"HTML cleaning failed: {e}")
            return text
    
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
        skipped_count = 0
        failed_count = 0
        
        try:
            for i, job_data in enumerate(jobs, 1):
                try:
                    # Check if job already exists (by URL)
                    existing = db.query(Job).filter(Job.job_url == job_data["job_url"]).first()
                    
                    if existing:
                        scraper_logger.debug(f"Job {i}/{len(jobs)} already exists: {job_data['title']}")
                        skipped_count += 1
                        continue
                    
                    # Create new job
                    new_job = Job(**job_data)
                    db.add(new_job)
                    db.flush()  # Generate ID
                    job_data['id'] = new_job.id  # Update original dict with ID
                    
                    saved_count += 1
                    scraper_logger.info(f"Added job {i}/{len(jobs)}: {job_data['title']} at {job_data['company']}")
                    
                except Exception as job_error:
                    failed_count += 1
                    scraper_logger.error(f"Failed to add job {i}/{len(jobs)}: {job_error}", exc_info=True)
                    scraper_logger.error(f"Problematic job data keys: {list(job_data.keys())}")
                    continue
            
            db.commit()
            
            # Summary logging
            scraper_logger.info(f"Database save summary: {saved_count} saved, {skipped_count} skipped (duplicate), {failed_count} failed")
            
            if saved_count == 0 and skipped_count > 0:
                scraper_logger.warning(f"All {skipped_count} jobs already exist in database!")
            
        except Exception as e:
            db.rollback()
            scraper_logger.error(f"Database commit failed: {e}", exc_info=True)
        
        finally:
            db.close()
        
        return saved_count
    
    def get_recent_jobs(self, days: int = 3) -> List[Job]:
        """
        Get jobs posted within last N days
        Uses created_at as fallback if posted_date is NULL
        
        Args:
            days: Number of days to look back
        
        Returns:
            list: Job objects
        """
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            # Use created_at as fallback if posted_date is NULL
            jobs = db.query(Job).filter(
                (Job.posted_date >= cutoff_date) | 
                ((Job.posted_date == None) & (Job.created_at >= cutoff_date))
            ).all()
            scraper_logger.info(f"Retrieved {len(jobs)} jobs from last {days} days")
            return jobs
        finally:
            db.close()
    
    def get_all_jobs(self, limit: int = 100, exclude_applied: bool = True) -> List[Job]:
        """
        Get all jobs from database
        
        Args:
            limit: Maximum number of jobs to return
            exclude_applied: If True, exclude jobs that have been marked as applied
        
        Returns:
            list: Job objects
        """
        db = SessionLocal()
        try:
            query = db.query(Job)
            
            if exclude_applied:
                # Subquery to find IDs of jobs that have been applied to
                applied_job_ids = db.query(Application.job_id).filter(
                    Application.status == 'applied'
                ).distinct()
                
                # Filter out these jobs
                query = query.filter(Job.id.notin_(applied_job_ids))
            
            # Order by most recently created
            jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
            
            scraper_logger.info(f"Retrieved {len(jobs)} jobs from database (exclude_applied={exclude_applied})")
            return jobs
        finally:
            db.close()

    def mark_job_as_applied(self, job_id: int, applied: bool = True) -> bool:
        """
        Mark a job as applied (or unmark it)
        
        Args:
            job_id: ID of the job
            applied: True to mark as applied, False to remove application
            
        Returns:
            bool: Success status
        """
        db = SessionLocal()
        try:
            # Check if application exists
            application = db.query(Application).filter(Application.job_id == job_id).first()
            
            if applied:
                if application:
                    application.status = 'applied'
                    application.updated_at = datetime.utcnow()
                else:
                    new_app = Application(
                        job_id=job_id,
                        status='applied',
                        email_stage='manual_web', # creating via checkbox
                        created_at=datetime.utcnow()
                    )
                    db.add(new_app)
            else:
                # If unmarking, we set back to 'to_apply'
                if application:
                    application.status = 'to_apply'
            
            db.commit()
            return True
        except Exception as e:
            scraper_logger.error(f"Failed to update application status for job {job_id}: {e}")
            db.rollback()
            return False
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
