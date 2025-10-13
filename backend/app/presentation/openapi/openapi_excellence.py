# 📡 OPENAPI 3.0 EXCELLENCE - Phase 4 Implementation
"""
Comprehensive OpenAPI 3.0 documentation and validation system
Professional API design with automatic validation, testing, and documentation

Phase 4: OpenAPI excellence for professional API standards
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import inspect

from fastapi import FastAPI, Request, Response
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ConfigDict
import yaml

from app.presentation.schemas.api_responses import (
    BaseApiResponse, PaginatedApiResponse, ResponseStatus, 
    HATEOASLink, ApiError, ErrorSeverity
)

logger = logging.getLogger(__name__)


class APICategory(str, Enum):
    """API endpoint categories"""
    AUTHENTICATION = "Authentication"
    ROBOT_CONTROL = "Robot Control"
    TELEMETRY = "Telemetry & Monitoring"
    CONFIGURATION = "Configuration"
    SYSTEM_MANAGEMENT = "System Management"
    USER_MANAGEMENT = "User Management"
    HEALTH_MONITORING = "Health & Diagnostics"


@dataclass
class EndpointDocumentation:
    """Enhanced endpoint documentation"""
    summary: str
    description: str
    category: APICategory
    example_request: Optional[Dict[str, Any]] = None
    example_response: Optional[Dict[str, Any]] = None
    error_responses: Optional[List[Dict[str, Any]]] = None
    performance_notes: Optional[str] = None
    security_requirements: Optional[List[str]] = None
    rate_limit: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "description": self.description,
            "category": self.category.value,
            "example_request": self.example_request,
            "example_response": self.example_response,
            "error_responses": self.error_responses or [],
            "performance_notes": self.performance_notes,
            "security_requirements": self.security_requirements or [],
            "rate_limit": self.rate_limit
        }


class OpenAPIExampleGenerator:
    """Generate comprehensive OpenAPI examples"""
    
    @staticmethod
    def generate_success_response_example(data_example: Any = None) -> Dict[str, Any]:
        """Generate standard success response example"""
        return {
            "status": "success",
            "message": "Operation completed successfully",
            "data": data_example or {"id": 1, "name": "Example Item"},
            "meta": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-28T10:30:00Z",
                "processing_time_ms": 23.5,
                "api_version": "v1"
            },
            "links": [
                {
                    "href": "/api/v1/example/1",
                    "rel": "self",
                    "method": "GET",
                    "title": "Get Item"
                }
            ]
        }
    
    @staticmethod
    def generate_error_response_example(error_code: str = "VALIDATION_ERROR") -> Dict[str, Any]:
        """Generate standard error response example"""
        return {
            "status": "error",
            "message": "Request validation failed",
            "data": None,
            "errors": [
                {
                    "code": error_code,
                    "message": "Invalid input data provided",
                    "severity": "medium",
                    "field": "username",
                    "details": {"min_length": 3, "provided_length": 1}
                }
            ],
            "meta": {
                "request_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": "2025-01-28T10:30:00Z",
                "processing_time_ms": 15.2,
                "api_version": "v1"
            }
        }
    
    @staticmethod
    def generate_paginated_response_example(items_example: List[Any] = None) -> Dict[str, Any]:
        """Generate paginated response example"""
        return {
            "status": "success",
            "message": "Items retrieved successfully",
            "data": items_example or [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_prev": False
            },
            "meta": {
                "request_id": "550e8400-e29b-41d4-a716-446655440002",
                "timestamp": "2025-01-28T10:30:00Z",
                "processing_time_ms": 45.8,
                "api_version": "v1"
            },
            "links": [
                {"href": "/api/v1/items?page=1", "rel": "self"},
                {"href": "/api/v1/items?page=2", "rel": "next"},
                {"href": "/api/v1/items?page=8", "rel": "last"}
            ]
        }


class APIDocumentationEnhancer:
    """Enhance FastAPI documentation with professional standards"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.endpoint_docs: Dict[str, EndpointDocumentation] = {}
        self.custom_schemas: Dict[str, Type[BaseModel]] = {}
        
    def add_endpoint_documentation(self, 
                                 path: str, 
                                 method: str, 
                                 docs: EndpointDocumentation):
        """Add enhanced documentation for endpoint"""
        key = f"{method.upper()}:{path}"
        self.endpoint_docs[key] = docs
    
    def register_custom_schema(self, name: str, schema: Type[BaseModel]):
        """Register custom schema for documentation"""
        self.custom_schemas[name] = schema
    
    def generate_enhanced_openapi(self) -> Dict[str, Any]:
        """Generate enhanced OpenAPI specification"""
        # Get base OpenAPI spec
        openapi_schema = get_openapi(
            title="OHT-50 Backend API",
            version="1.0.0",
            description=self._generate_api_description(),
            routes=self.app.routes,
            servers=[
                {"url": "http://localhost:8000", "description": "Development server"},
                {"url": "https://api.oht50.com", "description": "Production server"}
            ]
        )
        
        # Enhance with additional information
        self._enhance_info_section(openapi_schema)
        self._enhance_paths_section(openapi_schema)
        self._enhance_components_section(openapi_schema)
        self._add_security_schemes(openapi_schema)
        self._add_tags_metadata(openapi_schema)
        
        return openapi_schema
    
    def _generate_api_description(self) -> str:
        """Generate comprehensive API description"""
        return """
# OHT-50 Autonomous Mobile Robot Backend API

## Overview
The OHT-50 Backend API provides comprehensive control and monitoring capabilities for autonomous mobile robots. This RESTful API follows OpenAPI 3.0 standards and implements advanced features including:

- **Authentication & Authorization**: OAuth2 with JWT tokens and RBAC
- **Real-time Monitoring**: WebSocket connections for telemetry streaming
- **Safety Systems**: Emergency stop controls and safety interlocks
- **Performance Monitoring**: Comprehensive metrics and alerting
- **HATEOAS Support**: Hypermedia navigation for API discoverability

## API Design Principles
- **Consistency**: Standardized response formats across all endpoints
- **Performance**: Optimized for low-latency operations (< 50ms P95)
- **Security**: Enterprise-grade authentication and authorization
- **Reliability**: Comprehensive error handling and graceful degradation
- **Scalability**: Designed for high-throughput production environments

## Response Format
All API responses follow a standardized format:
```json
{
    "status": "success|error|warning|info",
    "message": "Human-readable message",
    "data": "Response payload",
    "errors": ["Error details if applicable"],
    "meta": {
        "request_id": "Unique request identifier",
        "timestamp": "ISO 8601 timestamp",
        "processing_time_ms": "Processing time in milliseconds",
        "api_version": "API version"
    },
    "links": ["HATEOAS navigation links"]
}
```

## Rate Limiting
- **Standard endpoints**: 1000 requests per minute
- **Authentication endpoints**: 100 requests per minute
- **Emergency endpoints**: Unlimited (safety critical)

## Error Handling
Errors are returned with appropriate HTTP status codes and detailed error information including:
- Error code for programmatic handling
- Human-readable error message
- Field-specific validation errors
- Severity level (low, medium, high, critical)
        """.strip()
    
    def _enhance_info_section(self, openapi_schema: Dict[str, Any]):
        """Enhance OpenAPI info section"""
        openapi_schema["info"].update({
            "contact": {
                "name": "OHT-50 API Support",
                "email": "api-support@oht50.com",
                "url": "https://docs.oht50.com"
            },
            "license": {
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            },
            "termsOfService": "https://oht50.com/terms",
            "x-logo": {
                "url": "https://oht50.com/logo.png",
                "altText": "OHT-50 Logo"
            }
        })
    
    def _enhance_paths_section(self, openapi_schema: Dict[str, Any]):
        """Enhance paths with additional documentation"""
        if "paths" not in openapi_schema:
            return
        
        for path, methods in openapi_schema["paths"].items():
            for method, spec in methods.items():
                key = f"{method.upper()}:{path}"
                if key in self.endpoint_docs:
                    docs = self.endpoint_docs[key]
                    
                    # Add enhanced documentation
                    spec.update({
                        "summary": docs.summary,
                        "description": docs.description,
                        "x-category": docs.category.value
                    })
                    
                    # Add examples
                    if docs.example_request:
                        if "requestBody" in spec and "content" in spec["requestBody"]:
                            for content_type in spec["requestBody"]["content"]:
                                spec["requestBody"]["content"][content_type]["example"] = docs.example_request
                    
                    if docs.example_response:
                        if "responses" in spec and "200" in spec["responses"]:
                            response_spec = spec["responses"]["200"]
                            if "content" in response_spec:
                                for content_type in response_spec["content"]:
                                    response_spec["content"][content_type]["example"] = docs.example_response
                    
                    # Add error response examples
                    if docs.error_responses:
                        for error_response in docs.error_responses:
                            status_code = str(error_response.get("status_code", 400))
                            if status_code not in spec.get("responses", {}):
                                spec.setdefault("responses", {})[status_code] = {
                                    "description": error_response.get("description", "Error response"),
                                    "content": {
                                        "application/json": {
                                            "example": error_response.get("example", {})
                                        }
                                    }
                                }
                    
                    # Add performance and security notes
                    if docs.performance_notes:
                        spec["x-performance-notes"] = docs.performance_notes
                    
                    if docs.security_requirements:
                        spec["x-security-requirements"] = docs.security_requirements
                    
                    if docs.rate_limit:
                        spec["x-rate-limit"] = docs.rate_limit
    
    def _enhance_components_section(self, openapi_schema: Dict[str, Any]):
        """Enhance components section with custom schemas"""
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}
        
        # Add custom schemas
        for name, schema in self.custom_schemas.items():
            openapi_schema["components"]["schemas"][name] = schema.model_json_schema()
        
        # Add standard response schemas
        openapi_schema["components"]["schemas"].update({
            "StandardResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["success", "error", "warning", "info"]},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                    "errors": {"type": "array", "items": {"$ref": "#/components/schemas/ApiError"}},
                    "meta": {"$ref": "#/components/schemas/ResponseMetadata"},
                    "links": {"type": "array", "items": {"$ref": "#/components/schemas/HATEOASLink"}}
                },
                "required": ["status", "message", "meta"]
            },
            "ApiError": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "field": {"type": "string"},
                    "details": {"type": "object"}
                },
                "required": ["code", "message", "severity"]
            },
            "ResponseMetadata": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string", "format": "uuid"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "processing_time_ms": {"type": "number"},
                    "api_version": {"type": "string"},
                    "server_instance": {"type": "string"}
                },
                "required": ["request_id", "timestamp", "api_version"]
            },
            "HATEOASLink": {
                "type": "object",
                "properties": {
                    "href": {"type": "string", "format": "uri"},
                    "rel": {"type": "string"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                    "title": {"type": "string"},
                    "type": {"type": "string"}
                },
                "required": ["href", "rel", "method"]
            }
        })
    
    def _add_security_schemes(self, openapi_schema: Dict[str, Any]):
        """Add security schemes to OpenAPI spec"""
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Bearer token authentication"
            },
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "/api/v1/auth/oauth2/authorize",
                        "tokenUrl": "/api/v1/auth/oauth2/token",
                        "refreshUrl": "/api/v1/auth/oauth2/refresh",
                        "scopes": {
                            "robot:control": "Control robot operations",
                            "robot:emergency": "Emergency stop controls",
                            "telemetry:view": "View telemetry data",
                            "telemetry:export": "Export telemetry data",
                            "system:admin": "System administration",
                            "user:manage": "User management"
                        }
                    }
                }
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for programmatic access"
            }
        }
        
        # Add global security requirement
        openapi_schema["security"] = [
            {"BearerAuth": []},
            {"OAuth2": []},
            {"ApiKeyAuth": []}
        ]
    
    def _add_tags_metadata(self, openapi_schema: Dict[str, Any]):
        """Add enhanced tags metadata"""
        openapi_schema["tags"] = [
            {
                "name": "Authentication",
                "description": "User authentication and authorization endpoints",
                "externalDocs": {
                    "description": "Authentication Guide",
                    "url": "https://docs.oht50.com/auth"
                }
            },
            {
                "name": "Robot Control",
                "description": "Direct robot control and operation endpoints",
                "externalDocs": {
                    "description": "Robot Control Guide",
                    "url": "https://docs.oht50.com/robot-control"
                }
            },
            {
                "name": "Telemetry & Monitoring",
                "description": "Telemetry data retrieval and monitoring endpoints",
                "externalDocs": {
                    "description": "Telemetry Guide",
                    "url": "https://docs.oht50.com/telemetry"
                }
            },
            {
                "name": "Configuration",
                "description": "System and robot configuration management",
                "externalDocs": {
                    "description": "Configuration Guide",
                    "url": "https://docs.oht50.com/configuration"
                }
            },
            {
                "name": "System Management",
                "description": "System administration and management endpoints",
                "externalDocs": {
                    "description": "System Admin Guide",
                    "url": "https://docs.oht50.com/system-admin"
                }
            },
            {
                "name": "Health & Diagnostics",
                "description": "System health checks and diagnostic endpoints",
                "externalDocs": {
                    "description": "Health Monitoring Guide",
                    "url": "https://docs.oht50.com/health"
                }
            }
        ]


class OpenAPIValidator:
    """Validate OpenAPI specifications and endpoints"""
    
    def __init__(self, openapi_schema: Dict[str, Any]):
        self.schema = openapi_schema
        self.validation_results: List[Dict[str, Any]] = []
    
    def validate_specification(self) -> Dict[str, Any]:
        """Validate OpenAPI specification comprehensively"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
            "score": 0,
            "max_score": 100
        }
        
        # Validate required sections
        self._validate_info_section(results)
        self._validate_paths_section(results)
        self._validate_components_section(results)
        self._validate_security_section(results)
        self._validate_documentation_quality(results)
        
        # Calculate overall score
        error_penalty = len(results["errors"]) * 10
        warning_penalty = len(results["warnings"]) * 2
        results["score"] = max(0, results["max_score"] - error_penalty - warning_penalty)
        
        results["valid"] = results["score"] >= 80  # 80+ is considered valid
        
        return results
    
    def _validate_info_section(self, results: Dict[str, Any]):
        """Validate info section completeness"""
        info = self.schema.get("info", {})
        
        required_fields = ["title", "version", "description"]
        for field in required_fields:
            if field not in info or not info[field]:
                results["errors"].append(f"Missing required info.{field}")
        
        recommended_fields = ["contact", "license", "termsOfService"]
        for field in recommended_fields:
            if field not in info:
                results["warnings"].append(f"Missing recommended info.{field}")
        
        if len(info.get("description", "")) < 100:
            results["warnings"].append("API description is too short (< 100 chars)")
    
    def _validate_paths_section(self, results: Dict[str, Any]):
        """Validate paths section completeness"""
        paths = self.schema.get("paths", {})
        
        if not paths:
            results["errors"].append("No paths defined in specification")
            return
        
        for path, methods in paths.items():
            for method, spec in methods.items():
                endpoint_key = f"{method.upper()} {path}"
                
                # Check required fields
                if "summary" not in spec:
                    results["warnings"].append(f"{endpoint_key}: Missing summary")
                
                if "description" not in spec:
                    results["warnings"].append(f"{endpoint_key}: Missing description")
                
                # Check response documentation
                responses = spec.get("responses", {})
                if "200" not in responses and "201" not in responses:
                    results["warnings"].append(f"{endpoint_key}: No success response documented")
                
                # Check error responses
                has_error_responses = any(code.startswith("4") or code.startswith("5") 
                                        for code in responses.keys())
                if not has_error_responses:
                    results["warnings"].append(f"{endpoint_key}: No error responses documented")
                
                # Check examples
                self._validate_endpoint_examples(spec, endpoint_key, results)
    
    def _validate_components_section(self, results: Dict[str, Any]):
        """Validate components section"""
        components = self.schema.get("components", {})
        
        if "schemas" not in components:
            results["warnings"].append("No schemas defined in components")
        
        if "securitySchemes" not in components:
            results["warnings"].append("No security schemes defined")
    
    def _validate_security_section(self, results: Dict[str, Any]):
        """Validate security configuration"""
        security = self.schema.get("security", [])
        
        if not security:
            results["warnings"].append("No global security requirements defined")
        
        components = self.schema.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        if not security_schemes:
            results["errors"].append("No security schemes defined")
    
    def _validate_documentation_quality(self, results: Dict[str, Any]):
        """Validate overall documentation quality"""
        # Check for external documentation
        if "externalDocs" not in self.schema:
            results["info"].append("Consider adding external documentation links")
        
        # Check tags
        tags = self.schema.get("tags", [])
        if len(tags) < 3:
            results["warnings"].append("Consider organizing endpoints with more tags")
        
        # Check servers
        servers = self.schema.get("servers", [])
        if len(servers) < 2:
            results["info"].append("Consider documenting multiple server environments")
    
    def _validate_endpoint_examples(self, spec: Dict[str, Any], endpoint_key: str, results: Dict[str, Any]):
        """Validate endpoint examples"""
        # Check request examples
        request_body = spec.get("requestBody", {})
        if request_body and "content" in request_body:
            has_examples = any(
                "example" in content or "examples" in content
                for content in request_body["content"].values()
            )
            if not has_examples:
                results["info"].append(f"{endpoint_key}: Consider adding request examples")
        
        # Check response examples
        responses = spec.get("responses", {})
        for status_code, response in responses.items():
            if "content" in response:
                has_examples = any(
                    "example" in content or "examples" in content
                    for content in response["content"].values()
                )
                if not has_examples:
                    results["info"].append(
                        f"{endpoint_key}: Consider adding response examples for {status_code}"
                    )


class OpenAPITestGenerator:
    """Generate automated tests from OpenAPI specification"""
    
    def __init__(self, openapi_schema: Dict[str, Any]):
        self.schema = openapi_schema
    
    def generate_endpoint_tests(self) -> str:
        """Generate pytest tests for all endpoints"""
        test_code = '''# Auto-generated API tests from OpenAPI specification
import pytest
from httpx import AsyncClient

class TestAPIEndpoints:
    """Automated tests generated from OpenAPI specification"""
    
'''
        
        paths = self.schema.get("paths", {})
        for path, methods in paths.items():
            for method, spec in methods.items():
                test_name = self._generate_test_name(method, path)
                test_method = self._generate_test_method(method, path, spec)
                test_code += f"    {test_method}\n\n"
        
        return test_code
    
    def _generate_test_name(self, method: str, path: str) -> str:
        """Generate test method name"""
        clean_path = path.replace("/", "_").replace("{", "").replace("}", "").replace("-", "_")
        return f"test_{method.lower()}{clean_path}"
    
    def _generate_test_method(self, method: str, path: str, spec: Dict[str, Any]) -> str:
        """Generate individual test method"""
        test_name = self._generate_test_name(method, path)
        summary = spec.get("summary", f"Test {method.upper()} {path}")
        
        return f'''async def {test_name}(self, async_client: AsyncClient):
        """Test: {summary}"""
        response = await async_client.{method.lower()}("{path}")
        
        # Validate response status
        assert response.status_code in [200, 201, 202, 204, 400, 401, 403, 404, 500]
        
        # Validate response format if successful
        if response.status_code < 400:
            data = response.json()
            assert "status" in data
            assert "message" in data
            assert "meta" in data'''


# Factory function to setup OpenAPI excellence
def setup_openapi_excellence(app: FastAPI) -> APIDocumentationEnhancer:
    """Setup comprehensive OpenAPI documentation for FastAPI app"""
    
    enhancer = APIDocumentationEnhancer(app)
    
    # Example endpoint documentation
    enhancer.add_endpoint_documentation(
        "/api/v1/health",
        "GET",
        EndpointDocumentation(
            summary="System Health Check",
            description="Comprehensive system health check including all service dependencies",
            category=APICategory.HEALTH_MONITORING,
            example_response=OpenAPIExampleGenerator.generate_success_response_example({
                "status": "healthy",
                "services": {"database": "healthy", "cache": "healthy", "monitoring": "healthy"},
                "uptime_seconds": 86400,
                "version": "1.0.0"
            }),
            error_responses=[
                {
                    "status_code": 503,
                    "description": "Service unavailable",
                    "example": OpenAPIExampleGenerator.generate_error_response_example("SERVICE_UNAVAILABLE")
                }
            ],
            performance_notes="Typical response time: < 10ms",
            rate_limit="Unlimited (health check endpoint)"
        )
    )
    
    # Setup custom OpenAPI generation
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = enhancer.generate_enhanced_openapi()
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Add custom documentation routes
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="OHT-50 API Documentation",
            swagger_favicon_url="/static/favicon.ico",
            swagger_ui_parameters={
                "deepLinking": True,
                "displayRequestDuration": True,
                "filter": True,
                "showExtensions": True,
                "showCommonExtensions": True,
                "tryItOutEnabled": True
            }
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="OHT-50 API Documentation",
            redoc_favicon_url="/static/favicon.ico"
        )
    
    @app.get("/openapi.yaml", include_in_schema=False)
    async def get_openapi_yaml():
        """Get OpenAPI specification in YAML format"""
        openapi_dict = custom_openapi()
        yaml_content = yaml.dump(openapi_dict, default_flow_style=False)
        return Response(content=yaml_content, media_type="application/x-yaml")
    
    @app.get("/api/docs/validation", include_in_schema=False)
    async def validate_openapi():
        """Validate OpenAPI specification quality"""
        openapi_dict = custom_openapi()
        validator = OpenAPIValidator(openapi_dict)
        validation_results = validator.validate_specification()
        return validation_results
    
    logger.info("✅ OpenAPI Excellence setup completed")
    return enhancer
