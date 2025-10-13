"""
API Summary Endpoint - Complete API Documentation
Hiển thị tổng hợp tất cả APIs có sẵn trong hệ thống
"""

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Request
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["api-summary"])


@router.get("/apis", summary="📚 Danh Sách Tất Cả APIs")
async def get_all_apis(request: Request):
    """
    **Lấy danh sách tất cả APIs có sẵn trong hệ thống**
    
    Trả về tổng hợp đầy đủ tất cả endpoints được implement,
    phân loại theo nhóm chức năng.
    
    **Returns:**
    - Danh sách đầy đủ tất cả APIs
    - Số lượng endpoints theo nhóm
    - Tổng số APIs trong hệ thống
    """
    
    # Get all routes from FastAPI app
    app = request.app
    routes = []
    
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            # Skip internal routes
            if route.path.startswith("/openapi") or route.path.startswith("/docs") or route.path.startswith("/redoc"):
                continue
                
            for method in route.methods:
                if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    routes.append({
                        "method": method,
                        "path": route.path,
                        "name": route.name,
                        "tags": list(route.tags) if hasattr(route, 'tags') else []
                    })
    
    # Group routes by tags
    grouped_apis = {}
    for route in routes:
        tags = route.get("tags", ["uncategorized"])
        tag = tags[0] if tags else "uncategorized"
        
        if tag not in grouped_apis:
            grouped_apis[tag] = []
        
        grouped_apis[tag].append({
            "method": route["method"],
            "path": route["path"],
            "name": route["name"]
        })
    
    # Count endpoints by group
    endpoint_counts = {tag: len(apis) for tag, apis in grouped_apis.items()}
    total_endpoints = sum(endpoint_counts.values())
    
    return {
        "success": True,
        "summary": {
            "total_endpoints": total_endpoints,
            "endpoint_counts_by_group": endpoint_counts,
            "total_groups": len(grouped_apis)
        },
        "apis_by_group": grouped_apis,
        "timestamp": datetime.now().isoformat(),
        "message": f"Retrieved {total_endpoints} APIs across {len(grouped_apis)} groups"
    }


@router.get("/apis/summary", summary="📊 API Summary Statistics")
async def get_api_summary(request: Request):
    """
    **Thống kê tóm tắt về APIs**
    
    Trả về số liệu thống kê về số lượng APIs theo từng nhóm chức năng.
    
    **Returns:**
    - Tổng số endpoints
    - Số lượng endpoints theo nhóm
    - Phân loại theo HTTP methods
    """
    
    app = request.app
    
    # Count by method
    method_counts = {}
    tag_counts = {}
    
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            # Skip internal routes
            if route.path.startswith("/openapi") or route.path.startswith("/docs") or route.path.startswith("/redoc"):
                continue
            
            # Count by method
            for method in route.methods:
                if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    method_counts[method] = method_counts.get(method, 0) + 1
            
            # Count by tag
            if hasattr(route, 'tags'):
                for tag in route.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    total_endpoints = sum(method_counts.values())
    
    # Predefined groups from documentation
    documented_groups = {
        "health": "Health & System APIs",
        "authentication": "Authentication APIs",
        "robot": "Robot Control APIs",
        "telemetry": "Telemetry APIs",
        "safety": "Safety APIs",
        "monitoring": "Monitoring APIs",
        "network": "Network APIs",
        "wifi": "WiFi APIs",
        "wifi-ap": "WiFi AP APIs",
        "rs485": "RS485 Module Management APIs",
        "websocket": "WebSocket Endpoints",
        "speed-control": "Speed Control APIs",
        "localization": "Localization APIs",
        "map": "Map Management APIs",
        "configuration": "Configuration APIs",
        "dashboard": "Dashboard APIs",
        "communication": "Communication APIs",
        "module-telemetry": "Module Telemetry APIs",
        "firmware-health": "Firmware Health APIs"
    }
    
    return {
        "success": True,
        "statistics": {
            "total_endpoints": total_endpoints,
            "http_methods": method_counts,
            "groups": tag_counts,
            "documented_groups": len(documented_groups),
            "implemented_groups": len(tag_counts)
        },
        "group_descriptions": documented_groups,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/apis/health", summary="🏥 API Health Check")
async def api_health_check():
    """
    **Kiểm tra sức khỏe của API system**
    
    Endpoint đơn giản để verify API đang hoạt động.
    
    **Returns:**
    - Status: healthy/unhealthy
    - Timestamp
    - Version info
    """
    
    return {
        "success": True,
        "status": "healthy",
        "api_version": "v1",
        "backend_version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "message": "API system is operational"
    }

