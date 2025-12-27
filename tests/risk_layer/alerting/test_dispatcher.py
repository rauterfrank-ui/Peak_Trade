"""
Tests for Alert Dispatcher
===========================
"""

from unittest.mock import Mock, MagicMock

import pytest

from src.risk_layer.alerting.models import AlertSeverity, AlertEvent
from src.risk_layer.alerting.dispatcher import AlertDispatcher
from src.risk_layer.alerting.channels import ConsoleChannel, FileChannel


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_channel():
    """Create a mock notification channel."""
    channel = Mock()
    channel.enabled = True
    channel.send.return_value = True
    channel.__class__.__name__ = "MockChannel"
    return channel


@pytest.fixture
def failing_channel():
    """Create a mock channel that always fails."""
    channel = Mock()
    channel.enabled = True
    channel.send.return_value = False
    channel.__class__.__name__ = "FailingChannel"
    return channel


@pytest.fixture
def disabled_channel():
    """Create a disabled mock channel."""
    channel = Mock()
    channel.enabled = False
    channel.__class__.__name__ = "DisabledChannel"
    return channel


@pytest.fixture
def info_alert():
    """Create an info-level alert."""
    return AlertEvent(
        source="test",
        severity=AlertSeverity.INFO,
        title="Info Alert",
        body="Informational message",
    )


@pytest.fixture
def warn_alert():
    """Create a warning-level alert."""
    return AlertEvent(
        source="test",
        severity=AlertSeverity.WARN,
        title="Warning Alert",
        body="Warning message",
    )


@pytest.fixture
def critical_alert():
    """Create a critical-level alert."""
    return AlertEvent(
        source="test",
        severity=AlertSeverity.CRITICAL,
        title="Critical Alert",
        body="Critical message",
    )


# =============================================================================
# DISPATCHER TESTS
# =============================================================================


def test_dispatcher_initialization():
    """Test dispatcher initialization."""
    console = ConsoleChannel()
    dispatcher = AlertDispatcher(channels=[console])

    assert len(dispatcher.channels) == 1
    assert "console" in dispatcher.channels


def test_dispatcher_default_routing_matrix():
    """Test default routing matrix."""
    console = ConsoleChannel()
    dispatcher = AlertDispatcher(channels=[console])

    info_routes = dispatcher.get_routing_for_severity(AlertSeverity.INFO)
    warn_routes = dispatcher.get_routing_for_severity(AlertSeverity.WARN)
    critical_routes = dispatcher.get_routing_for_severity(AlertSeverity.CRITICAL)

    assert "console" in info_routes
    assert "file" in info_routes
    assert "console" in warn_routes
    assert "slack" in warn_routes
    assert "console" in critical_routes
    assert "email" in critical_routes


def test_dispatcher_custom_routing_matrix():
    """Test custom routing matrix."""
    console = ConsoleChannel()
    
    custom_routing = {
        AlertSeverity.INFO: ["console"],
        AlertSeverity.WARN: ["console"],
        AlertSeverity.CRITICAL: ["console"],
    }
    
    dispatcher = AlertDispatcher(channels=[console], routing_matrix=custom_routing)
    
    critical_routes = dispatcher.get_routing_for_severity(AlertSeverity.CRITICAL)
    assert critical_routes == ["console"]


def test_dispatcher_dispatch_success(mock_channel, info_alert):
    """Test successful dispatch."""
    # Custom routing to send info alerts to mock channel
    routing = {
        AlertSeverity.INFO: ["mock"],
    }
    dispatcher = AlertDispatcher(channels=[mock_channel], routing_matrix=routing)
    
    results = dispatcher.dispatch(info_alert)
    
    assert "mock" in results
    assert results["mock"] is True
    mock_channel.send.assert_called_once_with(info_alert)


def test_dispatcher_dispatch_to_multiple_channels(info_alert):
    """Test dispatching to multiple channels."""
    channel1 = Mock()
    channel1.enabled = True
    channel1.send.return_value = True
    channel1.__class__.__name__ = "Channel1"
    
    channel2 = Mock()
    channel2.enabled = True
    channel2.send.return_value = True
    channel2.__class__.__name__ = "Channel2"
    
    routing = {
        AlertSeverity.INFO: ["channel1", "channel2"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[channel1, channel2],
        routing_matrix=routing
    )
    
    results = dispatcher.dispatch(info_alert)
    
    assert len(results) == 2
    assert results["channel1"] is True
    assert results["channel2"] is True
    channel1.send.assert_called_once()
    channel2.send.assert_called_once()


def test_dispatcher_disabled_channel_skipped(disabled_channel, info_alert):
    """Test that disabled channels are skipped."""
    routing = {
        AlertSeverity.INFO: ["disabled"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[disabled_channel],
        routing_matrix=routing
    )
    
    results = dispatcher.dispatch(info_alert)
    
    # Disabled channel should not be in results
    assert len(results) == 0
    disabled_channel.send.assert_not_called()


def test_dispatcher_failover_on_failure(failing_channel, critical_alert):
    """Test failover to backup channel when primary fails."""
    # Use console as backup (it's in the failover order)
    console_channel = ConsoleChannel()
    
    routing = {
        AlertSeverity.CRITICAL: ["failing"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[failing_channel, console_channel],
        routing_matrix=routing,
        enable_failover=True
    )
    
    results = dispatcher.dispatch(critical_alert)
    
    # Primary channel should fail
    assert results["failing"] is False
    
    # Failover should succeed to console channel
    assert "console" in results
    assert results["console"] is True
    
    # Both channels should have been attempted
    failing_channel.send.assert_called_once()


def test_dispatcher_no_failover_when_disabled(failing_channel, mock_channel, critical_alert):
    """Test no failover when disabled."""
    routing = {
        AlertSeverity.CRITICAL: ["failing"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[failing_channel, mock_channel],
        routing_matrix=routing,
        enable_failover=False
    )
    
    results = dispatcher.dispatch(critical_alert)
    
    # Only primary channel should be tried
    assert results["failing"] is False
    assert "mock" not in results
    
    failing_channel.send.assert_called_once()
    mock_channel.send.assert_not_called()


def test_dispatcher_get_enabled_channels():
    """Test getting enabled channels."""
    console = ConsoleChannel()
    file_channel = FileChannel()  # Disabled by default
    
    dispatcher = AlertDispatcher(channels=[console, file_channel])
    
    enabled = dispatcher.get_enabled_channels()
    
    assert "console" in enabled
    assert "file" not in enabled


def test_dispatcher_async_dispatch(mock_channel, warn_alert):
    """Test async dispatch."""
    # Custom routing to send warn alerts to mock channel
    routing = {
        AlertSeverity.WARN: ["mock"],
    }
    dispatcher = AlertDispatcher(channels=[mock_channel], routing_matrix=routing)
    
    results = dispatcher.dispatch_async(warn_alert)
    
    assert "mock" in results
    assert results["mock"] is True
    mock_channel.send.assert_called_once()


def test_dispatcher_async_dispatch_multiple_channels(warn_alert):
    """Test async dispatch to multiple channels."""
    channel1 = Mock()
    channel1.enabled = True
    channel1.send.return_value = True
    channel1.__class__.__name__ = "Channel1"
    
    channel2 = Mock()
    channel2.enabled = True
    channel2.send.return_value = True
    channel2.__class__.__name__ = "Channel2"
    
    channel3 = Mock()
    channel3.enabled = True
    channel3.send.return_value = True
    channel3.__class__.__name__ = "Channel3"
    
    routing = {
        AlertSeverity.WARN: ["channel1", "channel2", "channel3"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[channel1, channel2, channel3],
        routing_matrix=routing
    )
    
    results = dispatcher.dispatch_async(warn_alert)
    
    assert len(results) == 3
    assert all(results.values())
    
    # All channels should be called
    channel1.send.assert_called_once()
    channel2.send.assert_called_once()
    channel3.send.assert_called_once()


def test_dispatcher_exception_handling(critical_alert):
    """Test dispatcher handles exceptions gracefully."""
    bad_channel = Mock()
    bad_channel.enabled = True
    bad_channel.send.side_effect = Exception("Channel error")
    bad_channel.__class__.__name__ = "BadChannel"
    
    routing = {
        AlertSeverity.CRITICAL: ["bad"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[bad_channel],
        routing_matrix=routing
    )
    
    results = dispatcher.dispatch(critical_alert)
    
    # Should handle exception and return failure
    assert results["bad"] is False


def test_dispatcher_severity_based_routing():
    """Test that different severities route to different channels."""
    console = Mock()
    console.enabled = True
    console.send.return_value = True
    console.__class__.__name__ = "ConsoleChannel"
    
    email = Mock()
    email.enabled = True
    email.send.return_value = True
    email.__class__.__name__ = "EmailChannel"
    
    routing = {
        AlertSeverity.INFO: ["console"],
        AlertSeverity.WARN: ["console"],
        AlertSeverity.CRITICAL: ["console", "email"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[console, email],
        routing_matrix=routing
    )
    
    # Info alert: only console
    info_alert = AlertEvent(
        source="test",
        severity=AlertSeverity.INFO,
        title="Info",
        body="Info message",
    )
    results = dispatcher.dispatch(info_alert)
    assert "console" in results
    assert "email" not in results
    
    # Critical alert: both console and email
    critical_alert = AlertEvent(
        source="test",
        severity=AlertSeverity.CRITICAL,
        title="Critical",
        body="Critical message",
    )
    results = dispatcher.dispatch(critical_alert)
    assert "console" in results
    assert "email" in results


def test_dispatcher_failover_order():
    """Test failover follows predefined order."""
    # Create channels
    failing = Mock()
    failing.enabled = True
    failing.send.return_value = False
    failing.__class__.__name__ = "FailingChannel"
    
    console = Mock()
    console.enabled = True
    console.send.return_value = True
    console.__class__.__name__ = "ConsoleChannel"
    
    file_ch = Mock()
    file_ch.enabled = True
    file_ch.send.return_value = False
    file_ch.__class__.__name__ = "FileChannel"
    
    routing = {
        AlertSeverity.CRITICAL: ["failing"],
    }
    
    dispatcher = AlertDispatcher(
        channels=[failing, console, file_ch],
        routing_matrix=routing,
        enable_failover=True
    )
    
    critical_alert = AlertEvent(
        source="test",
        severity=AlertSeverity.CRITICAL,
        title="Critical",
        body="Critical message",
    )
    
    results = dispatcher.dispatch(critical_alert)
    
    # Primary should fail
    assert results["failing"] is False
    
    # Console should be tried first in failover (before file in fallback order)
    assert "console" in results
    assert results["console"] is True
    
    # File should not be tried since console succeeded
    assert "file" not in results
