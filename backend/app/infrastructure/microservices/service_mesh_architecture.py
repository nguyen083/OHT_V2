# 🏗️ MICROSERVICES & SERVICE MESH ARCHITECTURE - Phase 4 Implementation
"""
Service mesh-ready microservices architecture
Service discovery, load balancing, circuit breakers, distributed tracing

Phase 4: Microservices architecture for EXCELLENT level scalability
"""

import asyncio
import json
import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Callable, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import aiohttp
from contextlib import asynccontextmanager

from app.domain.interfaces.base_service import IBaseService

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Service type enumeration"""
    API_GATEWAY = "api_gateway"
    AUTH_SERVICE = "auth_service"
    ROBOT_CONTROL = "robot_control"
    TELEMETRY_SERVICE = "telemetry_service"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    NOTIFICATION = "notification"
    DATA_ANALYTICS = "data_analytics"


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    CONSISTENT_HASH = "consistent_hash"
    HEALTH_BASED = "health_based"


@dataclass
class ServiceInstance:
    """Service instance metadata"""
    instance_id: str
    service_name: str
    service_type: ServiceType
    version: str
    host: str
    port: int
    status: ServiceStatus
    health_check_url: str
    last_heartbeat: float
    metadata: Dict[str, Any]
    load_factor: float = 1.0  # Load balancing weight
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        return self.status == ServiceStatus.HEALTHY
    
    @property
    def heartbeat_age(self) -> float:
        return time.time() - self.last_heartbeat


@dataclass
class ServiceRequest:
    """Service request with tracing information"""
    request_id: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    service_name: str
    endpoint: str
    method: str
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    timestamp: float
    timeout: float = 30.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ServiceResponse:
    """Service response with performance metrics"""
    request_id: str
    trace_id: str
    status_code: int
    headers: Dict[str, str]
    body: Optional[Dict[str, Any]]
    response_time_ms: float
    timestamp: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    request_volume_threshold: int = 10
    error_percentage_threshold: float = 50.0
    half_open_max_calls: int = 3


class CircuitBreaker:
    """Circuit breaker for service resilience"""
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig):
        self.service_name = service_name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.request_log: List[bool] = []  # True for success, False for failure
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        current_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if current_time - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker for {self.service_name} moved to HALF_OPEN")
                return True
            return False
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record successful request"""
        self.request_log.append(True)
        self._trim_request_log()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit breaker for {self.service_name} moved to CLOSED")
    
    def record_failure(self):
        """Record failed request"""
        current_time = time.time()
        self.request_log.append(False)
        self._trim_request_log()
        self.last_failure_time = current_time
        
        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            if self._should_open_circuit():
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker for {self.service_name} OPENED")
        
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.half_open_calls = 0
            logger.warning(f"Circuit breaker for {self.service_name} returned to OPEN")
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened"""
        if len(self.request_log) < self.config.request_volume_threshold:
            return False
        
        failure_count = sum(1 for success in self.request_log if not success)
        failure_percentage = (failure_count / len(self.request_log)) * 100
        
        return failure_percentage >= self.config.error_percentage_threshold
    
    def _trim_request_log(self):
        """Keep request log size manageable"""
        if len(self.request_log) > self.config.request_volume_threshold * 2:
            self.request_log = self.request_log[-self.config.request_volume_threshold:]


class ServiceRegistry:
    """Service discovery and registry"""
    
    def __init__(self):
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.service_configs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
    async def register_service(self, instance: ServiceInstance):
        """Register service instance"""
        async with self._lock:
            service_name = instance.service_name
            
            if service_name not in self.services:
                self.services[service_name] = []
            
            # Remove existing instance with same ID
            self.services[service_name] = [
                inst for inst in self.services[service_name] 
                if inst.instance_id != instance.instance_id
            ]
            
            # Add new instance
            self.services[service_name].append(instance)
            
            logger.info(f"Registered service instance: {service_name}:{instance.instance_id}")
    
    async def deregister_service(self, service_name: str, instance_id: str):
        """Deregister service instance"""
        async with self._lock:
            if service_name in self.services:
                self.services[service_name] = [
                    inst for inst in self.services[service_name] 
                    if inst.instance_id != instance_id
                ]
                
                logger.info(f"Deregistered service instance: {service_name}:{instance_id}")
    
    async def discover_service(self, service_name: str) -> List[ServiceInstance]:
        """Discover healthy service instances"""
        async with self._lock:
            if service_name not in self.services:
                return []
            
            # Filter healthy instances
            healthy_instances = [
                inst for inst in self.services[service_name]
                if inst.is_healthy and inst.heartbeat_age < 30  # 30 seconds max age
            ]
            
            return healthy_instances
    
    async def update_service_health(self, service_name: str, instance_id: str, status: ServiceStatus):
        """Update service health status"""
        async with self._lock:
            if service_name in self.services:
                for instance in self.services[service_name]:
                    if instance.instance_id == instance_id:
                        instance.status = status
                        instance.last_heartbeat = time.time()
                        break
    
    def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """Get all registered services"""
        return self.services.copy()


class LoadBalancer:
    """Load balancer with multiple strategies"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.round_robin_counters: Dict[str, int] = {}
        self.connection_counts: Dict[str, int] = {}
    
    async def select_instance(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance based on load balancing strategy"""
        if not instances:
            return None
        
        healthy_instances = [inst for inst in instances if inst.is_healthy]
        if not healthy_instances:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(healthy_instances)
        
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_selection(healthy_instances)
        
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
            return self._weighted_random_selection(healthy_instances)
        
        elif self.strategy == LoadBalancingStrategy.HEALTH_BASED:
            return self._health_based_selection(healthy_instances)
        
        else:
            return healthy_instances[0]  # Fallback
    
    def _round_robin_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round-robin instance selection"""
        service_name = instances[0].service_name
        
        if service_name not in self.round_robin_counters:
            self.round_robin_counters[service_name] = 0
        
        index = self.round_robin_counters[service_name] % len(instances)
        self.round_robin_counters[service_name] += 1
        
        return instances[index]
    
    def _least_connections_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with least connections"""
        min_connections = float('inf')
        selected_instance = instances[0]
        
        for instance in instances:
            instance_key = f"{instance.service_name}:{instance.instance_id}"
            connections = self.connection_counts.get(instance_key, 0)
            
            if connections < min_connections:
                min_connections = connections
                selected_instance = instance
        
        return selected_instance
    
    def _weighted_random_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted random selection based on load factors"""
        import random
        
        total_weight = sum(inst.load_factor for inst in instances)
        if total_weight == 0:
            return instances[0]
        
        random_value = random.uniform(0, total_weight)
        current_weight = 0
        
        for instance in instances:
            current_weight += instance.load_factor
            if random_value <= current_weight:
                return instance
        
        return instances[-1]  # Fallback
    
    def _health_based_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance based on health metrics"""
        # Prefer instances with recent heartbeats
        instances.sort(key=lambda x: x.heartbeat_age)
        return instances[0]
    
    def track_connection(self, instance: ServiceInstance, increment: bool = True):
        """Track active connections to instance"""
        instance_key = f"{instance.service_name}:{instance.instance_id}"
        
        if increment:
            self.connection_counts[instance_key] = self.connection_counts.get(instance_key, 0) + 1
        else:
            if instance_key in self.connection_counts:
                self.connection_counts[instance_key] = max(0, self.connection_counts[instance_key] - 1)


class DistributedTracing:
    """Distributed tracing for microservices"""
    
    def __init__(self):
        self.active_traces: Dict[str, Dict[str, Any]] = {}
        self.trace_storage: List[Dict[str, Any]] = []
    
    def create_trace(self, service_name: str, operation_name: str) -> str:
        """Create new trace"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        trace_data = {
            "trace_id": trace_id,
            "spans": [{
                "span_id": span_id,
                "parent_span_id": None,
                "service_name": service_name,
                "operation_name": operation_name,
                "start_time": time.time(),
                "tags": {},
                "logs": []
            }]
        }
        
        self.active_traces[trace_id] = trace_data
        return trace_id
    
    def create_child_span(self, trace_id: str, parent_span_id: str, 
                         service_name: str, operation_name: str) -> str:
        """Create child span"""
        if trace_id not in self.active_traces:
            return self.create_trace(service_name, operation_name)
        
        span_id = str(uuid.uuid4())
        
        span_data = {
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "service_name": service_name,
            "operation_name": operation_name,
            "start_time": time.time(),
            "tags": {},
            "logs": []
        }
        
        self.active_traces[trace_id]["spans"].append(span_data)
        return span_id
    
    def finish_span(self, trace_id: str, span_id: str, tags: Dict[str, Any] = None):
        """Finish span and record timing"""
        if trace_id not in self.active_traces:
            return
        
        for span in self.active_traces[trace_id]["spans"]:
            if span["span_id"] == span_id:
                span["end_time"] = time.time()
                span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
                if tags:
                    span["tags"].update(tags)
                break
    
    def add_log(self, trace_id: str, span_id: str, message: str, level: str = "info"):
        """Add log entry to span"""
        if trace_id not in self.active_traces:
            return
        
        for span in self.active_traces[trace_id]["spans"]:
            if span["span_id"] == span_id:
                span["logs"].append({
                    "timestamp": time.time(),
                    "level": level,
                    "message": message
                })
                break
    
    def finish_trace(self, trace_id: str):
        """Finish trace and store"""
        if trace_id in self.active_traces:
            trace_data = self.active_traces.pop(trace_id)
            trace_data["finished_at"] = time.time()
            self.trace_storage.append(trace_data)
            
            # Keep storage manageable
            if len(self.trace_storage) > 10000:
                self.trace_storage = self.trace_storage[-5000:]


class ServiceMeshClient(IBaseService):
    """Service mesh client for microservices communication"""
    
    def __init__(self, 
                 service_name: str,
                 service_type: ServiceType,
                 host: str = "localhost",
                 port: int = 8000):
        
        self.service_name = service_name
        self.service_type = service_type
        self.host = host
        self.port = port
        self.instance_id = str(uuid.uuid4())
        self.version = "1.0.0"
        
        # Core components
        self.registry = ServiceRegistry()
        self.load_balancer = LoadBalancer()
        self.tracing = DistributedTracing()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Service instance
        self.instance = ServiceInstance(
            instance_id=self.instance_id,
            service_name=service_name,
            service_type=service_type,
            version=self.version,
            host=host,
            port=port,
            status=ServiceStatus.STARTING,
            health_check_url=f"http://{host}:{port}/health",
            last_heartbeat=time.time(),
            metadata={
                "start_time": time.time(),
                "environment": "production"
            }
        )
        
        # HTTP client session
        self.session: Optional[aiohttp.ClientSession] = None
        self.initialized = False
        
        logger.info(f"✅ ServiceMeshClient initialized: {service_name}:{self.instance_id}")
    
    async def initialize(self) -> bool:
        """Initialize service mesh client"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30.0)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Register service
            self.instance.status = ServiceStatus.HEALTHY
            await self.registry.register_service(self.instance)
            
            # Start heartbeat task
            asyncio.create_task(self._heartbeat_loop())
            
            self.initialized = True
            logger.info(f"✅ ServiceMeshClient initialization completed: {self.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ ServiceMeshClient initialization failed: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown service mesh client"""
        try:
            # Deregister service
            await self.registry.deregister_service(self.service_name, self.instance_id)
            
            # Close HTTP session
            if self.session:
                await self.session.close()
            
            self.initialized = False
            logger.info(f"✅ ServiceMeshClient shutdown completed: {self.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ ServiceMeshClient shutdown failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Service mesh health check"""
        try:
            all_services = self.registry.get_all_services()
            total_instances = sum(len(instances) for instances in all_services.values())
            healthy_instances = sum(
                len([inst for inst in instances if inst.is_healthy])
                for instances in all_services.values()
            )
            
            return {
                "service": "ServiceMeshClient",
                "status": "healthy" if self.initialized else "unhealthy",
                "instance_id": self.instance_id,
                "service_name": self.service_name,
                "service_type": self.service_type.value,
                "registry": {
                    "total_services": len(all_services),
                    "total_instances": total_instances,
                    "healthy_instances": healthy_instances
                },
                "circuit_breakers": {
                    name: breaker.state.value 
                    for name, breaker in self.circuit_breakers.items()
                },
                "active_traces": len(self.tracing.active_traces)
            }
            
        except Exception as e:
            return {
                "service": "ServiceMeshClient",
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": "ServiceMeshClient",
            "initialized": self.initialized,
            "instance_id": self.instance_id,
            "service_name": self.service_name
        }
    
    async def call_service(self, 
                          service_name: str,
                          endpoint: str,
                          method: str = "GET",
                          data: Optional[Dict[str, Any]] = None,
                          headers: Optional[Dict[str, str]] = None,
                          timeout: float = 30.0,
                          trace_id: Optional[str] = None) -> ServiceResponse:
        """Call another service through service mesh"""
        
        # Create or continue trace
        if trace_id is None:
            trace_id = self.tracing.create_trace(self.service_name, f"call_{service_name}")
        
        span_id = self.tracing.create_child_span(
            trace_id, None, service_name, f"{method} {endpoint}"
        )
        
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        try:
            # Discover service instances
            instances = await self.registry.discover_service(service_name)
            if not instances:
                raise Exception(f"No healthy instances found for service: {service_name}")
            
            # Select instance using load balancer
            instance = await self.load_balancer.select_instance(instances)
            if not instance:
                raise Exception(f"Load balancer failed to select instance for: {service_name}")
            
            # Check circuit breaker
            circuit_breaker = self._get_circuit_breaker(service_name)
            if not circuit_breaker.can_execute():
                raise Exception(f"Circuit breaker OPEN for service: {service_name}")
            
            # Track connection
            self.load_balancer.track_connection(instance, increment=True)
            
            try:
                # Prepare request
                url = f"{instance.base_url}{endpoint}"
                request_headers = headers or {}
                request_headers.update({
                    "X-Request-ID": request_id,
                    "X-Trace-ID": trace_id,
                    "X-Span-ID": span_id,
                    "X-Service-Name": self.service_name
                })
                
                # Make request
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    
                    response_body = None
                    if response.content_type == "application/json":
                        response_body = await response.json()
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    # Record success/failure
                    if response.status < 400:
                        circuit_breaker.record_success()
                        self.tracing.add_log(trace_id, span_id, f"Request successful: {response.status}")
                    else:
                        circuit_breaker.record_failure()
                        self.tracing.add_log(trace_id, span_id, f"Request failed: {response.status}", "error")
                    
                    # Create response
                    service_response = ServiceResponse(
                        request_id=request_id,
                        trace_id=trace_id,
                        status_code=response.status,
                        headers=dict(response.headers),
                        body=response_body,
                        response_time_ms=response_time,
                        timestamp=time.time()
                    )
                    
                    # Finish span
                    self.tracing.finish_span(trace_id, span_id, {
                        "http.status_code": response.status,
                        "http.method": method,
                        "http.url": url,
                        "response_time_ms": response_time
                    })
                    
                    return service_response
            
            finally:
                # Release connection
                self.load_balancer.track_connection(instance, increment=False)
        
        except Exception as e:
            # Record failure
            circuit_breaker = self._get_circuit_breaker(service_name)
            circuit_breaker.record_failure()
            
            response_time = (time.time() - start_time) * 1000
            
            # Log error
            self.tracing.add_log(trace_id, span_id, f"Request error: {str(e)}", "error")
            
            # Finish span with error
            self.tracing.finish_span(trace_id, span_id, {
                "error": True,
                "error.message": str(e),
                "response_time_ms": response_time
            })
            
            return ServiceResponse(
                request_id=request_id,
                trace_id=trace_id,
                status_code=500,
                headers={},
                body=None,
                response_time_ms=response_time,
                timestamp=time.time(),
                error=str(e)
            )
    
    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            config = CircuitBreakerConfig()
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, config)
        
        return self.circuit_breakers[service_name]
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to registry"""
        while self.initialized:
            try:
                # Update heartbeat
                self.instance.last_heartbeat = time.time()
                await self.registry.update_service_health(
                    self.service_name, 
                    self.instance_id, 
                    ServiceStatus.HEALTHY
                )
                
                # Wait for next heartbeat
                await asyncio.sleep(10)  # 10 second intervals
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(10)
    
    # Convenience methods for common operations
    async def get(self, service_name: str, endpoint: str, **kwargs) -> ServiceResponse:
        """GET request to service"""
        return await self.call_service(service_name, endpoint, "GET", **kwargs)
    
    async def post(self, service_name: str, endpoint: str, data: Dict[str, Any], **kwargs) -> ServiceResponse:
        """POST request to service"""
        return await self.call_service(service_name, endpoint, "POST", data=data, **kwargs)
    
    async def put(self, service_name: str, endpoint: str, data: Dict[str, Any], **kwargs) -> ServiceResponse:
        """PUT request to service"""
        return await self.call_service(service_name, endpoint, "PUT", data=data, **kwargs)
    
    async def delete(self, service_name: str, endpoint: str, **kwargs) -> ServiceResponse:
        """DELETE request to service"""
        return await self.call_service(service_name, endpoint, "DELETE", **kwargs)


# Factory function for creating service mesh client
def create_service_mesh_client(
    service_name: str,
    service_type: ServiceType,
    host: str = "localhost",
    port: int = 8000
) -> ServiceMeshClient:
    """Create and return service mesh client"""
    
    return ServiceMeshClient(service_name, service_type, host, port)


# Global service mesh client instance
_service_mesh_client: Optional[ServiceMeshClient] = None

async def get_service_mesh_client() -> ServiceMeshClient:
    """Get singleton service mesh client"""
    global _service_mesh_client
    if _service_mesh_client is None:
        _service_mesh_client = create_service_mesh_client(
            service_name="oht50_backend",
            service_type=ServiceType.API_GATEWAY
        )
        await _service_mesh_client.initialize()
    return _service_mesh_client
