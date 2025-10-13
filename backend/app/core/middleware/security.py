"""
Security Middleware - OHT-50 Backend
Handles security headers and CORS configuration
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import Settings

def add_cors_middleware(app, settings: Settings):
    """Add CORS middleware to FastAPI app"""
    _origins = settings.cors_origins
    if settings.environment.lower() == "production":
        # In production, disallow localhost defaults unless explicitly configured
        _origins = [o for o in _origins if "localhost" not in o and "127.0.0.1" not in o]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

def validate_production_secrets(settings: Settings):
    """Validate secrets are not using default values in production"""
    if settings.environment.lower() == "production":
        if settings.jwt_secret in ("your-secret-key-here", "test-secret-key"):
            raise RuntimeError("Invalid JWT secret in production")
