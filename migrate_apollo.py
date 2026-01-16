# Database Migration Script for Apollo Agent
# Run this once to add new columns to existing tables

from modules.database import engine
from sqlalchemy import text

print("Starting database migration...")

with engine.connect() as conn:
    # Add new columns to jobs table
    try:
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company_domain VARCHAR(255)"))
        print("  - Added company_domain to jobs")
    except Exception as e:
        print(f"  - company_domain: {e}")
    
    try:
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS hr_contact_status VARCHAR(20) DEFAULT 'pending'"))
        print("  - Added hr_contact_status to jobs")
    except Exception as e:
        print(f"  - hr_contact_status: {e}")
    
    try:
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS department VARCHAR(100)"))
        print("  - Added department to jobs")
    except Exception as e:
        print(f"  - department: {e}")
    
    # Add new columns to hr_contacts table
    try:
        conn.execute(text("ALTER TABLE hr_contacts ADD COLUMN IF NOT EXISTS job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL"))
        print("  - Added job_id to hr_contacts")
    except Exception as e:
        print(f"  - job_id: {e}")
    
    try:
        conn.execute(text("ALTER TABLE hr_contacts ADD COLUMN IF NOT EXISTS contact_type VARCHAR(20) DEFAULT 'recruiter'"))
        print("  - Added contact_type to hr_contacts")
    except Exception as e:
        print(f"  - contact_type: {e}")
    
    try:
        conn.execute(text("ALTER TABLE hr_contacts ADD COLUMN IF NOT EXISTS department VARCHAR(100)"))
        print("  - Added department to hr_contacts")
    except Exception as e:
        print(f"  - department: {e}")
    
    conn.commit()
    print("\n✅ Database migration complete!")
