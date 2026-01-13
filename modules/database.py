# Job Autopilot - Database Models
# SQLAlchemy ORM for Neon PostgreSQL

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ARRAY, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Dict
import os
from dotenv import load_dotenv
from modules.logger_config import app_logger

# Load environment variables
load_dotenv()

# ============================================================
# Database Configuration (Phase 2 - Resume Export Feature)
# Supports: SQLite (local), PostgreSQL (cloud/local), MySQL
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # No DATABASE_URL → Fallback to local SQLite
    DATABASE_URL = "sqlite:///data/job_autopilot.db"
    app_logger.warning("⚠️  No DATABASE_URL found, using local SQLite")
    app_logger.info(f"📂 Database file: data/job_autopilot.db")
    DEMO_MODE = False
    DB_TYPE = "sqlite"
else:
    DEMO_MODE = False
    # Detect database type
    if DATABASE_URL.startswith("sqlite"):
        DB_TYPE = "sqlite"
    elif DATABASE_URL.startswith("postgresql"):
        DB_TYPE = "postgresql"
    elif DATABASE_URL.startswith("mysql"):
        DB_TYPE = "mysql"
    else:
        DB_TYPE = "unknown"

# Create engine
try:
    # Ensure data directory exists for SQLite
    if DB_TYPE == "sqlite" and "data/" in DATABASE_URL:
        os.makedirs("data", exist_ok=True)
    
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True  # Check connection health before using
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    # Don't print full DATABASE_URL (may contain password)
    safe_url = DATABASE_URL.split("@")[0] if "@" in DATABASE_URL else DATABASE_URL
    app_logger.info(f"✅ Database connected: {DB_TYPE.upper()} ({safe_url})")
    
except Exception as e:
    app_logger.error(f"Failed to create database engine: {e}")
    # Fallback to SQLite
    app_logger.warning("⚠️  Falling back to SQLite in-memory database")
    engine = create_engine("sqlite:///:memory:", echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    DEMO_MODE = True
    DB_TYPE = "sqlite"

def get_database_info() -> Dict:
    """
    Get human-readable database information
    For display in Streamlit Settings page
    
    Returns:
        dict: Database type, location, and suitability info
    """
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/job_autopilot.db")
    
    if db_url.startswith("sqlite"):
        db_file = db_url.replace("sqlite:///", "")
        if db_file == ":memory:":
            return {
                "type": "SQLite",
                "location": "In-Memory (Demo Mode)",
                "file": ":memory:",
                "suitable_for": "Testing only",
                "persistent": False
            }
        else:
            return {
                "type": "SQLite",
                "location": "Local",
                "file": db_file,
                "suitable_for": "Personal use, single user",
                "persistent": True
            }
    
    elif db_url.startswith("postgresql"):
        host = db_url.split("@")[1].split("/")[0] if "@" in db_url else "localhost"
        
        if "neon" in host or "supabase" in host:
            provider = "Neon/Supabase"
            location = "Cloud"
        else:
            provider = "PostgreSQL"
            location = "Local/Self-hosted"
        
        return {
            "type": "PostgreSQL",
            "location": location,
            "provider": provider,
            "suitable_for": "Production, multi-device, high performance",
            "persistent": True
        }
    
    else:
        return {
            "type": "Unknown",
            "location": "Unknown",
            "suitable_for": "Unknown",
            "persistent": False
        }

# ============================================================
# Models
# ============================================================

class Job(Base):
    """Job postings table"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False, index=True)
    description = Column(Text)
    location = Column(String)
    salary = Column(String)
    is_remote = Column(Boolean, default=False)
    posted_date = Column(DateTime)
    job_url = Column(String, unique=True, nullable=False)
    match_score = Column(Integer)  # 0-10
    match_reasoning = Column(Text)
    ats_score = Column(Integer)  # 0-100
    ats_missing_keywords = Column(JSON)  # Store as JSON instead of ARRAY for compatibility
    job_category = Column(String(50))  # 'edtech', 'ai_pm', 'automation'
    scraped_source = Column(String(20), default='apify')
    
    # NEW: Resume Export fields (Phase 2)
    selected_template = Column(String(50))  # e.g., "classic_single_column"
    resume_version_id = Column(Integer, ForeignKey("resume_versions.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume_versions = relationship("ResumeVersion", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class ResumeVersion(Base):
    """
    Resume versions table (Phase 2 - Resume Export Feature)
    Stores all tailored resume versions with templates and ATS scores
    """
    __tablename__ = "resume_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    resume_json = Column(JSON)  # JSONB in PostgreSQL
    pdf_path = Column(String)
    docx_path = Column(String)
    
    # NEW: Template and compression info
    template_name = Column(String(50))  # e.g., "classic_single_column"
    compression_mode = Column(String(20))  # 'aggressive', 'balanced', 'conservative'
    word_count = Column(Integer)  # Approximate word count
    
    # NEW: ATS optimization
    ats_score = Column(Integer)  # 0-100
    ats_optimized_keywords = Column(JSON)  # Matched keywords
    ats_missing_keywords = Column(JSON)  # Missing keywords
    
    # NEW: Privacy compliance
    user_consent = Column(Boolean, default=False)  # User agreed to store data
    retention_days = Column(Integer, default=90)  # Auto-delete after X days
    
    version_number = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="resume_versions")
    applications = relationship("Application", back_populates="resume_version")

class HRContact(Base):
    """HR contacts table"""
    __tablename__ = "hr_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False, index=True)
    name = Column(String)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)
    title = Column(String)
    linkedin_url = Column(String)
    source = Column(String(20), default='selenium')  # 'selenium', 'lusha', 'website', 'manual'
    quality_score = Column(Integer)  # 0-100
    imported_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="hr_contact")

class Application(Base):
    """Job applications tracking table"""
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    resume_version_id = Column(Integer, ForeignKey("resume_versions.id"))
    hr_contact_id = Column(Integer, ForeignKey("hr_contacts.id"))
    gmail_draft_id = Column(String)
    gmail_thread_id = Column(String)  # For reply tracking
    email_stage = Column(String(20), default='initial')  # 'initial_draft', 'initial_sent', 'replied', 'followup_sent'
    status = Column(String(20), default='to_apply', index=True)
    last_reply_check = Column(DateTime)
    hr_replied = Column(Boolean, default=False)
    reply_content = Column(Text)
    notes = Column(Text)
    sent_at = Column(DateTime)
    replied_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    resume_version = relationship("ResumeVersion", back_populates="applications")
    hr_contact = relationship("HRContact", back_populates="applications")

class CacheEntry(Base):
    """Cache backup table (Redis → PostgreSQL)"""
    __tablename__ = "cache_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    cache_value = Column(JSON)
    cache_type = Column(String(50))  # 'job', 'hr_contact', 'ats_analysis'
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)

# ============================================================
# Database Initialization
# ============================================================

def init_db():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        if DEMO_MODE:
            app_logger.info("Database tables created (DEMO mode - in-memory)")
        else:
            app_logger.info("Database tables created successfully")
        return True
    except Exception as e:
        app_logger.error(f"Failed to create database tables: {e}", exc_info=True)
        if not DEMO_MODE:
            raise
        return False

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    # Test connection
    init_db()
    app_logger.info("Database connection successful!")
