# Job Autopilot - Redis Cache Manager
# Handles caching for jobs, HR contacts, and ATS analysis

import redis
import json
from datetime import timedelta
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from modules.logger_config import app_logger

load_dotenv()

class CacheManager:
    """Redis cache manager with automatic expiration"""
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        self.demo_mode = False
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=2  # Short timeout
            )
            # Test connection
            self.redis_client.ping()
            app_logger.info(f"Redis connected: {self.redis_host}:{self.redis_port}")
        except Exception as e:
            app_logger.warning(f"Redis connection failed (running in DEMO mode): {e}")
            self.redis_client = None
            self.demo_mode = True
    
    def _serialize(self, data: Any) -> str:
        """Serialize data to JSON string"""
        try:
            return json.dumps(data, default=str)
        except Exception as e:
            app_logger.error(f"Failed to serialize data: {e}")
            raise
    
    def _deserialize(self, data: str) -> Any:
        """Deserialize JSON string to Python object"""
        try:
            return json.loads(data)
        except Exception as e:
            app_logger.error(f"Failed to deserialize data: {e}")
            return None
    
    # ============================================================
    # Job Caching
    # ============================================================
    
    def cache_job(self, job_url: str, job_data: Dict, ttl_days: int = 7) -> bool:
        """
        Cache job data for 7 days
        
        Args:
            job_url: Unique job URL
            job_data: Job details dict
            ttl_days: Time to live in days
        
        Returns:
            bool: Success status
        """
        if self.demo_mode:
            return False
        
        try:
            key = f"job:{job_url}"
            self.redis_client.setex(
                key,
                timedelta(days=ttl_days),
                self._serialize(job_data)
            )
            app_logger.debug(f"Cached job: {job_url}")
            return True
        except Exception as e:
            app_logger.error(f"Failed to cache job {job_url}: {e}")
            return False
    
    def get_cached_job(self, job_url: str) -> Optional[Dict]:
        """
        Retrieve cached job data
        
        Args:
            job_url: Job URL
        
        Returns:
            dict or None: Job data if exists
        """
        if self.demo_mode:
            return None
        
        try:
            key = f"job:{job_url}"
            data = self.redis_client.get(key)
            if data:
                app_logger.debug(f"Cache hit: {job_url}")
                return self._deserialize(data)
            app_logger.debug(f"Cache miss: {job_url}")
            return None
        except Exception as e:
            app_logger.error(f"Failed to get cached job {job_url}: {e}")
            return None
    
    def cache_hr_contact(self, company_name: str, contact_data: Dict, ttl_days: int = 30) -> bool:
        """Cache HR contact for 30 days"""
        if self.demo_mode:
            return False
        try:
            key = f"hr:{company_name.lower().strip()}"
            self.redis_client.setex(key, timedelta(days=ttl_days), self._serialize(contact_data))
            app_logger.info(f"Cached HR contact for: {company_name}")
            return True
        except Exception as e:
            app_logger.error(f"Failed to cache HR contact for {company_name}: {e}")
            return False
    
    def get_cached_hr_contact(self, company_name: str) -> Optional[Dict]:
        """Retrieve cached HR contact"""
        if self.demo_mode:
            return None
        try:
            key = f"hr:{company_name.lower().strip()}"
            data = self.redis_client.get(key)
            if data:
                app_logger.info(f"Cache hit for HR: {company_name}")
                return self._deserialize(data)
            app_logger.debug(f"No cached HR for: {company_name}")
            return None
        except Exception as e:
            app_logger.error(f"Failed to get cached HR for {company_name}: {e}")
            return None
    
    def cache_ats_analysis(self, job_id: int, ats_data: Dict, ttl_days: int = 14) -> bool:
        """Cache ATS analysis for 14 days"""
        if self.demo_mode:
            return False
        try:
            key = f"ats_analysis:{job_id}"
            self.redis_client.setex(key, timedelta(days=ttl_days), self._serialize(ats_data))
            app_logger.debug(f"Cached ATS analysis for job {job_id}")
            return True
        except Exception as e:
            app_logger.error(f"Failed to cache ATS analysis for job {job_id}: {e}")
            return False
    
    def get_cached_ats_analysis(self, job_id: int) -> Optional[Dict]:
        """Retrieve cached ATS analysis"""
        if self.demo_mode:
            return None
        try:
            key = f"ats_analysis:{job_id}"
            data = self.redis_client.get(key)
            if data:
                app_logger.debug(f"Cache hit for ATS analysis: job {job_id}")
                return self._deserialize(data)
            return None
        except Exception as e:
            app_logger.error(f"Failed to get ATS analysis for job {job_id}: {e}")
            return None
    
    # ============================================================
    # Utility Functions
    # ============================================================
    
    def clear_cache(self, pattern: str = "*") -> int:
        """
        Clear cache by pattern
        
        Args:
            pattern: Redis key pattern (e.g., "job:*", "hr:*")
        
        Returns:
            int: Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                app_logger.info(f"Cleared {deleted} cache entries matching '{pattern}'")
                return deleted
            return 0
        except Exception as e:
            app_logger.error(f"Failed to clear cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            info = self.redis_client.info()
            stats = {
                "total_keys": self.redis_client.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_days": info.get("uptime_in_days", 0)
            }
            return stats
        except Exception as e:
            app_logger.error(f"Failed to get cache stats: {e}")
            return {}

# Global cache manager instance
cache_manager = CacheManager()

if __name__ == "__main__":
    # Test Redis connection
    stats = cache_manager.get_cache_stats()
    print(f"Redis stats: {stats}")
    app_logger.info("Redis cache manager initialized successfully!")
