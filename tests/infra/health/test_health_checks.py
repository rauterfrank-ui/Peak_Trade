"""
Tests for Health Check System
===============================

Tests for the health check components.
"""

import pytest
from datetime import datetime

from src.infra.health.checks.base_check import (
    BaseHealthCheck,
    CheckResult,
    HealthStatus,
)
from src.infra.health.checks.backtest_check import BacktestHealthCheck
from src.infra.health.checks.exchange_check import ExchangeHealthCheck
from src.infra.health.checks.portfolio_check import PortfolioHealthCheck
from src.infra.health.checks.risk_check import RiskHealthCheck
from src.infra.health.checks.live_check import LiveHealthCheck
from src.infra.health.health_checker import (
    HealthChecker,
    HealthCheckerResult,
)


class TestHealthStatus:
    """Test HealthStatus enum."""
    
    def test_health_status_values(self):
        """Test HealthStatus has correct values."""
        assert HealthStatus.GREEN.value == "GREEN"
        assert HealthStatus.YELLOW.value == "YELLOW"
        assert HealthStatus.RED.value == "RED"


class TestCheckResult:
    """Test CheckResult dataclass."""
    
    def test_create_check_result(self):
        """Test creating a CheckResult."""
        result = CheckResult(
            component_name="Test Component",
            status=HealthStatus.GREEN,
            message="All good",
            timestamp=datetime.now(),
            details={"foo": "bar"},
            response_time_ms=123.45,
        )
        
        assert result.component_name == "Test Component"
        assert result.status == HealthStatus.GREEN
        assert result.message == "All good"
        assert result.details == {"foo": "bar"}
        assert result.response_time_ms == 123.45
    
    def test_check_result_to_dict(self):
        """Test converting CheckResult to dict."""
        timestamp = datetime.now()
        result = CheckResult(
            component_name="Test",
            status=HealthStatus.GREEN,
            message="OK",
            timestamp=timestamp,
        )
        
        d = result.to_dict()
        assert d["component_name"] == "Test"
        assert d["status"] == "GREEN"
        assert d["message"] == "OK"
        assert d["timestamp"] == timestamp.isoformat()
        assert d["details"] == {}
        assert d["response_time_ms"] is None


class TestBaseHealthCheck:
    """Test BaseHealthCheck abstract class."""
    
    def test_create_result_helper(self):
        """Test _create_result helper method."""
        
        class DummyCheck(BaseHealthCheck):
            def check(self) -> CheckResult:
                return self._create_result(
                    status=HealthStatus.GREEN,
                    message="Test",
                )
        
        checker = DummyCheck("Test Component")
        result = checker.check()
        
        assert result.component_name == "Test Component"
        assert result.status == HealthStatus.GREEN
        assert result.message == "Test"


class TestBacktestHealthCheck:
    """Test BacktestHealthCheck."""
    
    def test_backtest_health_check(self):
        """Test backtest health check runs successfully."""
        checker = BacktestHealthCheck()
        result = checker.check()
        
        assert result.component_name == "Backtest Engine"
        assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW]
        assert result.message is not None
        assert result.timestamp is not None


class TestExchangeHealthCheck:
    """Test ExchangeHealthCheck."""
    
    def test_exchange_health_check(self):
        """Test exchange health check runs successfully."""
        checker = ExchangeHealthCheck()
        result = checker.check()
        
        assert result.component_name == "Exchange Connectivity"
        # Can be GREEN or YELLOW depending on module availability
        assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW]
        assert result.message is not None


class TestPortfolioHealthCheck:
    """Test PortfolioHealthCheck."""
    
    def test_portfolio_health_check(self):
        """Test portfolio health check runs successfully."""
        checker = PortfolioHealthCheck()
        result = checker.check()
        
        assert result.component_name == "Portfolio Management"
        assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW]
        assert result.message is not None


class TestRiskHealthCheck:
    """Test RiskHealthCheck."""
    
    def test_risk_health_check(self):
        """Test risk health check runs successfully."""
        checker = RiskHealthCheck()
        result = checker.check()
        
        assert result.component_name == "Risk Management"
        assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW]
        assert result.message is not None


class TestLiveHealthCheck:
    """Test LiveHealthCheck."""
    
    def test_live_health_check(self):
        """Test live health check runs successfully."""
        checker = LiveHealthCheck()
        result = checker.check()
        
        assert result.component_name == "Live Trading"
        # Should be GREEN or YELLOW, not RED
        assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW]
        assert result.message is not None


class TestHealthChecker:
    """Test HealthChecker."""
    
    def test_health_checker_initialization(self):
        """Test HealthChecker initializes with all checks."""
        checker = HealthChecker()
        assert len(checker.checks) == 5  # 5 component checks
    
    def test_check_all(self):
        """Test running all health checks."""
        checker = HealthChecker()
        result = checker.check_all()
        
        assert isinstance(result, HealthCheckerResult)
        assert len(result.results) == 5
        assert result.overall_status in [
            HealthStatus.GREEN,
            HealthStatus.YELLOW,
            HealthStatus.RED,
        ]
    
    def test_check_component(self):
        """Test checking a specific component."""
        checker = HealthChecker()
        result = checker.check_component("Backtest Engine")
        
        assert result.component_name == "Backtest Engine"
        assert result.status is not None
    
    def test_check_component_not_found(self):
        """Test checking non-existent component raises ValueError."""
        checker = HealthChecker()
        
        with pytest.raises(ValueError, match="Component.*not found"):
            checker.check_component("NonExistent Component")


class TestHealthCheckerResult:
    """Test HealthCheckerResult."""
    
    def test_overall_status_all_green(self):
        """Test overall status when all components are green."""
        results = [
            CheckResult(
                component_name=f"Component {i}",
                status=HealthStatus.GREEN,
                message="OK",
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]
        
        result = HealthCheckerResult(results)
        assert result.overall_status == HealthStatus.GREEN
    
    def test_overall_status_with_yellow(self):
        """Test overall status with yellow components."""
        results = [
            CheckResult(
                component_name="Component 1",
                status=HealthStatus.GREEN,
                message="OK",
                timestamp=datetime.now(),
            ),
            CheckResult(
                component_name="Component 2",
                status=HealthStatus.YELLOW,
                message="Warning",
                timestamp=datetime.now(),
            ),
        ]
        
        result = HealthCheckerResult(results)
        assert result.overall_status == HealthStatus.YELLOW
    
    def test_overall_status_with_red(self):
        """Test overall status with red components."""
        results = [
            CheckResult(
                component_name="Component 1",
                status=HealthStatus.GREEN,
                message="OK",
                timestamp=datetime.now(),
            ),
            CheckResult(
                component_name="Component 2",
                status=HealthStatus.RED,
                message="Error",
                timestamp=datetime.now(),
            ),
        ]
        
        result = HealthCheckerResult(results)
        assert result.overall_status == HealthStatus.RED
    
    def test_status_counts(self):
        """Test counting statuses."""
        results = [
            CheckResult("C1", HealthStatus.GREEN, "OK", datetime.now()),
            CheckResult("C2", HealthStatus.GREEN, "OK", datetime.now()),
            CheckResult("C3", HealthStatus.YELLOW, "Warn", datetime.now()),
            CheckResult("C4", HealthStatus.RED, "Error", datetime.now()),
        ]
        
        result = HealthCheckerResult(results)
        assert result.green_count == 2
        assert result.yellow_count == 1
        assert result.red_count == 1
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        results = [
            CheckResult("C1", HealthStatus.GREEN, "OK", datetime.now()),
        ]
        
        result = HealthCheckerResult(results)
        d = result.to_dict()
        
        assert "timestamp" in d
        assert "overall_status" in d
        assert "summary" in d
        assert "components" in d
        assert d["summary"]["total_components"] == 1
        assert d["summary"]["green"] == 1
    
    def test_to_json(self):
        """Test converting result to JSON."""
        results = [
            CheckResult("C1", HealthStatus.GREEN, "OK", datetime.now()),
        ]
        
        result = HealthCheckerResult(results)
        json_str = result.to_json()
        
        assert isinstance(json_str, str)
        assert "GREEN" in json_str
        
        # Verify it's valid JSON
        import json
        data = json.loads(json_str)
        assert data["overall_status"] == "GREEN"
