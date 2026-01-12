# Redis Configuration Guide for Job Autopilot

## What is Redis?
Redis is an in-memory database used for caching. In Job Autopilot, it stores:
- Job data (7 days) - avoid duplicate Apify calls
- HR contact info (30 days)
- ATS analysis results (14 days)

**⚠️ Redis is OPTIONAL** - The system works without it, just slower and costs more API calls.

---

## Option 1: Skip Redis (Recommended for MVP)

**Pros**:
- ✅ Zero setup
- ✅ System still works perfectly
- ✅ Less complexity

**Cons**:
- ❌ Each job search calls Apify (costs API quota)
- ❌ No caching between sessions

**How to skip**:
Just leave Redis settings blank in `.env`:
```env
# REDIS_HOST=
# REDIS_PORT=
# REDIS_DB=
```

The system will automatically fall back to database-only caching.

---

## Option 2: Local Redis (For Development)

### Windows Installation

**A. Using Docker (Easiest)**

1. Install Docker Desktop:
   https://www.docker.com/products/docker-desktop/

2. Run Redis container:
   ```powershell
   docker run -d --name job-autopilot-redis -p 6379:6379 redis:alpine
   ```

3. Update `.env`:
   ```env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```

4. Test connection:
   ```powershell
   python scripts/test_apis.py
   ```

**B. Using Windows Subsystem for Linux (WSL2)**

1. Install WSL2:
   ```powershell
   wsl --install
   ```

2. In WSL terminal:
   ```bash
   sudo apt update
   sudo apt install redis-server
   sudo service redis-server start
   ```

3. Update `.env`:
   ```env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```

**C. Windows Native (Deprecated, use Docker instead)**

Redis doesn't officially support Windows. Use Docker or WSL2 instead.

---

## Option 3: Cloud Redis (For Production)

### A. Upstash Redis (FREE tier available)

**Pros**:
- ✅ Free tier: 10,000 commands/day
- ✅ No credit card required
- ✅ Serverless (auto-scales)
- ✅ Perfect for your use case

**Setup**:

1. Visit https://upstash.com/
2. Sign up (free)
3. Create Redis Database:
   - Name: `job-autopilot-cache`
   - Region: Choose closest to you (e.g., `us-east-1`)
   - Type: Regional (free tier)

4. Copy connection details:
   - Click your database
   - Go to "REST API" tab
   - Copy: Endpoint URL and Token

5. Update `.env`:
   ```env
   # For Upstash REST API (recommended)
   REDIS_HOST=your-redis-url.upstash.io
   REDIS_PORT=6379
   REDIS_PASSWORD=your_redis_password_here
   REDIS_DB=0
   ```

6. Test:
   ```powershell
   python scripts/test_apis.py
   ```

### B. Redis Labs (RedisCloud)

**Pros**:
- ✅ Free tier: 30MB storage
- ✅ Managed service
- ✅ Good for production

**Setup**:

1. Visit https://redis.com/try-free/
2. Sign up
3. Create database
4. Copy connection string
5. Update `.env` with host, port, password

### C. AWS ElastiCache (Paid)

Only needed if you deploy to AWS production. Skip for MVP.

---

## Recommendation for Your Project

**MVP Stage (Now)**: 
```
❌ Don't install Redis yet
```

**Reasons**:
1. System works fine without it
2. One less thing to worry about
3. Database caching is enough for testing
4. You can add Redis later in 5 minutes (Upstash)

**When to add Redis**:
- When you scrape 50+ jobs/day regularly
- When you notice slow repeated searches
- When deploying to production

---

## Current Caching Strategy (Without Redis)

Your system ALREADY caches jobs in Neon PostgreSQL:

```python
# When you search jobs:
1. Call Apify to scrape Indeed
2. Save jobs to Neon database
3. Next time: Click "Load Cached Jobs"
   → Loads from Neon (no Apify call)
   → Saves API quota!
```

**This is good enough for now!**

---

## If You Want to Add Redis Later

Just run:
```powershell
# Option 1: Docker (5 seconds)
docker run -d --name redis -p 6379:6379 redis:alpine

# Option 2: Upstash (2 minutes)
# 1. Sign up at upstash.com
# 2. Create database
# 3. Copy credentials to .env
```

Then restart Streamlit - Redis will auto-activate!

---

## Cost Comparison

| Option | Cost | Setup Time | Reliability |
|--------|------|------------|-------------|
| No Redis | $0 | 0 min | ✅ Good |
| Local Docker | $0 | 5 min | ⚠️ Dev only |
| Upstash Free | $0 | 2 min | ✅ Excellent |
| Redis Labs Free | $0 | 3 min | ✅ Good |
| AWS ElastiCache | ~$15/mo | 30 min | ✅ Production |

**For Job Autopilot MVP**: No Redis (save time, add later)

---

**Current Status**: Your system is ✅ READY without Redis!
