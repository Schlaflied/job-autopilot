# Job Autopilot - LinkedIn HR Contact Scraper
# Multi-account rotation strategy with undetected-chromedriver

import os
import time
import random
import pickle
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from modules.database import SessionLocal, HRContact
from modules.cache_manager import cache_manager
from modules.logger_config import scraper_logger

load_dotenv()

class LinkedInScraper:
    """
    LinkedIn HR contact scraper with multi-account rotation
    
    Strategy:
    - Use 2-3 burner LinkedIn accounts
    - Rotate accounts (max 10 companies/day per account)
    - Random delays (30-60s between searches)
    - Save sessions to avoid frequent logins
    """
    
    def __init__(self):
        self.accounts = self._load_accounts()
        self.current_account_index = 0
        self.session_dir = "data/sessions"
        os.makedirs(self.session_dir, exist_ok=True)
        
        self.driver = None
        self.wait = None
        
        scraper_logger.info(f"LinkedIn scraper initialized with {len(self.accounts)} accounts")
    
    def _load_accounts(self) -> List[Dict]:
        """Load LinkedIn accounts from environment"""
        accounts = []
        
        for i in range(1, 4):  # Support up to 3 accounts
            email = os.getenv(f"LINKEDIN_ACCOUNT_{i}_EMAIL")
            password = os.getenv(f"LINKEDIN_ACCOUNT_{i}_PASSWORD")
            
            if email and password:
                accounts.append({
                    "email": email,
                    "password": password,
                    "index": i,
                    "searches_today": 0,
                    "last_used": None
                })
        
        if not accounts:
            scraper_logger.warning("No LinkedIn accounts configured")
        
        return accounts
    
    def _get_next_account(self) -> Optional[Dict]:
        """Get next available account (round-robin + daily limit check)"""
        if not self.accounts:
            return None
        
        # Check if current account hit daily limit
        for _ in range(len(self.accounts)):
            account = self.accounts[self.current_account_index]
            
            # Reset counter if it's a new day
            if account['last_used']:
                if account['last_used'].date() < datetime.now().date():
                    account['searches_today'] = 0
            
            # Check daily limit (10 per account)
            if account['searches_today'] < 10:
                scraper_logger.info(f"Using account #{account['index']} ({account['searches_today']}/10 today)")
                return account
            
            # Move to next account
            self.current_account_index = (self.current_account_index + 1) % len(self.accounts)
        
        scraper_logger.error("All LinkedIn accounts hit daily limit!")
        return None
    
    def _init_driver(self) -> bool:
        """Initialize undetected Chrome driver"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            # options.add_argument('--headless')  # Comment out for debugging
            
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            scraper_logger.info("Chrome driver initialized")
            return True
        
        except Exception as e:
            scraper_logger.error(f"Failed to initialize driver: {e}")
            return False
    
    def _login(self, account: Dict) -> bool:
        """
        Login to LinkedIn with session persistence
        
        Args:
            account: Account credentials dict
        
        Returns:
            bool: Login success
        """
        session_file = os.path.join(self.session_dir, f"linkedin_{account['index']}.pkl")
        
        # Try to load existing session
        if os.path.exists(session_file):
            try:
                self.driver.get("https://www.linkedin.com/feed/")
                time.sleep(2)
                
                with open(session_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                
                self.driver.refresh()
                time.sleep(3)
                
                # Check if still logged in
                if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                    scraper_logger.info(f"Restored session for account #{account['index']}")
                    return True
            
            except Exception as e:
                scraper_logger.warning(f"Session restore failed: {e}")
        
        # Fresh login
        try:
            scraper_logger.info(f"Performing fresh login for account #{account['index']}")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(account['email'])
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(account['password'])
            
            # Click login
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            time.sleep(5)
            
            # Check for verification/CAPTCHA
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                scraper_logger.warning("⚠️ LinkedIn verification required! Please complete manually...")
                input("Press Enter after completing verification...")
            
            # Save session
            cookies = self.driver.get_cookies()
            with open(session_file, 'wb') as f:
                pickle.dump(cookies, f)
            
            scraper_logger.info("Login successful, session saved")
            return True
        
        except Exception as e:
            scraper_logger.error(f"Login failed: {e}")
            return False
    
    def find_hr_contact(self, company_name: str, job_title: str = None) -> Optional[Dict]:
        """
        Search for HR/Hiring Manager at company
        
        Args:
            company_name: Company name to search
            job_title: Optional job title for context
        
        Returns:
            dict: HR contact info or None
        """
        # Check cache first
        cache_key = f"hr_{company_name.lower().replace(' ', '_')}"
        cached = cache_manager.get_cached_hr_contact(cache_key)
        if cached:
            scraper_logger.info(f"Using cached HR contact for {company_name}")
            return cached
        
        # Get available account
        account = self._get_next_account()
        if not account:
            scraper_logger.error("No available LinkedIn accounts")
            return None
        
        # Initialize driver if needed
        if not self.driver:
            if not self._init_driver():
                return None
        
        # Login
        if not self._login(account):
            return None
        
        try:
            # Search for HR at company
            search_query = f"{company_name} recruiter OR hiring manager OR HR"
            if job_title:
                search_query += f" OR {job_title}"
            
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query}"
            self.driver.get(search_url)
            
            # Random delay (30-60s to avoid detection)
            delay = random.randint(30, 60)
            scraper_logger.info(f"Searching LinkedIn... (delay: {delay}s)")
            time.sleep(delay)
            
            # Extract first result
            try:
                first_result = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".entity-result"))
                )
                
                # Extract name
                name_element = first_result.find_element(By.CSS_SELECTOR, ".entity-result__title-text a span")
                name = name_element.text.strip()
                
                # Extract title
                title_element = first_result.find_element(By.CSS_SELECTOR, ".entity-result__primary-subtitle")
                title = title_element.text.strip()
                
                # Extract LinkedIn URL
                linkedin_url = first_result.find_element(By.CSS_SELECTOR, ".entity-result__title-text a").get_attribute("href")
                
                # Try to get email (limited without premium)
                # Note: Email extraction requires LinkedIn Premium or contact info access
                email = f"{name.lower().replace(' ', '.')}@{company_name.lower().replace(' ', '')}.com"
                
                hr_contact = {
                    "company": company_name,
                    "name": name,
                    "title": title,
                    "email": email,  # Estimated email
                    "linkedin_url": linkedin_url,
                    "source": "linkedin_scraper",
                    "quality_score": 70  # Medium confidence (estimated email)
                }
                
                # Cache result
                cache_manager.cache_hr_contact(cache_key, hr_contact, ttl_days=30)
                
                # Update account usage
                account['searches_today'] += 1
                account['last_used'] = datetime.now()
                
                scraper_logger.info(f"Found HR contact: {name} ({title}) at {company_name}")
                return hr_contact
            
            except (TimeoutException, NoSuchElementException):
                scraper_logger.warning(f"No HR contacts found for {company_name}")
                return None
        
        except Exception as e:
            scraper_logger.error(f"LinkedIn search failed: {e}", exc_info=True)
            return None
    
    def save_to_database(self, hr_contact: Dict) -> bool:
        """Save HR contact to database"""
        try:
            db = SessionLocal()
            
            # Check if already exists
            existing = db.query(HRContact).filter(
                HRContact.email == hr_contact['email']
            ).first()
            
            if existing:
                scraper_logger.debug(f"HR contact already in database: {hr_contact['email']}")
                db.close()
                return True
            
            # Create new
            new_contact = HRContact(**hr_contact)
            db.add(new_contact)
            db.commit()
            
            scraper_logger.info(f"Saved HR contact to database: {hr_contact['name']}")
            db.close()
            return True
        
        except Exception as e:
            scraper_logger.error(f"Failed to save HR contact: {e}")
            return False
    
    def close(self):
        """Close driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            scraper_logger.info("LinkedIn scraper closed")

# Global instance
linkedin_scraper = LinkedInScraper()

if __name__ == "__main__":
    # Test
    scraper = LinkedInScraper()
    
    contact = scraper.find_hr_contact("EdTech Solutions Inc.", "Instructional Designer")
    if contact:
        print(f"Found: {contact['name']} - {contact['email']}")
        scraper.save_to_database(contact)
    
    scraper.close()
