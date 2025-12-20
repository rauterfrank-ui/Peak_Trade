"""
Tests for Monitoring Middleware
================================
Tests the performance monitoring decorators and middleware.
"""

import pytest
import time
from unittest.mock import patch, MagicMock, Mock


def test_monitor_performance_decorator_success():
    """Test monitor_performance decorator with successful operation."""
    from src.monitoring.middleware import monitor_performance
    
    mock_exporter = Mock()
    with patch('src.monitoring.prometheus_exporter.prometheus_exporter', mock_exporter):
        @monitor_performance("test_operation")
        def test_func():
            time.sleep(0.01)
            return "success"
        
        result = test_func()
        
        assert result == "success"
        # Verify prometheus_exporter.record_request was called
        assert mock_exporter.record_request.called


def test_monitor_performance_decorator_error():
    """Test monitor_performance decorator with error."""
    from src.monitoring.middleware import monitor_performance
    
    mock_exporter = Mock()
    with patch('src.monitoring.prometheus_exporter.prometheus_exporter', mock_exporter):
        @monitor_performance("test_operation")
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            test_func()
        
        # Verify prometheus_exporter.record_request was called with error method
        assert mock_exporter.record_request.called
        call_args = mock_exporter.record_request.call_args
        assert call_args[1]['method'] == "error"


def test_monitor_performance_without_prometheus():
    """Test monitor_performance when Prometheus is not available."""
    from src.monitoring.middleware import monitor_performance
    
    # The function handles ImportError internally, so it should work
    @monitor_performance("test_operation")
    def test_func():
        return "success"
    
    # Should still work without prometheus
    result = test_func()
    assert result == "success"


def test_monitor_performance_timing():
    """Test that monitor_performance measures execution time."""
    from src.monitoring.middleware import monitor_performance
    
    mock_exporter = Mock()
    with patch('src.monitoring.prometheus_exporter.prometheus_exporter', mock_exporter):
        @monitor_performance("test_operation")
        def test_func():
            time.sleep(0.05)
            return "success"
        
        test_func()
        
        # Verify duration_seconds is reasonable
        call_args = mock_exporter.record_request.call_args
        duration = call_args[1]['duration_seconds']
        assert duration >= 0.05
        assert duration < 0.2  # Should complete reasonably fast


def test_monitor_performance_with_args():
    """Test monitor_performance decorator with function arguments."""
    from src.monitoring.middleware import monitor_performance
    
    mock_exporter = Mock()
    with patch('src.monitoring.prometheus_exporter.prometheus_exporter', mock_exporter):
        @monitor_performance("test_operation")
        def test_func(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        result = test_func("x", "y", c="z")
        
        assert result == "x-y-z"
        assert mock_exporter.record_request.called


def test_monitor_performance_preserves_function_metadata():
    """Test that decorator preserves function metadata."""
    from src.monitoring.middleware import monitor_performance
    
    @monitor_performance("test_operation")
    def test_func():
        """Test function docstring."""
        return "success"
    
    assert test_func.__name__ == "test_func"
    assert test_func.__doc__ == "Test function docstring."

