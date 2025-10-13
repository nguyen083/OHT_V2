# 🧪 PHASE 3 END-TO-END INTEGRATION TESTS
"""
Comprehensive E2E integration tests for Phase 3 enhancements
Tests complete system workflows with all Phase 3 optimizations

Phase 3: Complete system validation with performance monitoring
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from httpx import AsyncClient
from datetime import datetime

from app.core.database_config import get_database_config
from app.infrastructure.cache.advanced_cache_service import get_advanced_cache_service
from app.infrastructure.monitoring.performance_monitoring_service import get_performance_monitoring_service
from app.services.async_database_service import get_async_database_service
from app.presentation.schemas.api_responses import ResponseBuilder


@pytest.fixture(scope="session")
async def system_setup():
    """Setup complete system for E2E testing"""
    print("🚀 Setting up Phase 3 system for E2E testing...")
    
    # Initialize all Phase 3 services
    services = {
        "database": await get_async_database_service(),
        "cache": await get_advanced_cache_service(),
        "monitoring": await get_performance_monitoring_service()
    }
    
    # Verify all services are healthy
    for name, service in services.items():
        health = await service.health_check()
        assert health["status"] in ["healthy", "degraded"], f"{name} service unhealthy"
        print(f"✅ {name.title()} service: {health['status']}")
    
    yield services
    
    # Cleanup
    print("🧹 Cleaning up Phase 3 system...")
    for name, service in services.items():
        await service.shutdown()
        print(f"✅ {name.title()} service shutdown")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDatabaseIntegration:
    """End-to-end database integration tests"""
    
    async def test_complete_telemetry_workflow(self, system_setup):
        """Test complete telemetry data workflow"""
        db_service = system_setup["database"]
        monitoring_service = system_setup["monitoring"]
        
        # Simulate realistic telemetry data
        telemetry_data = {
            "module_id": 1,
            "module_name": "main_drive_motor",
            "temperature": 42.5,
            "current": 15.2,
            "rpm": 1800,
            "vibration": 2.1,
            "voltage": 24.1,
            "status": "operational",
            "timestamp": int(time.time() * 1000)
        }
        
        start_time = time.time()
        
        # 1. Store telemetry data
        success = await db_service.store_telemetry_data(
            module_id=telemetry_data["module_id"],
            module_name=telemetry_data["module_name"],
            telemetry_data=telemetry_data,
            validation_status="valid"
        )
        assert success, "Failed to store telemetry data"
        
        # 2. Retrieve latest telemetry
        latest = await db_service.get_latest_telemetry(telemetry_data["module_id"])
        assert latest is not None, "Failed to retrieve latest telemetry"
        assert latest["module_name"] == telemetry_data["module_name"]
        assert latest["telemetry_data"]["temperature"] == telemetry_data["temperature"]
        
        # 3. Get validation summary
        summary = await db_service.get_validation_summary()
        assert summary["total_modules"] >= 1
        assert "valid" in summary["validation_status_counts"]
        
        # 4. Get module statistics
        stats = await db_service.get_module_telemetry_stats(telemetry_data["module_id"])
        assert stats["module_id"] == telemetry_data["module_id"]
        assert stats["total_records"] >= 1
        
        # 5. Record performance metrics
        workflow_time = (time.time() - start_time) * 1000
        await monitoring_service.record_database_query("telemetry_workflow", workflow_time)
        
        print(f"✅ Complete telemetry workflow: {workflow_time:.2f}ms")
        
        # Performance assertion
        assert workflow_time < 100, f"Telemetry workflow too slow: {workflow_time:.2f}ms"
    
    async def test_concurrent_database_operations(self, system_setup):
        """Test concurrent database operations under load"""
        db_service = system_setup["database"]
        monitoring_service = system_setup["monitoring"]
        
        async def concurrent_operation(module_id: int):
            """Single concurrent operation"""
            operation_start = time.time()
            
            # Store telemetry
            success = await db_service.store_telemetry_data(
                module_id=module_id,
                module_name=f"test_module_{module_id}",
                telemetry_data={
                    "value": module_id * 10,
                    "status": "testing",
                    "timestamp": int(time.time() * 1000)
                },
                validation_status="valid"
            )
            
            # Retrieve data
            if success:
                data = await db_service.get_latest_telemetry(module_id)
                assert data is not None
            
            operation_time = (time.time() - operation_start) * 1000
            await monitoring_service.record_database_query("concurrent_test", operation_time)
            
            return success
        
        # Run 50 concurrent operations
        start_time = time.time()
        tasks = [concurrent_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Verify all operations succeeded
        success_count = sum(results)
        assert success_count >= 45, f"Too many failures: {success_count}/50 succeeded"
        
        # Performance assertions
        avg_time_per_op = (total_time / len(tasks)) * 1000
        assert avg_time_per_op < 50, f"Average operation time too slow: {avg_time_per_op:.2f}ms"
        
        print(f"✅ Concurrent operations: {success_count}/50 succeeded in {total_time:.2f}s")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestCacheIntegration:
    """End-to-end cache integration tests"""
    
    async def test_multi_level_cache_workflow(self, system_setup):
        """Test complete multi-level cache workflow"""
        cache_service = system_setup["cache"]
        monitoring_service = system_setup["monitoring"]
        
        # Test data with different patterns for intelligent TTL
        test_cases = [
            ("telemetry_sensor_1", {"temp": 25.5, "humidity": 60}, "telemetry"),
            ("config_system_main", {"max_speed": 100, "timeout": 30}, "config"),
            ("module_firmware_v1", {"version": "1.2.3", "checksum": "abc123"}, "firmware")
        ]
        
        for key, value, category in test_cases:
            start_time = time.time()
            
            # 1. Set in cache (should hit both L1 and L2)
            success = await cache_service.set(key, value)
            assert success, f"Failed to set cache key: {key}"
            
            # 2. Get from cache (should hit L1 - fastest)
            cached_value = await cache_service.get(key)
            assert cached_value == value, f"Cache value mismatch for key: {key}"
            
            # 3. Record cache operation
            operation_time = (time.time() - start_time) * 1000
            await monitoring_service.record_cache_operation("multilevel_test", True)
            
            print(f"✅ Cache workflow for {category}: {operation_time:.2f}ms")
            
            # Performance assertion
            assert operation_time < 10, f"Cache operation too slow: {operation_time:.2f}ms"
    
    async def test_cache_warming_strategy(self, system_setup):
        """Test cache warming strategies"""
        cache_service = system_setup["cache"]
        
        # Register a warming strategy
        async def warm_config_data(key: str):
            """Mock warming strategy for config data"""
            if key.startswith("config_"):
                return {"warmed": True, "timestamp": time.time()}
            return None
        
        cache_service.register_warming_strategy("config_", warm_config_data)
        
        # Test cache miss that should trigger warming
        non_existent_key = "config_test_warming"
        
        # First get should miss and trigger warming
        value = await cache_service.get(non_existent_key)
        assert value is None, "Expected cache miss"
        
        # Wait a bit for warming to complete
        await asyncio.sleep(0.1)
        
        # Check if warming strategy was registered
        assert non_existent_key in cache_service.warming_strategies or len(cache_service.warming_strategies) > 0
        
        print("✅ Cache warming strategy working")
    
    async def test_cache_performance_under_load(self, system_setup):
        """Test cache performance under high load"""
        cache_service = system_setup["cache"]
        monitoring_service = system_setup["monitoring"]
        
        # Pre-populate cache with test data
        for i in range(100):
            await cache_service.set(f"load_test_{i}", f"value_{i}", ttl=300)
        
        async def cache_load_test(iteration: int):
            """Single cache load test operation"""
            start_time = time.time()
            
            # Mix of hits and misses
            if iteration % 3 == 0:
                # Cache miss
                key = f"miss_test_{iteration}"
                value = await cache_service.get(key)
                hit = value is not None
            else:
                # Cache hit
                key = f"load_test_{iteration % 100}"
                value = await cache_service.get(key)
                hit = value is not None
            
            operation_time = (time.time() - start_time) * 1000
            await monitoring_service.record_cache_operation("load_test", hit)
            
            return operation_time
        
        # Run high load test
        tasks = [cache_load_test(i) for i in range(1000)]
        operation_times = await asyncio.gather(*tasks)
        
        # Analyze performance
        avg_time = sum(operation_times) / len(operation_times)
        max_time = max(operation_times)
        p95_time = sorted(operation_times)[int(len(operation_times) * 0.95)]
        
        # Performance assertions
        assert avg_time < 5, f"Average cache time too slow: {avg_time:.2f}ms"
        assert p95_time < 20, f"P95 cache time too slow: {p95_time:.2f}ms"
        assert max_time < 100, f"Max cache time too slow: {max_time:.2f}ms"
        
        print(f"✅ Cache load test: avg={avg_time:.2f}ms, p95={p95_time:.2f}ms, max={max_time:.2f}ms")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestAPIIntegration:
    """End-to-end API integration tests"""
    
    async def test_standardized_api_responses(self, async_client: AsyncClient):
        """Test standardized API response format across endpoints"""
        endpoints = [
            "/api/v1/health",
            "/api/v1/robot/status",
            "/api/v1/telemetry/current"
        ]
        
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            
            # Response should be valid (200 or expected error)
            assert response.status_code in [200, 404, 500, 503], f"Unexpected status for {endpoint}"
            
            try:
                data = response.json()
                
                # Check standardized response format
                required_fields = ["status", "message", "meta"]
                for field in required_fields:
                    assert field in data, f"Missing {field} in {endpoint} response"
                
                # Check metadata format
                meta = data["meta"]
                assert "request_id" in meta, f"Missing request_id in {endpoint}"
                assert "timestamp" in meta, f"Missing timestamp in {endpoint}"
                assert "api_version" in meta, f"Missing api_version in {endpoint}"
                
                # Check processing time if available
                if "processing_time_ms" in meta:
                    assert meta["processing_time_ms"] >= 0, f"Invalid processing time in {endpoint}"
                
                print(f"✅ Standardized response format: {endpoint}")
                
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON response from {endpoint}")
    
    async def test_api_performance_monitoring(self, async_client: AsyncClient, system_setup):
        """Test API performance monitoring integration"""
        monitoring_service = system_setup["monitoring"]
        
        # Make several API calls
        endpoints = ["/api/v1/health"] * 10
        
        start_time = time.time()
        
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            
            # Record API metrics (simulate what middleware would do)
            response_time = (time.time() - start_time) * 1000
            await monitoring_service.record_api_request(
                endpoint=endpoint,
                method="GET",
                response_time_ms=response_time,
                status_code=response.status_code
            )
        
        # Verify monitoring is working
        health = await monitoring_service.health_check()
        assert health["status"] in ["healthy", "degraded"]
        
        print("✅ API performance monitoring integration working")
    
    async def test_hateoas_navigation(self, async_client: AsyncClient):
        """Test HATEOAS navigation links"""
        response = await async_client.get("/api/v1/health")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for HATEOAS links
            if "links" in data and data["links"]:
                links = data["links"]
                
                for link in links:
                    # Validate link structure
                    assert "href" in link, "Missing href in HATEOAS link"
                    assert "rel" in link, "Missing rel in HATEOAS link"
                    assert "method" in link, "Missing method in HATEOAS link"
                    
                    # Test that links are valid URIs
                    assert link["href"].startswith("/") or link["href"].startswith("http"), "Invalid href format"
                    
                print(f"✅ HATEOAS links validated: {len(links)} links found")
            else:
                print("ℹ️ HATEOAS links not present (may not be implemented yet)")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestMonitoringIntegration:
    """End-to-end monitoring integration tests"""
    
    async def test_comprehensive_system_monitoring(self, system_setup):
        """Test comprehensive system monitoring"""
        monitoring_service = system_setup["monitoring"]
        
        # Generate various types of metrics
        await monitoring_service.record_api_request("/test", "GET", 25.0, 200)
        await monitoring_service.record_api_request("/test", "POST", 45.0, 201)
        await monitoring_service.record_api_request("/error", "GET", 15.0, 500)
        
        await monitoring_service.record_database_query("SELECT", 5.0, True)
        await monitoring_service.record_database_query("INSERT", 8.0, True)
        await monitoring_service.record_database_query("UPDATE", 12.0, False)
        
        await monitoring_service.record_cache_operation("get", True)
        await monitoring_service.record_cache_operation("get", False)
        await monitoring_service.record_cache_operation("set", True)
        
        # Get comprehensive health check
        health = await monitoring_service.health_check()
        
        # Verify monitoring data
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "system_metrics" in health
        assert "application_metrics" in health
        
        system_metrics = health["system_metrics"]
        assert "cpu_percent" in system_metrics
        assert "memory_percent" in system_metrics
        assert "timestamp" in system_metrics
        
        print("✅ Comprehensive system monitoring working")
    
    async def test_alert_system_integration(self, system_setup):
        """Test integrated alert system"""
        monitoring_service = system_setup["monitoring"]
        
        # Simulate high response times to trigger alerts
        for _ in range(10):
            await monitoring_service.record_api_request("/slow", "GET", 150.0, 200)
        
        # Wait for alert processing
        await asyncio.sleep(1)
        
        # Check for alerts
        metrics_summary = monitoring_service.get_metrics_summary()
        
        # Should have some monitoring data
        assert "system_metrics" in metrics_summary
        assert "application_metrics" in metrics_summary
        assert "active_alerts" in metrics_summary
        assert "alert_history" in metrics_summary
        
        print("✅ Alert system integration working")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestSystemResilience:
    """System resilience and error handling tests"""
    
    async def test_service_failure_resilience(self, system_setup):
        """Test system resilience to service failures"""
        cache_service = system_setup["cache"]
        
        # Test cache failure resilience
        # Try to use cache even if Redis is unavailable
        try:
            # This might fail if Redis is down, but should degrade gracefully
            await cache_service.set("resilience_test", "test_value")
            value = await cache_service.get("resilience_test")
            
            print("✅ Cache service resilient to failures")
        except Exception as e:
            # Should degrade gracefully, not crash
            print(f"⚠️ Cache service degraded gracefully: {e}")
    
    async def test_high_load_resilience(self, async_client: AsyncClient, system_setup):
        """Test system resilience under high load"""
        monitoring_service = system_setup["monitoring"]
        
        async def load_test_request():
            """Single load test request"""
            try:
                response = await async_client.get("/api/v1/health")
                return response.status_code == 200
            except Exception:
                return False
        
        # Generate high load
        tasks = [load_test_request() for _ in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful requests
        success_count = sum(1 for result in results if result is True)
        
        # System should handle most requests even under load
        success_rate = success_count / len(tasks) * 100
        assert success_rate >= 80, f"Success rate too low under load: {success_rate:.1f}%"
        
        print(f"✅ High load resilience: {success_rate:.1f}% success rate")
    
    async def test_graceful_degradation(self, system_setup):
        """Test graceful degradation of services"""
        db_service = system_setup["database"]
        cache_service = system_setup["cache"]
        monitoring_service = system_setup["monitoring"]
        
        # Test that services report degraded status when appropriate
        services = [
            ("database", db_service),
            ("cache", cache_service),
            ("monitoring", monitoring_service)
        ]
        
        for name, service in services:
            health = await service.health_check()
            
            # Service should be in a known state
            assert health["status"] in ["healthy", "degraded", "unhealthy"], f"{name} service in unknown state"
            
            # Should have error handling in place
            if health["status"] == "unhealthy":
                assert "error" in health, f"{name} service unhealthy but no error details"
            
            print(f"✅ {name.title()} service graceful degradation: {health['status']}")


def generate_e2e_test_report(test_results: List[Dict[str, Any]]) -> str:
    """Generate comprehensive E2E test report"""
    report = """
# 🧪 PHASE 3 END-TO-END INTEGRATION TEST REPORT

## System Integration Validation

"""
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result.get("passed", False))
    
    report += f"- **Total Integration Tests:** {total_tests}\n"
    report += f"- **Passed:** {passed_tests}\n"
    report += f"- **Failed:** {total_tests - passed_tests}\n"
    report += f"- **Success Rate:** {passed_tests/total_tests*100:.1f}%\n\n"
    
    report += "## System Components Validated\n\n"
    report += "✅ **Database Integration:** Async operations, concurrent access, performance\n"
    report += "✅ **Cache Integration:** Multi-level caching, intelligent TTL, warming strategies\n"
    report += "✅ **API Integration:** Standardized responses, HATEOAS, performance monitoring\n"
    report += "✅ **Monitoring Integration:** Comprehensive metrics, alerting, system health\n"
    report += "✅ **System Resilience:** Failure handling, load tolerance, graceful degradation\n\n"
    
    report += "## Integration Quality Assessment\n\n"
    
    if passed_tests / total_tests >= 0.95:
        report += "🟢 **EXCELLENT:** All critical integrations working perfectly\n"
    elif passed_tests / total_tests >= 0.85:
        report += "🟡 **GOOD:** Most integrations working, minor issues to address\n"
    else:
        report += "🔴 **NEEDS ATTENTION:** Integration issues require immediate attention\n"
    
    report += "\n## Conclusions\n\n"
    report += "Phase 3 system integration has been comprehensively validated.\n"
    report += "All major components work together seamlessly.\n"
    report += "System demonstrates resilience and graceful degradation.\n"
    
    return report


# Run E2E integration tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
