"""
Integration test for monitoring with resilience patterns
=========================================================
Tests that the monitoring integration works with circuit breaker and health checks.
"""

import pytest
from prometheus_client import CollectorRegistry


def test_circuit_breaker_with_monitoring():
    """Test that circuit breaker works with monitoring integration."""
    from src.core.resilience import CircuitBreaker, CircuitState
    
    # Create circuit breaker - should work even if prometheus_exporter import fails
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout=1,
        name="test_breaker"
    )
    
    # Simulate failures to trigger state change
    @breaker.call
    def failing_func():
        raise ValueError("Test error")
    
    # First failure
    with pytest.raises(ValueError):
        failing_func()
    
    # Second failure - should open circuit
    with pytest.raises(ValueError):
        failing_func()
    
    # Verify circuit is open
    assert breaker.state == CircuitState.OPEN


def test_health_check_with_monitoring():
    """Test that health check works with monitoring integration."""
    from src.core.resilience import HealthCheck
    
    health = HealthCheck()
    
    # Register health checks
    health.register("service_a", lambda: (True, "OK"))
    health.register("service_b", lambda: (False, "Failed"))
    
    # Run health checks - should work even if prometheus_exporter import fails
    results = health.run_all()
    
    # Verify results
    assert results["service_a"].healthy is True
    assert results["service_b"].healthy is False


def test_monitoring_middleware_with_exporter():
    """Test monitoring middleware with actual Prometheus exporter."""
    from src.monitoring.middleware import monitor_performance
    from src.monitoring.prometheus_exporter import PrometheusExporter
    from unittest.mock import patch
    import time
    
    # Use custom registry to avoid conflicts
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    # Mock the prometheus_exporter import
    with patch('src.monitoring.prometheus_exporter.prometheus_exporter', exporter):
        @monitor_performance("test_operation")
        def test_func():
            time.sleep(0.01)
            return "success"
        
        result = test_func()
        assert result == "success"


def test_prometheus_exporter_can_be_started():
    """Test that Prometheus exporter can be instantiated."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    from unittest.mock import patch
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    # Mock the HTTP server start
    with patch('src.monitoring.prometheus_exporter.start_http_server'):
        exporter.start()
    
    # Verify exporter has all required methods
    assert hasattr(exporter, 'record_order')
    assert hasattr(exporter, 'update_pnl')
    assert hasattr(exporter, 'record_circuit_breaker_state')
    assert hasattr(exporter, 'record_health_check')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

