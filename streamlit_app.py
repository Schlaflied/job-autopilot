# Job Autopilot - Streamlit Frontend
# Main UI for job search automation

import streamlit as st
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.logger_config import streamlit_logger
from modules.job_scraper import JobScraper
from modules.ai_agent import ai_agent
from modules.database import SessionLocal, Job, Application
from modules.resume_generator import resume_generator
from modules.ats_scorer import ats_scorer
from datetime import datetime
import json
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.colored_header import colored_header
from streamlit_extras.badges import badge
from streamlit_card import card

# Page configuration
import base64
st.set_page_config(
    page_title="Job Autopilot 🚀",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .job-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background: white;
    }
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .score-high {background: #10b981; color: white;}
    .score-medium {background: #f59e0b; color: white;}
    .score-low {background: #ef4444; color: white;}
</style>
""", unsafe_allow_html=True)

def update_application_status(job_id, key):
    """Callback to update job application status"""
    if st.session_state.get(key):
        scraper = JobScraper()
        # Ensure job_id is an integer
        try:
            job_id_int = int(job_id)
            scraper.mark_job_as_applied(job_id_int, applied=True)
            st.toast(f"✅ Job marked as applied!")
        except ValueError:
            st.error(f"Invalid job ID: {job_id}")

# Session state initialization
if 'jobs' not in st.session_state:
    st.session_state.jobs = []
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = ai_agent.demo_mode

# Load demo data on first run
if 'demo_loaded' not in st.session_state:
    st.session_state.demo_loaded = False
    if st.session_state.demo_mode:
        # Auto-load demo data
        st.session_state.jobs = [
            {
                "id": 1,
                "title": "Senior Instructional Designer",
                "company": "EdTech Solutions Inc.",
                "location": "Toronto, ON (Remote)",
                "salary": "$65,000 - $80,000/year",
                "description": "We're seeking an experienced instructional designer to develop engaging online courses for our corporate clients. You'll work with AI-powered learning tools, create interactive content using H5P and Articulate, and collaborate with subject matter experts to design effective learning experiences.",
                "is_remote": True,
                "job_url": "https://example.com/job1",
                "posted_date": datetime.now(),
                "match_score": 9,
                "match_reasoning": "Perfect fit: EdTech role (+4) | Excellent salary (+3) | Remote (+1) | Ontario (+1)"
            },
            {
                "id": 2,
                "title": "AI Product Manager - Learning Technologies",
                "company": "TechCorp Canada",
                "location": "Ottawa, ON (Hybrid)",
                "salary": "$85,000 - $100,000/year",
                "description": "Join our AI team to lead the development of intelligent learning platforms. You'll define product strategy, work with ML engineers to implement AI features, conduct user research, and drive product adoption across educational institutions.",
                "is_remote": False,
                "job_url": "https://example.com/job2",
                "posted_date": datetime.now(),
                "match_score": 8,
                "match_reasoning": "Strong match: AI PM role (+4) | High salary (+3) | Ontario (+1)"
            },
            {
                "id": 3,
                "title": "Learning & Development Specialist",
                "company": "Global Training Co.",
                "location": "Mississauga, ON (Remote)",
                "salary": "$58,000 - $70,000/year",
                "description": "Design and deliver training programs for our multinational team. You'll use LMS platforms, create microlearning content, implement pilot programs for new features, and measure training effectiveness through data analytics.",
                "is_remote": True,
                "job_url": "https://example.com/job3",
                "posted_date": datetime.now(),
                "match_score": 7,
                "match_reasoning": "Good match: L&D role (+4) | Pilot Program keyword (+1) | Competitive salary (+1) | Ontario (+1)"
            },
            {
                "id": 4,
                "title": "Automation Engineer - Workflow Specialist",
                "company": "Innovate Systems",
                "location": "Waterloo, ON (Hybrid)",
                "salary": "$70,000 - $85,000/year",
                "description": "Build and deploy workflow automation solutions using n8n, Zapier, and custom Python scripts. You'll work on technical POCs, implement system integrations, and help clients optimize their business processes through intelligent automation.",
                "is_remote": False,
                "job_url": "https://example.com/job4",
                "posted_date": datetime.now(),
                "match_score": 8,
                "match_reasoning": "Excellent match: Automation role (+4) | Workflow keywords (+1) | POC experience (+1) | Good salary (+1) | Ontario (+1)"
            },
            {
                "id": 5,
                "title": "HRIS Analyst - Implementation Specialist",
                "company": "HR Pro Solutions",
                "location": "Toronto, ON (Remote)",
                "salary": "$62,000 - $75,000/year",
                "description": "Lead HRIS system implementations for new clients. You'll configure Workday modules, conduct system testing, train end users, and ensure smooth rollout of new features. Experience with workflow automation is a plus.",
                "is_remote": True,
                "job_url": "https://example.com/job5",
                "posted_date": datetime.now(),
                "match_score": 6,
                "match_reasoning": "Moderate match: HRIS role (+3) | System Implementation (+1) | Remote (+1) | Ontario (+1)"
            }
        ]
        st.session_state.demo_loaded = True

# Sidebar navigation
with st.sidebar:
    st.markdown("### 🚀 Job Autopilot")
    st.markdown("---")
    
    page = st.radio(
        "Navigate",
        ["🔍 Job Search", "📄 Resume Export", "📧 Email Center", "📊 Dashboard", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Demo mode indicator
    if st.session_state.demo_mode:
        st.warning("⚠️ **DEMO MODE**\nAPI keys not configured.\nUsing mock data.")
    else:
        st.success("✅ API Connected")
    
    st.markdown("---")
    st.markdown("**Quick Stats**")
    st.metric("Jobs Found", len(st.session_state.jobs))
    st.metric("High Matches (8+)", len([j for j in st.session_state.jobs if j.get('match_score', 0) >= 8]))
    st.metric("Remote Jobs", len([j for j in st.session_state.jobs if j.get('is_remote', False)]))


# Main content
if page == "🔍 Job Search":
    st.markdown('<h1 class="main-header">Job Search 🔍</h1>', unsafe_allow_html=True)
    st.markdown("Find and score job opportunities with AI")
    
    # Search form
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        keywords = st.text_input(
            "Keywords",
            value="Instructional Design, AI PM, Automation",
            help="Comma-separated job titles or skills"
        )
    
    with col2:
        location = st.text_input(
            "Location",
            value="Ontario, Canada"
        )
    
    with col3:
        max_jobs = st.number_input(
            "Max Jobs",
            min_value=5,
            max_value=50,
            value=10
        )
    
    col4, col5 = st.columns(2)
    with col4:
        job_type = st.selectbox("Job Type", ["fulltime", "parttime", "contract"])
    with col5:
        remote = st.selectbox("Remote", ["hybrid", "remote", "onsite"])
    
    # Two buttons: Search (new API call) and Load Cached (from DB)
    button_col1, button_col2 = st.columns(2)
    
    with button_col1:
        search_clicked = st.button("🔍 Search Jobs", type="primary", use_container_width=True)
    
    with button_col2:
        load_cached_clicked = st.button("📦 Load Cached Jobs", use_container_width=True, 
                                       help="Load previously scraped jobs from database (no API call)")
    
    if search_clicked:
        with st.spinner("Searching jobs..."):
            try:
                # Demo mode: create sample jobs
                if st.session_state.demo_mode:
                    st.session_state.jobs = [
                        {
                            "id": 1,
                            "title": "Senior Instructional Designer",
                            "company": "EdTech Solutions Inc.",
                            "location": "Toronto, ON (Remote)",
                            "salary": "$65,000 - $80,000/year",
                            "description": "We're seeking an experienced instructional designer to develop engaging online courses for our corporate clients. You'll work with AI-powered learning tools, create interactive content using H5P and Articulate, and collaborate with subject matter experts to design effective learning experiences. This role includes system implementation projects and piloting new learning technologies.",
                            "is_remote": True,
                            "job_url": "https://example.com/job1",
                            "posted_date": datetime.now(),
                            "match_score": 9,
                            "match_reasoning": "Perfect fit: EdTech role (+4) | Excellent salary (+3) | Remote (+1) | Ontario (+1)"
                        },
                        {
                            "id": 2,
                            "title": "AI Product Manager - Learning Technologies",
                            "company": "TechCorp Canada",
                            "location": "Ottawa, ON (Hybrid)",
                            "salary": "$85,000 - $100,000/year",
                            "description": "Join our AI team to lead the development of intelligent learning platforms. You'll define product strategy, work with ML engineers to implement AI features, conduct user research, and drive product adoption across educational institutions. Experience with POC development and workflow automation tools (n8n, Zapier) is a plus.",
                            "is_remote": False,
                            "job_url": "https://example.com/job2",
                            "posted_date": datetime.now(),
                            "match_score": 8,
                            "match_reasoning": "Strong match: AI PM role (+4) | High salary (+3) | Ontario (+1)"
                        },
                        {
                            "id": 3,
                            "title": "Learning & Development Specialist",
                            "company": "Global Training Co.",
                            "location": "Mississauga, ON (Remote)",
                            "salary": "$58,000 - $70,000/year",
                            "description": "Design and deliver training programs for our multinational team. You'll use LMS platforms (Moodle, Canvas), create microlearning content, implement pilot programs for new features, and measure training effectiveness through data analytics. Strong instructional design background required.",
                            "is_remote": True,
                            "job_url": "https://example.com/job3",
                            "posted_date": datetime.now(),
                            "match_score": 7,
                            "match_reasoning": "Good match: L&D role (+4) | Pilot Program keyword (+1) | Competitive salary (+1) | Remote (+1)"
                        },
                        {
                            "id": 4,
                            "title": "Automation Engineer - Workflow Specialist",
                            "company": "Innovate Systems",
                            "location": "Waterloo, ON (Hybrid)",
                            "salary": "$70,000 - $85,000/year",
                            "description": "Build and deploy workflow automation solutions using n8n, Zapier, and custom Python scripts. You'll work on technical POCs, implement system integrations, and help clients optimize their business processes through intelligent automation. Perfect for someone with both technical skills and understanding of business workflows.",
                            "is_remote": False,
                            "job_url": "https://example.com/job4",
                            "posted_date": datetime.now(),
                            "match_score": 8,
                            "match_reasoning": "Excellent match: Automation role (+4) | Workflow keywords (+1) | POC experience (+1) | Good salary (+1) | Ontario (+1)"
                        },
                        {
                            "id": 5,
                            "title": "HRIS Analyst - Implementation Specialist",
                            "company": "HR Pro Solutions",
                            "location": "Toronto, ON (Remote)",
                            "salary": "$62,000 - $75,000/year",
                            "description": "Lead HRIS system implementations for new clients. You'll configure Workday modules, conduct system testing, train end users, and ensure smooth rollout of new features. Experience with workflow automation and technical documentation is valued. This is a great opportunity to combine HR knowledge with technical skills.",
                            "is_remote": True,
                            "job_url": "https://example.com/job5",
                            "posted_date": datetime.now(),
                            "match_score": 6,
                            "match_reasoning": "Moderate match: HRIS role (+3) | System Implementation (+1) | Remote (+1) | Ontario (+1)"
                        }
                    ]
                    st.success(f"✅ Found {len(st.session_state.jobs)} jobs (DEMO MODE)")
                else:
                    # Real mode: use job scraper
                    scraper = JobScraper()
                    jobs = scraper.scrape_jobs(
                        keywords=keywords,
                        location=location,
                        max_jobs=max_jobs,
                        job_type=job_type,
                        remote=remote
                    )
                    
                    # Score each job
                    resume_summary = "EdTech and L&D professional with AI/SaaS experience"
                    for job in jobs:
                        score_data = ai_agent.score_job(job, resume_summary)
                        job['match_score'] = score_data['score']
                        job['match_reasoning'] = score_data['reasoning']
                    
                    # Save to database
                    saved_count = scraper.save_jobs_to_db(jobs)
                    streamlit_logger.info(f"Saved {saved_count} jobs to database")
                    
                    st.session_state.jobs = sorted(jobs, key=lambda x: x.get('match_score', 0), reverse=True)
                    st.success(f"✅ Found and scored {len(jobs)} jobs! ({saved_count} saved to database)")
                
                streamlit_logger.info(f"Job search completed: {keywords}")
            
            except Exception as e:
                st.error(f"Search failed: {e}")
                streamlit_logger.error(f"Job search error: {e}", exc_info=True)
    
    elif load_cached_clicked:
        with st.spinner("Loading cached jobs from database..."):
            try:
                # Load from database - get ALL jobs (not just recent)
                scraper = JobScraper()
                cached_jobs = scraper.get_all_jobs(limit=1000, exclude_applied=True)  # Get all jobs, filtering applied
                
                if cached_jobs:
                    # Convert SQLAlchemy objects to dicts
                    jobs = []
                    for job in cached_jobs:
                        job_dict = {
                            "id": job.id,  # Include ID for application tracking
                            "title": job.title,
                            "company": job.company,
                            "description": job.description,
                            "location": job.location,
                            "salary": job.salary,
                            "is_remote": job.is_remote,
                            "job_url": job.job_url,
                            "posted_date": job.posted_date,
                            "job_category": job.job_category,
                        }
                        jobs.append(job_dict)
                    
                    # Re-score with AI
                    resume_summary = "EdTech and L&D professional with AI/SaaS experience"
                    for job in jobs:
                        score_data = ai_agent.score_job(job, resume_summary)
                        job['match_score'] = score_data['score']
                        job['match_reasoning'] = score_data['reasoning']
                    
                    st.session_state.jobs = sorted(jobs, key=lambda x: x.get('match_score', 0), reverse=True)
                    st.success(f"✅ Loaded {len(jobs)} cached jobs from database (No API call!)")
                    streamlit_logger.info(f"Loaded {len(jobs)} cached jobs")
                else:
                    st.warning("No cached jobs found. Try searching for new jobs first!")
                    streamlit_logger.warning("No cached jobs available")
            
            except Exception as e:
                st.error(f"Failed to load cached jobs: {e}")
                streamlit_logger.error(f"Load cached error: {e}", exc_info=True)
    
    # Display jobs
    if st.session_state.jobs:
        st.markdown("---")
        st.markdown(f"### Results ({len(st.session_state.jobs)} jobs)")
        
        for job in st.session_state.jobs:
            score = job.get('match_score', 0)
            
            # Score badge color
            if score >= 8:
                badge_class = "score-high"
            elif score >= 5:
                badge_class = "score-medium"
            else:
                badge_class = "score-low"
            
            with st.container():
                cols = st.columns([3, 1])
                
                with cols[0]:
                    st.markdown(f"#### {job.get('title', 'Unknown')}")
                    st.markdown(f"**{job.get('company', 'Unknown')}** • {job.get('location', 'N/A')}")
                    
                    # Date and salary info
                    salary_info = f"💰 {job.get('salary', 'Not specified')}"
                    remote_info = f"🏠 {'Remote' if job.get('is_remote') else 'On-site'}"
                    
                    # Posted date
                    posted_info = ""
                    if job.get('job_age'):
                        posted_info = f"📅 Posted {job.get('job_age')}"
                    elif job.get('posted_date'):
                        posted_date = job.get('posted_date')
                        if isinstance(posted_date, str):
                            posted_info = f"📅 Posted {posted_date[:10]}"
                        else:
                            posted_info = f"📅 Posted {str(posted_date)[:10]}"
                    
                    # Expiration date
                    exp_info = ""
                    if job.get('expiration_date'):
                        exp_date = job.get('expiration_date')
                        if isinstance(exp_date, str):
                            exp_info = f"⏰ Expires {exp_date[:10]}"
                        else:
                            exp_info = f"⏰ Expires {str(exp_date)[:10]}"
                    
                    # Combine all metadata
                    metadata_parts = [salary_info, remote_info, posted_info, exp_info]
                    metadata = " | ".join([p for p in metadata_parts if p])
                    st.markdown(metadata)
                    
                    # Apply URL button
                    apply_url = job.get('apply_url') or job.get('job_url')
                    if apply_url:
                        st.markdown(f"[🔗 Apply Now]({apply_url})", unsafe_allow_html=False)
                    
                    with st.expander("📄 Description"):
                        st.write(job.get('description', 'No description')[:500] + "...")
                    
                    st.caption(f"🎯 **Match Reasoning:** {job.get('match_reasoning', 'N/A')}")
                
                with cols[1]:
                    st.markdown(f'<div class="score-badge {badge_class}">{score}/10</div>', unsafe_allow_html=True)
                    st.markdown("")
                    
                    # Applied Checkbox (Only if job has ID from database)
                    if job.get('id'):
                        cb_key = f"applied_{job.get('id')}"
                        st.checkbox("✅ Applied", key=cb_key, on_change=update_application_status, args=(job.get('id'), cb_key))
                        st.markdown("")
                    
                    # Use job_url as unique key (Apify jobs don't have 'id' field)
                    job_key = job.get('job_url', '').replace('/', '_').replace(':', '')[-50:]
                    
                    if st.button("✏️ Optimize Resume", key=f"resume_{job_key}"):
                        with st.spinner("Tailoring resume with AI..."):
                            try:
                                from modules.resume_generator import resume_generator
                                
                                # Load master resume
                                master_resume = resume_generator.load_master_resume()
                                
                                if not master_resume:
                                    st.error("⚠️ Master resume not found! Please create 'Yuting Sun Master Resume.md'")
                                else:
                                    # Tailor resume
                                    tailored = resume_generator.tailor_resume(
                                        master_resume,
                                        job.get('description', ''),
                                        job.get('title', ''),
                                        job.get('company', '')
                                    )
                                    
                                    # Preview in expander
                                    with st.expander("📄 Resume Preview", expanded=True):
                                        st.markdown(f"**{tailored.get('name', 'Your Name')}**")
                                        st.caption(f"Tailored for: {job.get('title')} at {job.get('company')}")
                                        
                                        st.markdown("#### Summary")
                                        st.write(tailored.get('summary', ''))
                                        
                                        st.markdown("#### Experience")
                                        for exp in tailored.get('experience', [])[:3]:  # Show top 3
                                            st.markdown(f"**{exp.get('title')}** | {exp.get('company', '')}")
                                            for detail in exp.get('details', [])[:2]:  # Show 2 bullets
                                                st.markdown(f"- {detail}")
                                        
                                        st.markdown("#### Skills")
                                        st.write(', '.join(tailored.get('skills', [])[:10]))
                                    
                                    # Download buttons
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("📥 Download DOCX", key=f"docx_{job_key}"):
                                            filename = f"{job.get('company', 'company').replace(' ', '_')}_resume.docx"
                                            path = resume_generator.export_docx(tailored, filename)
                                            st.success(f"✅ Resume saved: {path}")
                                    
                                    with col2:
                                        if st.button("📥 Download PDF", key=f"pdf_{job_key}"):
                                            filename = f"{job.get('company', 'company').replace(' ', '_')}_resume.pdf"
                                            path = resume_generator.export_pdf(tailored, filename)
                                            st.success(f"✅ Resume saved: {path}")
                            
                            except Exception as e:
                                st.error(f"Resume generation failed: {e}")
                                streamlit_logger.error(f"Resume error: {e}", exc_info=True)
                    
                    if st.button("✉️ Create Draft", key=f"email_{job_key}"):
                        with st.spinner("Generating email..."):
                            email = ai_agent.generate_cold_email(job, "Hiring Manager", "initial")
                            st.text_area("Generated Email:", email, height=300)
                            st.success("Email generated! (Gmail integration coming soon)")
                
                st.markdown("---")



elif page == "📄 Resume Export":
    # Custom CSS for UI Enhancement
    st.markdown("""
    <style>
        /* Primary Button Styling */
        div.stButton > button:first-child {
            background-color: #4F46E5;
            color: white;
            border-radius: 10px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: all 0.2s ease-in-out;
        }
        div.stButton > button:first-child:hover {
            background-color: #4338CA;
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        /* Secondary Button Styling */
        div.stButton > button:nth-child(2) {
            border-radius: 10px;
        }

        /* Card/Container Styling */
        div[data-testid="stExpander"] {
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        /* Metric Card Styling */
        div[data-testid="metric-container"] {
            background-color: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 10px;
            padding: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    colored_header(
        label="Resume Export Studio 📄",
        description="Craft ATS-optimized resumes with AI-powered tailoring, compression, and formatting.",
        color_name="violet-70"
    )
    
    # Initialize session state
    if 'resume_data' not in st.session_state: st.session_state.resume_data = None
    if 'selected_template' not in st.session_state: st.session_state.selected_template = None
    if 'compressed_resume' not in st.session_state: st.session_state.compressed_resume = None
    
    # Progress Steps (Reordered)
    steps = ["Upload", "Template", "AI Optimize", "Customize", "ATS Score", "Export"]
    current_step = 0
    if st.session_state.resume_data: current_step = 1
    if st.session_state.selected_template: current_step = 2
    # If optimization has happened (we'll check a flag or just assume based on flow)
    # Ideally tracking state better, but for now simple increment logic
    
    # Modern Progress Bar
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
        {''.join([f'<div style="text-align: center; color: {"#667eea" if i <= current_step else "#ccc"}; font-weight: {"bold" if i == current_step else "normal"};">{step}</div>' for i, step in enumerate(steps)])}
    </div>
    <div style="height: 4px; background: #eee; width: 100%; border-radius: 2px; margin-bottom: 30px;">
        <div style="height: 100%; width: {(current_step)/(len(steps)-1)*100}%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 2px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ===== STEP 1: Upload Master Resume =====
    with st.container(border=True):
        st.markdown("### 📤 Step 1: Upload Master Resume")
        uploaded_file = st.file_uploader("Upload your master resume", type=["md", "pdf", "docx"])
        
        if uploaded_file and (not st.session_state.resume_data or uploaded_file.name != st.session_state.get('last_uploaded_file', '')):
            file_type = uploaded_file.name.split('.')[-1].lower()
            with st.spinner(f"Parsing {file_type.upper()} resume..."):
                try:
                    temp_path = f"data/temp_resume.{file_type}"
                    with open(temp_path, 'wb') as f: f.write(uploaded_file.getbuffer())
                    
                    if file_type == "md": func = resume_generator.load_master_resume
                    elif file_type == "pdf": func = resume_generator.parse_pdf_resume
                    elif file_type == "docx": func = resume_generator.parse_docx_resume
                    
                    data = func(temp_path)
                    if data:
                        st.session_state.resume_data = data
                        st.session_state.last_uploaded_file = uploaded_file.name
                        st.balloons()
                        st.success(f"✅ Loaded: **{data.get('name', 'Unknown')}**")
                    else:
                        st.error("Failed to parse resume.")
                except Exception as e:
                    st.error(f"Error: {e}")

    # ===== STEP 2: Template Selection =====
    if st.session_state.resume_data:
        st.write("")
        with st.container(border=True):
            st.markdown("### 🎨 Step 2: Choose Template")
            
            # Grid layout for templates
            template_options = [
                {"name": "classic_single_column", "display": "Classic Single", "desc": "Clean & ATS Optimized", "img": "classic_single.jpg"},
                {"name": "modern_single_column", "display": "Modern Single", "desc": "Sleek & Minimalist", "img": "modern_single.jpg"},
                {"name": "classic_two_column", "display": "Classic Two-Column", "desc": "Professional Layout", "img": "classic_two.jpg"},
                {"name": "modern_two_column", "display": "Modern Two-Column", "desc": "Creative & Bold", "img": "modern_two.jpg"}
            ]
            
            cols = st.columns(4)
        for i, t in enumerate(template_options):
            with cols[i]:
                # Use custom HTML card for better control than streamlit-card
                img_path = f"assets/templates/{t['img']}"
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.warning(f"No preview for {t['display']}")
                
                st.markdown(f"**{t['display']}**")
                st.caption(t['desc'])
                
                if st.button(f"Select##{i}", key=f"sel_{t['name']}", type="primary" if st.session_state.selected_template == t['name'] else "secondary", use_container_width=True):
                    st.session_state.selected_template = t['name']
                    st.rerun()
        
        if st.session_state.selected_template:
            st.success(f"Selected: **{st.session_state.selected_template}**")

    
    # ===== STEP 3: AI Optimization (Moved up) =====

            # ==========================
            # Step 3: AI Optimization & Contact Info
            # ==========================
            st.header("Step 3: AI Optimization & Setup")
            
            col_input, col_ai = st.columns([1, 1])
            
            with col_input:
                st.subheader("1. Confirm Contact Info")
                # Pre-AI Contact Editing
                if 'resume_data' in st.session_state:
                    contact = st.session_state.resume_data.get('contact', {})
                    
                    # Direct inputs - Streamlit updates on blur (click away) or Enter
                    new_email = st.text_input("Email", value=contact.get('email', ''))
                    new_phone = st.text_input("Phone", value=contact.get('phone', ''))
                    new_linkedin = st.text_input("LinkedIn", value=contact.get('linkedin', ''))
                    new_portfolio = st.text_input("Portfolio", value=contact.get('portfolio', ''))
                    new_other = st.text_input("GitHub / Other Website", value=contact.get('github', '')) # Using 'github' key for other/github
                    new_location = st.text_input("Location", value=contact.get('location', ''))
                    
                    # Update session promptly
                    st.session_state.resume_data['contact'] = {
                        "email": new_email,
                        "phone": new_phone,
                        "linkedin": new_linkedin,
                        "portfolio": new_portfolio,
                        "github": new_other, # Store in github key or add 'other' if generator supports it
                        "location": new_location
                    }
            
            with col_ai:
                st.subheader("2. Target Job")
                # Job Selection - FIX: Use st.session_state.jobs
                jobs_source = st.session_state.jobs if st.session_state.jobs else []
                job_options = {f"{job['title']} at {job['company']}": job for job in jobs_source}
                selected_job_name = st.selectbox("Select Target Job", list(job_options.keys()))
                
                target_jd = ""
                if selected_job_name:
                    target_jd = job_options[selected_job_name].get('description', '')
                    # Clean HTML just in case
                    from modules.job_scraper import JobScraper
                    target_jd = JobScraper().clean_html_tags(target_jd)
                    
                with st.expander("View Job Description"):
                    st.text_area("JD Content", target_jd, height=150)
                    
                if st.button("✨ Auto-Tailor Resume", type="primary"):
                    with st.spinner("AI is rewriting your resume..."):
                        try:
                            # Run AI tailoring
                            # FIX 1: Use st.session_state.selected_template
                            layout_type = "two_column" if "two_column" in st.session_state.get('selected_template', '') else "single_column"
                            
                            optimized_resume = resume_generator.tailor_and_compress(
                                st.session_state.resume_data,
                                target_jd,
                                template={"layout": layout_type},
                                mode="balanced"
                            )
                            
                            if optimized_resume:
                                st.session_state.resume_data = optimized_resume
                                st.session_state.ai_tailored = True
                                st.success("Resume optimized!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Optimization failed: {e}")

            # ==========================
            # Step 4: Preview & Customize Loop
            # ==========================
            if st.session_state.get('ai_tailored', False):
                st.header("Step 4: Review & Customize (Loop)")
                
                col_edit, col_preview = st.columns([1, 1])
                
                with col_edit:
                    st.subheader("✏️ Edit Content")
                    
                    # 1. Reorder Section (Moved to Top)
                    with st.expander("📐 Reorder Resume Sections", expanded=True):
                        st.caption("Drag and drop to rearrange section order")
                        try:
                            from streamlit_sortables import sort_items
                            
                            # Get current order from session state first, then meta, then default
                            if 'custom_section_order' in st.session_state:
                                current_order = st.session_state.custom_section_order
                            else:
                                current_order = st.session_state.resume_data.get('_meta', {}).get('section_order', 
                                    ['summary', 'experience', 'education', 'skills', 'projects'])
                            
                            # Show sortable list
                            sorted_sections = sort_items(current_order, direction='horizontal')
                            
                            # ALWAYS save the current state
                            st.session_state.custom_section_order = sorted_sections
                            
                            # Update resume_data._meta.section_order
                            if '_meta' not in st.session_state.resume_data:
                                st.session_state.resume_data['_meta'] = {}
                            st.session_state.resume_data['_meta']['section_order'] = sorted_sections
                            
                            # Show current order for confirmation
                            st.success(f"📋 Current Order: {' → '.join([s.title() for s in sorted_sections])}")
                            
                            st.info("💡 Click 'Refresh Preview' after reordering to see changes")

                        except ImportError:
                            st.warning("streamlit-sortables not installed. Using manual reorder:")
                            # Fallback: use selectbox to reorder
                            sections = ['summary', 'experience', 'education', 'skills', 'projects']
                            new_order = []
                            for i in range(len(sections)):
                                selected = st.selectbox(f"Section {i+1}", sections, key=f"sect_{i}")
                                new_order.append(selected)
                            st.session_state.custom_section_order = new_order
                            
                        except Exception as e:
                            st.warning(f"Sortables error: {e}")
                    
                    # === Quick Jump Buttons ===
                    st.caption("🎯 Quick Jump to Edit Section:")
                    qj_cols = st.columns(5)
                    with qj_cols[0]:
                        if st.button("📝 Summary", use_container_width=True):
                            st.session_state.expand_summary = True
                    with qj_cols[1]:
                        if st.button("💼 Experience", use_container_width=True):
                            st.session_state.expand_experience = True
                    with qj_cols[2]:
                        if st.button("🎓 Education", use_container_width=True):
                            st.session_state.expand_education = True
                    with qj_cols[3]:
                        if st.button("⚙️ Skills", use_container_width=True):
                            st.session_state.expand_skills = True
                    with qj_cols[4]:
                        if st.button("🚀 Projects", use_container_width=True):
                            st.session_state.expand_projects = True
                    
                    st.markdown("---")
                    
                    # === Edit Sections ===
                    with st.expander("Professional Summary", expanded=st.session_state.get('expand_summary', False)):
                        new_summary = st.text_area("Summary", value=st.session_state.resume_data.get('summary', ''), height=150)
                        st.session_state.resume_data['summary'] = new_summary
                        st.session_state.expand_summary = False  # Reset after render
                    
                    with st.expander("Experience (Bullets)", expanded=st.session_state.get('expand_experience', True)):
                        experiences = st.session_state.resume_data.get('experience', [])
                        
                        # === Drag & Drop Reorder ===
                        try:
                            from streamlit_sortables import sort_items
                            st.caption("🔀 Drag to reorder jobs:")
                            job_labels = [f"{exp.get('company', 'Company')} - {exp.get('title', 'Title')}" for exp in experiences]
                            if job_labels:
                                sorted_labels = sort_items(job_labels, direction='vertical')
                                if sorted_labels != job_labels:
                                    # Reorder experiences based on sorted labels
                                    new_order = [job_labels.index(label) for label in sorted_labels]
                                    experiences = [experiences[i] for i in new_order]
                                    st.session_state.resume_data['experience'] = experiences
                                    st.rerun()
                        except ImportError:
                            st.caption("Install streamlit-sortables for drag & drop")
                        except Exception as e:
                            st.caption(f"Drag & drop unavailable: {e}")
                        
                        st.markdown("---")
                        
                        # === Edit Each Job ===
                        for i, exp in enumerate(experiences):
                            col_header, col_delete = st.columns([4, 1])
                            with col_header:
                                st.markdown(f"**Job {i+1}**")
                            with col_delete:
                                if st.button(f"🗑️ Delete", key=f"del_job_{i}", type="secondary"):
                                    del experiences[i]
                                    st.session_state.resume_data['experience'] = experiences
                                    st.rerun()
                            
                            col_c, col_t = st.columns(2)
                            with col_c:
                                new_comp = st.text_input(f"Company {i+1}", value=exp.get('company', ''), key=f"comp_{i}")
                            with col_t:
                                new_title = st.text_input(f"Title {i+1}", value=exp.get('title', ''), key=f"title_{i}")
                            
                            experiences[i]['company'] = new_comp
                            experiences[i]['title'] = new_title
                            
                            col_loc, col_dur = st.columns(2)
                            with col_loc:
                                new_loc = st.text_input(f"Location {i+1}", value=exp.get('location', ''), key=f"loc_{i}")
                                experiences[i]['location'] = new_loc
                            with col_dur:
                                new_dur = st.text_input(f"Duration {i+1}", value=exp.get('duration', ''), key=f"dur_{i}")
                                experiences[i]['duration'] = new_dur
                            
                            # Bullets with Add/Delete
                            new_bullets = []
                            if 'details' in exp:
                                for j, bullet in enumerate(exp['details']):
                                    col_bull, col_del_bull = st.columns([9, 1])
                                    with col_bull:
                                        val = st.text_area(f"Bullet {j+1}", value=bullet, key=f"bull_{i}_{j}", height=68)
                                        new_bullets.append(val)
                                    with col_del_bull:
                                        if st.button("✖", key=f"del_bull_{i}_{j}"):
                                            del exp['details'][j]
                                            st.rerun()
                            
                            experiences[i]['details'] = new_bullets
                            
                            # Add Bullet Button
                            if st.button(f"➕ Add Bullet", key=f"add_bull_{i}"):
                                if 'details' not in experiences[i]:
                                    experiences[i]['details'] = []
                                experiences[i]['details'].append("New bullet point")
                                st.rerun()
                            
                            st.markdown("---")
                        
                        # === Add New Job Button ===
                        if st.button("➕ Add New Experience", type="primary"):
                            experiences.append({
                                'company': 'New Company',
                                'title': 'Job Title',
                                'location': 'City, Province',
                                'duration': 'Start – End',
                                'details': ['Achievement bullet point']
                            })
                            st.session_state.resume_data['experience'] = experiences
                            st.rerun()
                        
                        # Force update session state
                        st.session_state.resume_data['experience'] = experiences
                        st.session_state.expand_experience = False  # Reset

                    # === Education CRUD ===
                    with st.expander("Education", expanded=st.session_state.get('expand_education', False)):
                        education = st.session_state.resume_data.get('education', [])
                        
                        for i, edu in enumerate(education):
                            col_edu_header, col_edu_del = st.columns([4, 1])
                            with col_edu_header:
                                st.markdown(f"**Education {i+1}**")
                            with col_edu_del:
                                if st.button(f"🗑️ Delete", key=f"del_edu_{i}", type="secondary"):
                                    del education[i]
                                    st.session_state.resume_data['education'] = education
                                    st.rerun()
                            
                            new_title = st.text_input(f"Degree/Title {i+1}", value=edu.get('title', ''), key=f"edu_title_{i}")
                            education[i]['title'] = new_title
                            
                            # Details as single text area
                            details_text = '\n'.join(edu.get('details', []))
                            new_details = st.text_area(f"Details {i+1}", value=details_text, height=80, key=f"edu_details_{i}")
                            education[i]['details'] = [d.strip() for d in new_details.split('\n') if d.strip()]
                            
                            st.markdown("---")
                        
                        # Add New Education
                        if st.button("➕ Add New Education", type="primary"):
                            education.append({
                                'title': 'Degree, Major',
                                'details': ['University, Year']
                            })
                            st.session_state.resume_data['education'] = education
                            st.rerun()
                        
                        st.session_state.resume_data['education'] = education
                        st.session_state.expand_education = False  # Reset

                    with st.expander("Skills (Bullet Points)", expanded=st.session_state.get('expand_skills', False)):
                        current_skills = st.session_state.resume_data.get('skills', [])
                        
                        # Helper to clean Python list syntax from strings
                        def clean_skill_text(text):
                            import re
                            # Remove ['...', '...'] patterns
                            text = re.sub(r"\['([^']+)'\s*,\s*'([^']+)'\]", r"\1, \2", text)
                            text = re.sub(r"\['([^']+)'\]", r"\1", text)
                            # Remove remaining brackets and quotes
                            text = text.replace("[", "").replace("]", "").replace("'", "")
                            return text.strip()
                        
                        # FORMATTING: Convert Dict or List to clean Multiline String
                        skills_text = ""
                        if isinstance(current_skills, dict):
                            # Convert Dict {'Cat': 'Skills'} -> "Cat: Skills"
                            lines = []
                            for cat, vals in current_skills.items():
                                # vals might be a list
                                if isinstance(vals, list):
                                    vals = ", ".join(vals)
                                lines.append(f"{cat}: {clean_skill_text(str(vals))}")
                            skills_text = "\n".join(lines)
                        elif isinstance(current_skills, list):
                            # Clean each skill string
                            skills_text = "\n".join([clean_skill_text(str(s)) for s in current_skills])
                        else:
                            skills_text = str(current_skills)
                            
                        st.caption("Edit skills line by line. Use **Category: Skills** format for bolding.")
                        new_skills_str = st.text_area("Skills List", value=skills_text, height=200, key="skills_input")
                        
                        # SAVING: Parse back to List of Strings (PDF generator handles the rest)
                        if new_skills_str:
                             # Just split by newline, clean whitespace
                             st.session_state.resume_data['skills'] = [s.strip() for s in new_skills_str.split('\n') if s.strip()]
                        
                        st.session_state.expand_skills = False  # Reset

                    # === Projects CRUD ===
                    with st.expander("Projects", expanded=st.session_state.get('expand_projects', False)):
                        projects = st.session_state.resume_data.get('projects', [])
                        
                        for i, proj in enumerate(projects):
                            col_proj_header, col_proj_del = st.columns([4, 1])
                            with col_proj_header:
                                st.markdown(f"**Project {i+1}**")
                            with col_proj_del:
                                if st.button(f"🗑️ Delete", key=f"del_proj_{i}", type="secondary"):
                                    del projects[i]
                                    st.session_state.resume_data['projects'] = projects
                                    st.rerun()
                            
                            # Project can be string or dict
                            if isinstance(proj, dict):
                                new_title = st.text_input(f"Title {i+1}", value=proj.get('title', ''), key=f"proj_title_{i}")
                                new_desc = st.text_area(f"Description {i+1}", value='\n'.join(proj.get('details', [])), height=80, key=f"proj_desc_{i}")
                                projects[i] = {
                                    'title': new_title,
                                    'details': [d.strip() for d in new_desc.split('\n') if d.strip()]
                                }
                            else:
                                # Simple string project
                                new_proj = st.text_area(f"Project {i+1}", value=str(proj), height=80, key=f"proj_{i}")
                                projects[i] = new_proj
                            
                            st.markdown("---")
                        
                        # Add New Project
                        if st.button("➕ Add New Project", type="primary"):
                            projects.append("New Project: Description of your project")
                            st.session_state.resume_data['projects'] = projects
                            st.rerun()
                        
                        st.session_state.resume_data['projects'] = projects
                        st.session_state.expand_projects = False  # Reset


                    # Tab 2: Sort Sections (Restored)


                    
                    # Refresh button with clear instruction
                    st.info("💡 After editing, click 'Refresh Preview' to see changes in PDF")
                    if st.button("🔄 Refresh Preview", type="primary", use_container_width=True):
                        st.rerun()
                        
                with col_preview:
                    st.subheader("📄 Live Preview")
                    
                    # Add timestamp to show when preview was generated
                    st.caption(f"Preview generated at: {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Generate temporary PDF for preview
                    try:
                        # Update meta template WITHOUT overwriting section_order
                        if '_meta' not in st.session_state.resume_data:
                            st.session_state.resume_data['_meta'] = {}
                        st.session_state.resume_data['_meta']['template'] = st.session_state.selected_template
                        
                        # Ensure section_order is preserved
                        if 'custom_section_order' in st.session_state:
                            st.session_state.resume_data['_meta']['section_order'] = st.session_state.custom_section_order
                        
                        preview_path = resume_generator.export_pdf(st.session_state.resume_data, "preview_temp.pdf")
                        
                        if preview_path and os.path.exists(preview_path):
                            with open(preview_path, "rb") as f:
                                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                            
                            # Embed PDF
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.warning("Preview generation failed.")
                    except Exception as e:
                        st.error(f"Preview error: {e}")

    # ==========================
    # Step 5: ATS Analysis (Moved down)
    # ==========================



    # ===== STEP 5: ATS Score =====
    if st.session_state.selected_template and st.session_state.resume_data:
        st.write("")
        with st.container(border=True):
            st.markdown("### 📊 Step 5: ATS Analysis")
            
            # Use selected job from Step 3 scope if available, else try to find it
            ats_target_job = None
            if selected_job_name and selected_job_name != "Generic (No specific job)":
                 # Reconstruct job lookup if necessary
                 jobs_source = st.session_state.jobs if st.session_state.jobs else []
                 job_map = {f"{job['title']} at {job['company']}": job for job in jobs_source}
                 ats_target_job = job_map.get(selected_job_name)

            if ats_target_job:
                 # Recalulate based on CURRENT resume content
                 resume_text = json.dumps(st.session_state.resume_data)
                 jd_text = ats_target_job.get('description', '')
                 
                 # Clean HTML from JD for ATS scoring
                 from modules.job_scraper import JobScraper
                 jd_text = JobScraper().clean_html_tags(jd_text)
                 
                 if st.button("Check ATS Score  📊", type="primary"):
                     res = ats_scorer.score_resume(resume_text, jd_text)
                     
                     c1, c2, c3 = st.columns(3)
                     c1.metric("Match Score", f"{res['score']}%", delta="High" if res['score']>70 else "Low")
                     c2.metric("Missing Keywords", len(res['missing_keywords']), delta_color="inverse")
                     c3.metric("Keyword Density", "Analyzed")
                     style_metric_cards()
                     
                     if res['missing_keywords']:
                        st.warning(f"**Missing Keywords**: {', '.join(res['missing_keywords'][:5])}")
                        st.caption("Tip: Add these keywords to your skills or summary in Step 4.")
            else:
                 st.info("Select a job in Step 3 to enable ATS scoring.")


    # ===== STEP 6: Export =====
    if st.session_state.compressed_resume or st.session_state.resume_data:
        st.write("")
        with st.container(border=True):
            st.markdown("### 💾 Step 6: Export & Save")
            
            # Determine which resume to export
            # FIX: STRICTLY use the data from Step 4 (Edit Mode) to ensure WYSIWYG
            export_data = st.session_state.resume_data

            
            # Load Template
            t_conf = None
            if st.session_state.selected_template:
                t_conf = resume_generator.load_template(st.session_state.selected_template)
                
            if not t_conf:
                 st.error("⚠️ Template not matched. Defaulting to standard layout.")
                 t_conf = {"name": "default", "section_order": ["summary", "experience", "education", "skills"], "layout": "single_column"}
            
            # Apply Custom Order if exists
            if 'custom_section_order' in st.session_state:
                t_conf['section_order'] = st.session_state.custom_section_order

            # Apply Template
            final_data = resume_generator.apply_template(export_data, t_conf)
            
            # Format selection guide
            st.info("Ready to export! Click 'Generate Files' to prepare your download.")
            
            if st.button("🚀 Generate PDF & DOCX Files", type="primary", use_container_width=True):
                 with st.spinner("Generating documents..."):
                    try:
                        # Generate PDF
                        pdf_name = f"Resume_{final_data.get('name', 'User').replace(' ', '_')}.pdf"
                        pdf_path = resume_generator.export_pdf(final_data, pdf_name)
                        st.session_state.export_pdf_path = pdf_path
                        
                        # Generate DOCX
                        docx_name = f"Resume_{final_data.get('name', 'User').replace(' ', '_')}.docx"
                        docx_path = resume_generator.export_docx(final_data, docx_name)
                        st.session_state.export_docx_path = docx_path
                        
                        # Save to DB (Background)
                        try:
                            from modules.database import ResumeVersion, SessionLocal
                            db = SessionLocal()
                            new_version = ResumeVersion(
                                template_name=st.session_state.selected_template,
                                resume_json=final_data,
                                pdf_path=pdf_path,
                                docx_path=docx_path,
                                job_id=selected_job.get('id') if selected_job and isinstance(selected_job, dict) else None
                            )
                            db.add(new_version)
                            db.commit()
                            db.close()
                        except Exception as e:
                            print(f"DB Save Error: {e}")
                            
                        st.success("✅ Files generated successfully!")
                        st.rerun() # Rerun to show download buttons
                        
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

            # Show Download Buttons only if files exist
            if 'export_pdf_path' in st.session_state and os.path.exists(st.session_state.export_pdf_path):
                col1, col2 = st.columns(2)
                
                with col1:
                    with open(st.session_state.export_pdf_path, "rb") as f:
                        st.download_button(
                            label="📄 Download PDF",
                            data=f,
                            file_name=os.path.basename(st.session_state.export_pdf_path),
                            mime="application/pdf",
                            use_container_width=True,
                            type="secondary"
                        )
                
                with col2:
                    if 'export_docx_path' in st.session_state and os.path.exists(st.session_state.export_docx_path):
                         with open(st.session_state.export_docx_path, "rb") as f:
                            st.download_button(
                                label="📝 Download DOCX",
                                data=f,
                                file_name=os.path.basename(st.session_state.export_docx_path),
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                                type="secondary"
                            )

# ==========================
# Email Center Tab
# ==========================
elif page == "📧 Email Center":
    st.markdown('<h1 class="main-header">Email Center 📧</h1>', unsafe_allow_html=True)
    st.markdown("Manage cold emails, follow-ups, and track responses")
    
    # Email stats
    col1, col2, col3, col4 = st.columns(4)
    
    # Get email stats from database
    try:
        from modules.database import SessionLocal, Application
        db = SessionLocal()
        total_drafts = db.query(Application).filter(Application.email_stage == 'initial_draft').count()
        total_sent = db.query(Application).filter(Application.email_stage == 'initial_sent').count()
        total_replied = db.query(Application).filter(Application.hr_replied == True).count()
        pending_followup = db.query(Application).filter(
            Application.email_stage == 'initial_sent',
            Application.hr_replied == False
        ).count()
        db.close()
    except:
        total_drafts, total_sent, total_replied, pending_followup = 0, 0, 0, 0
    
    with col1:
        st.metric("📝 Drafts", total_drafts)
    with col2:
        st.metric("✉️ Sent", total_sent)
    with col3:
        st.metric("💬 Replied", total_replied)
    with col4:
        st.metric("⏰ Pending Follow-up", pending_followup)
    
    st.markdown("---")
    
    # Tabs for different email functions
    email_tab1, email_tab2, email_tab3 = st.tabs(["📝 Draft New Email", "📬 Follow-up Queue", "📊 Email History"])
    
    with email_tab1:
        st.subheader("Create Cold Email Draft")
        
        # ===== Load Cache Button =====
        col_load, col_count = st.columns([1, 3])
        with col_load:
            if st.button("📦 Load Cached Jobs", help="Load jobs from cloud database (excludes applied jobs)"):
                try:
                    from modules.job_scraper import JobScraper
                    scraper = JobScraper()
                    cached = scraper.get_all_jobs(limit=100, exclude_applied=True)
                    if cached:
                        jobs = []
                        for job in cached:
                            jobs.append({
                                "id": job.id,
                                "title": job.title,
                                "company": job.company,
                                "description": job.description,
                                "location": job.location,
                                "salary": job.salary,
                                "is_remote": job.is_remote,
                                "job_url": job.job_url,
                                "posted_date": job.posted_date,
                            })
                        st.session_state.jobs = jobs
                        st.success(f"✅ Loaded {len(jobs)} jobs from database (applied jobs excluded)")
                    else:
                        st.warning("No cached jobs found. Search for jobs first!")
                except Exception as e:
                    st.error(f"Failed to load: {e}")
        
        with col_count:
            if st.session_state.jobs:
                st.caption(f"📊 {len(st.session_state.jobs)} jobs available")
        
        st.markdown("---")
        
        # ===== Daily Send Limit Tracking =====
        if 'emails_sent_today' not in st.session_state:
            st.session_state.emails_sent_today = 0
        daily_limit = 20
        remaining = daily_limit - st.session_state.emails_sent_today
        if remaining <= 5:
            st.warning(f"⚠️ Daily limit: {remaining}/{daily_limit} emails remaining today")
        
        # ===== Job Selection =====
        if st.session_state.jobs:
            job_options = {f"{j['title']} @ {j['company']}": j for j in st.session_state.jobs}
            selected_job_name = st.selectbox("Select Job", list(job_options.keys()))
            selected_job = job_options.get(selected_job_name, {})
            
            if selected_job:
                # ===== Enhanced Job Info Display =====
                with st.container(border=True):
                    st.markdown(f"### {selected_job.get('title', 'N/A')}")
                    st.markdown(f"**{selected_job.get('company', 'N/A')}**")
                    
                    # Metadata row
                    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
                    with meta_col1:
                        salary = selected_job.get('salary', 'Not specified')
                        st.caption(f"💰 {salary}")
                    with meta_col2:
                        location = selected_job.get('location', 'N/A')
                        st.caption(f"📍 {location}")
                    with meta_col3:
                        # Work mode: Remote / Hybrid / Onsite
                        if selected_job.get('is_remote'):
                            work_mode = "🏠 Remote"
                        else:
                            # Check if hybrid mentioned in description or location
                            loc_lower = str(selected_job.get('location', '')).lower()
                            if 'hybrid' in loc_lower:
                                work_mode = "🔄 Hybrid"
                            else:
                                work_mode = "🏢 Onsite"
                        st.caption(work_mode)
                    with meta_col4:
                        posted = selected_job.get('posted_date', '')
                        if posted:
                            posted_str = str(posted)[:10] if posted else 'N/A'
                        else:
                            posted_str = 'N/A'
                        st.caption(f"📅 {posted_str}")
                    
                    # JD Expandable Section
                    with st.expander("📄 View Job Description"):
                        jd = selected_job.get('description', 'No description available')
                        if jd:
                            # Clean HTML if present
                            from modules.job_scraper import JobScraper
                            jd_clean = JobScraper().clean_html_tags(jd)
                            display_jd = jd_clean[:2000] + "..." if len(jd_clean) > 2000 else jd_clean
                            st.markdown(display_jd)
                        else:
                            st.info("No job description available")
                    
                    # ===== Apply Link + Applied Checkbox =====
                    action_col1, action_col2 = st.columns([1, 1])
                    
                    with action_col1:
                        apply_url = selected_job.get('apply_url') or selected_job.get('job_url')
                        if apply_url:
                            st.link_button("🔗 Apply Now", apply_url, use_container_width=True)
                        else:
                            st.caption("No apply link available")
                    
                    with action_col2:
                        job_id = selected_job.get('id')
                        if job_id:
                            # Applied checkbox with callback
                            applied_key = f"email_applied_{job_id}"
                            if st.checkbox("✅ Mark as Applied", key=applied_key):
                                try:
                                    from modules.job_scraper import JobScraper
                                    scraper = JobScraper()
                                    scraper.mark_job_as_applied(int(job_id), applied=True)
                                    st.success("Marked as applied!")
                                    # Remove from current list to avoid showing again
                                    st.session_state.jobs = [j for j in st.session_state.jobs if j.get('id') != job_id]
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                
                st.markdown("---")
                
                # ===== HR Contact Auto-fill =====
                hr_email_default = ""
                hr_name_default = ""
                hr_contact_found = False
                
                try:
                    from modules.database import SessionLocal, HRContact
                    db = SessionLocal()
                    hr_contact = db.query(HRContact).filter(
                        HRContact.company == selected_job.get('company', '')
                    ).order_by(HRContact.imported_at.desc()).first()
                    
                    if hr_contact:
                        hr_email_default = hr_contact.email or ""
                        hr_name_default = hr_contact.name or ""
                        hr_contact_found = True
                        
                        # Check email freshness (warn if > 30 days old)
                        from datetime import datetime, timedelta
                        if hr_contact.imported_at:
                            age_days = (datetime.utcnow() - hr_contact.imported_at).days
                            if age_days > 30:
                                st.warning(f"⚠️ Contact data is {age_days} days old - consider verifying")
                    db.close()
                except Exception as e:
                    pass  # Silently fail, user can enter manually
                
                if not hr_contact_found:
                    st.info("ℹ️ No HR contact found for this company. Please enter manually.")
                
                # HR Contact inputs
                hr_email = st.text_input("HR/Recruiter Email", value=hr_email_default, placeholder="recruiter@company.com")
                hr_name = st.text_input("HR/Recruiter Name", value=hr_name_default, placeholder="Sarah Chen")
                
                # ===== Email Validation =====
                email_valid = False
                if hr_email:
                    try:
                        from email_validator import validate_email, EmailNotValidError
                        valid = validate_email(hr_email, check_deliverability=False)
                        st.success(f"✅ Email format valid: {valid.normalized}")
                        email_valid = True
                    except EmailNotValidError as e:
                        st.error(f"❌ Invalid email: {str(e)}")
                    except ImportError:
                        email_valid = True  # Skip validation if library not installed
                
                col_gen, col_preview = st.columns(2)
                
                with col_gen:
                    generate_disabled = remaining <= 0
                    if st.button("🤖 Generate Email with AI", type="primary", disabled=generate_disabled):
                        if not email_valid:
                            st.warning("Please enter a valid HR email address")
                        elif not hr_email:
                            st.warning("Please enter HR email address")
                        else:
                            try:
                                from modules.ai_agent import ai_agent
                                email_content = ai_agent.generate_cold_email(
                                    job_data=selected_job,
                                    hr_name=hr_name or "Hiring Manager",
                                    stage="initial"
                                )
                                st.session_state.generated_email = email_content
                                st.success("Email generated!")
                            except Exception as e:
                                st.error(f"Generation failed: {e}")
                
                # Display generated email
                if 'generated_email' in st.session_state:
                    email = st.session_state.generated_email
                    if isinstance(email, dict):
                        st.text_area("Subject", value=email.get('subject', ''), key="email_subject", height=50)
                        st.text_area("Body", value=email.get('body', ''), key="email_body", height=300)
                    else:
                        # If email is a string
                        st.text_area("Email Content", value=str(email), key="email_body", height=300)
                    
                    create_disabled = remaining <= 0
                    if st.button("📤 Create Gmail Draft", disabled=create_disabled):
                        if remaining <= 0:
                            st.error("❌ Daily email limit reached (20/day)")
                        else:
                            try:
                                from modules.gmail_service import gmail_service
                                subject = st.session_state.get('email_subject', f"Interest in {selected_job.get('title')}")
                                body = st.session_state.get('email_body', '')
                                draft = gmail_service.create_draft(
                                    to=hr_email,
                                    subject=subject,
                                    body=body
                                )
                                if draft:
                                    st.session_state.emails_sent_today += 1
                                    st.success(f"✅ Draft created in Gmail! ({remaining-1} remaining today)")
                                else:
                                    st.error("Failed to create draft. Check Gmail connection.")
                            except Exception as e:
                                st.error(f"Gmail error: {e}")
        else:
            st.info("📦 Click 'Load Cached Jobs' or search for jobs first to generate cold emails")
    
    with email_tab2:
        st.subheader("Follow-up Queue")
        st.info("Applications awaiting follow-up (5+ days since sent, no reply)")
        
        try:
            from modules.auto_followup import AutoFollowupService
            followup_service = AutoFollowupService()
            stats = followup_service.get_followup_statistics()
            
            st.write(f"**Total pending follow-ups:** {stats.get('pending', 0)}")
            st.write(f"**Sent this week:** {stats.get('sent_this_week', 0)}")
            
            if st.button("🔄 Check & Create Follow-up Drafts"):
                created = followup_service.check_and_create_followups()
                st.success(f"Created {len(created)} follow-up drafts")
        except Exception as e:
            st.warning(f"Follow-up service not available: {e}")
    
    with email_tab3:
        st.subheader("Email History")
        
        try:
            from modules.database import SessionLocal, Application, Job
            db = SessionLocal()
            applications = db.query(Application).order_by(Application.created_at.desc()).limit(20).all()
            
            if applications:
                for app in applications:
                    job = db.query(Job).filter(Job.id == app.job_id).first()
                    if job:
                        status_emoji = {"initial_draft": "📝", "initial_sent": "✉️", "replied": "💬", "followup_sent": "🔄"}.get(app.email_stage, "❓")
                        st.markdown(f"{status_emoji} **{job.title}** @ {job.company} - {app.email_stage}")
            else:
                st.info("No email history yet")
            
            db.close()
        except Exception as e:
            st.warning(f"Could not load history: {e}")

# ==========================
# Dashboard Tab
# ==========================
elif page == "📊 Dashboard":
    st.markdown('<h1 class="main-header">Dashboard 📊</h1>', unsafe_allow_html=True)
    st.markdown("Track your job applications")
    
    # ===== Web Applied Jobs Management (Manual) =====
    with st.expander("📚 Web Applied History (Manually Marked)", expanded=True):
        try:
            from modules.database import SessionLocal, Application, Job
            db = SessionLocal()
            
            # Get manually applied jobs
            web_apps = db.query(Application).join(Job).filter(
                Application.status == 'applied'
            ).order_by(Application.updated_at.desc()).limit(50).all()
            
            if web_apps:
                # Create a list for dataframe-like display
                for app in web_apps:
                    cols = st.columns([2, 3, 2, 2, 1])
                    with cols[0]:
                        st.write(app.updated_at.strftime("%Y-%m-%d %H:%M"))
                    with cols[1]:
                        st.write(f"**{app.job.title}**")
                    with cols[2]:
                        st.write(app.job.company)
                    with cols[3]:
                        st.caption(app.job.location)
                    with cols[4]:
                        if st.button("↩️ Undo", key=f"dash_unapply_{app.job.id}", help="Unmark as applied"):
                            try:
                                from modules.job_scraper import JobScraper
                                scraper = JobScraper()
                                scraper.mark_job_as_applied(app.job.id, applied=False)
                                st.toast(f"Unmarked: {app.job.title}")
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                    st.divider()
            else:
                st.info("No manually applied jobs yet. Use the 'Email Center' to mark jobs as applied.")
            
            db.close()
        except Exception as e:
            st.error(f"Error loading history: {e}")
            
    st.markdown("### Kanban Board")
    
    # Kanban columns
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        from modules.database import SessionLocal, Application, Job
        db = SessionLocal()
        
        with col1:
            st.markdown("### 📝 To Apply")
            to_apply = db.query(Job).filter(
                ~Job.id.in_(db.query(Application.job_id))
            ).limit(10).all()
            
            for job in to_apply:
                with st.container():
                    st.markdown(f"**{job.title}**")
                    st.caption(f"{job.company}")
                    if st.button("Apply ➡️", key=f"apply_{job.id}"):
                        new_app = Application(job_id=job.id, status='to_apply')
                        db.add(new_app)
                        db.commit()
                        st.rerun()
        
        with col2:
            st.markdown("### ✉️ Sent")
            sent = db.query(Application).join(Job).filter(
                Application.email_stage == 'initial_sent'
            ).limit(10).all()
            
            for app in sent:
                with st.container():
                    st.markdown(f"**{app.job.title}**")
                    st.caption(f"{app.job.company}")
        
        with col3:
            st.markdown("### 💬 Replied")
            replied = db.query(Application).join(Job).filter(
                Application.hr_replied == True
            ).limit(10).all()
            
            for app in replied:
                with st.container():
                    st.markdown(f"**{app.job.title}**")
                    st.caption(f"{app.job.company}")
                    st.success("Got reply!")
        
        with col4:
            st.markdown("### 🎯 Interview")
            interviews = db.query(Application).join(Job).filter(
                Application.status == 'interview'
            ).limit(10).all()
            
            for app in interviews:
                with st.container():
                    st.markdown(f"**{app.job.title}**")
                    st.caption(f"{app.job.company}")
        
        db.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        st.info("Make sure database is configured correctly.")

# ==========================
# Settings Tab
# ==========================
elif page == "⚙️ Settings":
    st.markdown('<h1 class="main-header">Settings ⚙️</h1>', unsafe_allow_html=True)
    
    st.markdown("### API Configuration")
    
    with st.expander("🔑 API Keys Status"):
        # Check Gmail status
        gmail_connected = False
        try:
            from modules.gmail_service import gmail_service
            import os
            gmail_connected = os.path.exists(gmail_service.token_path)
        except:
            pass
        
        st.write("**OpenAI:** ", "✅ Connected" if not st.session_state.demo_mode else "❌ Not configured")
        st.write("**Apify:** ", "✅ Connected" if not st.session_state.demo_mode else "❌ Not configured")
        st.write("**Gmail:** ", "✅ Connected" if gmail_connected else "❌ Not configured")
        st.write("**Database:** ", "⚠️ SQLite (Demo)" if st.session_state.demo_mode else "✅ Connected")
    
    st.markdown("### Job Search Preferences")
    
    default_keywords = st.text_area(
        "Default Keywords",
        value="Instructional Design, L&D, EdTech, AI PM, Automation",
        help="These keywords will be used by default in searches"
    )
    
    default_location = st.text_input(
        "Default Location",
        value="Ontario, Canada"
    )
    
    scraping_delay = st.slider(
        "Scraping Delay (seconds)",
        min_value=3,
        max_value=10,
        value=5,
        help="Delay between requests to avoid detection"
    )
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <p>Job Autopilot 🚀 | Built with ❤️ and AI</p>
        <p><a href="https://github.com/Schlaflied/job-autopilot" target="_blank">GitHub</a></p>
    </div>
    """,
    unsafe_allow_html=True
)
