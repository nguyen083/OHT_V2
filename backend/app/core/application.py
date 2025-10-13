"""
FastAPI Application Factory - OHT-50 Backend
Clean architecture application creation and configuration
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime

from app.config import Settings
from app.core.startup.lifespan import lifespan
from app.core.middleware.security import (
    add_cors_middleware, 
    add_security_headers, 
    validate_production_secrets
)
from app.core.middleware.rate_limit import create_rate_limit_middleware
from app.core.middleware.monitoring import (
    setup_monitoring_middleware, 
    add_exception_handlers
)
from app.core.container import get_service_container

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        FastAPI: Configured application instance
    """
    # Load settings
    settings = Settings()
    
    # Validate production configuration
    validate_production_secrets(settings)
    
    # Initialize DI Container
    container = get_service_container()
    logger.info("✅ Dependency Injection Container initialized")
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="OHT-50 Backend API",
        description="""
        # 🚀 OHT-50 Backend API v2.0 - Production Ready
        
        ## 📋 **API Overview**
        **100+ Endpoints** across 15+ main categories providing comprehensive robot control and monitoring
        
        ### 🔐 **Authentication API** (5 endpoints)
        - User login/logout, JWT token management, user profile, RBAC
        
        ### 🤖 **Robot Control API** (10 endpoints)  
        - Robot status, movement control (forward/backward/stop), position tracking, speed control, emergency stop
        
        ### 📊 **Telemetry API** (4 endpoints)
        - Current telemetry, historical data, LiDAR scan, summary statistics
        
        ### 🚨 **Safety API** (3 endpoints)
        - Safety status, emergency stop, alert management
        
        ### ⚡ **Speed Control API** (6+ endpoints)
        - Speed management, acceleration/deceleration limits, performance monitoring, safety integration
        
        ### ⚙️ **Configuration API** (4+ endpoints)
        - System settings, robot parameters, configuration management, real-time updates
        
        ### 📈 **Monitoring API** (3+ endpoints)
        - System health, performance metrics, logs, alerts, real-time monitoring
        
        ### 🗺️ **Map Management API** (6+ endpoints)
        - Map upload, retrieval, metadata, waypoint management
        
        ### 🎯 **Localization API** (8+ endpoints)
        - Position tracking, sensor fusion (RFID/NFC, Accelerometer, Proximity), configuration, statistics
        
        ### 🔌 **RS485 Module Management** (13+ endpoints)
        - Module discovery, telemetry, health check, register read/write, ping, reset, scan control
        
        ### 📶 **WiFi APIs** (5 endpoints)
        - WiFi scan, connect, disconnect, status, IP configuration
        
        ### 📡 **WiFi AP APIs** (6 endpoints)
        - Access Point start/stop, status, client management, configuration
        
        ### 🌐 **Network APIs** (2+ endpoints)
        - Network status, system info, interface management
        
        ### 🏥 **Health Check API** (3 endpoints)
        - Fast health check, detailed health, system info
        
        ### 📊 **Dashboard API** (4+ endpoints)
        - Real-time dashboard data, statistics, system overview
        
        ### 💬 **Communication API** (3+ endpoints)
        - Inter-module communication, message queue, event broadcasting
        
        ### 🔌 **WebSocket API** (4 endpoints - Real-time)
        - Live telemetry updates (`/ws/telemetry`)
        - Real-time status (`/ws/status`)
        - RS485 module updates (`/ws/rs485`)
        - Logging stream (`/ws/logs`)
        
        ### 📚 **API Summary** (3 endpoints - NEW!)
        - Complete API listing (`/api/v1/apis`)
        - API statistics (`/api/v1/apis/summary`)
        - API health check (`/api/v1/apis/health`)
        
        ## 🎯 **Performance Targets**
        - **API Response**: < 50ms (95th percentile)
        - **Emergency Stop**: < 10ms (critical path)
        - **WebSocket Latency**: < 20ms
        - **Database Queries**: < 10ms
        - **System Uptime**: > 99.9%
        
        ## 🔒 **Security Features**
        - JWT Authentication with RBAC (Role-Based Access Control)
        - Rate Limiting (configurable per endpoint group)
        - Input Validation with Pydantic
        - Security Headers (CSP, HSTS, X-Frame-Options)
        - Comprehensive Audit Logging
        - CORS Protection
        
        ## 🔧 **Authentication**
        Most endpoints require JWT token in header:
        ```
        Authorization: Bearer <your_jwt_token>
        ```
        
        ## 📖 **Quick Start**
        1. Check health: `GET /health`
        2. Login: `POST /api/v1/auth/login`
        3. Get all APIs: `GET /api/v1/apis`
        4. Explore: Use Swagger UI at `/docs`
        """,
        version="2.0.0",
        contact={
            "name": "OHT-50 Development Team",
            "email": "dev@oht50.com",
            "url": "https://github.com/oht50/backend"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.oht50.com", 
                "description": "Production server"
            }
        ],
        lifespan=lifespan
    )
    
    # Attach DI Container to app
    app.container = container
    
    # Configure middleware
    _configure_middleware(app, settings)
    
    # Configure API routes
    _configure_routes(app, settings)
    
    # Configure exception handlers
    add_exception_handlers(app)
    
    # Setup monitoring
    setup_monitoring_middleware(app)
    
    # Add health endpoints
    _add_health_endpoints(app)
    
    logger.info("✅ FastAPI application created and configured with DI Container")
    return app

def _configure_middleware(app: FastAPI, settings: Settings):
    """Configure all middleware"""
    
    # Rate limiting middleware
    rate_limiter = create_rate_limit_middleware(settings)
    app.middleware("http")(rate_limiter)
    
    # CORS middleware  
    add_cors_middleware(app, settings)
    
    # Security headers middleware
    app.middleware("http")(add_security_headers)

def _configure_routes(app: FastAPI, settings: Settings):
    """Configure API routes with optional reduction"""
    
    # Import core API routers
    from app.api.v1 import (
        auth, robot, telemetry, safety, monitoring, 
        registers, health, fw_integration
    )
    from app.api.v1 import deprecated as deprecated_api
    from app.api import websocket
    
    # Include core routers
    app.include_router(auth.router)
    app.include_router(robot.router)
    app.include_router(telemetry.router)
    app.include_router(safety.router)
    app.include_router(monitoring.router)
    
    # Include Network API router  
    from app.api.v1 import network
    app.include_router(network.router)
    
    # Include RS485 API router
    from app.api.v1 import rs485
    app.include_router(rs485.router)
    
    # Include Registers CRUD API router
    app.include_router(registers.router)
    
    # Include Firmware Integration router (Issue #176)
    app.include_router(fw_integration.router)
    
    # Include Admin Registers API router
    from app.api.v1 import admin_registers
    app.include_router(admin_registers.router)
    
    # Include Health API router (v1)
    app.include_router(health.router)
    
    # Include Network/WiFi API router
    try:
        from app.api.v1 import network_wifi
        app.include_router(network_wifi.router)
    except Exception as e:
        logger.warning(f"⚠️ WiFi router not loaded: {e}")
    
    # Include WiFi AP API router
    try:
        from app.api.v1 import network_ap
        app.include_router(network_ap.router)
    except Exception as e:
        logger.warning(f"⚠️ WiFi AP router not loaded: {e}")
    
    # Include Speed Control API router
    try:
        from app.api.v1 import speed_control
        app.include_router(speed_control.router)
        logger.info("✅ Speed Control router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Speed Control router not loaded: {e}")
    
    # Include Localization API router
    try:
        from app.api.v1 import localization
        app.include_router(localization.router)
        logger.info("✅ Localization router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Localization router not loaded: {e}")
    
    # Include Map API router
    try:
        from app.api.v1 import map as map_router
        app.include_router(map_router.router)
        logger.info("✅ Map router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Map router not loaded: {e}")
    
    # Include Configuration API router
    try:
        from app.api.v1 import config
        app.include_router(config.router)
        logger.info("✅ Config router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Config router not loaded: {e}")
    
    # Include Dashboard API router
    try:
        from app.api.v1 import dashboard
        app.include_router(dashboard.router)
        logger.info("✅ Dashboard router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Dashboard router not loaded: {e}")
    
    # Include Communication API router
    try:
        from app.api.v1 import communication
        app.include_router(communication.router)
        logger.info("✅ Communication router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Communication router not loaded: {e}")
    
    # Include Module Telemetry API router
    try:
        from app.api.v1 import module_telemetry
        app.include_router(module_telemetry.router)
        logger.info("✅ Module Telemetry router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Module Telemetry router not loaded: {e}")
    
    # Include Firmware Health API router
    try:
        from app.api.v1 import firmware_health
        app.include_router(firmware_health.router)
        logger.info("✅ Firmware Health router loaded")
    except Exception as e:
        logger.warning(f"⚠️ Firmware Health router not loaded: {e}")
    
    # Include API Summary router (Complete API listing)
    try:
        from app.api.v1 import api_summary
        app.include_router(api_summary.router)
        logger.info("✅ API Summary router loaded")
    except Exception as e:
        logger.warning(f"⚠️ API Summary router not loaded: {e}")
    
    # Include Deprecated API router (410 Gone with hints)
    app.include_router(deprecated_api.router)
    
    # Include WebSocket router
    try:
        app.include_router(websocket.router)
    except AttributeError:
        # WebSocket router not available, skip
        pass
    
    # Configure API reduction if enabled
    _configure_api_reduction(app, settings)

def _configure_api_reduction(app: FastAPI, settings: Settings):
    """Configure API reduction for production"""
    api_reduced = os.getenv("API_REDUCED", "true").lower() == "true"
    api_reduced_strict = os.getenv("API_REDUCED_STRICT", "true").lower() == "true"
    
    if not api_reduced:
        return
        
    # Whitelisted endpoints for reduced mode
    allowed_paths = {
        "/health", "/health/fast", "/api/v1/health/detailed", "/system/info",
        "/api/v1/auth/login", "/api/v1/auth/me", "/api/v1/auth/logout",
        "/api/v1/robot/status", "/api/v1/robot/control", "/api/v1/robot/emergency-stop",
        "/api/v1/telemetry/current", "/api/v1/safety/status", "/api/v1/monitoring/health",
        "/api/v1/network/status", "/api/v1/network/wifi/scan"
    }
    
    # Filter OpenAPI schema
    from fastapi.openapi.utils import get_openapi
    
    def custom_openapi():
        if app.openapi_schema:
            schema = app.openapi_schema
        else:
            schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
        # Filter paths not in whitelist
        paths = schema.get("paths", {})
        filtered = {path: methods for path, methods in paths.items() if path in allowed_paths}
        schema["paths"] = filtered
        app.openapi_schema = schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Add strict mode middleware if enabled
    if api_reduced_strict:
        import re
        
        @app.middleware("http")
        async def deprecate_hidden_endpoints(request: Request, call_next):
            req_path = request.url.path
            
            # Allow non-API paths and whitelisted API paths
            if not req_path.startswith("/api/"):
                return await call_next(request)
            
            if req_path in allowed_paths:
                return await call_next(request)
            
            # Allow new Issue #176 endpoints
            if re.match(r'^/api/v1/(fw/)?modules/\d+/registers(/.*)?$', req_path):
                return await call_next(request)
            
            return JSONResponse(
                status_code=410,
                content={
                    "detail": "Endpoint deprecated and removed in reduced API mode",
                    "path": req_path,
                    "hint": "Please use the documented core APIs in /docs",
                },
            )

def _add_health_endpoints(app: FastAPI):
    """Add health check endpoints"""
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint - OPTIMIZED for performance"""
        try:
            from app.core.monitoring_service import monitoring_service
            health_data = await monitoring_service.get_system_health()
            
            return {
                "success": True,
                "status": "healthy",
                "timestamp": health_data.get("last_updated", "unknown"),
                "system_health": health_data.get("status", "unknown"),
                "overall_health_score": health_data.get("overall_health_score", 0),
                "performance": "optimized"
            }
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "unknown"
            }

    @app.get("/health/fast")
    async def fast_health_check():
        """Fast health check endpoint - minimal checks"""
        return {
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "performance": "ultra_fast",
            "checks": "minimal"
        }

    @app.get("/test-auth")
    async def test_auth():
        """Test endpoint without authentication (disabled in production)"""
        env = os.getenv("ENVIRONMENT", "development").lower()
        testing = os.getenv("TESTING", "false").lower() == "true"
        if env == "production" and not testing:
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return {
            "success": True,
            "message": "Test endpoint working (non-production)",
            "timestamp": "2025-01-28T10:30:00Z"
        }

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "OHT-50 Backend API",
            "version": "2.0.0", 
            "status": "running",
            "docs": "/docs",
            "health": "/health"
        }
