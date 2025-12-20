"""
Tests for Prometheus Exporter
==============================
Tests the Prometheus metrics exporter functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from prometheus_client import CollectorRegistry


def test_prometheus_exporter_initialization():
    """Test PrometheusExporter initialization."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    # Use custom registry to avoid conflicts
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    assert exporter.port == 9999
    assert exporter.cpu_usage is not None
    assert exporter.memory_usage is not None
    assert exporter.orders_total is not None
    assert exporter.circuit_breaker_state is not None


def test_record_order():
    """Test recording order metrics."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    # Should not raise exception
    exporter.record_order("filled", "BTC/USD")
    exporter.record_order("canceled", "ETH/USD")


def test_update_pnl():
    """Test updating P&L metrics."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    # Should not raise exception
    exporter.update_pnl("momentum", 1000.50)
    exporter.update_pnl("mean_reversion", -250.25)


def test_record_circuit_breaker_state():
    """Test recording circuit breaker state."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    # Test all states
    exporter.record_circuit_breaker_state("api_breaker", 0)  # CLOSED
    exporter.record_circuit_breaker_state("api_breaker", 1)  # HALF_OPEN
    exporter.record_circuit_breaker_state("api_breaker", 2)  # OPEN


def test_record_health_check():
    """Test recording health check results."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    exporter.record_health_check("database", True)
    exporter.record_health_check("api", False)


def test_record_request():
    """Test recording request duration."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    exporter.record_request("api_call", "success", 0.5)
    exporter.record_request("api_call", "error", 1.0)


def test_record_cache_operations():
    """Test recording cache operations."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    exporter.record_cache_hit("L1")
    exporter.record_cache_miss("L1")
    exporter.record_cache_hit("L2")


def test_record_api_call():
    """Test recording API calls."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    exporter.record_api_call("kraken", "success")
    exporter.record_api_call("binance", "error")


def test_update_system_metrics():
    """Test updating system metrics."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    exporter = PrometheusExporter(port=9999, registry=registry)
    
    exporter.update_system_metrics(cpu_percent=45.5, memory_mb=1024.0)


def test_start_exporter():
    """Test starting the Prometheus exporter."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    with patch('src.monitoring.prometheus_exporter.start_http_server') as mock_start:
        exporter = PrometheusExporter(port=9999, registry=registry)
        exporter.start()
        mock_start.assert_called_once_with(9999)


def test_start_exporter_error():
    """Test error handling when starting exporter."""
    from src.monitoring.prometheus_exporter import PrometheusExporter
    
    registry = CollectorRegistry()
    with patch('src.monitoring.prometheus_exporter.start_http_server') as mock_start:
        mock_start.side_effect = Exception("Port already in use")
        exporter = PrometheusExporter(port=9999, registry=registry)
        
        with pytest.raises(Exception, match="Port already in use"):
            exporter.start()


