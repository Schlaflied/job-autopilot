# API Connection Test Script
# Tests all configured APIs and displays connection status

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from modules.logger_config import app_logger

load_dotenv()

print("=" * 70)
print("Job Autopilot - API Connection Test")
print("=" * 70)

# Test results
results = {}

# ============================================
# 1. Test OpenAI API
# ============================================
print("\n1️⃣  Testing OpenAI API...")
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        results["OpenAI"] = "❌ Not configured (OPENAI_API_KEY missing)"
    else:
        client = OpenAI(api_key=api_key)
        # Simple test: list models
        response = client.models.list()
        results["OpenAI"] = f"✅ Connected (API key: {api_key[:10]}...)"
        print(f"   ✅ OpenAI API working!")
except Exception as e:
    results["OpenAI"] = f"❌ Error: {str(e)[:50]}"
    print(f"   ❌ OpenAI Error: {e}")

# ============================================
# 2. Test Apify API
# ============================================
print("\n2️⃣  Testing Apify API...")
try:
    from apify_client import ApifyClient
    api_token = os.getenv("APIFY_API_TOKEN")
    
    if not api_token:
        results["Apify"] = "❌ Not configured (APIFY_API_TOKEN missing)"
    else:
        client = ApifyClient(api_token)
        # Test: get user info
        user = client.user().get()
        results["Apify"] = f"✅ Connected (User: {user.get('username', 'N/A')})"
        print(f"   ✅ Apify API working! User: {user.get('username')}")
except Exception as e:
    results["Apify"] = f"❌ Error: {str(e)[:50]}"
    print(f"   ❌ Apify Error: {e}")

# ============================================
# 3. Test Gmail API
# ============================================
print("\n3️⃣  Testing Gmail API...")
try:
    from modules.gmail_service import gmail_service
    
    token_path = gmail_service.token_path
    if not os.path.exists(token_path):
        results["Gmail"] = "❌ Not authenticated (run OAuth flow first)"
    else:
        # Try to get user email
        email = gmail_service.get_user_email()
        if email:
            results["Gmail"] = f"✅ Connected ({email})"
            print(f"   ✅ Gmail API working! Email: {email}")
        else:
            results["Gmail"] = "⚠️ Token exists but authentication failed"
except Exception as e:
    results["Gmail"] = f"❌ Error: {str(e)[:50]}"
    print(f"   ❌ Gmail Error: {e}")

# ============================================
# 4. Test Neon PostgreSQL Database
# ============================================
print("\n4️⃣  Testing Neon PostgreSQL...")
try:
    from modules.database import engine, DEMO_MODE, DATABASE_URL
    from sqlalchemy import text
    
    if DEMO_MODE:
        results["Database"] = "⚠️ DEMO mode (SQLite in-memory)"
    else:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            db_name = DATABASE_URL.split('/')[-1].split('?')[0]
            results["Database"] = f"✅ Connected (Database: {db_name})"
            print(f"   ✅ Neon PostgreSQL working! Database: {db_name}")
except Exception as e:
    results["Database"] = f"❌ Error: {str(e)[:50]}"
    print(f"   ❌ Database Error: {e}")

# ============================================
# 5. Test Redis Cache
# ============================================
print("\n5️⃣  Testing Redis Cache...")
try:
    import redis
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    
    if not os.getenv("REDIS_HOST"):
        results["Redis"] = "⚠️ Not configured (optional)"
    else:
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            socket_connect_timeout=2
        )
        r.ping()
        results["Redis"] = f"✅ Connected ({redis_host}:{redis_port})"
        print(f"   ✅ Redis working! Host: {redis_host}:{redis_port}")
except Exception as e:
    results["Redis"] = f"⚠️ Not available (optional): {str(e)[:30]}"
    print(f"   ⚠️ Redis not available: {e}")

# ============================================
# Summary
# ============================================
print("\n" + "=" * 70)
print("API Connection Summary")
print("=" * 70)

for api, status in results.items():
    print(f"{api:15} : {status}")

print("\n" + "=" * 70)

# Count successes
success_count = sum(1 for status in results.values() if "✅" in status)
total_required = 4  # OpenAI, Apify, Gmail, Database (Redis is optional)

print(f"\n✅ {success_count}/5 APIs connected successfully")

if success_count >= total_required:
    print("🚀 System ready for Job Autopilot!")
else:
    print("⚠️  Some APIs need configuration. Check the errors above.")
    print("\nConfiguration guide:")
    print("   1. Copy .env.example to .env")
    print("   2. Fill in your API keys")
    print("   3. Run: python scripts/test_apis.py")

print("=" * 70)
