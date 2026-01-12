# Initialize Neon PostgreSQL Database
# Run this script once to create all tables

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.database import init_db, DATABASE_URL, DEMO_MODE
from modules.logger_config import app_logger

print("=" * 60)
print("Job Autopilot - Database Initialization")
print("=" * 60)

if DEMO_MODE:
    print("\n⚠️  WARNING: Running in DEMO mode (SQLite in-memory)")
    print("   DATABASE_URL not configured in .env file")
    print("   Data will be lost when application restarts!")
else:
    print(f"\n✅ Neon PostgreSQL detected")
    print(f"   URL: {DATABASE_URL[:50]}...")

print("\nCreating database tables...")

try:
    success = init_db()
    
    if success:
        print("\n✅ SUCCESS! All tables created:")
        print("   - jobs")
        print("   - resume_versions")
        print("   - hr_contacts")
        print("   - applications")
        print("   - cache_entries")
        print("\nDatabase is ready for Job Autopilot! 🚀")
    else:
        print("\n⚠️  WARNING: Table creation completed with warnings")
        print("   Check logs/app.log for details")

except Exception as e:
    print(f"\n❌ ERROR: Failed to initialize database")
    print(f"   Error: {e}")
    print("\nPlease check:")
    print("   1. DATABASE_URL is correct in .env file")
    print("   2. Neon database is accessible")
    print("   3. Database credentials are valid")
    sys.exit(1)

print("\n" + "=" * 60)
