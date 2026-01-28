"""
Coffee Chat Center - Main Dashboard
"""
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.coffee_chat_models import UserProfile, CoffeeChatContact
from modules.database import Job

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Coffee Chat Center",
    page_icon="☕",
    layout="wide"
)

# Database connection
@st.cache_resource
def get_db_session():
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

session = get_db_session()

# Check if user profile is configured
profile = session.query(UserProfile).first()

if not profile or not profile.schools or not profile.target_fields:
    st.warning("⚠️ Please configure your User Profile first")
    st.info("👉 Go to User Profile page to set up your schools and target fields")
    
    if st.button("📝 Go to User Profile"):
        st.switch_page("pages/user_profile.py")
    
    st.stop()

# Page header
st.title("☕ Coffee Chat Center")
st.markdown("Find and connect with alumni, supervisors, and professionals")

# Display user configuration summary
with st.expander("📊 Your Configuration", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Schools", len(profile.schools))
        for school in profile.schools:
            st.caption(f"• {school['name']} (Priority {school['priority']})")
    
    with col2:
        st.metric("Target Fields", len(profile.target_fields))
        for field in profile.target_fields:
            st.caption(f"• {field}")
    
    with col3:
        st.metric("Daily Limits", f"{profile.daily_connection_limit + profile.daily_message_limit}")
        st.caption(f"Connections: {profile.daily_connection_limit}/day")
        st.caption(f"Messages: {profile.daily_message_limit}/day")

st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Quick Stats
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.header("📈 Quick Stats")

col1, col2, col3, col4 = st.columns(4)

# Count contacts by status
total_contacts = session.query(CoffeeChatContact).count()
pending_connections = session.query(CoffeeChatContact).filter(
    CoffeeChatContact.connection_status == 'pending'
).count()
connected = session.query(CoffeeChatContact).filter(
    CoffeeChatContact.connection_status == 'accepted'
).count()
replied = session.query(CoffeeChatContact).filter(
    CoffeeChatContact.replied_at.isnot(None)
).count()

with col1:
    st.metric("Total Contacts", total_contacts)

with col2:
    st.metric("Pending Connections", pending_connections)

with col3:
    st.metric("Connected", connected)

with col4:
    st.metric("Replied", replied)

st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Load Jobs Section
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.header("📦 Load High-Value Jobs")
st.markdown("Select jobs to search for alumni at these companies")

# Initialize session state
if 'selected_job_ids' not in st.session_state:
    st.session_state.selected_job_ids = set()

col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

with col1:
    min_score = st.slider("Minimum Job Score", 0, 10, 7, help="Only show jobs with this score or higher")

with col2:
    load_all = st.checkbox("Load All Cached Jobs", value=False, help="Load all jobs from database (ignore date range)")

with col3:
    if not load_all:
        days_back = st.slider("Days to Look Back", 1, 30, 7, help="Show jobs from the last N days")
    else:
        st.caption("Loading all cached jobs")
        days_back = None

with col4:
    if st.button("📦 Load Jobs", type="primary", use_container_width=True):
        st.rerun()

# Load jobs
from datetime import datetime, timedelta
from modules.job_contact_integrator import JobContactIntegrator

integrator = JobContactIntegrator()

if load_all:
    # Load ALL cached jobs (no date limit)
    all_jobs = session.query(Job).filter(
        Job.match_score >= min_score
    ).order_by(Job.match_score.desc()).all()
    high_value_jobs = all_jobs
    st.info(f"📦 Loading all cached jobs with score ≥ {min_score} (no date limit)")
else:
    # Load recent jobs only
    high_value_jobs = integrator.get_high_value_jobs(days=days_back, min_score=min_score)

if high_value_jobs:
    st.success(f"✅ Found {len(high_value_jobs)} high-value jobs!")
    
    # Select/Deselect All
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ Select All"):
            st.session_state.selected_job_ids = {job.id for job in high_value_jobs}
            st.rerun()
    with col_b:
        if st.button("❌ Deselect All"):
            st.session_state.selected_job_ids = set()
            st.rerun()
    
    st.markdown(f"**Selected: {len(st.session_state.selected_job_ids)} jobs**")
    
    # Display jobs with checkboxes
    for job in high_value_jobs:
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Checkbox for selection
                is_selected = job.id in st.session_state.selected_job_ids
                checkbox_key = f"job_select_{job.id}"
                
                if st.checkbox(
                    f"**{job.title}** @ {job.company}",
                    value=is_selected,
                    key=checkbox_key
                ):
                    st.session_state.selected_job_ids.add(job.id)
                else:
                    st.session_state.selected_job_ids.discard(job.id)
                
                # Job details
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.caption(f"📍 {job.location}")
                with col_b:
                    st.caption(f"💰 {job.salary}")
                with col_c:
                    # Posted date
                    if job.job_age:
                        st.caption(f"📅 Posted {job.job_age}")
                    elif job.posted_date:
                        posted_str = str(job.posted_date)[:10] if job.posted_date else "Unknown"
                        st.caption(f"📅 Posted {posted_str}")
                    else:
                        st.caption("📅 Date unknown")
                with col_d:
                    # Remote/On-site
                    if job.is_remote:
                        st.caption("🏠 Remote")
                    else:
                        st.caption("🏬 On-site")
                
                # Apply link
                apply_url = job.apply_url or job.job_url
                if apply_url:
                    st.markdown(f"[🔗 Apply Now]({apply_url})")
                
                # Domain info
                if job.company_domain:
                    st.caption(f"🔑 Domain: {job.company_domain}")
                else:
                    st.caption("⚠️ No domain")
            
            with col2:
                # Score badge
                score = job.match_score or 0
                if score >= 8:
                    st.success(f"**{score}/10**")
                elif score >= 6:
                    st.warning(f"**{score}/10**")
                else:
                    st.info(f"**{score}/10**")
            
            st.divider()
    
    # Action buttons
    st.markdown("### 🚀 Next Steps")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(
            f"🔍 Search LinkedIn for {len(st.session_state.selected_job_ids)} Companies",
            type="primary",
            use_container_width=True,
            disabled=len(st.session_state.selected_job_ids) == 0
        ):
            # Get selected jobs and their domains or company names
            selected_jobs = [j for j in high_value_jobs if j.id in st.session_state.selected_job_ids]
            
            # Collect either domain or company name
            search_targets = []
            for job in selected_jobs:
                if job.company_domain:
                    search_targets.append({'type': 'domain', 'value': job.company_domain, 'company': job.company})
                else:
                    search_targets.append({'type': 'company', 'value': job.company, 'company': job.company})
            
            if not search_targets:
                st.error("❌ No companies found in selected jobs")
            else:
                # Store in session for LinkedIn search
                st.session_state.linkedin_search_targets = search_targets
                st.session_state.linkedin_search_school = profile.schools[0]['name'] if profile.schools else "University of Western Ontario"
                
                domains_count = len([t for t in search_targets if t['type'] == 'domain'])
                companies_count = len([t for t in search_targets if t['type'] == 'company'])
                
                st.success(f"✅ Ready to search {len(search_targets)} companies!")
                if domains_count > 0:
                    st.caption(f"📧 {domains_count} with domain")
                if companies_count > 0:
                    st.caption(f"🏢 {companies_count} by company name")
                st.info(f"🎓 School: {st.session_state.linkedin_search_school}")
                
                # Show launch button
                st.session_state.show_linkedin_launch = True
    
    # LinkedIn Launch Section (after clicking search button)
    if st.session_state.get('show_linkedin_launch'):
        st.markdown("---")
        st.subheader("🚀 Launch LinkedIn Automation")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write("**Companies to search:**")
            for target in st.session_state.get('linkedin_search_targets', [])[:5]:
                icon = "📧" if target['type'] == 'domain' else "🏢"
                st.caption(f"{icon} {target['company']} ({target['value']})")
            if len(st.session_state.get('linkedin_search_targets', [])) > 5:
                st.caption(f"... and {len(st.session_state.get('linkedin_search_targets', [])) - 5} more")
        
        with col_b:
            st.write(f"**School:** {st.session_state.get('linkedin_search_school', 'Not set')}")
            max_connect = st.slider("Max connections per company", 1, 10, 5)
        
        if st.button("🌐 Launch Chrome & Connect", type="primary", use_container_width=True):
            import subprocess
            
            # Get first target
            targets = st.session_state.get('linkedin_search_targets', [])
            if targets:
                first_target = targets[0]
                search_keyword = first_target['value']
                school = st.session_state.get('linkedin_search_school', 'University of Western Ontario')
                
                st.info(f"🚀 Launching LinkedIn automation for: {first_target['company']}")
                st.warning("⚠️ Chrome will open. Please login to LinkedIn if needed.")
                
                # Run the script in a new terminal window with correct arguments
                project_dir = os.path.dirname(os.path.dirname(__file__)).replace(chr(92), '/')
                
                # Launch in new PowerShell window with company/school/limit arguments
                subprocess.Popen([
                    'powershell', '-NoExit', '-Command',
                    f'cd "{project_dir}"; python scripts/linkedin_auto_connect.py --company "{search_keyword}" --school "{school}" --limit {max_connect}'
                ], creationflags=subprocess.CREATE_NEW_CONSOLE)
                
                st.session_state.linkedin_running = True
                st.success("✅ LinkedIn automation launched in new terminal window!")
    
    with col2:
        if st.button(
            "📊 View Company Summary",
            use_container_width=True,
            disabled=len(st.session_state.selected_job_ids) == 0
        ):
            # Show summary of selected companies
            selected_jobs = [j for j in high_value_jobs if j.id in st.session_state.selected_job_ids]
            companies_with_domain = set([j.company_domain for j in selected_jobs if j.company_domain])
            companies_without_domain = set([j.company for j in selected_jobs if not j.company_domain])
            
            st.markdown("#### Selected Companies:")
            st.markdown(f"**With Domain ({len(companies_with_domain)}):**")
            for domain in companies_with_domain:
                st.markdown(f"- {domain}")
            
            st.markdown(f"**Without Domain ({len(companies_without_domain)}):**")
            for company in companies_without_domain:
                st.markdown(f"- {company}")

else:
    st.warning(f"⚠️ No jobs found with score ≥ {min_score} in the last {days_back} days")
    st.info("💡 Try lowering the score threshold or running the job scraper first")

integrator.close()

st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Contact List
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Automation Actions (Integrated MCP)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.header("🤖 Outreach Actions")
st.caption("New: Integrated Browser Control (No PowerShell needed)")

# Session state for draft
if 'draft_message' not in st.session_state:
    st.session_state.draft_message = ""
if 'current_processing_contact' not in st.session_state:
    st.session_state.current_processing_contact = None

from modules.linkedin_agent_v2 import LinkedInAgentV2
agent_v2 = LinkedInAgentV2()

# Browser Status
col_status, col_btn = st.columns([3, 1])
with col_status:
    st.info("Ensure Chrome is open with debugging port 9222 (run chrome.exe --remote-debugging-port=9222)")
with col_btn:
    if st.button("🔗 Test Connection"):
        if agent_v2.connect_browser():
            st.success("Connected to Chrome!")
        else:
            st.error("Failed to connect to localhost:9222")

st.divider()

# List contacts with actions
st.subheader("Priority Contacts for Outreach")

contacts = session.query(CoffeeChatContact).order_by(
    CoffeeChatContact.priority_score.desc()
).limit(10).all()

for contact in contacts:
    with st.expander(f"{contact.name} ({contact.current_title}) - Score: {contact.priority_score:.1f}", expanded=False):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(f"**Company**: {contact.current_company}")
            st.write(f"**School**: {contact.school_name}")
            st.caption(f"Status: {contact.status}")
        
        with c2:
            # Action 1: Deep Dive & Draft
            if st.button("📝 1. Dive & Draft", key=f"draft_{contact.id}"):
                with st.spinner(f"Navigating to {contact.name}..."):
                    res = agent_v2.deep_dive_and_generate_draft(contact.name, contact.linkedin_url)
                    if res.get('success'):
                        st.session_state.draft_message = res['draft']
                        st.session_state.current_processing_contact = contact.name
                        st.success("Draft Generated!")
                        st.rerun()
                    else:
                        st.error(str(res.get('error')))
        
        # Draft Area (if active for this contact)
        if st.session_state.current_processing_contact == contact.name:
            st.markdown("---")
            st.markdown("#### Message Draft")
            edited_draft = st.text_area("Review Message", value=st.session_state.draft_message, height=200, key=f"text_{contact.id}")
            st.session_state.draft_message = edited_draft
            
            c3, c4 = st.columns(2)
            with c3:
                # Action 2: Click Message Button
                if st.button("🖱️ 2. Open Message Box", key=f"open_{contact.id}"):
                    if agent_v2.open_message_box().get('success'):
                        st.success("Message box opened!")
                    else:
                        st.warning("Could not find 'Message' button (try manually clicking)")
            
            with c4:
                # Action 3: Paste
                if st.button("📋 3. Paste to LinkedIn", type="primary", key=f"paste_{contact.id}"):
                    res = agent_v2.paste_message(st.session_state.draft_message)
                    if res.get('success'):
                        st.success("Pasted! Please review and click Send manually.")
                        # Update status (Optional)
                        # contact.status = 'drafted'
                        # session.commit()
                    else:
                        st.error("Paste failed. Please focus the message box manually and try again.")
            st.markdown("---")
            
st.divider()

# Footer
st.caption("Agent V2 enabled. Manual review required before sending.")
