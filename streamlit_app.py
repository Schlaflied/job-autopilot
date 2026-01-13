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

# Page configuration
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
        ["🔍 Job Search", "📄 Resume Export", "📊 Dashboard", "⚙️ Settings"],
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
                    
                    st.session_state.jobs = sorted(jobs, key=lambda x: x.get('match_score', 0), reverse=True)
                    st.success(f"✅ Found and scored {len(jobs)} jobs!")
                
                streamlit_logger.info(f"Job search completed: {keywords}")
            
            except Exception as e:
                st.error(f"Search failed: {e}")
                streamlit_logger.error(f"Job search error: {e}", exc_info=True)
    
    elif load_cached_clicked:
        with st.spinner("Loading cached jobs from database..."):
            try:
                # Load from database
                scraper = JobScraper()
                cached_jobs = scraper.get_recent_jobs(days=7)  # Last 7 days
                
                if cached_jobs:
                    # Convert SQLAlchemy objects to dicts
                    jobs = []
                    for job in cached_jobs:
                        job_dict = {
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
                    st.markdown(f"💰 {job.get('salary', 'Not specified')} | 🏠 {'Remote' if job.get('is_remote') else 'On-site'}")
                    
                    with st.expander("📄 Description"):
                        st.write(job.get('description', 'No description')[:500] + "...")
                    
                    st.caption(f"🎯 **Match Reasoning:** {job.get('match_reasoning', 'N/A')}")
                
                with cols[1]:
                    st.markdown(f'<div class="score-badge {badge_class}">{score}/10</div>', unsafe_allow_html=True)
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

elif page == "📊 Dashboard":
    st.markdown('<h1 class="main-header">Application Dashboard 📊</h1>', unsafe_allow_html=True)
    
    st.info("📋 Application tracking will be available once database is connected")
    
    # Demo kanban board
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 📝 To Apply")
        st.metric("Jobs", 3)
    
    with col2:
        st.markdown("### ✉️ Sent")
        st.metric("Applications", 0)
    
    with col3:
        st.markdown("### 💬 Replied")
        st.metric("Responses", 0)
    
    with col4:
        st.markdown("### 📅 Interview")
        st.metric("Scheduled", 0)

elif page == "📄 Resume Export":
    st.markdown('<h1 class="main-header">Resume Export 📄</h1>', unsafe_allow_html=True)
    st.markdown("Create tailored, ATS-optimized resumes with AI")
    
    # Initialize session state for resume export
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = None
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None
    if 'compressed_resume' not in st.session_state:
        st.session_state.compressed_resume = None
    
    # Step progress indicator
    steps = ["📤 Upload", "🎨 Template", "✂️ Customize", "🤖 AI Compress", "📊 ATS Score", "💾 Export"]
    current_step = 0
    if st.session_state.resume_data:
        current_step = 1
    if st.session_state.selected_template:
        current_step = 2
    if st.session_state.compressed_resume:
        current_step = 4
    
    # Visual progress bar
    progress_cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with progress_cols[i]:
            if i < current_step:
                st.markdown(f"✅ **{step}**")
            elif i == current_step:
                st.markdown(f"🔵 **{step}**")
            else:
                st.markdown(f"⚪ {step}")
    
    st.markdown("---")
    
    # ===== STEP 1: Upload Master Resume =====
    st.markdown("### 📤 Step 1: Upload Master Resume")
    
    uploaded_file = st.file_uploader(
        "Upload your master resume",
        type=["md", "pdf", "docx"],
        help="Supports Markdown, PDF, and Word documents"
    )
    
    # Only parse if file changed
    if uploaded_file and (not st.session_state.resume_data or 
                          uploaded_file.name != st.session_state.get('last_uploaded_file', '')):
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        with st.spinner(f"📄 Parsing {file_type.upper()} resume..."):
            try:
                # Save uploaded file temporarily
                temp_path = f"data/temp_resume.{file_type}"
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Parse based on file type
                if file_type == "md":
                    resume_data = resume_generator.load_master_resume(temp_path)
                elif file_type == "pdf":
                    resume_data = resume_generator.parse_pdf_resume(temp_path)
                elif file_type == "docx":
                    resume_data = resume_generator.parse_docx_resume(temp_path)
                
                if resume_data:
                    st.session_state.resume_data = resume_data
                    st.session_state.last_uploaded_file = uploaded_file.name
                    st.success(f"✅ Resume loaded: {resume_data.get('name', 'Unknown')}")
                    
                    # Show resume preview
                    with st.expander("👁️ Preview Resume"):
                        st.json(resume_data)
                else:
                    st.error("❌ Failed to parse resume. Please check the file format.")
            
            except Exception as e:
                st.error(f"❌ Error parsing resume: {e}")
                streamlit_logger.error(f"Resume parsing error: {e}", exc_info=True)
    
    elif st.session_state.resume_data:
        # Already loaded
        st.success(f"✅ Resume loaded: {st.session_state.resume_data.get('name', 'Unknown')}")
        with st.expander("👁️ Preview Resume"):
            st.json(st.session_state.resume_data)
    
    # ===== STEP 2: Template Selection =====
    if st.session_state.resume_data:
        st.markdown("---")
        st.markdown("### 🎨 Step 2: Choose a Template")
        
        # Load template previews
        template_options = [
            {"name": "classic_single_column", "display": "Classic Single", "desc": "ATS-friendly", "img": "classic_single.jpg"},
            {"name": "modern_single_column", "display": "Modern Single", "desc": "Clean design", "img": "modern_single.jpg"},
            {"name": "classic_two_column", "display": "Classic Two-Column", "desc": "Professional", "img": "classic_two.jpg"},
            {"name": "modern_two_column", "display": "Modern Two-Column", "desc": "Contemporary", "img": "modern_two.jpg"}
        ]
        
        cols = st.columns(4)
        for i, template in enumerate(template_options):
            with cols[i]:
                img_path = f"assets/templates/{template['img']}"
                if os.path.exists(img_path):
                    st.image(img_path, use_column_width=True, caption=template['display'])
                else:
                    st.info(f"🎨 {template['display']}")
                
                st.caption(template['desc'])
                
                if st.button("Select", key=f"select_{template['name']}", use_container_width=True):
                    st.session_state.selected_template = template['name']
                    # Don't rerun - just update state
        
        if st.session_state.selected_template:
            st.info(f"📋 Current template: **{st.session_state.selected_template}**")
    
    # ===== STEP 3: Customize Resume =====
    if st.session_state.selected_template:
        st.markdown("---")
        st.markdown("### ✂️ Step 3: Customize Resume")
        
        # Load template config
        template_config = resume_generator.load_template(st.session_state.selected_template)
        
        if template_config:
            # Section Reordering
            st.markdown("#### 📋 Section Order")
            st.caption("Drag to reorder sections (or use arrows)")
            
            current_sections = template_config.get('section_order', ['summary', 'experience', 'skills', 'education'])
            
            # Arrow button method (mobile-friendly)
            col_sections = st.columns(4)
            for idx, section in enumerate(current_sections):
                with col_sections[idx % 4]:
                    st.write(f"**{idx + 1}.** {section.title()}")
                    subcol1, subcol2 = st.columns(2)
                    with subcol1:
                        if idx > 0 and st.button("⬆️", key=f"up_{section}"):
                            current_sections[idx], current_sections[idx-1] = current_sections[idx-1], current_sections[idx]
                    with subcol2:
                        if idx < len(current_sections) - 1 and st.button("⬇️", key=f"down_{section}"):
                            current_sections[idx], current_sections[idx+1] = current_sections[idx+1], current_sections[idx]
            
            # Line Spacing Adjustment
            st.markdown("#### 📏 Line Spacing")
            line_spacing = st.slider(
                "Adjust line spacing to fit content on 1 page",
                min_value=0.8,
                max_value=1.5,
                value=template_config.get('line_spacing', 1.0),
                step=0.1,
                help="Lower spacing = more content fits on 1 page"
            )
            
            # Word Count Estimate
            if st.session_state.resume_data:
                word_count = resume_generator._count_words(st.session_state.resume_data)
                layout = template_config.get('layout', 'single_column')
                max_words = 700 if layout == 'two_column' else 600
                
                st.info(f"📊 Current word count: **{word_count}** words | Target: ≤{max_words} words")
                
                if word_count > max_words:
                    st.warning(f"⚠️ Resume too long! Use AI compression to reduce to ~{max_words} words.")
    
    # ===== STEP 4: AI Compression =====
    if st.session_state.selected_template and st.session_state.resume_data:
        st.markdown("---")
        st.markdown("### 🤖 Step 4: AI Compression (1-Page Constraint)")
        
        # Select a job for tailoring
        st.markdown("#### 🎯 Select Target Job (Optional)")
        
        if st.session_state.jobs:
            job_names = [f"{j.get('title', 'Unknown')} @ {j.get('company', 'Unknown')}" for j in st.session_state.jobs]
            job_names.insert(0, "None - Generic compression")
            
            selected_job_idx = st.selectbox(
                "Choose a job to tailor this resume for:",
                range(len(job_names)),
                format_func=lambda x: job_names[x]
            )
            
            selected_job = None if selected_job_idx == 0 else st.session_state.jobs[selected_job_idx - 1]
        else:
            st.info("💡 No jobs found. Add some jobs from Job Search first, or proceed with generic compression.")
            selected_job = None
        
        # Compression mode
        st.markdown("#### ⚙️ Compression Strategy")
        
        st.warning("⚠️ **IMPORTANT**: Compression may remove details. Use 'No Compression' to keep full resume.")
        
        compression_mode = st.radio(
            "How much to compress?",
            ["No Compression (Keep Full Resume)", "Conservative (60%)", "Balanced (70%)", "Aggressive (80%)"],
            index=0,
            help="Higher compression = shorter resume. 'No Compression' keeps ALL details.",
            horizontal=False
        )
        
        mode_map = {
            "No Compression (Keep Full Resume)": "none",
            "Conservative (60%)": "conservative",
            "Balanced (70%)": "balanced",
            "Aggressive (80%)": "aggressive"
        }
        mode = mode_map[compression_mode]
        
        if st.button("🤖 Process Resume", type="primary"):
            if mode == "none":
                # No compression - just use original resume
                st.session_state.compressed_resume = st.session_state.resume_data.copy()
                st.session_state.compressed_resume['_word_count'] = resume_generator._count_words(st.session_state.resume_data)
                st.success(f"✅ Using full resume ({st.session_state.compressed_resume['_word_count']} words)")
            else:
                # Compress with AI
                with st.spinner("🤖 AI is optimizing your resume... (10-15 seconds)"):
                    try:
                        progress_bar = st.progress(0)
                        
                        # Prepare job description
                        job_description = selected_job.get('description', 'General resume') if selected_job else "General resume"
                        
                        progress_bar.progress(30)
                        
                        # Compress
                        compressed = resume_generator.compress_to_one_page(
                            st.session_state.resume_data,
                            job_description,
                            template_config,
                            mode
                        )
                        
                        progress_bar.progress(100)
                        
                        if compressed:
                            st.session_state.compressed_resume = compressed
                            st.success(f"✅ Resume compressed to {compressed.get('_word_count', 0)} words!")
                            
                            # Show comparison
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Original", f"{resume_generator._count_words(st.session_state.resume_data)} words")
                            with col2:
                                st.metric("Compressed", f"{compressed.get('_word_count', 0)} words", 
                                         delta=f"-{resume_generator._count_words(st.session_state.resume_data) - compressed.get('_word_count', 0)}")
                        else:
                            st.error("❌ Compression failed. Please try again.")
                    
                    except Exception as e:
                        st.error(f"❌ Compression error: {e}")
                        streamlit_logger.error(f"Compression error: {e}", exc_info=True)
    
    # ===== STEP 5: ATS Score =====
    if st.session_state.compressed_resume and selected_job:
        st.markdown("---")
        st.markdown("### 📊 Step 5: ATS Score")
        
        if st.button("📊 Calculate ATS Score"):
            with st.spinner("Analyzing resume vs job description..."):
                try:
                    resume_text = json.dumps(st.session_state.compressed_resume)
                    jd_text = selected_job.get('description', '')
                    
                    ats_result = ats_scorer.score_resume(resume_text, jd_text)
                    
                    # Display score
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("ATS Match Score", f"{ats_result['score']}/100")
                    with col2:
                        st.metric("Missing Keywords", len(ats_result['missing_keywords']))
                    with col3:
                        score_class = "high" if ats_result['score'] >= 70 else ("medium" if ats_result['score'] >= 50 else "low")
                        st.markdown(f"**Status:** {'✅ Good' if score_class == 'high' else ('⚠️ Moderate' if score_class == 'medium' else '❌ Low')}")
                    
                    # Missing keywords
                    if ats_result['missing_keywords']:
                        with st.expander("❌ Missing Keywords"):
                            st.write(", ".join(ats_result['missing_keywords'][:10]))
                    
                    # Suggestions
                    if ats_result['suggestions']:
                        with st.expander("💡 Improvement Suggestions"):
                            for suggestion in ats_result['suggestions']:
                                st.markdown(f"- {suggestion}")
                
                except Exception as e:
                    st.error(f"❌ ATS scoring error: {e}")
    
    # ===== STEP 6: Export =====
    if st.session_state.compressed_resume or st.session_state.resume_data:
        st.markdown("---")
        st.markdown("### 💾 Step 6: Export Resume")
        
        # Determine which resume to export
        export_data = st.session_state.compressed_resume if st.session_state.compressed_resume else st.session_state.resume_data
        
        # Apply template if selected
        if st.session_state.selected_template:
            template_config = resume_generator.load_template(st.session_state.selected_template)
            if template_config:
                export_data = resume_generator.apply_template(export_data, template_config)
                st.success(f"✅ Template applied: {template_config['name']}")
        
        # Format selection guide
        st.info("""
📥 **Export Format Guide:**
- **DOCX**: Editable format, best for ATS systems
- **PDF**: Professional appearance, best for email attachments
- **Recommendation**: Export both!
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download DOCX", type="primary", use_container_width=True):
                with st.spinner("Generating DOCX..."):
                    try:
                        filename = f"resume_{export_data.get('name', 'user').replace(' ', '_')}.docx"
                        path = resume_generator.export_docx(export_data, filename)
                        st.success(f"✅ Resume exported: `{path}`")
                    except Exception as e:
                        st.error(f"❌ Export failed: {e}")
                        streamlit_logger.error(f"DOCX export error: {e}", exc_info=True)
        
        with col2:
            if st.button("📥 Download PDF", type="primary", use_container_width=True):
                with st.spinner("Generating PDF..."):
                    try:
                        filename = f"resume_{export_data.get('name', 'user').replace(' ', '_')}.pdf"
                        path = resume_generator.export_pdf(export_data, filename)
                        st.success(f"✅ Resume exported: `{path}`")
                    except Exception as e:
                        st.error(f"❌ Export failed: {e}")
                        streamlit_logger.error(f"PDF export error: {e}", exc_info=True)
        
        # Version History (placeholder)
        st.markdown("---")
        st.markdown("#### 📚 Version History")
        st.info("💡 Version history feature coming soon! All exports will be saved automatically.")

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
