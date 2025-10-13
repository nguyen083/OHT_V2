# 🚀 PHASE 2: SERVICE LAYER & DI CONTAINER - DETAILED IMPLEMENTATION PLAN

**Date:** 2025-01-28  
**Phase:** 2 of 4  
**Duration:** Week 2-3 (10-12 working days)  
**Prerequisites:** Phase 1 completed ✅

---

## 🎯 **PHASE 2 OBJECTIVES**

Transform tightly coupled service layer thành **loosely coupled, interface-based architecture** với **Dependency Injection container** để achieve:

- ✅ **Loose Coupling:** Services depend on abstractions, not implementations
- ✅ **Testability:** Easy mocking và unit testing
- ✅ **Flexibility:** Swap implementations (mock/real/test) easily
- ✅ **SOLID Compliance:** Dependency Inversion Principle
- ✅ **Redis Security:** Scalable token management

---

## 📊 **PHASE 2 DELIVERABLES**

### **Major Components:**
1. ✅ Abstract Service Interfaces (Domain Layer)
2. ✅ Dependency Injection Container
3. ✅ Service Implementations Refactoring
4. ✅ Redis-based Token Store
5. ✅ Mock Service Registry

### **Expected Improvements:**
- **Service Coupling:** Tight → Loose
- **Test Coverage:** ~60% → ~75%
- **Security Score:** 7/10 → 8/10
- **Architecture Score:** 6/10 → 8/10

---

## 🗂️ **IMPLEMENTATION TASKS BREAKDOWN**

### **TASK GROUP 1: SERVICE INTERFACES (Days 1-3)**

#### **Task 1.1: Create Base Service Interface**
**Priority:** CRITICAL  
**Effort:** 2 hours  
**Dependencies:** None

**Actions:**
- [ ] Create `domain/interfaces/base_service.py`
- [ ] Define `IBaseService` abstract class với:
  - `initialize()` method
  - `shutdown()` method
  - `health_check()` method
  - `get_status()` method

**Code Structure:**
```python
# domain/interfaces/base_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class IBaseService(ABC):
    """Base interface for all services"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize service"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown service gracefully"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        pass
```

**Validation:**
- [ ] File created at correct location
- [ ] All abstract methods defined
- [ ] Type hints properly specified
- [ ] Docstrings complete

---

#### **Task 1.2: Create Firmware Service Interface**
**Priority:** CRITICAL  
**Effort:** 3 hours  
**Dependencies:** Task 1.1

**Actions:**
- [ ] Create `domain/interfaces/firmware_service.py`
- [ ] Define `IFirmwareService` extending `IBaseService`
- [ ] Add firmware-specific methods:
  - `get_robot_status()`
  - `send_robot_command()`
  - `get_telemetry_data()`
  - `get_connection_status()`

**Code Structure:**
```python
# domain/interfaces/firmware_service.py
from abc import abstractmethod
from typing import Dict, Any
from .base_service import IBaseService

class IFirmwareService(IBaseService):
    """Interface for firmware integration services"""
    
    @abstractmethod
    async def get_robot_status(self) -> Dict[str, Any]:
        """Get current robot status"""
        pass
    
    @abstractmethod
    async def send_robot_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to robot"""
        pass
    
    @abstractmethod
    async def get_telemetry_data(self) -> Dict[str, Any]:
        """Get telemetry data"""
        pass
    
    @abstractmethod
    def get_connection_status(self) -> Dict[str, Any]:
        """Get firmware connection status"""
        pass
```

**Validation:**
- [ ] Extends IBaseService correctly
- [ ] All firmware methods defined
- [ ] Parameter và return types specified
- [ ] Compatible với existing UnifiedFirmwareService

---

#### **Task 1.3: Create Cache Service Interface**
**Priority:** HIGH  
**Effort:** 2 hours  
**Dependencies:** Task 1.1

**Actions:**
- [ ] Create `domain/interfaces/cache_service.py`
- [ ] Define `ICacheService` với methods:
  - `get(key: str)`
  - `set(key: str, value: Any, ttl: int)`
  - `delete(key: str)`
  - `clear()`
  - `get_stats()`

**Code Structure:**
```python
# domain/interfaces/cache_service.py
from abc import abstractmethod
from typing import Any, Optional
from .base_service import IBaseService

class ICacheService(IBaseService):
    """Interface for caching services"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass
```

**Validation:**
- [ ] All cache operations defined
- [ ] TTL support included
- [ ] Stats method for monitoring

---

#### **Task 1.4: Create Auth Service Interface**
**Priority:** HIGH  
**Effort:** 2 hours  
**Dependencies:** Task 1.1

**Actions:**
- [ ] Create `domain/interfaces/auth_service.py`
- [ ] Define `IAuthService` với methods:
  - `create_token(user_data: Dict)`
  - `validate_token(token: str)`
  - `revoke_token(token: str)`
  - `refresh_token(token: str)`

**Code Structure:**
```python
# domain/interfaces/auth_service.py
from abc import abstractmethod
from typing import Dict, Any, Optional
from .base_service import IBaseService

class IAuthService(IBaseService):
    """Interface for authentication services"""
    
    @abstractmethod
    def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create authentication token"""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate token and return user data"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        pass
    
    @abstractmethod
    async def refresh_token(self, token: str) -> Optional[str]:
        """Refresh authentication token"""
        pass
```

**Validation:**
- [ ] Token lifecycle methods complete
- [ ] Async methods for I/O operations
- [ ] Return types properly defined

---

### **TASK GROUP 2: DEPENDENCY INJECTION CONTAINER (Days 4-5)**

#### **Task 2.1: Install DI Library**
**Priority:** CRITICAL  
**Effort:** 1 hour  
**Dependencies:** None

**Actions:**
- [ ] Add `dependency-injector` to `requirements.txt`
- [ ] Install package: `pip install dependency-injector`
- [ ] Verify installation

**Command:**
```bash
echo "dependency-injector==4.41.0" >> backend/requirements.txt
cd backend && pip install dependency-injector
```

**Validation:**
- [ ] Package added to requirements.txt
- [ ] Successfully installed
- [ ] Import test passes

---

#### **Task 2.2: Create DI Container Structure**
**Priority:** CRITICAL  
**Effort:** 4 hours  
**Dependencies:** Task 2.1, Task Group 1

**Actions:**
- [ ] Create `core/dependencies.py`
- [ ] Define `ServiceContainer` class
- [ ] Configure service providers:
  - Firmware service provider
  - Cache service provider
  - Auth service provider
  - Database provider
- [ ] Add environment-based service selection (mock vs real)

**Code Structure:**
```python
# core/dependencies.py
from dependency_injector import containers, providers
from app.config import Settings

class ServiceContainer(containers.DeclarativeContainer):
    """Dependency Injection Container"""
    
    # Configuration
    config = providers.Configuration()
    
    # Settings
    settings = providers.Singleton(Settings)
    
    # Infrastructure Services
    cache_service = providers.Factory(
        lambda: get_cache_service_implementation(settings),
    )
    
    # Domain Services  
    firmware_service = providers.Factory(
        lambda: get_firmware_service_implementation(settings),
    )
    
    auth_service = providers.Factory(
        lambda: get_auth_service_implementation(settings, cache_service),
    )

def get_service_container() -> ServiceContainer:
    """Get configured service container"""
    container = ServiceContainer()
    container.config.from_dict({
        "environment": os.getenv("ENVIRONMENT", "development"),
        "use_mock": os.getenv("USE_MOCK_FIRMWARE", "false").lower() == "true"
    })
    return container
```

**Validation:**
- [ ] Container properly configured
- [ ] Service providers registered
- [ ] Environment-based selection works
- [ ] Singleton/Factory scopes correct

---

#### **Task 2.3: Integrate DI Container với Application Factory**
**Priority:** CRITICAL  
**Effort:** 2 hours  
**Dependencies:** Task 2.2

**Actions:**
- [ ] Update `core/application.py` to use DI container
- [ ] Replace direct service imports với container.resolve()
- [ ] Configure dependency injection cho API endpoints
- [ ] Add container to FastAPI app state

**Code Changes:**
```python
# In core/application.py
from app.core.dependencies import get_service_container

def create_application() -> FastAPI:
    # ...
    
    # Setup DI Container
    container = get_service_container()
    app.container = container
    
    # Configure routes with DI
    _configure_routes(app, settings, container)
    
    return app
```

**Validation:**
- [ ] Container accessible in app.container
- [ ] Services resolved correctly
- [ ] No circular dependencies
- [ ] Startup successful

---

### **TASK GROUP 3: SERVICE IMPLEMENTATIONS (Days 6-8)**

#### **Task 3.1: Refactor UnifiedFirmwareService**
**Priority:** CRITICAL  
**Effort:** 4 hours  
**Dependencies:** Task 1.2, Task 2.2

**Actions:**
- [ ] Move `services/unified_firmware_service.py` to `infrastructure/external/`
- [ ] Implement `IFirmwareService` interface
- [ ] Add proper dependency injection
- [ ] Maintain backward compatibility

**Code Structure:**
```python
# infrastructure/external/firmware_service_impl.py
from app.domain.interfaces.firmware_service import IFirmwareService

class UnifiedFirmwareService(IFirmwareService):
    """Production firmware service implementation"""
    
    def __init__(self, firmware_url: str, cache_service: ICacheService):
        self.firmware_url = firmware_url
        self.cache = cache_service
        # ... existing init code
    
    async def get_robot_status(self) -> Dict[str, Any]:
        # Existing implementation
        pass
    
    # Implement all interface methods
```

**Validation:**
- [ ] Interface fully implemented
- [ ] All abstract methods have implementations
- [ ] Existing functionality preserved
- [ ] Tests still passing

---

#### **Task 3.2: Create Mock Firmware Service**
**Priority:** HIGH  
**Effort:** 3 hours  
**Dependencies:** Task 1.2

**Actions:**
- [ ] Create `infrastructure/external/mock_firmware_service.py`
- [ ] Implement `IFirmwareService` với mock data
- [ ] Add realistic delays và error simulation
- [ ] Document mock behavior

**Code Structure:**
```python
# infrastructure/external/mock_firmware_service.py
from app.domain.interfaces.firmware_service import IFirmwareService

class MockFirmwareService(IFirmwareService):
    """Mock firmware service for testing"""
    
    def __init__(self):
        self.mock_data = self._initialize_mock_data()
    
    async def get_robot_status(self) -> Dict[str, Any]:
        # Return mock robot status
        return {
            "robot_id": "OHT-50-001",
            "status": "idle",
            "position": {"x": 150.5, "y": 200.3},
            "battery_level": 87
        }
    
    # Implement all interface methods với mock data
```

**Validation:**
- [ ] All interface methods mocked
- [ ] Realistic mock data
- [ ] Proper async behavior
- [ ] Useful for testing

---

#### **Task 3.3: Create Redis Cache Service**
**Priority:** HIGH  
**Effort:** 4 hours  
**Dependencies:** Task 1.3

**Actions:**
- [ ] Create `infrastructure/cache/redis_cache_service.py`
- [ ] Implement `ICacheService` interface
- [ ] Add connection pooling
- [ ] Add error handling và fallback
- [ ] Add metrics collection

**Code Structure:**
```python
# infrastructure/cache/redis_cache_service.py
import redis.asyncio as redis
from app.domain.interfaces.cache_service import ICacheService

class RedisCacheService(ICacheService):
    """Redis-based cache implementation"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
        self.stats = {"hits": 0, "misses": 0}
    
    async def initialize(self) -> bool:
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            return True
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self.client.get(key)
            if value:
                self.stats["hits"] += 1
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None
    
    # Implement all interface methods
```

**Validation:**
- [ ] Redis connection working
- [ ] All cache operations functional
- [ ] Stats collection working
- [ ] Error handling robust

---

### **TASK GROUP 4: REDIS TOKEN STORE (Days 9-10)**

#### **Task 4.1: Create Token Store Interface**
**Priority:** CRITICAL  
**Effort:** 2 hours  
**Dependencies:** Task 1.1

**Actions:**
- [ ] Create `domain/interfaces/token_store.py`
- [ ] Define `ITokenStore` interface
- [ ] Methods for token blacklist management

**Code Structure:**
```python
# domain/interfaces/token_store.py
from abc import abstractmethod
from typing import Optional
from .base_service import IBaseService

class ITokenStore(IBaseService):
    """Interface for token storage"""
    
    @abstractmethod
    async def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        pass
    
    @abstractmethod
    async def blacklist_token(self, token: str, expiry: int) -> bool:
        """Add token to blacklist"""
        pass
    
    @abstractmethod
    async def remove_from_blacklist(self, token: str) -> bool:
        """Remove token from blacklist"""
        pass
```

**Validation:**
- [ ] Interface defined correctly
- [ ] Methods cover all token operations
- [ ] Async properly used

---

#### **Task 4.2: Implement Redis Token Store**
**Priority:** CRITICAL  
**Effort:** 4 hours  
**Dependencies:** Task 4.1, Task 3.3

**Actions:**
- [ ] Create `infrastructure/security/redis_token_store.py`
- [ ] Implement `ITokenStore` interface
- [ ] Use Redis với automatic expiration
- [ ] Add audit logging

**Code Structure:**
```python
# infrastructure/security/redis_token_store.py
from app.domain.interfaces.token_store import ITokenStore

class RedisTokenStore(ITokenStore):
    """Redis-based token blacklist"""
    
    def __init__(self, cache_service: ICacheService):
        self.cache = cache_service
        self.prefix = "token:blacklist:"
    
    async def is_token_blacklisted(self, token: str) -> bool:
        key = f"{self.prefix}{token}"
        return await self.cache.get(key) is not None
    
    async def blacklist_token(self, token: str, expiry: int) -> bool:
        key = f"{self.prefix}{token}"
        return await self.cache.set(key, "1", ttl=expiry)
    
    # Implement all methods
```

**Validation:**
- [ ] Token blacklist working
- [ ] Automatic expiration functional
- [ ] Integration với auth system tested

---

#### **Task 4.3: Migrate Auth System to Use Token Store**
**Priority:** CRITICAL  
**Effort:** 3 hours  
**Dependencies:** Task 4.2

**Actions:**
- [ ] Update `api/v1/auth.py` to use `ITokenStore`
- [ ] Remove in-memory token blacklist
- [ ] Update logout endpoint
- [ ] Add token validation middleware

**Code Changes:**
```python
# In api/v1/auth.py
from app.core.dependencies import get_service_container

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    container: ServiceContainer = Depends(get_service_container)
):
    token = credentials.credentials
    token_store = container.token_store()
    
    # Blacklist token
    await token_store.blacklist_token(token, expiry=3600)
    
    return {"success": True, "message": "Logged out successfully"}
```

**Validation:**
- [ ] Login/logout working
- [ ] Token blacklist functional
- [ ] No in-memory storage used
- [ ] Scalable across instances

---

### **TASK GROUP 5: TESTING & VALIDATION (Days 11-12)**

#### **Task 5.1: Unit Tests for Interfaces**
**Priority:** HIGH  
**Effort:** 4 hours  
**Dependencies:** Task Group 1

**Actions:**
- [ ] Create `tests/unit/domain/test_interfaces.py`
- [ ] Test interface contracts
- [ ] Test mock implementations
- [ ] Verify interface compliance

**Test Structure:**
```python
# tests/unit/domain/test_interfaces.py
import pytest
from app.domain.interfaces.firmware_service import IFirmwareService

class TestServiceInterfaces:
    def test_firmware_service_interface_methods(self):
        """Test IFirmwareService has required methods"""
        required_methods = [
            'get_robot_status',
            'send_robot_command',
            'get_telemetry_data',
            'get_connection_status'
        ]
        for method in required_methods:
            assert hasattr(IFirmwareService, method)
    
    # More tests...
```

**Validation:**
- [ ] All interfaces tested
- [ ] Mock implementations verified
- [ ] Coverage > 90% for interfaces

---

#### **Task 5.2: Integration Tests for DI Container**
**Priority:** HIGH  
**Effort:** 4 hours  
**Dependencies:** Task Group 2, Task Group 3

**Actions:**
- [ ] Create `tests/integration/test_di_container.py`
- [ ] Test service resolution
- [ ] Test service lifecycle
- [ ] Test environment-based selection

**Test Structure:**
```python
# tests/integration/test_di_container.py
import pytest
from app.core.dependencies import get_service_container

class TestDIContainer:
    @pytest.mark.asyncio
    async def test_firmware_service_resolution(self):
        """Test firmware service can be resolved"""
        container = get_service_container()
        firmware_service = container.firmware_service()
        
        assert firmware_service is not None
        assert hasattr(firmware_service, 'get_robot_status')
    
    # More tests...
```

**Validation:**
- [ ] Service resolution working
- [ ] No circular dependencies
- [ ] Mock/real switching works

---

#### **Task 5.3: End-to-End Authentication Tests**
**Priority:** CRITICAL  
**Effort:** 3 hours  
**Dependencies:** Task Group 4

**Actions:**
- [ ] Create `tests/e2e/test_auth_flow.py`
- [ ] Test full login/logout flow
- [ ] Test token blacklist
- [ ] Test concurrent token operations

**Test Structure:**
```python
# tests/e2e/test_auth_flow.py
import pytest
from httpx import AsyncClient

class TestAuthFlow:
    @pytest.mark.asyncio
    async def test_login_logout_flow(self, async_client):
        """Test complete auth flow with Redis token store"""
        # Login
        response = await async_client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "password"
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Use token
        response = await async_client.get(
            "/api/v1/robot/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        # Try to use blacklisted token
        response = await async_client.get(
            "/api/v1/robot/status",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
```

**Validation:**
- [ ] Full auth flow working
- [ ] Token blacklist functional
- [ ] No race conditions
- [ ] Scalable across instances

---

## 📊 **SUCCESS METRICS**

### **Architecture Improvements:**
- ✅ **Service Interfaces:** 4+ abstract interfaces created
- ✅ **DI Container:** Fully functional với environment switching
- ✅ **Service Coupling:** Reduced from tight to loose
- ✅ **SOLID Compliance:** Dependency Inversion achieved

### **Security Improvements:**
- ✅ **Token Management:** Redis-based, scalable
- ✅ **In-memory Storage:** Eliminated
- ✅ **Scalability:** Multi-instance ready
- ✅ **Security Score:** 7/10 → 8/10

### **Testing Improvements:**
- ✅ **Unit Tests:** Interface coverage > 90%
- ✅ **Integration Tests:** DI container tested
- ✅ **E2E Tests:** Full auth flow validated
- ✅ **Test Coverage:** ~60% → ~75%

---

## 🚨 **RISK MITIGATION**

### **Potential Risks:**
1. **Breaking Changes:** Service signature changes may break existing code
2. **DI Learning Curve:** Team needs to understand DI patterns
3. **Redis Dependency:** Requires Redis running
4. **Performance Impact:** DI resolution overhead

### **Mitigation Strategies:**
1. **Backward Compatibility:** Keep old services working during transition
2. **Documentation:** Comprehensive DI usage guide
3. **Redis Fallback:** In-memory fallback if Redis unavailable
4. **Performance Testing:** Benchmark DI resolution overhead

---

## 📋 **DAILY CHECKLIST**

### **Day 1-3: Interfaces**
- [ ] Base service interface created
- [ ] Firmware service interface created
- [ ] Cache service interface created
- [ ] Auth service interface created
- [ ] All interfaces documented

### **Day 4-5: DI Container**
- [ ] dependency-injector installed
- [ ] Service container created
- [ ] Providers configured
- [ ] Container integrated với app

### **Day 6-8: Implementations**
- [ ] UnifiedFirmwareService refactored
- [ ] Mock firmware service created
- [ ] Redis cache service implemented
- [ ] All services implement interfaces

### **Day 9-10: Token Store**
- [ ] Token store interface created
- [ ] Redis token store implemented
- [ ] Auth system migrated
- [ ] In-memory storage removed

### **Day 11-12: Testing**
- [ ] Unit tests written
- [ ] Integration tests created
- [ ] E2E tests passing
- [ ] Coverage targets met

---

## 🎯 **COMPLETION CRITERIA**

**Phase 2 is COMPLETE when:**
- ✅ All 4 service interfaces created và documented
- ✅ DI container fully functional
- ✅ At least 3 major services refactored
- ✅ Redis token store implemented và tested
- ✅ All tests passing (unit + integration + e2e)
- ✅ Test coverage > 75%
- ✅ Documentation updated
- ✅ No regression in existing functionality

---

## 📞 **NEXT STEPS AFTER PHASE 2**

1. **Review Phase 2 Deliverables** với team
2. **Performance Testing** để validate DI overhead acceptable
3. **Documentation Review** để ensure clarity
4. **Plan Phase 3:** Database migration và performance optimization

---

**🚀 Ready to implement? Phase 2 sẽ transform service layer từ "coupled mess" thành "clean, testable architecture"!**

**📈 Expected ISO Score after Phase 2:** 40/60 → 48/60
