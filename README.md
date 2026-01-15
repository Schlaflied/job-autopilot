# Job Autopilot 🚀

[![GitHub stars](https://img.shields.io/github/stars/Schlaflied/job-autopilot?style=social)](https://github.com/Schlaflied/job-autopilot/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Schlaflied/job-autopilot?style=social)](https://github.com/Schlaflied/job-autopilot/network/members)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**AI-powered job application automation system** that streamlines your job search workflow using GPT-4o-mini, automated scraping, resume optimization, and intelligent cold email campaigns.

> **Perfect for**: Job seekers in EdTech, L&D, AI Product Management, and Automation fields

---

## ✨ Features

### 🎯 **Intelligent Job Discovery**
- 🔍 **Automated Indeed/LinkedIn Scraping** via Apify
- 🤖 **AI-Powered Job Scoring** (0-10 rating based on your profile)
- 📊 **Smart Categorization** (EdTech, AI PM, Automation, L&D)
- 💾 **Database Caching** (Neon PostgreSQL + Local SQLite fallback)
- 📦 **Load Cached Jobs** (reuse previous searches, save API quota)
- 📅 **Date Filtering** (post-processing filter ensures only recent jobs)

### 📄 **Resume Export & Optimization** ✨ IMPROVED
- 📤 **Multi-Format Upload**: Support PDF, DOCX, and Markdown master resumes
- 🎨 **Professional Templates**: 4 ATS-friendly templates (single/two-column, classic/modern)
- 🧠 **GPT-4o Powered**: Resume optimization uses GPT-4o for higher accuracy (other features use cost-effective GPT-4o-mini)
- 🔄 **AI Compression**: Smart compression to fit strict 1-page (350 words target)
- 📊 **ATS Scoring**: Real-time ATS compatibility score with keyword matching
- 🎯 **Job-Tailored Resumes**: AI optimizes resume for each job description
- 🔒 **Anti-Hallucination**: Iron-clad data protection - dates, locations, and company names are locked and cannot be modified by AI
- 📦 **Projects Section**: Always preserved with markdown syntax cleanup
- 🛠️ **Skills Filtering**: AI filters skills to match JD keywords
- 📥 **Export Options**: Download as PDF or DOCX with proper formatting
- 🔧 **Drag-and-Drop Sections**: Reorder resume sections interactively
- ✏️ **CRUD Experience/Education**: Add, edit, delete job entries directly in UI
- 🖼️ **Live Preview**: Real-time preview with timestamp

### 📧 **Email Center** ✨ NEW
- 📝 **Draft Cold Emails**: AI-generated personalized emails
- 📬 **Gmail Integration**: Create drafts directly in Gmail
- 📊 **Email Statistics**: Track drafts, sent, replied counts
- ⏰ **Follow-up Queue**: Auto-generate follow-up drafts
- 📜 **Email History**: View all email activities

### 📊 **Dashboard** ✨ NEW
- 📈 **Kanban Board**: Visual pipeline (To Apply → Sent → Replied → Interview)
- 📚 **Applied History**: Manage manually marked applications (Undo/View History)
- 🎯 **One-Click Apply**: Move jobs through stages
- 📧 **Status Tracking**: Real-time application status

### ✉️ **Smart Cold Email Campaigns**
- 📧 **Two-Stage Strategy**:
  - Stage 1: Brief intro (no resume, avoid spam filters)
  - Stage 2: Detailed email with optimized resume (after HR replies)
- 🤖 **AI Email Generation** (personalized for each company/role)
- 📬 **Gmail Integration** (create drafts, send emails)
- 🔔 **Reply Detection** (auto-track HR responses)
- ⏰ **Auto Follow-up** (5 days after initial email, max 1 per job)
- 🤝 **AI Disclosure** (transparent about AI-assisted outreach)

### 🎨 **Modern UI**
- 🖥️ **Streamlit Web Interface** (clean, responsive design)
- 🌓 **Dark Mode Support**
- 📱 **Mobile-Friendly**
- 🎯 **Real-time API Status** (check connection health)

---

## 🔄 Workflow

```mermaid
graph TD
    User([User Input]) -->|Keywords & Location| Scraper[Job Scraper Engine]
    Scraper -->|Apify Indeed Actor| DB[(PostgreSQL Database)]
    DB --> UI[Streamlit Dashboard]
    
    subgraph "Phase 1: Resume Engine"
    UI -->|Select Job| AI_Resume{AI Resume Tailor}
    Master[Master Resume] --> AI_Resume
    AI_Resume -->|GPT-4o Optimization| Draft[Draft Resume]
    Draft -->|Manual Edit & Reorder| Preview[Live PDF Preview]
    Preview -->|ATS Check| FinalPDF[Exported Resume]
    end
    
    subgraph "Phase 2: Outreach System"
    UI -->|Target Job| AI_mail{AI Email Generator}
    FinalPDF -->|Attach| AI_mail
    AI_mail -->|Generate| Drafts[Gmail Drafts]
    Drafts -->|Review & Send| Sent[Sent Emails]
    Sent -->|Monitor Reply| Tracker[Reply Tracker]
    Tracker -->|No Reply + 5 Days| FollowUp[Auto-Followup]
    end
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **AI/LLM** | OpenAI GPT-4o-mini |
| **Frontend** | Streamlit 1.30+ |
| **Backend** | Flask 3.0, Python 3.11+ |
| **Database** | Neon PostgreSQL (cloud) |
| **Cache** | Redis (optional) |
| **Job Scraping** | Apify (Indeed Actor) |
| **HR Contacts** | Selenium + undetected-chromedriver (LinkedIn) |
| **Email** | Gmail API (OAuth 2.0) |
| **Resume** | python-docx, ReportLab (PDF), docx2txt, pdfminer.six |
| **ORM** | SQLAlchemy 2.0 |
| **Deployment** | Docker, Docker Compose |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Git**
- **API Keys** (see [Configuration](#-configuration) section)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Schlaflied/job-autopilot.git
cd job-autopilot

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. **REQUIRED**: Create your master resume
# Create a file named "Master Resume.md" (or "[Your Name] Master Resume.md")
# Place it in the project root directory
# Format: Markdown with sections for Experience, Education, Skills
# Example:
# # Your Name
# ## Contact
# email@example.com | (123) 456-7890 | Toronto, ON
# ## Professional Summary
# Your summary here...
# ## Experience
# ### Job Title | Company | Duration
# - Achievement bullet point 1
# - Achievement bullet point 2
# ## Education
# ### Degree | University | Year
# ## Skills
# - Skill 1
# - Skill 2

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your API keys (see Configuration section)

# 6. Initialize database
python scripts/init_database.py

# 7. Run the application
streamlit run streamlit_app.py --server.port=8501
```

**Access the app**: http://localhost:8501

---

## 📁 Project Structure

```
job-autopilot/
├── modules/
│   ├── ai_agent.py              # GPT-4o-mini integration (scoring, resume, emails)
│   ├── job_scraper.py           # Apify job scraper with caching
│   ├── gmail_service.py         # Gmail API integration
│   ├── database.py              # SQLAlchemy models (Neon PostgreSQL)
│   ├── cache_manager.py         # Redis caching layer
│   ├── auto_followup.py         # Auto follow-up email generator
│   └── logger_config.py         # Centralized logging
├── scripts/
│   ├── init_database.py         # Database initialization
│   └── test_apis.py             # API connection testing
├── data/
│   ├── credentials/             # Gmail OAuth credentials (gitignored)
│   ├── resumes/                 # Generated resumes (gitignored)
│   └── logs/                    # Application logs (gitignored)
├── docs/
│   ├── AUTO_FOLLOWUP.md         # Follow-up email strategy
│   └── REDIS_SETUP.md           # Redis configuration guide
├── streamlit_app.py             # Main Streamlit UI
├── app.py                       # Flask API (optional)
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Multi-service orchestration
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

---

## ⚙️ Configuration

### Required API Keys

#### 1. **OpenAI API** (AI features)
```env
OPENAI_API_KEY=sk-proj-your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```
- Get key: https://platform.openai.com/api-keys
- Cost: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

#### 2. **Apify API** (Job scraping)
```env
APIFY_API_TOKEN=apify_api_your_token_here
APIFY_INDEED_ACTOR_ID=MXLpngmVpE8WTESQr
```
- Get token: https://console.apify.com/account/integrations
- Free tier: $5 credit (enough for ~100-200 job searches)

#### 3. **Neon PostgreSQL** (Database)
```env
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require
```
- Get database: https://neon.tech/ (free tier: 0.5GB storage)
- Copy connection string from Neon dashboard

#### 4. **Gmail API** (Email automation)
```env
GMAIL_CREDENTIALS_PATH=./data/credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=./data/credentials/gmail_token.json
```

**Setup Gmail OAuth**:
1. Go to https://console.cloud.google.com/
2. Create project → Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download JSON → Rename to `gmail_credentials.json`
5. Place in `data/credentials/`
6. Run app → First time will open browser for OAuth login

**Detailed guide**: See `data/credentials/README.md`

### Optional Services

#### Redis Cache (Optional)
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```
- **Without Redis**: System uses database caching (works fine!)
- **With Redis**: Faster repeated searches, lower API costs
- Setup guide: `docs/REDIS_SETUP.md`

#### LinkedIn Automation (Optional)
```env
LINKEDIN_ACCOUNT_1_EMAIL=yourname.job1@gmail.com
LINKEDIN_ACCOUNT_1_PASSWORD=your_password_here
# Use 2-3 burner accounts for HR contact scraping
```

---

## 🐳 Docker Deployment

### Local Docker

```bash
# Build and run
docker-compose up -d

# Access services
# Streamlit: http://localhost:8501
# Flask API: http://localhost:5000

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

#### Option 1: Heroku

```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create your-job-autopilot

# Set environment variables
heroku config:set OPENAI_API_KEY=sk-proj-your_key_here
heroku config:set APIFY_API_TOKEN=apify_api_your_token_here
heroku config:set DATABASE_URL=postgresql://...

# Deploy
git push heroku master

# Open app
heroku open
```

#### Option 2: Railway.app

1. Visit https://railway.app/
2. Sign in with GitHub
3. **New Project** → **Deploy from GitHub repo**
4. Select `Schlaflied/job-autopilot`
5. Add environment variables (same as `.env`)
6. Deploy automatically on push

#### Option 3: Google Cloud Platform (Free Tier)

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Create project
gcloud projects create job-autopilot

# Deploy to Cloud Run
gcloud run deploy job-autopilot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 📖 Usage Guide

### 1. **Job Search**

**DEMO Mode** (without API keys):
- System loads 5 sample jobs automatically
- Test UI functionality
- No API calls

**Production Mode**:
```python
1. Enter keywords: "Instructional Design, AI PM, Automation"
2. Set location: "Ontario, Canada"
3. Click "🔍 Search Jobs"
   → Calls Apify (scrapes Indeed)
   → AI scores each job (0-10)
   → Saves to Neon database

4. Click "📦 Load Cached Jobs"
   → Loads from database (no API call!)
   → Saves Apify quota
```

### 2. **Resume Optimization**

```python
1. Find high-match job (8+ score)
2. Click "✏️ Optimize Resume"
   → AI tailors resume for this job
   → Ensures ATS compatibility
   → Strictly 1-page format
   → Exports .docx + PDF
```

### 3. **Cold Email Campaign**

**Strategy**: Two-stage approach (higher reply rate)

```python
# Stage 1: Initial Contact (no resume)
1. Click "✉️ Create Draft"
2. AI generates personalized email:
   - Brief introduction (< 150 words)
   - 1 relevant project highlight
   - AI disclosure statement
   - Ask if they'd like to see resume
3. Email saved as Gmail draft
4. Manually review and send

# Stage 2: Follow-up (with resume)
5 days later:
1. System checks for HR reply
2. If no reply → generates follow-up email:
   - References initial email
   - Attaches optimized resume
   - Suggests specific meeting times
3. Max 1 follow-up per job (avoid spam)
```

**Expected Results**:
- Initial email: 1-5% reply rate
- With follow-up: 15-20% reply rate
- **3-4x improvement!**

### 4. **Application Tracking**

```python
Dashboard → View all applications:
- To Apply: Jobs you scored 8+
- Sent: Cold emails sent
- Replied: HR responded
- Interview: Scheduled meetings

Gmail integration auto-updates status!
```

---

## 🧪 Testing APIs

Test all API connections:

```bash
python scripts/test_apis.py
```

**Output example**:
```
Job Autopilot - API Connection Test
==========================================
1️⃣ Testing OpenAI API...
   ✅ OpenAI API working!

2️⃣ Testing Apify API...
   ✅ Apify API working! User: your_username

3️⃣ Testing Gmail API...
   ✅ Gmail API working! Email: your_email@gmail.com

4️⃣ Testing Neon PostgreSQL...
   ✅ Neon PostgreSQL working! Database: neondb

5️⃣ Testing Redis Cache...
   ⚠️ Not available (optional)

✅ 4/5 APIs connected successfully
🚀 System ready for Job Autopilot!
```

---

## 💰 Cost Estimate

**Monthly costs** (assuming 50 jobs/week search activity):

| Service | Cost | Notes |
|---------|------|-------|
| OpenAI GPT-4o-mini | ~$5-10/mo | Job scoring + resume + emails |
| Apify (Indeed scraper) | $0 (free tier) | $5 free credit → ~200 searches |
| Neon PostgreSQL | $0 (free tier) | 0.5GB storage, auto-scale |
| Gmail API | $0 | Free for personal use |
| Redis (optional) | $0 | Local/Upstash free tier |
| **Total** | **$5-10/mo** | Scalable to 100+ applications |

**ROI**: If this system helps you land **1 job**, the $60/year cost is negligible!

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'X'"
```bash
pip install -r requirements.txt
```

### "DATABASE_URL not found - running in DEMO mode"
- Check `.env` file exists
- Ensure `DATABASE_URL=postgresql://...` is set
- Restart application

### "Gmail API: Token not found"
- Run OAuth flow: Open app → Try creating email draft
- Browser will open for Gmail login
- Approve permissions
- Token auto-saves to `data/credentials/gmail_token.json`

### "Apify: User was not found"
- Check `APIFY_API_TOKEN` in `.env`
- Verify token at https://console.apify.com/account/integrations

### "Load Cached Jobs: No cached jobs found"
- You need to search jobs first (to populate database)
- Click "🔍 Search Jobs" before using "📦 Load Cached"

### Port 8501 already in use
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8501 | xargs kill -9

# Or use different port
streamlit run streamlit_app.py --server.port=8502
```

---

## 🤝 Contributing

Contributions are welcome! This is an open-source project to help job seekers.

**Ways to contribute**:
1. 🐛 Report bugs (GitHub Issues)
2. 💡 Suggest features (GitHub Discussions)
3. 🔧 Submit pull requests
4. 📚 Improve documentation
5. ⭐ Star the repo (helps others discover it!)

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** - see the [LICENSE](LICENSE) file for details.

### What This Means:

- **Open Source**: You are free to use, modify, and distribute this software.
- **Copyleft (Viral)**: If you modify this software and distribute it (or host it as a service), you *must* open-source your modifications under the same AGPL-3.0 license.
- **State Changes**: You must state significant changes made to the software.
- **Network Use**: Users interacting with this software over a network are entitled to receive the source code.

For full details, please read the [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o-mini API
- **Apify** for job scraping infrastructure
- **Neon** for generous free PostgreSQL tier
- **Streamlit** for amazing UI framework
- **[Resume-Matcher](https://github.com/srbhr/Resume-Matcher)** for inspiring our PDF/DOCX parsing approach using `pdfminer.six` and `docx2txt`
- Job seekers worldwide struggling with manual applications 💪

---

## 📞 Contact

**Author**: Built with ❤️ and AI

**GitHub**: https://github.com/Schlaflied/job-autopilot

**Issues**: https://github.com/Schlaflied/job-autopilot/issues

---

## 🎯 Roadmap

- [ ] Multi-language support (French, Spanish)
- [ ] A/B testing for cold emails
- [ ] LinkedIn auto-messaging (post-email)
- [ ] Salary negotiation AI assistant
- [ ] Interview prep AI coach
- [ ] Chrome extension for one-click apply

**Want to see a feature?** Open an issue!

---

## ⚠️ Disclaimer

This tool is designed to **assist** job seekers, not replace human effort. Always:
- ✅ Review AI-generated content before sending
- ✅ Personalize emails for each company
- ✅ Follow LinkedIn/platform terms of service
- ✅ Disclose AI assistance (we do this automatically)
- ✅ Use burner LinkedIn accounts for scraping (protect your main profile)

**Ethical use only!** 🤝

---

<div align="center">

**⭐ Star this repo if it helped you land a job! ⭐**

[Report Bug](https://github.com/Schlaflied/job-autopilot/issues) · [Request Feature](https://github.com/Schlaflied/job-autopilot/issues) · [Documentation](https://github.com/Schlaflied/job-autopilot/wiki)

</div>
