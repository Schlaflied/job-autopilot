# Job Autopilot 🚀

**AI-Driven Job Application Automation System**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Automate your job search with AI-powered resume optimization, intelligent HR contact discovery, and personalized cold email campaigns.

## 🎯 Features

- **🔍 Smart Job Discovery**: Scrapes LinkedIn & Indeed for relevant positions (EdTech, L&D, AI roles)
- **🤖 AI-Powered Matching**: GPT-4o-mini scores jobs (0-10) based on your profile
- **📄 ATS-Optimized Resumes**: Generates keyword-rich .docx & PDF resumes (1-page)
- **👤 HR Contact Finder**: Automated LinkedIn scraping + Lusha API for decision-makers
- **✉️ Two-Stage Cold Emails**: Initial contact → Follow-up with resume (Gmail API)
- **📊 Reply Detection**: Automatically tracks HR responses (V1)
- **💾 Smart Caching**: Redis reduces API costs by 60%

## 🛠 Tech Stack

- **Frontend**: Streamlit (Port 7000)
- **Backend**: Python 3.11+, Flask 3.0+
- **Database**: Neon PostgreSQL (Cloud)
- **AI**: OpenAI GPT-4o-mini, LangChain
- **Automation**: Selenium, undetected-chromedriver
- **Deployment**: Docker + Docker Compose

## 📋 Prerequisites

- Docker & Docker Compose
- API Keys:
  - OpenAI API Key
  - Apify API Token
  - Lusha API Key (optional)
  - Gmail API Credentials (OAuth 2.0)
- Neon PostgreSQL Database URL
- 2-3 LinkedIn accounts (for scraping)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Schlaflied/job-autopilot.git
cd job-autopilot
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

### 3. Run with Docker

```bash
docker-compose up -d
```

### 4. Access the Application

- **Streamlit UI**: http://localhost:7000
- **Flask API**: http://localhost:5000

## 📁 Project Structure

```
job-autopilot/
├── modules/
│   ├── job_scraper.py          # Apify job scraping
│   ├── linkedin_scraper.py     # LinkedIn HR contact discovery
│   ├── ai_agent.py             # GPT job scoring & resume optimization
│   ├── resume_generator.py     # ATS-friendly .docx/.pdf generation
│   ├── gmail_service.py        # Gmail API + reply detection
│   ├── cache_manager.py        # Redis caching layer
│   └── database.py             # Neon PostgreSQL models
├── templates/
│   └── resume_template.html    # Jinja2 resume template
├── logs/                       # Log files
├── data/                       # Generated resumes & credentials
├── app.py                      # Flask API
├── streamlit_app.py            # Streamlit frontend
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 📖 Usage Guide

### Step 1: Search Jobs
1. Open http://localhost:7000
2. Enter keywords: "Instructional Design, AI PM, Automation"
3. Select location: "Ontario, Canada"
4. Click **Search** → View scored job listings (0-10)

### Step 2: Optimize Resume
1. Click **Optimize Resume** on any job card
2. AI generates tailored 1-page resume (ATS-optimized)
3. Download as .docx or PDF

### Step 3: Cold Email
1. Click **Create Draft** → System finds HR contact
2. AI generates personalized email (Stage 1: no attachment)
3. Draft saved to Gmail → Send manually
4. System auto-detects replies → Notifies for Stage 2 follow-up

### Step 4: Track Applications
- View all applications in **Application Tracker**
- Monitor reply status
- Update notes and stages

## 🔧 Configuration

### LinkedIn Accounts Setup

Create 2-3 LinkedIn accounts with different emails:

```env
LINKEDIN_ACCOUNT_1_EMAIL=yourname.job1@gmail.com
LINKEDIN_ACCOUNT_1_PASSWORD=your_password
LINKEDIN_ACCOUNT_2_EMAIL=yourname.career@outlook.com
LINKEDIN_ACCOUNT_2_PASSWORD=your_password
```

**Safety Tips**:
- Use separate accounts (not your main profile)
- Limit to 10 companies/day per account
- System auto-rotates accounts

### API Keys

```env
OPENAI_API_KEY=sk-...
APIFY_API_TOKEN=apify_api_...
LUSHA_API_KEY=... (optional)
DATABASE_URL=postgresql://user:pass@...neon.tech/dbname
```

## 📊 Cost Estimate

| Service | Usage | Cost |
|---------|-------|------|
| OpenAI GPT-4o-mini | 20 jobs/day, 3 days/week | $3-5/month |
| Apify | Job scraping | $0 (free tier) |
| Lusha | Backup HR contacts | $0 (5 credits/month) |
| Neon PostgreSQL | Database | $0 (free tier) |
| **Total** | | **$3-5/month** |

## 🐛 Troubleshooting

### Streamlit Errors

Check logs:
```bash
docker-compose logs -f streamlit
# Logs saved to: logs/streamlit.log
```

### LinkedIn Scraper Issues

If CAPTCHA detected:
- System auto-pauses
- Check `logs/scraper.log`
- Manually complete CAPTCHA or switch to Lusha fallback

### Gmail API Quota

- Daily limit: 10,000 requests
- Reply detection: 1/hour (24 requests/day)
- Well within quota

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 👤 Author

**Yuting Sun**
- Portfolio: https://syttt.my.canva.site/
- LinkedIn: https://www.linkedin.com/in/yuting-sun-48bbb4211/
- GitHub: https://github.com/Schlaflied

## 🙏 Acknowledgments

- OpenAI for GPT-4o-mini API
- Apify for job scraping infrastructure
- Streamlit for rapid UI development

---

**Built with ❤️ and AI** - Demonstrating AI/automation skills through practical application
