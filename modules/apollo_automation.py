# Apollo Automation Module
# Uses Playwright to scrape HR contacts from Apollo.io

import os
import re
import random
import time
import json
from typing import Optional, List, Dict
from playwright.sync_api import sync_playwright, Page

# Import database models
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modules.database import Job, HRContact, SessionLocal
from modules.logger_config import app_logger

# Storage for Playwright session (not Chrome, but a separate profile)
PLAYWRIGHT_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".playwright_data")


class ApolloAutomation:
    """
    Automates HR contact discovery on Apollo.io using Playwright.
    Maintains its own login session separate from your Chrome browser.
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.daily_limit = 30
        self.scraped_today = 0
        
        # Create data directory if needed
        os.makedirs(PLAYWRIGHT_DATA_DIR, exist_ok=True)
        
    def verify_company_match(self, job_company: str, apollo_company: str) -> bool:
        """
        Verify that the company found on Apollo matches the job's company.
        """
        if not job_company or not apollo_company:
            return False
            
        job_clean = job_company.lower().strip()
        apollo_clean = apollo_company.lower().strip()
        
        # Exact match
        if job_clean == apollo_clean:
            return True
        
        # Contains match
        if job_clean in apollo_clean or apollo_clean in job_clean:
            return True
        
        # Word-based match
        job_words = set(job_clean.split())
        apollo_words = set(apollo_clean.split())
        stopwords = {'inc', 'inc.', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co', 'the'}
        meaningful_common = (job_words & apollo_words) - stopwords
        
        return len(meaningful_common) >= 1
    
    def ensure_logged_in(self, page: Page) -> bool:
        """
        Check if logged in, if not prompt user to login.
        """
        page.goto("https://app.apollo.io/#/people")
        time.sleep(3)
        
        if "login" in page.url.lower():
            print("\n" + "=" * 60)
            print("🔐 APOLLO LOGIN REQUIRED")
            print("=" * 60)
            print("Please login to Apollo in the browser window that just opened.")
            print("After logging in successfully, press Enter here to continue...")
            print("=" * 60 + "\n")
            
            input("Press Enter after logging in...")
            
            # Check again
            time.sleep(2)
            if "login" in page.url.lower():
                print("❌ Still not logged in. Please try again.")
                return False
            
            print("✅ Login successful! Session saved for future runs.\n")
        
        return True
    
    def scrape_hr_contacts(self, job: Job, browser_context) -> List[Dict]:
        """
        Scrape HR contacts for a specific job from Apollo.io.
        """
        contacts = []
        
        app_logger.info(f"[Apollo] Starting scrape for: {job.company}")
        page = browser_context.new_page()
        
        try:
            contacts = self._search_and_extract(page, job)
        except Exception as e:
            app_logger.error(f"[Apollo] Scraping error: {e}")
        finally:
            page.close()
        
        return contacts
    
    def _search_and_extract(self, page: Page, job: Job) -> List[Dict]:
        """
        Perform the actual search and extraction on Apollo.
        """
        contacts = []
        
        # Build search URL
        search_params = []
        
        if job.company_domain:
            search_params.append(f"organizationDomains[]={job.company_domain}")
            app_logger.info(f"[Apollo] Using domain search: {job.company_domain}")
        else:
            company_encoded = job.company.replace(" ", "%20")
            search_params.append(f"organizationName={company_encoded}")
            app_logger.info(f"[Apollo] Using company name search: {job.company}")
        
        # Add recruiter titles
        recruiter_titles = self._get_recruiter_titles(job.department)
        for title in recruiter_titles:
            search_params.append(f"personTitles[]={title.replace(' ', '%20')}")
        
        search_url = f"https://app.apollo.io/#/people?{'&'.join(search_params)}"
        app_logger.info(f"[Apollo] Opening: {search_url}")
        
        page.goto(search_url)
        time.sleep(random.uniform(4, 6))
        
        # Wait for table rows
        try:
            page.wait_for_selector('[role="row"]', timeout=15000)
        except:
            app_logger.warning("[Apollo] No results found or page didn't load")
            return []
        
        rows = page.query_selector_all('[role="row"]')
        app_logger.info(f"[Apollo] Found {len(rows)} rows")
        
        if len(rows) <= 1:
            app_logger.info("[Apollo] No contacts found for this company")
            return []
        
        max_contacts = min(len(rows) - 1, 3)
        
        for i in range(1, max_contacts + 1):
            try:
                row = rows[i]
                contact = self._extract_contact_from_row(page, row, job)
                
                if contact and contact.get('email'):
                    contacts.append(contact)
                    app_logger.info(f"[Apollo] ✅ Extracted: {contact['name']} <{contact['email']}> - {contact['title']}")
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                app_logger.error(f"[Apollo] Error extracting contact {i}: {e}")
                continue
        
        return contacts
    
    def _extract_contact_from_row(self, page: Page, row, job: Job) -> Optional[Dict]:
        """
        Extract contact information from a single row.
        """
        contact = {
            'name': '',
            'email': None,
            'title': '',
            'company': ''
        }
        
        # Extract name
        name_el = row.query_selector('a[href*="#/people/"]')
        if name_el:
            contact['name'] = name_el.inner_text().strip()
        
        # Extract company
        company_el = row.query_selector('a[href*="#/organizations/"]')
        if company_el:
            contact['company'] = company_el.inner_text().strip()
        
        # Verify company match (if not using domain search)
        if not job.company_domain:
            if not self.verify_company_match(job.company, contact['company']):
                app_logger.warning(f"[Apollo] Company mismatch: {job.company} vs {contact['company']}")
                return None
        
        # Extract title - IMPROVED LOGIC
        # 1. Try to find the specific title element (usually has a specific class like 'zp_job-title' or similar in Apollo)
        # However, classes change, so we look for the text node containing keywords
        
        full_title = ''
        
        # Get all non-empty text nodes from the row
        # This is better than row.inner_text() which smashes everything together
        # We look for the text block that looks most like a job title
        try:
            # Evaluate JS to get text content of all elements individually
            text_blocks = row.evaluate("""(element) => {
                const results = [];
                function traverse(node) {
                    if (node.nodeType === 3) { # Text node
                        const text = node.textContent.trim();
                        if (text.length > 2) results.push(text);
                    } else {
                        for (const child of node.childNodes) traverse(child);
                    }
                }
                traverse(element);
                return results;
            }""")
            
            # Filter blocks that contain title keywords
            title_keywords = ['recruiter', 'talent', 'acquisition', 'hr ', 'human resources', 'people', 'staffing', 'sourcing']
            potential_titles = []
            
            for text in text_blocks:
                text_lower = text.lower()
                # Skip the person's name (contact['name']) or company name
                if contact['name'] and text in contact['name']: continue
                if contact['company'] and text in contact['company']: continue
                
                # Check for keywords
                if any(kw in text_lower for kw in title_keywords):
                    potential_titles.append(text)
            
            # Pick the best title (usually the longest one that isn't too long)
            if potential_titles:
                # Sort by length, prefer longer (more specific) titles
                potential_titles.sort(key=len, reverse=True)
                full_title = potential_titles[0]
                # If too long (> 60 chars), might be a bio or description, fallback
                if len(full_title) > 60: 
                    full_title = ''
                    
        except Exception as e:
            app_logger.warning(f"[Apollo] Error extracting exact title: {e}")

        # 2. Fallback to regex if specific extraction failed
        if full_title:
             contact['title'] = full_title
        else:
            row_text = row.inner_text()
            title_patterns = [
                r'((?:senior\s+)?(?:technical\s+)?recruiter)',
                r'(talent\s+acquisition(?:\s+\w+)?)',
                r'(hr\s+manager)',
                r'(human\s+resources\s+\w+)',
                r'(recruiting\s+\w+)',
                r'(people\s+operations\s+\w+)'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, row_text, re.IGNORECASE)
                if match:
                    contact['title'] = match.group(1).strip()
                    break
        
        # Check if email is already visible
        email_el = row.query_selector('a[href^="mailto:"]')
        
        if email_el:
            contact['email'] = email_el.get_attribute('href').replace('mailto:', '')
        else:
            # Click "Access email" button
            access_buttons = row.query_selector_all('a, button, span')
            for btn in access_buttons:
                try:
                    btn_text = btn.inner_text().lower().strip()
                    if 'access email' in btn_text or btn_text == 'access':
                        app_logger.info("[Apollo] Clicking 'Access email'...")
                        btn.click()
                        time.sleep(random.uniform(3, 5))
                        
                        email_el = row.query_selector('a[href^="mailto:"]')
                        if email_el:
                            contact['email'] = email_el.get_attribute('href').replace('mailto:', '')
                        else:
                            updated_text = row.inner_text()
                            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', updated_text)
                            if email_match:
                                contact['email'] = email_match.group(0)
                        break
                except:
                    continue
        
        return contact if contact['email'] else None
    
    def _get_recruiter_titles(self, department: str) -> List[str]:
        """Get relevant recruiter titles based on job department."""
        mapping = {
            'Engineering': ['Technical Recruiter', 'Engineering Recruiter'],
            'Marketing': ['Marketing Recruiter'],
            'Sales': ['Sales Recruiter'],
            'Design': ['Design Recruiter', 'Creative Recruiter'],
            'HR': ['HR Recruiter', 'Talent Acquisition'],
            'General': ['Recruiter', 'Talent Acquisition', 'HR Manager']
        }
        return mapping.get(department, mapping['General'])
    
    def save_contacts_to_db(self, job_id: int, contacts: List[Dict]) -> int:
        """Save extracted contacts to database."""
        db = SessionLocal()
        saved_count = 0
        
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                app_logger.error(f"[Apollo] Job {job_id} not found")
                return 0
            
            for contact_data in contacts:
                existing = db.query(HRContact).filter(
                    HRContact.email == contact_data['email']
                ).first()
                
                if existing:
                    app_logger.info(f"[Apollo] Email already exists: {contact_data['email']}")
                    continue
                
                new_contact = HRContact(
                    job_id=job_id,
                    company=job.company,
                    name=contact_data.get('name', ''),
                    email=contact_data['email'],
                    title=contact_data.get('title', 'Recruiter'),
                    contact_type='recruiter'
                )
                
                db.add(new_contact)
                saved_count += 1
                app_logger.info(f"[Apollo] Saved: {new_contact.name} <{new_contact.email}> - {new_contact.title}")
            
            job.hr_contact_status = 'found' if saved_count > 0 else 'not_found'
            db.commit()
            app_logger.info(f"[Apollo] Saved {saved_count} contacts for job {job_id}")
            
        except Exception as e:
            db.rollback()
            app_logger.error(f"[Apollo] Database error: {e}")
        finally:
            db.close()
        
        return saved_count
    
    def process_pending_jobs(self, limit: int = 5, job_id: int = None) -> Dict:
        """Process pending jobs that need HR contacts."""
        db = SessionLocal()
        results = {'processed': 0, 'found': 0, 'not_found': 0, 'errors': 0}
        
        try:
            if job_id:
                # Specific job requested - ignore status
                pending_jobs = db.query(Job).filter(Job.id == job_id).all()
                app_logger.info(f"[Apollo] Processing specific job ID: {job_id}")
            else:
                # Standard batch processing
                pending_jobs = db.query(Job).filter(
                    Job.hr_contact_status == 'pending'
                ).limit(limit).all()
            
            if not pending_jobs:
                app_logger.info("[Apollo] No pending jobs found")
                return results
            
            app_logger.info(f"[Apollo] Found {len(pending_jobs)} pending jobs")
            
            # Start Playwright with persistent context
            with sync_playwright() as p:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=PLAYWRIGHT_DATA_DIR,
                    headless=self.headless,
                    viewport={'width': 1280, 'height': 800}
                )
                
                # Ensure logged in
                temp_page = browser.new_page()
                if not self.ensure_logged_in(temp_page):
                    temp_page.close()
                    browser.close()
                    return results
                temp_page.close()
                
                # Process each job
                for job in pending_jobs:
                    if self.scraped_today >= self.daily_limit:
                        app_logger.warning(f"[Apollo] Daily limit reached ({self.daily_limit})")
                        break
                    
                    try:
                        contacts = self.scrape_hr_contacts(job, browser)
                        saved = self.save_contacts_to_db(job.id, contacts)
                        
                        results['processed'] += 1
                        if saved > 0:
                            results['found'] += 1
                        else:
                            results['not_found'] += 1
                        
                        self.scraped_today += 1
                        time.sleep(random.uniform(5, 10))
                        
                    except Exception as e:
                        app_logger.error(f"[Apollo] Error processing job {job.id}: {e}")
                        results['errors'] += 1
                
                browser.close()
                
        finally:
            db.close()
        
        return results


if __name__ == "__main__":
    automation = ApolloAutomation()
    results = automation.process_pending_jobs(limit=3)
    print(f"Results: {results}")
