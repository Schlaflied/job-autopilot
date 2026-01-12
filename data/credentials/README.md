# Gmail Credentials Placeholder

This directory stores Gmail API credentials and tokens.

## Files:
- `gmail_credentials.json` - OAuth 2.0 client credentials from Google Cloud Console
- `gmail_token.json` - Auto-generated after first OAuth login (DO NOT manually create)

## Setup Instructions:

### 1. Get Gmail API Credentials

1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Gmail API:
   - APIs & Services → Enable APIs and Services
   - Search "Gmail API" → Enable
4. Create OAuth credentials:
   - APIs & Services → Credentials
   - Create Credentials → OAuth 2.0 Client ID
   - Application type: **Desktop app**
   - Name: `Job Autopilot`
   - Click Create
5. Download JSON file
6. Rename to `gmail_credentials.json`
7. Place in this directory (`data/credentials/`)

### 2. First-time Authentication

When you first use Gmail features:
```python
from modules.gmail_service import gmail_service

# This will open browser for OAuth login
gmail_service.authenticate()
```

A browser window will open asking you to:
1. Select your Gmail account
2. Grant permissions to Job Autopilot
3. Allow access to:
   - Read emails (for reply detection)
   - Create drafts (for cold emails)

After successful login, `gmail_token.json` will be auto-created.

### 3. Security Notes

⚠️ **These files contain sensitive credentials!**
- Already added to `.gitignore` (won't be committed to Git)
- Keep them secure
- Never share publicly

### 4. Troubleshooting

**"File not found" error**:
- Make sure `gmail_credentials.json` is in this exact directory
- Check file name (no extra spaces, correct extension)

**"Invalid credentials" error**:
- Re-download from Google Cloud Console
- Make sure you enabled Gmail API

**OAuth consent screen error**:
- In Google Cloud Console:
  - OAuth consent screen → Add test users
  - Add your Gmail address as test user

---

**This is a placeholder file. The actual credentials will be placed here by you.**
