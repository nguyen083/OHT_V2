"""
Rate Limiting Middleware - OHT-50 Backend
Simple per-IP rate limiting implementation
"""

import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from app.config import Settings

# Global rate limiting storage (per-process, per-IP)
_rate_buckets = defaultdict(list)

def create_rate_limit_middleware(settings: Settings):
    """Create rate limiting middleware with configuration"""
    
    rate_limit_requests = settings.rate_limit_requests
    rate_limit_window = settings.rate_limit_window
    
    async def rate_limit_middleware(request: Request, call_next):
        """Rate limiting middleware implementation"""
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - rate_limit_window
        bucket = _rate_buckets[client_ip]
        
        # Prune old entries
        while bucket and bucket[0] < window_start:
            bucket.pop(0)
        
        # Check rate limit
        if len(bucket) >= rate_limit_requests:
            return JSONResponse(
                status_code=429, 
                content={"detail": "Rate limit exceeded"}
            )
        
        bucket.append(now)
        return await call_next(request)
    
    return rate_limit_middleware
