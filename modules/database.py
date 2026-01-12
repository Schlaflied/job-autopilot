# Job Autopilot - Database Models
# SQLAlchemy ORM for Neon PostgreSQL

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ARRAY, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv
from modules.logger_config import app_logger

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    app_logger.warning("DATABASE_URL not found - running in DEMO mode (no database)")
    # Use SQLite in-memory database for demo mode
    DATABASE_URL = "sqlite:///:memory:"
    DEMO_MODE = True
else:
    DEMO_MODE = False

# Create engine
try:
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    app_logger.info(f"Database engine created ({'DEMO mode' if DEMO_MODE else 'Production mode'})")
except Exception as e:
    app_logger.error(f"Failed to create database engine: {e}")
    # Fallback to in-memory SQLite
    engine = create_engine("sqlite:///:memory:", echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    DEMO_MODE = True
    app_logger.warning("Using fallback in-memory database")

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
    ats_missing_keywords = Column(ARRAY(String))
    job_category = Column(String(50))  # 'edtech', 'ai_pm', 'automation'
    scraped_source = Column(String(20), default='apify')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume_versions = relationship("ResumeVersion", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class ResumeVersion(Base):
    """Resume versions table"""
    __tablename__ = "resume_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    resume_json = Column(JSON)  # JSONB in PostgreSQL
    pdf_path = Column(String)
    docx_path = Column(String)
    ats_optimized_keywords = Column(ARRAY(String))
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
