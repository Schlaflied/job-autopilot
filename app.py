# Job Autopilot - Flask API (Minimal MVP)
# REST API for Streamlit frontend

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from modules.logger_config import app_logger
from modules.database import init_db

app = Flask(__name__)
CORS(app)

# Initialize database
try:
    init_db()
    app_logger.info("Database initialized")
except Exception as e:
    app_logger.error(f"Database initialization failed: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Job Autopilot API is running"})

@app.route('/api/jobs/search', methods=['POST'])
def search_jobs():
    """Search jobs endpoint (placeholder)"""
    data = request.json
    app_logger.info(f"Job search request: {data}")
    return jsonify({"message": "Job search endpoint - to be implemented"})

@app.route('/api/resume/optimize', methods=['POST'])
def optimize_resume():
    """Resume optimization endpoint (placeholder)"""
    return jsonify({"message": "Resume optimization endpoint - to be implemented"})

@app.route('/api/email/generate', methods=['POST'])
def generate_email():
    """Email generation endpoint (placeholder)"""
    return jsonify({"message": "Email generation endpoint - to be implemented"})

# ============================================================
# Apollo Agent API Endpoints (For Chrome Extension)
# ============================================================

@app.route('/api/apollo/task/next', methods=['GET'])
def get_next_apollo_task():
    """
    Get the next pending HR search task for Chrome Extension.
    Returns a job that needs HR contact discovery.
    """
    from modules.database import Job, SessionLocal
    
    try:
        db = SessionLocal()
        
        # Find jobs with pending HR contact status
        pending_job = db.query(Job).filter(
            Job.hr_contact_status == 'pending',
            Job.company_domain.isnot(None)  # Must have domain for Apollo search
        ).first()
        
        if not pending_job:
            db.close()
            return jsonify({"status": "no_task", "message": "No pending HR search tasks"})
        
        task = {
            "status": "task_found",
            "task": {
                "job_id": pending_job.id,
                "company": pending_job.company,
                "company_domain": pending_job.company_domain,
                "job_title": pending_job.title,
                "department": pending_job.department or "General",
                "job_description": pending_job.description[:500] if pending_job.description else ""
            }
        }
        
        db.close()
        app_logger.info(f"Apollo task assigned: Job {pending_job.id} - {pending_job.company}")
        return jsonify(task)
        
    except Exception as e:
        app_logger.error(f"Error fetching Apollo task: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/apollo/task/complete', methods=['POST'])
def complete_apollo_task():
    """
    Receive HR contact data from Chrome Extension and save to database.
    
    Expected payload:
    {
        "job_id": 123,
        "contacts": [
            {"name": "John Doe", "email": "john@company.com", "title": "Technical Recruiter"},
            {"name": "Jane Smith", "email": "jane@company.com", "title": "HR Manager"}
        ],
        "status": "found" | "not_found"
    }
    """
    from modules.database import Job, HRContact, SessionLocal
    from datetime import datetime
    
    data = request.json
    
    if not data or 'job_id' not in data:
        return jsonify({"status": "error", "message": "Missing job_id"}), 400
    
    try:
        db = SessionLocal()
        
        job = db.query(Job).filter(Job.id == data['job_id']).first()
        if not job:
            db.close()
            return jsonify({"status": "error", "message": "Job not found"}), 404
        
        # Update job HR contact status
        job.hr_contact_status = data.get('status', 'not_found')
        
        # Save contacts if found
        contacts_saved = 0
        if data.get('contacts') and data.get('status') == 'found':
            for contact_data in data['contacts']:
                # Check if email already exists
                existing = db.query(HRContact).filter(HRContact.email == contact_data['email']).first()
                if existing:
                    continue
                
                new_contact = HRContact(
                    company=job.company,
                    name=contact_data.get('name'),
                    email=contact_data['email'],
                    title=contact_data.get('title'),
                    source='apollo',
                    job_id=job.id,
                    contact_type='recruiter' if 'recruiter' in contact_data.get('title', '').lower() else 'hiring_manager',
                    department=job.department,
                    imported_at=datetime.utcnow()
                )
                db.add(new_contact)
                contacts_saved += 1
        
        db.commit()
        db.close()
        
        app_logger.info(f"Apollo task completed: Job {data['job_id']} - {contacts_saved} contacts saved")
        return jsonify({
            "status": "success",
            "job_id": data['job_id'],
            "contacts_saved": contacts_saved
        })
        
    except Exception as e:
        app_logger.error(f"Error completing Apollo task: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    app_logger.info(f"Starting Flask API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
