"""
Tests for Health Check System
"""

import pytest
from src.infra.health import HealthChecker, HealthStatus
from src.infra.health.checks import BacktestHealthCheck, ExchangeHealthCheck


@pytest.mark.asyncio
async def test_health_checker_initialization():
    """Test HealthChecker initialization"""
    checker = HealthChecker()
    assert len(checker.checks) == 5
    assert "backtest" in checker.checks
    assert "exchange" in checker.checks


@pytest.mark.asyncio
async def test_run_all_checks():
    """Test running all health checks"""
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    assert len(results) == 5
    assert "backtest" in results
    assert "exchange" in results
    assert "portfolio" in results
    assert "risk" in results
    assert "live" in results
    
    # All results should have required attributes
    for name, result in results.items():
        assert result.name == name
        assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW, HealthStatus.RED]
        assert result.message
        assert result.timestamp


@pytest.mark.asyncio
async def test_overall_status():
    """Test overall status calculation"""
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    overall = checker.get_overall_status(results)
    assert overall in [HealthStatus.GREEN, HealthStatus.YELLOW, HealthStatus.RED]


@pytest.mark.asyncio
async def test_json_output():
    """Test JSON output format"""
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    json_output = checker.format_results_json(results)
    assert json_output
    assert "overall_status" in json_output
    assert "checks" in json_output


@pytest.mark.asyncio
async def test_cli_output():
    """Test CLI output format"""
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    cli_output = checker.format_results_cli(results)
    assert cli_output
    assert "Peak_Trade Health Check Report" in cli_output
    assert "Overall Status" in cli_output


@pytest.mark.asyncio
async def test_backtest_check():
    """Test backtest health check"""
    check = BacktestHealthCheck()
    result = await check.check()
    
    assert result.name == "backtest"
    assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW, HealthStatus.RED]
    assert result.details


@pytest.mark.asyncio
async def test_exchange_check():
    """Test exchange health check"""
    check = ExchangeHealthCheck()
    result = await check.check()
    
    assert result.name == "exchange"
    assert result.status in [HealthStatus.GREEN, HealthStatus.YELLOW, HealthStatus.RED]
    assert result.details
    assert "exchanges_available" in result.details


@pytest.mark.asyncio
async def test_specific_checks_only():
    """Test running only specific checks"""
    checker = HealthChecker(checks=["backtest", "exchange"])
    results = await checker.run_all_checks()
    
    assert len(results) == 2
    assert "backtest" in results
    assert "exchange" in results
    assert "portfolio" not in results
