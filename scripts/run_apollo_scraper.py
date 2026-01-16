#!/usr/bin/env python
"""
Apollo HR Scraper - Standalone Script
Run this to automatically find HR contacts for pending jobs.

Usage:
    python scripts/run_apollo_scraper.py [--limit N] [--headless]
    
First run will prompt for Apollo login. Session is saved for future runs.
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.apollo_automation import ApolloAutomation
from modules.logger_config import app_logger


def main():
    parser = argparse.ArgumentParser(description='Apollo HR Contact Scraper')
    parser.add_argument('--limit', type=int, default=5, help='Max jobs to process (default: 5)')
    parser.add_argument('--job-id', type=int, help='Specific Job ID to process')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (not recommended)')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🚀 Apollo HR Contact Scraper")
    print("=" * 60)
    print(f"📊 Job Limit: {args.limit}")
    print(f"🖥️  Headless: {args.headless}")
    print("=" * 60)
    
    print("\n📝 Note: First run will require Apollo login.")
    print("   A browser window will open - log in there.\n")
    
    try:
        automation = ApolloAutomation(headless=args.headless)
        
        print("🔍 Processing pending jobs...\n")
        results = automation.process_pending_jobs(limit=args.limit, job_id=args.job_id)
        
        print("\n" + "=" * 60)
        print("📊 Results Summary")
        print("=" * 60)
        print(f"   Processed: {results['processed']}")
        print(f"   ✅ Found HR:  {results['found']}")
        print(f"   ❌ Not Found: {results['not_found']}")
        print(f"   ⚠️  Errors:    {results['errors']}")
        print("=" * 60)
        
        if results['found'] > 0:
            print("\n✅ HR contacts saved to database!")
            print("   Check Streamlit Email Center to see them.\n")
        else:
            print("\n💡 No HR contacts found. This could mean:")
            print("   - The companies are too small (not in Apollo)")
            print("   - No recruiters found for those companies")
            print("   - Try with larger companies\n")
        
    except Exception as e:
        app_logger.error(f"Script error: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
