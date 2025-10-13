# ⚡ STANDARDIZED API RESPONSE SCHEMAS - Phase 3 Implementation
"""
Unified API response schemas with HATEOAS support
Provides consistent response format across all endpoints

Phase 3: API Performance optimization with standardized responses
"""

from typing import Any, Dict, List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
import uuid


class ResponseStatus(str, Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HATEOASLink(BaseModel):
    """HATEOAS link representation"""
    href: str = Field(..., description="Link URL")
    rel: str = Field(..., description="Link relationship")
    method: str = Field(default="GET", description="HTTP method")
    title: Optional[str] = Field(None, description="Human-readable title")
    type: Optional[str] = Field(None, description="Media type")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "href": "/api/v1/robot/status",
                "rel": "self",
                "method": "GET",
                "title": "Get Robot Status",
                "type": "application/json"
            }
        }
    )


class ApiError(BaseModel):
    """Standardized error information"""
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    severity: ErrorSeverity = Field(default=ErrorSeverity.MEDIUM, description="Error severity level")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "severity": "medium",
                "field": "username",
                "details": {"min_length": 3, "provided_length": 1}
            }
        }
    )


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., description="Current page number", ge=1)
    per_page: int = Field(..., description="Items per page", ge=1, le=1000)
    total_items: int = Field(..., description="Total number of items", ge=0)
    total_pages: int = Field(..., description="Total number of pages", ge=0)
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "per_page": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_prev": False
            }
        }
    )


class ResponseMetadata(BaseModel):
    """Response metadata with performance metrics"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    api_version: str = Field(default="v1", description="API version")
    server_instance: Optional[str] = Field(None, description="Server instance identifier")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-28T10:30:00Z",
                "processing_time_ms": 23.5,
                "api_version": "v1",
                "server_instance": "oht50-backend-01"
            }
        }
    )


# Generic type for response data
T = TypeVar('T')


class BaseApiResponse(BaseModel, Generic[T]):
    """Base API response with HATEOAS support"""
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    data: Optional[T] = Field(None, description="Response data")
    errors: Optional[List[ApiError]] = Field(None, description="List of errors if any")
    warnings: Optional[List[str]] = Field(None, description="List of warnings if any")
    meta: ResponseMetadata = Field(default_factory=ResponseMetadata, description="Response metadata")
    links: Optional[List[HATEOASLink]] = Field(None, description="HATEOAS navigation links")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {"id": 1, "name": "Example"},
                "errors": None,
                "warnings": None,
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
                        "method": "GET"
                    }
                ]
            }
        }
    )


class PaginatedApiResponse(BaseApiResponse[List[T]]):
    """Paginated API response"""
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination metadata")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Items retrieved successfully",
                "data": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total_items": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_prev": False
                },
                "links": [
                    {"href": "/api/v1/items?page=1", "rel": "self"},
                    {"href": "/api/v1/items?page=2", "rel": "next"},
                    {"href": "/api/v1/items?page=8", "rel": "last"}
                ]
            }
        }
    )


# Specialized response types for common operations
class SuccessResponse(BaseApiResponse[T]):
    """Success response wrapper"""
    status: ResponseStatus = Field(default=ResponseStatus.SUCCESS)


class ErrorResponse(BaseApiResponse[None]):
    """Error response wrapper"""
    status: ResponseStatus = Field(default=ResponseStatus.ERROR)
    data: None = Field(default=None)


class WarningResponse(BaseApiResponse[T]):
    """Warning response wrapper"""
    status: ResponseStatus = Field(default=ResponseStatus.WARNING)


# Common response data models
class HealthCheckData(BaseModel):
    """Health check response data"""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency statuses")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")


class OperationStatusData(BaseModel):
    """Operation status response data"""
    operation_id: str = Field(..., description="Operation identifier")
    status: str = Field(..., description="Operation status")
    progress_percent: Optional[float] = Field(None, description="Progress percentage", ge=0, le=100)
    started_at: datetime = Field(..., description="Operation start time")
    completed_at: Optional[datetime] = Field(None, description="Operation completion time")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result")


class ValidationErrorData(BaseModel):
    """Validation error response data"""
    field_errors: Dict[str, List[str]] = Field(default_factory=dict, description="Field-specific errors")
    general_errors: List[str] = Field(default_factory=list, description="General validation errors")
    error_count: int = Field(..., description="Total number of errors")


# Type aliases for common response patterns
HealthCheckResponse = SuccessResponse[HealthCheckData]
OperationStatusResponse = SuccessResponse[OperationStatusData]
ValidationErrorResponse = ErrorResponse


class ResponseBuilder:
    """Builder class for creating standardized API responses"""
    
    @staticmethod
    def success(
        data: T = None,
        message: str = "Operation completed successfully",
        links: Optional[List[HATEOASLink]] = None,
        processing_time_ms: Optional[float] = None
    ) -> SuccessResponse[T]:
        """Build success response"""
        meta = ResponseMetadata()
        if processing_time_ms is not None:
            meta.processing_time_ms = processing_time_ms
            
        return SuccessResponse(
            message=message,
            data=data,
            meta=meta,
            links=links
        )
    
    @staticmethod
    def error(
        message: str,
        errors: Optional[List[ApiError]] = None,
        error_code: str = "INTERNAL_ERROR",
        processing_time_ms: Optional[float] = None
    ) -> ErrorResponse:
        """Build error response"""
        meta = ResponseMetadata()
        if processing_time_ms is not None:
            meta.processing_time_ms = processing_time_ms
            
        if errors is None and message:
            errors = [ApiError(code=error_code, message=message)]
            
        return ErrorResponse(
            message=message,
            errors=errors,
            meta=meta
        )
    
    @staticmethod
    def warning(
        data: T = None,
        message: str = "Operation completed with warnings",
        warnings: Optional[List[str]] = None,
        links: Optional[HATEOASLink] = None,
        processing_time_ms: Optional[float] = None
    ) -> WarningResponse[T]:
        """Build warning response"""
        meta = ResponseMetadata()
        if processing_time_ms is not None:
            meta.processing_time_ms = processing_time_ms
            
        return WarningResponse(
            message=message,
            data=data,
            warnings=warnings,
            meta=meta,
            links=links
        )
    
    @staticmethod
    def paginated(
        data: List[T],
        page: int,
        per_page: int,
        total_items: int,
        message: str = "Items retrieved successfully",
        base_url: str = "/api/v1",
        processing_time_ms: Optional[float] = None
    ) -> PaginatedApiResponse[T]:
        """Build paginated response with HATEOAS links"""
        total_pages = (total_items + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        # Build HATEOAS links
        links = [
            HATEOASLink(href=f"{base_url}?page={page}&per_page={per_page}", rel="self"),
            HATEOASLink(href=f"{base_url}?page=1&per_page={per_page}", rel="first"),
            HATEOASLink(href=f"{base_url}?page={total_pages}&per_page={per_page}", rel="last")
        ]
        
        if has_prev:
            links.append(
                HATEOASLink(href=f"{base_url}?page={page-1}&per_page={per_page}", rel="prev")
            )
        
        if has_next:
            links.append(
                HATEOASLink(href=f"{base_url}?page={page+1}&per_page={per_page}", rel="next")
            )
        
        meta = ResponseMetadata()
        if processing_time_ms is not None:
            meta.processing_time_ms = processing_time_ms
        
        return PaginatedApiResponse(
            message=message,
            data=data,
            pagination=pagination,
            meta=meta,
            links=links
        )


class HATEOASBuilder:
    """Builder for HATEOAS links"""
    
    @staticmethod
    def build_resource_links(
        resource_type: str,
        resource_id: Union[str, int],
        base_url: str = "/api/v1",
        available_operations: Optional[List[str]] = None
    ) -> List[HATEOASLink]:
        """Build standard HATEOAS links for a resource"""
        if available_operations is None:
            available_operations = ["get", "update", "delete"]
        
        links = []
        resource_url = f"{base_url}/{resource_type}/{resource_id}"
        
        # Self link
        links.append(HATEOASLink(
            href=resource_url,
            rel="self",
            method="GET",
            title=f"Get {resource_type.title()}"
        ))
        
        # Collection link
        links.append(HATEOASLink(
            href=f"{base_url}/{resource_type}",
            rel="collection",
            method="GET",
            title=f"List {resource_type.title()}s"
        ))
        
        # Operation links
        if "update" in available_operations:
            links.append(HATEOASLink(
                href=resource_url,
                rel="edit",
                method="PUT",
                title=f"Update {resource_type.title()}"
            ))
        
        if "delete" in available_operations:
            links.append(HATEOASLink(
                href=resource_url,
                rel="delete",
                method="DELETE",
                title=f"Delete {resource_type.title()}"
            ))
        
        return links
    
    @staticmethod
    def build_collection_links(
        resource_type: str,
        base_url: str = "/api/v1",
        available_operations: Optional[List[str]] = None
    ) -> List[HATEOASLink]:
        """Build HATEOAS links for a collection"""
        if available_operations is None:
            available_operations = ["create"]
        
        links = []
        collection_url = f"{base_url}/{resource_type}"
        
        # Self link
        links.append(HATEOASLink(
            href=collection_url,
            rel="self",
            method="GET",
            title=f"List {resource_type.title()}s"
        ))
        
        # Create link
        if "create" in available_operations:
            links.append(HATEOASLink(
                href=collection_url,
                rel="create",
                method="POST",
                title=f"Create {resource_type.title()}"
            ))
        
        return links


# Export commonly used types
__all__ = [
    "ResponseStatus", "ErrorSeverity", "HATEOASLink", "ApiError",
    "PaginationMeta", "ResponseMetadata", "BaseApiResponse", 
    "PaginatedApiResponse", "SuccessResponse", "ErrorResponse", 
    "WarningResponse", "HealthCheckResponse", "OperationStatusResponse",
    "ValidationErrorResponse", "ResponseBuilder", "HATEOASBuilder"
]
