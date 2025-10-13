# 🛡️ ADVANCED SECURITY MIDDLEWARE - Phase 4 Implementation
"""
Enterprise-grade security middleware for FastAPI
Comprehensive security enforcement for EXCELLENT compliance level

Phase 4: Advanced security middleware với rate limiting, audit logging, and compliance
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.infrastructure.security.advanced_auth_service import AdvancedAuthService, SecurityLevel
from app.infrastructure.monitoring.performance_monitoring_service import get_performance_monitoring_service
from app.presentation.schemas.api_responses import ResponseBuilder, ApiError, ErrorSeverity

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Advanced security middleware với comprehensive protection
    Phase 4: Enterprise-grade security enforcement
    """
    
    def __init__(
        self,
        app,
        auth_service: AdvancedAuthService,
        excluded_paths: Optional[List[str]] = None,
        rate_limit_config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(app)
        self.auth_service = auth_service
        self.excluded_paths = excluded_paths or [
            "/docs", "/redoc", "/openapi.json", "/favicon.ico",
            "/api/v1/health", "/api/v1/auth/login"
        ]
        
        # Rate limiting configuration
        self.rate_limit_config = rate_limit_config or {
            "global_limit": 1000,  # requests per minute
            "per_ip_limit": 100,   # requests per minute per IP
            "auth_limit": 10,      # auth requests per minute per IP
            "burst_limit": 20,     # burst allowance
        }
        
        # Security headers configuration
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()"
        }
        
        # Request tracking
        self.request_counts: Dict[str, Dict[str, Any]] = {}
        self.suspicious_ips: Dict[str, float] = {}
        
        logger.info("✅ Advanced Security Middleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main security middleware dispatch"""
        start_time = time.time()
        
        try:
            # Extract request information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            request_path = request.url.path
            method = request.method
            
            # Security checks
            security_result = await self._perform_security_checks(
                request, client_ip, user_agent, request_path, method
            )
            
            if not security_result["allowed"]:
                return await self._create_security_response(
                    security_result["status_code"],
                    security_result["message"],
                    security_result.get("details", {})
                )
            
            # Add security context to request state
            request.state.security_context = security_result.get("security_context")
            request.state.client_ip = client_ip
            request.state.start_time = start_time
            
            # Process request
            response = await call_next(request)
            
            # Post-process response
            response = await self._post_process_response(request, response, start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            
            # Log security incident
            await self._log_security_incident(
                ip_address=self._get_client_ip(request),
                request_path=request.url.path,
                error=str(e),
                severity="high"
            )
            
            return await self._create_security_response(
                500,
                "Security system error",
                {"error": "Internal security error"}
            )
    
    async def _perform_security_checks(
        self,
        request: Request,
        client_ip: str,
        user_agent: str,
        request_path: str,
        method: str
    ) -> Dict[str, Any]:
        """Comprehensive security checks"""
        
        # 1. Path-based checks
        if request_path in self.excluded_paths:
            return {"allowed": True, "reason": "excluded_path"}
        
        # 2. Rate limiting checks
        rate_limit_result = await self._check_rate_limits(client_ip, request_path, method)
        if not rate_limit_result["allowed"]:
            return {
                "allowed": False,
                "status_code": HTTP_429_TOO_MANY_REQUESTS,
                "message": "Rate limit exceeded",
                "details": rate_limit_result
            }
        
        # 3. Suspicious activity detection
        if await self._is_suspicious_activity(client_ip, user_agent, request_path):
            await self._log_security_incident(
                ip_address=client_ip,
                request_path=request_path,
                user_agent=user_agent,
                severity="medium",
                details={"reason": "suspicious_activity_detected"}
            )
            
            # For now, log but allow (could be enhanced to block)
            logger.warning(f"Suspicious activity detected from {client_ip}: {request_path}")
        
        # 4. Authentication checks
        auth_result = await self._check_authentication(request)
        if not auth_result["allowed"]:
            return {
                "allowed": False,
                "status_code": auth_result["status_code"],
                "message": auth_result["message"],
                "details": auth_result.get("details", {})
            }
        
        return {
            "allowed": True,
            "security_context": auth_result.get("security_context"),
            "rate_limit_info": rate_limit_result
        }
    
    async def _check_rate_limits(
        self,
        client_ip: str,
        request_path: str,
        method: str
    ) -> Dict[str, Any]:
        """Advanced rate limiting checks"""
        current_time = time.time()
        window_start = int(current_time / 60) * 60  # 1-minute windows
        
        # Initialize tracking for this IP if needed
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {
                "window_start": window_start,
                "total_requests": 0,
                "auth_requests": 0,
                "burst_tokens": self.rate_limit_config["burst_limit"]
            }
        
        ip_data = self.request_counts[client_ip]
        
        # Reset window if needed
        if window_start > ip_data["window_start"]:
            ip_data["window_start"] = window_start
            ip_data["total_requests"] = 0
            ip_data["auth_requests"] = 0
            # Replenish burst tokens
            ip_data["burst_tokens"] = min(
                ip_data["burst_tokens"] + 5,  # Add 5 tokens per minute
                self.rate_limit_config["burst_limit"]
            )
        
        # Check global rate limit per IP
        if ip_data["total_requests"] >= self.rate_limit_config["per_ip_limit"]:
            # Check burst allowance
            if ip_data["burst_tokens"] > 0:
                ip_data["burst_tokens"] -= 1
                logger.info(f"Burst token used for {client_ip}, remaining: {ip_data['burst_tokens']}")
            else:
                return {
                    "allowed": False,
                    "reason": "per_ip_limit_exceeded",
                    "limit": self.rate_limit_config["per_ip_limit"],
                    "current": ip_data["total_requests"]
                }
        
        # Check auth-specific rate limit
        if request_path.startswith("/api/v1/auth"):
            if ip_data["auth_requests"] >= self.rate_limit_config["auth_limit"]:
                return {
                    "allowed": False,
                    "reason": "auth_limit_exceeded",
                    "limit": self.rate_limit_config["auth_limit"],
                    "current": ip_data["auth_requests"]
                }
            ip_data["auth_requests"] += 1
        
        # Increment counters
        ip_data["total_requests"] += 1
        
        return {
            "allowed": True,
            "remaining": self.rate_limit_config["per_ip_limit"] - ip_data["total_requests"],
            "reset_time": window_start + 60
        }
    
    async def _is_suspicious_activity(
        self,
        client_ip: str,
        user_agent: str,
        request_path: str
    ) -> bool:
        """Detect suspicious activity patterns"""
        
        # Check for suspicious IP patterns
        if client_ip in self.suspicious_ips:
            last_suspicious = self.suspicious_ips[client_ip]
            if time.time() - last_suspicious < 3600:  # Still suspicious within 1 hour
                return True
        
        # Suspicious user agent patterns
        suspicious_ua_patterns = [
            "bot", "crawler", "spider", "scraper",
            "curl", "wget", "python-requests"
        ]
        
        if any(pattern in user_agent.lower() for pattern in suspicious_ua_patterns):
            # Not necessarily blocked, but flagged
            self.suspicious_ips[client_ip] = time.time()
            return True
        
        # Suspicious path patterns
        suspicious_paths = [
            "/admin", "/.env", "/wp-admin", "/phpmyadmin",
            "/.git", "/config", "/backup"
        ]
        
        if any(sus_path in request_path.lower() for sus_path in suspicious_paths):
            self.suspicious_ips[client_ip] = time.time()
            return True
        
        return False
    
    async def _check_authentication(self, request: Request) -> Dict[str, Any]:
        """Advanced authentication checks"""
        request_path = request.url.path
        
        # Public endpoints that don't require authentication
        public_endpoints = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/docs", "/redoc", "/openapi.json"
        ]
        
        if any(request_path.startswith(endpoint) for endpoint in public_endpoints):
            return {"allowed": True, "reason": "public_endpoint"}
        
        # Extract authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {
                "allowed": False,
                "status_code": HTTP_401_UNAUTHORIZED,
                "message": "Missing or invalid authorization header"
            }
        
        # Extract token
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate token
        is_valid, security_context, error_message = await self.auth_service.validate_token(token)
        
        if not is_valid:
            return {
                "allowed": False,
                "status_code": HTTP_401_UNAUTHORIZED,
                "message": error_message or "Invalid token",
                "details": {"token_error": error_message}
            }
        
        # Check endpoint-specific permissions
        required_permissions = self._get_required_permissions(request_path, request.method)
        if required_permissions:
            if not all(perm in security_context.permissions for perm in required_permissions):
                return {
                    "allowed": False,
                    "status_code": HTTP_403_FORBIDDEN,
                    "message": "Insufficient permissions",
                    "details": {
                        "required_permissions": required_permissions,
                        "user_permissions": security_context.permissions
                    }
                }
        
        return {
            "allowed": True,
            "security_context": security_context
        }
    
    def _get_required_permissions(self, path: str, method: str) -> List[str]:
        """Get required permissions for specific endpoints"""
        
        # Permission mapping for different endpoints
        permission_map = {
            # Robot control endpoints
            "/api/v1/robot/control": ["write", "robot_control"],
            "/api/v1/robot/emergency": ["write", "emergency_control"],
            
            # Configuration endpoints
            "/api/v1/config": {
                "GET": ["read"],
                "POST": ["write", "config_write"],
                "PUT": ["write", "config_write"],
                "DELETE": ["admin"]
            },
            
            # User management endpoints
            "/api/v1/users": {
                "GET": ["read", "user_read"],
                "POST": ["admin"],
                "PUT": ["admin"],
                "DELETE": ["admin"]
            },
            
            # System endpoints
            "/api/v1/system": ["admin"],
            "/api/v1/logs": ["read", "system_logs"],
        }
        
        # Check exact path match first
        if path in permission_map:
            perm_config = permission_map[path]
            if isinstance(perm_config, dict):
                return perm_config.get(method, [])
            else:
                return perm_config
        
        # Check prefix matches
        for endpoint_pattern, perms in permission_map.items():
            if path.startswith(endpoint_pattern):
                if isinstance(perms, dict):
                    return perms.get(method, [])
                else:
                    return perms
        
        # Default: require authentication but no specific permissions
        return []
    
    async def _post_process_response(
        self,
        request: Request,
        response: Response,
        start_time: float
    ) -> Response:
        """Post-process response với security headers and logging"""
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add rate limiting headers
        client_ip = self._get_client_ip(request)
        if client_ip in self.request_counts:
            ip_data = self.request_counts[client_ip]
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit_config["per_ip_limit"])
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, self.rate_limit_config["per_ip_limit"] - ip_data["total_requests"])
            )
            response.headers["X-RateLimit-Reset"] = str(ip_data["window_start"] + 60)
        
        # Log request for monitoring
        processing_time = (time.time() - start_time) * 1000
        
        try:
            monitoring_service = await get_performance_monitoring_service()
            await monitoring_service.record_api_request(
                endpoint=request.url.path,
                method=request.method,
                response_time_ms=processing_time,
                status_code=response.status_code
            )
        except Exception as e:
            logger.warning(f"Failed to record API metrics: {e}")
        
        return response
    
    async def _create_security_response(
        self,
        status_code: int,
        message: str,
        details: Dict[str, Any]
    ) -> JSONResponse:
        """Create standardized security response"""
        
        # Determine error severity
        if status_code >= 500:
            severity = ErrorSeverity.CRITICAL
        elif status_code == 429:
            severity = ErrorSeverity.MEDIUM
        elif status_code in [401, 403]:
            severity = ErrorSeverity.HIGH
        else:
            severity = ErrorSeverity.LOW
        
        # Create error response
        error_response = ResponseBuilder.error(
            message=message,
            errors=[ApiError(
                code=f"SECURITY_ERROR_{status_code}",
                message=message,
                severity=severity,
                details=details
            )]
        )
        
        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
        )
    
    async def _log_security_incident(
        self,
        ip_address: str,
        request_path: str,
        severity: str = "medium",
        user_agent: Optional[str] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security incident for analysis"""
        
        incident = {
            "timestamp": time.time(),
            "ip_address": ip_address,
            "request_path": request_path,
            "severity": severity,
            "user_agent": user_agent,
            "error": error,
            "details": details or {}
        }
        
        # Log to system logger
        log_message = f"Security Incident [{severity.upper()}]: {ip_address} -> {request_path}"
        if error:
            log_message += f" - {error}"
        
        if severity == "high":
            logger.error(log_message)
        elif severity == "medium":
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # TODO: In production, could send to SIEM or security monitoring system
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address với proxy support"""
        
        # Check for forwarded headers (common in production with load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        current_time = time.time()
        
        # Calculate statistics
        total_ips = len(self.request_counts)
        total_requests = sum(data["total_requests"] for data in self.request_counts.values())
        suspicious_ips_count = len([
            ip for ip, last_time in self.suspicious_ips.items()
            if current_time - last_time < 3600
        ])
        
        # Rate limiting stats
        rate_limited_ips = len([
            data for data in self.request_counts.values()
            if data["total_requests"] >= self.rate_limit_config["per_ip_limit"]
        ])
        
        return {
            "total_unique_ips": total_ips,
            "total_requests_current_window": total_requests,
            "suspicious_ips": suspicious_ips_count,
            "rate_limited_ips": rate_limited_ips,
            "rate_limit_config": self.rate_limit_config,
            "security_headers_count": len(self.security_headers),
            "excluded_paths": self.excluded_paths
        }
